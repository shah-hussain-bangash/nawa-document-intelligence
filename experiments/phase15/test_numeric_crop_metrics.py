import unittest
from best_numeric_crop_experiment import numeric

class NumericComparisonTests(unittest.TestCase):
    def test_arabic_and_ascii_digits_with_decimal_point(self):
        self.assertEqual(numeric('٩٠٠٫٠٠'), numeric('900.00'))

    def test_text_or_embedded_letters_are_not_treated_as_numbers(self):
        self.assertIsNone(numeric('total: 900.00'))
        self.assertIsNone(numeric('9O0.00'))

    def test_decimal_and_thousands_punctuation_are_not_guessed(self):
        self.assertNotEqual(numeric('900,00'), numeric('900.00'))

if __name__ == '__main__':
    unittest.main()
