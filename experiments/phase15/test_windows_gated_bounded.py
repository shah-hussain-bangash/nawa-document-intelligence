import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from windows_gated_bounded import GatedRunError, run_gated_bounded

@unittest.skipUnless(os.name == 'nt', 'Windows-only local experiment')
class WindowsGatedBoundedTests(unittest.TestCase):
    def test_captures_successful_output(self):
        output = run_gated_bounded([sys.executable, '-c', "print('synthetic')"])
        self.assertEqual(output.strip(), b'synthetic')

    def test_stops_timed_out_process(self):
        with self.assertRaises(GatedRunError):
            run_gated_bounded([sys.executable, '-c', 'import time; time.sleep(10)'], timeout=0.5)

    def test_rejects_excess_output(self):
        with self.assertRaises(GatedRunError):
            run_gated_bounded([sys.executable, '-c', "print('x' * 100000)"], max_output=100)

    def test_rejects_failed_child(self):
        with self.assertRaises(GatedRunError):
            run_gated_bounded([sys.executable, '-c', 'raise SystemExit(3)'])

    def test_cleanup_stops_synthetic_descendant_after_parent_exits(self):
        with tempfile.TemporaryDirectory() as directory:
            ready = Path(directory) / 'ready'
            finished = Path(directory) / 'finished'
            child = ('import pathlib,sys,time; pathlib.Path(sys.argv[1]).write_text("ready"); '
                     'time.sleep(2); pathlib.Path(sys.argv[2]).write_text("late")')
            parent = ('import pathlib,subprocess,sys,time; '
                      'subprocess.Popen([sys.executable,"-c",sys.argv[1],sys.argv[2],sys.argv[3]]); '
                      'p=pathlib.Path(sys.argv[2]); '
                      '[(time.sleep(.02)) for _ in range(100) if not p.exists()]; '
                      'sys.exit(0 if p.exists() else 2)')
            run_gated_bounded([sys.executable, '-c', parent, child, str(ready), str(finished)])
            self.assertTrue(ready.exists())
            time.sleep(2.2)
            self.assertFalse(finished.exists())

if __name__ == '__main__':
    unittest.main()
