"""Inspect event hash links in an already-loaded synthetic review ledger.

This does not replay the ledger, authenticate it, or establish its correctness.
"""
from .review import _digest


def inspect_event_links(ledger):
    """Check event hashes and ordering without interpreting financial values.

    The returned result is a narrow integrity signal only. The outer document
    name is not covered by event hashes. Human review is always required.
    """
    result = {'event_links_match': False, 'events_examined': 0,
              'reason': 'invalid_ledger', 'human_review_required': True,
              'scope': 'Synthetic event links only; no authenticity, replay, or approval.'}
    if (not isinstance(ledger, dict) or set(ledger) != {'schema', 'document', 'events'}
            or ledger['schema'] != 'nawa-review-v1'
            or not isinstance(ledger['document'], str) or not ledger['document'].strip()):
        return result
    events = ledger['events']
    if not isinstance(events, list) or not 1 <= len(events) <= 1000:
        return result
    previous = 'GENESIS'
    required = {'sequence', 'type', 'actor', 'timestamp', 'data', 'previous_hash', 'hash'}
    for index, event in enumerate(events, 1):
        if (not isinstance(event, dict) or set(event) != required
                or type(event['sequence']) is not int or event['sequence'] != index
                or event['previous_hash'] != previous or not isinstance(event['hash'], str)):
            result['reason'] = 'invalid_event_link'
            return result
        try:
            matches = event['hash'] == _digest(event)
        except (TypeError, ValueError, OverflowError, RecursionError):
            result['reason'] = 'invalid_event_encoding'
            return result
        result['events_examined'] = index
        if not matches:
            result['reason'] = 'event_hash_mismatch'
            return result
        previous = event['hash']
    result['event_links_match'] = True
    result['reason'] = 'links_match_review_still_required'
    return result
