"""Run the explicit synthetic version policy with the local embedding model."""
import json
from pathlib import Path

from compare_retrieval import cosine, embed, MODEL
from lifecycle_fixture import embed_eligible, recheck_results
from retrieval import read_corpus

HERE = Path(__file__).resolve().parent


def main():
    passages = read_corpus(HERE / 'expanded_corpus.json')
    # This is a synthetic, caller-supplied snapshot; not live database metadata.
    states = {p.passage_id: 'current' for p in passages}
    states['en-delivery-v1'] = 'superseded'
    q = 'What is the latest Cedar laptop delivery time?'
    chosen, vectors = embed_eligible(passages, tenant='demo-a', principal='analyst-a',
                                     lifecycle=states)
    query = embed([q])[0]
    ranked = sorted(((cosine(query, v), p.passage_id) for p, v in zip(chosen, vectors)),
                    key=lambda row: (-row[0], row[1]))
    top = [pid for _, pid in ranked[:3]]
    recheck_results(passages, top, tenant='demo-a', principal='analyst-a', lifecycle=states)
    assert 'en-delivery-v1' not in {p.passage_id for p in chosen}
    print(json.dumps({'model':MODEL, 'scope':'Fixture lifecycle snapshot; no live authorization.',
                      'synthetic_query':'latest Cedar delivery',
                      'top3_after_current_filter':top,
                      'superseded_passage_indexed':False}, indent=2))


if __name__ == '__main__':
    main()

