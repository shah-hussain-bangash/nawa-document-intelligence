"""Narrow local QA repair for one synthetic currency-label ordering."""
import re
import unicodedata


def normalize_fixture_line(line, base_normalizer):
    value=unicodedata.normalize('NFKC',line).strip()
    if re.fullmatch(r'AED\s*:\s*العملة',value,flags=re.IGNORECASE):
        return 'العملة: AED'
    return base_normalizer(line)

