"""Offline synthetic intake integration; caller-provided tenants are untrusted."""
from .intake_postgres import IntakeRejected


class SyntheticIntakePipeline:
    def __init__(self, store, jobs):
        self.store = store
        self.jobs = jobs

    def submit(self, tenant, filename, content):
        """Store bytes then register a job; clean up confirmed duplicates.

        A crash or uncertain database error can leave an orphaned file. Keep it
        for offline reconciliation: a commit may have succeeded despite an error.
        No production authorization or automatic repair is provided here.
        """
        if not isinstance(tenant, str) or not tenant.strip():
            raise ValueError('Tenant is required')
        document_id, metadata = self.store.save(filename, content)
        try:
            registered_id, created = self.jobs.register(tenant, document_id, metadata)
        except IntakeRejected:
            self.store.discard(document_id)
            raise
        if not created:
            self.store.discard(document_id)
        return registered_id, created

