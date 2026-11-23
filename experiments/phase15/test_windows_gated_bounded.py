import os
import ctypes
from ctypes import wintypes
from pathlib import Path
import sys
import tempfile
import time
import unittest
from windows_gated_bounded import GatedRunError, run_gated_bounded
from windows_cleanup_job import WindowsCleanupJob, _CpuRateControl

@unittest.skipUnless(os.name == 'nt', 'Windows-only local experiment')
class WindowsGatedBoundedTests(unittest.TestCase):
    def test_windows_reports_configured_cpu_hard_cap(self):
        job = WindowsCleanupJob(cpu_percent=30)
        try:
            job.kernel.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
            job.kernel.QueryInformationJobObject.restype = wintypes.BOOL
            value = _CpuRateControl()
            self.assertTrue(job.kernel.QueryInformationJobObject(job.handle, 15,
                ctypes.byref(value), ctypes.sizeof(value), None))
            self.assertEqual(value.flags & 0x5, 0x5)
            self.assertEqual(value.rate, 3000)
        finally:
            job.close()

    def test_invalid_cpu_limit_rejected(self):
        with self.assertRaises(ValueError):
            WindowsCleanupJob(cpu_percent=0)

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

    def test_active_process_limit_prevents_synthetic_child_launch(self):
        # The gated starter occupies the single permitted process slot.
        with self.assertRaises(GatedRunError):
            run_gated_bounded([sys.executable, '-c', "print('must not run')"], max_processes=1)

    def test_job_memory_limit_rejects_oversized_allocation(self):
        small = "x=bytearray(1024*1024); print('small-ok')"
        self.assertEqual(run_gated_bounded([sys.executable, '-c', small],
            memory_limit_bytes=96*1024*1024).strip(), b'small-ok')
        code = ('import sys\ntry:\n x=bytearray(256*1024*1024)\n'
                'except MemoryError:\n sys.exit(7)\n')
        with self.assertRaises(GatedRunError):
            run_gated_bounded([sys.executable, '-c', code], memory_limit_bytes=96*1024*1024)

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
