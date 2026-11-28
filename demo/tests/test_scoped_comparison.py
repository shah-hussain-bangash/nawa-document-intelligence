import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from nawa_demo.core import extract
from nawa_demo.review import begin, correct, decide
from nawa_demo.scoped_state import ScopedState


class ScopedComparisonTests(unittest.TestCase):
    def setUp(self):
        self.quote = extract(Path(__file__).resolve().parents[1] / 'samples/english_quote.txt')
        self.conn = MagicMock()
        self.state = ScopedState(MagicMock())

    def checked(self, row, quote=None):
        self.conn.execute.return_value.fetchone.return_value = row
        with patch.object(self.state, '_quote', return_value=quote or self.quote):
            return self.state._comparison_quote(self.conn, object(), 'synthetic-id')

    def test_unreviewed_quotation_preserves_original(self):
        result = self.checked(None)
        self.assertEqual(result['total'], '1050.00')
        self.assertEqual(result['comparison']['basis'], 'original_unreviewed')
        self.assertTrue(result['comparison']['eligible'])

    def test_pending_correction_is_not_eligible(self):
        ledger = correct(begin(self.quote), actor='analyst', field='total', value='1051.00',
                         reason='synthetic', source=self.quote['document'], line=6,
                         quote='Grand Total: 1050.00', expected_revision=1)
        result = self.checked((2, ledger))
        self.assertFalse(result['comparison']['eligible'])
        self.assertEqual(result['total'], '1050.00')

    def test_approved_correction_uses_reviewed_values_and_original_evidence(self):
        original = dict(self.quote, total='1051.00', checks={'vat_matches_rate':True, 'total_matches_components':False})
        ledger = correct(begin(original), actor='analyst', field='total', value='1050.00',
                         reason='synthetic', source=original['document'], line=3,
                         quote='Subtotal: 1000.00', expected_revision=1)
        ledger = decide(ledger, actor='reviewer', decision='approve', reason='synthetic', expected_revision=2)
        result = self.checked((3, ledger), original)
        self.assertEqual(result['total'], '1050.00')
        self.assertTrue(result['checks']['total_matches_components'])
        self.assertEqual(result['comparison']['basis'], 'approved_review')
        self.assertEqual(result['comparison']['review_revision'], 3)
        self.assertEqual(result['evidence'], original['evidence'])
        self.assertEqual(original['total'], '1051.00')

    def test_rejected_review_is_not_ranked(self):
        ledger = decide(begin(self.quote), actor='reviewer', decision='reject', reason='synthetic', expected_revision=1)
        self.assertFalse(self.checked((2, ledger))['comparison']['eligible'])

    def test_mismatched_review_revision_or_original_is_rejected(self):
        ledger = begin(self.quote)
        with self.assertRaises(ValueError):
            self.checked((99, ledger))
        changed = dict(self.quote, total='999.00')
        with self.assertRaises(ValueError):
            self.checked((1, ledger), changed)

    def test_pending_review_cannot_win_comparison(self):
        second = dict(self.quote, supplier='Z synthetic supplier')
        context = MagicMock()
        context.__enter__.return_value = self.conn
        self.state._connect.return_value = context
        self.conn.execute.return_value.fetchone.side_effect = [(1, begin(self.quote)), None]
        with patch.object(self.state, '_require'), patch.object(self.state, '_recheck'), \
             patch.object(self.state, '_quote', side_effect=[self.quote, second]):
            result = self.state.compare(object(), ['first', 'second'])
        self.assertEqual(result['lowest_valid_total'], 'Z synthetic supplier')
        self.assertFalse(result['quotations'][0]['comparison']['eligible'])


if __name__ == '__main__':
    unittest.main()
