"""Compare retrieval on newly authored synthetic questions, not reviewed labels."""
import json
from pathlib import Path
import statistics
import time

from benchmark import metrics
from compare_retrieval import authorized_vectors, cosine, embed, rrf, MODEL
from retrieval import BM25Index, read_corpus

HERE = Path(__file__).resolve().parent


def evaluate(passages, cases, embedding_fn):
    index = BM25Index(passages,tenant_id='demo-a',principal_id='analyst-a')
    allowed, vectors = authorized_vectors(passages,'demo-a','analyst-a',embedding_fn)
    allowed_ids = {p.passage_id for p in allowed}
    if len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Duplicate case ID')
    for case in cases:
        refs = set(case['relevant'])
        if (case['kind'] not in ('answerable','unanswerable')
                or case['language'] not in ('en','ar')
                or not refs <= allowed_ids
                or (case['kind'] == 'answerable') != bool(refs)):
            raise ValueError('Invalid synthetic evaluation label')
    query_vectors = embedding_fn([c['query'] for c in cases])
    if len(query_vectors) != len(cases):
        raise ValueError('Embedding count mismatch')
    rows=[]
    for case,qvector in zip(cases,query_vectors):
        bm = [r['passage_id'] for r in index.search(case['query'],k=100)]
        vector = [p.passage_id for _,p in sorted(
            ((cosine(qvector,v),p) for p,v in zip(allowed,vectors)),
            key=lambda row:(-row[0],row[1].passage_id))]
        rankings = {'bm25':bm,'vector':vector,'hybrid':rrf(bm,vector)}
        row={'id':case['id'],'language':case['language'],'kind':case['kind'],
             'reference_relevant_ids':case['relevant']}
        for name,ranking in rankings.items():
            if not set(ranking) <= allowed_ids:
                raise AssertionError('Unauthorized candidate')
            row[name]={'top5':ranking[:5]}
            if case['kind']=='answerable':
                recall,reciprocal_rank,ndcg=metrics(ranking,set(case['relevant']))
                row[name].update({'recall_at_5':recall,'reciprocal_rank_at_5':reciprocal_rank,
                                  'ndcg_at_5':ndcg})
        rows.append(row)
    summary={}
    for name in ('bm25','vector','hybrid'):
        answerable=[r for r in rows if r['kind']=='answerable']
        unknown=[r for r in rows if r['kind']=='unanswerable']
        summary[name]={'answerable_count':len(answerable),
                       'recall_at_5':statistics.mean(r[name]['recall_at_5'] for r in answerable),
                       'mrr_at_5':statistics.mean(r[name]['reciprocal_rank_at_5'] for r in answerable),
                       'ndcg_at_5':statistics.mean(r[name]['ndcg_at_5'] for r in answerable),
                       'unanswerable_count':len(unknown),
                       'unanswerable_with_candidates':sum(bool(r[name]['top5']) for r in unknown)}
    return {'case_count':len(rows),'authorized_passage_count':len(allowed),'methods':summary,'cases':rows}


def main():
    passages=read_corpus(HERE/'new_eval_corpus.json')
    cases=json.loads((HERE/'new_eval_cases.json').read_text(encoding='utf-8'))
    start=time.perf_counter()
    result=evaluate(passages,cases,embed)
    result.update({'model':MODEL,'elapsed_seconds_batch_single_run':round(time.perf_counter()-start,3),
                   'scope':'New hand-authored synthetic set; not independently reviewed.',
                   'warning':'Unanswerable candidates are retrieval results, not generated answers. Labels are preliminary.'})
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()

