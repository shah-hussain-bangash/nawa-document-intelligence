from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from nawa_demo.prepare_oidc_fixture import prepare


class Phase13FixtureTests(unittest.TestCase):
    def test_phase13_fixture_is_separate_and_refuses_overwrite(self):
        with TemporaryDirectory() as folder:
            target = Path(folder) / 'phase13'
            prepare(target, phase=13)
            realm = json.loads((target / 'import' / 'realm.json').read_text(encoding='utf-8'))
            self.assertEqual(realm['realm'], 'nawa-phase13')
            self.assertEqual(realm['clients'][0]['redirectUris'], ['http://127.0.0.1:19765/auth/callback',
                                                                  'http://127.0.0.1:19766/auth/callback'])
            self.assertIn('POSTGRES_DB=nawa_phase13_qa_demo\n', (target / 'db.env').read_text(encoding='utf-8'))
            with self.assertRaises(FileExistsError):
                prepare(target, phase=13)

    def test_phase12_defaults_remain_unchanged(self):
        with TemporaryDirectory() as folder:
            target = Path(folder) / 'phase12'
            prepare(target)
            realm = json.loads((target / 'import' / 'realm.json').read_text(encoding='utf-8'))
            self.assertEqual(realm['realm'], 'nawa-phase12')
            self.assertEqual(realm['clients'][0]['redirectUris'], ['http://127.0.0.1:18765/auth/callback'])


if __name__ == '__main__':
    unittest.main()

