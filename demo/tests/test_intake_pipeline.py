from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tempfile import TemporaryDirectory
import unittest

from nawa_demo.intake_jobs import IntakeJobs
from nawa_demo.intake_pipeline import SyntheticIntakePipeline
from nawa_demo.intake_store import LocalIntakeStore
from nawa_demo.intake_validation import check_document


class PipelineTests(unittest.TestCase):
    def test_concurrent_duplicate_submissions_register_once(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            files = root / 'files'
            pipeline = SyntheticIntakePipeline(LocalIntakeStore(files), IntakeJobs(root / 'jobs.db'))
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda _: pipeline.submit('a', 'quote.txt', b'same'), range(4)))
            self.assertEqual(sum(created for _, created in results), 1)
            self.assertEqual(len({document_id for document_id, _ in results}), 1)
            self.assertEqual(len(list(files.iterdir())), 1)

    def test_duplicate_submission_keeps_one_file_and_job_after_reopen(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            files = root / 'files'
            jobs_path = root / 'jobs.db'
            pipeline = SyntheticIntakePipeline(LocalIntakeStore(files), IntakeJobs(jobs_path))
            content = 'عرض سعر / quotation'.encode('utf-8')
            document_id, created = pipeline.submit('tenant-a', 'quote.txt', content)
            self.assertTrue(created)
            self.assertEqual(pipeline.submit('tenant-a', 'duplicate.txt', content), (document_id, False))
            self.assertEqual([p.name for p in files.iterdir()], [document_id])
            self.assertEqual(IntakeJobs(jobs_path).state('tenant-a', document_id), ('validated', 0))
            self.assertEqual(LocalIntakeStore(files).read_verified(
                document_id, check_document('quote.txt', content).sha256), content)

    def test_database_failure_preserves_file_for_reconciliation(self):
        class FailingJobs:
            def register(self, *args):
                raise RuntimeError('synthetic database failure')
        with TemporaryDirectory() as folder:
            store = LocalIntakeStore(folder)
            with self.assertRaisesRegex(RuntimeError, 'synthetic database failure'):
                SyntheticIntakePipeline(store, FailingJobs()).submit('a', 'x.txt', b'test')
            self.assertEqual(len(list(Path(folder).iterdir())), 1)

    def test_uncertain_commit_never_deletes_committed_source(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'files')
            jobs = IntakeJobs(root / 'jobs.db')
            class UncertainJobs:
                def register(self, *args):
                    jobs.register(*args)
                    raise RuntimeError('simulated error after commit')
            with self.assertRaisesRegex(RuntimeError, 'after commit'):
                SyntheticIntakePipeline(store, UncertainJobs()).submit('a', 'x.txt', b'test')
            stored = list(store.directory.iterdir())
            self.assertEqual(len(stored), 1)
            self.assertEqual(jobs.state('a', stored[0].name), ('validated', 0))
            self.assertEqual(stored[0].read_bytes(), b'test')

    def test_invalid_upload_does_not_create_a_job(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            files = root / 'files'
            pipeline = SyntheticIntakePipeline(LocalIntakeStore(files), IntakeJobs(root / 'jobs.db'))
            with self.assertRaises(ValueError):
                pipeline.submit('a', 'x.pdf', b'not pdf')
            self.assertEqual(list(files.iterdir()), [])


if __name__ == '__main__':
    unittest.main()

