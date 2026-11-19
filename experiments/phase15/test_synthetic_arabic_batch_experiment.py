import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

import synthetic_arabic_batch_experiment as experiment
from paddle_arabic_page_experiment import evaluate_lines


class SyntheticArabicBatchTests(unittest.TestCase):
    def test_pinned_images_and_recorded_results(self):
        root = Path(__file__).parent
        pages = root / 'arabic-new-synthetic-pages'
        manifest_file = pages / 'manifest.json'
        self.assertEqual(experiment.digest(manifest_file), experiment.MANIFEST_SHA256)
        manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
        recorded = json.loads((root / 'synthetic-arabic-batch-result.json').read_text(encoding='utf-8'))
        self.assertEqual(recorded['status'], 'human_review_required')
        self.assertEqual(len(manifest['cases']), 2)
        for case, result in zip(manifest['cases'], recorded['cases'], strict=True):
            self.assertEqual(experiment.digest(pages / case['image']), experiment.IMAGE_SHA256[case['image']])
            self.assertEqual(case['id'], result['id'])
            for engine in ('tesseract', 'paddle'):
                metrics = evaluate_lines(result[engine]['lines_synthetic'],
                                         {'reference':case['lines'], 'fields':case['fields']})
                self.assertEqual(metrics['strict_field_matches'], result[engine]['strict_field_matches'])
                self.assertEqual(metrics['candidate_field_matches'], result[engine]['candidate_field_matches'])

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.json'
            output.write_text('keep', encoding='utf-8')
            argv = ['experiment', '--pages-dir', 'missing', '--det-dir', 'missing',
                    '--rec-dir', 'missing', '--qa-home', 'missing', '--output', str(output)]
            with patch.object(sys, 'argv', argv), self.assertRaises(FileExistsError):
                experiment.main()
            self.assertEqual(output.read_text(encoding='utf-8'), 'keep')


if __name__ == '__main__':
    unittest.main()
