"""End-to-end process plumbing with a synthetic engine, not an OCR accuracy test."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image
from bounded_ocr_prototype import recognize_with_model_provenance
from windows_gated_bounded import GatedRunError, run_gated_bounded

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
        result = recognize_with_model_provenance(self.image, 'synthetic-engine', self.root,
            'eng', {'eng.traineddata':self.model_hash}, runner=runner)
        self.assertEqual(len(calls), 2)
        self.assertNotEqual(Path(calls[1][1]), self.image)
        self.assertEqual(result['source_sha256'], self.image_hash)
        self.assertEqual(result['model_sha256']['eng.traineddata'], self.model_hash)
        self.assertEqual(result['extracted_text_untrusted'].strip(), 'synthetic evidence')
        self.assertEqual(result['status'], 'human_review_required')

    def test_engine_failure_does_not_return_a_review_result(self):
        def runner(command, **limits):
            code = "print('synthetic engine 1')" if command[-1] == '--version' else 'raise SystemExit(4)'
            return run_gated_bounded([sys.executable, '-c', code], **limits)
        with self.assertRaises(GatedRunError):
            recognize_with_model_provenance(self.image, 'synthetic-engine', self.root,
                'eng', {'eng.traineddata':self.model_hash}, runner=runner)

if __name__ == '__main__':
    unittest.main()
