import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import arabic_threshold_experiment as experiment


class SyntheticThresholdExperimentTests(unittest.TestCase):
    def test_crop_preparation_scales_and_adds_white_border(self):
        source = Image.new('RGB', (20, 20), 'black')
        prepared = experiment.prepare_crop(source, (2, 3, 12, 8))
        self.assertEqual(prepared.size, (90, 75))
        self.assertEqual(prepared.getpixel((0, 0)), 255)
        self.assertEqual(prepared.getpixel((45, 37)), 0)

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.json'
            output.write_text('keep', encoding='utf-8')
            with patch.object(sys, 'argv', ['experiment', '--output', str(output)]):
                with self.assertRaises(FileExistsError):
                    experiment.main()
            self.assertEqual(output.read_text(encoding='utf-8'), 'keep')


if __name__ == '__main__':
    unittest.main()
