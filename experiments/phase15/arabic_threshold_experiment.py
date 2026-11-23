"""Explore thresholding on four hand-selected synthetic Arabic number crops."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageOps
import ocr_benchmark as bench
from numeric_crop_experiment import REGIONS

BEST = bench.HERE / 'tessdata-best-e12c65a'


def prepare_crop(page, box):
    crop = ImageOps.autocontrast(page.crop(box).convert('L'))
    crop = crop.resize((crop.width * 3, crop.height * 3), Image.Resampling.LANCZOS)
    return ImageOps.expand(crop.point(lambda value: 255 if value > 160 else 0),
                           border=30, fill='white')


def main():
    parser = argparse.ArgumentParser(description='Threshold a fixed synthetic Arabic OCR fixture')
    parser.add_argument('--output', type=Path, required=True, help='New result file')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Refusing to overwrite the output file')
    sample = bench.SAMPLES[1]
    image = bench.HERE / sample['image']
    bench.verify(image, sample['sha256'])
    provenance = json.loads((BEST / 'provenance.json').read_text(encoding='utf-8'))
    script = json.loads((BEST / 'script' / 'provenance.json').read_text(encoding='utf-8'))
    models = {'ara.traineddata': provenance['files']['ara.traineddata']['sha256'],
              'script/Arabic.traineddata': script['sha256']}
    for filename, digest in models.items():
        bench.verify(BEST / filename, digest)
    engine_hash = hashlib.sha256(bench.TESSERACT.read_bytes()).hexdigest()
    version = subprocess.run([str(bench.TESSERACT), '--version'], check=True,
                             capture_output=True, timeout=10).stdout.decode('utf-8').splitlines()[0]
    rows = []
    with tempfile.TemporaryDirectory() as temp, Image.open(image) as page:
        for name, box, expected in REGIONS:
            path = Path(temp) / 'synthetic-crop.png'
            prepare_crop(page, box).save(path)
            for language in ('ara', 'script/Arabic'):
                for psm in (7, 13):
                    out = subprocess.run([str(bench.TESSERACT), str(path), 'stdout',
                        '--tessdata-dir', str(BEST), '-l', language, '--psm', str(psm)],
                        capture_output=True, check=True, timeout=30).stdout.decode('utf-8')
                    recognized = bench.normalize(out)
                    value = bench.comparison_value(name, recognized)
                    rows.append({'region':name, 'box':list(box), 'language':language, 'psm':psm,
                                 'expected':expected, 'recognized':recognized,
                                 'match':value is not None and value == bench.comparison_value(name, expected)})
    result = {'status':'human_review_required', 'image_sha256':sample['sha256'],
              'engine':version, 'engine_sha256':engine_hash, 'model_sha256':models,
              'preprocessing':'grayscale, autocontrast, 3x Lanczos, threshold 160, 30px white border',
              'scope':'One synthetic image and hand-selected crops; not an independent or representative evaluation.',
              'results':rows}
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print('Synthetic number-crop matches:', sum(item['match'] for item in rows), '/', len(rows))


if __name__ == '__main__':
    main()
