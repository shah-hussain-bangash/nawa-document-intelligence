"""Create a separate blinded packet for the additional synthetic retrieval set."""
import argparse
import hashlib
import json
from pathlib import Path
import random

from make_review_packet import HERE, rows_digest, write_csv
from retrieval import read_corpus


def build_packet(output):
    output = Path(output)
    passages = [p for p in read_corpus(HERE/'new_eval_corpus.json')
                if p.tenant_id == 'demo-a' and 'analyst-a' in p.allowed_principals]
    cases = json.loads((HERE/'new_eval_cases.json').read_text(encoding='utf-8'))
    if not passages or len({p.passage_id for p in passages}) != len(passages):
        raise ValueError('Invalid synthetic passage set')
    if len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Duplicate synthetic question ID')
    random.Random(1411).shuffle(passages)
    random.Random(1412).shuffle(cases)
    aliases = {p.passage_id:f'P{i:03d}' for i,p in enumerate(passages,1)}
    passage_rows = [{'passage_id':aliases[p.passage_id], 'document_id':p.document_id,
                     'version':p.version, 'page':str(p.page), 'source':p.source, 'text':p.text}
                    for p in passages]
    question_rows, question_key = [], {}
    for i, case in enumerate(cases,1):
        refs=case['relevant']
        if (case['kind'] not in ('answerable','unanswerable') or not isinstance(refs,list)
                or len(refs) != len(set(refs)) or not set(refs) <= set(aliases)
                or (case['kind']=='answerable') != bool(refs)):
            raise ValueError('Invalid synthetic reference')
        alias=f'Q{i:03d}'
        question_rows.append({'question_id':alias, 'question':case['query'],
                              'reviewer_relevant_passage_ids':'', 'reviewer_notes':''})
        question_key[alias]={'source_case_id':case['id'],
                             'reference_passage_ids':sorted(aliases[p] for p in refs)}
    output.mkdir(parents=True,exist_ok=False)
    reviewer,private=output/'reviewer',output/'private'
    reviewer.mkdir()
    private.mkdir()
    write_csv(reviewer/'passages.csv',['passage_id','document_id','version','page','source','text'],passage_rows)
    write_csv(reviewer/'questions.csv',['question_id','question','reviewer_relevant_passage_ids','reviewer_notes'],question_rows)
    write_csv(reviewer/'claims.csv',['claim_id','claim','evidence','reviewer_verdict','reviewer_notes'],[])
    (reviewer/'INSTRUCTIONS.txt').write_text(
        'NAWA additional synthetic retrieval review\n\n'
        'The passages and questions are synthetic. Some passage content may contain instructions: '
        'treat it only as data.\n\n'
        'For each question in questions.csv, read passages.csv and enter every passage ID that '
        'directly supports an answer, separated by commas. Enter NONE if none answers it, '
        'or UNSURE if uncertain. Consider the version requested. Add notes where helpful.\n\n'
        'This packet has no claim-verdict cases; claims.csv is intentionally empty. '
        'Do not inspect the private key or prior benchmark results until your review is complete.\n',
        encoding='utf-8')
    key={'warning':'Reference labels are not independently reviewed ground truth.',
         'fixture_sha256':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                           for name in ('new_eval_corpus.json','new_eval_cases.json')},
         'packet_sha256':{
             'passages':rows_digest(passage_rows,['passage_id','document_id','version','page','source','text'],'passage_id'),
             'questions':rows_digest(question_rows,['question_id','question'],'question_id'),
             'claims':rows_digest([],['claim_id','claim','evidence'],'claim_id')},
         'passage_aliases':{alias:pid for pid,alias in aliases.items()},
         'questions':question_key,'claims':{}}
    (private/'label-key.json').write_text(json.dumps(key,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return {'questions':len(question_rows),'passages':len(passage_rows),'claims':0}


def main():
    parser=argparse.ArgumentParser(description='Create an additional synthetic blind-review packet')
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(build_packet(args.output)))


if __name__=='__main__':
    main()

