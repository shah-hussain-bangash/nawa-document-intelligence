"""Synthetic, in-memory lifecycle policy experiment; not an authorization service.

The caller must obtain the current identity, membership and lifecycle metadata
from trusted systems. This prototype uses only test fixture snapshots.
"""
from compare_retrieval import embed


def eligible(passages, *, tenant, principal, lifecycle, history_document=None):
    """Return authorized, active fixture passages; permit explicit history only.

    `history_document` represents a decision already authorized by the
    trusted caller, not a user-controlled grant of access.
    """
    if not isinstance(tenant, str) or not tenant or not isinstance(principal, str) or not principal:
        raise ValueError('Trusted tenant and principal are required')
    if not isinstance(lifecycle, dict):
        raise ValueError('Lifecycle snapshot required')
    if history_document is not None and (not isinstance(history_document, str) or not history_document):
        raise ValueError('Invalid history selection')
    selected = []
    seen = set()
    for passage in passages:
        if passage.tenant_id != tenant or principal not in passage.allowed_principals:
            continue
        if passage.passage_id in seen:
            raise ValueError('Duplicate authorized passage ID')
        seen.add(passage.passage_id)
        state = lifecycle.get(passage.passage_id)
        if state not in ('current', 'superseded', 'deleted', 'revoked'):
            raise ValueError('Missing or invalid lifecycle metadata')
        if state == 'current' or (state == 'superseded' and passage.document_id == history_document):
            selected.append(passage)
    return selected


def embed_eligible(passages, *, tenant, principal, lifecycle, history_document=None, embedding_fn=embed):
    chosen = eligible(passages, tenant=tenant, principal=principal,
                      lifecycle=lifecycle, history_document=history_document)
    vectors = embedding_fn([p.text for p in chosen]) if chosen else []
    if len(vectors) != len(chosen):
        raise ValueError('Embedding count mismatch')
    return chosen, vectors


def recheck_results(passages, result_ids, *, tenant, principal, lifecycle, history_document=None):
    """Recheck candidate IDs using a fresh trusted fixture snapshot."""
    if len(result_ids) != len(set(result_ids)):
        raise ValueError('Duplicate result ID')
    permitted = {p.passage_id: p for p in eligible(
        passages, tenant=tenant, principal=principal, lifecycle=lifecycle,
        history_document=history_document)}
    # Reject the entire candidate batch if a candidate is no longer permitted.
    if any(item not in permitted for item in result_ids):
        raise ValueError('Candidate is no longer available')
    return [permitted[item] for item in result_ids]

