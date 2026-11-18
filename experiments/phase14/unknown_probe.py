"""Measure vector scores for synthetic answerable and unanswerable questions.

This probe does not choose a threshold or produce answers. Fixture labels are
hand-authored and must not be interpreted as a production acceptance set.
"""
import json
from pathlib import Path

from compare_retrieval import authorized_vectors, cosine, embed, MODEL
from retrieval import read_corpus

HERE = Path(__file__).resolve().parent


def main():
    passages = read_corpus(HERE / 'expanded_corpus.json')
    allowed, document_vectors = authorized_vectors(passages, 'demo-a', 'analyst-a')
    known = json.loads((HERE / 'expanded_evaluation.json').read_text(encoding='utf-8'))
    unknown = json.loads((HERE / 'unknown_evaluation.json').read_text(encoding='utf-8'))
    if any(c['tenant_id'] != 'demo-a' or c['principal_id'] != 'analyst-a' for c in known):
        raise ValueError('Unexpected fixture identity')
    questions = [c['query'] for c in known + unknown]
    query_vectors = embed(questions)
    rows = []
    for i, (case, query_vector) in enumerate(zip(known + unknown, query_vectors)):
        ranked = sorted(((cosine(query_vector, v), p.passage_id)
                         for p, v in zip(allowed, document_vectors)),
                        key=lambda pair: (-pair[0], pair[1]))
        rows.append({'id':case['id'], 'category':case['category'],
                     'label':'answerable' if i < len(known) else 'unanswerable',
                     'top_passage_id':ranked[0][1], 'top_cosine':round(ranked[0][0], 6)})
    known_scores = [row['top_cosine'] for row in rows if row['label'] == 'answerable']
    unknown_scores = [row['top_cosine'] for row in rows if row['label'] == 'unanswerable']
    print(json.dumps({'model':MODEL, 'scope':'Hand-authored synthetic score probe, not threshold calibration.',
                      'answerable_top_score_range':[min(known_scores), max(known_scores)],
                      'unanswerable_top_score_range':[min(unknown_scores), max(unknown_scores)],
                      'overlap':max(unknown_scores) >= min(known_scores),
                      'warning':'Every question is ranked, including unanswerable questions; no abstention.',
                      'cases':rows}, indent=2))


if __name__ == '__main__':
    main()

