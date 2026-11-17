"""Draft server-side intake boundary; no HTTP endpoint is connected."""
from contextlib import nullcontext

from .authorization import Principal, authorized
from .identity_repository import membership_by_key
from .intake_postgres import PostgresIntakeJobs


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
