import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from pathlib import Path
import subprocess
import pymupdf

from nawa_demo.authorization import Principal
from nawa_demo.correction_source_check import load_intake_text, verify_line
from nawa_demo.scoped_state import ScopedState, validate_correction_source_policy


class CorrectionSourceCheckTests(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.document = uuid4()
        self.conn.execute.return_value.fetchone.return_value = (self.document, 'synthetic.txt', 'a' * 64)
        self.principal = Principal('synthetic-subject', 'tenant-a', 'analyst')
        self.quote = {'document':'synthetic.txt'}
        self.store = MagicMock()
        self.store.read_verified.return_value = b'first line\nSubtotal: 1000.00\n'

    def test_exact_line_uses_tenant_scoped_digest_verified_source(self):
        filename, lines = load_intake_text(self.conn, self.principal, 'q1', self.quote, self.store)
        self.assertEqual(verify_line('synthetic.txt', 2, 'Subtotal: 1000.00', filename, lines),
                         {'kind':'txt_line', 'line':2})
        self.assertEqual(self.conn.execute.call_args.args[1], ('tenant-a', 'q1'))
        self.store.read_verified.assert_called_once_with(self.document.hex, 'a' * 64)

    def test_wrong_line_excerpt_and_invalid_line_are_rejected(self):
        filename, lines = load_intake_text(self.conn, self.principal, 'q1', self.quote, self.store)
        for source, line, excerpt in [('synthetic.txt', 1, 'Subtotal: 1000.00'),
                                      ('synthetic.txt', 2, 'forged'),
                                      ('other.txt', 2, 'Subtotal: 1000.00'),
                                      ('synthetic.txt', True, 'first line'),
                                      ('synthetic.txt', 99, 'first line')]:
            with self.subTest(line=line, excerpt=excerpt), self.assertRaises(ValueError):
                verify_line(source, line, excerpt, filename, lines)

    def test_missing_mapping_or_unavailable_source_fails_closed(self):
        self.conn.execute.return_value.fetchone.return_value = None
        with self.assertRaises(ValueError):
            load_intake_text(self.conn, self.principal, 'q1', self.quote, self.store)
        self.store.read_verified.assert_not_called()
        self.conn.execute.return_value.fetchone.return_value = (self.document, 'synthetic.txt', 'a' * 64)
        self.store.read_verified.side_effect = ValueError('Source hash mismatch')
        with self.assertRaises(ValueError):
            load_intake_text(self.conn, self.principal, 'q1', self.quote, self.store)

    def test_pdf_invalid_utf8_and_wrong_document_are_not_claimed_verified(self):
        self.conn.execute.return_value.fetchone.return_value = (self.document, 'synthetic.pdf', 'a' * 64)
        with self.assertRaises(ValueError):
            load_intake_text(self.conn, self.principal, 'q1', {'document':'synthetic.pdf'}, self.store)
        self.conn.execute.return_value.fetchone.return_value = (self.document, 'synthetic.txt', 'a' * 64)
        with self.assertRaises(ValueError):
            load_intake_text(self.conn, self.principal, 'q1', {'document':'other.txt'}, self.store)
        self.store.read_verified.return_value = b'\xff'
        with self.assertRaises(ValueError):
            load_intake_text(self.conn, self.principal, 'q1', self.quote, self.store)

    def test_required_policy_requires_store_and_rejects_unknown_mode(self):
        with self.assertRaises(ValueError):
            ScopedState(MagicMock(), correction_source_policy='require_intake_txt')
        with self.assertRaises(ValueError):
            validate_correction_source_policy('typo')

    def test_only_pinned_pdf_is_accepted_and_raw_lines_are_not_normalized(self):
        source = Path(__file__).resolve().parents[1] / 'samples/pdf/arabic_text_supplier.pdf'
        self.conn.execute.return_value.fetchone.return_value = (self.document, 'synthetic.pdf', 'a' * 64)
        self.store.read_verified.return_value = source.read_bytes()
        filename, lines = load_intake_text(self.conn, self.principal, 'q1', {'document':'synthetic.pdf'},
                                           self.store, allow_fixture_pdf=True)
        self.assertEqual(lines[5]['text'], 'Grand Total: 945.00')
        self.assertEqual(verify_line(filename, 6, 'Grand Total: 945.00', filename, lines),
                         {'kind':'pdf_text_layer', 'global_line':6, 'page':1, 'page_line':6})
        self.assertNotEqual(lines[2]['text'], 'المجموع الفرعي: ٩٠٠٫٠٠')
        with self.assertRaises(ValueError):
            verify_line(filename, 3, 'المجموع الفرعي: ٩٠٠٫٠٠', filename, lines)
        self.store.read_verified.return_value = source.read_bytes() + b'altered'
        with self.assertRaises(ValueError):
            load_intake_text(self.conn, self.principal, 'q1', {'document':'synthetic.pdf'},
                             self.store, allow_fixture_pdf=True)

    def test_pinned_multipage_pdf_resolves_global_line_to_page(self):
        source = Path(__file__).resolve().parents[1] / 'samples/pdf/second_page_supplier.pdf'
        self.conn.execute.return_value.fetchone.return_value = (self.document, 'synthetic.pdf', 'a' * 64)
        self.store.read_verified.return_value = source.read_bytes()
        filename, lines = load_intake_text(self.conn, self.principal, 'q1', {'document':'synthetic.pdf'},
                                           self.store, allow_fixture_pdf=True)
        self.assertEqual(verify_line(filename, 7, 'Grand Total: 945.00', filename, lines),
                         {'kind':'pdf_text_layer', 'global_line':7, 'page':2, 'page_line':6})
        with self.assertRaises(ValueError):
            verify_line(filename, 6, 'Grand Total: 945.00', filename, lines)

    def test_pdf_timeout_is_rejected_without_exposing_error_details(self):
        from nawa_demo.correction_source_check import fixture_pdf_lines
        source = Path(__file__).resolve().parents[1] / 'samples/pdf/arabic_text_supplier.pdf'
        with patch('nawa_demo.correction_source_check.subprocess.run',
                   side_effect=subprocess.TimeoutExpired('sensitive parser detail', 20)):
            with self.assertRaises(ValueError) as caught:
                fixture_pdf_lines(source.read_bytes())
        self.assertNotIn('sensitive parser detail', str(caught.exception))

    def test_opt_in_checks_unlisted_synthetic_text_layer_with_page_location(self):
        document = pymupdf.open()
        document.new_page().insert_text((50, 60), 'Synthetic cover page')
        document.new_page().insert_text((50, 60), 'Grand Total: 315.00')
        content = document.tobytes()
        document.close()
        self.conn.execute.return_value.fetchone.return_value = (self.document, 'synthetic.pdf', 'a' * 64)
        self.store.read_verified.return_value = content
        with self.assertRaises(ValueError):
            load_intake_text(self.conn, self.principal, 'q1', {'document':'synthetic.pdf'},
                             self.store, allow_fixture_pdf=True)
        filename, lines = load_intake_text(self.conn, self.principal, 'q1', {'document':'synthetic.pdf'},
                                          self.store, allow_strict_text_layer=True)
        self.assertEqual(verify_line(filename, 2, 'Grand Total: 315.00', filename, lines),
                         {'kind':'pdf_text_layer', 'global_line':2, 'page':2, 'page_line':1})

    def test_opt_in_rejects_blank_encrypted_and_invalid_pdf(self):
        from nawa_demo.correction_source_check import fixture_pdf_lines
        document = pymupdf.open()
        document.new_page()
        blank = document.tobytes()
        encrypted = document.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw='synthetic-test')
        document.close()
        for value in (blank, encrypted, b'not a PDF'):
            with self.subTest(size=len(value)), self.assertRaises(ValueError):
                fixture_pdf_lines(value, allow_strict_text_layer=True)


if __name__ == '__main__':
    unittest.main()
