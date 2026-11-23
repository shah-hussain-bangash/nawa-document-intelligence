"""Render the one pinned synthetic PDF page used for local OCR comparison."""
import argparse
import hashlib
from pathlib import Path
import pymupdf

PDF_SHA256 = 'efe191b915a9ba0f205017f9c7911d72422ddb047c9a7ef48c3e728a47499b68'
IMAGE_SHA256 = '8ba0740b728db0fac7bc655183854ea882db00545445a6bfd11f3d206f7e75b9'


def render(source):
    pdf = Path(source).read_bytes()
    if hashlib.sha256(pdf).hexdigest() != PDF_SHA256:
        raise ValueError('Synthetic PDF hash mismatch')
    with pymupdf.open(stream=pdf, filetype='pdf') as document:
        image = document[0].get_pixmap(dpi=200, alpha=False).tobytes('png')
    if hashlib.sha256(image).hexdigest() != IMAGE_SHA256:
        raise ValueError('Rendered bytes differ from the pinned test image')
    return image


def main():
    parser = argparse.ArgumentParser(description='Render a pinned synthetic PDF for OCR testing')
    parser.add_argument('--pdf', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Refusing to overwrite the result')
    data = render(args.pdf)
    with args.output.open('xb') as stream:
        stream.write(data)
    print('Pinned synthetic page rendered')


if __name__ == '__main__':
    main()
