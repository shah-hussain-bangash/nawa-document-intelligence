"""Draft HTTPS OIDC provider transport; not wired into dashboard startup.

Only a preconfigured HTTPS issuer origin is trusted. TLS certificate checks are
mandatory. Provider responses are size-limited and redirects are rejected.
"""
from __future__ import annotations

import json
import ssl
from urllib.parse import urlencode, urlparse
from urllib.request import Request, HTTPSHandler, HTTPRedirectHandler, build_opener


class ProviderError(ValueError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class OidcProvider:
    def __init__(self, issuer, *, ca_file=None, timeout=10, opener=None):
        route = urlparse(issuer)
        if (route.scheme != 'https' or not route.hostname or route.username or route.password
                or route.query or route.fragment or timeout <= 0 or timeout > 30):
            raise ValueError('Invalid identity provider configuration')
        self.issuer = issuer.rstrip('/')
        self.origin = route.netloc
        self.timeout = timeout
        context = ssl.create_default_context(cafile=ca_file)
        self._opener = opener or build_opener(HTTPSHandler(context=context), _NoRedirect())

    def _request(self, url, *, body=None):
        route = urlparse(url)
        if (route.scheme != 'https' or route.netloc != self.origin or route.username or route.password
                or route.query or route.fragment):
            raise ProviderError('Identity service unavailable')
        request = Request(url, data=body, headers={'Accept': 'application/json',
                          **({'Content-Type': 'application/x-www-form-urlencoded'} if body is not None else {})})
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise ProviderError('Identity service unavailable')
                raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ProviderError('Identity service unavailable')
            value = json.loads(raw.decode('utf-8'))
            if not isinstance(value, dict):
                raise ProviderError('Identity service unavailable')
            return value
        except Exception:
            raise ProviderError('Identity service unavailable') from None

    def metadata(self):
        return self._request(self.issuer + '/.well-known/openid-configuration')

    def exchange(self, endpoint, *, code, verifier, redirect_uri, client_id):
        body = urlencode({'grant_type': 'authorization_code', 'code': code, 'code_verifier': verifier,
                          'redirect_uri': redirect_uri, 'client_id': client_id}).encode('ascii')
        value = self._request(endpoint, body=body)
        if not isinstance(value.get('id_token'), str) or not value['id_token']:
            raise ProviderError('Identity service unavailable')
        return value['id_token']

    def jwks(self, endpoint):
        value = self._request(endpoint)
        if not isinstance(value.get('keys'), list):
            raise ProviderError('Identity service unavailable')
        return value
