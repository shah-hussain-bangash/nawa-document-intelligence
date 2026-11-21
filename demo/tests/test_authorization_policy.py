"""Policy unit tests only; endpoints remain unauthenticated until integrated."""
import unittest
from nawa_demo.authorization import Principal, authorized


class AuthorizationPolicyTests(unittest.TestCase):
    def test_role_capabilities(self):
        for role in ('viewer', 'analyst', 'reviewer'):
            person = Principal('issuer|subject', 'tenant-a', role)
            for action in ('list', 'view', 'compare', 'review_view'):
                self.assertTrue(authorized(person, action, tenant='tenant-a'))
        self.assertTrue(authorized(Principal('s', 'a', 'analyst'), 'correct', tenant='a'))
        self.assertFalse(authorized(Principal('s', 'a', 'analyst'), 'decide', tenant='a'))
        self.assertTrue(authorized(Principal('s', 'a', 'reviewer'), 'decide', tenant='a'))
        self.assertFalse(authorized(Principal('s', 'a', 'reviewer'), 'correct', tenant='a'))
        self.assertFalse(authorized(Principal('s', 'a', 'viewer'), 'load', tenant='a'))

    def test_default_deny_and_tenant_isolation(self):
        person = Principal('subject', 'tenant-a', 'reviewer')
        self.assertFalse(authorized(person, 'decide', tenant='tenant-b'))
        self.assertFalse(authorized(person, 'unknown', tenant='tenant-a'))
        self.assertFalse(authorized(Principal('subject', 'tenant-a', 'admin'), 'decide', tenant='tenant-a'))
        self.assertFalse(authorized(Principal('subject', 'tenant-a', 'reviewer', False), 'view', tenant='tenant-a'))
        self.assertFalse(authorized(Principal('subject', 'tenant-a', []), 'view', tenant='tenant-a'))
        self.assertFalse(authorized(None, 'view', tenant='tenant-a'))
        self.assertFalse(authorized(Principal('', 'tenant-a', 'viewer'), 'view', tenant='tenant-a'))


if __name__ == '__main__':
    unittest.main()
