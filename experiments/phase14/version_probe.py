"""Probe version-aware questions without pretending similarity enforces lifecycle."""
import json
from pathlib import Path

from compare_retrieval import authorized_vectors, cosine, embed, rrf, MODEL
from retrieval import BM25Index, read_corpus

HERE = Path(__file__).resolve().parent
CASES = [
    {'id':'latest', 'query':'What is the latest Cedar laptop delivery time?',
     'expected':'en-delivery-v2'},
    {'id':'original', 'query':'What was the original Cedar delivery time?',
     'expected':'en-delivery-v1'},
]


def main():
    passages = read_corpus(HERE / 'expanded_corpus.json')
    allowed, vectors = authorized_vectors(passages, 'demo-a', 'analyst-a')
    index = BM25Index(passages, tenant_id='demo-a', principal_id='analyst-a')
    rows = []
    for case, query_vector in zip(CASES, embed([item['query'] for item in CASES])):
        bm25 = [h['passage_id'] for h in index.search(case['query'], k=100)]
        vector = [p.passage_id for _, p in sorted(
            ((cosine(query_vector, v), p) for p, v in zip(allowed, vectors)),
            key=lambda pair: (-pair[0], pair[1].passage_id))]
        hybrid = rrf(bm25, vector)
        rows.append({'id':case['id'], 'assumed_expected':case['expected'],
                     'bm25_top3':bm25[:3], 'vector_top3':vector[:3],
                     'hybrid_top3':hybrid[:3]})
    print(json.dumps({'scope':'Synthetic assumption: v1 original, v2 latest. No lifecycle filtering.',
                      'model':MODEL, 'cases':rows}, indent=2))


if __name__ == '__main__':
    main()

