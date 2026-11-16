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

    def test_operator_grant_and_revoke_invalidates_existing_session(self):
        from nawa_demo.migrate import migrate
        from nawa_demo.identity_repository import membership, membership_by_key
        from nawa_demo.membership_admin import grant, revoke
        from nawa_demo.session_draft import SessionError, SessionStore
        issuer, subject, tenant = 'https://issuer.example/realm', 'synthetic-user', 'tenant-a'
        with self.connect() as conn:
            migrate(conn)
            with self.assertRaisesRegex(ValueError, 'provisioned first'):
                grant(conn, issuer=issuer, subject=subject, tenant=tenant, role='analyst', operator='qa-operator', reason='Synthetic test')
            conn.execute('INSERT INTO nawa_tenants (id) VALUES (%s)', (tenant,))
            conn.execute('INSERT INTO nawa_identities (issuer, subject) VALUES (%s,%s)', (issuer, subject))
            grant(conn, issuer=issuer, subject=subject, tenant=tenant, role='analyst', operator='qa-operator', reason='Synthetic test')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                grant(conn, issuer=issuer, subject=subject, tenant=tenant, role='reviewer', operator='qa-operator', reason='Synthetic test')
        def lookup(identity_key, tenant_id):
            with self.connect() as conn:
                return membership_by_key(conn, identity_key=identity_key, tenant=tenant_id)
        with self.connect() as conn:
            principal = membership(conn, issuer=issuer, subject=subject, tenant=tenant)
        sessions = SessionStore(lookup)
        tokens = sessions.issue(principal.subject, tenant)
        self.assertEqual(sessions.authorize_current(tokens['session'], 'view').role, 'analyst')
        with self.connect() as conn:
            self.assertTrue(revoke(conn, issuer=issuer, subject=subject, tenant=tenant, operator='qa-operator', reason='Synthetic test'))
            self.assertFalse(revoke(conn, issuer=issuer, subject=subject, tenant=tenant, operator='qa-operator', reason='Synthetic test'))
        with self.assertRaises(SessionError):
            sessions.authorize_current(tokens['session'], 'view')
        with self.connect() as conn:
            self.assertIsNone(membership(conn, issuer=issuer, subject=subject, tenant=tenant))
            events = conn.execute('SELECT action, operator_name FROM nawa_membership_events ORDER BY id').fetchall()
            self.assertEqual(events, [('grant', 'qa-operator'), ('revoke', 'qa-operator')])
            with self.assertRaisesRegex(ValueError, 'already exists'):
                grant(conn, issuer=issuer, subject=subject, tenant=tenant, role='reviewer', operator='qa-operator', reason='Synthetic test')

    def test_audit_failure_rolls_back_membership_revocation(self):
        from nawa_demo.migrate import migrate
        from nawa_demo.membership_admin import grant, revoke
        issuer, subject, tenant = 'https://issuer.example/realm', 'synthetic-user', 'tenant-a'
        with self.connect() as conn:
            migrate(conn)
            conn.execute('INSERT INTO nawa_tenants (id) VALUES (%s)', (tenant,))
            conn.execute('INSERT INTO nawa_identities (issuer, subject) VALUES (%s,%s)', (issuer, subject))
            grant(conn, issuer=issuer, subject=subject, tenant=tenant, role='analyst', operator='qa', reason='test')
            conn.execute("ALTER TABLE nawa_membership_events ADD CONSTRAINT qa_reject_revoke CHECK (action <> 'revoke')")
        with self.connect() as conn:
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                revoke(conn, issuer=issuer, subject=subject, tenant=tenant, operator='qa', reason='test')
        with self.connect() as conn:
            row = conn.execute('SELECT active FROM nawa_memberships WHERE subject=%s', (subject,)).fetchone()
            self.assertEqual(row, (True,))
            self.assertEqual(conn.execute('SELECT count(*) FROM nawa_membership_events').fetchone()[0], 1)

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
