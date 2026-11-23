import copy
import unittest
from pathlib import Path

from nawa_demo.core import extract
from nawa_demo.review import _digest, begin, inspect
from nawa_demo.synthetic_legacy_review import inspect_event_links


SAMPLE = Path(__file__).resolve().parents[1] / 'samples' / 'english_quote.txt'


class LegacyLinkTests(unittest.TestCase):
    def setUp(self):
        self.ledger = begin(extract(SAMPLE))

    def test_legacy_number_prevents_replay_but_links_can_be_inspected(self):
        event = {'sequence': 2, 'type': 'correction', 'actor': 'synthetic-reviewer',
                 'timestamp': '2026-01-02T00:00:00+00:00',
                 'data': {'field': 'total', 'from': '1050.00', 'to': '1,23', 'reason': 'synthetic',
                          'evidence': {'source': self.ledger['document'], 'line': 6, 'quote': 'synthetic'}},
                 'previous_hash': self.ledger['events'][0]['hash']}
        event['hash'] = _digest(event)
        self.ledger['events'].append(event)
        before = copy.deepcopy(self.ledger)
        with self.assertRaises(ValueError):
            inspect(self.ledger)
        report = inspect_event_links(self.ledger)
        self.assertTrue(report['event_links_match'])
        self.assertTrue(report['human_review_required'])
        self.assertEqual(report['events_examined'], 2)
        self.assertEqual(self.ledger, before)
        self.assertNotIn('1,23', str(report))

    def test_tampering_and_missing_links_are_detected(self):
        self.ledger['events'][0]['data']['fields']['total'] = '999'
        self.assertEqual(inspect_event_links(self.ledger)['reason'], 'event_hash_mismatch')
        self.ledger['events'][0]['previous_hash'] = 'wrong'
        self.assertEqual(inspect_event_links(self.ledger)['reason'], 'invalid_event_link')

    def test_malformed_records_fail_without_success_claim(self):
        for value in (None, {}, {'schema': 'nawa-review-v1', 'document': 'x', 'events': []}):
            with self.subTest(value=value):
                result = inspect_event_links(value)
                self.assertFalse(result['event_links_match'])
                self.assertTrue(result['human_review_required'])

    def test_outer_document_name_is_not_authenticated(self):
        self.ledger['document'] = 'other-synthetic-file.txt'
        result = inspect_event_links(self.ledger)
        self.assertTrue(result['event_links_match'])
        self.assertIn('no authenticity', result['scope'])


if __name__ == '__main__':
    unittest.main()
