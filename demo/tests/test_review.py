"""Phase 8 human-review ledger tests; synthetic only; no authentication."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from nawa_demo.core import extract
from nawa_demo.review import begin, correct, decide, inspect
from nawa_demo.review_cli import _save_new, _save_update, _load

SAMPLE = Path(__file__).resolve().parents[1] / 'samples' / 'english_quote.txt'
BAD = Path(__file__).resolve().parents[1] / 'samples' / 'incorrect_vat_quote.txt'


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.quotation = extract(SAMPLE)
        self.ledger = begin(self.quotation)

    def correction(self, record=None, **changes):
        ledger = self.ledger if record is None else record
        kwargs = dict(actor='reviewer-1', field='total', value='1050.00', reason='Verified on source',
                      source=ledger['document'], line=6, quote='Grand Total: 1050.00',
                      expected_revision=inspect(ledger)['revision'], timestamp='2026-01-02T00:00:00+00:00')
        kwargs.update(changes)
        return correct(ledger, **kwargs)

    def test_initial_pending_with_provenance(self):
        state = inspect(self.ledger)
        self.assertEqual((state['status'], state['revision']), ('pending_review', 1))
        self.assertEqual(state['source_evidence']['total']['line'], 6)

    def test_approve_valid_quotation(self):
        state = inspect(decide(self.ledger, actor='reviewer-1', decision='approve',
                               reason='Verified values', expected_revision=1))
        self.assertEqual(state['status'], 'approved')
        self.assertTrue(state['checks']['vat_matches_rate'])

    def test_reject_and_request_changes(self):
        for decision, expected in [('reject', 'rejected'), ('request_changes', 'changes_requested')]:
            with self.subTest(decision=decision):
                x = decide(self.ledger, actor='reviewer-1', decision=decision,
                           reason='Human review', expected_revision=1)
                self.assertEqual(inspect(x)['status'], expected)

    def test_correction_rechecks_math(self):
        changed = self.correction(value='900.00')
        self.assertFalse(inspect(changed)['checks']['total_matches_components'])
        self.assertEqual(inspect(changed)['fields']['total'], '900.00')
        self.assertEqual(inspect(changed)['history'][-1]['type'], 'correction')

    def test_bad_math_blocks_approval(self):
        changed = self.correction(value='900.00')
        with self.assertRaisesRegex(ValueError, 'Cannot approve'):
            decide(changed, actor='reviewer-1', decision='approve', reason='bad', expected_revision=2)

    def test_correct_bad_then_approve(self):
        changed = self.correction(value='900.00')
        fixed = self.correction(changed, value='1050.00')
        done = decide(fixed, actor='reviewer-2', decision='approve', reason='Rechecked', expected_revision=3)
        self.assertEqual(inspect(done)['status'], 'approved')
        self.assertEqual(inspect(done)['revision'], 4)

    def test_stale_revision_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Stale revision'):
            decide(self.ledger, actor='reviewer', decision='approve', reason='ok', expected_revision=0)

    def test_tampered_event_rejected(self):
        tampered = copy.deepcopy(self.ledger)
        tampered['events'][0]['data']['fields']['total'] = '99999.00'
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            inspect(tampered)

    def test_broken_chain_rejected(self):
        reviewed = decide(self.ledger, actor='reviewer', decision='approve', reason='ok', expected_revision=1)
        tampered = copy.deepcopy(reviewed)
        tampered['events'][1]['previous_hash'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'chain broken'):
            inspect(tampered)

    def test_no_changes_after_final(self):
        reviewed = decide(self.ledger, actor='reviewer', decision='approve', reason='ok', expected_revision=1)
        with self.assertRaisesRegex(ValueError, 'Final decision'):
            decide(reviewed, actor='reviewer', decision='reject', reason='no', expected_revision=2)
        with self.assertRaisesRegex(ValueError, 'Final review'):
            self.correction(reviewed, value='950.00')

    def test_no_change_correction_rejected(self):
        with self.assertRaisesRegex(ValueError, 'must change'):
            self.correction()

    def test_invalid_provenance_rejected(self):
        with self.assertRaisesRegex(ValueError, 'source must match'):
            self.correction(value='900.00', source='another.pdf')

    def test_unsupported_field_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported correction'):
            self.correction(field='password', value='x')

    def test_actor_system_reserved(self):
        with self.assertRaisesRegex(ValueError, 'reserved'):
            decide(self.ledger, actor='system', decision='approve', reason='ok', expected_revision=1)

    def test_arabic_values_and_evidence(self):
        arabic = extract(SAMPLE.parent / 'arabic_quote.txt')
        state = inspect(begin(arabic))
        self.assertIn('شركة', state['fields']['supplier'])
        self.assertEqual(state['fields']['total'], '945.00')

    def test_bad_source_starts_pending_not_approved(self):
        state = inspect(begin(extract(BAD)))
        self.assertFalse(state['checks']['vat_matches_rate'])
        with self.assertRaisesRegex(ValueError, 'Cannot approve'):
            decide(begin(extract(BAD)), actor='reviewer', decision='approve', reason='ok', expected_revision=1)

    def test_ledger_serialization_and_atomic_update(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'ledger.json'
            _save_new(path, self.ledger)
            self.assertEqual(inspect(_load(path))['revision'], 1)
            with self.assertRaises(FileExistsError):
                _save_new(path, self.ledger)
            reviewed = decide(_load(path), actor='reviewer', decision='approve', reason='ok', expected_revision=1)
            _save_update(path, reviewed)
            self.assertEqual(inspect(_load(path))['status'], 'approved')

    def test_ledger_has_no_secret_or_auth_claim(self):
        self.assertNotIn('authenticated', json.dumps(inspect(self.ledger)))
        self.assertNotIn('api_key', json.dumps(self.ledger))

    def test_money_precision_rejected(self):
        with self.assertRaisesRegex(ValueError, 'two decimal places'):
            self.correction(value='1050.001')

    def test_timestamp_is_in_history(self):
        reviewed = decide(self.ledger, actor='reviewer', decision='approve', reason='yes', expected_revision=1,
                          timestamp='2026-05-01T00:00:00+00:00')
        self.assertEqual(inspect(reviewed)['history'][-1]['timestamp'], '2026-05-01T00:00:00+00:00')


if __name__ == '__main__':
    unittest.main()
