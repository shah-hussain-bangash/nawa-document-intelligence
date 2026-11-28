"""Offline evaluation of the Phase 4 synthetic BM25 baseline.

This uses caller-supplied fixture identities; it is not an authorization service.
"""
import json
import math
from pathlib import Path
import statistics
import time

from retrieval import BM25Index, read_corpus

HERE = Path(__file__).resolve().parent


def metrics(ranked, relevant, k=5):
    if not relevant:
        raise ValueError('Relevant IDs are required for ranked metrics')
    ranked = ranked[:k]
    if len(ranked) != len(set(ranked)):
        raise ValueError('Duplicate ranked IDs')
    positions = [i for i, item in enumerate(ranked, 1) if item in relevant]
    recall = len(positions) / len(relevant)
    reciprocal_rank = 1 / positions[0] if positions else 0.0
    dcg = sum(1 / math.log2(i + 1) for i in positions)
    ideal = sum(1 / math.log2(i + 1) for i in range(1, min(k, len(relevant)) + 1))
    return recall, reciprocal_rank, dcg / ideal


def main():
    passages = read_corpus(HERE / 'passages.json')
    cases = json.loads((HERE / 'evaluation.json').read_text(encoding='utf-8'))
    rows = []
    latencies = []
    for case in cases:
        index = BM25Index(passages, tenant_id=case['tenant_id'], principal_id=case['principal_id'])
        relevant = set(case['relevant_passage_ids'])
        if not relevant or not relevant <= {p.passage_id for p in index.passages}:
            raise ValueError('Relevance labels must identify authorized passages')
        start = time.perf_counter()
        hits = index.search(case['query'], k=5)
        latencies.append((time.perf_counter() - start) * 1000)
        ids = [h['passage_id'] for h in hits]
        recall, mrr, ndcg = metrics(ids, relevant)
        rows.append({'query': case['query'], 'retrieved_ids': ids,
                     'recall_at_5': recall, 'reciprocal_rank_at_5': mrr,
                     'ndcg_at_5': ndcg})

    index = BM25Index(passages, tenant_id='demo-a', principal_id='reviewer-a')
    unknown = index.search('interplanetary antimatter quantum')
    foreign = index.search('Exclusive tenant B satellite Orion')
    restricted = index.search('Falcon Robotics confidential inspection')
    if unknown or foreign or restricted:
        raise AssertionError('Synthetic unknown or access-boundary regression')
    result = {'scope': 'Three existing synthetic labeled queries; not a production benchmark.',
              'case_count': len(rows), 'macro_recall_at_5': statistics.mean(r['recall_at_5'] for r in rows),
              'mrr_at_5': statistics.mean(r['reciprocal_rank_at_5'] for r in rows),
              'macro_ndcg_at_5': statistics.mean(r['ndcg_at_5'] for r in rows),
              'mean_search_ms_single_run': statistics.mean(latencies),
              'synthetic_unknown_and_access_smoke': 'pass', 'cases': rows}
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()

