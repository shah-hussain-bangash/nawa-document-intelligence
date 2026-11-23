import unittest
from support_probe import confusion, exact_substring, lexical_coverage


class SupportProbeTests(unittest.TestCase):
    def test_exact_and_lexical_heuristics_have_different_limits(self):
        source = 'Payment is due thirty days after receiving the invoice.'
        self.assertTrue(exact_substring('thirty days after receiving', source))
        claim = 'Payment is due thirty days before receiving the invoice.'
        self.assertFalse(exact_substring(claim, source))
        self.assertTrue(lexical_coverage(claim, source))

    def test_confusion_counts(self):
        self.assertEqual(confusion([(True, True), (True, False),
                                    (False, True), (False, False)]),
                         {'tp':1, 'fn':1, 'fp':1, 'tn':1})


if __name__ == '__main__':
    unittest.main()

