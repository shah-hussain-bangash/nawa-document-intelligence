"""Phase 6 CLI, synthetic data. Run from demo/; provider mock is offline."""
import argparse
import json
from pathlib import Path

from .rag import MockProvider, OpenAIProvider, ask_rag
from .retrieval import BM25Index, read_corpus


def main():
    parser = argparse.ArgumentParser(description='NAWA Phase 6 cited RAG demo (synthetic documents)')
    parser.add_argument('--corpus', type=Path, default=Path('samples/retrieval/passages.json'))
    parser.add_argument('--tenant', required=True, help='Self-asserted identity: DEMO ONLY')
    parser.add_argument('--principal', required=True, help='Self-asserted identity: DEMO ONLY')
    parser.add_argument('--question', required=True)
    parser.add_argument('--provider', choices=('mock', 'openai'), default='mock')
    parser.add_argument('--model', default='gpt-4.1-mini')
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        index = BM25Index(read_corpus(args.corpus), tenant_id=args.tenant,
                          principal_id=args.principal)
        provider = MockProvider() if args.provider == 'mock' else OpenAIProvider(model=args.model)
        report = ask_rag(index, args.question, provider=provider, top_k=args.top_k)
        report['provider'] = args.provider
        rendered = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            args.output.write_text(rendered + '\n', encoding='utf-8')
        print(rendered)
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
