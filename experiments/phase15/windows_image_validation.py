"""Experimental job-limited image validation, not a security sandbox."""
from pathlib import Path
import sys
import tempfile
import PIL
from bounded_ocr_prototype import MAX_INPUT_BYTES, MAX_PIXELS
from windows_gated_bounded import GatedRunError, run_gated_bounded

_VALIDATE = '''
import sys
sys.path.insert(0, sys.argv[3])
from PIL import Image
with Image.open(sys.argv[1], formats=['PNG']) as image:
    if image.width * image.height > int(sys.argv[2]):
        raise ValueError('image too large')
    image.verify()
print('validated')
'''

def validate_png_in_job(data):
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError('Input exceeds limit')
    with tempfile.TemporaryDirectory(prefix='nawa_validation_') as directory:
        path = Path(directory) / 'image.png'
        path.write_bytes(data)
        dependency_dir = str(Path(PIL.__file__).resolve().parent.parent)
        output = run_gated_bounded([sys.executable, '-I', '-c', _VALIDATE,
                                   str(path), str(MAX_PIXELS), dependency_dir], timeout=10, max_output=1024)
        if output.strip() != b'validated':
            raise GatedRunError('Image validation returned an unexpected response')
