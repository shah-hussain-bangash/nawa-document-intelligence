"""Compare pinned fast and best models on local synthetic examples."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
import pymupdf
import ocr_benchmark as b

BEST = b.HERE / 'tessdata-best-e12c65a'

def main():
    provenance = json.loads((BEST / 'provenance.json').read_text(encoding='utf-8'))
    for name in ('ara.traineddata', 'eng.traineddata'):
        b.verify(BEST / name, provenance['files'][name]['sha256'])
    for name, digest in b.MODEL_HASHES.items():
        b.verify(b.TESSDATA / name, digest)
    cases = json.loads((b.HERE / 'additional-samples-result.json').read_text(encoding='utf-8'))['cases']
    arabic = cases[-1]
    pdf = b.HERE.parents[1] / 'nawa-phase13' / 'demo' / 'samples' / 'pdf' / arabic['file']
    b.verify(pdf, arabic['pdf_sha256'])
    results = []
    with tempfile.TemporaryDirectory(dir=b.HERE) as temp:
        image = Path(temp) / 'arabic-pdf-page.png'
        with pymupdf.open(pdf) as document:
            document[0].get_pixmap(dpi=200, alpha=False).save(image)
        samples = [dict(b.SAMPLES[0]), dict(b.SAMPLES[1]), {
            'id':'arabic_pdf_page', 'language':'ara+eng', 'image':str(image),
            'reference':arabic['reference_synthetic'], 'fields':b.SAMPLES[1]['fields']}]
        for sample in samples:
            path = Path(sample['image']) if Path(sample['image']).is_absolute() else b.HERE / sample['image']
            if 'sha256' in sample:
                b.verify(path, sample['sha256'])
            for model, folder in [('fast',b.TESSDATA), ('best',BEST)]:
                start = time.perf_counter()
                run = subprocess.run([str(b.TESSERACT), str(path), 'stdout', '--tessdata-dir',str(folder),
                    '-l',sample['language'],'--psm','6'], capture_output=True, check=True, timeout=60)
                elapsed = time.perf_counter()-start
                text = run.stdout.decode('utf-8')
                fields = b.field_results(text,sample['fields'])
                results.append({'case':sample['id'], 'model':model, 'elapsed_seconds_single_run':round(elapsed,3),
                    'fields_correct':sum(fields.values()), 'field_matches':fields,
                    **b.rates('\n'.join(sample['reference']),text), 'ocr_text_synthetic':text})
    out = {'scope':'Same three synthetic images; no independent ground truth or production validation.',
           'status':'human_review_required', 'fast_commit':'87416418657359cb625c412a48b6e1d6d41c29bd',
           'best_provenance':provenance, 'dpi':200, 'psm':6, 'results':results}
    with (b.HERE / 'best-model-comparison.json').open('x',encoding='utf-8') as stream:
        json.dump(out,stream,ensure_ascii=False,indent=2)
    for row in results:
        print(f"{row['case']} {row['model']}: {row['fields_correct']}/6 fields, CER {row['cer']:.1%}, {row['elapsed_seconds_single_run']}s")

if __name__ == '__main__':
    main()
