"""Offline evaluation: python -m nawa_demo.eval_cli [--output path]"""
import argparse
import json
from pathlib import Path
from .evaluation import evaluate


def main():
    parser = argparse.ArgumentParser(description='NAWA Phase 7 synthetic RAG evaluation')
    parser.add_argument('--corpus', type=Path, default=Path('samples/retrieval/passages.json'))
    parser.add_argument('--cases', type=Path, default=Path('samples/evaluation/phase7_cases.json'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(args.corpus, args.cases)
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.output:
            args.output.write_text(rendered, encoding='utf-8')
        print(rendered, end='')
        if not result['all_passed']:
            parser.exit(1)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
