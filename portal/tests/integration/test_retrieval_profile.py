"""EmbeddingGemma formatting, source scope, ambiguity and captured-score replay."""
import gzip
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from uae_ai.core.config import Settings
from uae_ai.rag.embeddings import retrieval_inputs, retrieval_profile
from uae_ai.rag.retrieval import answer_question, search, source_language_hint, source_documents

CAPTURE = Path(__file__).resolve().parents[1] / 'data/embeddinggemma-v064-cosines.json.gz'


def document(id, text, *, title=None, language='en', classification='synthetic', status='ready'):
    return SimpleNamespace(id=id, title=title or id, language=language, classification=classification,
                           category='Policy', status=status, version=1, pages=[{'page':1,'text':text}])


def config(tmp_path, **kwargs):
    return Settings(app_env='test', data_dir=tmp_path, retrieval_mode='hybrid',
                    embedding_model='embeddinggemma:300m', retrieval_min_cosine=.25, **kwargs)


@pytest.mark.parametrize('question,expected', [
    ('What does the Arabic procurement guide require?', 'ar'),
    ('Find the English access policy', 'en'),
    ('Show the handbook written in Arabic', 'ar'),
    ('ما شروط الدليل العربي؟', 'ar'),
    ('اعرض السياسة باللغة الإنجليزية', 'en'),
    ('Compare Arabic and English policies', None),
    ('Quotation for Arabic document processing', None),
    ('كم عرض سعر مطلوب للمشتريات؟', None),
])
def test_explicit_source_language_is_separate_from_query_language(question, expected):
    assert source_language_hint(question) == expected


def test_gemma_protocol_keeps_source_text_unchanged(tmp_path):
    passages=[{'title':'عنوان تجريبي','text':'Original evidence'}]
    settings=config(tmp_path)
    assert retrieval_inputs('Question',passages,settings)==[
        'task: search result | query: Question','title: عنوان تجريبي | text: Original evidence']
    settings.embedding_model='other-model'
    assert retrieval_inputs('Question',passages,settings)==['Question','Original evidence']
    assert passages[0]['text']=='Original evidence'


def test_page_script_can_correct_a_stale_upload_language_label():
    doc=document('scan','سياسة مشتريات تجريبية باللغة العربية',title='uploaded-scan.pdf',language='en')
    assert source_documents('Show the Arabic policy',[doc],'all') == [doc]


def test_semantic_source_heads_survive_many_weak_lexical_overlaps(tmp_path, monkeypatch):
    docs=[document(f'noise-{i}','annual vacation generic unrelated guidance') for i in range(8)]
    docs.append(document('meaning','Staff may take paid time away from work.'))
    docs.append(document('private','PRIVATE_CANARY',classification='confidential'))
    docs.append(document('withdrawn','WITHDRAWN_CANARY',status='deleted'))
    seen=[]
    def embed(texts,_):
        seen.extend(texts)
        scores=[.95 if 'Staff may' in text else .3 for text in texts[1:]]
        return [[1.,0.],*[[s,math.sqrt(1-s*s)] for s in scores]]
    monkeypatch.setattr('uae_ai.rag.embeddings.vectors',embed)
    results=search('annual vacation',docs,settings=config(tmp_path))
    assert results[0]['document_id']=='meaning'
    assert results[0]['text']=='Staff may take paid time away from work.'
    assert 'PRIVATE_CANARY' not in ' '.join(seen) and 'WITHDRAWN_CANARY' not in ' '.join(seen)


@pytest.mark.parametrize('scores,expected', [([.30,.295],False),([.70,.695],True)])
def test_only_weak_ambiguous_dense_only_matches_abstain(tmp_path, monkeypatch, scores, expected):
    docs=[document('one','Source alpha'),document('two','Source beta')]
    monkeypatch.setattr('uae_ai.rag.embeddings.vectors',lambda *_:[[1.,0.],*[[s,math.sqrt(1-s*s)] for s in scores]])
    assert bool(search('purple spaceship',docs,settings=config(tmp_path))) == expected


def test_overlapping_pages_of_one_source_are_not_distinct_source_ambiguity(tmp_path, monkeypatch):
    doc=document('one','Source alpha')
    doc.pages.append({'page':2,'text':'Source beta'})
    monkeypatch.setattr('uae_ai.rag.embeddings.vectors',lambda *_:[[1.,0.],[.3,math.sqrt(.91)],[.295,math.sqrt(1-.295**2)]])
    assert search('purple spaceship',[doc],settings=config(tmp_path))


def test_language_scope_applies_before_embedding_and_field_grounding(tmp_path, monkeypatch):
    docs=[document('en','Supplier: Example Works\nBank account: 12345678',language='en'),
          document('ar','سياسة مشتريات تجريبية',language='ar')]
    monkeypatch.setattr('uae_ai.rag.embeddings.vectors',lambda *_:pytest.fail('Missing field must not reach embeddings'))
    result=answer_question('What bank account number is in the Arabic policy for Example Works?',docs,config(tmp_path))
    assert result['status']=='insufficient_evidence' and result['citations']==[]


def captured_replay(monkeypatch, settings):
    fixture=json.loads(gzip.decompress(CAPTURE.read_bytes()).decode('utf-8'))
    corpus=fixture['documents']; questions=fixture['questions']
    docs=[SimpleNamespace(id=row['document_id'],title=row['title'],category=row['category'],
                          classification=row['classification'],language=row['language'],status='ready',
                          version=row['version'],pages=[{'page':row['page'],'text':row['text']}]) for row in corpus]
    query_index={'task: search result | query: '+q['question']:i for i,q in enumerate(questions)}
    doc_index={'title: '+d['title']+' | text: '+d['text']:i for i,d in enumerate(corpus)}
    def embed(inputs,_):
        n=query_index[inputs[0]]
        scores=[fixture['cosines']['retrieval'][n][doc_index[text]] for text in inputs[1:]]
        # Unit vectors reproduce the captured query/passage cosines exactly;
        # this tests post-embedding ranking, not the model's forward pass.
        return [[1.,0.],*[[s,math.sqrt(max(0,1-s*s))] for s in scores]]
    monkeypatch.setattr('uae_ai.rag.embeddings.vectors',embed)
    rows=[]
    for question in questions:
        titles=[r['title'] for r in search(question['question'],docs,question.get('domain','all'),settings)]
        target=question['expected_title']
        rows.append({**question,'retrieved_titles':titles,'passed':target in titles if target else not titles,
                     'reciprocal_rank':1/(titles.index(target)+1) if target in titles else 0})
    return fixture,rows


def test_captured_real_model_scores_improve_cross_language_targets_without_regression(tmp_path,monkeypatch):
    fixture,rows=captured_replay(monkeypatch,config(tmp_path))
    positives=[row for row in rows if row['expected_title']]
    negatives=[row for row in rows if not row['expected_title']]
    assert sum(row['passed'] for row in positives)==76
    assert sum(row['passed'] for row in negatives)==9
    before={row['id'] for row in fixture['baseline_results'] if row['expected_title'] and row['passed']}
    after={row['id'] for row in positives if row['passed']}
    assert before <= after
    assert retrieval_profile(config(tmp_path))['min_cosine']==.25
