from datetime import date,timedelta
from pathlib import Path
import hashlib
import pytest
from sqlalchemy import select,text
from sqlalchemy.exc import IntegrityError
from uae_ai.db import Document,DocumentVersion,Extraction,ExtractionReview
from test_workspace import app,client,login,workspace,new_case,run

TEXT=b'Supplier: Example Services\nNet amount: 12500.00 AED\nTax: 5%\nDelivery: 14 days\nValid until: 2027-12-31'


def upload(client):
    response=client.post('/api/v1/documents',files={'file':('quote.txt',TEXT,'text/plain')},data={'category':'Quotation','classification':'synthetic'})
    assert response.status_code==202,response.text
    return response.json()


def replace(client,id,version=1,content=None):
    return client.post(f'/api/v1/documents/{id}/versions',data={'expected_version':str(version)},files={'file':('updated.txt',content or TEXT.replace(b'12500',b'13000'),'text/plain')})


def draft_review(client,doc,amount='12600.00'):
    extracted=client.post(f'/api/v1/documents/{doc["id"]}/quotation-draft',json={'expected_version':doc['version']})
    assert extracted.status_code==200,extracted.text
    draft=extracted.json()
    values={k:f['value'] for k,f in draft['fields'].items()}
    values['amount']=amount
    review=client.post(f'/api/v1/extractions/{draft["extraction_id"]}/reviews',json={'values':values,'reason':'Verified the source and recorded corrected net amount.'})
    assert review.status_code==201,review.text
    return draft,review.json()


def test_versions_keep_old_pages_files_and_reject_stale_upload(client,app):
    login(client);doc=upload(client)
    before=client.get(f'/api/v1/documents/{doc["id"]}/versions/1').json()
    assert before['pages'][0]['text'].startswith('Supplier:')
    result=replace(client,doc['id']);assert result.status_code==202,result.text
    versions=client.get(f'/api/v1/documents/{doc["id"]}/versions').json()
    assert [v['version'] for v in versions]==[2,1]
    old=client.get(f'/api/v1/documents/{doc["id"]}/versions/1').json()
    assert old['pages']==before['pages']
    assert old['content_hash']==hashlib.sha256(TEXT).hexdigest()
    assert client.get(f'/api/v1/documents/{doc["id"]}/versions/1/download').content==TEXT
    assert b'13000' in client.get(f'/api/v1/documents/{doc["id"]}/versions/2/download').content
    assert replace(client,doc['id']).status_code==409
    assert len(client.get(f'/api/v1/documents/{doc["id"]}/versions').json())==2


def test_review_history_is_append_only_and_matches_case_values(client):
    login(client);doc=upload(client);draft,review=draft_review(client,doc)
    assert review['changes']['amount']=={'before':'12500.00','after':'12600.00'}
    history=client.get(f'/api/v1/documents/{doc["id"]}/extractions').json()
    assert history[0]['reviews'][0]['id']==review['id']
    assert history[0]['payload']['fields']['amount']['value']=='12500.00'
    payload={'title':'Reviewed source purchase','department':'Digital Services','budget':'20000','due_date':(date.today()+timedelta(days=10)).isoformat(),'document_ids':[doc['id']], 'quotes':[{**review['values'],'document_id':doc['id'],'source_version':1,'review_id':review['id']}]}
    created=client.post('/api/v1/cases',json=payload)
    assert created.status_code==201,created.text
    assert created.json()['evidence_versions']=={doc['id']:1}
    payload['quotes'][0]['amount']='1.00'
    assert client.post('/api/v1/cases',json=payload).status_code==409
    payload['quotes'][0]['amount']='12600.00';replace(client,doc['id'])
    assert client.post('/api/v1/cases',json=payload).status_code==409
    assert client.post(f'/api/v1/extractions/{draft["extraction_id"]}/reviews',json={'values':review['values'],'reason':'Reusing an older draft'}).status_code==409


def test_replacement_invalidates_pending_approval_and_requires_repin(client):
    login(client);case=run(client,new_case(client));source=case['document_ids'][0]
    approval=case['approval']['id'];revision=case['revision']
    result=replace(client,source);assert result.status_code==202,result.text
    current=client.get(f'/api/v1/cases/{case["id"]}').json()
    assert current['status']=='needs_information' and current['revision']>revision
    assert current['approval'] is None and current['evidence_versions'][source]==1
    assert client.post(f'/api/v1/cases/{case["id"]}/runs',headers={'Idempotency-Key':'new-version-run'}).status_code==409
    login(client,role='reviewer')
    assert client.post(f'/api/v1/approvals/{approval}/decisions',json={'expected_revision':revision,'decision':'approve','reason':'Attempted stale approval'}).status_code==409


def test_terminal_report_remains_pinned_to_old_version(client):
    login(client);case=run(client,new_case(client));source=case['document_ids'][0]
    first=client.get(f'/api/v1/report/{case["id"]}').json()['source_versions'][0]
    login(client,role='reviewer')
    decision=client.post(f'/api/v1/approvals/{case["approval"]["id"]}/decisions',json={'expected_revision':case['revision'],'decision':'approve','reason':'Independent verification complete'})
    assert decision.status_code==200,decision.text
    login(client);assert replace(client,source).status_code==202
    report=client.get(f'/api/v1/report/{case["id"]}').json()
    assert report['case']['status']=='approved_simulation'
    assert report['source_versions'][0]['content_hash']==first['content_hash']
    assert report['source_versions'][0]['version']==1
    assert client.get(f'/api/v1/report/{case["id"]}/print').status_code==200


def test_history_permissions_and_withdrawal(client,app):
    login(client);doc=upload(client);draft,review=draft_review(client,doc)
    login(client,tenant='research')
    for tail in ['versions','versions/1','versions/1/download','extractions']:
        assert client.get(f'/api/v1/documents/{doc["id"]}/{tail}').status_code==404
    assert client.post(f'/api/v1/extractions/{draft["extraction_id"]}/reviews',json={'values':review['values'],'reason':'Cross-tenant attempt'}).status_code==404
    login(client,role='reviewer');assert replace(client,doc['id']).status_code==403
    login(client);assert client.delete(f'/api/v1/documents/{doc["id"]}').status_code==204
    assert client.get(f'/api/v1/documents/{doc["id"]}/versions/1/download').status_code==404
    with app.state.session_factory() as db:
        assert db.get(Extraction,draft['extraction_id']).payload=={'withdrawn':True}
        assert db.get(ExtractionReview,review['id']).values=={}


def test_composite_database_constraints_reject_cross_tenant_version(client,app):
    login(client);doc=upload(client)
    with app.state.session_factory() as db:
        db.add(DocumentVersion(tenant_id='research',document_id=doc['id'],version=3,filename='bad.txt',content_hash='a'*64,storage_key='bad.txt',pages=[],status='ready',size=1,created_by='invalid'))
        with pytest.raises(IntegrityError):db.commit()


def test_old_schema_upgrade_backfills_versions_and_case_pins(tmp_path):
    import sqlalchemy as sa
    from alembic import command
    from uae_ai.core.migrations import config_for
    url=f'sqlite:///{tmp_path}/legacy.db'
    config=config_for(url)
    command.upgrade(config,'9abe5d076321')
    engine=sa.create_engine(url)
    metadata=sa.MetaData()
    docs=sa.Table('documents',metadata,autoload_with=engine)
    cases=sa.Table('cases',metadata,autoload_with=engine)
    with engine.begin() as connection:
        connection.execute(docs.insert().values(id='old-doc',tenant_id='tenant',created_by='actor',title='Legacy',filename='old.txt',category='Quotation',classification='synthetic',allowed_roles=['analyst'],language='en',status='ready',version=1,content_hash='a'*64,pages=[{'page':1,'text':'Old source preserved'}],size=20,source='Legacy',created_at='2026-11-01'))
        connection.execute(cases.insert().values(id='old-case',tenant_id='tenant',reference='OLD',title='Legacy case',description='',department='Test',created_by='actor',budget=100,currency='AED',due_date='2027-01-01',priority='Normal',status='draft',revision=1,document_ids=['old-doc'],quotes=[],comparison={},created_at='2026-11-01'))
    command.upgrade(config,'head')
    metadata=sa.MetaData()
    versions=sa.Table('document_versions',metadata,autoload_with=engine)
    cases=sa.Table('cases',metadata,autoload_with=engine)
    with engine.connect() as connection:
        row=connection.execute(sa.select(versions)).mappings().one()
        assert row['pages'][0]['text']=='Old source preserved' and row['storage_key']=='old-doc.txt'
        assert connection.execute(sa.select(cases.c.evidence_versions)).scalar_one()=={'old-doc':1}
    engine.dispose()


def test_local_migration_creates_readable_preupgrade_sqlite_backup(tmp_path):
    import sqlite3
    from alembic import command
    from uae_ai.core.migrations import config_for,migrate_local
    from uae_ai.db import make_database
    url=f'sqlite:///{tmp_path}/before.db'
    command.upgrade(config_for(url),'9abe5d076321')
    with sqlite3.connect(tmp_path/'before.db') as db:
        db.execute("INSERT INTO tenants (id,name) VALUES ('preserved','Before migration')")
    engine,_=make_database(url)
    migrate_local(engine,url)
    backup=list((tmp_path/'backups').glob('pre-migration-*.db'))
    assert len(backup)==1
    with sqlite3.connect(backup[0]) as db:
        assert db.execute('SELECT name FROM tenants').fetchone()[0]=='Before migration'
        assert db.execute('SELECT version_num FROM alembic_version').fetchone()[0]=='9abe5d076321'
    migrate_local(engine,url)
    assert len(list((tmp_path/'backups').glob('*.db')))==1
    engine.dispose()
