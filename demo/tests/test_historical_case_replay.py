"""Tests for the historical synthetic case-study input boundary."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'docs/07-case-study/evidence'
GUARD = EVIDENCE / 'historical_input_guard.py'


@unittest.skipUnless(GUARD.is_file(), 'case-study files are available in the integrated draft')
class HistoricalCaseReplayTests(unittest.TestCase):
    def test_guard_accepts_matching_bytes_and_rejects_changes(self):
        spec = importlib.util.spec_from_file_location('historical_guard', GUARD)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'demo/nawa_demo/rag.py'
            path.parent.mkdir(parents=True)
            path.write_bytes(b'synthetic original\n')
            record = {'source_commit':'823565f7c44c15b07719b91670fe8bbfb8d96521',
                      'source_file_sha256':{'demo/nawa_demo/rag.py':hashlib.sha256(path.read_bytes()).hexdigest()}}
            guard.verify_recorded_inputs(folder, record)
            path.write_bytes(b'synthetic changed\n')
            with self.assertRaisesRegex(ValueError, 'inputs differ'):
                guard.verify_recorded_inputs(folder, record)

    def test_updated_checkout_cannot_be_mislabeled_as_historical_replay(self):
        script = EVIDENCE / 'reproduce_synthetic_checks.py'
        result = subprocess.run([sys.executable, str(script), '--repo', str(ROOT)],
                                capture_output=True, text=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Historical case-study inputs differ', result.stderr)
        self.assertEqual(result.stdout, '')
