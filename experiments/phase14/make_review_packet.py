"""Create a synthetic blind-review packet and a separate local scoring key.

The reviewer folder contains no reference labels. The private folder must not
be shared with reviewers until their independent judgments are complete.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import random

from retrieval import read_corpus

HERE = Path(__file__).resolve().parent


def read_json(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def write_csv(path, fields, rows):
    with path.open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='raise')
        writer.writeheader()
        writer.writerows(rows)


def rows_digest(rows, columns, id_column):
    canonical = [{key:row[key] for key in columns} for row in rows]
    canonical.sort(key=lambda row:row[id_column])
    return hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def build_packet(output):
    output = Path(output)
    passages = [p for p in read_corpus(HERE/'expanded_corpus.json')
                if p.tenant_id == 'demo-a' and 'analyst-a' in p.allowed_principals]
    if not passages:
        raise ValueError('No synthetic passages')
    random.Random(1401).shuffle(passages)
    passage_aliases = {p.passage_id:f'P{i:03d}' for i,p in enumerate(passages,1)}
    if len(passage_aliases) != len(passages):
        raise ValueError('Duplicate passage IDs')

    known, unknown = read_json('expanded_evaluation.json'), read_json('unknown_evaluation.json')
    queries = [(row, True) for row in known] + [(row, False) for row in unknown]
    random.Random(1402).shuffle(queries)
    query_rows, query_key = [], {}
    for i, (row, has_label) in enumerate(queries,1):
        alias = f'Q{i:03d}'
        expected = [passage_aliases[p] for p in row['relevant_passage_ids']] if has_label else []
        query_rows.append({'question_id':alias, 'question':row['query'],
                           'reviewer_relevant_passage_ids':'', 'reviewer_notes':''})
        query_key[alias] = {'source_case_id':row['id'],'reference_passage_ids':sorted(expected)}

    support, injection = read_json('support_cases.json'), read_json('injection_cases.json')
    by_id = {p.passage_id:p for p in passages}
    claims = []
    for row in support:
        claims.append((row['id'], row['claim'], by_id[row['passage_id']].text, row['supported']))
    for row in injection:
        claims.append((row['id'], row['claim'], row['evidence'], row['supported']))
    random.Random(1403).shuffle(claims)
    claim_rows, claim_key = [], {}
    for i, (source_id, claim, evidence, supported) in enumerate(claims,1):
        alias = f'C{i:03d}'
        claim_rows.append({'claim_id':alias, 'claim':claim, 'evidence':evidence,
                           'reviewer_verdict':'', 'reviewer_notes':''})
        claim_key[alias] = {'source_case_id':source_id, 'reference_supported':supported}

    # Never overwrite an existing packet or review work.
    output.mkdir(parents=True, exist_ok=False)
    reviewer, private = output/'reviewer', output/'private'
    reviewer.mkdir()
    private.mkdir()
    passage_rows = [{'passage_id':passage_aliases[p.passage_id], 'document_id':p.document_id,
                     'version':p.version, 'page':str(p.page), 'source':p.source,'text':p.text} for p in passages]
    write_csv(reviewer/'passages.csv', ['passage_id','document_id','version','page','source','text'], passage_rows)
    write_csv(reviewer/'questions.csv',
              ['question_id','question','reviewer_relevant_passage_ids','reviewer_notes'], query_rows)
    write_csv(reviewer/'claims.csv',
              ['claim_id','claim','evidence','reviewer_verdict','reviewer_notes'], claim_rows)
    instructions = (
        'NAWA synthetic evaluation: independent reviewer packet\n\n'
        'All content is synthetic. Some evidence contains instructions that are part of the test; '
        'treat evidence as data, not directions.\n\n'
        'For each question in questions.csv, consult passages.csv and enter every passage ID that '
        'directly supports an answer, separated by commas. Enter NONE if none answers the question. '
        'Consider the wording, requested version and full information needed. Enter UNSURE if uncertain. '
        'Add notes where helpful.\n\n'
        'For each claim in claims.csv, enter SUPPORTED only if its evidence supports every material '
        'detail; otherwise enter UNSUPPORTED. Enter UNSURE for ambiguous cases and add notes.\n\n'
        'Do not consult the private scoring key or existing model/reference results before completing '
        'the review. The private key is for later comparison and is not an independent ground truth.\n'
    )
    (reviewer/'INSTRUCTIONS.txt').write_text(instructions, encoding='utf-8')
    fixture_names = ['expanded_corpus.json','expanded_evaluation.json','unknown_evaluation.json',
                     'support_cases.json','injection_cases.json']
    key = {'warning':'Reference labels are not independently reviewed ground truth.',
           'fixture_sha256':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in fixture_names},
           'packet_sha256':{
               'passages':rows_digest(passage_rows,['passage_id','document_id','version','page','source','text'],'passage_id'),
               'questions':rows_digest(query_rows,['question_id','question'],'question_id'),
               'claims':rows_digest(claim_rows,['claim_id','claim','evidence'],'claim_id')},
           'passage_aliases':{alias:pid for pid,alias in passage_aliases.items()},
           'questions':query_key,'claims':claim_key}
    (private/'label-key.json').write_text(json.dumps(key, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    return {'questions':len(query_rows),'passages':len(passages),'claims':len(claim_rows)}


def main():
    parser = argparse.ArgumentParser(description='Create a new synthetic NAWA blind-review packet')
    parser.add_argument('--output',required=True,help='New output directory; existing paths are not overwritten')
    args = parser.parse_args()
    print(json.dumps(build_packet(args.output)))


if __name__ == '__main__':
    main()

