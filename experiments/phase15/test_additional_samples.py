import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import additional_samples as samples

class SyntheticReproductionTests(unittest.TestCase):
    def test_existing_result_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.json'
            output.write_text('keep me', encoding='utf-8')
            argv = ['additional_samples.py', '--pdf-dir', directory, '--tesseract', 'unused',
                    '--tessdata', directory, '--output', str(output)]
            with patch.object(sys, 'argv', argv):
                with self.assertRaises(FileExistsError):
                    samples.main()
            self.assertEqual(output.read_text(encoding='utf-8'), 'keep me')

    def test_changed_fixture_rejected_before_ocr(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'case.pdf').write_bytes(b'changed')
            argv = ['additional_samples.py', '--pdf-dir', directory, '--tesseract', 'unused',
                    '--tessdata', directory, '--output', str(Path(directory) / 'result.json')]
            with patch.object(sys, 'argv', argv), patch.object(samples.bench, 'MODEL_HASHES', {}), \
                 patch.object(samples, 'PDF_HASHES', {'case.pdf':'0' * 64}), \
                 patch.object(samples.subprocess, 'run') as run:
                with self.assertRaises(ValueError):
                    samples.main()
                run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
