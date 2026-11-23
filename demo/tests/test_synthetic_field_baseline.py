"""Small development-fixture replay; not independently reviewed ground truth."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from nawa_demo.synthetic_field_baseline import evaluate_fixture

SAMPLES = Path(__file__).resolve().parents[1] / 'samples'


class SyntheticFieldBaselineTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((SAMPLES / 'evaluation/draft_field_review.json').read_text(encoding='utf-8'))

    def test_three_draft_text_fixtures_and_vat_mismatch(self):
        report = evaluate_fixture(SAMPLES, self.fixture)
        self.assertEqual((report['case_count'], report['cases_with_draft_labels']), (3,3))
        self.assertTrue(report['development_only'])
        self.assertTrue(all(item['matches_draft'] for item in report['arithmetic_checks']))
        mismatch = next(item for item in report['arithmetic_checks'] if item['id'] == 'en_vat_mismatch')
        self.assertFalse(mismatch['observed']['vat_matches_rate'])
        self.assertTrue(mismatch['observed']['total_matches_components'])
        self.assertEqual(report['by_language_and_field']['ar']['total']['correct'], 1)

    def test_modified_source_and_promoted_labels_are_rejected(self):
        fixture = deepcopy(self.fixture)
        fixture['cases'][0]['label_status'] = 'reviewed'
        with self.assertRaises(ValueError):
            evaluate_fixture(SAMPLES, fixture)
        with TemporaryDirectory() as folder:
            for item in self.fixture['cases']:
                shutil.copyfile(SAMPLES / item['source'], Path(folder) / item['source'])
            (Path(folder) / 'english_quote.txt').write_bytes(b'changed synthetic source')
            with self.assertRaises(ValueError):
                evaluate_fixture(folder, self.fixture)


if __name__ == '__main__':
    unittest.main()
