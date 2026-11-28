import unittest
from benchmark import metrics


class RankingMetricTests(unittest.TestCase):
    def test_multiple_relevant_items_and_cutoff(self):
        recall, rr, ndcg = metrics(['x', 'a', 'y', 'b'], {'a', 'b', 'c'}, k=3)
        self.assertAlmostEqual(recall, 1 / 3)
        self.assertEqual(rr, 1 / 2)
        self.assertAlmostEqual(ndcg, (1 / __import__('math').log2(3)) /
                               (1 + 1 / __import__('math').log2(3) + 1 / 2))

    def test_no_match_and_invalid_labels(self):
        self.assertEqual(metrics(['x'], {'a'}), (0, 0.0, 0.0))
        with self.assertRaises(ValueError):
            metrics([], set())
        with self.assertRaises(ValueError):
            metrics(['a', 'a'], {'a'})


if __name__ == '__main__':
    unittest.main()

