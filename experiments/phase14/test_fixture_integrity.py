"""Validate the synthetic evaluation labels and fixture boundaries."""
import json
from pathlib import Path
import unittest

from retrieval import BM25Index, read_corpus

HERE = Path(__file__).resolve().parent


class FixtureIntegrityTests(unittest.TestCase):
    def test_labeled_questions_are_unique_and_relevant_ids_are_authorized(self):
        known = json.loads((HERE / 'expanded_evaluation.json').read_text(encoding='utf-8'))
        unknown = json.loads((HERE / 'unknown_evaluation.json').read_text(encoding='utf-8'))
        corpus = read_corpus(HERE / 'expanded_corpus.json')
        combined = known + unknown
        self.assertEqual(len({row['id'] for row in combined}), len(combined))
        self.assertEqual(len({row['query'] for row in combined}), len(combined))
        for row in known:
            index = BM25Index(corpus, tenant_id=row['tenant_id'], principal_id=row['principal_id'])
            self.assertTrue(set(row['relevant_passage_ids']))
            self.assertLessEqual(set(row['relevant_passage_ids']),
                                 {p.passage_id for p in index.passages})


if __name__ == '__main__':
    unittest.main()

