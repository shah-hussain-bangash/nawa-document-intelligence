"""Compare one local synthetic Arabic page; not a production OCR pipeline."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import ocr_benchmark as bench
from rtl_field_experiment import field_matches as rtl_field_matches
from arabic_label_candidate_experiment import evaluate as evaluate_candidates

MODEL_FILES = ('inference.json', 'inference.pdiparams', 'inference.yml')
PDF_SAMPLE = {
    'sha256':'8ba0740b728db0fac7bc655183854ea882db00545445a6bfd11f3d206f7e75b9',
    'reference':['اسم المورد: شركة المثال للتوريدات', 'العملة: AED',
                 'المجموع الفرعي: ٩٠٠٫٠٠', 'نسبة الضريبة: ٥', 'قيمة الضريبة: ٤٥٫٠٠',
                 'Grand Total: 945.00'],
    'fields':{'supplier':'شركة المثال للتوريدات', 'currency':'AED', 'subtotal':'900.00',
              'vat_rate':'5', 'vat_amount':'45.00', 'total':'945.00'},
}


def hashes(folder):
    return {name:hashlib.sha256((folder / name).read_bytes()).hexdigest()
            for name in MODEL_FILES}


def evaluate_lines(lines, sample):
    if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
        raise ValueError('Invalid synthetic OCR lines')
    text = '\n'.join(lines)
    strict = bench.field_results(text, sample['fields'])
    rtl = rtl_field_matches(text, sample['fields'])
    candidates = evaluate_candidates(text, sample['fields'])
    return {'lines_synthetic':lines, **bench.rates('\n'.join(sample['reference']), text),
            'strict_field_matches':strict, 'rtl_field_matches':rtl,
            'candidate_field_matches':candidates['field_matches'],
            'strict_fields_correct':sum(strict.values()), 'rtl_fields_correct':sum(rtl.values()),
            'candidate_fields_correct':candidates['fields_correct']}


def main():
    parser = argparse.ArgumentParser(description='Run fixed synthetic Arabic page OCR locally')
    parser.add_argument('--det-dir', type=Path, required=True)
    parser.add_argument('--rec-dir', type=Path, required=True)
    parser.add_argument('--qa-home', type=Path, required=True)
    parser.add_argument('--case', choices=('arabic-label', 'arabic-pdf'), default='arabic-label')
    parser.add_argument('--synthetic-image', type=Path, help='Pinned rendered synthetic PDF page for arabic-pdf')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Refusing to overwrite the result')
    det, rec, qa = (item.resolve(strict=True) for item in (args.det_dir, args.rec_dir, args.qa_home))
    if not all(item.is_dir() for item in (det, rec, qa)):
        raise ValueError('Model and QA paths must be directories')
    model_hashes = {'detector':hashes(det), 'recognizer':hashes(rec)}
    sample = bench.SAMPLES[1] if args.case == 'arabic-label' else PDF_SAMPLE
    if args.case == 'arabic-pdf' and args.synthetic_image is None:
        raise ValueError('The pinned synthetic PDF rendering is required')
    if args.case == 'arabic-label' and args.synthetic_image is not None:
        raise ValueError('Custom image is not supported for this case')
    image = bench.HERE / sample['image'] if args.case == 'arabic-label' else args.synthetic_image
    bench.verify(image, sample['sha256'])
    old_expanduser = os.path.expanduser
    os.path.expanduser = lambda path: str(qa) if path == '~' else old_expanduser(path)
    try:
        import paddle
        import paddleocr
        from paddleocr import PaddleOCR
        pipeline = PaddleOCR(text_detection_model_name='PP-OCRv5_mobile_det',
            text_detection_model_dir=str(det), text_recognition_model_name='arabic_PP-OCRv5_mobile_rec',
            text_recognition_model_dir=str(rec), use_doc_orientation_classify=False,
            use_doc_unwarping=False, use_textline_orientation=False, device='cpu', enable_mkldnn=False)
        outputs = list(pipeline.predict(str(image)))
        if len(outputs) != 1:
            raise ValueError('Unexpected synthetic page result count')
        rows = list(outputs[0].json['res']['rec_texts'])
        metrics = evaluate_lines(rows, sample)
        if model_hashes != {'detector':hashes(det), 'recognizer':hashes(rec)}:
            raise ValueError('Synthetic models changed during run')
        result = {'status':'human_review_required', 'source_sha256':sample['sha256'],
                  'case':args.case,
                  'model_sha256':model_hashes, 'paddle_version':paddle.__version__,
                  'paddleocr_version':paddleocr.__version__, 'python_version':sys.version.split()[0],
                  'scope':'One fixed synthetic image; reference is not independently reviewed.',
                  **metrics}
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
        print('Detected lines:', len(rows), '; strict fields:', metrics['strict_fields_correct'],
              '/ 6; RTL helper fields:', metrics['rtl_fields_correct'],
              '/ 6; exact-label candidates:', metrics['candidate_fields_correct'], '/ 6')
    finally:
        os.path.expanduser = old_expanduser


if __name__ == '__main__':
    main()
