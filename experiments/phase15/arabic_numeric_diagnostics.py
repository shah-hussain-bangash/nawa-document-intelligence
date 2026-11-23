"""Synthetic-only review hints for exact Arabic numeric labels; no approval."""
import ocr_benchmark as bench
from arabic_label_candidate_experiment import ARABIC_LABELS, NUMERIC


def diagnose(text):
    """Categorize observed text without correcting OCR or validating amounts."""
    if not isinstance(text, str):
        raise ValueError('Expected synthetic OCR text')
    output = {}
    for field in sorted(NUMERIC):
        label = ARABIC_LABELS[field]
        tails = []
        for line in text.splitlines():
            line = bench.normalize(line)
            if not line.startswith(label):
                continue
            tail = line[len(label):]
            if tail and not (tail[0].isspace() or tail[0] == ':' or
                             tail[0] in '0123456789٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹'):
                continue
            value = tail.strip()
            if value.startswith(':'):
                value = value[1:].strip()
            tails.append(value)
        if not tails:
            reason = 'exact_label_not_found'
        elif len(tails) > 1:
            reason = 'duplicate_label'
        elif not tails[0]:
            reason = 'value_missing'
        elif '،' in tails[0]:
            reason = 'ambiguous_arabic_comma'
        elif bench.comparison_value(field, tails[0]) is None:
            reason = 'unrecognized_number'
        else:
            reason = 'unverified_numeric_candidate'
        output[field] = reason
    return {'status':'human_review_required', 'promotable':False, 'reasons':output,
            'scope':'Synthetic review hints only; values are not corrected or verified.'}
