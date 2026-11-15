"""Run: python -m nawa_demo.qa_cli --tenant demo-a --principal reviewer-a --question '...'"""
import argparse
import json
from pathlib import Path
from .grounded_qa import ask
from .retrieval import BM25Index, read_corpus


def main():
    parser = argparse.ArgumentParser(description='NAWA synthetic extractive, cited Q&A (no LLM)')
    parser.add_argument('--corpus', type=Path, default=Path('samples/retrieval/passages.json'))
    parser.add_argument('--tenant', required=True, help='Trusted tenant ID (CLI simulation only)')
    parser.add_argument('--principal', required=True, help='Trusted principal ID (CLI simulation only)')
    parser.add_argument('--question', required=True)
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--min-coverage', type=float, default=0.60)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        index = BM25Index(read_corpus(args.corpus), tenant_id=args.tenant, principal_id=args.principal)
        report = ask(index, args.question, top_k=args.top_k, min_coverage=args.min_coverage)
        rendered = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output is not None:
            args.output.write_text(rendered + '\n', encoding='utf-8')
        print(rendered)
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
