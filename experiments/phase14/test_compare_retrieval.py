import unittest
from compare_retrieval import authorized_vectors, cosine, rrf
from retrieval import Passage


class ComparisonTests(unittest.TestCase):
    def test_filter_happens_before_embedding(self):
        def passage(pid, tenant, principals):
            return Passage(pid, pid, 'v1', tenant, 1, pid, principals, pid, 'synthetic')
        corpus = [passage('allowed', 'a', ('user',)),
                  passage('restricted', 'a', ('admin',)),
                  passage('other', 'b', ('user',))]
        seen = []
        def fake(texts):
            seen.extend(texts)
            return [[1.0, 0.0] for _ in texts]
        allowed, vectors = authorized_vectors(corpus, 'a', 'user', fake)
        self.assertEqual(seen, ['allowed'])
        self.assertEqual([p.passage_id for p in allowed], ['allowed'])
        self.assertEqual(len(vectors), 1)

    def test_cosine_and_reciprocal_rank_fusion(self):
        self.assertAlmostEqual(cosine([1.0, 0.0], [1.0, 1.0]), 2 ** -0.5)
        with self.assertRaises(ValueError):
            cosine([0.0, 0.0], [1.0, 0.0])
        self.assertEqual(rrf(['a', 'b'], ['b', 'a']), ['a', 'b'])
        with self.assertRaises(ValueError):
            rrf(['a', 'a'])

    def test_cosine_handles_extreme_finite_values_without_nan(self):
        for n in (1e308, 1e-300):
            with self.subTest(magnitude=n):
                self.assertAlmostEqual(cosine([n, n], [n, n]), 1.0)
                self.assertAlmostEqual(cosine([n, 0], [0, n]), 0.0)

    def test_cosine_rejects_invalid_embedding_values(self):
        for invalid in ([True], [float('nan')], [float('inf')], ['1'], [10**400]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                cosine(invalid, [1.0])


if __name__ == '__main__':
    unittest.main()
