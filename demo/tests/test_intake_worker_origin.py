import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from nawa_demo.core import extract
from nawa_demo.intake_jobs import IntakeJobs
from nawa_demo.intake_pipeline import SyntheticIntakePipeline
from nawa_demo.intake_store import LocalIntakeStore
from nawa_demo.intake_worker import process_one

SAMPLE = Path(__file__).resolve().parents[1] / 'samples' / 'english_quote.txt'

class WorkerOriginTests(unittest.TestCase):
    def test_text_worker_sets_server_origin(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store, jobs = LocalIntakeStore(root / 'files'), IntakeJobs(root / 'jobs.db')
            document, _ = SyntheticIntakePipeline(store, jobs).submit('synthetic', 'example.txt', SAMPLE.read_bytes())
            self.assertEqual(process_one(jobs, store, 'synthetic'), 'completed')
            self.assertEqual(jobs.result('synthetic', document)['extraction_origin'], 'synthetic_text_worker_v1')

    def test_ocr_marked_parser_result_is_not_completed_or_relabelled(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store, jobs = LocalIntakeStore(root / 'files'), IntakeJobs(root / 'jobs.db')
            document, _ = SyntheticIntakePipeline(store, jobs).submit('synthetic', 'example.txt', SAMPLE.read_bytes())
            candidate = dict(extract(SAMPLE), input_type='ocr_pdf')
            def fake_parser(*args, stdout, **kwargs):
                stdout.write(json.dumps(candidate).encode('utf-8'))
                return subprocess.CompletedProcess(args, 0)
            with patch('nawa_demo.intake_worker.subprocess.run', side_effect=fake_parser):
                self.assertEqual(process_one(jobs, store, 'synthetic', max_attempts=1), 'failed')
            self.assertIsNone(jobs.result('synthetic', document))

if __name__ == '__main__':
    unittest.main()
