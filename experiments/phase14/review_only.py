"""Synthetic review-only decision boundary; not integrated with NAWA.

Trusted identity and lifecycle metadata are represented by fixture snapshots.
This module does not sanitize document content or establish injection safety.
"""
from lifecycle_fixture import recheck_results


def prepare_review(passages, candidate_ids, *, tenant, principal, lifecycle, model_verdict):
    """Recheck evidence and route a model suggestion to a human reviewer.

    A model suggestion is never an approval. On invalid suggestions or an
    unavailable evidence candidate, do not include the suggestion or evidence.
    """
    if not isinstance(candidate_ids, list) or not candidate_ids:
        return {'status':'unavailable'}
    if model_verdict not in ('supported', 'unsupported'):
        return {'status':'unavailable'}
    try:
        evidence = recheck_results(passages, candidate_ids, tenant=tenant,
                                   principal=principal, lifecycle=lifecycle)
    except (ValueError, TypeError):
        return {'status':'unavailable'}
    return {'status':'requires_human_review',
            'model_suggestion':model_verdict,
            'evidence':[{'passage_id':p.passage_id,'document_id':p.document_id,
                         'version':p.version,'page':p.page,'source':p.source}
                        for p in evidence]}

