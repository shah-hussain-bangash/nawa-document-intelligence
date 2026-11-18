"""Disposable PostgreSQL and temporary-source integration only."""
import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

try:
    import psycopg
except ImportError:
    psycopg = None

from nawa_demo.authorization import Principal
from nawa_demo.intake_postgres import PostgresIntakeJobs
from nawa_demo.intake_scoped import ScopedIntake
from nawa_demo.intake_store import LocalIntakeStore
from nawa_demo.intake_worker import _extract_pdf
from phase13_database_snapshot import load_snapshot
from hybrid_review import retrieve_for_review

DSN = os.environ.get('NAWA_PHASE14_TEST_DSN')
ENABLED = os.environ.get('NAWA_PHASE14_DISPOSABLE') == '1'
DEMO = Path(__import__('nawa_demo').__file__).resolve().parent.parent


@unittest.skipUnless(DSN and ENABLED and psycopg, 'disposable Phase 14 PostgreSQL not configured')
class Phase13DatabaseSnapshotTests(unittest.TestCase):
    def setUp(self):
        config = psycopg.conninfo.conninfo_to_dict(DSN)
        if (config.get('host') != '127.0.0.1' or 'hostaddr' in config
                or not config.get('dbname', '').startswith('nawa_phase13_qa_')):
            raise ValueError('Disposable localhost test database required')
        self.tenant = 'qa-' + uuid4().hex
        self.other = 'qa-' + uuid4().hex
        self.issuer, self.subject = 'https://synthetic.invalid', uuid4().hex
        key = json.dumps([self.issuer,self.subject], separators=(',', ':'))
        self.principal = Principal(key, self.tenant, 'analyst')
        self.connect = lambda: psycopg.connect(DSN)
        with self.connect() as conn:
            conn.execute('INSERT INTO nawa_tenants (id) VALUES (%s),(%s)', (self.tenant,self.other))
            conn.execute('INSERT INTO nawa_identities (issuer,subject) VALUES (%s,%s)', (self.issuer,self.subject))
            conn.execute('INSERT INTO nawa_memberships (issuer,subject,tenant_id,role) VALUES (%s,%s,%s,%s)',
                         (self.issuer,self.subject,self.tenant,'analyst'))
        self.temp = TemporaryDirectory(prefix='nawa14-synthetic-')
        self.addCleanup(self.temp.cleanup)
        self.store = LocalIntakeStore(self.temp.name)
        self.intake = ScopedIntake(self.connect,self.store)
        self.jobs = PostgresIntakeJobs(self.connect)

    def add_pdf(self, sample, family, version, *, complete):
        content = (DEMO / 'samples' / 'pdf' / sample).read_bytes()
        document, created = self.intake.submit(self.principal, sample, content)
        self.assertTrue(created)
        self.jobs.link_version(self.tenant,document,family,expected_previous=version-1)
        if complete:
            with TemporaryDirectory(prefix='nawa14-extract-') as temp:
                result = _extract_pdf(content,temp)
            job, token = self.jobs.claim(self.tenant)
            self.assertEqual(self.jobs.finish(self.tenant,job,token,success=True,result=result), 'completed')
        return document

    def test_real_membership_source_and_version_recheck(self):
        family = uuid4().hex
        old = self.add_pdf('english_supplier.pdf',family,1,complete=True)
        first = load_snapshot(self.connect,self.store,self.principal)
        self.assertTrue(first['passages'])
        self.assertTrue(all(p.passage_id.startswith(old+':') and p.page > 0 for p in first['passages']))
        newer = self.add_pdf('incorrect_vat.pdf',family,2,complete=False)
        self.assertEqual(load_snapshot(self.connect,self.store,self.principal)['passages'], [])
        with self.connect() as conn:
            conn.execute("UPDATE nawa_memberships SET active=false WHERE issuer=%s AND subject=%s AND tenant_id=%s",
                         (self.issuer,self.subject,self.tenant))
        with self.assertRaises(PermissionError):
            load_snapshot(self.connect,self.store,self.principal)
        self.assertTrue(newer)

    def test_tampered_source_and_cross_tenant_membership_are_denied(self):
        document = self.add_pdf('english_supplier.pdf',uuid4().hex,1,complete=True)
        (Path(self.temp.name) / document).write_bytes(b'tampered synthetic file')
        with self.assertRaises(ValueError):
            load_snapshot(self.connect,self.store,self.principal)
        cross_tenant = Principal(self.principal.subject,self.other,'analyst')
        with self.assertRaises(PermissionError):
            load_snapshot(self.connect,self.store,cross_tenant)

    def test_membership_revocation_between_retrieval_snapshots(self):
        self.add_pdf('english_supplier.pdf',uuid4().hex,1,complete=True)
        calls = 0
        def snapshot():
            nonlocal calls
            calls += 1
            if calls == 2:
                with self.connect() as conn:
                    conn.execute("UPDATE nawa_memberships SET active=false WHERE issuer=%s AND subject=%s AND tenant_id=%s",
                                 (self.issuer,self.subject,self.tenant))
            return load_snapshot(self.connect,self.store,self.principal)
        result = retrieve_for_review('total',tenant=self.tenant,principal=self.principal.subject,
                                     load_snapshot=snapshot,embed_fn=lambda texts:[[1.0] for _ in texts])
        self.assertEqual(result, {'status':'unavailable'})


if __name__ == '__main__':
    unittest.main()

