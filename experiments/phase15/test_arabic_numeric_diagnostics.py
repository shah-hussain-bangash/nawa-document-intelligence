import unittest
from arabic_numeric_diagnostics import diagnose


class ArabicNumericDiagnosticsTests(unittest.TestCase):
    def test_ambiguous_comma_is_not_interpreted(self):
        result = diagnose('المجموع الفرعي١٢٠٠،٠٠')
        self.assertEqual(result['reasons']['subtotal'], 'ambiguous_arabic_comma')
        self.assertEqual(result['status'], 'human_review_required')
        self.assertIs(result['promotable'], False)

    def test_valid_looking_number_is_only_an_unverified_candidate(self):
        self.assertEqual(diagnose('المجموع الفرعي: ٩٠٠٫٠٠')['reasons']['subtotal'],
                         'unverified_numeric_candidate')

    def test_missing_malformed_and_duplicate_are_distinct(self):
        text = 'نسبة الضريبة\nقيمة الضريبة: ??\nالإجمالي شامل الضريبة ٩٤٥٫٠٠\nالإجمالي شامل الضريبة'
        reasons = diagnose(text)['reasons']
        self.assertEqual(reasons['vat_rate'], 'value_missing')
        self.assertEqual(reasons['vat_amount'], 'unrecognized_number')
        self.assertEqual(reasons['total'], 'duplicate_label')
        self.assertEqual(reasons['subtotal'], 'exact_label_not_found')

    def test_misspelled_and_embedded_labels_are_not_guessed(self):
        result = diagnose('قيمة الضرية٤٥٫٠٠\nتفاصيل المجموع الفرعي ٩٠٠٫٠٠')
        self.assertEqual(result['reasons']['vat_amount'], 'exact_label_not_found')
        self.assertEqual(result['reasons']['subtotal'], 'exact_label_not_found')

    def test_rejects_non_text(self):
        with self.assertRaises(ValueError):
            diagnose(None)


if __name__ == '__main__':
    unittest.main()
