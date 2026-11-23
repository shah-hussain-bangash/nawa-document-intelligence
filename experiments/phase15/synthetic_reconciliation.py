"""Classify two synthetic observations; makes no changes or authorization decisions."""
import re

_HASH = re.compile(r'[0-9a-f]{64}\Z')

def classify_snapshots(ledger, application):
    """Classify supplied snapshots; they may not be mutually consistent in time."""
    base = {'scope':'synthetic read-only classification; snapshots may be from different times',
            'automatic_action':'none'}
    if ledger is None or application is None:
        return {**base, 'status':'missing_observation', 'human_review_required':True}
    if not isinstance(ledger, dict) or not isinstance(application, dict):
        raise ValueError('Observations must be objects')
    ls, aps = ledger.get('state'), application.get('state')
    lh, ah = ledger.get('result_sha256'), application.get('result_sha256')
    if ls not in ('pending','consumed') or aps not in ('pending','completed'):
        return {**base, 'status':'invalid_observation', 'human_review_required':True}
    if ((ls == 'pending' and lh is not None) or (ls == 'consumed' and (not isinstance(lh,str) or not _HASH.fullmatch(lh)))
            or (aps == 'pending' and ah is not None) or (aps == 'completed' and (not isinstance(ah,str) or not _HASH.fullmatch(ah)))):
        return {**base, 'status':'invalid_observation', 'human_review_required':True}
    if ls == 'pending' and aps == 'pending':
        return {**base, 'status':'both_pending', 'human_review_required':True}
    if ls == 'consumed' and aps == 'pending':
        return {**base, 'status':'manual_reconciliation_required', 'human_review_required':True}
    if ls == 'consumed' and aps == 'completed' and lh == ah:
        return {**base, 'status':'observed_hashes_match', 'human_review_required':True}
    return {**base, 'status':'inconsistent_observations', 'human_review_required':True}
