"""Seed or verify a synthetic record in an isolated Phase 11 QA deployment."""
import json
import sys
from urllib.request import Request, urlopen

ROOT = 'http://127.0.0.1:8765'


def call(path, payload=None):
    if payload is None:
        request = Request(ROOT + path)
    else:
        request = Request(ROOT + path, data=json.dumps(payload).encode('utf-8'),
                          headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('seed', 'verify'):
        raise SystemExit('Choose seed or verify')
    result = call('/api/quotations')
    if result['storage'] != 'postgres':
        raise SystemExit('PostgreSQL storage is not active')
    if sys.argv[1] == 'seed':
        if result['quotations']:
            raise SystemExit('QA database is not empty; inspect before seeding')
        row = call('/api/load-sample', {'name': 'english_quote.txt'})
        call('/api/review/start', {'id': row['id']})
        call('/api/review/decide', {'id': row['id'], 'actor': 'qa-reviewer',
             'reason': 'Synthetic restart check', 'decision': 'approve', 'expected_revision': 1})
        print('Synthetic quotation and approval saved in QA database.')
    else:
        matches = [x for x in result['quotations'] if x['quotation']['document'] == 'english_quote.txt']
        if len(matches) != 1:
            raise SystemExit('Expected one QA quotation')
        review = call('/api/review/show', {'id': matches[0]['id']})
        if review['status'] != 'approved' or review['revision'] != 2:
            raise SystemExit('QA review did not persist as expected')
        print('QA quotation and approved revision 2 are present.')


if __name__ == '__main__':
    main()
