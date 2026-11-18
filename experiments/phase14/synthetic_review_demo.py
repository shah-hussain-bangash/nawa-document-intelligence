"""Review-only demo of one exact bundled synthetic PDF; no production data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from compare_retrieval import embed
from hybrid_review import retrieve_for_review
from phase13_snapshot_fixture import fixture_snapshot
from resolve_review_evidence import resolve_for_review

SAMPLE_SHA256 = frozenset({
    'ff139c12dde6ea0091b621d9cda22c33ba33a6c87024ff24937a9fc638b28697',
    'b647be96d49b143867e0564060770659dbc7d1a0b183d71e13a534d117ea5fba',
})
QUESTION = 'What is the grand total in AED?'


def parse_sample(content, demo_dir):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(demo_dir) + os.pathsep + env.get('PYTHONPATH','')
    with TemporaryDirectory(prefix='nawa14-demo-') as directory:
        source,output = Path(directory)/'source.pdf',Path(directory)/'result.json'
        source.write_bytes(content)
        with output.open('wb') as stream:
            subprocess.run([sys.executable,'-m','nawa_demo.intake_parser',str(source)],
                           cwd=demo_dir,env=env,stdout=stream,stderr=subprocess.DEVNULL,
                           check=True,timeout=20)
        with output.open('rb') as stream:
            encoded=stream.read(2*1024*1024+1)
        if len(encoded)>2*1024*1024:
            raise ValueError('Synthetic parser output too large')
        return json.loads(encoded.decode('utf-8'))


def run_demo(demo_dir, *, embedding_fn=embed, extraction_fn=parse_sample):
    demo_dir=Path(demo_dir)
    sample=demo_dir/'samples'/'pdf'/'english_supplier.pdf'
    def snapshot():
        with sample.open('rb') as stream:
            content=stream.read(4*1024*1024+1)
        if len(content)>4*1024*1024:
            raise ValueError('Synthetic fixture too large')
        digest=hashlib.sha256(content).hexdigest()
        if digest not in SAMPLE_SHA256:
            raise ValueError('Only the exact bundled synthetic PDF is supported')
        result=extraction_fn(content,demo_dir)
        row={'document_id':'1'*32,'family_id':'a'*32,'version':1,
             'tenant_id':'demo-a','job_state':'completed','filename':'english_supplier.pdf',
             'sha256':digest,'source_verified':True,'result':result}
        return fixture_snapshot([row],tenant='demo-a',principal='analyst-a',membership_active=True)
    review=retrieve_for_review(QUESTION,tenant='demo-a',principal='analyst-a',
                               load_snapshot=snapshot,embed_fn=embedding_fn,limit=5)
    if review['status']!='requires_human_review':
        return {'status':'unavailable'}
    result=resolve_for_review(review,tenant='demo-a',principal='analyst-a',load_snapshot=snapshot)
    if result['status']=='requires_human_review':
        result['scope']='Synthetic fixture only; source text is untrusted and requires human review.'
        result['question']=QUESTION
    return result


def main():
    parser=argparse.ArgumentParser(description='NAWA synthetic evidence-review demo')
    parser.add_argument('--demo-dir',type=Path,default=Path(__file__).resolve().parents[2]/'demo',
                        help='Repository demo directory containing the bundled synthetic PDF')
    args=parser.parse_args()
    try:
        result=run_demo(args.demo_dir)
    except (OSError,ValueError,subprocess.SubprocessError):
        result={'status':'unavailable'}
    print(json.dumps(result,ensure_ascii=True,indent=2))
    if result['status']!='requires_human_review':
        raise SystemExit(1)


if __name__=='__main__':
    main()

