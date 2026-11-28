"""Review-only retrieval from one exact bundled Arabic-label TXT fixture."""
import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from compare_retrieval import cosine, embed, rrf
from retrieval import BM25Index

SAMPLE_SHA256=frozenset({
    '2ca18b842da159cb00f85d8da3f0fb4382715f80ee7518d915150e4bec134210',
    'fdf488846d40ce360f90e64e0c86825fe16112d55f25339c9ad44a64cf560ac8',
})
QUESTION='كم يبلغ الإجمالي شامل الضريبة بالدرهم؟'


@dataclass(frozen=True)
class TextPassage:
    passage_id:str
    document_id:str
    version:str
    tenant_id:str
    page:None
    text:str
    allowed_principals:tuple
    source:str
    method:str


def extract_text_fixture(content,demo_dir):
    env=os.environ.copy()
    env['PYTHONPATH']=str(demo_dir)+os.pathsep+env.get('PYTHONPATH','')
    with TemporaryDirectory(prefix='nawa14-text-') as directory:
        source,output=Path(directory)/'source.txt',Path(directory)/'result.json'
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


def run_demo(demo_dir, *, embedding_fn=embed, extraction_fn=extract_text_fixture):
    demo_dir=Path(demo_dir)
    sample=demo_dir/'samples'/'arabic_quote.txt'
    def snapshot():
        with sample.open('rb') as stream:
            content=stream.read(4*1024*1024+1)
        digest=hashlib.sha256(content).hexdigest()
        if len(content)>4*1024*1024 or digest not in SAMPLE_SHA256:
            raise ValueError('Only the exact bundled synthetic TXT is supported')
        lines=content.decode('utf-8').splitlines()
        result=extraction_fn(content,demo_dir)
        evidence=result.get('evidence')
        if not isinstance(evidence,dict) or not evidence:
            raise ValueError('Synthetic text evidence unavailable')
        rows={}
        for field,item in evidence.items():
            if not isinstance(field,str) or not isinstance(item,dict):
                raise ValueError('Invalid synthetic text evidence')
            line=item.get('line')
            if (not isinstance(line,int) or isinstance(line,bool) or not 1 <= line <= len(lines)
                    or item.get('source_text') != lines[line-1]):
                raise ValueError('Synthetic text evidence differs from source')
            rows[field]={'line':line,'text':item['source_text']}
        return digest,rows
    try:
        digest,rows=snapshot()
        passages=[TextPassage(field,'synthetic-text','1','demo-a',None,item['text'],
                              ('analyst-a',),'arabic_quote.txt','synthetic')
                  for field,item in rows.items()]
        bm25=[r['passage_id'] for r in BM25Index(passages,tenant_id='demo-a',
                                                 principal_id='analyst-a').search(QUESTION,k=100)]
        vectors=embedding_fn([p.text for p in passages]+[QUESTION])
        if len(vectors)!=len(passages)+1:
            raise ValueError('Embedding count mismatch')
        ranked=[p.passage_id for _,p in sorted(
            ((cosine(v,vectors[-1]),p) for p,v in zip(passages,vectors[:-1])),
            key=lambda item:(-item[0],item[1].passage_id))]
        selected=rrf(bm25,ranked)[:5]
        current_digest,current_rows=snapshot()
        if digest!=current_digest or any(rows[id_]!=current_rows.get(id_) for id_ in selected):
            raise ValueError('Synthetic source changed')
        return {'status':'requires_human_review','question':QUESTION,
                'scope':'Synthetic UTF-8 TXT; exact source lines are untrusted and require human review.',
                'evidence':[{'source':'arabic_quote.txt','line':current_rows[id_]['line'],
                             'source_sha256':current_digest,
                             'untrusted_source_text':current_rows[id_]['text']} for id_ in selected]}
    except (ValueError,TypeError,KeyError,OSError,TimeoutError,subprocess.SubprocessError):
        return {'status':'unavailable'}


def main():
    parser=argparse.ArgumentParser(description='Synthetic Arabic TXT evidence-review demo')
    parser.add_argument('--demo-dir',type=Path,default=Path(__file__).resolve().parents[2]/'demo')
    args=parser.parse_args()
    result=run_demo(args.demo_dir)
    print(json.dumps(result,ensure_ascii=True,indent=2))
    if result['status']!='requires_human_review':
        raise SystemExit(1)


if __name__=='__main__':
    main()

