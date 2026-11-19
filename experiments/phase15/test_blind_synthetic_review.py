import json
from pathlib import Path
import tempfile
import unittest

import blind_synthetic_review as review


class BlindSyntheticReviewTests(unittest.TestCase):
    def test_packet_has_matching_images_and_only_blank_transcriptions(self):
        source = Path(__file__).parent / 'arabic-new-synthetic-pages'
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'review'
            packet = review.create_packet(source, output)
            self.assertEqual(packet['status'], 'awaiting_human_transcription')
            self.assertIs(packet['promotable'], False)
            for case in packet['cases']:
                self.assertTrue(all(value == '' for value in case['transcriptions'].values()))
                self.assertEqual((output / case['image']).read_bytes(), (source / case['image']).read_bytes())
            saved = json.loads((output / 'blank-transcriptions.json').read_text(encoding='utf-8'))
            self.assertEqual(saved, packet)
            self.assertNotIn('lines_synthetic', json.dumps(saved))

    def test_rejects_changed_input_before_creating_packet(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'input'
            source.mkdir()
            for name in review.IMAGE_SHA256:
                (source / name).write_bytes(b'changed')
            output = Path(temp) / 'review'
            with self.assertRaises(ValueError):
                review.create_packet(source, output)
            self.assertFalse(output.exists())

    def test_existing_destination_is_not_overwritten(self):
        source = Path(__file__).parent / 'arabic-new-synthetic-pages'
        with tempfile.TemporaryDirectory() as temp:
            existing = Path(temp) / 'review'
            existing.mkdir()
            (existing / 'keep.txt').write_text('keep', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                review.create_packet(source, existing)
            self.assertEqual((existing / 'keep.txt').read_text(encoding='utf-8'), 'keep')


if __name__ == '__main__':
    unittest.main()
