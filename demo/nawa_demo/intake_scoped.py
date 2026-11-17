"""Draft server-side intake boundary; no HTTP endpoint is connected."""
from contextlib import nullcontext
import json
from uuid import UUID, uuid4

from .authorization import Principal, authorized
from .identity_repository import membership_by_key
from .intake_postgres import IntakeRejected, PostgresIntakeJobs


class ScopedIntake:
    """Use only principals resolved from an authenticated server-side session."""
    def __init__(self, connect, store):
        self.connect = connect
        self.store = store

    @staticmethod
    def _require(principal, action):
        if not isinstance(principal, Principal) or not authorized(principal, action, tenant=principal.tenant):
            raise PermissionError('Request denied')

    @staticmethod
    def _recheck(conn, principal, action):
        current = membership_by_key(conn, identity_key=principal.subject, tenant=principal.tenant, lock=True)
        if current != principal or not authorized(current, action, tenant=principal.tenant):
            raise PermissionError('Request denied')

    def submit(self, principal, filename, content):
        self._require(principal, 'load')
        document_id, metadata = self.store.save(filename, content)
        registration_attempted = False
        try:
            with self.connect() as conn:
                self._recheck(conn, principal, 'load')
                jobs = PostgresIntakeJobs(lambda: nullcontext(conn))
                registration_attempted = True
                registered, created = jobs.register(principal.tenant, document_id, metadata)
        except IntakeRejected:
            # This explicit rejection occurs before insertion or commit.
            self.store.discard(document_id)
            raise
        except Exception:
            # If registration or commit failed, the commit outcome may be
            # unknown. Preserve bytes for the offline reconciliation check.
            if not registration_attempted:
                self.store.discard(document_id)
            raise
        if not created:
            self.store.discard(document_id)
        return registered, created

    def state(self, principal, document_id):
        self._require(principal, 'view')
        with self.connect() as conn:
            self._recheck(conn, principal, 'view')
            return PostgresIntakeJobs(lambda: nullcontext(conn)).state(principal.tenant, document_id)

    def result(self, principal, document_id):
        self._require(principal, 'view')
        with self.connect() as conn:
            self._recheck(conn, principal, 'view')
            return PostgresIntakeJobs(lambda: nullcontext(conn)).result(principal.tenant, document_id)

    def link_version(self, principal, document_id, family_id, *, expected_previous):
        self._require(principal, 'load')
        with self.connect() as conn:
            self._recheck(conn, principal, 'load')
            return PostgresIntakeJobs(lambda: nullcontext(conn)).link_version(
                principal.tenant, document_id, family_id, expected_previous=expected_previous)

    def version_history(self, principal, family_id):
        self._require(principal, 'view')
        with self.connect() as conn:
            self._recheck(conn, principal, 'view')
            return PostgresIntakeJobs(lambda: nullcontext(conn)).version_history(principal.tenant, family_id)

    def promote(self, principal, document_id):
        """Atomically publish one completed synthetic result to tenant review."""
        self._require(principal, 'load')
        if not isinstance(document_id, str):
            raise ValueError('Document unavailable')
        document = UUID(document_id)
        with self.connect() as conn:
            self._recheck(conn, principal, 'load')
            row = conn.execute('''SELECT j.state,j.result,d.sha256 FROM nawa_intake_documents d
                JOIN nawa_intake_jobs j ON j.tenant_id=d.tenant_id AND j.document_id=d.id
                WHERE d.tenant_id=%s AND d.id=%s FOR UPDATE OF d,j''',
                (principal.tenant, document)).fetchone()
            if row is None or row[0] != 'completed' or not isinstance(row[1], dict):
                raise ValueError('Completed document unavailable')
            # Recheck the current source before returning or creating a review
            # record; processing may have completed before the file changed.
            self.store.read_verified(document.hex, row[2].strip())
            previous = conn.execute('''SELECT q.id,q.quotation FROM nawa_intake_promotions p
                JOIN nawa_quotations q ON q.id=p.quotation_id
                WHERE p.tenant_id=%s AND p.document_id=%s''',
                (principal.tenant, document)).fetchone()
            from .dashboard import _public_quote
            if previous:
                return {'id':previous[0], 'quotation':_public_quote(previous[1]), 'created':False}
            quote = row[1]
            public_quote = _public_quote(quote)
            conn.execute('SELECT pg_advisory_xact_lock(%s)', (6892110312,))
            count = conn.execute('SELECT count(*) FROM nawa_quotation_tenants WHERE tenant_id=%s',
                                 (principal.tenant,)).fetchone()[0]
            if count >= 20:
                raise ValueError('Synthetic quotation limit reached')
            item_id = uuid4().hex[:12]
            conn.execute('INSERT INTO nawa_quotations (id,quotation) VALUES (%s,%s::jsonb)',
                         (item_id, json.dumps(quote, ensure_ascii=False, allow_nan=False)))
            conn.execute('INSERT INTO nawa_quotation_tenants (quotation_id,tenant_id) VALUES (%s,%s)',
                         (item_id, principal.tenant))
            conn.execute('INSERT INTO nawa_intake_promotions (tenant_id,document_id,quotation_id) VALUES (%s,%s,%s)',
                         (principal.tenant, document, item_id))
            return {'id':item_id, 'quotation':public_quote, 'created':True}

