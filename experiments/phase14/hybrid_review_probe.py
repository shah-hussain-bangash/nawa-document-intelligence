"""Exercise the synthetic review path using local embeddings and fixture data."""
import json
from pathlib import Path

from compare_retrieval import embed, MODEL
from hybrid_review import retrieve_for_review
from retrieval import read_corpus

HERE = Path(__file__).resolve().parent


def main():
    passages = read_corpus(HERE / 'expanded_corpus.json')
    states = {p.passage_id:'current' for p in passages}
    states['en-delivery-v1'] = 'superseded'
    def snapshot():
        return {'passages':passages, 'lifecycle':states.copy()}
    result = retrieve_for_review('What is the latest Cedar laptop delivery time?',
                                 tenant='demo-a', principal='analyst-a',
                                 load_snapshot=snapshot, embed_fn=embed)
    if result['status'] != 'requires_human_review':
        raise ValueError('Synthetic retrieval unavailable')
    ids = [item['passage_id'] for item in result['evidence']]
    if 'en-delivery-v1' in ids or 'restricted' in ids or 'tenant-b' in ids:
        raise AssertionError('Fixture policy boundary failed')
    print(json.dumps({'model':MODEL, 'scope':'Synthetic fixture snapshot; no live identity or database.',
                      'query':'latest Cedar laptop delivery',
                      'status':result['status'], 'evidence_ids':ids}, indent=2))


if __name__ == '__main__':
    main()

