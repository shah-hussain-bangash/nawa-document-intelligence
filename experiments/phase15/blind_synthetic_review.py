"""Prepare a blinded transcription packet for two pinned synthetic pages."""
import argparse
import hashlib
import json
from pathlib import Path

from synthetic_arabic_batch_experiment import IMAGE_SHA256

FIELDS = ('supplier', 'currency', 'subtotal', 'vat_rate', 'vat_amount', 'total')


def create_packet(source_dir, output_dir):
    source_dir, output_dir = Path(source_dir), Path(output_dir)
    images = {}
    for name, expected in IMAGE_SHA256.items():
        data = (source_dir / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Synthetic page hash mismatch')
        images[name] = data
    output_dir.mkdir(parents=False, exist_ok=False)
    cases = []
    for name, data in images.items():
        with (output_dir / name).open('xb') as stream:
            stream.write(data)
        cases.append({'case':name[:-4], 'image':name, 'image_sha256':IMAGE_SHA256[name],
                      'transcriptions':{field:'' for field in FIELDS}})
    packet = {'status':'awaiting_human_transcription', 'promotable':False,
              'scope':'Synthetic pages only; no reviewer authentication or approval.', 'cases':cases}
    with (output_dir / 'blank-transcriptions.json').open('x', encoding='utf-8') as stream:
        json.dump(packet, stream, ensure_ascii=False, indent=2)
    instructions = ('# Synthetic Arabic page review\n\n'
        'For each image, read the original page and transcribe the supplier, currency, '
        'subtotal, VAT rate, VAT amount and total. Enter exactly what you see; '
        'use “unclear” if you cannot read a value. Do not use OCR output or calculate missing values.\n\n'
        '- [Page A](synthetic-a.png)\n- [Page B](synthetic-b.png)\n\n'
        'Fill in `blank-transcriptions.json` or send the six values for each page. '
        'This is a transcription exercise, not a quotation approval. The file does not authenticate a reviewer.\n')
    (output_dir / 'READ-ME.md').write_text(instructions, encoding='utf-8')
    return packet


def main():
    parser = argparse.ArgumentParser(description='Create a blind synthetic transcription packet')
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    create_packet(args.source_dir, args.output_dir)
    print('Two synthetic pages prepared; awaiting human transcription.')


if __name__ == '__main__':
    main()
