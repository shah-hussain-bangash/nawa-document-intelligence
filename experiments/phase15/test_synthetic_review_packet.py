import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from synthetic_review_packet import create_packet

class SyntheticReviewPacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / 'sample.png'
        Image.new('RGB', (20, 20), 'white').save(self.image)
        self.sha = hashlib.sha256(self.image.read_bytes()).hexdigest()

    def test_packet_preserves_evidence_and_review_status(self):
        output = self.root / 'review'
        packet = create_packet(self.image, self.sha, [('Amount', (0, 0, 10, 10))], output)
        self.assertEqual(packet['status'], 'human_review_required')
        self.assertEqual(packet['source_image_sha256'], self.sha)
        self.assertEqual(hashlib.sha256((output / packet['source_file']).read_bytes()).hexdigest(), self.sha)
        crop = packet['regions'][0]
        self.assertEqual(hashlib.sha256((output / crop['crop_file']).read_bytes()).hexdigest(), crop['crop_sha256'])
        self.assertEqual(json.loads((output / 'review-packet.json').read_text(encoding='utf-8')), packet)
        self.assertIn('No value or approval has been inferred', (output / 'review.html').read_text(encoding='utf-8'))

    def test_changed_source_is_rejected(self):
        with self.assertRaises(ValueError):
            create_packet(self.image, '0' * 64, [('Amount', (0, 0, 10, 10))], self.root / 'out')

    def test_outside_region_rejected_before_creating_output(self):
        output = self.root / 'out'
        with self.assertRaises(ValueError):
            create_packet(self.image, self.sha, [('Amount', (0, 0, 21, 10))], output)
        self.assertFalse(output.exists())

    def test_existing_directory_is_not_overwritten(self):
        with self.assertRaises(FileExistsError):
            create_packet(self.image, self.sha, [('Amount', (0, 0, 10, 10))], self.root)

if __name__ == '__main__':
    unittest.main()
