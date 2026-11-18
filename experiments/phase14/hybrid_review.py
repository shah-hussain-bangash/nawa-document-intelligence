"""Synthetic hybrid retrieval and human-review boundary; not a NAWA service.

Identity, access lists and lifecycle snapshots are test fixtures. The caller
must supply trusted data; these helpers do not authenticate users.
"""
from compare_retrieval import cosine, rrf
from lifecycle_fixture import eligible, recheck_results
from retrieval import BM25Index


def retrieve_for_review(query, *, tenant, principal, load_snapshot, embed_fn, limit=5):
    """Retrieve current synthetic candidates and recheck against a fresh snapshot.

    Never makes a support, answerability or approval decision. Any test-fixture
    permission/lifecycle change that invalidates a candidate closes the batch.
    """
    if not isinstance(query, str) or not query.strip():
        return {'status':'unavailable'}
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
        return {'status':'unavailable'}
    try:
        before = load_snapshot()
        candidates = eligible(before['passages'], tenant=tenant, principal=principal,
                              lifecycle=before['lifecycle'])
        if not candidates:
            return {'status':'unavailable'}
        index = BM25Index(candidates, tenant_id=tenant, principal_id=principal)
        bm25 = [hit['passage_id'] for hit in index.search(query, k=100)]
        embeddings = embed_fn([p.text for p in candidates] + [query])
        if len(embeddings) != len(candidates) + 1:
            raise ValueError('Embedding count mismatch')
        query_vector = embeddings[-1]
        vector = [passage.passage_id for _, passage in sorted(
            ((cosine(query_vector, embedding), passage)
             for passage, embedding in zip(candidates, embeddings[:-1])),
            key=lambda row: (-row[0], row[1].passage_id))]
        ids = rrf(bm25, vector)[:limit]
        after = load_snapshot()
        current = recheck_results(after['passages'], ids, tenant=tenant, principal=principal,
                                  lifecycle=after['lifecycle'])
        original = {p.passage_id:p for p in candidates}
        if any(original[p.passage_id] != p for p in current):
            raise ValueError('Candidate changed while retrieval was running')
        if 'provenance' in before or 'provenance' in after:
            old_provenance, new_provenance = before.get('provenance'), after.get('provenance')
            if not isinstance(old_provenance, dict) or not isinstance(new_provenance, dict):
                raise ValueError('Provenance snapshot unavailable')
            if any(p.passage_id not in old_provenance or p.passage_id not in new_provenance
                   or old_provenance[p.passage_id] != new_provenance[p.passage_id] for p in current):
                raise ValueError('Candidate provenance changed while retrieval was running')
        return {'status':'requires_human_review',
                'evidence':[{'passage_id':p.passage_id, 'document_id':p.document_id,
                             'version':p.version, 'page':p.page, 'source':p.source}
                            for p in current]}
    except (ValueError, TypeError, KeyError, OSError, TimeoutError):
        return {'status':'unavailable'}

