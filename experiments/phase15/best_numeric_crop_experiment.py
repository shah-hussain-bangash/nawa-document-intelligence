"""Compare two pinned Tesseract models on manually selected synthetic number crops."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
from PIL import Image
import ocr_benchmark as bench
from numeric_crop_experiment import REGIONS

BEST = bench.HERE / 'tessdata-best-e12c65a'

def numeric(text):
    value = bench.normalize(text)
    if not re.fullmatch(r'[0-9٠-٩۰-۹.,٫٬]+', value):
        return None
    return value.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫', '01234567890123456789.'))

def main():
    sample = bench.SAMPLES[1]
    image = bench.HERE / sample['image']
    bench.verify(image, sample['sha256'])
    bench.verify(bench.TESSDATA / 'ara.traineddata', bench.MODEL_HASHES['ara.traineddata'])
    provenance = json.loads((BEST / 'provenance.json').read_text(encoding='utf-8'))
    bench.verify(BEST / 'ara.traineddata', provenance['files']['ara.traineddata']['sha256'])
    rows = []
    with tempfile.TemporaryDirectory(dir=bench.HERE) as temp, Image.open(image) as page:
        for name, box, expected in REGIONS:
            for scale in (1, 2, 3):
                crop = page.crop(box)
                if scale > 1:
                    crop = crop.resize((crop.width * scale, crop.height * scale), Image.Resampling.LANCZOS)
                path = Path(temp) / 'crop.png'
                crop.save(path)
                for model, folder in [('fast', bench.TESSDATA), ('best', BEST)]:
                    for mode in (7, 13):
                        proc = subprocess.run([str(bench.TESSERACT), str(path), 'stdout',
                            '--tessdata-dir', str(folder), '-l', 'ara', '--psm', str(mode)],
                            check=True, capture_output=True, timeout=30)
                        output = bench.normalize(proc.stdout.decode('utf-8'))
                        rows.append({'region':name, 'box':box, 'scale':scale, 'model':model,
                            'psm':mode, 'expected':expected, 'recognized':output,
                            'normalized_numeric_match':numeric(output) is not None and numeric(output) == numeric(expected)})
    with (bench.HERE / 'best-numeric-crop-result.json').open('x', encoding='utf-8') as out:
        json.dump({'status':'human_review_required', 'scope':'Manually chosen regions of one synthetic image; not an automatic or independent accuracy test.',
            'image_sha256':sample['sha256'], 'best_model_commit':provenance['commit'], 'results':rows}, out, ensure_ascii=False, indent=2)
    for model in ('fast', 'best'):
        for name, _, _ in REGIONS:
            group = [r for r in rows if r['region'] == name and r['model'] == model]
            print(model, name, 'exact normalized matches:', sum(r['normalized_numeric_match'] for r in group), '/', len(group))

if __name__ == '__main__':
    main()
