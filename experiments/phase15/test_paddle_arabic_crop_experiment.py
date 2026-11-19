import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import paddle_arabic_crop_experiment as experiment


class PaddleArabicCropExperimentTests(unittest.TestCase):
    def test_existing_result_is_not_overwritten_or_model_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / 'result.json'
            result.write_text('keep', encoding='utf-8')
            argv = ['experiment', '--model-dir', 'missing', '--qa-home', 'missing',
                    '--output', str(result)]
            with patch.object(sys, 'argv', argv), self.assertRaises(FileExistsError):
                experiment.main()
            self.assertEqual(result.read_text(encoding='utf-8'), 'keep')


if __name__ == '__main__':
    unittest.main()
