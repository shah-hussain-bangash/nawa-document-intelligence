"""Small hand-authored tests; not an independent benchmark."""
import unittest

from nawa_demo.structured_financial_claims import check_structured_claim


class StructuredFinancialClaimsTests(unittest.TestCase):
    def check(self, field, amount, source):
        return check_structured_claim({'field':field, 'amount':amount, 'currency':'AED'}, source)

    def test_swapped_subtotal_and_total_are_not_supported(self):
        self.assertFalse(self.check('subtotal', '1050.00', 'Subtotal AED 1000.00')['field_value_match'])
        self.assertFalse(self.check('subtotal', '1050.00', 'Grand total AED 1050.00')['field_value_match'])
        self.assertFalse(self.check('subtotal', '1050.00',
            'Subtotal AED 1000.00 and Grand total AED 1050.00')['field_value_match'])

    def test_matching_english_and_arabic_lines_remain_review_only(self):
        for field, amount, line in (
            ('subtotal', '1000.00', 'Subtotal AED 1000.00'),
            ('total', '1050', 'Grand total: AED 1050.00'),
            ('vat_amount', '45.00', 'قيمة الضريبة: AED ٤٥٫٠٠'),
        ):
            with self.subTest(line=line):
                result = self.check(field, amount, line)
                self.assertEqual(result, {'status':'requires_human_review','field_value_match':True})

    def test_ambiguous_or_unsupported_evidence_is_withheld(self):
        for line in ('Subtotal AED 1,000.00', 'Subtotal USD 1000.00',
                     'Subtotal AED 1000.00 but excludes delivery', 'Not subtotal AED 1000.00',
                     'Subtotal AED 1000.00\nSubtotal AED 2000.00', 'Subtotal AED NaN',
                     'Subtotal\nAED 1000.00', 'Subtotal\r\nAED 1000.00',
                     'Subtotal\u2028AED 1000.00', 'Subtotal AED 1000.00\n'):
            with self.subTest(line=line):
                self.assertFalse(self.check('subtotal', '1000', line)['field_value_match'])
        self.assertFalse(self.check('subtotal', '-1000', 'Subtotal AED 1000')['field_value_match'])
        self.assertFalse(check_structured_claim({'field':'subtotal','amount':1000,'currency':'AED'},
                                                'Subtotal AED 1000')['field_value_match'])


if __name__ == '__main__':
    unittest.main()
