"""Exercise the combined experimental Windows path on fixed local fixtures."""
import ocr_benchmark as baseline
import hashlib
from bounded_ocr_prototype import recognize_with_pinned_engine
from windows_gated_bounded import run_gated_bounded

def main():
    # For this local smoke test only, derive the comparison hash from the local
    # executable. A real deployment needs a separately trusted expected digest.
    engine_hash = hashlib.sha256(baseline.TESSERACT.read_bytes()).hexdigest()
    for sample, expected_count in zip(baseline.SAMPLES, (6, 2)):
        image = baseline.HERE / sample['image']
        baseline.verify(image, sample['sha256'])
        hashes = {lang + '.traineddata': baseline.MODEL_HASHES[lang + '.traineddata']
                  for lang in sample['language'].split('+')}
        result = recognize_with_pinned_engine(image, baseline.TESSERACT,
            baseline.TESSDATA, sample['language'], hashes, engine_hash, runner=run_gated_bounded)
        count = sum(baseline.field_results(result['extracted_text_untrusted'], sample['fields']).values())
        if count != expected_count or result['status'] != 'human_review_required':
            raise AssertionError('Synthetic result changed or review status missing')
        print(f"{sample['id']}: {count}/6 fields; {result['status']}; {result['engine_version_unverified']}")

if __name__ == '__main__':
    main()
