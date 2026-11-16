"""Isolated-schema Phase 12 membership tests, opt in with NAWA_TEST_POSTGRES=1."""
import os
import unittest
from uuid import uuid4


@unittest.skipUnless(os.environ.get('NAWA_TEST_POSTGRES') == '1', 'PostgreSQL integration not configured')
class IdentityPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        from psycopg import sql
        cls.psycopg, cls.sql = psycopg, sql
        cls.params = dict(host=os.environ['POSTGRES_HOST'], dbname=os.environ['POSTGRES_DB'],
                          user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'],
                          connect_timeout=5)

    def setUp(self):
        self.schema = 'nawa_identity_test_' + uuid4().hex
        with self.psycopg.connect(**self.params, autocommit=True) as conn:
            conn.execute(self.sql.SQL('CREATE SCHEMA {}').format(self.sql.Identifier(self.schema)))

    def tearDown(self):
        with self.psycopg.connect(**self.params, autocommit=True) as conn:
            conn.execute(self.sql.SQL('DROP SCHEMA {} CASCADE').format(self.sql.Identifier(self.schema)))

    def connect(self):
        return self.psycopg.connect(**self.params, options='-c search_path=' + self.schema)

    def test_database_mode_blocks_unsafe_switch_and_legacy_assignment(self):
        from nawa_demo.postgres_state import PostgresState
        from nawa_demo.storage_mode import claim_database_mode
        state = PostgresState(self.connect)
        state.add_sample('english_quote.txt')  # Existing unassigned Phase 11 data.
        with self.assertRaisesRegex(RuntimeError, 'Legacy quotations'):
            claim_database_mode(self.connect, 'oidc')
        claim_database_mode(self.connect, 'demo')
        claim_database_mode(self.connect, 'demo')
        with self.assertRaisesRegex(RuntimeError, 'different access mode'):
            claim_database_mode(self.connect, 'oidc')

    def test_authenticated_database_cannot_start_in_demo_mode(self):
        from nawa_demo.postgres_state import PostgresState
        from nawa_demo.storage_mode import claim_database_mode
        PostgresState(self.connect)
        claim_database_mode(self.connect, 'oidc')
        claim_database_mode(self.connect, 'oidc')
        with self.assertRaisesRegex(RuntimeError, 'different access mode'):
            claim_database_mode(self.connect, 'demo')

    def test_membership_is_server_provisioned_and_revocable(self):
        from nawa_demo.migrate import migrate
        from nawa_demo.identity_repository import membership, membership_by_key
        from nawa_demo.authorization import authorized
        with self.connect() as conn:
            migrate(conn)
            migrate(conn)
            conn.execute('INSERT INTO nawa_tenants (id) VALUES (%s), (%s)', ('tenant-a', 'tenant-b'))
            conn.execute('INSERT INTO nawa_identities (issuer, subject) VALUES (%s, %s)',
                         ('https://issuer.example', 'person-1'))
            conn.execute('INSERT INTO nawa_memberships (issuer, subject, tenant_id, role) VALUES (%s,%s,%s,%s)',
                         ('https://issuer.example', 'person-1', 'tenant-a', 'analyst'))
        with self.connect() as conn:
            principal = membership(conn, issuer='https://issuer.example', subject='person-1', tenant='tenant-a')
            self.assertEqual(membership_by_key(conn, identity_key=principal.subject, tenant='tenant-a'), principal)
            self.assertIsNone(membership_by_key(conn, identity_key='not-json', tenant='tenant-a'))
            self.assertTrue(authorized(principal, 'correct', tenant='tenant-a'))
            self.assertFalse(authorized(principal, 'decide', tenant='tenant-a'))
            self.assertIsNone(membership(conn, issuer='https://issuer.example', subject='person-1', tenant='tenant-b'))
            self.assertIsNone(membership(conn, issuer='https://wrong.example', subject='person-1', tenant='tenant-a'))
            self.assertIsNone(membership(conn, issuer='https://issuer.example', subject="x' OR 1=1 --", tenant='tenant-a'))
            conn.execute('UPDATE nawa_memberships SET active = false WHERE subject = %s', ('person-1',))
        with self.connect() as conn:
            self.assertIsNone(membership(conn, issuer='https://issuer.example', subject='person-1', tenant='tenant-a'))

    def test_tenant_scoped_operations_and_server_actor(self):
        from nawa_demo.migrate import migrate
        from nawa_demo.scoped_state import ScopedState, AccessDenied
        from nawa_demo.identity_repository import membership
        with self.connect() as conn:
            migrate(conn)
            conn.execute('INSERT INTO nawa_tenants (id) VALUES (%s), (%s)', ('red', 'blue'))
            for subject, tenant, role in [('analyst', 'red', 'analyst'), ('reviewer', 'red', 'reviewer'),
                                          ('outsider', 'blue', 'reviewer')]:
                conn.execute('INSERT INTO nawa_identities (issuer, subject) VALUES (%s, %s)',
                             ('https://id.example', subject))
                conn.execute('INSERT INTO nawa_memberships (issuer, subject, tenant_id, role) VALUES (%s,%s,%s,%s)',
                             ('https://id.example', subject, tenant, role))
            analyst = membership(conn, issuer='https://id.example', subject='analyst', tenant='red')
            reviewer = membership(conn, issuer='https://id.example', subject='reviewer', tenant='red')
            outsider = membership(conn, issuer='https://id.example', subject='outsider', tenant='blue')
        state = ScopedState(self.connect)
        first = state.add_sample(analyst, 'english_quote.txt')
        second = state.add_sample(analyst, 'arabic_quote.txt')
        self.assertEqual(len(state.list_items(analyst)), 2)
        self.assertEqual(state.list_items(outsider), [])
        with self.assertRaisesRegex(ValueError, 'Quotation not found'):
            state.get_quote(outsider, first['id'])
        with self.assertRaisesRegex(ValueError, 'Quotation not found'):
            state.compare(outsider, [first['id'], second['id']])
        state.review_start(analyst, first['id'])
        payload = {'id': first['id'], 'actor': 'forged-actor', 'decision': 'approve',
                   'reason': 'Synthetic review', 'expected_revision': 1}
        with self.assertRaises(AccessDenied):
            state.review_decision(analyst, payload)
        with self.assertRaisesRegex(ValueError, 'Quotation not found'):
            state.review_decision(outsider, payload)
        result = state.review_decision(reviewer, payload)
        import hashlib
        self.assertEqual(result['history'][-1]['actor'], 'oidc:' + hashlib.sha256(reviewer.subject.encode()).hexdigest())
        with self.connect() as conn:
            conn.execute('UPDATE nawa_memberships SET active = false WHERE subject = %s', ('reviewer',))
        with self.assertRaises(AccessDenied):
            state.list_items(reviewer)


if __name__ == '__main__':
    unittest.main()
