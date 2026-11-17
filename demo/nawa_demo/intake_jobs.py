"""Isolated SQLite job prototype for synthetic data; not the production database."""
import sqlite3
import time
import json
from contextlib import contextmanager
from uuid import uuid4


class IntakeJobs:
    """Persist job states locally. Caller-supplied tenants are not authentication."""
    def __init__(self, path):
        self.path = str(path)
        with self._connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, tenant TEXT NOT NULL, filename TEXT NOT NULL,
                    sha256 TEXT NOT NULL, size INTEGER NOT NULL,
                    UNIQUE (tenant, sha256)
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, document_id TEXT NOT NULL UNIQUE REFERENCES documents(id),
                    state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                    worker TEXT, lease_until REAL, result_json TEXT
                );
            ''')

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            db.execute('PRAGMA foreign_keys = ON')
            with db:
                yield db
        finally:
            db.close()

    def register(self, tenant, document_id, metadata):
        if not isinstance(tenant, str) or not tenant.strip():
            raise ValueError('Tenant is required')
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT id FROM documents WHERE tenant=? AND sha256=?',
                                  (tenant, metadata.sha256)).fetchone()
            if existing:
                return existing[0], False
            db.execute('INSERT INTO documents VALUES (?, ?, ?, ?, ?)',
                       (document_id, tenant, metadata.filename, metadata.sha256, metadata.size))
            db.execute('INSERT INTO jobs (id, document_id, state) VALUES (?, ?, ?)',
                       (uuid4().hex, document_id, 'received'))
            return document_id, True

    def claim(self, tenant, worker, *, lease_seconds=60, max_attempts=3, now=None):
        if not tenant or not worker or lease_seconds <= 0 or max_attempts < 1:
            raise ValueError('Valid tenant, worker, lease and attempt limit are required')
        now = time.time() if now is None else now
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('''UPDATE jobs SET state='failed', worker=NULL, lease_until=NULL
                WHERE state='processing' AND lease_until <= ? AND attempts >= ?
                AND document_id IN (SELECT id FROM documents WHERE tenant=?)''',
                       (now, max_attempts, tenant))
            row = db.execute('''SELECT jobs.id FROM jobs JOIN documents ON documents.id=jobs.document_id
                WHERE documents.tenant=? AND jobs.attempts < ? AND
                (jobs.state IN ('received', 'retry-pending') OR
                 (jobs.state='processing' AND jobs.lease_until <= ?))
                ORDER BY jobs.rowid LIMIT 1''', (tenant, max_attempts, now)).fetchone()
            if row is None:
                return None
            claim_token = uuid4().hex
            db.execute("UPDATE jobs SET state='processing', attempts=attempts+1, worker=?, lease_until=? WHERE id=?",
                       (claim_token, now + lease_seconds, row[0]))
            return row[0], claim_token

    def finish(self, tenant, job_id, claim_token, *, success, result=None, max_attempts=3, now=None):
        now = time.time() if now is None else now
        if result is not None and not success:
            raise ValueError('A failed job cannot contain a result')
        result_json = json.dumps(result, ensure_ascii=False, allow_nan=False) if result is not None else None
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('''SELECT jobs.attempts FROM jobs JOIN documents ON documents.id=jobs.document_id
                WHERE jobs.id=? AND documents.tenant=? AND jobs.state='processing'
                AND jobs.worker=? AND jobs.lease_until > ?''', (job_id, tenant, claim_token, now)).fetchone()
            if row is None:
                raise ValueError('Job claim is unavailable or expired')
            state = 'completed' if success else ('failed' if row[0] >= max_attempts else 'retry-pending')
            db.execute('UPDATE jobs SET state=?, result_json=?, worker=NULL, lease_until=NULL WHERE id=?',
                       (state, result_json, job_id))
            return state

    def claimed_document(self, tenant, job_id, claim_token, *, now=None):
        now = time.time() if now is None else now
        with self._connect() as db:
            row = db.execute('''SELECT documents.id, documents.filename, documents.sha256
                FROM documents JOIN jobs ON jobs.document_id=documents.id
                WHERE documents.tenant=? AND jobs.id=? AND jobs.state='processing'
                AND jobs.worker=? AND jobs.lease_until > ?''',
                (tenant, job_id, claim_token, now)).fetchone()
            if row is None:
                raise ValueError('Job claim is unavailable or expired')
            return row

    def result(self, tenant, document_id):
        with self._connect() as db:
            row = db.execute('''SELECT jobs.result_json FROM jobs JOIN documents
                ON documents.id=jobs.document_id WHERE documents.tenant=? AND documents.id=?
                AND jobs.state='completed' ''', (tenant, document_id)).fetchone()
            return json.loads(row[0]) if row and row[0] is not None else None

    def state(self, tenant, document_id):
        with self._connect() as db:
            row = db.execute('''SELECT jobs.state, jobs.attempts FROM jobs JOIN documents
                ON documents.id=jobs.document_id WHERE documents.tenant=? AND documents.id=?''',
                             (tenant, document_id)).fetchone()
            return row

    def recovery_snapshot(self):
        """List references for an offline maintenance check, not a user API."""
        with self._connect() as db:
            return db.execute('SELECT id, sha256 FROM documents ORDER BY id').fetchall()
