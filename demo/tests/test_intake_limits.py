import os
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from nawa_demo.intake_limits import apply_parser_limits, MEMORY_BYTES, CPU_SECONDS, FILE_BYTES


class ParserLimitsTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == 'win32', 'Windows job object only')
    def test_windows_child_cannot_allocate_beyond_process_memory_limit(self):
        code = ('from nawa_demo.intake_limits import apply_parser_limits,MEMORY_BYTES; '
                'apply_parser_limits();\n'
                'try:\n bytearray(MEMORY_BYTES + 64*1024*1024)\n'
                'except MemoryError:\n print("limited")\n'
                'else:\n raise SystemExit("allocation unexpectedly succeeded")')
        result = subprocess.run([sys.executable, '-c', code], check=True, capture_output=True,
                                text=True, env=os.environ.copy(), timeout=15)
        self.assertEqual(result.stdout.strip(), 'limited')

    def test_linux_limits_do_not_raise_existing_limits(self):
        calls = []
        fake = SimpleNamespace(RLIMIT_AS=1, RLIMIT_CPU=2, RLIMIT_FSIZE=3, RLIM_INFINITY=-1,
                               getrlimit=lambda kind: (100, 200) if kind == 2 else (-1, -1),
                               setrlimit=lambda kind, pair: calls.append((kind, pair)))
        with patch('nawa_demo.intake_limits.sys.platform', 'linux'), patch.dict(sys.modules, {'resource': fake}):
            self.assertTrue(apply_parser_limits())
        self.assertEqual(calls, [(1, (MEMORY_BYTES, MEMORY_BYTES)), (2, (15, 15)),
                                 (3, (FILE_BYTES, FILE_BYTES))])

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux resource limits only')
    def test_linux_child_has_actual_memory_limit(self):
        code = ('import resource; from nawa_demo.intake_limits import apply_parser_limits; '
                'apply_parser_limits(); print(resource.getrlimit(resource.RLIMIT_AS)[0])')
        result = subprocess.run([sys.executable, '-c', code], check=True, capture_output=True, text=True,
                                env=os.environ.copy(), timeout=10)
        self.assertGreater(int(result.stdout.strip()), 0)
        self.assertLessEqual(int(result.stdout.strip()), MEMORY_BYTES)

