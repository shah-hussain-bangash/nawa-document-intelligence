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


if __name__=='__main__':
    unittest.main()

