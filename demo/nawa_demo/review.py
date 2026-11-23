"""Phase 8: offline human review of synthetic quotations.

Append-only hash-linked events detect accidental edits (not a secure audit store).
Trusted identity, authorization and concurrency are NOT implemented.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re

from .core import decimal_value

FIELDS = ('supplier', 'currency', 'subtotal', 'vat_rate_percent', 'vat_amount', 'total')
MONEY = Decimal('0.01')
DECISIONS = ('approve', 'reject', 'request_changes')


def _json(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def _digest(event):
    return hashlib.sha256(_json({k: v for k, v in event.items() if k != 'hash'}).encode('utf-8')).hexdigest()


def _check_str(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 500:
        raise ValueError(f'{label} must be a nonempty string (max 500 characters)')
    return value.strip()


def _financial(fields):
    if set(fields) != set(FIELDS):
        raise ValueError('Quotation fields missing or unexpected')
    if not all(isinstance(fields[k], str) for k in FIELDS):
        raise ValueError('All quotation values must be strings')
    _check_str(fields['supplier'], 'supplier')
    if fields['currency'] != 'AED':
        raise ValueError('Only AED is supported')
    amounts = {k: decimal_value(fields[k], k) for k in FIELDS[2:]}
    if any(v < 0 for v in amounts.values()) or amounts['vat_rate_percent'] > 100:
        raise ValueError('Invalid nonnegative financial ranges or VAT rate')
    expected_vat = (amounts['subtotal'] * amounts['vat_rate_percent'] / 100).quantize(MONEY, rounding=ROUND_HALF_UP)
    expected_total = (amounts['subtotal'] + amounts['vat_amount']).quantize(MONEY, rounding=ROUND_HALF_UP)
    # In this demo, monetary values must represent actual cents (no rounding-off input).
    if any(amounts[k] != amounts[k].quantize(MONEY) for k in ('subtotal', 'vat_amount', 'total')):
        raise ValueError('Monetary values must have at most two decimal places')
    return {'vat_matches_rate': amounts['vat_amount'] == expected_vat,
            'total_matches_components': amounts['total'] == expected_total,
            'expected_vat': str(expected_vat), 'expected_total': str(expected_total)}


def _apply(record):
    if not isinstance(record, dict) or set(record) != {'schema', 'document', 'events'} or record['schema'] != 'nawa-review-v1':
        raise ValueError('Invalid review ledger schema')
    events = record['events']
    if not isinstance(events, list) or not events:
        raise ValueError('Review ledger requires events')
    document = _check_str(record['document'], 'document')
    fields = None
    evidence = None
    status = 'pending_review'
    last_hash = 'GENESIS'
    history = []
    corrections = []
    for i, event in enumerate(events, 1):
        if not isinstance(event, dict) or set(event) != {'sequence', 'type', 'actor', 'timestamp', 'data', 'previous_hash', 'hash'}:
            raise ValueError('Invalid event structure')
        if type(event['sequence']) is not int or event['sequence'] != i or event['previous_hash'] != last_hash:
            raise ValueError('Event order or hash chain broken')
        if event['hash'] != _digest(event):
            raise ValueError('Event integrity hash mismatch')
        actor = _check_str(event['actor'], 'actor')
        _check_str(event['timestamp'], 'timestamp')
        data = event['data']
        if not isinstance(data, dict):
            raise ValueError('Invalid event data')
        kind = event['type']
        if i == 1:
            if (kind != 'created' or set(data) not in ({'fields', 'evidence'}, {'fields', 'evidence', 'preparer'})
                    or actor != 'system'):
                raise ValueError('First event must be system-created')
            if 'preparer' in data and (not isinstance(data['preparer'], str)
                    or not re.fullmatch(r'oidc:[0-9a-f]{64}', data['preparer'])):
                raise ValueError('Invalid synthetic preparer identity')
            if not isinstance(data['fields'], dict) or not isinstance(data['evidence'], dict):
                raise ValueError('Invalid source data')
            fields = deepcopy(data['fields'])
            evidence = deepcopy(data['evidence'])
            if not {'supplier', 'currency', 'subtotal', 'vat_rate', 'vat_amount', 'total'} <= set(evidence):
                raise ValueError('All fields require provenance evidence')
            for name in ('supplier', 'currency', 'subtotal', 'vat_rate', 'vat_amount', 'total'):
                ev = evidence[name]
                if not isinstance(ev, dict) or not isinstance(ev.get('line'), int) or ev['line'] < 1 or not isinstance(ev.get('source_text'), str) or not ev['source_text'].strip():
                    raise ValueError('Invalid field provenance')
            _financial(fields)
        elif kind == 'correction':
            if set(data) != {'field', 'from', 'to', 'reason', 'evidence'} or data['field'] not in FIELDS:
                raise ValueError('Invalid correction event')
            if status in ('approved', 'rejected'):
                raise ValueError('Final review cannot be edited')
            field = data['field']
            if data['from'] != fields[field]:
                raise ValueError('Correction old value mismatch')
            if not isinstance(data['to'], str) or data['to'] == fields[field]:
                raise ValueError('Correction must change a string value')
            _check_str(data['reason'], 'correction reason')
            provenance = data['evidence']
            if not isinstance(provenance, dict) or set(provenance) != {'source', 'line', 'quote'}:
                raise ValueError('Correction evidence requires source, line and quote')
            _check_str(provenance['source'], 'source')
            _check_str(provenance['quote'], 'evidence quote')
            if type(provenance['line']) is not int or provenance['line'] < 1 or provenance['source'] != document:
                raise ValueError('Correction source must match original document')
            fields[field] = data['to']
            _financial(fields)
            corrections.append({'sequence': i, 'field': field, 'from': data['from'], 'to': data['to'],
                                'reason': data['reason'], 'evidence': deepcopy(provenance)})
            status = 'pending_review'
        elif kind == 'decision':
            if set(data) != {'decision', 'reason'} or data['decision'] not in DECISIONS:
                raise ValueError('Invalid decision')
            _check_str(data['reason'], 'decision reason')
            if status in ('approved', 'rejected'):
                raise ValueError('Final decision already made')
            if data['decision'] == 'approve' and not all(_financial(fields)[k] for k in ('vat_matches_rate', 'total_matches_components')):
                raise ValueError('Cannot approve a quotation with financial mismatches')
            status = {'approve': 'approved', 'reject': 'rejected', 'request_changes': 'changes_requested'}[data['decision']]
        else:
            raise ValueError('Unknown event type')
        history.append({'sequence': i, 'type': kind, 'actor': actor, 'timestamp': event['timestamp'], 'hash': event['hash']})
        last_hash = event['hash']
    return {'document': document, 'fields': fields, 'source_evidence': evidence,
            'checks': _financial(fields), 'status': status, 'revision': len(events),
            'last_hash': last_hash, 'history': history, 'corrections': corrections}


def inspect(record):
    """Replay and verify entire ledger before exposing current state."""
    return _apply(deepcopy(record))


def _append(record, kind, actor, data, *, expected_revision, timestamp=None):
    state = inspect(record)
    if type(expected_revision) is not int or expected_revision != state['revision']:
        raise ValueError('Stale revision; reload before changing review')
    actor = _check_str(actor, 'reviewer identity')
    if actor == 'system':
        raise ValueError('system is reserved')
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    else:
        _check_str(timestamp, 'timestamp')
    event = {'sequence': expected_revision + 1, 'type': kind, 'actor': actor,
             'timestamp': timestamp, 'data': data, 'previous_hash': state['last_hash']}
    event['hash'] = _digest(event)
    updated = deepcopy(record)
    updated['events'].append(event)
    inspect(updated)
    return updated


def begin(quotation, *, actor='system', timestamp='2026-01-01T00:00:00+00:00', preparer=None):
    if not isinstance(quotation, dict):
        raise ValueError('Invalid quotation')
    document = _check_str(quotation.get('document'), 'document')
    fields = {field: quotation[field] for field in FIELDS}
    evidence = quotation.get('evidence')
    if not isinstance(evidence, dict):
        raise ValueError('Quotation evidence required')
    data = {'fields': fields, 'evidence': evidence}
    if preparer is not None:
        data['preparer'] = preparer
    event = {'sequence': 1, 'type': 'created', 'actor': actor, 'timestamp': timestamp,
             'data': data, 'previous_hash': 'GENESIS'}
    event['hash'] = _digest(event)
    record = {'schema': 'nawa-review-v1', 'document': document, 'events': [event]}
    inspect(record)
    return record


def correct(record, *, actor, field, value, reason, source, line, quote, expected_revision, timestamp=None):
    state = inspect(record)
    if field not in FIELDS:
        raise ValueError('Unsupported correction field')
    return _append(record, 'correction', actor,
                   {'field': field, 'from': state['fields'][field], 'to': value,
                    'reason': reason, 'evidence': {'source': source, 'line': line, 'quote': quote}},
                   expected_revision=expected_revision, timestamp=timestamp)


def decide(record, *, actor, decision, reason, expected_revision, timestamp=None):
    return _append(record, 'decision', actor, {'decision': decision, 'reason': reason},
                   expected_revision=expected_revision, timestamp=timestamp)

