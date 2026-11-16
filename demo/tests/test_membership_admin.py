"""Input checks only; PostgreSQL integration is tested separately."""
import unittest
from nawa_demo.membership_admin import grant, revoke


class MembershipAdminTests(unittest.TestCase):
    def test_rejects_untrusted_issuer_and_invalid_identifiers(self):
        for issuer, subject, tenant in [('http://id.example', 's', 't'),
                                         ('https://user@id.example', 's', 't'),
                                         ('https://id.example?bad=1', 's', 't'),
                                         ('https://id.example', '', 't'),
                                         ('https://id.example', 's', 't\x00')]:
            with self.subTest(issuer=issuer, subject=subject, tenant=tenant), self.assertRaises(ValueError):
                revoke(None, issuer=issuer, subject=subject, tenant=tenant, operator='qa', reason='test')

    def test_rejects_unknown_or_unhashable_role(self):
        for role in ('admin', [], None):
            with self.subTest(role=role), self.assertRaises(ValueError):
                grant(None, issuer='https://id.example', subject='s', tenant='t', role=role, operator='qa', reason='test')

    def test_requires_synthetic_operator_and_reason(self):
        for operator, reason in (('', 'test'), ('qa', ''), ('qa', 'x' * 501)):
            with self.subTest(operator=operator, reason_length=len(reason)), self.assertRaises(ValueError):
                revoke(None, issuer='https://id.example', subject='s', tenant='t', operator=operator, reason=reason)


if __name__ == '__main__':
    unittest.main()
