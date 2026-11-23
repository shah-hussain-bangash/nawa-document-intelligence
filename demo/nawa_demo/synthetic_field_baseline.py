"""Replay three fixed synthetic text fixtures against draft labels only."""
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .core import extract
from .synthetic_field_metrics import FIELDS, score_cases

_SOURCE_HASHES = {
    'english_quote.txt':'13c5a4d9f2695877afdc2a19b0fb803cb7acee06a24fb19d625390b73e2e9f02',
    'arabic_quote.txt':'fdf488846d40ce360f90e64e0c86825fe16112d55f25339c9ad44a64cf560ac8',
    'incorrect_vat_quote.txt':'123ceccb907cdf30025c3bfbf1f2dc8df84a22104b6368660039f9c162de1a16',
}
_CHECKS = {'vat_matches_rate', 'total_matches_components'}


def evaluate_fixture(samples, fixture):
    if (not isinstance(fixture, dict) or set(fixture) != {'scope','normalization_policy','cases'}
            or not isinstance(fixture['scope'], str) or not isinstance(fixture['cases'], list)
            or len(fixture['cases']) != 3):
        raise ValueError('Invalid draft fixture')
    samples = Path(samples).resolve()
    source_ids, cases, checks = set(), [], []
    for item in fixture['cases']:
        if (not isinstance(item, dict) or set(item) != {'id','language','source','label_status','expected','expected_checks'}
                or not isinstance(item['source'], str) or item['source'] not in _SOURCE_HASHES
                or item['source'] in source_ids or item['label_status'] != 'draft'
                or not isinstance(item['expected_checks'], dict) or set(item['expected_checks']) != _CHECKS
                or not all(type(value) is bool for value in item['expected_checks'].values())):
            raise ValueError('Invalid draft fixture')
        source_ids.add(item['source'])
        path = samples / item['source']
        if path.is_symlink() or path.resolve().parent != samples:
            raise ValueError('Synthetic source unavailable')
        try:
            content = path.read_bytes().replace(b'\r\n', b'\n')
        except OSError:
            raise ValueError('Synthetic source unavailable') from None
        if hashlib.sha256(content).hexdigest() != _SOURCE_HASHES[item['source']]:
            raise ValueError('Synthetic source does not match the fixed fixture')
        with TemporaryDirectory(prefix='nawa-field-baseline-') as folder:
            checked = Path(folder) / item['source']
            checked.write_bytes(content)
            result = extract(checked)
        predicted = {field:result.get('vat_rate_percent' if field == 'vat_rate' else field) for field in FIELDS}
        cases.append({'id':item['id'], 'language':item['language'], 'source_type':'synthetic',
                      'label_status':item['label_status'], 'expected':item['expected'], 'predicted':predicted})
        checks.append({'id':item['id'], 'observed':result['checks'],
                       'matches_draft':result['checks'] == item['expected_checks']})
    report = score_cases(cases, normalization_policy=fixture['normalization_policy'])
    report.update({'scope':'Three fixed synthetic text fixtures with draft labels; not an independent benchmark.',
                   'development_only':True, 'arithmetic_checks':checks})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=Path, default=Path(__file__).resolve().parents[1] / 'samples')
    args = parser.parse_args()
    fixture = json.loads((args.samples / 'evaluation/draft_field_review.json').read_text(encoding='utf-8'))
    print(json.dumps(evaluate_fixture(args.samples, fixture), ensure_ascii=True, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
