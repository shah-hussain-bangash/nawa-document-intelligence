"""Evaluation-only extraction of exact Arabic labels from synthetic OCR lines."""
import re
import ocr_benchmark as bench

ARABIC_LABELS = {
    'supplier':'اسم المورد', 'currency':'العملة', 'subtotal':'المجموع الفرعي',
    'vat_rate':'نسبة الضريبة', 'vat_amount':'قيمة الضريبة',
    'total':'الإجمالي شامل الضريبة',
}
NUMERIC = frozenset({'subtotal', 'vat_rate', 'vat_amount', 'total'})


def candidates(text):
    """Collect untrusted candidates only; reject duplicated or malformed labels.

    Exact prefix labels are supported with a colon, whitespace, or (for
    numeric fields only) an immediately adjacent digit. This cannot verify a
    quotation or infer the meaning of a punctuation mark.
    """
    if not isinstance(text, str):
        raise ValueError('Synthetic OCR text must be a string')
    found = {}
    for line in text.splitlines():
        normalized = bench.normalize(line)
        for key, label in ARABIC_LABELS.items():
            if not normalized.startswith(label):
                continue
            tail = normalized[len(label):]
            if tail and not (tail[0].isspace() or tail[0] == ':' or
                             (key in NUMERIC and tail[0] in '0123456789٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹')):
                continue
            value = tail.strip()
            if value.startswith(':'):
                value = value[1:].strip()
            if not value or ':' in value or any(other in value for other in ARABIC_LABELS.values()):
                value = None
            if key in NUMERIC and value is not None and bench.comparison_value(key, value) is None:
                value = None
            found.setdefault(key, []).append(value)
    return {key:values[0] for key, values in found.items()
            if len(values) == 1 and values[0] is not None}


def evaluate(text, expected):
    """Compare candidates to synthetic references; never authorize a decision."""
    values = candidates(text)
    matches = {}
    for key, reference in expected.items():
        actual = bench.comparison_value(key, values.get(key))
        matches[key] = actual is not None and actual == bench.comparison_value(key, reference)
    return {'status':'human_review_required', 'promotable':False,
            'field_matches':matches, 'fields_correct':sum(matches.values())}
