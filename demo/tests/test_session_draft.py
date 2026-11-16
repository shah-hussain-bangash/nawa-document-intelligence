"""Session primitives only; these tests do not establish HTTP security."""
import unittest
from nawa_demo.authorization import Principal
from nawa_demo.session_draft import SessionError, SessionStore


class SessionDraftTests(unittest.TestCase):
    def setUp(self):
        self.clock = [0]
        self.members = {('issuer|subject', 'tenant-a'): Principal('issuer|subject', 'tenant-a', 'analyst')}
        self.store = SessionStore(lambda s, t: self.members.get((s, t)), ttl=10, clock=lambda: self.clock[0])
        self.tokens = self.store.issue('issuer|subject', 'tenant-a')

    def test_csrf_role_and_tenant_checks(self):
        token, csrf = self.tokens['session'], self.tokens['csrf']
        self.assertEqual(self.store.authorize(token, 'correct', tenant='tenant-a', csrf=csrf).role, 'analyst')
        for kwargs in ({'tenant':'tenant-b', 'csrf':csrf}, {'tenant':'tenant-a'},
                       {'tenant':'tenant-a', 'csrf':'wrong'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(SessionError):
                self.store.authorize(token, 'correct', **kwargs)
        with self.assertRaises(SessionError):
            self.store.authorize(token, 'decide', tenant='tenant-a', csrf=csrf)

    def test_membership_changes_and_revocation_take_effect(self):
        token = self.tokens['session']
        self.members[('issuer|subject','tenant-a')] = Principal('issuer|subject','tenant-a','viewer')
        with self.assertRaises(SessionError):
            self.store.authorize(token, 'correct', tenant='tenant-a', csrf=self.tokens['csrf'])
        del self.members[('issuer|subject','tenant-a')]
        with self.assertRaises(SessionError):
            self.store.authorize(token, 'view', tenant='tenant-a')

    def test_logout_and_expiration(self):
        token = self.tokens['session']
        with self.assertRaises(SessionError):
            self.store.logout(token, 'wrong')
        self.store.logout(token, self.tokens['csrf'])
        with self.assertRaises(SessionError):
            self.store.authorize(token, 'view', tenant='tenant-a')
        new = self.store.issue('issuer|subject', 'tenant-a')['session']
        self.clock[0] = 10
        with self.assertRaises(SessionError):
            self.store.authorize(new, 'view', tenant='tenant-a')

    def test_tokens_are_not_stored_as_plaintext(self):
        self.assertNotIn(self.tokens['session'], repr(self.store._sessions))
        self.assertNotIn(self.tokens['csrf'], repr(self.store._sessions))
        with self.assertRaises(SessionError):
            self.store.issue('unknown', 'tenant-a')


if __name__ == '__main__':
    unittest.main()
