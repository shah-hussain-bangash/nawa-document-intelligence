from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import sys
import argparse

parser = argparse.ArgumentParser(description='Reproduce selected NAWA synthetic case-study checks')
parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[3])
parser.add_argument('--output', type=Path)
args = parser.parse_args()
root = args.repo.resolve()
from historical_input_guard import verify_recorded_inputs
try:
    evidence_file = Path(__file__).resolve().parent / 'nawa-synthetic-checks-2026-11-21.json'
    evidence = json.loads(evidence_file.read_text(encoding='utf-8'))
    verify_recorded_inputs(root, evidence)
except (OSError, ValueError) as exc:
    parser.error(str(exc) + '; use the recorded baseline files at commit 823565f')
sys.path.insert(0, str(root / 'demo'))
from nawa_demo.core import extract, compare
from nawa_demo.review import begin, decide, inspect
from nawa_demo.rag import validate_generated
from nawa_demo.evaluation import evaluate

samples = root / 'demo/samples'
quotes = [extract(samples / name) for name in ['english_quote.txt', 'arabic_quote.txt', 'incorrect_vat_quote.txt']]
evaluation = evaluate(samples/'retrieval/passages.json', samples/'evaluation/phase7_cases.json')
bad = begin(quotes[2])
blocked = False
try:
    decide(bad, actor='synthetic-reviewer', decision='approve', reason='Synthetic check', expected_revision=1)
except ValueError as exc:
    blocked = 'financial mismatches' in str(exc)
good = begin(quotes[0])
decided = decide(good, actor='synthetic-reviewer', decision='approve', reason='Synthetic evidence inspected', expected_revision=1)
stale_blocked = False
try:
    decide(decided, actor='synthetic-reviewer', decision='request_changes', reason='Stale revision check', expected_revision=1)
except ValueError as exc:
    stale_blocked = 'Stale revision' in str(exc)
passage = json.loads((samples/'retrieval/passages.json').read_text(encoding='utf-8'))[0]
counterexample = {'answer':'Subtotal AED 1050.00', 'citations':[{'passage_id':passage['passage_id'],'quote':passage['text']}]}
counterexample_accepted = validate_generated(counterexample, [passage]) is not None
files = sorted((root/'demo/nawa_demo').glob('*.py')) + sorted((root/'demo/samples').rglob('*'))
hashes = {str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
report = {
 'source_commit':'823565f7c44c15b07719b91670fe8bbfb8d96521',
 'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
 'environment':{'python':platform.python_version(),'platform':platform.system()},
 'scope':'Selected unchanged source modules and committed synthetic fixtures; standard-library local replay. Not a full test-suite rerun.',
 'extraction':[{'document':q['document'],'subtotal':q['subtotal'],'vat_amount':q['vat_amount'],'total':q['total'],'checks':q['checks']} for q in quotes],
 'price_comparison':compare([samples/'english_quote.txt',samples/'arabic_quote.txt',samples/'incorrect_vat_quote.txt'])['lowest_valid_total'],
 'review':{'financial_mismatch_approval_blocked':blocked,'valid_quotation_status':inspect(decided)['status'],'stale_revision_blocked':stale_blocked},
 'evaluation':evaluation,
 'known_semantic_limitation':{'candidate_answer':counterexample['answer'],'source_subtotal':'1000.00','source_grand_total':'1050.00','accepted_by_lexical_gate':counterexample_accepted,'interpretation':'The validator checks tokens and exact quotes, not whether the answer assigns a number to the correct field. This is a reproduced limitation, not a semantic-accuracy result.'},
 'source_file_sha256':hashes,
 'not_executed':['PDF extraction','Tesseract OCR','PostgreSQL','Docker','Live model API','Browser automation','Cloud deployment','Independent bilingual benchmark']
}
assert evaluation['all_passed'] and evaluation['total_cases']==11
assert blocked and stale_blocked and inspect(decided)['status']=='approved'
assert counterexample_accepted
rendered = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
if args.output:
    args.output.write_text(rendered, encoding='utf-8')
else:
    sys.stdout.buffer.write(rendered.encode('utf-8'))
