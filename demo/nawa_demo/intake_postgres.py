"""Synthetic PostgreSQL intake operations; tenant values are not authentication."""
import hashlib
import json
import secrets
from uuid import UUID, uuid4

MAX_DOCUMENTS_PER_TENANT = 20
MAX_BYTES_PER_TENANT = 16 * 1024 * 1024


class IntakeRejected(ValueError):
    """A known rejection before a new document row was inserted."""


class PostgresIntakeJobs:
    """Connection factory must provide transactional psycopg connections.

    This is not wired to an API or identity provider. Membership enforcement,
    permissions and migration deployment are still required.
    """
    def __init__(self, connect):
        self.connect = connect

    def register(self, tenant, document_id, metadata):
        if not isinstance(tenant, str) or not tenant.strip():
            raise ValueError('Tenant is required')
        identifier = UUID(document_id)
        with self.connect() as conn:
            with conn.cursor() as cur:
                # Serialize duplicate and quota decisions for this tenant.
                cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))',
                            ('nawa-intake-quota:' + tenant,))
                cur.execute('SELECT id FROM nawa_intake_documents WHERE tenant_id=%s AND sha256=%s',
                            (tenant, metadata.sha256))
                existing = cur.fetchone()
                if existing:
                    return existing[0].hex, False
                cur.execute('''SELECT count(*), COALESCE(sum(size_bytes),0)
                    FROM nawa_intake_documents WHERE tenant_id=%s''', (tenant,))
                count, used_bytes = cur.fetchone()
                if count >= MAX_DOCUMENTS_PER_TENANT or used_bytes + metadata.size > MAX_BYTES_PER_TENANT:
                    raise IntakeRejected('Synthetic document quota reached')
                cur.execute('''INSERT INTO nawa_intake_documents (id,tenant_id,filename,sha256,size_bytes)
                    VALUES (%s,%s,%s,%s,%s) ON CONFLICT (tenant_id,sha256) DO NOTHING RETURNING id''',
                    (identifier, tenant, metadata.filename, metadata.sha256, metadata.size))
                row = cur.fetchone()
                if row is None:
                    cur.execute('SELECT id FROM nawa_intake_documents WHERE tenant_id=%s AND sha256=%s',
                                (tenant, metadata.sha256))
                    return cur.fetchone()[0].hex, False
                cur.execute('INSERT INTO nawa_intake_jobs (id,tenant_id,document_id,state) VALUES (%s,%s,%s,%s)',
                            (uuid4(), tenant, identifier, 'received'))
                return identifier.hex, True

    def claim(self, tenant, worker='synthetic-worker', *, lease_seconds=60, max_attempts=3):
        if not tenant or not worker or not 1 <= lease_seconds <= 300 or not 1 <= max_attempts <= 3:
            raise ValueError('Valid tenant, worker, lease and attempt limit are required')
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode('ascii')).hexdigest()
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute('''UPDATE nawa_intake_jobs SET state='failed', claim_token_hash=NULL,
                    lease_until=NULL, updated_at=now() WHERE tenant_id=%s AND state='processing'
                    AND lease_until <= now() AND attempts >= %s''', (tenant, max_attempts))
                cur.execute('''WITH candidate AS (
                    SELECT id FROM nawa_intake_jobs WHERE tenant_id=%s AND attempts<%s AND
                    (state IN ('received','retry-pending') OR (state='processing' AND lease_until<=now()))
                    ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1)
                    UPDATE nawa_intake_jobs j SET state='processing',attempts=j.attempts+1,
                    claim_token_hash=%s,lease_until=now()+(%s * interval '1 second'),updated_at=now()
                    FROM candidate WHERE j.id=candidate.id RETURNING j.id''',
                    (tenant, max_attempts, token_hash, lease_seconds))
                row = cur.fetchone()
                return (row[0].hex, token) if row else None

    def finish(self, tenant, job_id, token, *, result=None, success, max_attempts=3):
        if not isinstance(token, str) or not token.isascii():
            raise ValueError('Invalid claim')
        if success and not isinstance(result, dict):
            raise ValueError('Successful jobs require an object result')
        if not success and result is not None:
            raise ValueError('Failed jobs cannot contain a result')
        if not 1 <= max_attempts <= 3:
            raise ValueError('Invalid attempt limit')
        token_hash = hashlib.sha256(token.encode('ascii')).hexdigest()
        data = json.dumps(result, ensure_ascii=False, allow_nan=False) if success else None
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute('''UPDATE nawa_intake_jobs SET
                    state=CASE WHEN %s THEN 'completed' WHEN attempts>=%s THEN 'failed' ELSE 'retry-pending' END,
                    result=%s::jsonb,claim_token_hash=NULL,lease_until=NULL,updated_at=now()
                    WHERE id=%s AND tenant_id=%s AND state='processing' AND claim_token_hash=%s
                    AND lease_until>now() RETURNING state''',
                    (success, max_attempts, data, UUID(job_id), tenant, token_hash))
                row = cur.fetchone()
                if row is None:
                    raise ValueError('Job claim is unavailable or expired')
                return row[0]

    def claimed_document(self, tenant, job_id, token):
        token_hash = hashlib.sha256(token.encode('ascii')).hexdigest()
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute('''SELECT d.id,d.filename,d.sha256 FROM nawa_intake_documents d
                    JOIN nawa_intake_jobs j ON j.tenant_id=d.tenant_id AND j.document_id=d.id
                    WHERE j.tenant_id=%s AND j.id=%s AND j.state='processing'
                    AND j.claim_token_hash=%s AND j.lease_until>now()''',
                    (tenant, UUID(job_id), token_hash))
                row = cur.fetchone()
                if row is None:
                    raise ValueError('Job claim is unavailable or expired')
                return row[0].hex, row[1], row[2].strip()

    def state(self, tenant, document_id):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT state,attempts FROM nawa_intake_jobs WHERE tenant_id=%s AND document_id=%s',
                            (tenant, UUID(document_id)))
                return cur.fetchone()

    def result(self, tenant, document_id):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute('''SELECT result FROM nawa_intake_jobs
                    WHERE tenant_id=%s AND document_id=%s AND state='completed' ''',
                    (tenant, UUID(document_id)))
                row = cur.fetchone()
                return row[0] if row else None

    def recovery_snapshot(self):
        """Offline administrative inventory; not suitable for an untrusted caller."""
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id,sha256 FROM nawa_intake_documents ORDER BY id')
                return [(row[0].hex, row[1].strip()) for row in cur.fetchall()]

    def link_version(self, tenant, document_id, family_id, *, expected_previous):
        """Link an existing source to a family with optimistic version checking."""
        if not tenant or type(expected_previous) is not int or expected_previous < 0:
            raise ValueError('Invalid version request')
        family = UUID(family_id)
        document = UUID(document_id)
        with self.connect() as conn:
            with conn.cursor() as cur:
                # Serialize writers to the same tenant/family, including creation.
                cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))',
                            (tenant + ':' + family.hex,))
                cur.execute('SELECT COALESCE(MAX(version),0) FROM nawa_intake_versions WHERE tenant_id=%s AND family_id=%s',
                            (tenant, family))
                previous = cur.fetchone()[0]
                if previous != expected_previous:
                    raise ValueError('Document version changed')
                cur.execute('SELECT 1 FROM nawa_intake_documents WHERE tenant_id=%s AND id=%s',
                            (tenant, document))
                if cur.fetchone() is None:
                    raise ValueError('Document unavailable')
                cur.execute('SELECT 1 FROM nawa_intake_versions WHERE tenant_id=%s AND document_id=%s',
                            (tenant, document))
                if cur.fetchone() is not None:
                    raise ValueError('Document already has a version')
                cur.execute('''INSERT INTO nawa_intake_versions (tenant_id,family_id,version,document_id)
                    VALUES (%s,%s,%s,%s)''', (tenant, family, previous + 1, document))
                return previous + 1

    def version_history(self, tenant, family_id):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute('''SELECT version,document_id FROM nawa_intake_versions
                    WHERE tenant_id=%s AND family_id=%s ORDER BY version''', (tenant, UUID(family_id)))
                return [(row[0], row[1].hex) for row in cur.fetchall()]

