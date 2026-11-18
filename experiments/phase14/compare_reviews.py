"""Compare synthetic reviewer judgments; reference labels are not ground truth."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from make_review_packet import HERE, rows_digest


def csv_rows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def indexed(rows, name, expected):
    ids = [row[name] for row in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError('Review IDs do not match the packet')
    return {row[name]:row for row in rows}


def parse_question(value, permitted):
    value = value.strip().upper()
    if not value or value == 'UNSURE':
        return None
    if value == 'NONE':
        return frozenset()
    parts = [part.strip() for part in value.split(',')]
    if not all(parts) or len(parts) != len(set(parts)) or not set(parts) <= permitted:
        raise ValueError('Invalid passage selection')
    return frozenset(parts)


def parse_claim(value):
    value = value.strip().upper()
    if not value or value == 'UNSURE':
        return None
    if value not in ('SUPPORTED','UNSUPPORTED'):
        raise ValueError('Invalid claim verdict')
    return value == 'SUPPORTED'


def read_review(folder, key):
    folder = Path(folder)
    passages, questions, claims = (csv_rows(folder/name) for name in ('passages.csv','questions.csv','claims.csv'))
    indexed(passages, 'passage_id', key['passage_aliases'])
    q = indexed(questions, 'question_id', key['questions'])
    c = indexed(claims, 'claim_id', key['claims'])
    expected = key.get('packet_sha256')
    if expected is not None:
        actual = {
            'passages':rows_digest(passages,['passage_id','document_id','version','page','source','text'],'passage_id'),
            'questions':rows_digest(questions,['question_id','question'],'question_id'),
            'claims':rows_digest(claims,['claim_id','claim','evidence'],'claim_id')}
        if actual != expected:
            raise ValueError('Review packet content has changed')
    return {
        'integrity':'matched' if expected is not None else 'unverified_legacy_packet',
        'questions':{key_:parse_question(row['reviewer_relevant_passage_ids'],set(key['passage_aliases']))
                     for key_,row in q.items()},
        'claims':{key_:parse_claim(row['reviewer_verdict']) for key_,row in c.items()}}


def agreement(left, right):
    compared = [key for key in left if left[key] is not None and right[key] is not None]
    disagreements = sorted(key for key in compared if left[key] != right[key])
    return {'compared':len(compared),'agreement_count':len(compared)-len(disagreements),
            'disagreement_ids':disagreements,
            'not_compared':len(left)-len(compared)}


def compare(key_path, folders):
    if not 1 <= len(folders) <= 2:
        raise ValueError('Provide one or two independent reviewer folders')
    key = json.loads(Path(key_path).read_text(encoding='utf-8'))
    for name,expected in key['fixture_sha256'].items():
        if Path(name).name != name or hashlib.sha256((HERE/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Reference fixture changed')
    reviews = [read_review(folder,key) for folder in folders]
    references = {'questions':{id_:frozenset(row['reference_passage_ids']) for id_,row in key['questions'].items()},
                  'claims':{id_:row['reference_supported'] for id_,row in key['claims'].items()}}
    summary = {'warning':'Reference labels are not ground truth; resolve disagreements by independent adjudication.',
               'reviewers':[]}
    for review in reviews:
        summary['reviewers'].append({'packet_integrity':review['integrity'],
            'questions_vs_reference':agreement(review['questions'],references['questions']),
            'claims_vs_reference':agreement(review['claims'],references['claims'])})
    if len(reviews) == 2:
        summary['between_reviewers'] = {
            name:agreement(reviews[0][name],reviews[1][name]) for name in ('questions','claims')}
    return summary


def main():
    parser = argparse.ArgumentParser(description='Compare completed synthetic reviewer judgments')
    parser.add_argument('--key',required=True)
    parser.add_argument('--reviewer',action='append',required=True)
    args = parser.parse_args()
    print(json.dumps(compare(args.key,args.reviewer),indent=2))


if __name__ == '__main__':
    main()

