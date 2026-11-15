import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from nawa_demo.core import compare, extract, find_fields, normalized_number

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


class QuotationTests(unittest.TestCase):
    def test_english(self):
        quote = extract(SAMPLES / "english_quote.txt")
        self.assertTrue(all(quote["checks"].values()))
        self.assertEqual(quote["total"], "1050.00")
        self.assertEqual(quote["evidence"]["total"]["line"], 6)

    def test_arabic_digits(self):
        quote = extract(SAMPLES / "arabic_quote.txt")
        self.assertTrue(all(quote["checks"].values()))
        self.assertEqual(quote["total"], "945.00")
        self.assertEqual(normalized_number("١٬٢٣٤٫٥٠"), "1234.50")

    def test_bad_vat_is_flagged(self):
        quote = extract(SAMPLES / "incorrect_vat_quote.txt")
        self.assertFalse(quote["checks"]["vat_matches_rate"])
        self.assertTrue(quote["checks"]["total_matches_components"])

    def test_compare_excludes_invalid(self):
        report = compare([SAMPLES / "english_quote.txt", SAMPLES / "arabic_quote.txt", SAMPLES / "incorrect_vat_quote.txt"])
        self.assertEqual(report["lowest_valid_total"], "شركة المثال للتوريدات")
        self.assertEqual(len(report["quotations"]), 3)

    def test_missing_fields(self):
        with self.assertRaisesRegex(ValueError, "Missing required fields"):
            find_fields("Supplier: Test\n")

    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError, "Repeated field"):
            find_fields("Supplier: One\nSupplier: Two\n")

    def test_reject_unsupported_currency(self):
        txt = (SAMPLES / "english_quote.txt").read_text().replace("AED", "USD")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "quote.txt"
            path.write_text(txt)
            with self.assertRaisesRegex(ValueError, "AED"):
                extract(path)

    def test_minimum_two_documents(self):
        with self.assertRaisesRegex(ValueError, "At least two"):
            compare([SAMPLES / "english_quote.txt"])


if __name__ == "__main__":
    unittest.main()
