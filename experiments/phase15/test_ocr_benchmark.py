import unittest
from ocr_benchmark import distance, field_results, normalize, rates


class OCRBenchmarkTests(unittest.TestCase):
    def test_edit_distance_and_error_rates(self):
        self.assertEqual(distance('kitten','sitting'),3)
        self.assertEqual(rates('one two','one two'),{'cer':0,'wer':0})
        self.assertEqual(rates('one two','one')['wer'],0.5)

    def test_partial_and_incorrect_fields_are_not_counted_correct(self):
        expected={'currency':'AED','total':'945.00'}
        self.assertEqual(field_results('العملة: AED\nالإجمالي شامل الضريبة: ٩٤٥٫٠٠',expected),
                         {'currency':True,'total':True})
        self.assertEqual(field_results('العملة: AED\nالإجمالي شامل الضريبة: ٩٤٦٫٠٠',expected),
                         {'currency':True,'total':False})
        self.assertEqual(field_results('Currency: AED\nCurrency: USD',{'currency':'AED'}),{'currency':False})

    def test_unicode_format_marks_are_removed(self):
        self.assertEqual(normalize('AED\u200f  نص'),'AED نص')

    def test_numeric_grouping_is_validated_before_removing_commas(self):
        expected = {'total': '1050.00'}
        for text in ('Grand Total: 1,050.00', 'Grand Total: ١٬٠٥٠٫٠٠'):
            with self.subTest(text=text):
                self.assertTrue(field_results(text, expected)['total'])
        for text in ('Grand Total: 10,50.00', 'Grand Total: 1,05,0.00',
                     'Grand Total: 1050,.00'):
            with self.subTest(text=text):
                self.assertFalse(field_results(text, expected)['total'])

    def test_supplier_punctuation_is_not_discarded(self):
        self.assertFalse(field_results('Supplier: Example, Supplies',
                                       {'supplier': 'Example Supplies'})['supplier'])


if __name__=='__main__':
    unittest.main()
