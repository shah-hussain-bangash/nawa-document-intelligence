import unittest
from arabic_pdf_fixture_normalize import normalize_fixture_line


class ArabicPDFFixtureNormalizeTests(unittest.TestCase):
    def test_repairs_only_the_exact_synthetic_currency_order(self):
        fallback=lambda line:'base:'+line
        self.assertEqual(normalize_fixture_line(' AED :العملة ',fallback),'العملة: AED')
        self.assertEqual(normalize_fixture_line('USD :العملة',fallback),'base:USD :العملة')
        self.assertEqual(normalize_fixture_line('other',fallback),'base:other')


if __name__=='__main__':
    unittest.main()

