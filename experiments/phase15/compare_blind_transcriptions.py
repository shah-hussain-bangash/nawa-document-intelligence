"""Compare synthetic human transcriptions; not identity verification or approval."""
import argparse
import hashlib
import json
from pathlib import Path

import ocr_benchmark as bench
from blind_synthetic_review import FIELDS
from synthetic_arabic_batch_experiment import IMAGE_SHA256, MANIFEST_SHA256

MAX_INPUT = 65536
NUMERIC = frozenset({'subtotal', 'vat_rate', 'vat_amount', 'total'})


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def read_json(path):
    with Path(path).open('rb') as stream:
        data = stream.read(MAX_INPUT + 1)
    if len(data) > MAX_INPUT:
        raise ValueError('Synthetic review file exceeds size limit')
    return json.loads(data.decode('utf-8-sig'), object_pairs_hook=_unique_object)


def compare_review(review, manifest):
    """Return field statuses only; no identity, source truth, or approval assertion."""
    if (not isinstance(review, dict) or set(review) != {'status', 'promotable', 'scope', 'cases'}
            or review['status'] != 'awaiting_human_transcription' or review['promotable'] is not False
            or review['scope'] != 'Synthetic pages only; no reviewer authentication or approval.'
            or not isinstance(review['cases'], list) or len(review['cases']) != 2):
        raise ValueError('Invalid synthetic review format')
    if not isinstance(manifest, dict) or not isinstance(manifest.get('cases'), list):
        raise ValueError('Invalid synthetic fixture manifest')
    expected = {case['id']:case for case in manifest['cases']}
    if set(expected) != {'synthetic-a', 'synthetic-b'}:
        raise ValueError('Invalid synthetic fixture set')
    rows, seen = [], set()
    for case in review['cases']:
        if not isinstance(case, dict) or set(case) != {'case', 'image', 'image_sha256', 'transcriptions'}:
            raise ValueError('Invalid synthetic review case')
        identifier = case['case']
        if not isinstance(identifier, str) or identifier not in expected or identifier in seen:
            raise ValueError('Invalid synthetic review case')
        seen.add(identifier)
        original = expected[identifier]
        if (case['image'] != original['image'] or case['image_sha256'] != IMAGE_SHA256.get(case['image'])
                or original['sha256'] != IMAGE_SHA256.get(case['image'])):
            raise ValueError('Synthetic source identity mismatch')
        answers = case['transcriptions']
        if not isinstance(answers, dict) or set(answers) != set(FIELDS):
            raise ValueError('Invalid synthetic transcription fields')
        statuses = {}
        for field in FIELDS:
            value = answers[field]
            if not isinstance(value, str) or len(value) > 120:
                raise ValueError('Invalid synthetic transcription')
            if not value.strip():
                statuses[field] = 'not_transcribed'
            elif value.strip().casefold() in {'unclear', 'غير واضح'}:
                statuses[field] = 'reviewer_marked_unclear'
            else:
                actual = bench.comparison_value(field, value)
                reference = bench.comparison_value(field, original['fields'][field])
                if field in NUMERIC and actual is None:
                    statuses[field] = 'numeric_format_uncomparable'
                elif actual == reference and reference is not None:
                    statuses[field] = 'matches_fixture'
                else:
                    statuses[field] = 'differs_from_fixture'
        rows.append({'case':identifier, 'fields':statuses})
    return {'status':'human_review_required', 'promotable':False, 'cases':rows,
            'scope':'Synthetic normalized comparison only; reviewer identity and independence are not verified.'}


def main():
    parser = argparse.ArgumentParser(description='Compare a synthetic transcription with pinned fixture values')
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--fixture-manifest', type=Path, required=True)
    args = parser.parse_args()
    manifest_bytes = args.fixture_manifest.read_bytes()
    if len(manifest_bytes) > MAX_INPUT or hashlib.sha256(manifest_bytes).hexdigest() != MANIFEST_SHA256:
        raise ValueError('Synthetic fixture manifest hash mismatch')
    manifest = json.loads(manifest_bytes.decode('utf-8'), object_pairs_hook=_unique_object)
    print(json.dumps(compare_review(read_json(args.review), manifest), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
