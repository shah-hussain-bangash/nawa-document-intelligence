"""Disposable PostgreSQL receipt experiment; not NAWA intake or production."""
import re
from psycopg import sql
from synthetic_worker_receipt import verify_receipt

_SCHEMA = re.compile(r'nawa_p15_[0-9a-f]{32}\Z')

def _guard(conn, schema):
    if not isinstance(schema, str) or not _SCHEMA.fullmatch(schema):
        raise ValueError('A unique synthetic Phase 15 schema is required')
    name = conn.execute('SELECT current_database()').fetchone()[0]
    if not name.startswith('nawa_phase15_qa_'):
        raise ValueError('A disposable Phase 15 QA database is required')

def initialize(connect, schema):
    with connect() as conn:
        _guard(conn, schema)
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        conn.execute(sql.SQL('''CREATE TABLE {}.receipts (
            job_id text PRIMARY KEY, tenant text NOT NULL, document_id text NOT NULL,
            source_sha256 text NOT NULL, key_id text NOT NULL,
            state text NOT NULL CHECK (state IN ('pending','consumed')),
            result_sha256 text, receipt_mac text,
            CHECK ((state='pending' AND result_sha256 IS NULL AND receipt_mac IS NULL)
              OR (state='consumed' AND result_sha256 IS NOT NULL AND receipt_mac IS NOT NULL)))''').format(sql.Identifier(schema)))
        conn.execute(sql.SQL('''CREATE TABLE {}.events (
            job_id text PRIMARY KEY REFERENCES {}.receipts(job_id),
            event_type text NOT NULL CHECK (event_type='receipt_consumed'),
            result_sha256 text NOT NULL)''').format(sql.Identifier(schema),sql.Identifier(schema)))

def register(connect, schema, *, job_id, tenant, document_id, source_sha256, key_id):
    """Context is supplied by the synthetic test harness, not an HTTP client."""
    with connect() as conn:
        _guard(conn, schema)
        conn.execute(sql.SQL('INSERT INTO {}.receipts VALUES (%s,%s,%s,%s,%s,\'pending\',NULL,NULL)')
                     .format(sql.Identifier(schema)), (job_id,tenant,document_id,source_sha256,key_id))

def consume(connect, schema, *, job_id, tenant, receipt, result, keys):
    """Lock a synthetic job, verify its receipt, and atomically record an event."""
    with connect() as conn:
        _guard(conn, schema)
        row = conn.execute(sql.SQL('''SELECT document_id,source_sha256,key_id,state
                FROM {}.receipts WHERE job_id=%s AND tenant=%s FOR UPDATE''').format(sql.Identifier(schema)),
                (job_id,tenant)).fetchone()
        if row is None or row[3] != 'pending':
            return False
        document, source, key_id, _ = row
        if not verify_receipt(receipt, keys.get(key_id), tenant=tenant, document_id=document,
                              job_id=job_id, source_sha256=source, result=result, key_id=key_id):
            return False
        result_hash = receipt['payload']['result_sha256']
        conn.execute(sql.SQL('''UPDATE {}.receipts SET state='consumed',result_sha256=%s,receipt_mac=%s
                      WHERE job_id=%s AND tenant=%s''').format(sql.Identifier(schema)),
                     (result_hash,receipt['mac_sha256'],job_id,tenant))
        conn.execute(sql.SQL('INSERT INTO {}.events VALUES (%s,\'receipt_consumed\',%s)')
                     .format(sql.Identifier(schema)), (job_id,result_hash))
        return True
