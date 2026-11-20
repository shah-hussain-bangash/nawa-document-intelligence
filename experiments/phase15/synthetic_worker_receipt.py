"""Synthetic HMAC receipt experiment; not integrated or production security."""
import hashlib
import hmac
import json
import re

DOMAIN = b'nawa-synthetic-worker-receipt-v1\x00'
MAX_RESULT_BYTES = 2 * 1024 * 1024
_HASH = re.compile(r'[0-9a-f]{64}\Z')
_ID = re.compile(r'[0-9a-f]{32}\Z')
_KEY_ID = re.compile(r'[a-zA-Z0-9_-]{1,32}\Z')

def _payload(*, tenant, document_id, job_id, source_sha256, result, key_id):
    if not isinstance(tenant, str) or not tenant or len(tenant) > 100:
        raise ValueError('Invalid tenant')
    if not isinstance(document_id, str) or not _ID.fullmatch(document_id):
        raise ValueError('Invalid document ID')
    if not isinstance(job_id, str) or not _ID.fullmatch(job_id):
        raise ValueError('Invalid job ID')
    if not isinstance(source_sha256, str) or not _HASH.fullmatch(source_sha256):
        raise ValueError('Invalid source hash')
    if not isinstance(key_id, str) or not _KEY_ID.fullmatch(key_id):
        raise ValueError('Invalid key identifier')
    if not isinstance(result, dict) or result.get('extraction_origin') != 'synthetic_text_worker_v1':
        raise ValueError('Unsupported synthetic result')
    # Python-only serialization experiment, not a cross-language canonical JSON standard.
    encoded = json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(',', ':'),
                         allow_nan=False).encode('utf-8')
    if len(encoded) > MAX_RESULT_BYTES:
        raise ValueError('Result too large')
    return {'version':1, 'tenant':tenant, 'document_id':document_id, 'job_id':job_id,
            'source_sha256':source_sha256, 'result_sha256':hashlib.sha256(encoded).hexdigest(),
            'origin':'synthetic_text_worker_v1', 'key_id':key_id}

def _mac(key, payload):
    if not isinstance(key, bytes) or len(key) < 32:
        raise ValueError('A synthetic test key of at least 32 bytes is required')
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hmac.new(key, DOMAIN + encoded, hashlib.sha256).hexdigest()

def issue_receipt(key, *, tenant, document_id, job_id, source_sha256, result, key_id):
    payload = _payload(tenant=tenant, document_id=document_id, job_id=job_id,
                       source_sha256=source_sha256, result=result, key_id=key_id)
    return {'payload':payload, 'mac_sha256':_mac(key, payload)}

def verify_receipt(receipt, key, *, tenant, document_id, job_id, source_sha256, result, key_id):
    try:
        expected = _payload(tenant=tenant, document_id=document_id, job_id=job_id,
                            source_sha256=source_sha256, result=result, key_id=key_id)
        if not isinstance(receipt, dict) or set(receipt) != {'payload','mac_sha256'}:
            return False
        supplied = receipt['mac_sha256']
        if not isinstance(receipt['payload'], dict) or not isinstance(supplied, str) or not _HASH.fullmatch(supplied):
            return False
        actual_bytes = json.dumps(receipt['payload'], sort_keys=True, ensure_ascii=False,
                                  separators=(',', ':'), allow_nan=False).encode('utf-8')
        expected_bytes = json.dumps(expected, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode('utf-8')
        if len(actual_bytes) > 4096 or not hmac.compare_digest(actual_bytes, expected_bytes):
            return False
        return hmac.compare_digest(supplied, _mac(key, expected))
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return False
