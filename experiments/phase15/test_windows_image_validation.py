import io
import os
import unittest
import zlib
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

    def test_rejects_corrupt_image_data_with_valid_chunk_crc(self):
        data = bytearray(self.png((5, 5)))
        chunk = data.index(b'IDAT')
        length = int.from_bytes(data[chunk-4:chunk], 'big')
        data[chunk+4] = 0  # Invalid compression header, with a corrected PNG CRC.
        crc = zlib.crc32(data[chunk:chunk+4+length]) & 0xffffffff
        data[chunk+4+length:chunk+8+length] = crc.to_bytes(4, 'big')
        with Image.open(io.BytesIO(data)) as image:
            image.verify()  # Structural verification alone does not decode pixels.
        with self.assertRaises(GatedRunError):
            validate_png_in_job(bytes(data))

if __name__ == '__main__':
    unittest.main()
