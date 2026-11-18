"""Phase 3 regression tests: Arabic text-layer, OCR opt-in and evidence metadata."""
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from nawa_demo.pdf_ingest import OCRUnavailable, PDFTextUnavailable, extract_pdf, compare_pdfs, _normalize_pdf_line

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "pdf"


class Phase3Tests(unittest.TestCase):
    def test_currency_label_extracted_in_visual_order(self):
        self.assertEqual(_normalize_pdf_line("AED :العملة"), "العملة: AED")
        self.assertEqual(_normalize_pdf_line("  aed: ﺍﻟﻌﻤﻠﺔ  "), "العملة: AED")
        self.assertEqual(_normalize_pdf_line("USD :العملة"), "USD :العملة")

    def test_explicit_page_and_text_limits(self):
        with self.assertRaisesRegex(ValueError,'page limit'):
            extract_pdf(SAMPLES/'second_page_supplier.pdf',max_pages=1)
        with self.assertRaisesRegex(ValueError,'text limit'):
            extract_pdf(SAMPLES/'english_supplier.pdf',max_text_chars=10)
        with self.assertRaises(ValueError):
            extract_pdf(SAMPLES/'english_supplier.pdf',max_pages=True)

    def test_arabic_text_layer(self):
        q = extract_pdf(SAMPLES / "arabic_text_supplier.pdf")
        self.assertEqual(q["supplier"], "شركة المثال للتوريدات")
        self.assertEqual(q["total"], "945.00")
        self.assertEqual(q["evidence"]["total"]["page"], 1)
        self.assertEqual(q["evidence"]["total"]["method"], "text_layer")
        self.assertEqual(q["ocr_pages"], [])

    def test_arabic_pdf_compares_to_english(self):
        r = compare_pdfs([SAMPLES / "english_supplier.pdf", SAMPLES / "arabic_text_supplier.pdf"])
        self.assertEqual(r["lowest_valid_total"], "شركة المثال للتوريدات")

    def test_default_scanned_error(self):
        with self.assertRaisesRegex(PDFTextUnavailable, "need OCR"):
            extract_pdf(SAMPLES / "image_only.pdf")

    def test_ocr_binary_missing(self):
        with patch("nawa_demo.pdf_ingest.shutil.which", return_value=None):
            with self.assertRaises(OCRUnavailable):
                extract_pdf(SAMPLES / "image_only.pdf", ocr=True)

    @unittest.skipUnless(shutil.which("tesseract"), "Tesseract is not installed")
    def test_scanned_english_ocr(self):
        q = extract_pdf(SAMPLES / "scanned_english_supplier.pdf", ocr=True, languages="eng")
        self.assertEqual(q["supplier"], "Example English Supplies")
        self.assertEqual(q["total"], "1050.00")
        self.assertEqual(q["ocr_pages"], [1])
        self.assertEqual(q["evidence"]["total"]["method"], "ocr")


if __name__ == "__main__":
    unittest.main()

