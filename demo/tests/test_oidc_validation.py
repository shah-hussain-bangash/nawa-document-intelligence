"""Signed synthetic tokens; these do not test a live provider or login flow."""
import time
import unittest
import warnings
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from nawa_demo.oidc_validation import IdentityValidationError, verify_id_token


class OidcValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        import json
        cls.jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(cls.private.public_key()))
        cls.jwk.update({'kid': 'test-key', 'use': 'sig', 'alg': 'RS256'})

    def token(self, **overrides):
        claims = {'iss': 'https://issuer.example/realm', 'aud': 'nawa-client', 'sub': 'user-1',
                  'iat': int(time.time()), 'exp': int(time.time()) + 300, 'nonce': 'expected-nonce'}
        claims.update(overrides)
        return jwt.encode(claims, self.private, algorithm='RS256', headers={'kid': 'test-key'})

    def check(self, token, keys=None):
        return verify_id_token(token, jwks={'keys': [self.jwk] if keys is None else keys},
                               issuer='https://issuer.example/realm', audience='nawa-client',
                               nonce='expected-nonce')

    def test_valid_signed_token(self):
        self.assertEqual(self.check(self.token())['subject'], 'user-1')

    def test_invalid_claims_fail_closed(self):
        for changes in ({'iss': 'https://evil.example'}, {'aud': 'other'}, {'nonce': 'other'},
                        {'exp': int(time.time()) - 1}, {'exp': str(int(time.time()) + 300)}, {'sub': ''}, {'azp': 'other'},
                        {'aud': ['nawa-client', 'other']}):
            with self.subTest(changes=changes), self.assertRaises(IdentityValidationError):
                self.check(self.token(**changes))

    def test_wrong_or_ambiguous_signing_key(self):
        token = self.token()
        other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        import json
        wrong = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(other.public_key()))
        wrong.update({'kid': 'test-key', 'alg': 'RS256', 'use': 'sig'})
        for keys in ([], [wrong], [self.jwk, self.jwk]):
            with self.subTest(key_count=len(keys)), self.assertRaises(IdentityValidationError):
                self.check(token, keys)

    def test_missing_nonce_and_untrusted_algorithm_rejected(self):
        claims = {'iss':'https://issuer.example/realm', 'aud':'nawa-client', 'sub':'user-1',
                  'iat':int(time.time()), 'exp':int(time.time()) + 300}
        missing_nonce = jwt.encode(claims, self.private, algorithm='RS256', headers={'kid':'test-key'})
        wrong_algorithm = jwt.encode({**claims, 'nonce':'expected-nonce'}, 'synthetic-test-key-with-32-bytes-minimum',
                                     algorithm='HS256', headers={'kid':'test-key'})
        for token in (missing_nonce, wrong_algorithm):
            with self.assertRaises(IdentityValidationError):
                self.check(token)

    def test_unsupported_key_hints_and_weak_keys_rejected(self):
        import json
        claims = {'iss':'https://issuer.example/realm', 'aud':'nawa-client', 'sub':'user-1',
                  'iat':int(time.time()), 'exp':int(time.time()) + 300, 'nonce':'expected-nonce'}
        for extra in ({'crit':['unknown'], 'unknown':'value'}, {'jku':'https://evil.example/keys'},
                      {'x5u':'https://evil.example/cert'}):
            token = jwt.encode(claims, self.private, algorithm='RS256', headers={'kid':'test-key', **extra})
            with self.subTest(extra=extra), self.assertRaises(IdentityValidationError):
                self.check(token)
        token = self.token()
        with self.assertRaises(IdentityValidationError):
            self.check(token, [{**self.jwk, 'key_ops':['sign']}])
        weak = rsa.generate_private_key(public_exponent=65537, key_size=1024)
        weak_jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(weak.public_key()))
        weak_jwk.update({'kid':'test-key', 'alg':'RS256', 'use':'sig'})
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='The RSA key is 1024 bits long.*')
            weak_token = jwt.encode(claims, weak, algorithm='RS256', headers={'kid':'test-key'})
        with self.assertRaises(IdentityValidationError):
            self.check(weak_token, [weak_jwk])


if __name__ == '__main__':
    unittest.main()
