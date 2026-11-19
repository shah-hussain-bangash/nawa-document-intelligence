"""Synthetic process tests, not an isolation or security certification."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock
import windows_gated_launcher_experiment as launcher
import windows_cleanup_job

@unittest.skipUnless(os.name == 'nt', 'Windows-only local experiment')
class GatedLaunchTests(unittest.TestCase):
    def test_child_starts_only_after_assignment(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'started'
            code = 'from pathlib import Path; import sys; Path(sys.argv[1]).write_text("ran")'
            job = Mock()
            def attach(parent):
                self.assertIsNone(parent.poll())
                self.assertFalse(marker.exists())
            job.attach.side_effect = attach
            parent = launcher.start_gated(job, [sys.executable, '-c', code, str(marker)])
            try:
                self.assertEqual(parent.wait(timeout=5), 0)
                self.assertEqual(marker.read_text(), 'ran')
                job.attach.assert_called_once()
            finally:
                if parent.poll() is None:
                    parent.kill()
                    parent.wait(timeout=5)
                parent.stdout.close()

    def test_assignment_failure_does_not_start_child(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'should-not-exist'
            code = 'from pathlib import Path; import sys; Path(sys.argv[1]).write_text("ran")'
            job = Mock()
            job.attach.side_effect = RuntimeError('simulated refusal')
            with self.assertRaises(RuntimeError):
                launcher.start_gated(job, [sys.executable, '-c', code, str(marker)])
            self.assertFalse(marker.exists())

    def test_job_closure_stops_started_synthetic_child(self):
        job = windows_cleanup_job.WindowsCleanupJob()
        child = 'import time; print("ready",flush=True); time.sleep(8)'
        parent = None
        try:
            parent = launcher.start_gated(job, [sys.executable, '-u', '-c', child])
            self.assertEqual(parent.stdout.readline(), b'ready\r\n')
            job.close()
            parent.wait(timeout=5)
            self.assertEqual(parent.stdout.read(), b'')
        finally:
            job.close()
            if parent is not None:
                if parent.poll() is None:
                    parent.kill()
                    parent.wait(timeout=5)
                parent.stdout.close()

if __name__ == '__main__':
    unittest.main()
