"""Compare OCR on two fixed generated synthetic pages, without NAWA integration."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import ocr_benchmark as bench
from paddle_arabic_page_experiment import evaluate_lines, hashes

MANIFEST_SHA256 = '65aa7d15e168c348c33032438925b8c2a35019714ade600a22d48a8c4f381313'
IMAGE_SHA256 = {'synthetic-a.png':'f16b3e80aeb53d44fe889b18ade1194f0f1714754a68b547b3e4bb54b93efb98',
                'synthetic-b.png':'a32c828b9259a25cee93efd2f86344f42f0be640924b8f50d5e0c1a5a8411e40'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description='Evaluate fixed synthetic Arabic pages')
    for name in ('pages-dir', 'det-dir', 'rec-dir', 'qa-home', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Refusing to overwrite the result')
    pages, det, rec, qa = (item.resolve(strict=True) for item in
                            (args.pages_dir, args.det_dir, args.rec_dir, args.qa_home))
    manifest_path = pages / 'manifest.json'
    if digest(manifest_path) != MANIFEST_SHA256:
        raise ValueError('Synthetic manifest hash mismatch')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if len(manifest['cases']) != 2:
        raise ValueError('Unexpected synthetic case count')
    for case in manifest['cases']:
        if case['image'] not in IMAGE_SHA256 or digest(pages / case['image']) != IMAGE_SHA256[case['image']]:
            raise ValueError('Synthetic image hash mismatch')
    for name, expected in bench.MODEL_HASHES.items():
        bench.verify(bench.TESSDATA / name, expected)
    model_hashes = {'detector':hashes(det), 'recognizer':hashes(rec)}
    tesseract_hash = digest(bench.TESSERACT)
    tesseract_version = subprocess.run([str(bench.TESSERACT), '--version'], check=True,
        capture_output=True, timeout=10).stdout.decode('utf-8').splitlines()[0]
    original = os.path.expanduser
    os.path.expanduser = lambda path: str(qa) if path == '~' else original(path)
    try:
        import paddle
        import paddleocr
        from paddleocr import PaddleOCR
        pipeline = PaddleOCR(text_detection_model_name='PP-OCRv5_mobile_det', text_detection_model_dir=str(det),
            text_recognition_model_name='arabic_PP-OCRv5_mobile_rec', text_recognition_model_dir=str(rec),
            use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False,
            device='cpu', enable_mkldnn=False)
        rows = []
        for case in manifest['cases']:
            image = pages / case['image']
            sample = {'reference':case['lines'], 'fields':case['fields']}
            output = subprocess.run([str(bench.TESSERACT), str(image), 'stdout', '--tessdata-dir',
                str(bench.TESSDATA), '-l', 'ara+eng', '--psm', '6'],
                check=True, capture_output=True, timeout=30).stdout.decode('utf-8')
            tesseract = evaluate_lines(output.splitlines(), sample)
            found = list(pipeline.predict(str(image)))
            if len(found) != 1:
                raise ValueError('Unexpected Paddle page count')
            paddle_result = evaluate_lines(list(found[0].json['res']['rec_texts']), sample)
            rows.append({'id':case['id'], 'image_sha256':IMAGE_SHA256[case['image']],
                         'tesseract':tesseract, 'paddle':paddle_result})
        if model_hashes != {'detector':hashes(det), 'recognizer':hashes(rec)} or digest(bench.TESSERACT) != tesseract_hash:
            raise ValueError('Synthetic test engine or models changed during run')
        for name, expected in bench.MODEL_HASHES.items():
            bench.verify(bench.TESSDATA / name, expected)
        result = {'status':'human_review_required', 'manifest_sha256':MANIFEST_SHA256,
                  'scope':'Two Windows-generated synthetic pages, same layout and font; not independently reviewed.',
                  'tesseract':tesseract_version, 'tesseract_sha256':tesseract_hash,
                  'tesseract_model_sha256':bench.MODEL_HASHES, 'paddle_version':paddle.__version__,
                  'paddleocr_version':paddleocr.__version__, 'paddle_model_sha256':model_hashes,
                  'python_version':sys.version.split()[0], 'cases':rows}
        with args.output.open('x', encoding='utf-8') as out:
            json.dump(result, out, ensure_ascii=False, indent=2)
        for row in rows:
            print(row['id'], 'Tesseract strict', row['tesseract']['strict_fields_correct'],
                  'Paddle strict', row['paddle']['strict_fields_correct'],
                  'Paddle candidate', row['paddle']['candidate_fields_correct'], '/ 6')
    finally:
        os.path.expanduser = original


if __name__ == '__main__':
    main()
