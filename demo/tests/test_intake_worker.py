from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import subprocess
from unittest.mock import patch

from nawa_demo.intake_jobs import IntakeJobs
from nawa_demo.intake_pipeline import SyntheticIntakePipeline
from nawa_demo.intake_store import LocalIntakeStore
from nawa_demo.intake_worker import process_one


def synthetic_fixture(name):
    """Read an existing bundled fixture without changing it."""
    path = Path(__file__).resolve().parents[1] / 'samples' / 'pdf' / name
    return path.read_bytes()


class IntakeWorkerTests(unittest.TestCase):
    def test_parser_timeout_returns_retry_without_result(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'files')
            jobs = IntakeJobs(root / 'jobs.db')
            doc, _ = SyntheticIntakePipeline(store, jobs).submit('a', 'x.txt', b'synthetic')
            with patch('nawa_demo.intake_worker.subprocess.run', side_effect=subprocess.TimeoutExpired('parser', 1)):
                self.assertEqual(process_one(jobs, store, 'a', timeout=1), 'retry-pending')
            self.assertIsNone(jobs.result('a', doc))

    def test_selectable_pdf_result_has_page_evidence(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'files')
            jobs = IntakeJobs(root / 'jobs.db')
            sample = synthetic_fixture('second_page_supplier.pdf')
            doc, _ = SyntheticIntakePipeline(store, jobs).submit('a', 'sample.pdf', sample)
            self.assertEqual(process_one(jobs, store, 'a'), 'completed')
            result = jobs.result('a', doc)
            self.assertEqual(result['input_type'], 'text_layer_pdf')
            self.assertEqual(result['evidence']['supplier']['page'], 2)

    def test_image_only_pdf_is_not_claimed_as_processed(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'files')
            jobs = IntakeJobs(root / 'jobs.db')
            sample = synthetic_fixture('image_only.pdf')
            doc, _ = SyntheticIntakePipeline(store, jobs).submit('a', 'scan.pdf', sample)
            self.assertEqual(process_one(jobs, store, 'a', max_attempts=1), 'failed')
            self.assertIsNone(jobs.result('a', doc))

    def test_extracts_synthetic_arabic_after_reopen(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'files')
            jobs = IntakeJobs(root / 'jobs.db')
            sample = (Path(__file__).resolve().parents[1] / 'samples' / 'arabic_quote.txt').read_bytes()
            doc, _ = SyntheticIntakePipeline(store, jobs).submit('a', 'arabic.txt', sample)
            self.assertEqual(process_one(jobs, store, 'a'), 'completed')
            result = IntakeJobs(root / 'jobs.db').result('a', doc)
            self.assertEqual(result['total'], '945.00')
            self.assertIsNone(jobs.result('b', doc))
            self.assertIsNone(process_one(jobs, store, 'a'))

    def test_integrity_failure_retries_then_fails_without_result(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'files')
            jobs = IntakeJobs(root / 'jobs.db')
            doc, _ = SyntheticIntakePipeline(store, jobs).submit('a', 'x.txt', b'valid utf8')
            (root / 'files' / doc).write_bytes(b'tampered')
            self.assertEqual(process_one(jobs, store, 'a', max_attempts=2), 'retry-pending')
            self.assertEqual(process_one(jobs, store, 'a', max_attempts=2), 'failed')
            self.assertIsNone(jobs.result('a', doc))


if __name__ == '__main__':
    unittest.main()
