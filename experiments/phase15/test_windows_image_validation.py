import io
import os
import unittest
from PIL import Image
from windows_gated_bounded import GatedRunError
from windows_image_validation import validate_png_in_job

@unittest.skipUnless(os.name == 'nt', 'Windows-only experimental validator')
class WindowsImageValidationTests(unittest.TestCase):
    def png(self, size):
        buffer = io.BytesIO()
        Image.new('1', size, 1).save(buffer, format='PNG')
        return buffer.getvalue()

    def test_valid_synthetic_png(self):
        self.assertIsNone(validate_png_in_job(self.png((5, 5))))

    def test_rejects_invalid_png(self):
        with self.assertRaises(GatedRunError):
            validate_png_in_job(b'not a png')

    def test_rejects_excessive_dimensions(self):
        with self.assertRaises(GatedRunError):
            validate_png_in_job(self.png((4000, 3100)))

if __name__ == '__main__':
    unittest.main()
