from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from nawa_demo.intake_jobs import IntakeJobs
from nawa_demo.intake_validation import check_document


class IntakeJobsTests(unittest.TestCase):
    def test_persistence_dedup_and_tenant_separation(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'jobs.db'
            metadata = check_document('عرض.txt', 'عرض سعر'.encode('utf8'))
            jobs = IntakeJobs(path)
            self.assertEqual(jobs.register('a', 'id1', metadata), ('id1', True))
            self.assertEqual(jobs.register('a', 'id2', metadata), ('id1', False))
            self.assertEqual(jobs.register('b', 'id3', metadata), ('id3', True))
            reopened = IntakeJobs(path)
            self.assertEqual(reopened.state('a', 'id1'), ('validated', 0))
            self.assertIsNone(reopened.state('b', 'id1'))

    def test_expired_claim_recovered_and_retry_bounded(self):
        with TemporaryDirectory() as folder:
            jobs = IntakeJobs(Path(folder) / 'jobs.db')
            jobs.register('a', 'id1', check_document('x.txt', b'synthetic'))
            job, token = jobs.claim('a', 'one', now=100, lease_seconds=5, max_attempts=2)
            self.assertIsNone(jobs.claim('a', 'two', now=104, max_attempts=2))
            recovered_job, recovered_token = jobs.claim('a', 'two', now=105, max_attempts=2)
            self.assertEqual(recovered_job, job)
            with self.assertRaises(ValueError):
                jobs.finish('a', job, token, success=True, now=106, max_attempts=2)
            self.assertEqual(jobs.finish('a', job, recovered_token, success=False, now=106, max_attempts=2), 'failed')
            self.assertIsNone(jobs.claim('a', 'three', now=107, max_attempts=2))
            self.assertEqual(jobs.state('a', 'id1'), ('failed', 2))

    def test_successful_finish_and_wrong_tenant(self):
        with TemporaryDirectory() as folder:
            jobs = IntakeJobs(Path(folder) / 'jobs.db')
            jobs.register('a', 'id1', check_document('x.txt', b'demo'))
            job, token = jobs.claim('a', 'one', now=100)
            with self.assertRaises(ValueError):
                jobs.finish('b', job, token, success=True, now=101)
            self.assertEqual(jobs.finish('a', job, token, success=True, now=101), 'completed')


if __name__ == '__main__':
    unittest.main()

