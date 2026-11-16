"""Draft OIDC ID-token validation; not yet connected to login or endpoints.

The caller must acquire JWKS from the configured trusted issuer over verified
TLS and bind the expected nonce to a one-use login attempt. ID tokens must not
be used as API access tokens. Membership and session creation are separate.
"""
from __future__ import annotations

import secrets
import jwt


class IdentityValidationError(ValueError):
    """A deliberately generic identity validation failure."""


def verify_id_token(encoded, *, jwks, issuer, audience, nonce):
    """Validate a signed RS256 ID token against already trusted key material."""
    try:
        if not all(isinstance(x, str) and x for x in (encoded, issuer, audience, nonce)):
            raise ValueError('Missing validation input')
        if not isinstance(jwks, dict) or not isinstance(jwks.get('keys'), list):
            raise ValueError('Invalid key set')
        header = jwt.get_unverified_header(encoded)
        if header.get('alg') != 'RS256' or not isinstance(header.get('kid'), str) or not header['kid']:
            raise ValueError('Untrusted token header')
        keys = [key for key in jwks['keys'] if isinstance(key, dict)
                and key.get('kid') == header['kid'] and key.get('kty') == 'RSA'
                and key.get('use', 'sig') == 'sig' and key.get('alg', 'RS256') == 'RS256']
        if len(keys) != 1:
            raise ValueError('Signing key unavailable or ambiguous')
        key = jwt.PyJWK.from_dict(keys[0], algorithm='RS256').key
        claims = jwt.decode(encoded, key, algorithms=['RS256'], issuer=issuer, audience=audience,
                            options={'require': ['iss', 'aud', 'sub', 'exp', 'iat', 'nonce']})
        if not isinstance(claims.get('sub'), str) or not claims['sub'].strip():
            raise ValueError('Invalid subject')
        if not isinstance(claims.get('nonce'), str) or not secrets.compare_digest(claims['nonce'], nonce):
            raise ValueError('Invalid nonce')
        if claims.get('azp', audience) != audience:
            raise ValueError('Invalid authorized party')
        if isinstance(claims['aud'], list) and len(claims['aud']) > 1 and 'azp' not in claims:
            raise ValueError('Missing authorized party')
        return {'issuer': issuer, 'subject': claims['sub']}
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise IdentityValidationError('Identity response could not be verified') from None
