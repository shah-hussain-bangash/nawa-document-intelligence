"""Offline synthetic-only BM25/vector/RRF comparison using local Ollama.

Identity and access lists are test fixtures, not an authentication system.
"""
from collections import defaultdict
import json
import math
from pathlib import Path
import statistics
import time
from urllib.request import ProxyHandler, Request, build_opener

from benchmark import metrics
from retrieval import BM25Index, read_corpus

HERE = Path(__file__).resolve().parent
MODEL = 'embeddinggemma:300m'
OPENER = build_opener(ProxyHandler({}))


def embed(texts):
    payload = json.dumps({'model': MODEL, 'input': texts}).encode('utf-8')
    req = Request('http://127.0.0.1:11434/api/embed', data=payload,
                  headers={'Content-Type': 'application/json'})
    with OPENER.open(req, timeout=120) as response:
        result = json.load(response)
    vectors = result['embeddings']
    if len(vectors) != len(texts):
        raise ValueError('Embedding count mismatch')
    return vectors


def cosine(a, b):
    if not a or len(a) != len(b) or not all(math.isfinite(x) for x in a + b):
        raise ValueError('Invalid embedding')
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    if not na or not nb:
        raise ValueError('Zero embedding')
    return sum(x*y for x, y in zip(a, b)) / (na * nb)


def rrf(*rankings, k=60):
    scores = defaultdict(float)
    for ranking in rankings:
        if len(set(ranking)) != len(ranking):
            raise ValueError('Duplicate ranked IDs')
        for position, item in enumerate(ranking, 1):
            scores[item] += 1 / (k + position)
    return sorted(scores, key=lambda item: (-scores[item], item))


def authorized_vectors(passages, tenant, principal, embedding_fn=embed):
    authorized = [p for p in passages if p.tenant_id == tenant and principal in p.allowed_principals]
    vectors = embedding_fn([p.text for p in authorized]) if authorized else []
    if len(vectors) != len(authorized):
        raise ValueError('Embedding count mismatch')
    return authorized, vectors


def main():
    passages = read_corpus(HERE / 'expanded_corpus.json')
    cases = json.loads((HERE / 'expanded_evaluation.json').read_text(encoding='utf-8'))
    identities = {(case['tenant_id'], case['principal_id']) for case in cases}
    if len(identities) != 1:
        raise ValueError('This small comparison expects one synthetic identity')
    tenant, principal = next(iter(identities))
    start = time.perf_counter()
    allowed, vectors = authorized_vectors(passages, tenant, principal)
    indexing_ms = (time.perf_counter() - start) * 1000
    lexical = BM25Index(passages, tenant_id=tenant, principal_id=principal)
    allowed_ids = {p.passage_id for p in allowed}
    aggregates = {mode: [] for mode in ('bm25', 'vector', 'hybrid')}
    times = {mode: [] for mode in aggregates}
    rows = []
    for case in cases:
        relevant = set(case['relevant_passage_ids'])
        if not relevant or not relevant <= allowed_ids:
            raise ValueError('Relevant passage missing or unauthorized')
        start = time.perf_counter()
        bm = [hit['passage_id'] for hit in lexical.search(case['query'], k=100)]
        bm_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        query_vector = embed([case['query']])[0]
        vector = [p.passage_id for _, p in sorted(
            ((cosine(query_vector, v), p) for p, v in zip(allowed, vectors)),
            key=lambda item: (-item[0], item[1].passage_id))]
        vector_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        hybrid = rrf(bm, vector)
        fusion_ms = (time.perf_counter() - start) * 1000
        row = {'id':case['id'], 'category':case['category']}
        for mode, ranking, duration in (
                ('bm25', bm, bm_ms), ('vector', vector, vector_ms),
                ('hybrid', hybrid, bm_ms + vector_ms + fusion_ms)):
            if not set(ranking) <= allowed_ids:
                raise AssertionError('Unauthorized candidate')
            recall, rank, ndcg = metrics(ranking, relevant)
            aggregates[mode].append((recall, rank, ndcg))
            times[mode].append(duration)
            row[mode] = {'top5':ranking[:5], 'recall_at_5':recall,
                         'reciprocal_rank_at_5':rank, 'ndcg_at_5':ndcg}
        rows.append(row)
    result = {'scope':'10 hand-authored synthetic cases, same author as fixtures; no production claims.',
              'model':MODEL, 'authorized_passage_count':len(allowed), 'case_count':len(cases),
              'document_embedding_ms_single_run':indexing_ms,
              'methods':{mode:{'recall_at_5':statistics.mean(x[0] for x in values),
                               'mrr_at_5':statistics.mean(x[1] for x in values),
                               'ndcg_at_5':statistics.mean(x[2] for x in values),
                               'mean_query_ms_single_run':statistics.mean(times[mode])}
                         for mode, values in aggregates.items()},
              'warning':'Vector and hybrid always rank candidates; unknown-answer abstention is not implemented.',
              'cases':rows}
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()

