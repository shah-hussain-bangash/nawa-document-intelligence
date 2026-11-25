"""Repeatable synthetic retrieval/abstention and OCR-field evaluation.

Developer-authored draft fixtures are not independent, held-out ground truth.
Low scores remain failures in the report; this command never fabricates sign-off.
"""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from uae_ai.core.config import Settings
from uae_ai.core.security import readable_documents
from uae_ai.db import Base, User, make_database
from uae_ai.domain.extraction import extract_quotation
from uae_ai.rag.parser import parse
from uae_ai.rag.retrieval import search
from uae_ai.rag.embeddings import retrieval_profile
from uae_ai.seed import seed

ROOT=Path(__file__).resolve().parents[1]


def evaluate(settings, progress=None):
    suite=json.loads((ROOT/'evals/knowledge-100.json').read_text(encoding='utf-8-sig'))
    rows=[]
    with TemporaryDirectory(prefix='nawa-quality-') as directory:
        local=replace(settings,app_env='test',auth_mode='demo',seed_demo=True,data_dir=Path(directory),database_url=f'sqlite:///{Path(directory).as_posix()}/quality.db')
        local.validate();engine,factory=make_database(local.database_url)
        try:
            Base.metadata.create_all(engine)
            with factory() as db:
                seed(db,local)
                sources=readable_documents(db,db.get(User,'operations-analyst'))
                for index, question in enumerate(suite['questions'], 1):
                    result=search(question['question'],sources,question.get('domain','all'),local)
                    titles=[row['title'] for row in result]
                    target=question['expected_title']
                    rank=titles.index(target)+1 if target in titles else None
                    rows.append({'id':question['id'],'language':question['language'],'expected_title':target,'retrieved_titles':titles,'passed':not titles if target is None else rank is not None,'reciprocal_rank':1/rank if rank else 0})
                    if progress is not None and index % 10 == 0:
                        progress(index, len(suite['questions']))
        finally:
            # Release SQLite handles before TemporaryDirectory cleanup on Windows,
            # including when the embedding endpoint/search raises an exception.
            engine.dispose()
    positives=[row for row in rows if row['expected_title'] is not None]
    negatives=[row for row in rows if row['expected_title'] is None]
    ocr=[]
    expected={'supplier':'Example Services','amount':'12500.00','currency':'AED','tax_percent':'5.00','delivery_days':'14','valid_until':'2027-12-31'}
    for language in ['en','ar']:
        path=ROOT/f'data/samples/scanned-quotation-{language}.pdf'
        parsed=parse(path,ocr_mode=settings.ocr_mode,languages=settings.ocr_languages,max_ocr_pages=settings.ocr_max_pages)
        fields=extract_quotation(SimpleNamespace(id='fixture',title=path.name,version=1,content_hash=hashlib.sha256(path.read_bytes()).hexdigest(),pages=parsed['pages']))['fields']
        target={**expected,'supplier':'شركة تجريبية'} if language=='ar' else expected
        correct=sum(fields[key]['value']==value for key,value in target.items())
        predicted=sum(field['value'] is not None for field in fields.values())
        ocr.append({'language':language,'status':parsed['status'],'correct_fields':correct,'expected_fields':6,'predicted_fields':predicted,'precision':correct/max(1,predicted),'recall':correct/6,'f1':2*correct/max(1,predicted+6),'methods':[p.get('method') for p in parsed['pages']]})
    return {'scope':suite['notice'],'retrieval_mode':settings.retrieval_mode,'questions':len(rows),'recall_at_4':sum(row['passed'] for row in positives)/max(1,len(positives)),'mean_reciprocal_rank':sum(row['reciprocal_rank'] for row in positives)/max(1,len(positives)),'unanswerable_abstention_rate':sum(row['passed'] for row in negatives)/max(1,len(negatives)),'abstention_scope':'Retrieval candidate emptiness on unsupported questions; final-answer field grounding is not evaluated by this metric.','ocr_labelled_field_results':ocr,'results':rows,'independently_reviewed':False,'production_accepted':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='artifacts/quality-report.json')
    args=parser.parse_args()
    settings=Settings()
    print('Retrieval mode:',settings.retrieval_mode,flush=True)
    print('Retrieval profile:',json.dumps(retrieval_profile(settings),ensure_ascii=True),flush=True)
    report=evaluate(settings,progress=lambda done,total:print(f'Questions processed: {done}/{total}',flush=True))
    report['retrieval_profile']=retrieval_profile(settings)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Draft retrieval Recall@4:',round(report['recall_at_4'],3),'candidate-empty rate:',round(report['unanswerable_abstention_rate'],3))
    print('Draft OCR field F1:',[(item['language'],round(item['f1'],3)) for item in report['ocr_labelled_field_results']])
    print('Independent review and production acceptance remain pending. Report:',path)
