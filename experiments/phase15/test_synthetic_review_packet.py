import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess
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
        self.assertIn('Download review JSON', (output / 'review.html').read_text(encoding='utf-8'))

    def test_region_label_is_escaped_in_review_page(self):
        output = self.root / 'review'
        create_packet(self.image, self.sha, [('<script>alert(1)</script>', (0, 0, 10, 10))], output)
        page = (output / 'review.html').read_text(encoding='utf-8')
        self.assertNotIn('<script>alert(1)</script>', page)
        self.assertIn('&lt;script&gt;', page)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for the local browser-script test')
    def test_download_script_exports_reviewer_text_without_approval(self):
        output = self.root / 'review'
        create_packet(self.image, self.sha, [('Amount', (0, 0, 10, 10))], output)
        page = (output / 'review.html').read_text(encoding='utf-8')
        script = re.search(r'<script>(.*?)</script>', page).group(1)
        script_file = self.root / 'script.js'
        script_file.write_text(script, encoding='utf-8')
        harness = r'''const fs=require('fs'),vm=require('vm'); let handler,blob;
const region={dataset:{label:'Amount',box:'[0,0,10,10]',crop:'region-1.png',cropSha:'abc'},querySelector:()=>({value:'900.00'})};
const document={getElementById:()=>({addEventListener:(name,fn)=>handler=fn}),querySelectorAll:()=>[region],
 body:{appendChild:()=>{}},createElement:()=>({click:()=>{},remove:()=>{}})};
class Blob {constructor(parts){blob=parts.join('')}}
const URL={createObjectURL:()=> 'blob:test',revokeObjectURL:()=>{}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{document,Blob,URL,setTimeout:()=>{}});
handler(); process.stdout.write(blob);'''
        result = subprocess.run(['node', '-e', harness, str(script_file)], check=True,
                                capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        self.assertEqual(data['status'], 'human_review_required')
        self.assertEqual(data['source_image_sha256'], self.sha)
        self.assertEqual(data['regions'][0]['reviewer_transcription'], '900.00')
        self.assertEqual(data['regions'][0]['box_pixels'], [0, 0, 10, 10])

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
