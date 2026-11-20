"""End-to-end process plumbing with a synthetic engine, not an OCR accuracy test."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image
from bounded_ocr_prototype import OCRLimitError, recognize_with_pinned_engine
from windows_gated_bounded import GatedRunError, run_gated_bounded
from windows_image_validation import validate_png_in_job

@unittest.skipUnless(os.name == 'nt', 'Windows-only synthetic process test')
class WindowsOcrEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nawa_synthetic_e2e_')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / 'synthetic.png'
        Image.new('RGB', (5, 5), 'white').save(self.image)
        self.image_hash = hashlib.sha256(self.image.read_bytes()).hexdigest()
        (self.root / 'eng.traineddata').write_bytes(b'synthetic model')
        self.model_hash = hashlib.sha256(b'synthetic model').hexdigest()
        self.engine = self.root / 'synthetic-engine.exe'
        self.engine.write_bytes(b'synthetic engine identity only')
        self.engine_hash = hashlib.sha256(self.engine.read_bytes()).hexdigest()

    def test_synthetic_engine_receives_checked_copy_and_requires_review(self):
        calls = []
        def runner(command, **limits):
            calls.append(command)
            if command[-1] == '--version':
                code = "print('synthetic engine 1')"
                return run_gated_bounded([sys.executable, '-c', code], **limits)
            code = ('import hashlib,pathlib,sys; '
                    'assert hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest()==sys.argv[2]; '
                    'print("synthetic evidence")')
            return run_gated_bounded([sys.executable, '-c', code, command[1], self.image_hash], **limits)
        result = recognize_with_pinned_engine(self.image, self.engine, self.root,
            'eng', {'eng.traineddata':self.model_hash}, self.engine_hash, runner=runner,
            validator=validate_png_in_job)
        self.assertEqual(len(calls), 2)
        self.assertNotEqual(Path(calls[1][1]), self.image)
        self.assertEqual(result['source_sha256'], self.image_hash)
        self.assertEqual(result['model_sha256']['eng.traineddata'], self.model_hash)
        self.assertEqual(result['engine_sha256'], self.engine_hash)
        self.assertEqual(result['extracted_text_untrusted'].strip(), 'synthetic evidence')
        self.assertEqual(result['status'], 'human_review_required')

    def test_engine_failure_does_not_return_a_review_result(self):
        def runner(command, **limits):
            code = "print('synthetic engine 1')" if command[-1] == '--version' else 'raise SystemExit(4)'
            return run_gated_bounded([sys.executable, '-c', code], **limits)
        with self.assertRaises(GatedRunError):
            recognize_with_pinned_engine(self.image, self.engine, self.root,
                'eng', {'eng.traineddata':self.model_hash}, self.engine_hash, runner=runner,
                validator=validate_png_in_job)

    def test_engine_digest_mismatch_prevents_gated_launch(self):
        calls = []
        def runner(command, **limits):
            calls.append(command)
            raise AssertionError('Runner must not start')
        with self.assertRaises(OCRLimitError):
            recognize_with_pinned_engine(self.image, self.engine, self.root,
                'eng', {'eng.traineddata':self.model_hash}, '0' * 64, runner=runner)
        self.assertEqual(calls, [])

if __name__ == '__main__':
    unittest.main()
