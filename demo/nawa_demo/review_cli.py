"""Local-only review CLI. Run `python -m nawa_demo.review_cli --help`."""
import argparse
import json
from pathlib import Path
import sys

from .core import extract
from .pdf_ingest import extract_pdf
from .review import begin, correct, decide, inspect


def _load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def _save_new(path, data):
    # Never overwrite a preexisting ledger from init.
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def _save_update(path, data):
    # Local demo only. No cross-process lock or durable transactional database.
    import os
    import tempfile
    fd, temp = tempfile.mkstemp(prefix='.nawa-review-', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def main():
    p = argparse.ArgumentParser(description='NAWA Phase 8 synthetic local review (not authentication)')
    commands = p.add_subparsers(dest='command', required=True)
    new = commands.add_parser('init')
    new.add_argument('--quotation', type=Path, required=True)
    new.add_argument('--ledger', type=Path, required=True)
    show = commands.add_parser('show')
    show.add_argument('--ledger', type=Path, required=True)
    correction = commands.add_parser('correct')
    correction.add_argument('--ledger', type=Path, required=True)
    correction.add_argument('--actor', required=True)
    correction.add_argument('--field', required=True)
    correction.add_argument('--value', required=True)
    correction.add_argument('--reason', required=True)
    correction.add_argument('--source', required=True)
    correction.add_argument('--line', required=True, type=int)
    correction.add_argument('--quote', required=True)
    correction.add_argument('--expected-revision', required=True, type=int)
    decision = commands.add_parser('decide')
    decision.add_argument('--ledger', type=Path, required=True)
    decision.add_argument('--actor', required=True)
    decision.add_argument('--decision', choices=('approve','reject','request_changes'), required=True)
    decision.add_argument('--reason', required=True)
    decision.add_argument('--expected-revision', required=True, type=int)
    args = p.parse_args()
    try:
        if args.command == 'init':
            q = extract_pdf(args.quotation) if args.quotation.suffix.lower() == '.pdf' else extract(args.quotation)
            record = begin(q)
            _save_new(args.ledger, record)
            state = inspect(record)
        elif args.command == 'show':
            state = inspect(_load(args.ledger))
        else:
            record = _load(args.ledger)
            if args.command == 'correct':
                updated = correct(record, actor=args.actor, field=args.field, value=args.value,
                                  reason=args.reason, source=args.source, line=args.line, quote=args.quote,
                                  expected_revision=args.expected_revision)
            else:
                updated = decide(record, actor=args.actor, decision=args.decision, reason=args.reason,
                                 expected_revision=args.expected_revision)
            _save_update(args.ledger, updated)
            state = inspect(updated)
        print(json.dumps(state, ensure_ascii=False, indent=2))
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
        p.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
