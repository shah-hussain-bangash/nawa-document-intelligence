import json
from pathlib import Path
import tempfile
import unittest
import hashlib
from PIL import Image
from synthetic_review_packet import create_packet
from validate_synthetic_review import validate_export

class SyntheticExportValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = self.root / 'image.png'
        Image.new('RGB', (20, 20), 'white').save(source)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        self.packet_dir = self.root / 'packet'
        packet = create_packet(source, digest, [('Amount', (0, 0, 10, 10))], self.packet_dir)
        self.export = {'status':'human_review_required', 'source_image_sha256':digest,
                       'regions':[{k:v for k,v in packet['regions'][0].items() if k != 'status'}]}
        self.export['regions'][0]['reviewer_transcription'] = '900.00'
        self.export_path = self.root / 'export.json'

    def check(self):
        self.export_path.write_text(json.dumps(self.export), encoding='utf-8')
        return validate_export(self.packet_dir, self.export_path)

    def test_valid_export_stays_review_required(self):
        result = self.check()
        self.assertEqual(result['status'], 'human_review_required')
        self.assertEqual(result['with_transcription'], 1)

    def test_rejects_altered_metadata(self):
        self.export['regions'][0]['box_pixels'][0] = 1
        with self.assertRaises(ValueError): self.check()

    def test_rejects_altered_crop(self):
        (self.packet_dir / 'region-1.png').write_bytes(b'changed')
        with self.assertRaises(ValueError): self.check()

    def test_rejects_crop_substitution_even_if_hashes_are_updated(self):
        crop = self.packet_dir / 'region-1.png'
        Image.new('RGB', (10, 10), 'black').save(crop)
        digest = hashlib.sha256(crop.read_bytes()).hexdigest()
        packet_path = self.packet_dir / 'review-packet.json'
        packet = json.loads(packet_path.read_text(encoding='utf-8'))
        packet['regions'][0]['crop_sha256'] = digest
        packet_path.write_text(json.dumps(packet), encoding='utf-8')
        self.export['regions'][0]['crop_sha256'] = digest
        with self.assertRaises(ValueError): self.check()

    def test_rejects_crop_path_traversal(self):
        packet_path = self.packet_dir / 'review-packet.json'
        packet = json.loads(packet_path.read_text(encoding='utf-8'))
        packet['regions'][0]['crop_file'] = '../outside.png'
        packet_path.write_text(json.dumps(packet), encoding='utf-8')
        self.export['regions'][0]['crop_file'] = '../outside.png'
        with self.assertRaises(ValueError): self.check()

    def test_rejects_approval_status(self):
        self.export['status'] = 'approved'
        with self.assertRaises(ValueError): self.check()

    def test_rejects_oversized_transcription(self):
        self.export['regions'][0]['reviewer_transcription'] = '1' * 81
        with self.assertRaises(ValueError): self.check()

if __name__ == '__main__':
    unittest.main()
