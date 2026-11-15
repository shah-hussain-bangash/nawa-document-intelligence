"""Deterministic, permission-filtered BM25 retrieval of synthetic PDF page evidence.

Not a generative RAG service, an authentication system, or a production ACL engine.
Permissions are passed explicitly by the trusted caller and MUST be enforced upstream.
"""
from collections import Counter
from dataclasses import dataclass
import math
from pathlib import Path
import re
import unicodedata

# Accept Arabic letters, ASCII alphanumerics and Unicode decimal digits.
TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize('NFKC', text).casefold()
    text = text.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789'))
    return TOKEN_RE.findall(text)


@dataclass(frozen=True)
class Passage:
    passage_id: str
    document_id: str
    version: str
    tenant_id: str
    page: int
    text: str
    allowed_principals: tuple[str, ...]
    source: str
    method: str = 'text_layer'

    @classmethod
    def from_dict(cls, data: dict):
        required = {'passage_id','document_id','version','tenant_id','page','text','allowed_principals','source'}
        missing = required - data.keys()
        if missing:
            raise ValueError(f'Missing passage fields: {sorted(missing)}')
        if not all(isinstance(data[k], str) and data[k].strip() for k in required - {'page','allowed_principals'}):
            raise ValueError('Passage identifiers, source and text must be nonempty strings')
        if not isinstance(data['page'], int) or isinstance(data['page'], bool) or data['page'] < 1:
            raise ValueError('Page must be a positive integer')
        principals = data['allowed_principals']
        if not isinstance(principals, list) or not principals or not all(isinstance(p,str) and p.strip() for p in principals):
            raise ValueError('Passage ACL must be a nonempty list of principal IDs')
        if len(principals) != len(set(principals)):
            raise ValueError('Duplicate ACL principals')
        method = data.get('method','text_layer')
        if method not in ('text_layer','ocr','synthetic'):
            raise ValueError('Unsupported evidence method')
        return cls(**{**data,'allowed_principals':tuple(principals),'method':method})


class BM25Index:
    """Index only passages authorized for one trusted tenant and principal.

    The constructor deliberately refuses empty credentials. Filtering takes place
    BEFORE statistics are computed, so unauthorized text cannot affect ranking.
    """
    def __init__(self, passages: list[Passage], *, tenant_id: str, principal_id: str, k1: float = 1.5, b: float = 0.75):
        if not tenant_id or not principal_id:
            raise ValueError('tenant_id and principal_id are required (fail closed)')
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError('Invalid BM25 parameters')
        self.tenant_id, self.principal_id, self.k1, self.b = tenant_id, principal_id, k1, b
        self.passages = [p for p in passages if p.tenant_id == tenant_id and principal_id in p.allowed_principals]
        if len({p.passage_id for p in self.passages}) != len(self.passages):
            raise ValueError('Duplicate authorized passage_id')
        self.freqs = [Counter(tokenize(p.text)) for p in self.passages]
        self.lengths = [sum(f.values()) for f in self.freqs]
        self.avgdl = sum(self.lengths)/len(self.lengths) if self.lengths else 0
        self.df = Counter(t for f in self.freqs for t in f)

    def search(self, query: str, *, k: int = 5) -> list[dict]:
        if not isinstance(query,str) or not query.strip():
            raise ValueError('Nonempty search query required')
        if not isinstance(k,int) or isinstance(k,bool) or k < 1 or k > 100:
            raise ValueError('k must be from 1 to 100')
        terms = set(tokenize(query))
        if not terms:
            return []
        n = len(self.passages)
        results=[]
        for p, f, dl in zip(self.passages,self.freqs,self.lengths):
            score=0.0
            for t in terms:
                tf=f.get(t,0)
                if not tf:
                    continue
                df=self.df[t]
                idf=math.log(1+(n-df+0.5)/(df+0.5))
                score+=idf*(tf*(self.k1+1))/(tf+self.k1*(1-self.b+self.b*dl/self.avgdl))
            if score > 0:
                results.append({'passage_id':p.passage_id,'document_id':p.document_id,
                                'version':p.version,'page':p.page,'source':p.source,
                                'method':p.method,'text':p.text,'score':round(score,6)})
        return sorted(results,key=lambda x:(-x['score'],x['passage_id']))[:k]


def read_corpus(path: Path) -> list[Passage]:
    import json
    path=Path(path)
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,list):
        raise ValueError('Corpus must be a JSON array')
    passages=[Passage.from_dict(item) for item in data]
    if len({p.passage_id for p in passages})!=len(passages):
        raise ValueError('Duplicate passage IDs in corpus')
    return passages


def pdf_page_passages(path: Path, *, document_id: str, version: str, tenant_id: str,
                      allowed_principals: list[str]) -> list[Passage]:
    """Optional direct PDF page indexing, text-layer only; no hidden OCR.

    For real access control, a trusted service must supply tenant/principal values.
    """
    import pymupdf
    if Path(path).suffix.lower() != '.pdf':
        raise ValueError('Expected PDF')
    if not document_id or not version or not tenant_id or not allowed_principals:
        raise ValueError('Required document metadata and ACL missing')
    result=[]
    with pymupdf.open(path) as doc:
        if doc.needs_pass:
            raise ValueError('Password-protected PDF unsupported')
        for i,page in enumerate(doc,1):
            text=page.get_text('text',sort=True).strip()
            if not text:
                continue
            result.append(Passage.from_dict({
                'passage_id':f'{document_id}:{version}:p{i}', 'document_id':document_id,
                'version':version,'tenant_id':tenant_id,'page':i,'text':text,
                'source':Path(path).name,'allowed_principals':allowed_principals,
                'method':'text_layer',
            }))
    return result
