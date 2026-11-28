"""Read-only observations for disposable Phase 15 QA; not an operator tool."""
import re
from psycopg import sql
from synthetic_pg_receipt_ledger import _guard
from synthetic_reconciliation import classify_snapshots

_ID = re.compile(r'[0-9a-f]{32}\Z')

def inspect(ledger_connect, app_connect, *, schema, job_id, tenant):
    """Read separately; no cross-database atomic snapshot or automatic action."""
    if (not isinstance(job_id, str) or not _ID.fullmatch(job_id) or
            not isinstance(tenant, str) or not tenant or len(tenant) > 100):
        raise ValueError('Invalid synthetic job context')
    try:
        with ledger_connect() as conn:
            conn.execute('SET TRANSACTION READ ONLY')
            _guard(conn, schema)
            if conn.execute('SHOW transaction_read_only').fetchone()[0] != 'on':
                raise ValueError('Read-only transaction required')
            row = conn.execute(sql.SQL('''SELECT state,result_sha256 FROM {}.receipts
                               WHERE job_id=%s AND tenant=%s''').format(sql.Identifier(schema)),
                               (job_id,tenant)).fetchone()
            ledger = {'state':row[0], 'result_sha256':row[1]} if row else None
        with app_connect() as conn:
            conn.execute('SET TRANSACTION READ ONLY')
            database = conn.execute('SELECT current_database()').fetchone()[0]
            if not database.startswith('nawa_phase15_qa_'):
                raise ValueError('A disposable Phase 15 QA database is required')
            if conn.execute('SHOW transaction_read_only').fetchone()[0] != 'on':
                raise ValueError('Read-only transaction required')
            row = conn.execute('''SELECT state,result_sha256 FROM public.synthetic_app_jobs
                                  WHERE job_id=%s AND tenant=%s''', (job_id,tenant)).fetchone()
            application = {'state':row[0], 'result_sha256':row[1]} if row else None
        return classify_snapshots(ledger, application)
    except Exception:
        # Do not leak connection strings, credentials or database errors.
        return {'status':'observation_unavailable', 'automatic_action':'none',
                'human_review_required':True,
                'scope':'Synthetic observations unavailable; no changes made.'}
