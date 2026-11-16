"""Isolated-schema integration tests; opt in with NAWA_TEST_POSTGRES=1."""
import os
import json
import subprocess
import sys
import unittest
from urllib.request import Request, urlopen
from uuid import uuid4


@unittest.skipUnless(os.environ.get('NAWA_TEST_POSTGRES') == '1', 'PostgreSQL integration not configured')
class PostgresIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        from psycopg import sql
        cls.psycopg = psycopg
        cls.sql = sql
        cls.schema = 'nawa_test_' + uuid4().hex
        cls.params = dict(host=os.environ['POSTGRES_HOST'], dbname=os.environ['POSTGRES_DB'],
                          user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'],
                          connect_timeout=5)
        with psycopg.connect(**cls.params, autocommit=True) as conn:
            conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(cls.schema)))

    @classmethod
    def tearDownClass(cls):
        with cls.psycopg.connect(**cls.params, autocommit=True) as conn:
            conn.execute(cls.sql.SQL('DROP SCHEMA {} CASCADE').format(cls.sql.Identifier(cls.schema)))

    def connect(self):
        return self.psycopg.connect(**self.params, options='-c search_path=' + self.schema)

    def test_migrations_and_persistent_reviews(self):
        from nawa_demo.migrate import migrate
        from nawa_demo.postgres_state import PostgresState
        from concurrent.futures import ThreadPoolExecutor
        state = PostgresState(self.connect)
        state.ready()
        with self.connect() as conn:
            migrate(conn)  # repeated migration is idempotent
        english = state.add_sample('english_quote.txt')
        arabic = state.add_sample('arabic_quote.txt')
        ids = {item['id'] for item in PostgresState(self.connect).list_items()}
        self.assertTrue({english['id'], arabic['id']} <= ids)
        self.assertEqual(state.compare([english['id'], arabic['id']])['lowest_valid_total'], 'شركة المثال للتوريدات')
        state.review_start(english['id'])
        payload = {'id': english['id'], 'actor': 'reviewer-1', 'decision': 'approve',
                   'reason': 'Synthetic review', 'expected_revision': 1}
        def decide_once():
            try:
                return state.review_decision(payload)['status']
            except ValueError:
                return 'rejected'
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(lambda _: decide_once(), range(2))), ['approved', 'rejected'])
        self.assertEqual(PostgresState(self.connect).review_show(english['id'])['revision'], 2)
        invalid = state.add_sample('incorrect_vat_quote.txt')
        state.review_start(invalid['id'])
        with self.assertRaisesRegex(ValueError, 'financial mismatches'):
            state.review_decision({'id': invalid['id'], 'actor': 'reviewer-1', 'decision': 'approve',
                                   'reason': 'Invalid synthetic VAT', 'expected_revision': 1})
        self.assertEqual(state.review_show(invalid['id'])['revision'], 1)
        duplicate = state.add_sample('english_quote.txt')
        self.assertNotEqual(english['id'], duplicate['id'])
        state.review_start(duplicate['id'])
        unusual_actor = "reviewer'; DROP TABLE nawa_quotations; --"
        reviewed = state.review_decision({'id': duplicate['id'], 'actor': unusual_actor,
                                          'decision': 'reject', 'reason': 'Input handling check',
                                          'expected_revision': 1})
        self.assertEqual(reviewed['history'][-1]['actor'], unusual_actor)
        self.assertEqual(state.get_quote(english['id'])['total'], '1050.00')
        with self.assertRaisesRegex(ValueError, 'Quotation not found'):
            state.get_quote("missing'; DROP TABLE nawa_quotations; --")
        with self.assertRaises(ValueError):
            state.review_decision({'id': invalid['id'], 'actor': 'reviewer-1', 'decision': 'reject',
                                   'reason': 'Stale', 'expected_revision': 0})
        self.assertEqual(state.review_show(invalid['id'])['revision'], 1)
        with self.connect() as conn:
            conn.execute("UPDATE nawa_schema_migrations SET checksum = 'changed'")
        with self.assertRaisesRegex(RuntimeError, 'Migration history mismatch'):
            PostgresState(self.connect)

    def test_http_records_survive_application_restart(self):
        server_script = '''
import os, psycopg
from http.server import HTTPServer
from nawa_demo.dashboard import make_handler
from nawa_demo.postgres_state import PostgresState
def connect():
    return psycopg.connect(host=os.environ['POSTGRES_HOST'], dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'],
        options='-c search_path=' + os.environ['TEST_SCHEMA'], connect_timeout=5)
state = PostgresState(connect)
state.storage_mode = 'postgres'
with HTTPServer(('127.0.0.1', 0), make_handler(state)) as server:
    print(server.server_port, flush=True)
    server.serve_forever()
'''
        env = dict(os.environ, TEST_SCHEMA=self.schema)
        def start():
            proc = subprocess.Popen([sys.executable, '-c', server_script], env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            line = proc.stdout.readline().strip()
            if not line.isdigit():
                error = proc.stderr.read()
                proc.wait(timeout=5)
                self.fail('Test server failed to start: ' + error)
            return proc, 'http://127.0.0.1:' + line
        def post(root, path, data):
            request = Request(root + path, data=json.dumps(data).encode(),
                              headers={'Content-Type': 'application/json'})
            with urlopen(request, timeout=5) as response:
                return json.load(response)
        proc, root = start()
        try:
            row = post(root, '/api/load-sample', {'name': 'arabic_quote.txt'})
            post(root, '/api/review/start', {'id': row['id']})
            post(root, '/api/review/decide', {'id': row['id'], 'actor': 'reviewer-1',
                 'decision': 'approve', 'reason': 'Synthetic review', 'expected_revision': 1})
        finally:
            proc.terminate()
            proc.wait(timeout=5)
            proc.stdout.close()
            proc.stderr.close()
        proc, root = start()
        try:
            with urlopen(root + '/api/quotations', timeout=5) as response:
                result = json.load(response)
            self.assertEqual(result['storage'], 'postgres')
            self.assertTrue(any(item['id'] == row['id'] for item in result['quotations']))
            review = post(root, '/api/review/show', {'id': row['id']})
            self.assertEqual((review['status'], review['revision']), ('approved', 2))
        finally:
            proc.terminate()
            proc.wait(timeout=5)
            proc.stdout.close()
            proc.stderr.close()

