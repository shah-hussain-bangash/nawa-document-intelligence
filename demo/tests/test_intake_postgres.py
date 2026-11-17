"""Runs only against an explicitly configured disposable synthetic database."""
import os
import json
import base64
import threading
import subprocess
import sys
import shutil
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from uuid import uuid4
from pathlib import Path
from tempfile import TemporaryDirectory
from http.server import HTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

try:
    import psycopg
except ImportError:
    psycopg = None

from nawa_demo.intake_postgres import PostgresIntakeJobs
from nawa_demo.intake_validation import check_document
from nawa_demo.intake_pipeline import SyntheticIntakePipeline
from nawa_demo.intake_store import LocalIntakeStore
from nawa_demo.intake_worker import process_one
from nawa_demo.authorization import Principal
from nawa_demo.intake_scoped import ScopedIntake
from nawa_demo.dashboard import DashboardState
from nawa_demo.identity_repository import membership_by_key
from nawa_demo.protected_api import make_protected_handler
from nawa_demo.session_draft import SessionStore
from nawa_demo.intake_runtime import build_synthetic_intake
from nawa_demo.intake_migrate import apply_intake_migrations, verify_intake_migrations
from nawa_demo.migrate import migrate
from nawa_demo.phase13_qa_snapshot import snapshot

DSN = os.environ.get('NAWA_PHASE13_TEST_DSN')


@unittest.skipUnless(DSN and psycopg, 'isolated PostgreSQL test not configured')
class PostgresIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tenant = 'synthetic-' + uuid4().hex
        self.other = 'synthetic-' + uuid4().hex
        self.connect = lambda: psycopg.connect(DSN)
        with self.connect() as conn:
            conn.execute('INSERT INTO nawa_tenants (id) VALUES (%s),(%s)', (self.tenant, self.other))
        self.jobs = PostgresIntakeJobs(self.connect)

    def test_registration_dedup_and_claim_boundary(self):
        meta = check_document('عرض.txt', 'عرض سعر'.encode('utf-8'))
        document = uuid4().hex
        self.assertEqual(self.jobs.register(self.tenant, document, meta), (document, True))
        self.assertEqual(self.jobs.register(self.tenant, uuid4().hex, meta), (document, False))
        job, token = self.jobs.claim(self.tenant)
        self.assertIsNone(self.jobs.claim(self.other))
        with self.assertRaises(ValueError):
            self.jobs.finish(self.other, job, token, success=True, result={'ok': True})
        with self.assertRaises(ValueError):
            self.jobs.finish(self.tenant, job, 'wrong-token', success=True, result={'ok': True})
        with self.connect() as conn:
            stored = conn.execute('SELECT claim_token_hash FROM nawa_intake_jobs WHERE id=%s', (job,)).fetchone()[0]
        self.assertNotEqual(stored, token)
        self.assertEqual(self.jobs.finish(self.tenant, job, token, success=True, result={'ok': True}), 'completed')

    def test_concurrent_workers_claim_distinct_jobs(self):
        for content in (b'one', b'two'):
            self.jobs.register(self.tenant, uuid4().hex, check_document('synthetic.txt', content))
        with ThreadPoolExecutor(max_workers=2) as pool:
            claims = list(pool.map(lambda _: self.jobs.claim(self.tenant), range(2)))
        self.assertTrue(all(claims))
        self.assertNotEqual(claims[0][0], claims[1][0])

    def test_document_versions_preserve_previous_source_and_reject_stale_update(self):
        family = uuid4().hex
        first, second = uuid4().hex, uuid4().hex
        self.jobs.register(self.tenant, first, check_document('quote.txt', b'version one'))
        self.jobs.register(self.tenant, second, check_document('quote.txt', b'version two'))
        self.assertEqual(self.jobs.link_version(self.tenant, first, family, expected_previous=0), 1)
        self.assertEqual(self.jobs.link_version(self.tenant, second, family, expected_previous=1), 2)
        self.assertEqual(self.jobs.version_history(self.tenant, family), [(1, first), (2, second)])
        self.assertEqual(self.jobs.version_history(self.other, family), [])
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.jobs.link_version(self.tenant, first, family, expected_previous=1)

    def test_concurrent_document_versions_allow_only_one_head_update(self):
        family = uuid4().hex
        documents = [uuid4().hex, uuid4().hex]
        for index, document in enumerate(documents):
            self.jobs.register(self.tenant, document, check_document('x.txt', f'version {index}'.encode()))
        def attempt(document):
            try:
                return self.jobs.link_version(self.tenant, document, family, expected_previous=0)
            except ValueError:
                return 'stale'
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(attempt, documents))
        self.assertEqual(sorted(map(str, outcomes)), ['1', 'stale'])
        self.assertEqual(len(self.jobs.version_history(self.tenant, family)), 1)

    def test_retries_and_expired_claim(self):
        self.jobs.register(self.tenant, uuid4().hex, check_document('x.txt', b'retry'))
        job, old_token = self.jobs.claim(self.tenant)
        with self.connect() as conn:
            conn.execute("UPDATE nawa_intake_jobs SET lease_until=now()-interval '1 second' WHERE id=%s", (job,))
        new_job, new_token = self.jobs.claim(self.tenant)
        self.assertEqual(job, new_job)
        with self.assertRaises(ValueError):
            self.jobs.finish(self.tenant, job, old_token, success=True, result={'ok': True})
        self.assertEqual(self.jobs.finish(self.tenant, job, new_token, success=False), 'retry-pending')
        _, final_token = self.jobs.claim(self.tenant)
        self.assertEqual(self.jobs.finish(self.tenant, job, final_token, success=False), 'failed')
        self.assertIsNone(self.jobs.claim(self.tenant))

    def test_synthetic_file_to_result_through_postgres(self):
        with TemporaryDirectory() as folder:
            store = LocalIntakeStore(folder)
            content = (Path(__file__).resolve().parents[1] / 'samples/arabic_quote.txt').read_bytes()
            pipeline = SyntheticIntakePipeline(store, self.jobs)
            document, created = pipeline.submit(self.tenant, 'arabic.txt', content)
            self.assertTrue(created)
            self.assertEqual(pipeline.submit(self.tenant, 'copy.txt', content), (document, False))
            self.assertEqual(process_one(self.jobs, store, self.tenant), 'completed')
            self.assertEqual(self.jobs.state(self.tenant, document), ('completed', 1))
            self.assertEqual(self.jobs.result(self.tenant, document)['total'], '945.00')
            self.assertIsNone(self.jobs.result(self.other, document))

    def test_scoped_access_rechecks_roles_tenant_and_revocation(self):
        issuer, subject = 'https://synthetic-issuer', uuid4().hex
        identity_key = json.dumps([issuer, subject], separators=(',', ':'))
        with self.connect() as conn:
            conn.execute('INSERT INTO nawa_identities (issuer,subject) VALUES (%s,%s)', (issuer, subject))
            conn.execute('INSERT INTO nawa_memberships (issuer,subject,tenant_id,role) VALUES (%s,%s,%s,%s)',
                         (issuer, subject, self.tenant, 'analyst'))
            conn.execute('INSERT INTO nawa_memberships (issuer,subject,tenant_id,role) VALUES (%s,%s,%s,%s)',
                         (issuer, subject, self.other, 'viewer'))
        analyst = Principal(identity_key, self.tenant, 'analyst')
        viewer = Principal(identity_key, self.other, 'viewer')
        with TemporaryDirectory() as folder:
            store = LocalIntakeStore(folder)
            service = ScopedIntake(self.connect, store)
            content = (Path(__file__).resolve().parents[1] / 'samples/english_quote.txt').read_bytes()
            document, _ = service.submit(analyst, 'english.txt', content)
            family = uuid4().hex
            self.assertEqual(service.link_version(analyst, document, family, expected_previous=0), 1)
            self.assertEqual(service.version_history(viewer, family), [])
            with self.assertRaises(PermissionError):
                service.submit(viewer, 'no.txt', content)
            with self.assertRaises(PermissionError):
                service.link_version(viewer, document, family, expected_previous=0)
            self.assertIsNone(service.state(viewer, document))
            self.assertEqual(process_one(self.jobs, store, self.tenant), 'completed')
            self.assertEqual(service.result(analyst, document)['total'], '1050.00')
            promoted = service.promote(analyst, document)
            self.assertTrue(promoted['created'])
            self.assertEqual(promoted['quotation']['total'], '1050.00')
            repeated = service.promote(analyst, document)
            self.assertFalse(repeated['created'])
            self.assertEqual(repeated['id'], promoted['id'])
            with self.assertRaises(PermissionError):
                service.promote(viewer, document)
            self.assertIsNone(service.result(viewer, document))
            with self.connect() as conn:
                conn.execute('UPDATE nawa_memberships SET active=false WHERE issuer=%s AND subject=%s AND tenant_id=%s',
                             (issuer, subject, self.tenant))
            with self.assertRaises(PermissionError):
                service.result(analyst, document)
            with self.assertRaises(PermissionError):
                service.version_history(analyst, family)
            with self.assertRaises(PermissionError):
                service.promote(analyst, document)
            with self.assertRaises(PermissionError):
                service.submit(analyst, 'again.txt', content)
            self.assertEqual(len(list(Path(folder).iterdir())), 1)

    def test_scoped_uncertain_commit_preserves_committed_file(self):
        issuer, subject = 'https://synthetic-issuer', uuid4().hex
        identity_key = json.dumps([issuer, subject], separators=(',', ':'))
        with self.connect() as conn:
            conn.execute('INSERT INTO nawa_identities (issuer,subject) VALUES (%s,%s)', (issuer, subject))
            conn.execute('INSERT INTO nawa_memberships (issuer,subject,tenant_id,role) VALUES (%s,%s,%s,%s)',
                         (issuer, subject, self.tenant, 'analyst'))

        @contextmanager
        def uncertain_connection():
            with self.connect() as conn:
                yield conn
            raise RuntimeError('simulated error after commit')

        with TemporaryDirectory() as folder:
            store = LocalIntakeStore(folder)
            service = ScopedIntake(uncertain_connection, store)
            principal = Principal(identity_key, self.tenant, 'analyst')
            with self.assertRaisesRegex(RuntimeError, 'after commit'):
                service.submit(principal, 'x.txt', b'synthetic')
            stored = list(Path(folder).iterdir())
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0].read_bytes(), b'synthetic')
            self.assertEqual(self.jobs.state(self.tenant, stored[0].name), ('received', 0))

    def test_concurrent_promotions_create_one_quotation(self):
        issuer, subject = 'https://synthetic-issuer', uuid4().hex
        identity_key = json.dumps([issuer, subject], separators=(',', ':'))
        with self.connect() as conn:
            conn.execute('INSERT INTO nawa_identities (issuer,subject) VALUES (%s,%s)', (issuer, subject))
            conn.execute('INSERT INTO nawa_memberships (issuer,subject,tenant_id,role) VALUES (%s,%s,%s,%s)',
                         (issuer, subject, self.tenant, 'analyst'))
        with TemporaryDirectory() as folder:
            store = LocalIntakeStore(folder)
            service = ScopedIntake(self.connect, store)
            principal = Principal(identity_key, self.tenant, 'analyst')
            content = (Path(__file__).resolve().parents[1] / 'samples/english_quote.txt').read_bytes()
            document, _ = service.submit(principal, 'english.txt', content)
            self.assertEqual(process_one(self.jobs, store, self.tenant), 'completed')
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda _: service.promote(principal, document), range(4)))
            self.assertEqual(sum(item['created'] for item in results), 1)
            self.assertEqual(len({item['id'] for item in results}), 1)
            with self.connect() as conn:
                count = conn.execute('SELECT count(*) FROM nawa_quotation_tenants WHERE tenant_id=%s',
                                     (self.tenant,)).fetchone()[0]
            self.assertEqual(count, 1)

    def test_promotion_refuses_changed_source_before_and_after_creation(self):
        issuer, subject = 'https://synthetic-issuer', uuid4().hex
        identity_key = json.dumps([issuer, subject], separators=(',', ':'))
        with self.connect() as conn:
            conn.execute('INSERT INTO nawa_identities (issuer,subject) VALUES (%s,%s)', (issuer, subject))
            conn.execute('INSERT INTO nawa_memberships (issuer,subject,tenant_id,role) VALUES (%s,%s,%s,%s)',
                         (issuer, subject, self.tenant, 'analyst'))
        with TemporaryDirectory() as folder:
            store = LocalIntakeStore(folder)
            service = ScopedIntake(self.connect, store)
            principal = Principal(identity_key, self.tenant, 'analyst')
            content = (Path(__file__).resolve().parents[1] / 'samples/english_quote.txt').read_bytes()
            document, _ = service.submit(principal, 'english.txt', content)
            self.assertEqual(process_one(self.jobs, store, self.tenant), 'completed')
            source = Path(folder) / document
            source.write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError, 'integrity'):
                service.promote(principal, document)
            with self.connect() as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM nawa_quotation_tenants WHERE tenant_id=%s',
                                              (self.tenant,)).fetchone()[0], 0)
            source.write_bytes(content)
            self.assertTrue(service.promote(principal, document)['created'])
            source.write_bytes(b'tampered again')
            with self.assertRaisesRegex(ValueError, 'integrity'):
                service.promote(principal, document)

    def test_http_synthetic_session_to_postgres_result(self):
        issuer, subject = 'https://synthetic-issuer', uuid4().hex
        identity_key = json.dumps([issuer, subject], separators=(',', ':'))
        with self.connect() as conn:
            conn.execute('INSERT INTO nawa_identities (issuer,subject) VALUES (%s,%s)', (issuer, subject))
            conn.execute('INSERT INTO nawa_memberships (issuer,subject,tenant_id,role) VALUES (%s,%s,%s,%s)',
                         (issuer, subject, self.tenant, 'analyst'))

        def lookup(key, tenant):
            with self.connect() as conn:
                return membership_by_key(conn, identity_key=key, tenant=tenant)

        sessions = SessionStore(lookup)
        tokens = sessions.issue(identity_key, self.tenant)
        with TemporaryDirectory() as folder:
            store = LocalIntakeStore(folder)
            handler = make_protected_handler(None, sessions, DashboardState(), intake=ScopedIntake(self.connect, store))
            server = HTTPServer(('127.0.0.1', 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                content = (Path(__file__).resolve().parents[1] / 'samples/english_quote.txt').read_bytes()
                body = json.dumps({'filename': 'english.txt', 'content_base64': base64.b64encode(content).decode()}).encode()
                base = f'http://127.0.0.1:{server.server_port}'
                headers = {'Content-Type': 'application/json', 'Origin': 'http://127.0.0.1:8765',
                           'Cookie': 'nawa_session=' + tokens['session'], 'X-NAWA-CSRF': tokens['csrf']}
                with urlopen(Request(base + '/api/intake/submit', data=body, headers=headers), timeout=10) as response:
                    document = json.load(response)['id']
                version_payload = json.dumps({'id': document, 'expected_previous': 0}).encode()
                with urlopen(Request(base + '/api/intake/version', data=version_payload, headers=headers), timeout=10) as response:
                    version = json.load(response)
                self.assertEqual(version['version'], 1)
                with urlopen(Request(base + '/api/intake/versions?family=' + version['family_id'],
                                     headers={'Cookie': headers['Cookie']}), timeout=10) as response:
                    self.assertEqual(json.load(response)['versions'], [{'version': 1, 'id': document}])
                self.assertEqual(process_one(self.jobs, store, self.tenant), 'completed')
                with urlopen(Request(base + '/api/intake/result?id=' + document, headers={'Cookie': headers['Cookie']}), timeout=10) as response:
                    self.assertEqual(json.load(response)['result']['total'], '1050.00')
                promotion = json.dumps({'id':document}).encode()
                with urlopen(Request(base + '/api/intake/promote', data=promotion, headers=headers), timeout=10) as response:
                    first = json.load(response)
                self.assertTrue(first['created'])
                with urlopen(Request(base + '/api/intake/promote', data=promotion, headers=headers), timeout=10) as response:
                    repeated = json.load(response)
                self.assertFalse(repeated['created'])
                self.assertEqual(first['id'], repeated['id'])
                arabic = (Path(__file__).resolve().parents[1] / 'samples/arabic_quote.txt').read_bytes()
                batch = {'files': [{'filename': 'duplicate.txt', 'content_base64': base64.b64encode(content).decode()},
                                   {'filename': 'arabic.txt', 'content_base64': base64.b64encode(arabic).decode()},
                                   {'filename': 'invalid.txt', 'content_base64': '%%%'}]}
                with urlopen(Request(base + '/api/intake/batch', data=json.dumps(batch).encode(), headers=headers), timeout=10) as response:
                    batch_results = json.load(response)['files']
                self.assertEqual(batch_results[0], {'id': document, 'created': False})
                self.assertTrue(batch_results[1]['created'])
                self.assertEqual(batch_results[2], {'error': 'Invalid or unsupported file'})
                self.assertEqual(process_one(self.jobs, store, self.tenant), 'completed')
                self.assertEqual(self.jobs.result(self.tenant, batch_results[1]['id'])['total'], '945.00')
                with self.assertRaises(HTTPError) as denied:
                    urlopen(base + '/api/intake/status?id=' + document, timeout=10)
                self.assertEqual(denied.exception.code, 403)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_configured_runtime_and_one_shot_worker(self):
        issuer, subject = 'https://synthetic-issuer', uuid4().hex
        identity_key = json.dumps([issuer, subject], separators=(',', ':'))
        with self.connect() as conn:
            conn.execute('INSERT INTO nawa_identities (issuer,subject) VALUES (%s,%s)', (issuer, subject))
            conn.execute('INSERT INTO nawa_memberships (issuer,subject,tenant_id,role) VALUES (%s,%s,%s,%s)',
                         (issuer, subject, self.tenant, 'analyst'))
        principal = Principal(identity_key, self.tenant, 'analyst')
        with TemporaryDirectory() as folder:
            service = build_synthetic_intake(self.connect, str(Path(folder).resolve()))
            content = (Path(__file__).resolve().parents[1] / 'samples/english_quote.txt').read_bytes()
            document, created = service.submit(principal, 'english.txt', content)
            self.assertTrue(created)
            params = psycopg.conninfo.conninfo_to_dict(DSN)
            env = os.environ.copy()
            env.update({'NAWA_INTAKE':'synthetic', 'NAWA_AUTH':'oidc', 'NAWA_TENANT_ID':self.tenant,
                        'NAWA_INTAKE_DIR':str(Path(folder).resolve()), 'POSTGRES_HOST':params['host'],
                        'POSTGRES_PORT':params['port'], 'POSTGRES_DB':params['dbname'],
                        'POSTGRES_USER':params['user'], 'POSTGRES_PASSWORD':params.get('password', 'synthetic-unused')})
            worker = subprocess.run([sys.executable, '-m', 'nawa_demo.intake_worker_cli'],
                                    env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(worker.returncode, 0, worker.stderr)
            self.assertIn('completed', worker.stdout)
            self.assertEqual(service.result(principal, document)['total'], '1050.00')

    def test_quiesced_database_and_file_backup_restore(self):
        # This uses only the disposable local cluster created by the test harness.
        params = psycopg.conninfo.conninfo_to_dict(DSN)
        pg_bin = Path(r'C:\Program Files\PostgreSQL\18\bin')
        def pg_tool(name):
            return shutil.which(name) or str(pg_bin / (name + '.exe'))
        restore_name = 'nawa_restore_' + uuid4().hex[:12]
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        common = ['-h', params['host'], '-p', params['port'], '-U', params['user']]
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'source')
            content = (Path(__file__).resolve().parents[1] / 'samples/arabic_quote.txt').read_bytes()
            document, _ = SyntheticIntakePipeline(store, self.jobs).submit(self.tenant, 'arabic.txt', content)
            self.assertEqual(process_one(self.jobs, store, self.tenant), 'completed')
            digest = check_document('arabic.txt', content).sha256

            # No intake or worker writes occur while the two snapshots are made.
            dump = root / 'synthetic.dump'
            subprocess.run([pg_tool('pg_dump'), *common, '-Fc', '-f', str(dump), params['dbname']],
                           check=True, capture_output=True, creationflags=flags)
            shutil.copytree(store.directory, root / 'backup-files')
            subprocess.run([pg_tool('createdb'), *common, restore_name],
                           check=True, capture_output=True, creationflags=flags)
            subprocess.run([pg_tool('pg_restore'), *common, '-d', restore_name, '--no-owner', str(dump)],
                           check=True, capture_output=True, creationflags=flags)
            restored_params = dict(params, dbname=restore_name)
            restored = PostgresIntakeJobs(lambda: psycopg.connect(**restored_params))
            restored_store = LocalIntakeStore(root / 'backup-files')
            self.assertEqual(restored.result(self.tenant, document)['total'], '945.00')
            self.assertEqual(restored_store.read_verified(document, digest), content)

    def test_explicit_intake_migration_is_idempotent_and_detects_changed_history(self):
        name = 'nawa_phase13_qa_' + uuid4().hex[:12]
        params = psycopg.conninfo.conninfo_to_dict(DSN)
        with psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute(psycopg.sql.SQL('CREATE DATABASE {}').format(psycopg.sql.Identifier(name)))
        params['dbname'] = name
        with psycopg.connect(**params) as conn:
            migrate(conn)
            apply_intake_migrations(conn)
            apply_intake_migrations(conn)
            verify_intake_migrations(conn)
            self.assertEqual(conn.execute('SELECT count(*) FROM nawa_intake_schema_migrations').fetchone()[0], 1)
            self.assertIsNotNone(conn.execute("SELECT to_regclass('nawa_intake_versions')").fetchone()[0])
            conn.execute("UPDATE nawa_intake_schema_migrations SET checksum='altered'")
            conn.commit()
            with self.assertRaisesRegex(ValueError, 'history mismatch'):
                verify_intake_migrations(conn)
            with self.assertRaisesRegex(RuntimeError, 'history mismatch'):
                apply_intake_migrations(conn)

    def test_qa_snapshot_checks_result_and_source_integrity(self):
        with self.connect() as conn:
            conn.execute("INSERT INTO nawa_tenants(id) VALUES ('tenant-a') ON CONFLICT DO NOTHING")
        with TemporaryDirectory() as folder:
            store = LocalIntakeStore(folder)
            content = (Path(__file__).resolve().parents[1] / 'samples/english_quote.txt').read_bytes() + b'\n# qa-test\n'
            doc, _ = SyntheticIntakePipeline(store, self.jobs).submit('tenant-a', 'synthetic.txt', content)
            self.assertEqual(process_one(self.jobs, store, 'tenant-a'), 'completed')
            result = snapshot(self.connect, folder)
            self.assertEqual((result['document_id'], result['total']), (doc, '1050.00'))
            (Path(folder) / doc).write_bytes(b'changed')
            with self.assertRaises(ValueError):
                snapshot(self.connect, folder)

