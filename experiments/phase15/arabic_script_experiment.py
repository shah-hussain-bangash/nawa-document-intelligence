"""Compare official Arabic script OCR on one fixed synthetic image and crops."""
import json
from pathlib import Path
import subprocess
import tempfile
from PIL import Image
import ocr_benchmark as bench
from best_numeric_crop_experiment import numeric
from numeric_crop_experiment import REGIONS

TESSDATA = bench.HERE / 'tessdata-best-e12c65a'

def ocr(path, language, mode):
    result = subprocess.run([str(bench.TESSERACT), str(path), 'stdout', '--tessdata-dir',
        str(TESSDATA), '-l', language, '--psm', str(mode)],
        check=True, capture_output=True, timeout=30)
    return result.stdout.decode('utf-8')

def main():
    sample = bench.SAMPLES[1]
    image = bench.HERE / sample['image']
    bench.verify(image, sample['sha256'])
    provenance = json.loads((TESSDATA / 'script' / 'provenance.json').read_text(encoding='utf-8'))
    bench.verify(TESSDATA / 'script' / 'Arabic.traineddata', provenance['sha256'])
    models = json.loads((TESSDATA / 'provenance.json').read_text(encoding='utf-8'))
    for name in ('ara.traineddata', 'eng.traineddata'):
        bench.verify(TESSDATA / name, models['files'][name]['sha256'])
    full = []
    for language in ('ara+eng', 'script/Arabic+eng'):
        text = ocr(image, language, 6)
        matches = bench.field_results(text, sample['fields'])
        full.append({'language':language, 'fields_correct':sum(matches.values()), 'field_matches':matches,
                     **bench.rates('\n'.join(sample['reference']), text), 'ocr_text_synthetic':text})
    crops = []
    with tempfile.TemporaryDirectory(dir=bench.HERE) as temp, Image.open(image) as page:
        for name, box, expected in REGIONS:
            for scale in (1, 2, 3):
                crop = page.crop(box)
                if scale > 1:
                    crop = crop.resize((crop.width * scale, crop.height * scale), Image.Resampling.LANCZOS)
                path = Path(temp) / 'crop.png'
                crop.save(path)
                for mode in (7, 13):
                    text = bench.normalize(ocr(path, 'script/Arabic', mode))
                    crops.append({'region':name,'scale':scale,'psm':mode,'recognized':text,
                        'expected':expected,'numeric_match':numeric(text) is not None and numeric(text)==numeric(expected)})
    with (bench.HERE / 'arabic-script-result.json').open('x', encoding='utf-8') as out:
        json.dump({'status':'human_review_required','scope':'One synthetic image; hand-selected crops, not representative or independent.',
                   'image_sha256':sample['sha256'],'script_model':provenance,'full_page':full,'crops':crops}, out, ensure_ascii=False, indent=2)
    for row in full:
        print(row['language'], 'full page:', row['fields_correct'], '/ 6 fields; CER', f"{row['cer']:.1%}")
    for name, _, _ in REGIONS:
        group = [r for r in crops if r['region'] == name]
        print(name, 'crop numeric matches:', sum(r['numeric_match'] for r in group), '/', len(group))

if __name__ == '__main__':
    main()
