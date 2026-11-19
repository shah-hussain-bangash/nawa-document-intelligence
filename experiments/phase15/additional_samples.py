"""Measure OCR on three additional local synthetic PDF pages, not real scans."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import pymupdf
import ocr_benchmark as bench

PDF_HASHES = {
    'incorrect_vat.pdf':{'be8de4dbf2cfbf4dad03009b571ebb13b5e873248ec149842576a2ea7d7dc3e0', 'b1edcea773136941a4bb3c4e24f86c6d8fe6881037295ef0807159b063300c16'},
    'second_page_supplier.pdf':{'3bbebac92722b82770c31725806efb6148f2b317b0a3af7348145a2f336d95d6', '1b95cabe02ceca5f7e9f71216c3f9b1ef6e8e41a546faea053641ab7a71fad03'},
    'arabic_text_supplier.pdf':{'efe191b915a9ba0f205017f9c7911d72422ddb047c9a7ef48c3e728a47499b68'},
}
CASES = [
    {'file': 'incorrect_vat.pdf', 'page': 0, 'lang': 'eng',
     'reference': ['Supplier: Example Bad VAT', 'Currency: AED', 'Subtotal: 1000.00',
                   'VAT Rate: 5', 'VAT Amount: 60.00', 'Grand Total: 1060.00'],
     'fields': {'supplier':'Example Bad VAT','currency':'AED','subtotal':'1000.00',
                'vat_rate':'5','vat_amount':'60.00','total':'1060.00'}},
    {'file': 'second_page_supplier.pdf', 'page': 1, 'lang': 'eng',
     'reference': ['Supplier: Example Page Two Supplies', 'Currency: AED', 'Subtotal: 900.00',
                   'VAT Rate: 5', 'VAT Amount: 45.00', 'Grand Total: 945.00'],
     'fields': {'supplier':'Example Page Two Supplies','currency':'AED','subtotal':'900.00',
                'vat_rate':'5','vat_amount':'45.00','total':'945.00'}},
    {'file': 'arabic_text_supplier.pdf', 'page': 0, 'lang': 'ara+eng',
     'reference': ['اسم المورد: شركة المثال للتوريدات', 'العملة: AED',
                   'المجموع الفرعي: ٩٠٠٫٠٠', 'نسبة الضريبة: ٥', 'قيمة الضريبة: ٤٥٫٠٠',
                   'Grand Total: 945.00'],
     'fields': {'supplier':'شركة المثال للتوريدات','currency':'AED','subtotal':'900.00',
                'vat_rate':'5','vat_amount':'45.00','total':'945.00'}},
]

def main():
    parser = argparse.ArgumentParser(description='Run the three fixed synthetic PDF OCR cases')
    parser.add_argument('--pdf-dir', type=Path, required=True, help='Directory containing the repository synthetic PDFs')
    parser.add_argument('--tesseract', type=Path, required=True, help='Path to Tesseract executable')
    parser.add_argument('--tessdata', type=Path, required=True, help='Directory containing the pinned fast language models')
    parser.add_argument('--output', type=Path, required=True, help='New JSON output file; existing files are not overwritten')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Refusing to overwrite the output file')
    engine_sha256 = hashlib.sha256(args.tesseract.read_bytes()).hexdigest()
    for name, digest in bench.MODEL_HASHES.items():
        bench.verify(args.tessdata / name, digest)
    for name, expected in PDF_HASHES.items():
        digest = hashlib.sha256((args.pdf_dir / name).read_bytes()).hexdigest()
        if digest not in expected:
            raise ValueError('Synthetic PDF input changed: ' + name)
    rows = []
    with tempfile.TemporaryDirectory(prefix='nawa_synthetic_ocr_') as temp:
        for case in CASES:
            pdf = args.pdf_dir / case['file']
            pdf_bytes = pdf.read_bytes()
            digest = hashlib.sha256(pdf_bytes).hexdigest()
            if digest not in PDF_HASHES[case['file']]:
                raise ValueError('Synthetic PDF input changed: ' + case['file'])
            image = Path(temp) / (case['file'] + '.png')
            with pymupdf.open(stream=pdf_bytes, filetype='pdf') as document:
                document[case['page']].get_pixmap(dpi=200, alpha=False).save(image)
            image_sha256 = hashlib.sha256(image.read_bytes()).hexdigest()
            proc = subprocess.run([str(args.tesseract), str(image), 'stdout',
                '--tessdata-dir', str(args.tessdata), '-l', case['lang'], '--psm', '6'],
                check=True, capture_output=True, timeout=30)
            text = proc.stdout.decode('utf-8')
            matches = bench.field_results(text, case['fields'])
            rows.append({'file':case['file'], 'pdf_sha256':digest, 'page':case['page'] + 1,
                'rendered_image_sha256':image_sha256, 'language':case['lang'],
                **bench.rates('\n'.join(case['reference']), text),
                'fields_correct':sum(matches.values()), 'field_matches':matches,
                'reference_synthetic':case['reference'], 'ocr_text_synthetic':text})
    version = subprocess.run([str(args.tesseract), '--version'], check=True,
                             capture_output=True, timeout=10).stdout.decode('utf-8').splitlines()[0]
    if hashlib.sha256(args.tesseract.read_bytes()).hexdigest() != engine_sha256:
        raise ValueError('Synthetic OCR executable changed during run')
    for name, digest in bench.MODEL_HASHES.items():
        bench.verify(args.tessdata / name, digest)
    result = {'status':'human_review_required', 'engine':version, 'engine_sha256':engine_sha256,
              'model_sha256':dict(bench.MODEL_HASHES),
              'model_commit':'87416418657359cb625c412a48b6e1d6d41c29bd', 'render_dpi':200,
              'psm':6, 'scope':'Three additional synthetic PDF pages rasterized to images; not physical scans or independent ground truth.',
              'cases':rows}
    with args.output.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    for row in rows:
        print(f"{row['file']} page {row['page']}: {row['fields_correct']}/{len(row['field_matches'])} fields, CER {row['cer']:.1%}, WER {row['wer']:.1%}")

if __name__ == '__main__':
    main()
