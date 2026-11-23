"""Read-only number-format signals for a single synthetic quotation export.

This is not a database scanner, a migration, or a correctness determination.
"""
from .core import decimal_value


FIELDS = {'subtotal': 'subtotal', 'vat_rate_percent': 'vat_rate',
          'vat_amount': 'vat_amount', 'total': 'total'}


def review_signals(quotation, ledger=None):
    """Return review signals without copying source text or changing inputs.

    An empty list is not proof of correctness, locale, provenance or authorization.
    A supplied ledger is inspected structurally, not authenticated or hash-verified.
    """
    if not isinstance(quotation, dict):
        raise ValueError('A quotation object is required')
    findings = []

    def flag(location, reason):
        findings.append({'location': location, 'reason': reason})

    evidence = quotation.get('evidence')
    for field, evidence_field in FIELDS.items():
        location = 'quotation.' + field
        ev = evidence.get(evidence_field) if isinstance(evidence, dict) else None
        raw = ev.get('value') if isinstance(ev, dict) else None
        saved = quotation.get(field)
        if not isinstance(raw, str) or not isinstance(saved, str):
            flag(location, 'missing_value_or_source_evidence')
            continue
        if ',' in raw or '٬' in raw:
            flag(location, 'separator_convention_requires_review')
        try:
            source_value = decimal_value(raw, field)
            saved_value = decimal_value(saved, field)
            if source_value != saved_value:
                flag(location, 'saved_value_differs_from_source')
        except ValueError:
            flag(location, 'unsupported_or_invalid_number')

    if ledger is not None:
        events = ledger.get('events') if isinstance(ledger, dict) else None
        if not isinstance(events, list) or not events:
            flag('ledger', 'missing_or_invalid_events')
        else:
            for index, event in enumerate(events, 1):
                if not isinstance(event, dict):
                    flag('ledger', 'invalid_event')
                    continue
                if event.get('type') == 'correction':
                    location = f'ledger.event_{index}'
                    flag(location, 'correction_requires_source_review')
                    data = event.get('data')
                    field = data.get('field') if isinstance(data, dict) else None
                    value = data.get('to') if isinstance(data, dict) else None
                    if isinstance(field, str) and field in FIELDS:
                        if isinstance(value, str) and (',' in value or '٬' in value):
                            flag(location, 'separator_convention_requires_review')
                        try:
                            if not isinstance(value, str):
                                raise ValueError('Invalid value')
                            decimal_value(value, field)
                        except ValueError:
                            flag(location, 'unsupported_or_invalid_number')
    return {'signals_detected': bool(findings), 'findings': findings,
            'scope': 'Synthetic screening only; original-source human review remains required.'}
