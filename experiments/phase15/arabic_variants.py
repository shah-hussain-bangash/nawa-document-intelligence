"""Compare settings on the fixed synthetic Arabic image; not production OCR."""
import json
from pathlib import Path
import subprocess
import tempfile
from PIL import Image
import ocr_benchmark as baseline

def main():
    sample = baseline.SAMPLES[1]
    image = baseline.HERE / sample['image']
    baseline.verify(image, sample['sha256'])
    for name, digest in baseline.MODEL_HASHES.items():
        baseline.verify(baseline.TESSDATA / name, digest)
    results = []
    with tempfile.TemporaryDirectory(dir=baseline.HERE) as temp:
        scaled = Path(temp) / 'scaled.png'
        with Image.open(image) as source:
            source.resize((source.width * 2, source.height * 2), Image.Resampling.LANCZOS).save(scaled)
        for scale, input_path in [(1, image), (2, scaled)]:
            for lang in ['ara+eng', 'eng+ara', 'ara']:
                for mode in [3, 4, 6, 11]:
                    run = subprocess.run([str(baseline.TESSERACT), str(input_path), 'stdout',
                        '--tessdata-dir', str(baseline.TESSDATA), '-l', lang, '--psm', str(mode)],
                        capture_output=True, check=True, timeout=30)
                    output = run.stdout.decode('utf-8')
                    fields = baseline.field_results(output, sample['fields'])
                    results.append({'scale': scale, 'language': lang, 'psm': mode,
                        'fields_correct': sum(fields.values()), 'field_matches': fields,
                        **baseline.rates('\n'.join(sample['reference']), output),
                        'ocr_text_synthetic': output})
    results.sort(key=lambda r: (-r['fields_correct'], r['cer']))
    destination = baseline.HERE / 'arabic-variants-result.json'
    with destination.open('x', encoding='utf-8') as out:
        json.dump({'status':'human_review_required', 'scope':'Exploratory tuning on one synthetic image; no held-out evaluation.', 'variants':results}, out, ensure_ascii=False, indent=2)
    for row in results:
        print(f"scale={row['scale']} language={row['language']} psm={row['psm']} fields={row['fields_correct']}/6 CER={row['cer']:.1%}")

if __name__ == '__main__':
    main()
