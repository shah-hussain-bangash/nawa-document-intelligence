"""Fail-closed marker check for the synthetic text-only intake draft."""

def require_text_only_result(result):
    """Reject OCR, unknown provenance and review markers before promotion.

    This checks the server-produced result shape. It does not authenticate the
    producer or prove that a text result is not derived from OCR elsewhere.
    """
    if not isinstance(result, dict):
        raise ValueError('Synthetic result unavailable for promotion')
    if 'input_type' in result and result['input_type'] != 'text_layer_pdf':
        raise ValueError('Unknown or OCR extraction requires separate review')
    forbidden = {'status', 'state', 'promotable', 'requires_human_review'}
    if forbidden.intersection(result) or any(str(key).startswith('ocr_') for key in result):
        raise ValueError('Unknown or OCR extraction requires separate review')
    evidence = result.get('evidence')
    if not isinstance(evidence, dict) or not evidence:
        raise ValueError('Synthetic source evidence is required')
    for item in evidence.values():
        if not isinstance(item, dict) or ('method' in item and item['method'] != 'text_layer'):
            raise ValueError('Unknown or OCR extraction requires separate review')
        if forbidden.intersection(item) or any(str(key).startswith('ocr_') for key in item):
            raise ValueError('Unknown or OCR extraction requires separate review')
