"""Transport unit tests with a fake opener; not an actual TLS/provider test."""
import json
import unittest
from nawa_demo.oidc_provider_draft import OidcProvider, ProviderError


class Response:
    def __init__(self, value, status=200):
        self.value, self.status = value, status
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, size): return self.value[:size]


class Opener:
    def __init__(self, value, status=200):
        self.value, self.status, self.requests = value, status, []
    def open(self, request, timeout):
        self.requests.append((request, timeout))
        return Response(self.value, self.status)


class ProviderTests(unittest.TestCase):
    def test_metadata_and_exchange(self):
        opener = Opener(json.dumps({'id_token': 'synthetic'}).encode())
        provider = OidcProvider('https://id.example/realm', opener=opener)
        self.assertEqual(provider.metadata()['id_token'], 'synthetic')
        self.assertEqual(provider.exchange('https://id.example/token', code='code', verifier='verifier',
                                          redirect_uri='http://127.0.0.1:8765/auth/callback', client_id='client'), 'synthetic')
        self.assertIn(b'code_verifier=verifier', opener.requests[-1][0].data)
        self.assertEqual(opener.requests[-1][1], 10)

    def test_rejects_untrusted_endpoints(self):
        provider = OidcProvider('https://id.example/realm', opener=Opener(b'{}'))
        for url in ('http://id.example/token', 'https://evil.example/token',
                    'https://id.example/token?extra=1', 'https://user@id.example/token'):
            with self.subTest(url=url), self.assertRaises(ProviderError):
                provider.jwks(url)

    def test_rejects_errors_invalid_json_and_oversize(self):
        for raw, status in ((b'{}', 302), (b'invalid', 200), (b'x' * (1024 * 1024 + 1), 200), (b'[]', 200)):
            with self.subTest(status=status, length=len(raw)), self.assertRaises(ProviderError):
                OidcProvider('https://id.example/realm', opener=Opener(raw, status)).metadata()

    def test_insecure_issuer_is_rejected(self):
        with self.assertRaises(ValueError):
            OidcProvider('http://id.example/realm')


if __name__ == '__main__':
    unittest.main()
