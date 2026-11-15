"""PDF tests run with the synthetic PDFs included in demo/samples/pdf/."""
import unittest
from pathlib import Path
from nawa_demo.pdf_ingest import PDFTextUnavailable, compare_pdfs, extract_pdf

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "pdf"


class PDFIngestTests(unittest.TestCase):
    def test_valid_pdf_extraction(self):
        q = extract_pdf(SAMPLES / "english_supplier.pdf")
        self.assertEqual(q["supplier"], "Example English Supplies")
        self.assertEqual(q["total"], "1050.00")
        self.assertEqual(q["evidence"]["total"]["page"], 1)
        self.assertTrue(all(q["checks"].values()))

    def test_multipage_evidence(self):
        q = extract_pdf(SAMPLES / "second_page_supplier.pdf")
        self.assertEqual(q["evidence"]["supplier"]["page"], 2)
        self.assertEqual(q["evidence"]["total"]["page"], 2)
        self.assertEqual(q["page_count"], 2)

    def test_comparison(self):
        r = compare_pdfs([SAMPLES / "english_supplier.pdf", SAMPLES / "second_page_supplier.pdf"])
        self.assertEqual(r["lowest_valid_total"], "Example Page Two Supplies")

    def test_scanned_pdf_requires_ocr(self):
        with self.assertRaisesRegex(PDFTextUnavailable, "need OCR"):
            extract_pdf(SAMPLES / "image_only.pdf")

    def test_invalid_vat_is_flagged(self):
        q = extract_pdf(SAMPLES / "incorrect_vat.pdf")
        self.assertFalse(q["checks"]["vat_matches_rate"])

    def test_minimum_documents(self):
        with self.assertRaisesRegex(ValueError, "At least two"):
            compare_pdfs([SAMPLES / "english_supplier.pdf"])


if __name__ == "__main__":
    unittest.main()
