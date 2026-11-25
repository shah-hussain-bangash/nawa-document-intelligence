"""Opt-in real local Keycloak code/PKCE login using a private synthetic fixture.

Creates a disposable application DB. Never targets a production issuer and never
logs credentials, authorization codes, tokens, cookies or provider HTML.
"""
import argparse
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import ssl
from tempfile import TemporaryDirectory
from urllib.parse import urlparse, parse_qs
import httpx
from fastapi.testclient import TestClient
from uae_ai.core.config import Settings
from uae_ai.db import Tenant, User
from uae_ai.main import create_app


class LoginForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.action = None
        self.values = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form" and attrs.get("id") == "kc-form-login":
            self.active, self.action = True, attrs.get("action")
        if self.active and tag == "input" and attrs.get("name"):
            self.values[attrs["name"]] = attrs.get("value", "")
    def handle_endtag(self, tag):
        if tag == "form": self.active = False


def validate(issuer, ca, fixture):
    parsed = urlparse(issuer)
    if parsed.scheme != "https" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"} or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("This opt-in test accepts a local HTTPS identity issuer only")
    material = json.loads(Path(fixture).read_text())
    os.environ["SSL_CERT_FILE"] = str(Path(ca).resolve())
    with TemporaryDirectory(prefix="nawa-identity-test-") as directory:
        settings = Settings(app_env="test", auth_mode="oidc", seed_demo=False, data_dir=Path(directory), database_url=f"sqlite:///{Path(directory).as_posix()}/identity.db", oidc_issuer=issuer, oidc_client="nawa-local-validation", oidc_redirect="http://127.0.0.1:8137/auth/callback", model_mode="extractive", retrieval_mode="lexical")
        app = create_app(settings)
        checks = []
        with TestClient(app) as api, httpx.Client(verify=ssl.create_default_context(cafile=ca), timeout=20, trust_env=False, follow_redirects=False) as identity:
            with app.state.session_factory() as db:
                db.add(Tenant(id="validation", name="Synthetic identity validation"))
                db.add(User(id="fixture-analyst", tenant_id="validation", name="Synthetic analyst", email="fixture@example.invalid", role="analyst", active=True, preferences={}, oidc_subject=issuer+"|"+material["subject"]))
                db.commit()

            def code_flow():
                started = api.get("/auth/login", follow_redirects=False)
                assert started.status_code == 307
                parameters = parse_qs(urlparse(started.headers["location"]).query)
                assert parameters["code_challenge_method"] == ["S256"]
                response = identity.get(started.headers["location"])
                if response.status_code == 200:
                    form = LoginForm(); form.feed(response.text)
                    action = urlparse(form.action or "")
                    assert action.scheme == "https" and action.netloc == parsed.netloc
                    response = identity.post(form.action, data={**form.values, "username": material["username"], "password": material["password"]})
                assert response.status_code in {302,303}
                callback = urlparse(response.headers["location"])
                assert callback.scheme == "http" and callback.netloc == "127.0.0.1:8137" and callback.path == "/auth/callback"
                query = parse_qs(callback.query)
                return {"state":query["state"][0],"code":query["code"][0]}

            params = code_flow()
            response = api.get("/auth/callback", params=params, follow_redirects=False)
            assert response.status_code == 303
            session = api.get("/auth/me").json()
            assert session["user"]["role"] == "analyst" and session["user"]["tenant_id"] == "validation"
            checks.extend(["https_certificate_verification", "real_authorization_code_and_pkce", "signed_id_token_and_nonce", "provisioned_membership_session"])
            assert api.get("/auth/callback", params=params, follow_redirects=False).status_code == 403
            checks.append("state_replay_rejected")
            assert api.post("/auth/logout", headers={"X-CSRF-Token":session["csrf"]}).status_code == 204
            assert api.get("/auth/me").status_code == 401
            checks.append("session_logout")
            with app.state.session_factory() as db:
                db.get(User,"fixture-analyst").active=False
                db.commit()
            assert api.get("/auth/callback", params=code_flow(), follow_redirects=False).status_code == 403
            checks.append("revoked_membership_rejected")
    return {"scope":"Real local Keycloak and disposable synthetic membership only; not production MFA/recovery/UAT", "passed":checks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issuer",required=True)
    parser.add_argument("--ca",required=True)
    parser.add_argument("--fixture",required=True)
    parser.add_argument("--output",default="artifacts/live-identity-validation.json")
    args=parser.parse_args()
    try:
        result=validate(args.issuer,args.ca,args.fixture)
    except Exception as exc:
        print("Local identity validation failed:",type(exc).__name__,"(provider details withheld)")
        raise SystemExit(1) from None
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(len(result["passed"]),"real identity checks passed. Report:",target)
