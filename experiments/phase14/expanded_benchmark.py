"""Hand-labeled synthetic retrieval evaluation; no model or answer generation."""
from collections import defaultdict
import json
from pathlib import Path
import statistics
import time

from benchmark import metrics
from retrieval import BM25Index, read_corpus

HERE = Path(__file__).resolve().parent


def main():
    passages = read_corpus(HERE / 'expanded_corpus.json')
    cases = json.loads((HERE / 'expanded_evaluation.json').read_text(encoding='utf-8'))
    if len({case['id'] for case in cases}) != len(cases):
        raise ValueError('Duplicate case ID')
    scores = defaultdict(list)
    rows, elapsed = [], []
    for case in cases:
        index = BM25Index(passages, tenant_id=case['tenant_id'], principal_id=case['principal_id'])
        allowed = {p.passage_id for p in index.passages}
        relevant = set(case['relevant_passage_ids'])
        if not relevant or not relevant <= allowed:
            raise ValueError('Relevant passage missing or unauthorized')
        start = time.perf_counter()
        ids = [item['passage_id'] for item in index.search(case['query'], k=5)]
        elapsed.append((time.perf_counter() - start) * 1000)
        if not set(ids) <= allowed:
            raise AssertionError('An unauthorized result was returned')
        recall, reciprocal_rank, ndcg = metrics(ids, relevant)
        scores[case['category']].append((recall, reciprocal_rank, ndcg))
        rows.append({'id':case['id'], 'category':case['category'], 'retrieved_ids':ids,
                     'relevant_ids':sorted(relevant), 'recall_at_5':recall,
                     'reciprocal_rank_at_5':reciprocal_rank, 'ndcg_at_5':ndcg})
    index = BM25Index(passages, tenant_id='demo-a', principal_id='analyst-a')
    checks = {
        'unknown_query_has_no_lexical_match': not index.search('interplanetary antimatter quantum'),
        'restricted_passage_absent': 'restricted' not in {r['passage_id'] for r in index.search('Zenith Falcon secure inspection')},
        'other_tenant_passage_absent': 'tenant-b' not in {r['passage_id'] for r in index.search('Orion lunar devices')},
    }
    if not all(checks.values()):
        raise AssertionError('A synthetic access or unknown-query smoke check failed')
    output = {'scope':'Hand-authored synthetic cases; no lifecycle enforcement or answer generation.',
              'case_count':len(rows),
              'macro_recall_at_5':statistics.mean(r['recall_at_5'] for r in rows),
              'mrr_at_5':statistics.mean(r['reciprocal_rank_at_5'] for r in rows),
              'macro_ndcg_at_5':statistics.mean(r['ndcg_at_5'] for r in rows),
              'mean_search_ms_single_run':statistics.mean(elapsed),
              'by_category':{category:{'count':len(values),
                    'recall_at_5':statistics.mean(v[0] for v in values),
                    'mrr_at_5':statistics.mean(v[1] for v in values),
                    'ndcg_at_5':statistics.mean(v[2] for v in values)}
                    for category, values in sorted(scores.items())},
              'smoke_checks':checks, 'cases':rows}
    print(json.dumps(output, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()

