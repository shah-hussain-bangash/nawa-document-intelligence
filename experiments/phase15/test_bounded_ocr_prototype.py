import sys
import hashlib
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from bounded_ocr_prototype import (bounded_process, recognize_synthetic_png,
                                   recognize_with_model_provenance, OCRLimitError)

class BoundedProcessTests(unittest.TestCase):
    def test_captures_small_output(self):
        self.assertEqual(bounded_process([sys.executable, '-c', "print('hello')"]), b'hello\r\n' if sys.platform == 'win32' else b'hello\n')

    def test_rejects_excessive_output(self):
        with self.assertRaises(OCRLimitError):
            bounded_process([sys.executable, '-c', "print('x' * 100000)"], max_output=100)

    def test_stops_timed_out_child(self):
        with self.assertRaises(OCRLimitError):
            bounded_process([sys.executable, '-c', 'import time; time.sleep(10)'], timeout=0.2)

    def test_descendant_holding_stdout_does_not_block_caller(self):
        child = 'import time; time.sleep(2)'
        parent = 'import subprocess,sys; subprocess.Popen([sys.executable,"-c",%r])' % child
        start = time.monotonic()
        with self.assertRaises(OCRLimitError):
            bounded_process([sys.executable, '-c', parent], timeout=0.5)
        self.assertLess(time.monotonic() - start, 1.5)

    def test_rejects_failure_status(self):
        with self.assertRaises(OCRLimitError):
            bounded_process([sys.executable, '-c', 'raise SystemExit(7)'])

    def test_rejects_non_png_before_running_ocr(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'image.png'
            path.write_bytes(b'not a PNG')
            with self.assertRaises(OCRLimitError):
                recognize_synthetic_png(path, 'not-an-executable', '.', 'eng')

    def test_rejects_large_dimensions_before_running_ocr(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'large.png'
            Image.new('1', (4000, 3100), 1).save(path)
            with self.assertRaises(OCRLimitError):
                recognize_synthetic_png(path, 'not-an-executable', '.', 'eng')

    def test_rejects_unapproved_language(self):
        with self.assertRaises(ValueError):
            recognize_synthetic_png('unused', 'unused', '.', 'other')

    def test_ocr_reads_validated_copy_when_original_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'image.png'
            Image.new('RGB', (4, 4), 'white').save(path)
            original = path.read_bytes()
            def fake_ocr(command):
                path.write_bytes(b'changed after validation')
                self.assertNotEqual(Path(command[1]), path)
                self.assertEqual(Path(command[1]).read_bytes(), original)
                return b'synthetic output'
            with patch('bounded_ocr_prototype.bounded_process', side_effect=fake_ocr):
                result = recognize_synthetic_png(path, 'example', '.', 'eng')
            self.assertEqual(result['status'], 'human_review_required')
            self.assertEqual(result['extracted_text_untrusted'], 'synthetic output')

    def test_incorrect_model_hash_rejects_before_ocr(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'eng.traineddata').write_bytes(b'model')
            with patch('bounded_ocr_prototype.bounded_process') as runner:
                with self.assertRaises(OCRLimitError):
                    recognize_with_model_provenance('unused', 'unused', directory, 'eng',
                                                    {'eng.traineddata':'0' * 64})
                runner.assert_not_called()

    def test_model_change_during_ocr_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / 'eng.traineddata'
            model.write_bytes(b'model')
            digest = hashlib.sha256(b'model').hexdigest()
            def ocr(*args):
                model.write_bytes(b'changed')
                return {'status':'human_review_required'}
            with patch('bounded_ocr_prototype.bounded_process', return_value=b'tesseract vtest\n'):
                with patch('bounded_ocr_prototype.recognize_synthetic_png', side_effect=ocr):
                    with self.assertRaises(OCRLimitError):
                        recognize_with_model_provenance('unused', 'unused', directory, 'eng',
                                                       {'eng.traineddata':digest})

if __name__ == '__main__':
    unittest.main()
