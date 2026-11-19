"""Disposable SQLite receipt-consumption experiment; not NAWA persistence."""
import re
import sqlite3
from contextlib import closing
from synthetic_worker_receipt import verify_receipt

_ID = re.compile(r'[0-9a-f]{32}\Z')
_HASH = re.compile(r'[0-9a-f]{64}\Z')
_KEY_ID = re.compile(r'[a-zA-Z0-9_-]{1,32}\Z')

def initialize(path):
    with closing(sqlite3.connect(path, timeout=10)) as conn, conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS synthetic_receipts (
            job_id TEXT PRIMARY KEY, tenant TEXT NOT NULL, document_id TEXT NOT NULL,
            source_sha256 TEXT NOT NULL, key_id TEXT NOT NULL,
            state TEXT NOT NULL CHECK (state IN ('pending', 'consumed')),
            receipt_mac TEXT, result_sha256 TEXT,
            CHECK ((state='pending' AND receipt_mac IS NULL AND result_sha256 IS NULL)
                OR (state='consumed' AND receipt_mac IS NOT NULL AND result_sha256 IS NOT NULL)))''')
        conn.execute('''CREATE TABLE IF NOT EXISTS synthetic_receipt_events (
            job_id TEXT PRIMARY KEY REFERENCES synthetic_receipts(job_id),
            event_type TEXT NOT NULL CHECK (event_type='receipt_consumed'),
            result_sha256 TEXT NOT NULL)''')

def register(path, *, job_id, tenant, document_id, source_sha256, key_id):
    """Register context supplied by the trusted test harness, not an HTTP client."""
    if (not isinstance(job_id, str) or not _ID.fullmatch(job_id) or
        not isinstance(document_id, str) or not _ID.fullmatch(document_id) or
        not isinstance(tenant, str) or not tenant or len(tenant) > 100 or
        not isinstance(source_sha256, str) or not _HASH.fullmatch(source_sha256) or
        not isinstance(key_id, str) or not _KEY_ID.fullmatch(key_id)):
        raise ValueError('Invalid synthetic job context')
    with closing(sqlite3.connect(path, timeout=10)) as conn, conn:
        conn.execute('INSERT INTO synthetic_receipts VALUES (?,?,?,?,?,\'pending\',NULL,NULL)',
                     (job_id, tenant, document_id, source_sha256, key_id))

def consume(path, *, job_id, tenant, receipt, result, keys):
    """Verify and consume once in one SQLite transaction; keys stay in memory."""
    with closing(sqlite3.connect(path, timeout=10)) as conn, conn:
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('''SELECT document_id,source_sha256,key_id,state
                              FROM synthetic_receipts WHERE job_id=? AND tenant=?''',
                           (job_id, tenant)).fetchone()
        if row is None or row[3] != 'pending':
            return False
        document_id, source_sha256, key_id, _ = row
        key = keys.get(key_id)
        if not verify_receipt(receipt, key, tenant=tenant, document_id=document_id,
                              job_id=job_id, source_sha256=source_sha256, result=result, key_id=key_id):
            return False
        result_sha256 = receipt['payload']['result_sha256']
        changed = conn.execute('''UPDATE synthetic_receipts SET state='consumed',receipt_mac=?,result_sha256=?
                                  WHERE job_id=? AND tenant=? AND state='pending' ''',
                               (receipt['mac_sha256'], result_sha256, job_id, tenant)).rowcount
        if changed != 1:
            return False
        conn.execute('INSERT INTO synthetic_receipt_events VALUES (?,\'receipt_consumed\',?)',
                     (job_id, result_sha256))
        return True
