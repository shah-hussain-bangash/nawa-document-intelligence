"""Synthetic lifecycle experiment; not an authentication or retrieval endpoint.

Trusted callbacks supply a current principal and an authorized passage snapshot.
The callbacks used in tests are in-memory fixtures, not a production data source.
"""
from .authorization import Principal, authorized
from .retrieval import BM25Index, Passage


class EvidenceUnavailable(ValueError):
    pass


class SyntheticLiveRetrieval:
    def __init__(self, resolve_principal, load_passages):
        if not callable(resolve_principal) or not callable(load_passages):
            raise ValueError('Trusted callbacks required')
        self._resolve_principal = resolve_principal
        self._load_passages = load_passages

    def _snapshot(self, subject, tenant):
        try:
            principal = self._resolve_principal(subject, tenant)
            if (not isinstance(principal, Principal) or principal.subject != subject
                    or principal.tenant != tenant or not authorized(principal, 'view', tenant=tenant)):
                raise EvidenceUnavailable('Evidence unavailable')
            passages = self._load_passages(principal)
            if not isinstance(passages, (list, tuple)) or not all(isinstance(p, Passage) for p in passages):
                raise EvidenceUnavailable('Evidence unavailable')
            # Ignore all rows outside the resolved tenant and passage ACL.
            allowed = tuple(sorted((p for p in passages if p.tenant_id == tenant
                                    and subject in p.allowed_principals), key=lambda p:p.passage_id))
            if len({p.passage_id for p in allowed}) != len(allowed):
                raise EvidenceUnavailable('Evidence unavailable')
            return principal, allowed
        except Exception:
            raise EvidenceUnavailable('Evidence unavailable') from None

    def search(self, subject, tenant, query, *, k=5, expected_principal=None):
        """Fail closed if the trusted snapshot changes before returning results.

        The loader must already exclude withdrawn, obsolete and unapproved
        sources. Equality checks cannot detect changes after the final read,
        changes that revert between reads, or dishonest callback responses.
        """
        before = self._snapshot(subject, tenant)
        if expected_principal is not None and before[0] != expected_principal:
            raise EvidenceUnavailable('Evidence unavailable')
        hits = BM25Index(list(before[1]), tenant_id=tenant, principal_id=subject).search(query, k=k)
        if self._snapshot(subject, tenant) != before:
            raise EvidenceUnavailable('Evidence unavailable')
        return hits

    def resolve(self, subject, tenant, passage_id, *, expected_principal=None):
        """Recheck the snapshot when an earlier passage ID is opened."""
        if not isinstance(passage_id, str) or not passage_id.strip():
            raise EvidenceUnavailable('Evidence unavailable')
        before = self._snapshot(subject, tenant)
        if expected_principal is not None and before[0] != expected_principal:
            raise EvidenceUnavailable('Evidence unavailable')
        match = next((p for p in before[1] if p.passage_id == passage_id), None)
        if match is None or self._snapshot(subject, tenant) != before:
            raise EvidenceUnavailable('Evidence unavailable')
        return match
