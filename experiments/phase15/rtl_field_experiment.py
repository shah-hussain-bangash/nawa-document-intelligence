"""Conservative evaluation-only support for value-before-label OCR lines."""
import ocr_benchmark as baseline

def field_matches(text, expected):
    """Accept exactly one known label and one value per line; reject duplicates."""
    digit_map = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫٬', '01234567890123456789.,')
    def canonical(value):
        return baseline.normalize(value).translate(digit_map).replace(',', '').strip().casefold()
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
            canonical(fields[key][0]) == canonical(value)
            for key, value in expected.items()}
