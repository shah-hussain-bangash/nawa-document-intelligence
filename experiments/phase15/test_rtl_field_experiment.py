import unittest
from rtl_field_experiment import field_matches

class ReversedLabelTests(unittest.TestCase):
    def test_value_before_arabic_label(self):
        self.assertEqual(field_matches('\u200eAED\u200f :العملة', {'currency':'AED'}), {'currency':True})

    def test_normal_arabic_numeric_line(self):
        self.assertEqual(field_matches('المجموع الفرعي: ٩٠٠٫٠٠', {'subtotal':'900.00'}), {'subtotal':True})

    def test_duplicate_values_are_not_accepted(self):
        self.assertEqual(field_matches('AED :العملة\nالعملة: AED', {'currency':'AED'}), {'currency':False})

    def test_ambiguous_or_extra_colons_are_not_accepted(self):
        self.assertEqual(field_matches('currency: العملة\nAED :العملة: extra', {'currency':'AED'}), {'currency':False})

    def test_wrong_value_is_not_a_match(self):
        self.assertEqual(field_matches('USD :العملة', {'currency':'AED'}), {'currency':False})

    def test_malformed_grouping_is_not_counted_correct(self):
        expected = {'total': '1050.00'}
        self.assertTrue(field_matches('١٬٠٥٠٫٠٠ :الإجمالي شامل الضريبة', expected)['total'])
        self.assertFalse(field_matches('١٠٬٥٠٫٠٠ :الإجمالي شامل الضريبة', expected)['total'])

if __name__ == '__main__':
    unittest.main()
