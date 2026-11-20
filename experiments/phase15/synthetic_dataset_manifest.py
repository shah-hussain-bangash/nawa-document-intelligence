"""Validate experimental synthetic OCR dataset metadata, not its truth or accuracy."""
import hashlib
import re

_ID = re.compile(r'[a-z0-9][a-z0-9_-]{0,63}\Z')
_SHA = re.compile(r'[0-9a-f]{64}\Z')
_SPLITS = frozenset({'development', 'evaluation'})
_LANGUAGES = frozenset({'ar', 'en'})


def validate_manifest(manifest):
    """Fail closed on invalid metadata and source leakage; perform no file I/O.

    Reviewer and license fields are self-declared identifiers, not proof of
    independent review, licensing, representativeness or production quality.
    """
    if not isinstance(manifest, dict) or set(manifest) != {'scope', 'samples'}:
        raise ValueError('Invalid synthetic dataset manifest')
    if manifest['scope'] != 'synthetic-only' or not isinstance(manifest['samples'], list) or not manifest['samples']:
        raise ValueError('A nonempty synthetic-only dataset is required')
    sources, hashes, ids = {}, {}, set()
    fields = {'sample_id', 'source_id', 'content_sha256', 'split', 'language',
              'creator_id', 'reviewer_id', 'license_ref'}
    for sample in manifest['samples']:
        if not isinstance(sample, dict) or set(sample) != fields:
            raise ValueError('Invalid synthetic sample metadata')
        for name in ('sample_id', 'source_id', 'creator_id', 'reviewer_id', 'license_ref'):
            if not isinstance(sample[name], str) or not _ID.fullmatch(sample[name]):
                raise ValueError('Invalid synthetic sample identifier')
        digest = sample['content_sha256']
        if not isinstance(digest, str) or not _SHA.fullmatch(digest):
            raise ValueError('Invalid sample content hash')
        if (not isinstance(sample['split'], str) or sample['split'] not in _SPLITS or
                not isinstance(sample['language'], str) or sample['language'] not in _LANGUAGES):
            raise ValueError('Invalid sample split or language')
        if sample['creator_id'] == sample['reviewer_id']:
            raise ValueError('A different reviewer identifier is required')
        if sample['sample_id'] in ids:
            raise ValueError('Duplicate sample identifier')
        ids.add(sample['sample_id'])
        for seen, key in ((sources, sample['source_id']), (hashes, digest)):
            if key in seen and seen[key] != sample['split']:
                raise ValueError('Source or content occurs across splits')
            seen[key] = sample['split']
    return {'status': 'metadata_valid_only', 'sample_count': len(ids),
            'human_review_required': True}


def verify_sample_bytes(manifest, sample_bytes):
    """Check caller-supplied synthetic bytes; do not load files or run OCR."""
    validate_manifest(manifest)
    expected = {sample['sample_id']: sample['content_sha256']
                for sample in manifest['samples']}
    if not isinstance(sample_bytes, dict) or sample_bytes.keys() != expected.keys():
        raise ValueError('Synthetic sample set does not match manifest')
    for sample_id, expected_digest in expected.items():
        data = sample_bytes[sample_id]
        if not isinstance(data, bytes) or not 0 < len(data) <= 16 * 1024 * 1024:
            raise ValueError('Invalid synthetic sample bytes')
        if hashlib.sha256(data).hexdigest() != expected_digest:
            raise ValueError('Synthetic sample hash mismatch')
    return {'status': 'sample_hashes_match', 'sample_count': len(expected),
            'human_review_required': True}
