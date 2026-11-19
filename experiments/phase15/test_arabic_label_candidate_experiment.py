import json
from pathlib import Path
import unittest
from arabic_label_candidate_experiment import candidates, evaluate
import ocr_benchmark as bench


class ArabicLabelCandidateExperimentTests(unittest.TestCase):
    def test_supplier_with_no_colon(self):
        result = evaluate('اسم المورد شركة المثال للتوريدات',
                          {'supplier':'شركة المثال للتوريدات'})
        self.assertEqual(result['fields_correct'], 1)
        self.assertEqual(result['status'], 'human_review_required')
        self.assertIs(result['promotable'], False)

    def test_known_numeric_label_adjacent_to_digits(self):
        result = evaluate('المجموع الفرعي٩٠٠٫٠٠', {'subtotal':'900.00'})
        self.assertTrue(result['field_matches']['subtotal'])

    def test_incorrect_or_ambiguous_numbers_are_not_matched(self):
        expected = {'total':'945.00'}
        for text in ('الإجمالي شامل الضريبة٩٤٥،٠٠', 'الإجمالي شامل الضريبة٩٤٫٠٠',
                     'الإجمالي شامل الضريبة', 'الإجمالي شامل الضريبة٩٤٥:٠٠'):
            with self.subTest(text=text):
                self.assertFalse(evaluate(text, expected)['field_matches']['total'])

    def test_duplicate_labels_block_candidate_even_if_one_missing(self):
        for second in ('الإجمالي شامل الضريبة٩٤٥٫٠٠', 'الإجمالي شامل الضريبة'):
            with self.subTest(second=second):
                text = 'الإجمالي شامل الضريبة٩٤٥٫٠٠\n' + second
                self.assertNotIn('total', candidates(text))

    def test_partial_or_embedded_labels_are_not_recognized(self):
        for text in ('المجموع الفرعيالإضافي ٩٠٠٫٠٠', 'بيان المجموع الفرعي٩٠٠٫٠٠',
                     'قيمة الضرية٤٥٫٠٠'):
            with self.subTest(text=text):
                self.assertEqual(candidates(text), {})

    def test_text_values_need_a_boundary_and_multiple_labels_are_rejected(self):
        self.assertEqual(candidates('اسم الموردشركة المثال'), {})
        self.assertEqual(candidates('اسم المورد شركة المثال العملة: AED'), {})

    def test_saved_synthetic_page_only_matches_supplier(self):
        result = json.loads((Path(__file__).parent / 'paddle-arabic-page-result.json').read_text(encoding='utf-8'))
        matches = evaluate('\n'.join(result['lines_synthetic']), bench.SAMPLES[1]['fields'])
        self.assertEqual([key for key, value in matches['field_matches'].items() if value], ['supplier'])


if __name__ == '__main__':
    unittest.main()
