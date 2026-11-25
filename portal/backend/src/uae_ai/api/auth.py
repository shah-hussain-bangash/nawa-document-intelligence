import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode, urlparse
import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select, delete
from uae_ai.core.security import create_session, current_user, get_db, token_hash, user_view
from uae_ai.db import LoginSession, OAuthState, User
from uae_ai.domain.schemas import DemoLogin

router = APIRouter(prefix="/auth", tags=["Identity"])


@router.get("/config")
def auth_config(request: Request):
    return {"mode": request.app.state.settings.auth_mode}


@router.post("/demo")
def demo_login(payload: DemoLogin, request: Request, response: Response, db=Depends(get_db)):
    settings = request.app.state.settings
    if settings.auth_mode != "demo" or settings.app_env not in {"local", "test"}:
        raise HTTPException(403, "Demo sign-in is disabled.")
    user = db.get(User, f"{payload.tenant}-{payload.role}")
    if not user or not user.active:
        raise HTTPException(401, "Demo account is unavailable.")
    return create_session(db, user, response, settings)


@router.get("/me")
def me(request: Request, user=Depends(current_user), db=Depends(get_db)):
    session = db.get(LoginSession, token_hash(request.cookies["nawa_session"]))
    return {"user": user_view(user), "csrf": session.csrf, "mode": request.app.state.settings.auth_mode}


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, user=Depends(current_user), db=Depends(get_db)):
    session = db.get(LoginSession, token_hash(request.cookies["nawa_session"]))
    db.delete(session)
    db.commit()
    response.delete_cookie("nawa_session", path="/")


def discovery(settings):
    with httpx.Client(timeout=10, follow_redirects=False) as client:
        result = client.get(settings.oidc_issuer.rstrip("/") + "/.well-known/openid-configuration")
        result.raise_for_status()
        metadata = result.json()
    if metadata.get("issuer") != settings.oidc_issuer:
        raise HTTPException(503, "Identity issuer mismatch.")
    for key in ["authorization_endpoint", "token_endpoint", "jwks_uri"]:
        route = urlparse(metadata.get(key, ""))
        issuer = urlparse(settings.oidc_issuer)
        if route.scheme != "https" or route.netloc != issuer.netloc or route.username or route.password or route.fragment:
            raise HTTPException(503, "Identity endpoints must use the trusted issuer's HTTPS origin.")
    return metadata


@router.get("/login")
def oidc_login(request: Request, db=Depends(get_db)):
    settings = request.app.state.settings
    if settings.auth_mode != "oidc":
        raise HTTPException(400, "Use demo sign-in in this environment.")
    try:
        meta = discovery(settings)
    except (httpx.HTTPError, ValueError):
        raise HTTPException(503, "The trusted identity service is unavailable.") from None
    state, verifier, nonce = [secrets.token_urlsafe(32) for _ in range(3)]
    db.execute(delete(OAuthState).where(OAuthState.expires < int(time.time())))
    db.add(OAuthState(id=token_hash(state), verifier=verifier, nonce=nonce, expires=int(time.time())+300))
    db.commit()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    url = meta["authorization_endpoint"] + "?" + urlencode({"response_type": "code", "client_id": settings.oidc_client, "redirect_uri": settings.oidc_redirect, "scope": "openid profile email", "state": state, "nonce": nonce, "code_challenge": challenge, "code_challenge_method": "S256"})
    response = RedirectResponse(url)
    response.set_cookie("nawa_oauth_state", state, max_age=300, httponly=True, secure=settings.app_env == "production", samesite="lax")
    return response


@router.get("/callback")
def oidc_callback(request: Request, code: str = "", state: str = "", db=Depends(get_db)):
    settings = request.app.state.settings
    if settings.auth_mode != "oidc":
        raise HTTPException(403, "OIDC is not enabled.")
    saved = db.get(OAuthState, token_hash(state)) if state else None
    if not saved or saved.expires < time.time() or not secrets.compare_digest(state, request.cookies.get("nawa_oauth_state", "")):
        raise HTTPException(403, "The sign-in state is invalid or expired.")
    nonce, verifier = saved.nonce, saved.verifier
    db.delete(saved)
    db.commit()
    try:
        meta = discovery(settings)
        with httpx.Client(timeout=15, follow_redirects=False) as client:
            response = client.post(meta["token_endpoint"], data={"grant_type": "authorization_code", "code": code, "redirect_uri": settings.oidc_redirect, "client_id": settings.oidc_client, "client_secret": settings.oidc_secret, "code_verifier": verifier})
            response.raise_for_status()
            encoded = response.json()["id_token"]
        header = jwt.get_unverified_header(encoded)
        if header.get("alg") not in {"RS256", "ES256"} or not isinstance(header.get("kid"), str):
            raise ValueError("Untrusted signing algorithm or missing key ID")
        with httpx.Client(timeout=10, follow_redirects=False) as client:
            key_response = client.get(meta["jwks_uri"])
            key_response.raise_for_status()
            candidates = [key for key in key_response.json()["keys"] if key.get("kid") == header["kid"] and key.get("use", "sig") == "sig" and key.get("alg", header["alg"]) == header["alg"]]
        if len(candidates) != 1:
            raise ValueError("Ambiguous signing key")
        key = jwt.PyJWK.from_dict(candidates[0], algorithm=header["alg"]).key
        claims = jwt.decode(encoded, key, algorithms=["RS256", "ES256"], issuer=settings.oidc_issuer, audience=settings.oidc_client, options={"require": ["exp", "iat", "iss", "aud", "sub", "nonce"]})
        if not secrets.compare_digest(claims["nonce"], nonce):
            raise ValueError("nonce")
        if claims.get("azp", settings.oidc_client) != settings.oidc_client or isinstance(claims["aud"], list) and len(claims["aud"]) > 1 and "azp" not in claims:
            raise ValueError("Authorised party mismatch")
        user = db.scalar(select(User).where(User.oidc_subject == settings.oidc_issuer + "|" + claims["sub"], User.active == True))
        if not user:
            raise HTTPException(403, "Your identity has no provisioned workspace membership.")
    except (httpx.HTTPError, jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "The trusted identity response could not be verified.") from None
    result = RedirectResponse(settings.web_origin, status_code=303)
    result.delete_cookie("nawa_oauth_state")
    create_session(db, user, result, settings)
    return result
