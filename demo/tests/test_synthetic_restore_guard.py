"""Fixture-only tests for the read-only synthetic restore guard."""
from types import SimpleNamespace
import unittest

from nawa_demo.synthetic_restore_guard import verify_no_active_synthetic_grants


class Connection:
    def __init__(self, *, database='nawa_phase13_qa_restore_123456abcdef', active=False,
                 host='127.0.0.1', autocommit=False, visibility=(True, False, 'r')):
        self.database, self.active = database, active
        self.info, self.autocommit = SimpleNamespace(host=host), autocommit
        self.visibility = visibility
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query):
        self.queries.append(query)
        if query == 'SET TRANSACTION READ ONLY':
            return self
        if query == 'SELECT current_database()':
            return SimpleNamespace(fetchone=lambda:(self.database,))
        if query == "SELECT has_table_privilege(current_user, 'public.nawa_synthetic_document_grants', 'SELECT'), row_security_active('public.nawa_synthetic_document_grants'), (SELECT relkind::text FROM pg_class WHERE oid = 'public.nawa_synthetic_document_grants'::regclass)":
            return SimpleNamespace(fetchone=lambda:self.visibility)
        if query in ('SELECT EXISTS (SELECT 1 FROM public.nawa_synthetic_document_grants WHERE active)',
                     'SELECT EXISTS (SELECT 1 FROM nawa_synthetic_document_grants WHERE active)'):
            return SimpleNamespace(fetchone=lambda:(self.active,))
        raise AssertionError('Unexpected query')


class SyntheticRestoreGuardTests(unittest.TestCase):
    def test_read_only_check_accepts_only_zero_active_grants(self):
        for active in (False, True):
            with self.subTest(active=active):
                connection = Connection(active=active)
                self.assertIs(verify_no_active_synthetic_grants(lambda:connection), not active)
                self.assertEqual(connection.queries[0], 'SET TRANSACTION READ ONLY')
                self.assertEqual(len(connection.queries), 4)

    def test_rejects_unapproved_connection_and_database(self):
        for connection in (Connection(database='nawa_demo'), Connection(host='db.example'),
                           Connection(autocommit=True), Connection(database='nawa_phase13_qa_restore_invalid')):
            with self.subTest(connection=connection):
                self.assertFalse(verify_no_active_synthetic_grants(lambda:connection))
                self.assertNotIn('SELECT EXISTS (SELECT 1 FROM public.nawa_synthetic_document_grants WHERE active)',
                                 connection.queries)

    def test_row_security_or_missing_visibility_cannot_report_a_clear_restore(self):
        for visibility in ((True, True, 'r'), (False, False, 'r'), (True, False, 'v'), None):
            with self.subTest(visibility=visibility):
                connection = Connection(active=False, visibility=visibility)
                self.assertFalse(verify_no_active_synthetic_grants(lambda:connection))
                self.assertNotIn('SELECT EXISTS (SELECT 1 FROM public.nawa_synthetic_document_grants WHERE active)',
                                 connection.queries)

    def test_errors_and_malformed_results_fail_closed(self):
        self.assertFalse(verify_no_active_synthetic_grants(None))
        def fail():
            raise OSError('private diagnostic')
        self.assertFalse(verify_no_active_synthetic_grants(fail))
        self.assertFalse(verify_no_active_synthetic_grants(lambda:Connection(active=None)))
        self.assertFalse(verify_no_active_synthetic_grants(lambda:Connection(active=0)))


if __name__ == '__main__':
    unittest.main()
