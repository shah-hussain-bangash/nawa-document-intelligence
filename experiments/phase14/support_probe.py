"""Offline comparison of two string heuristics, not an entailment verifier."""
from collections import Counter
import json
from pathlib import Path
import unicodedata

from retrieval import read_corpus, tokenize

HERE = Path(__file__).resolve().parent


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def exact_substring(claim, source):
    return normalized(claim) in normalized(source)


def lexical_coverage(claim, source, threshold=0.8):
    terms = set(tokenize(claim))
    return bool(terms) and len(terms & set(tokenize(source))) / len(terms) >= threshold


def confusion(pairs):
    counts = Counter()
    for expected, actual in pairs:
        counts['tp' if expected and actual else 'fn' if expected
               else 'fp' if actual else 'tn'] += 1
    return {key: counts[key] for key in ('tp', 'fn', 'fp', 'tn')}


def main():
    corpus = {p.passage_id:p for p in read_corpus(HERE / 'expanded_corpus.json')}
    cases = json.loads((HERE / 'support_cases.json').read_text(encoding='utf-8'))
    if len({case['id'] for case in cases}) != len(cases):
        raise ValueError('Duplicate case ID')
    rows = []
    for case in cases:
        if type(case['supported']) is not bool or case['passage_id'] not in corpus:
            raise ValueError('Invalid label or passage')
        passage = corpus[case['passage_id']]
        rows.append({'id':case['id'], 'category':case['category'],
                     'expected_supported':case['supported'],
                     'exact_substring':exact_substring(case['claim'], passage.text),
                     'lexical_coverage_0_8':lexical_coverage(case['claim'], passage.text)})
    summary = {name:confusion((row['expected_supported'], row[name]) for row in rows)
               for name in ('exact_substring', 'lexical_coverage_0_8')}
    print(json.dumps({'scope':'20 hand-authored synthetic labels, not independently reviewed.',
                      'warning':'String heuristics do not establish semantic support.',
                      'case_count':len(rows), 'confusion':summary, 'cases':rows}, indent=2))


if __name__ == '__main__':
    main()

