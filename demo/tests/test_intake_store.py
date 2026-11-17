from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from unittest.mock import patch

from nawa_demo.intake_store import LocalIntakeStore


class LocalIntakeStoreTests(unittest.TestCase):
    def test_save_and_reopen_bilingual_document(self):
        with TemporaryDirectory() as folder:
            data = 'عرض سعر / quotation'.encode('utf-8')
            document_id, meta = LocalIntakeStore(folder).save('عرض.txt', data)
            self.assertNotIn('عرض', document_id)
            self.assertEqual(LocalIntakeStore(folder).read_verified(document_id, meta.sha256), data)

    def test_tampering_and_path_traversal_are_rejected(self):
        with TemporaryDirectory() as folder:
            store = LocalIntakeStore(folder)
            document_id, meta = store.save('quote.txt', b'quotation')
            (Path(folder) / document_id).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'integrity'):
                store.read_verified(document_id, meta.sha256)
            with self.assertRaises(ValueError):
                store.read_verified('../quote.txt', meta.sha256)

    def test_invalid_input_leaves_no_file(self):
        with TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                LocalIntakeStore(folder).save('x.pdf', b'not a pdf')
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_symlink_is_not_read_as_a_stored_document(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'storage')
            document, meta = store.save('quote.txt', b'synthetic')
            target = root / 'outside.txt'
            target.write_bytes(b'synthetic')
            path = store.directory / document
            path.unlink()
            try:
                path.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest('Creating symbolic links is not available')
            with self.assertRaises(ValueError):
                store.read_verified(document, meta.sha256)

    def test_file_swapped_for_symlink_during_open_is_rejected(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'storage')
            document, meta = store.save('quote.txt', b'synthetic')
            target = root / 'outside.txt'
            target.write_bytes(b'synthetic')
            probe = root / 'probe'
            try:
                probe.symlink_to(target)
                probe.unlink()
            except (OSError, NotImplementedError):
                self.skipTest('Creating symbolic links is not available')
            original_open = os.open
            path = store.directory / document
            def swap_then_open(name, flags):
                path.unlink()
                path.symlink_to(target)
                return original_open(name, flags)
            with patch('nawa_demo.intake_store.os.open', side_effect=swap_then_open):
                with self.assertRaises(ValueError):
                    store.read_verified(document, meta.sha256)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'Named pipes are not available')
    def test_named_pipe_is_rejected_without_blocking(self):
        with TemporaryDirectory() as folder:
            store = LocalIntakeStore(folder)
            document = 'a' * 32
            os.mkfifo(store.directory / document)
            with self.assertRaises(ValueError):
                store.read_verified(document, 'b' * 64)


if __name__ == '__main__':
    unittest.main()

