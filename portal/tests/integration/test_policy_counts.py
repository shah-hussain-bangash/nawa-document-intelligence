"""Source-bound counts, reported model failures and conservative fallbacks."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from uae_ai.core.config import Settings
from uae_ai.db import Document
from uae_ai.rag.policy_counts import is_count_question, minimums
from uae_ai.rag.retrieval import answer_question
from test_workspace import app, client, login


CAPTURE = json.loads((Path(__file__).parents[1] / 'data/policy-count-cases-v066.json').read_text(encoding='utf-8'))


def document(id, text, *, category='Procurement', **kwargs):
    values = dict(id=id, title=id, status='ready', category=category, version=1,
                  classification='synthetic', pages=[{'page': 1, 'text': text}])
    values.update(kwargs)
    return SimpleNamespace(**values)


def no_model(*args, **kwargs):
    pytest.fail('Count answers must not send evidence to a generation model')


@pytest.mark.parametrize('case', CAPTURE['cases'], ids=lambda case: case['id'])
def test_live_counterexamples_are_answered_from_their_actual_evidence(case, monkeypatch):
    evidence = case['evidence']
    docs = [document(c['document_id'], c['text'], title=c['title'], version=c['version'],
                     category='HR' if c['document_id']=='hr-ar' else 'Quotation' if c['document_id']=='quote-ar' else 'Procurement')
            for c in evidence]
    monkeypatch.setattr('uae_ai.rag.retrieval.search', lambda *args: evidence)
    monkeypatch.setattr('uae_ai.rag.retrieval.httpx.Client', no_model)
    result = answer_question(case['question'], docs, Settings(app_env='test', model_mode='ollama'))
    assert result['mode'] == 'extractive'
    assert result['citations'] == evidence  # Original text, order, page and version.
    if case['expected'] == 'verified':
        assert result['reason'] == 'policy_count_verified'
        assert {fact['minimum'] for fact in result['count_facts']} == {case['minimum']}
        assert str(case['minimum']) in result['answer']
    elif case['expected'] == 'conflict':
        assert result['reason'] == 'conflicting_policy_counts'
        assert result['status'] == 'insufficient_evidence'
        assert {fact['minimum'] for fact in result['count_facts']} == {2, 3}
        assert 'Procurement operating framework' in result['answer']
        assert 'دليل الموارد البشرية' not in result['answer']
    else:
        assert result['reason'] == 'policy_count_unverified'
        assert result['status'] == 'insufficient_evidence'
        assert not result['count_facts']


@pytest.mark.parametrize('text,expected', [
    ('At least 7 valid supplier quotations are required.', [7]),
    ('Procurement requires at least three written vendor quotes.', [3]),
    ('يجب إرفاق ٣ عروض أسعار صالحة على الأقل.', [3]),
    ('يجب إرفاق أربعة عروض صالحة على الأقل.', [4]),
    ('يلزم عرضان صالحان على الأقل.', [2]),
    ('يجب إرفاق عرض واحد صالح على الأقل.', [1]),
])
def test_supported_minimum_statements_are_not_hardcoded_to_two(text, expected):
    assert minimums(text) == (expected, False)


@pytest.mark.parametrize('text', [
    'Procurement does not require at least two valid supplier quotations.',
    'At least two quotations are not required.',
    'If the amount exceeds a threshold, require at least three supplier quotations.',
    'For example, procurement requires at least two quotations.',
    'Procurement requires exactly four quotations.',
    'Procurement requires at most four quotations.',
    'Procurement requires at least twenty-one supplier quotations.',
    'Procurement requires at least 0 quotations.',
    'Procurement requires at least two or three quotations.',
    'Does procurement require at least two quotations?',
    'Procurement requires at least two quotations per supplier.',
    'Procurement requires at least three quotations for purchases below a threshold.',
    'لا يجب إرفاق عرضين صالحين على الأقل.',
    'إذا تجاوز المبلغ الحد يجب إرفاق ثلاثة عروض صالحة على الأقل.',
])
def test_unknown_negated_conditional_or_nonminimum_wording_stays_unverified(text):
    values, uncertain = minimums(text)
    assert not values and uncertain


@pytest.mark.parametrize('question', [
    "What is Falcon Digital's bank account number?",
    'What is the net amount in the quotation?',
    'ما المبلغ الصافي في عرض السعر الممسوح؟',
    'هل يمكنني اعتماد طلب شراء أعددته بنفسي؟',
    'What is the quotation number?',
    'How many annual leave days do I have?',
    'What is the minimum quotation price?',
    'What is the minimum net amount for the supplier quotations?',
    'ما الحد الأدنى لسعر عرض سعر؟',
    'كم تكلفة عرض سعر للمورد؟',
])
def test_other_question_types_keep_their_existing_route(question):
    assert not is_count_question(question)


@pytest.mark.parametrize('question', [
    'What is the minimum number of supplier quotations required?',
    'ما الحد الأدنى لعدد عروض الأسعار المطلوبة؟',
])
def test_minimum_number_wording_is_a_count_question(question):
    assert is_count_question(question)


def test_deleted_hr_and_quotation_amounts_are_not_policy_counts(monkeypatch):
    docs = [document('withdrawn', 'Procurement requires at least nine quotations.', status='deleted'),
            document('hr', 'Procurement requires at least seven quotations.', category='HR'),
            document('quotation', 'Example requires at least four quotations. Net amount: 12500 AED', category='Quotation'),
            document('policy', 'Procurement requires at least three valid supplier quotations.')]
    monkeypatch.setattr('uae_ai.rag.retrieval.httpx.Client', no_model)
    result = answer_question('How many quotations are required?', docs,
                             Settings(app_env='test', model_mode='ollama'))
    assert result['reason'] == 'policy_count_verified'
    assert {fact['minimum'] for fact in result['count_facts']} == {3}
    assert 'withdrawn' not in {c['document_id'] for c in result['citations']}


def test_unknown_required_policy_wording_cannot_be_silently_overridden(monkeypatch):
    docs = [document('known', 'Procurement requires at least two quotations.'),
            document('unsupported', 'Procurement requires exactly four quotations.')]
    monkeypatch.setattr('uae_ai.rag.retrieval.httpx.Client', no_model)
    result = answer_question('How many quotations are required?', docs,
                             Settings(app_env='test', model_mode='ollama'))
    assert result['reason'] == 'policy_count_unverified'
    assert result['status'] == 'insufficient_evidence'


def test_real_api_uses_readable_policy_evidence_and_records_bounded_reason(client, app, monkeypatch):
    login(client)
    app.state.settings.model_mode = 'ollama'
    monkeypatch.setattr('uae_ai.rag.retrieval.httpx.Client', no_model)
    r = client.post('/api/v1/knowledge/query', json={
        'question': 'كم عرض سعر صالح يلزم قبل الموافقة التجريبية؟', 'domain': 'procurement'})
    assert r.status_code == 200, r.text
    result = r.json()
    assert result['reason'] == 'policy_count_verified' and result['mode'] == 'extractive'
    assert {fact['minimum'] for fact in result['count_facts']} == {2}
    event = client.get('/api/v1/workspace').json()['events'][0]
    assert event['action'] == 'Knowledge search completed'
    assert event['details']['reason'] == 'policy_count_verified'
    assert 'سياسة' not in str(event['details'])  # No raw policy text added to audit.


@pytest.mark.parametrize('mismatch', ['page', 'version', 'text'])
def test_source_page_version_and_literal_passage_must_match(mismatch, monkeypatch):
    doc = document('policy', 'Procurement requires at least two quotations.')
    citation = {'document_id': doc.id, 'version': 1, 'page': 1, 'title': doc.title,
                'text': doc.pages[0]['text'], 'classification': 'synthetic'}
    citation[mismatch] = 'Procurement requires at least nine quotations.' if mismatch=='text' else 2
    monkeypatch.setattr('uae_ai.rag.retrieval.search', lambda *args: [citation])
    monkeypatch.setattr('uae_ai.rag.retrieval.httpx.Client', no_model)
    result = answer_question('How many quotations are required?', [doc], Settings(model_mode='ollama'))
    assert result['reason'] == 'policy_count_unverified'
    assert not result['count_facts']


def test_actual_api_excludes_other_tenant_and_role_restricted_counts(client, app, monkeypatch):
    login(client)
    app.state.settings.model_mode = 'ollama'
    with app.state.session_factory() as db:
        for id, tenant, roles, count in [('private-count', 'operations', ['admin'], 99),
                                         ('other-tenant-count', 'research', ['analyst'], 88)]:
            db.add(Document(id=id, tenant_id=tenant, created_by='test', title='PRIVATE_COUNT_CANARY',
                            filename='private.txt', category='Procurement', status='ready',
                            classification='synthetic', allowed_roles=roles, language='en',
                            version=1, content_hash='synthetic-test',
                            pages=[{'page':1,'text':f'Procurement requires at least {count} supplier quotations.'}]))
        db.commit()
    monkeypatch.setattr('uae_ai.rag.retrieval.httpx.Client', no_model)
    r = client.post('/api/v1/knowledge/query', json={'question':'How many valid supplier quotations are required before simulated approval?'})
    assert r.status_code == 200, r.text
    result = r.json()
    assert result['reason'] == 'policy_count_verified'
    assert {fact['minimum'] for fact in result['count_facts']} == {2}
    assert 'PRIVATE_COUNT_CANARY' not in json.dumps(result)
