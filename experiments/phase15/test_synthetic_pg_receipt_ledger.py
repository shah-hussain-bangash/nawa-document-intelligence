"""Integration tests; require a dedicated Phase 15 QA database."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import unittest
from uuid import uuid4
from unittest.mock import MagicMock

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None

DSN = os.environ.get('NAWA_PHASE15_TEST_DSN')

@unittest.skipUnless(DSN and psycopg, 'Disposable Phase 15 PostgreSQL test not configured')
class SyntheticPostgresReceiptTests(unittest.TestCase):
    def setUp(self):
        from synthetic_pg_receipt_ledger import initialize, register
        from synthetic_worker_receipt import issue_receipt
        self.connect = lambda: psycopg.connect(DSN)
        self.schema = 'nawa_p15_' + uuid4().hex
        initialize(self.connect, self.schema)
        self.key = b'synthetic-test-key-not-for-use!!!'
        self.context = {'tenant':'synthetic-a','document_id':'a'*32,'job_id':'b'*32,
                        'source_sha256':'c'*64,'key_id':'test-v1'}
        self.result = {'extraction_origin':'synthetic_text_worker_v1','total':'1050.00'}
        register(self.connect,self.schema,**self.context)
        self.receipt = issue_receipt(self.key,**self.context,result=self.result)

    def consume(self, **changes):
        from synthetic_pg_receipt_ledger import consume
        args = {'job_id':self.context['job_id'],'tenant':self.context['tenant'],
                'receipt':self.receipt,'result':self.result,'keys':{'test-v1':self.key}}
        args.update(changes)
        return consume(self.connect,self.schema,**args)

    def test_concurrent_receipt_is_consumed_once(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(lambda _: self.consume(), range(2))), [False,True])
        with self.connect() as conn:
            self.assertEqual(conn.execute(sql.SQL('SELECT count(*) FROM {}.events').format(sql.Identifier(self.schema))).fetchone()[0], 1)

    def test_invalid_context_does_not_consume(self):
        self.assertFalse(self.consume(tenant='synthetic-b'))
        self.assertFalse(self.consume(result=dict(self.result,total='1.00')))
        self.assertFalse(self.consume(keys={'test-v1':b'x'*32}))
        self.assertTrue(self.consume())

    def test_event_failure_rolls_back_consumption(self):
        with self.connect() as conn:
            conn.execute(sql.SQL("ALTER TABLE {}.events ADD CONSTRAINT synthetic_failure CHECK (event_type <> 'receipt_consumed')")
                         .format(sql.Identifier(self.schema)))
        with self.assertRaises(psycopg.Error):
            self.consume()
        with self.connect() as conn:
            row = conn.execute(sql.SQL('SELECT state,result_sha256,receipt_mac FROM {}.receipts')
                               .format(sql.Identifier(self.schema))).fetchone()
            self.assertEqual(row, ('pending',None,None))
            self.assertEqual(conn.execute(sql.SQL('SELECT count(*) FROM {}.events').format(sql.Identifier(self.schema))).fetchone()[0], 0)

    def test_non_qa_database_is_rejected_before_schema_creation(self):
        from synthetic_pg_receipt_ledger import initialize
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = ('not_a_qa_database',)
        context = MagicMock()
        context.__enter__.return_value = conn
        with self.assertRaisesRegex(ValueError, 'QA database'):
            initialize(lambda: context, 'nawa_p15_' + uuid4().hex)
        self.assertEqual(conn.execute.call_count, 1)

    def test_stale_app_restore_cannot_reuse_receipt_if_ledger_survives(self):
        from synthetic_reconciliation import classify_snapshots
        from synthetic_reconciliation_inspector import inspect
        # Both databases are created only on the disposable Phase 15 CI server.
        params = psycopg.conninfo.conninfo_to_dict(DSN)
        self.assertTrue(params['dbname'].startswith('nawa_phase15_qa_'))
        app_name = 'nawa_phase15_qa_app_' + uuid4().hex[:12]
        restore_name = 'nawa_phase15_qa_restore_' + uuid4().hex[:12]
        with psycopg.connect(DSN, autocommit=True) as admin:
            for name in (app_name, restore_name):
                admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
        app_params = dict(params, dbname=app_name)
        restored_params = dict(params, dbname=restore_name)
        pg_env = os.environ.copy()
        pg_env['PGPASSWORD'] = params.get('password', '')
        app_cli = dict(app_params)
        restored_cli = dict(restored_params)
        app_cli.pop('password', None)
        restored_cli.pop('password', None)
        with psycopg.connect(**app_params) as conn:
            conn.execute('''CREATE TABLE synthetic_app_jobs (job_id text PRIMARY KEY, tenant text NOT NULL,
                            state text NOT NULL, result_sha256 text)''')
            conn.execute('INSERT INTO synthetic_app_jobs VALUES (%s,%s,%s,NULL)',
                         (self.context['job_id'],self.context['tenant'],'pending'))
        with tempfile.TemporaryDirectory(prefix='nawa_p15_backup_') as directory:
            dump = Path(directory) / 'synthetic-app.dump'
            subprocess.run(['pg_dump','--format=custom','--file',str(dump),
                            '--dbname',psycopg.conninfo.make_conninfo(**app_cli)],
                           check=True,capture_output=True,timeout=60,env=pg_env)
            self.assertTrue(self.consume())
            with psycopg.connect(**app_params) as conn:
                conn.execute("UPDATE synthetic_app_jobs SET state='completed',result_sha256=%s WHERE job_id=%s",
                             (self.receipt['payload']['result_sha256'],self.context['job_id']))
            subprocess.run(['pg_restore','--no-owner','--dbname',psycopg.conninfo.make_conninfo(**restored_cli),str(dump)],
                           check=True,capture_output=True,timeout=60,env=pg_env)
            with psycopg.connect(**restored_params) as conn:
                self.assertEqual(conn.execute('SELECT state FROM synthetic_app_jobs WHERE job_id=%s',
                                              (self.context['job_id'],)).fetchone()[0], 'pending')
            with self.connect() as conn:
                ledger_state, result_hash = conn.execute(sql.SQL('SELECT state,result_sha256 FROM {}.receipts WHERE job_id=%s')
                    .format(sql.Identifier(self.schema)), (self.context['job_id'],)).fetchone()
            outcome = classify_snapshots({'state':ledger_state,'result_sha256':result_hash},
                                         {'state':'pending','result_sha256':None})
            self.assertEqual(outcome['status'], 'manual_reconciliation_required')
            self.assertEqual(outcome['automatic_action'], 'none')
            # A disposable synthetic login is created only in CI's isolated
            # cluster. Its generated password is never printed or committed.
            reader_role = 'nawa_p15_reader_' + uuid4().hex[:12]
            reader_password = secrets.token_urlsafe(32)
            with self.connect() as conn:
                conn.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION')
                             .format(sql.Identifier(reader_role),sql.Literal(reader_password)))
                conn.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}')
                             .format(sql.Identifier(params['dbname']),sql.Identifier(reader_role)))
                conn.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO {}')
                             .format(sql.Identifier(self.schema),sql.Identifier(reader_role)))
                conn.execute(sql.SQL('GRANT SELECT ON {}.receipts TO {}')
                             .format(sql.Identifier(self.schema),sql.Identifier(reader_role)))
            with psycopg.connect(**restored_params) as conn:
                conn.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}')
                             .format(sql.Identifier(restore_name),sql.Identifier(reader_role)))
                conn.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(reader_role)))
                conn.execute(sql.SQL('GRANT SELECT ON public.synthetic_app_jobs TO {}').format(sql.Identifier(reader_role)))
            def reader_connect(params):
                return psycopg.connect(**dict(params, user=reader_role, password=reader_password))
            ledger_reader = lambda: reader_connect(params)
            restored_reader = lambda: reader_connect(restored_params)
            with self.assertRaises(psycopg.OperationalError):
                psycopg.connect(**dict(params, user=reader_role, password='synthetic-wrong-password', connect_timeout=5))
            with ledger_reader() as conn:
                self.assertEqual(conn.execute('SELECT current_user').fetchone()[0], reader_role)
                self.assertFalse(conn.execute('SELECT rolsuper FROM pg_roles WHERE rolname=current_user').fetchone()[0])
            inspected = inspect(ledger_reader, restored_reader,
                                schema=self.schema,job_id=self.context['job_id'],tenant=self.context['tenant'])
            self.assertEqual(inspected['status'], 'manual_reconciliation_required')
            self.assertEqual(inspected['automatic_action'], 'none')
            other_tenant = inspect(ledger_reader, restored_reader,
                                   schema=self.schema,job_id=self.context['job_id'],tenant='synthetic-b')
            self.assertEqual(other_tenant['status'], 'missing_observation')
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with ledger_reader() as conn:
                    conn.execute(sql.SQL('UPDATE {}.receipts SET state=state WHERE false').format(sql.Identifier(self.schema)))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with ledger_reader() as conn:
                    conn.execute(sql.SQL('SELECT * FROM {}.events').format(sql.Identifier(self.schema)))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with restored_reader() as conn:
                    conn.execute('UPDATE public.synthetic_app_jobs SET state=state WHERE false')
            with psycopg.connect(**restored_params) as conn:
                self.assertEqual(conn.execute('SELECT state FROM synthetic_app_jobs WHERE job_id=%s',
                                              (self.context['job_id'],)).fetchone()[0], 'pending')
            with self.connect() as conn:
                self.assertEqual(conn.execute(sql.SQL('SELECT state FROM {}.receipts WHERE job_id=%s')
                    .format(sql.Identifier(self.schema)), (self.context['job_id'],)).fetchone()[0], 'consumed')
            self.assertFalse(self.consume())  # The separately preserved ledger remembers consumption.

    def test_inspector_fails_closed_without_exposing_database_errors(self):
        from synthetic_reconciliation_inspector import inspect
        def unavailable():
            raise OSError('sensitive synthetic connection detail')
        result = inspect(self.connect, unavailable, schema=self.schema,
                         job_id=self.context['job_id'], tenant=self.context['tenant'])
        self.assertEqual(result['status'], 'observation_unavailable')
        self.assertEqual(result['automatic_action'], 'none')
        self.assertNotIn('sensitive synthetic connection detail', str(result))

    def test_inspector_rejects_invalid_job_before_connecting(self):
        from synthetic_reconciliation_inspector import inspect
        def must_not_connect():
            raise AssertionError('Unexpected connection')
        with self.assertRaises(ValueError):
            inspect(must_not_connect, must_not_connect, schema=self.schema,
                    job_id='invalid', tenant=self.context['tenant'])

    def test_ledger_commit_before_app_commit_requires_reconciliation(self):
        from synthetic_reconciliation import classify_snapshots
        # A ledger-first design can prevent duplicate acceptance but can also
        # strand a legitimate job if the application write never commits.
        with self.connect() as conn:
            conn.execute(sql.SQL('CREATE TABLE {}.app_jobs (job_id text PRIMARY KEY, state text NOT NULL)')
                         .format(sql.Identifier(self.schema)))
            conn.execute(sql.SQL('INSERT INTO {}.app_jobs VALUES (%s,%s)').format(sql.Identifier(self.schema)),
                         (self.context['job_id'],'pending'))
        self.assertTrue(self.consume())
        with self.connect() as conn:
            state = conn.execute(sql.SQL('SELECT state FROM {}.app_jobs WHERE job_id=%s').format(sql.Identifier(self.schema)),
                                 (self.context['job_id'],)).fetchone()[0]
            ledger_state, result_hash = conn.execute(sql.SQL('SELECT state,result_sha256 FROM {}.receipts WHERE job_id=%s')
                .format(sql.Identifier(self.schema)), (self.context['job_id'],)).fetchone()
        self.assertEqual(state, 'pending')
        self.assertEqual(classify_snapshots({'state':ledger_state,'result_sha256':result_hash},
            {'state':state,'result_sha256':None})['status'], 'manual_reconciliation_required')
        self.assertFalse(self.consume())

if __name__ == '__main__':
    unittest.main()
