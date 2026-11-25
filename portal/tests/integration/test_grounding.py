from types import SimpleNamespace
import pytest
from uae_ai.core.config import Settings
from uae_ai.rag.retrieval import answer_question
from test_workspace import app, client, login

QUESTION = "What is Falcon Digital's bank account number?"
ARABIC = "ما رقم الحساب البنكي للمورد Falcon Digital؟"


def doc(text, id="bank", **overrides):
    values = dict(id=id, title="Synthetic supplier details", version=1, status="ready", category="Quotation", classification="synthetic", pages=[{"page":1,"text":text}])
    values.update(overrides)
    return SimpleNamespace(**values)


def answer(question, docs):
    return answer_question(question, docs, Settings(app_env="test", model_mode="extractive"))


@pytest.mark.parametrize("question", [QUESTION, ARABIC, "What's Falcon Digital's bank account number?", "Bank account number for Falcon Digital?", "What is Falcon Digital's bank account number according to the policy?", "How can I get Falcon Digital's bank account number?", "Do you have Falcon Digital's bank account number?", "Please show me Falcon Digital's bank account numbers?"])
def test_supplier_name_and_price_are_not_bank_account_evidence(question):
    result = answer(question, [doc("Supplier: Falcon Digital\nNet amount: 172800.00 AED\nTax: 5%")])
    assert result['status'] == 'insufficient_evidence'
    assert result['reason'] == 'requested_field_not_supported'
    assert result['citations'] == []
    assert result['requested_fields'] == ['account_number']


@pytest.mark.parametrize("question", [QUESTION, ARABIC])
def test_exact_reported_failure_against_seeded_workspace(client, question):
    login(client)
    response=client.post('/api/v1/knowledge/query',json={'question':question})
    assert response.status_code==200,response.text
    assert response.json()['status']=='insufficient_evidence'
    assert response.json()['citations']==[]
    events=client.get('/api/v1/workspace').json()['events']
    event=next(e for e in events if e['action']=='Knowledge search completed')
    assert event['details']['answer_status']=='insufficient_evidence'
    assert event['details']['reason']=='requested_field_not_supported'
    assert '991122' not in str(event['details'])


def test_supported_field_in_lower_ranked_source_is_found_without_semantic_service():
    distractors = [doc('Supplier: Falcon Digital\nNet amount: 100 AED',str(i),title='Falcon Digital bank account number query') for i in range(6)]
    supported = doc('SYNTHETIC TEST ONLY\nSupplier: Falcon Digital\nBank account number: 9911223344')
    result=answer(QUESTION,[*distractors,supported])
    assert result['status']=='answered'
    assert [c['document_id'] for c in result['citations']]==['bank']
    assert '9911223344' in result['citations'][0]['text']


def test_supported_polite_field_request_remains_grounded():
    result=answer("Do you have Falcon Digital's bank account number?",[doc('Supplier: Falcon Digital\nBank account number: 9911223344')])
    assert result['status']=='answered' and result['citations']


@pytest.mark.parametrize('supplier',['Atlas Technology','Falcon Services'])
def test_another_supplier_cannot_supply_the_requested_value(supplier):
    result=answer(QUESTION,[doc(f'Supplier: {supplier}\nBank account number: 9911223344',title='Falcon Digital')])
    assert result['status']=='insufficient_evidence'
    assert not result['citations']


def test_unknown_or_unspecified_supplier_cannot_use_the_only_available_account():
    source=doc('Supplier: Atlas Technology\nBank account number: 9911223344')
    assert answer("What is Unknown Company's bank account number?",[source])['status']=='insufficient_evidence'
    assert answer('What is the bank account number?',[source])['reason']=='supplier_not_specified'


@pytest.mark.parametrize('line',['Net amount: 172800.00 AED','Bank account number: not provided','Bank account number: unknown 172800','Bank account number: [redacted]','Account number: 9911223344'])
def test_prices_placeholders_and_nonbank_customer_accounts_do_not_pass(line):
    assert answer(QUESTION,[doc('Supplier: Falcon Digital\n'+line)])['status']=='insufficient_evidence'


def test_conflicting_fields_are_withheld():
    sources=[doc('Supplier: Falcon Digital\nBank account number: '+value,str(i)) for i,value in enumerate(['9911223344','8877665544'])]
    result=answer(QUESTION,sources)
    assert result['status']=='insufficient_evidence'
    assert result['reason']=='conflicting_field_evidence'
    assert not result['citations']


def test_arabic_fields_and_digits_and_legal_suffix_normalisation():
    result=answer('ما رقم الحساب البنكي للمورد Falcon Digital؟',[doc('اسم المورد: Falcon Digital LLC\nرقم الحساب البنكي: ٩٩١١٢٢٣٣٤٤')])
    assert result['status']=='answered'
    assert '٩٩١١٢٢٣٣٤٤' in result['citations'][0]['text']


@pytest.mark.parametrize('question,line',[
    ("What is Falcon Digital's IBAN?",'IBAN: DE89 3704 0044 0532 0130 00'),
    ("What is Falcon Digital's SWIFT code?",'SWIFT: DEUTDEFF'),
    ('What is the email address for Falcon Digital?','Email: billing@falcon.example'),
    ('Phone number for Falcon Digital?','Phone: +1 202 555 0123'),
    ("What is Falcon Digital's tax registration number?",'TRN: 100200300400500'),
])
def test_requested_field_families_need_actual_labelled_values(question,line):
    positive=answer(question,[doc('Supplier: Falcon Digital\n'+line)])
    assert positive['status']=='answered'
    negative=answer(question,[doc('Supplier: Falcon Digital\nNet amount: 172800.00 AED')])
    assert negative['status']=='insufficient_evidence' and not negative['citations']


def test_invalid_iban_and_missing_second_requested_field_are_not_supported():
    assert answer("What is Falcon Digital's IBAN?",[doc('Supplier: Falcon Digital\nIBAN: DE00370400440532013000')])['status']=='insufficient_evidence'
    q="What is Falcon Digital's bank account number and SWIFT code?"
    assert answer(q,[doc('Supplier: Falcon Digital\nBank account number: 9911223344')])['status']=='insufficient_evidence'
    result=answer(q,[doc('Supplier: Falcon Digital\nBank account number: 9911223344\nSWIFT: DEUTDEFF')])
    assert result['status']=='answered' and len(result['citations'])==1


def test_multiple_suppliers_and_cross_page_provenance_remain_bound():
    mixed=doc('Supplier: Falcon Digital\nNet amount: 100 AED\nSupplier: Atlas Technology\nBank account number: 9911223344')
    assert answer(QUESTION,[mixed])['status']=='insufficient_evidence'
    separate=doc('',pages=[{'page':1,'text':'Supplier: Falcon Digital'},{'page':2,'text':'Bank account number: 9911223344'}])
    result=answer(QUESTION,[separate])
    assert result['status']=='answered'
    assert {c['page'] for c in result['citations']}=={1,2}


def test_policy_guidance_does_not_require_a_literal_account_number():
    source=doc('Supplier bank account changes require independent verification and a reviewer.',category='Policy')
    result=answer('How should supplier bank account changes be verified?',[source])
    assert result['status']=='answered' and result['citations']
    policy=doc('Bank account verification policy requires two reviewers.',category='Policy')
    assert answer('What is the policy for bank account verification?',[policy])['status']=='answered'


def test_missing_field_never_calls_embedding_or_generation_provider(monkeypatch):
    monkeypatch.setattr('uae_ai.rag.retrieval.httpx.Client',lambda *a,**k:pytest.fail('Missing evidence must not call a model'))
    settings=Settings(app_env='test',model_mode='ollama',model_url='http://127.0.0.1:11434/v1',model_name='test',retrieval_mode='hybrid',embedding_model='test')
    result=answer_question(QUESTION,[doc('Supplier: Falcon Digital\nNet amount: 172800.00 AED')],settings)
    assert result['status']=='insufficient_evidence'


def test_tenant_role_domain_version_and_withdrawal_apply_before_field_use(client):
    login(client)
    source=client.post('/api/v1/documents',files={'file':('synthetic-bank.txt',b'SYNTHETIC TEST ONLY\nSupplier: Falcon Digital\nBank account number: 9911223344','text/plain')},data={'category':'Quotation','classification':'confidential'}).json()
    query=lambda **kwargs:client.post('/api/v1/knowledge/query',json={'question':QUESTION,**kwargs}).json()
    assert query()['status']=='answered'
    assert query(domain='hr')['status']=='insufficient_evidence'
    login(client,role='requester')
    assert query()['status']=='insufficient_evidence'
    login(client,tenant='research')
    assert query()['status']=='insufficient_evidence'
    login(client)
    changed=client.post(f'/api/v1/documents/{source["id"]}/versions',data={'expected_version':'1'},files={'file':('updated.txt',b'Supplier: Falcon Digital\nBank account number: not provided','text/plain')})
    assert changed.status_code==202,changed.text
    assert query()['status']=='insufficient_evidence'
    assert client.delete(f'/api/v1/documents/{source["id"]}').status_code==204
    assert query()['status']=='insufficient_evidence'
