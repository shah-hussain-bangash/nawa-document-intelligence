from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

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


if __name__ == '__main__':
    unittest.main()
