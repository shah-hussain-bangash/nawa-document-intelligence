"""Local-only OCR comparison on fixed synthetic crops; no NAWA integration."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

import ocr_benchmark as bench
from numeric_crop_experiment import REGIONS


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description='Evaluate fixed synthetic Arabic number crops')
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--qa-home', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Refusing to overwrite the result')
    model_dir = args.model_dir.resolve(strict=True)
    qa_home = args.qa_home.resolve(strict=True)
    if not model_dir.is_dir() or not qa_home.is_dir():
        raise ValueError('Model and QA home must be directories')
    model_files = ('inference.json', 'inference.pdiparams', 'inference.yml')
    model_hashes = {name:sha256(model_dir / name) for name in model_files}
    sample = bench.SAMPLES[1]
    image = bench.HERE / sample['image']
    bench.verify(image, sample['sha256'])

    # Paddle creates a cache under expanduser('~'); redirect only this process.
    old_expanduser = os.path.expanduser
    os.path.expanduser = lambda path: str(qa_home) if path == '~' else old_expanduser(path)
    try:
        import paddle
        import paddleocr
        from paddleocr import TextRecognition
        from PIL import Image, ImageOps
        model = TextRecognition(model_name='arabic_PP-OCRv5_mobile_rec',
                                model_dir=str(model_dir), device='cpu', enable_mkldnn=False)
        rows = []
        with tempfile.TemporaryDirectory() as temp, Image.open(image) as page:
            for name, box, expected in REGIONS:
                base = page.crop(box)
                for variant in ('original', 'enlarged_border'):
                    crop = base
                    if variant == 'enlarged_border':
                        crop = ImageOps.expand(base.resize((base.width * 2, base.height * 2),
                                              Image.Resampling.LANCZOS), border=20, fill='white')
                    image_path = Path(temp) / 'crop.png'
                    crop.save(image_path)
                    results = list(model.predict(str(image_path), batch_size=1))
                    if len(results) != 1:
                        raise ValueError('Unexpected synthetic model result count')
                    value = results[0].json['res']
                    recognized = value['rec_text']
                    actual = bench.comparison_value(name, recognized)
                    rows.append({'region':name, 'box':list(box), 'variant':variant,
                                 'expected':expected, 'recognized':recognized,
                                 'model_score_uncalibrated':value['rec_score'],
                                 'strict_numeric_match':actual is not None and
                                     actual == bench.comparison_value(name, expected)})
        if model_hashes != {name:sha256(model_dir / name) for name in model_files}:
            raise ValueError('Synthetic test model changed during run')
        result = {'status':'human_review_required', 'source_sha256':sample['sha256'],
                  'model_name':'arabic_PP-OCRv5_mobile_rec', 'model_sha256':model_hashes,
                  'paddle_version':paddle.__version__, 'paddleocr_version':paddleocr.__version__,
                  'python_version':sys.version.split()[0],
                  'scope':'One synthetic image, manually selected regions, no detection or independent evaluation.',
                  'results':rows}
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
        print('Strict numeric matches:', sum(row['strict_numeric_match'] for row in rows), '/', len(rows))
    finally:
        os.path.expanduser = old_expanduser


if __name__ == '__main__':
    main()
