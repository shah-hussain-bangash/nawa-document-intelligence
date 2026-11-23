"""Offline synthetic field/value experiment; not a source or approval validator."""
import re
from decimal import Decimal, InvalidOperation

_LABELS = {
    'subtotal': ('subtotal', 'المجموع الفرعي'),
    'vat_amount': ('vat amount', 'قيمة الضريبة'),
    'total': ('grand total', 'الإجمالي شامل الضريبة'),
}
_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫', '01234567890123456789.')
_AMOUNT = re.compile(r'^[0-9]{1,12}(?:\.[0-9]{1,2})?$', re.ASCII)
_LINE = re.compile(
    r'^\s*(?P<label>subtotal|vat amount|grand total|المجموع الفرعي|قيمة الضريبة|الإجمالي شامل الضريبة)'
    r'\s*:?\s+AED\s+(?P<amount>[0-9٠-٩۰-۹.٫]+)\s*$', re.IGNORECASE)


def _amount(value):
    if not isinstance(value, str) or len(value) > 30:
        raise ValueError('Unsupported amount')
    value = value.translate(_DIGITS)
    if not _AMOUNT.fullmatch(value):
        raise ValueError('Unsupported amount')
    try:
        return Decimal(value)
    except InvalidOperation:
        raise ValueError('Unsupported amount') from None


def check_structured_claim(claim, source_line):
    """Compare one exact synthetic AED field line; never authorize or approve.

    The caller must independently establish source origin, access and freshness.
    Unsupported formats and contradictory amounts require human review.
    """
    result = {'status': 'requires_human_review', 'field_value_match': False}
    if (not isinstance(claim, dict) or set(claim) != {'field', 'amount', 'currency'}
            or not isinstance(claim.get('field'), str) or claim['field'] not in _LABELS
            or claim.get('currency') != 'AED'
            or not isinstance(source_line, str) or len(source_line) > 200
            or source_line.splitlines() != [source_line]):
        return result
    try:
        match = _LINE.fullmatch(source_line)
        if not match or match.group('label').casefold() not in _LABELS[claim['field']]:
            return result
        result['field_value_match'] = _amount(claim['amount']) == _amount(match.group('amount'))
    except ValueError:
        return result
    return result
