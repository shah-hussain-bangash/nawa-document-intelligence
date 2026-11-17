from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from unittest.mock import patch

from nawa_demo.intake_runtime import build_synthetic_intake
from nawa_demo.intake_worker_cli import main
from nawa_demo.intake_migrate import main as migrate_main
from nawa_demo.intake_migrate import _files


class RuntimeTests(unittest.TestCase):
    def test_worker_requires_explicit_test_mode(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            main()

    def test_migration_refuses_unapproved_database_configuration(self):
        with patch.dict(os.environ, {'NAWA_INTAKE':'synthetic', 'NAWA_AUTH':'oidc',
                                     'NAWA_STORAGE':'postgres', 'POSTGRES_DB':'nawa_demo'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'nawa_phase13_qa_'):
                migrate_main()

    def test_migration_input_normalizes_windows_and_linux_line_endings(self):
        with TemporaryDirectory() as folder:
            migration = Path(folder) / '001_test.sql'
            with patch('nawa_demo.intake_migrate.MIGRATIONS', Path(folder)):
                migration.write_bytes(b'SELECT 1;\r\nSELECT 2;\r\n')
                windows = _files()
                migration.write_bytes(b'SELECT 1;\nSELECT 2;\n')
                self.assertEqual(_files(), windows)

    def test_runtime_requires_absolute_directory_and_existing_schema(self):
        @contextmanager
        def connect():
            yield object()
        with self.assertRaisesRegex(ValueError, 'absolute'):
            build_synthetic_intake(connect, 'relative')
        with TemporaryDirectory() as folder:
            with patch('nawa_demo.intake_runtime.verify_intake_migrations', side_effect=ValueError('schema')):
                with self.assertRaisesRegex(ValueError, 'schema'):
                    build_synthetic_intake(connect, str(Path(folder)))
            self.assertEqual(list(Path(folder).iterdir()), [])

