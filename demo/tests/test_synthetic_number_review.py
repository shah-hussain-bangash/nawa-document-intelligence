import copy
import unittest
from pathlib import Path

from nawa_demo.core import extract
from nawa_demo.review import begin
from nawa_demo.synthetic_number_review import review_signals


SAMPLE = Path(__file__).resolve().parents[1] / 'samples' / 'english_quote.txt'


class SyntheticNumberReviewTests(unittest.TestCase):
    def setUp(self):
        self.quote = extract(SAMPLE)

    def reasons(self, report):
        return [item['reason'] for item in report['findings']]

    def test_historical_decimal_comma_is_flagged_without_mutation(self):
        self.quote['evidence']['total']['value'] = '1,23'
        self.quote['total'] = '123'
        before = copy.deepcopy(self.quote)
        result = review_signals(self.quote)
        self.assertIn('unsupported_or_invalid_number', self.reasons(result))
        self.assertEqual(self.quote, before)

    def test_grouped_value_still_requires_locale_review(self):
        self.quote['evidence']['total']['value'] = '1,234'
        self.quote['total'] = '1234'
        self.assertIn('separator_convention_requires_review', self.reasons(review_signals(self.quote)))

    def test_mismatch_and_missing_evidence_are_reported(self):
        self.quote['total'] = '100'
        del self.quote['evidence']['subtotal']
        reasons = self.reasons(review_signals(self.quote))
        self.assertIn('saved_value_differs_from_source', reasons)
        self.assertIn('missing_value_or_source_evidence', reasons)

    def test_corrections_are_reviewed_without_exposing_source(self):
        ledger = begin(self.quote)
        ledger['events'].append({'type': 'correction', 'data': {'field': 'total', 'to': '1,23',
                                  'evidence': {'quote': 'PRIVATE SYNTHETIC TEXT'}}})
        before = copy.deepcopy(ledger)
        result = review_signals(self.quote, ledger)
        self.assertIn('correction_requires_source_review', self.reasons(result))
        self.assertIn('unsupported_or_invalid_number', self.reasons(result))
        self.assertNotIn('PRIVATE SYNTHETIC TEXT', str(result))
        self.assertEqual(ledger, before)

    def test_no_signals_is_not_a_correctness_claim(self):
        result = review_signals(self.quote, begin(self.quote))
        self.assertFalse(result['signals_detected'])
        self.assertIn('human review remains required', result['scope'])


if __name__ == '__main__':
    unittest.main()
