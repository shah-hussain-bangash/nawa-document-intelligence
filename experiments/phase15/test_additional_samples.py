import sys
import hashlib
import json
import subprocess
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
            engine = Path(directory) / 'fake-engine'
            engine.write_bytes(b'synthetic-engine')
            argv = ['additional_samples.py', '--pdf-dir', directory, '--tesseract', str(engine),
                    '--tessdata', directory, '--output', str(Path(directory) / 'result.json')]
            with patch.object(sys, 'argv', argv), patch.object(samples.bench, 'MODEL_HASHES', {}), \
                 patch.object(samples, 'PDF_HASHES', {'case.pdf':{'0' * 64}}), \
                 patch.object(samples.subprocess, 'run') as run:
                with self.assertRaises(ValueError):
                    samples.main()
                run.assert_not_called()

    def test_records_engine_model_and_rendered_page_digests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = samples.pymupdf.open()
            document.new_page()
            pdf = document.tobytes()
            document.close()
            (root / 'case.pdf').write_bytes(pdf)
            engine = root / 'fake-engine'
            engine.write_bytes(b'synthetic-engine')
            model = root / 'synthetic.traineddata'
            model.write_bytes(b'synthetic-model')
            sha = lambda data: hashlib.sha256(data).hexdigest()
            case = {'file':'case.pdf', 'page':0, 'lang':'eng',
                    'reference':['Grand Total: 10.00'], 'fields':{'total':'10.00'}}
            argv = ['additional_samples.py', '--pdf-dir', directory, '--tesseract', str(engine),
                    '--tessdata', directory, '--output', str(root / 'result.json')]
            def fake_run(args, **kwargs):
                out = b'synthetic-engine 1.0\n' if '--version' in args else b'Grand Total: 10.00\n'
                return subprocess.CompletedProcess(args, 0, stdout=out, stderr=b'')
            with patch.object(sys, 'argv', argv), \
                 patch.object(samples.bench, 'MODEL_HASHES', {'synthetic.traineddata':sha(b'synthetic-model')}), \
                 patch.object(samples, 'PDF_HASHES', {'case.pdf':{sha(pdf)}}), \
                 patch.object(samples, 'CASES', [case]), patch.object(samples.subprocess, 'run', fake_run):
                samples.main()
            result = json.loads((root / 'result.json').read_text(encoding='utf-8'))
            self.assertEqual(result['engine_sha256'], sha(b'synthetic-engine'))
            self.assertEqual(result['model_sha256']['synthetic.traineddata'], sha(b'synthetic-model'))
            self.assertEqual(result['cases'][0]['pdf_sha256'], sha(pdf))
            self.assertEqual(len(result['cases'][0]['rendered_image_sha256']), 64)
            self.assertEqual(result['status'], 'human_review_required')

    def test_rejects_changed_engine_without_saving_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            engine = root / 'fake-engine'
            engine.write_bytes(b'before')
            argv = ['additional_samples.py', '--pdf-dir', directory, '--tesseract', str(engine),
                    '--tessdata', directory, '--output', str(root / 'result.json')]
            def fake_run(args, **kwargs):
                engine.write_bytes(b'after')
                return subprocess.CompletedProcess(args, 0, stdout=b'synthetic 1.0\n', stderr=b'')
            with patch.object(sys, 'argv', argv), patch.object(samples.bench, 'MODEL_HASHES', {}), \
                 patch.object(samples, 'PDF_HASHES', {}), patch.object(samples, 'CASES', []), \
                 patch.object(samples.subprocess, 'run', fake_run):
                with self.assertRaises(ValueError):
                    samples.main()
            self.assertFalse((root / 'result.json').exists())

if __name__ == '__main__':
    unittest.main()
