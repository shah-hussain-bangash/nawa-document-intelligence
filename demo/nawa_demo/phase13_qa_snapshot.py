"""Read-only persistence check for the dedicated synthetic Phase 13 QA."""
import json
import hashlib
import os
from pathlib import Path

from .intake_migrate import verify_intake_migrations
from .intake_store import LocalIntakeStore
from .review import inspect


def snapshot(connect, directory):
    with connect() as conn:
        verify_intake_migrations(conn)
        row = conn.execute('''SELECT d.id,d.sha256,j.state,j.result,p.quotation_id,r.revision,r.ledger
            FROM nawa_intake_documents d JOIN nawa_intake_jobs j
              ON j.tenant_id=d.tenant_id AND j.document_id=d.id
            JOIN nawa_intake_promotions p ON p.tenant_id=d.tenant_id AND p.document_id=d.id
            JOIN nawa_reviews r ON r.quotation_id=p.quotation_id
            WHERE d.tenant_id=%s AND d.filename=%s AND j.state='completed'
            ORDER BY d.created_at DESC,d.id DESC LIMIT 1''', ('tenant-a', 'synthetic.txt')).fetchone()
    if row is None or row[3].get('total') != '1050.00':
        raise ValueError('Synthetic QA result unavailable')
    review = inspect(row[6])
    if (review['status'] != 'approved' or review['revision'] != 2 or row[5] != 2
            or review['source_evidence'] != row[3].get('evidence')):
        raise ValueError('Synthetic QA review or source evidence unavailable')
    document_id, digest = row[0].hex, row[1].strip()
    content = LocalIntakeStore(directory).read_verified(document_id, digest)
    if not content or b'qa-' not in content:
        raise ValueError('Synthetic QA source unavailable')
    evidence = json.dumps(review['source_evidence'], sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return {'document_id': document_id, 'sha256': digest, 'state': row[2], 'total': row[3]['total'],
            'quotation_id':row[4], 'review_status':review['status'], 'review_revision':review['revision'],
            'review_hash':review['last_hash'], 'evidence_sha256':hashlib.sha256(evidence).hexdigest()}


def main():
    if (os.environ.get('NAWA_INTAKE') != 'synthetic' or os.environ.get('NAWA_AUTH') != 'oidc'
            or os.environ.get('POSTGRES_DB') != 'nawa_phase13_qa_demo'
            or os.environ.get('NAWA_INTAKE_DIR') != '/intake'):
        raise ValueError('Dedicated synthetic Phase 13 QA configuration required')
    import psycopg
    def connect():
        return psycopg.connect(host=os.environ['POSTGRES_HOST'], dbname=os.environ['POSTGRES_DB'],
                               user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'],
                               connect_timeout=5)
    print(json.dumps(snapshot(connect, Path('/intake')), sort_keys=True))


if __name__ == '__main__':
    main()

