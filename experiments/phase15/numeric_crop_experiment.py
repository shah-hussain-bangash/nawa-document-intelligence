"""Manually crop four numeric regions in one synthetic image for OCR exploration."""
import json
from pathlib import Path
import subprocess
import tempfile
from PIL import Image
import ocr_benchmark as baseline

# Coordinates were chosen by visually inspecting this exact synthetic image.
# They are not a detector and will not work reliably on other documents.
REGIONS = [
    ('subtotal', (1130, 460, 1282, 520), '٩٠٠٫٠٠'),
    ('vat_rate', (1270, 565, 1325, 625), '٥'),
    ('vat_amount', (1200, 670, 1325, 730), '٤٥٫٠٠'),
    ('total', (1045, 775, 1200, 835), '٩٤٥٫٠٠'),
]

def main():
    sample = baseline.SAMPLES[1]
    image = baseline.HERE / sample['image']
    baseline.verify(image, sample['sha256'])
    for name, digest in baseline.MODEL_HASHES.items():
        baseline.verify(baseline.TESSDATA / name, digest)
    rows = []
    with tempfile.TemporaryDirectory(dir=baseline.HERE) as temp, Image.open(image) as page:
        for name, box, expected in REGIONS:
            for scale in (1, 2):
                crop = page.crop(box)
                if scale == 2:
                    crop = crop.resize((crop.width * 2, crop.height * 2), Image.Resampling.LANCZOS)
                path = Path(temp) / 'crop.png'
                crop.save(path)
                for mode in (7, 13):
                    proc = subprocess.run([str(baseline.TESSERACT), str(path), 'stdout',
                        '--tessdata-dir', str(baseline.TESSDATA), '-l', 'ara', '--psm', str(mode)],
                        capture_output=True, check=True, timeout=30)
                    output = baseline.normalize(proc.stdout.decode('utf-8'))
                    rows.append({'region':name, 'box':box, 'scale':scale, 'psm':mode,
                        'expected':expected, 'recognized':output, 'exact_match':output == expected})
    with (baseline.HERE / 'numeric-crop-result.json').open('x', encoding='utf-8') as out:
        json.dump({'status':'human_review_required', 'scope':'Manually selected numeric regions from one known synthetic image; not an automatic extraction test.',
                   'image_sha256':sample['sha256'], 'results':rows}, out, ensure_ascii=False, indent=2)
    for name, _, _ in REGIONS:
        group = [r for r in rows if r['region'] == name]
        print(name, 'exact matches:', sum(r['exact_match'] for r in group), '/', len(group))

if __name__ == '__main__':
    main()
