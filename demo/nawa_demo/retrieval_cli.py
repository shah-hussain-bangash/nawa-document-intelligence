"""CLI entry: python -m nawa_demo.retrieval_cli search/evaluate ..."""
import argparse
import json
from pathlib import Path
from .retrieval import BM25Index, read_corpus


def evaluate(corpus: Path, cases: Path) -> dict:
    scenarios=json.loads(Path(cases).read_text(encoding='utf-8'))
    if not isinstance(scenarios,list) or not scenarios:
        raise ValueError('Evaluation set must be a nonempty JSON array')
    passages=read_corpus(corpus)
    output=[]
    for row in scenarios:
        expected={'query','tenant_id','principal_id','relevant_passage_ids'}
        if not expected.issubset(row) or not isinstance(row['relevant_passage_ids'],list) or not row['relevant_passage_ids']:
            raise ValueError('Evaluation case missing query, authorized identity or relevant IDs')
        idx=BM25Index(passages,tenant_id=row['tenant_id'],principal_id=row['principal_id'])
        relevant=set(row['relevant_passage_ids'])
        authorized={p.passage_id for p in idx.passages}
        if not relevant <= authorized:
            raise ValueError('Evaluation relevance set contains nonexistent or unauthorized passages')
        retrieved=[hit['passage_id'] for hit in idx.search(row['query'],k=5)]
        recall=len(relevant.intersection(retrieved))/len(relevant)
        output.append({'query':row['query'],'recall_at_5':recall,'retrieved_ids':retrieved,'relevant_ids':sorted(relevant)})
    return {'metric':'macro_recall_at_5','score':sum(x['recall_at_5'] for x in output)/len(output),
            'case_count':len(output),'cases':output,'scope':'Synthetic labeled data; no LLM and no retrieval quality claim on real quotations'}


def main():
    parser=argparse.ArgumentParser(description='NAWA synthetic BM25 retrieval (not generative RAG)')
    commands=parser.add_subparsers(dest='command',required=True)
    search=commands.add_parser('search')
    search.add_argument('--corpus',type=Path,default=Path('samples/retrieval/passages.json'))
    search.add_argument('--tenant',required=True)
    search.add_argument('--principal',required=True)
    search.add_argument('--query',required=True)
    search.add_argument('--top-k',type=int,default=5)
    evaluation=commands.add_parser('evaluate')
    evaluation.add_argument('--corpus',type=Path,default=Path('samples/retrieval/passages.json'))
    evaluation.add_argument('--cases',type=Path,default=Path('samples/retrieval/evaluation.json'))
    args=parser.parse_args()
    try:
        if args.command=='search':
            idx=BM25Index(read_corpus(args.corpus),tenant_id=args.tenant,principal_id=args.principal)
            output={'query':args.query,'tenant_id':args.tenant,'principal_id':args.principal,
                    'results':idx.search(args.query,k=args.top_k)}
        else:
            output=evaluate(args.corpus,args.cases)
        print(json.dumps(output,ensure_ascii=False,indent=2))
    except (OSError,ValueError) as exc:
        parser.exit(2,f'Error: {exc}\n')

if __name__=='__main__':
    main()
