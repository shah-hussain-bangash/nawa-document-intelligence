"""Conservative evaluation-only support for value-before-label OCR lines."""
import ocr_benchmark as baseline

def field_matches(text, expected):
    """Accept exactly one known label and one value per line; reject duplicates."""
    label_map = {baseline.normalize(label).casefold(): key
                 for key, labels in baseline.LABELS.items() for label in labels}
    fields = {}
    for line in text.splitlines():
        line = baseline.normalize(line)
        if line.count(':') != 1:
            continue
        left, right = (part.strip() for part in line.split(':'))
        left_key, right_key = label_map.get(left.casefold()), label_map.get(right.casefold())
        if bool(left_key) == bool(right_key):
            continue
        key, value = (left_key, right) if left_key else (right_key, left)
        if value:
            fields.setdefault(key, []).append(value)
    return {key: len(fields.get(key, [])) == 1 and
            baseline.comparison_value(key, fields[key][0]) is not None and
            baseline.comparison_value(key, fields[key][0]) == baseline.comparison_value(key, value)
            for key, value in expected.items()}
