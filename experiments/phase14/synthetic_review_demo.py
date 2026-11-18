"""Review-only demo of two exact bundled synthetic PDFs; no production data."""
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
ARABIC_SAMPLE_SHA256 = frozenset({
    'efe191b915a9ba0f205017f9c7911d72422ddb047c9a7ef48c3e728a47499b68',
    'ff402285c60252bf4b25084cf35cbc9a1f61769aa51adf19274bfaf0ba23fc53',
})
ARABIC_QUESTION = 'ما إجمالي عرض السعر بالدرهم؟'


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

def parse_arabic_sample(content,demo_dir):
    env=os.environ.copy()
    env['PYTHONPATH']=str(demo_dir)+os.pathsep+env.get('PYTHONPATH','')
    with TemporaryDirectory(prefix='nawa14-arabic-') as directory:
        source,output=Path(directory)/'source.pdf',Path(directory)/'result.json'
        source.write_bytes(content)
        with output.open('wb') as stream:
            subprocess.run([sys.executable,str(Path(__file__).with_name('synthetic_arabic_parser.py')),str(source)],
                           cwd=demo_dir,env=env,stdout=stream,stderr=subprocess.DEVNULL,
                           check=True,timeout=20)
        with output.open('rb') as stream:
            encoded=stream.read(2*1024*1024+1)
        if len(encoded)>2*1024*1024:
            raise ValueError('Synthetic parser output too large')
        return json.loads(encoded.decode('utf-8'))

def run_demo(demo_dir, *, language='en', embedding_fn=embed, extraction_fn=None):
    if language not in ('en','ar'):
        raise ValueError('Unsupported synthetic fixture')
    demo_dir=Path(demo_dir)
    filename='english_supplier.pdf' if language=='en' else 'arabic_text_supplier.pdf'
    allowed=SAMPLE_SHA256 if language=='en' else ARABIC_SAMPLE_SHA256
    question=QUESTION if language=='en' else ARABIC_QUESTION
    if extraction_fn is None:
        extraction_fn=parse_sample if language=='en' else parse_arabic_sample
    sample=demo_dir/'samples'/'pdf'/filename
    def snapshot():
        with sample.open('rb') as stream:
            content=stream.read(4*1024*1024+1)
        if len(content)>4*1024*1024:
            raise ValueError('Synthetic fixture too large')
        digest=hashlib.sha256(content).hexdigest()
        if digest not in allowed:
            raise ValueError('Only the exact bundled synthetic PDF is supported')
        result=extraction_fn(content,demo_dir)
        row={'document_id':'1'*32,'family_id':'a'*32,'version':1,
             'tenant_id':'demo-a','job_state':'completed','filename':filename,
             'sha256':digest,'source_verified':True,'result':result}
        return fixture_snapshot([row],tenant='demo-a',principal='analyst-a',membership_active=True)
    review=retrieve_for_review(question,tenant='demo-a',principal='analyst-a',
                               load_snapshot=snapshot,embed_fn=embedding_fn,limit=5)
    if review['status']!='requires_human_review':
        return {'status':'unavailable'}
    result=resolve_for_review(review,tenant='demo-a',principal='analyst-a',load_snapshot=snapshot)
    if result['status']=='requires_human_review':
        result['scope']='Synthetic fixture only; extracted text is untrusted and requires human review.'
        result['question']=question
        if language=='ar':
            for item in result['evidence']:
                item['untrusted_normalized_text']=item.pop('untrusted_source_text')
            result['normalization_note']=('Arabic text may be normalized or reordered for extraction; '
                                          'compare against the original PDF. The total label in this fixture is English.')
    return result


def main():
    parser=argparse.ArgumentParser(description='NAWA synthetic evidence-review demo')
    parser.add_argument('--demo-dir',type=Path,default=Path(__file__).resolve().parents[2]/'demo',
                        help='Repository demo directory containing the bundled synthetic PDF')
    parser.add_argument('--language',choices=('en','ar'),default='en')
    args=parser.parse_args()
    try:
        result=run_demo(args.demo_dir,language=args.language)
    except (OSError,ValueError,subprocess.SubprocessError):
        result={'status':'unavailable'}
    print(json.dumps(result,ensure_ascii=True,indent=2))
    if result['status']!='requires_human_review':
        raise SystemExit(1)


if __name__=='__main__':
    main()

