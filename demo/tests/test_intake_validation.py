import hashlib
import unittest
import subprocess
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfWriter
from pypdf.errors import PdfReadError

from nawa_demo.intake_validation import MAX_DOCUMENT_BYTES, check_document
from nawa_demo.intake_pdf import open_pdf


class IntakeValidationTests(unittest.TestCase):
    def test_bilingual_text_metadata(self):
        data = 'عرض سعر\nQuotation'.encode('utf-8')
        result = check_document('عرض.txt', data)
        self.assertEqual(result.sha256, hashlib.sha256(data).hexdigest())
        self.assertEqual(result.size, len(data))
        self.assertEqual(result.media_type, 'text/plain')

    def test_invalid_names_and_content(self):
        for filename in ('../x.txt', r'..\x.txt', 'C:x.txt', '.x.txt', 'a\n.txt'):
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                check_document(filename, b'hello')
        for filename, data in (('x.pdf', b'hello'), ('x.txt', b'%PDF-1.7'),
                               ('x.txt', b'\xff'), ('x.txt', b'a\x00b'),
                               ('x.txt', b''), ('x.txt', b'a' * (MAX_DOCUMENT_BYTES + 1)),
                               ('x.exe', b'hello')):
            with self.subTest(filename=filename, size=len(data)), self.assertRaises(ValueError):
                check_document(filename, data)

    def test_pdf_structure_and_encryption(self):
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        content = BytesIO()
        writer.write(content)
        self.assertEqual(check_document('test.pdf', content.getvalue()).media_type, 'application/pdf')
        writer.encrypt('synthetic-password')
        encrypted = BytesIO()
        writer.write(encrypted)
        with self.assertRaises(ValueError):
            check_document('test.pdf', encrypted.getvalue())
        with self.assertRaises(ValueError):
            check_document('test.pdf', b'%PDF-1.7\n')

    def test_pdf_page_limit(self):
        writer = PdfWriter()
        for _ in range(51):
            writer.add_blank_page(width=100, height=100)
        content = BytesIO()
        writer.write(content)
        with self.assertRaises(ValueError):
            check_document('many.pdf', content.getvalue())

    def test_pdf_preflight_timeout_is_rejected(self):
        with patch('nawa_demo.intake_validation.subprocess.run',
                   side_effect=subprocess.TimeoutExpired('preflight', 10)):
            with self.assertRaisesRegex(ValueError, 'time limit'):
                check_document('sample.pdf', b'%PDF-1.7\n')

    def test_only_exact_known_fixture_gets_lenient_fallback(self):
        fixture = (Path(__file__).resolve().parents[1] / 'samples/pdf/english_supplier.pdf').read_bytes()
        self.assertEqual(check_document('synthetic.pdf', fixture).media_type, 'application/pdf')
        def parse(_stream, *, strict):
            if strict:
                raise PdfReadError('synthetic strict-parser failure')
            return 'lenient fallback used'
        with patch('nawa_demo.intake_pdf.PdfReader', side_effect=parse) as reader:
            self.assertEqual(open_pdf(fixture), 'lenient fallback used')
            self.assertEqual(reader.call_count, 2)
        with patch('nawa_demo.intake_pdf.PdfReader', side_effect=parse) as reader:
            with self.assertRaises(PdfReadError):
                open_pdf(fixture + b'changed')
            self.assertEqual(reader.call_count, 1)


if __name__ == '__main__':
    unittest.main()

