import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import paddle_arabic_page_experiment as experiment


class PaddleArabicPageExperimentTests(unittest.TestCase):
    def test_unlabeled_text_is_not_counted_as_a_field(self):
        sample = {'reference':['Grand Total: 1050.00'], 'fields':{'total':'1050.00'}}
        result = experiment.evaluate_lines(['Grand Total 1050.00'], sample)
        self.assertEqual(result['strict_fields_correct'], 0)
        self.assertEqual(result['rtl_fields_correct'], 0)
        self.assertEqual(result['candidate_fields_correct'], 0)

    def test_evaluates_strict_and_reversed_label_separately(self):
        sample = {'reference':['العملة: AED'], 'fields':{'currency':'AED'}}
        result = experiment.evaluate_lines(['AED :العملة'], sample)
        self.assertEqual(result['strict_fields_correct'], 0)
        self.assertEqual(result['rtl_fields_correct'], 1)

    def test_rejects_non_string_line(self):
        with self.assertRaises(ValueError):
            experiment.evaluate_lines([None], {'reference':['x'], 'fields':{}})

    def test_existing_result_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.json'
            output.write_text('keep', encoding='utf-8')
            argv = ['experiment', '--det-dir', 'missing', '--rec-dir', 'missing',
                    '--qa-home', 'missing', '--output', str(output)]
            with patch.object(sys, 'argv', argv), self.assertRaises(FileExistsError):
                experiment.main()
            self.assertEqual(output.read_text(encoding='utf-8'), 'keep')

    def test_saved_second_synthetic_page_matches_supplier_and_vat_rate(self):
        path = Path(__file__).parent / 'paddle-arabic-pdf-result.json'
        saved = json.loads(path.read_text(encoding='utf-8'))
        recalculated = experiment.evaluate_lines(saved['lines_synthetic'], experiment.PDF_SAMPLE)
        self.assertEqual(recalculated['candidate_field_matches'], saved['candidate_field_matches'])
        self.assertEqual([k for k, v in recalculated['candidate_field_matches'].items() if v],
                         ['supplier', 'vat_rate'])


if __name__ == '__main__':
    unittest.main()
