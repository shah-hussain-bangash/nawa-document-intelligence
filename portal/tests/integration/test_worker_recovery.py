import json
import time
from types import SimpleNamespace
from sqlalchemy import select
from uae_ai.db import Document, User
from uae_ai.worker import ingest
from test_workspace import app, client, login


def source(client):
    login(client)
    response=client.post('/api/v1/documents',files={'file':('queued.txt',b'Original recoverable source','text/plain')})
    assert response.status_code==202
    return response.json()['id']


def test_expired_worker_lease_recovers_without_competing_for_live_work(client,app,monkeypatch):
    id=source(client)
    with app.state.session_factory() as db:
        doc=db.get(Document,id)
        doc.status='processing';doc.processing_token='old-worker';doc.processing_until=int(time.time())+100;doc.processing_attempts=1
        db.commit()
    calls=[]
    def parsed(*args,**kwargs):
        calls.append(True)
        return SimpleNamespace(stdout=json.dumps({'pages':[{'page':1,'text':'Recovered source'}],'status':'ready'}))
    monkeypatch.setattr('uae_ai.worker.subprocess.run',parsed)
    ingest(app.state.session_factory,app.state.settings,id)
    assert calls==[]
    with app.state.session_factory() as db:
        db.get(Document,id).processing_until=0;db.commit()
    ingest(app.state.session_factory,app.state.settings,id)
    with app.state.session_factory() as db:
        doc=db.get(Document,id)
        assert doc.status=='ready' and doc.processing_token=='' and doc.processing_attempts==2
    assert len(calls)==1


def test_exhausted_retries_stop_and_manual_retry_is_explicit(client,app):
    id=source(client)
    with app.state.session_factory() as db:
        doc=db.get(Document,id);doc.status='processing';doc.processing_until=0;doc.processing_attempts=3;db.commit()
    ingest(app.state.session_factory,app.state.settings,id)
    assert client.get(f'/api/v1/documents/{id}').json()['status']=='failed'
    assert client.post(f'/api/v1/documents/{id}/retry').status_code==202
    value=client.get(f'/api/v1/documents/{id}').json()
    assert value['status']=='ready' and value['processing_attempts']==1


def test_worker_cannot_resurrect_withdrawn_source_or_finish_revoked_membership(client,app,monkeypatch):
    id=source(client)
    with app.state.session_factory() as db:
        doc=db.get(Document,id);doc.status='queued';doc.processing_attempts=0;db.commit()
    def revoked(*args,**kwargs):
        with app.state.session_factory() as db:
            db.get(User,'operations-analyst').active=False;db.commit()
        return SimpleNamespace(stdout=json.dumps({'pages':[{'page':1,'text':'Must not be persisted'}],'status':'ready'}))
    monkeypatch.setattr('uae_ai.worker.subprocess.run',revoked)
    ingest(app.state.session_factory,app.state.settings,id)
    with app.state.session_factory() as db:
        assert db.get(Document,id).status=='failed'
        assert 'Must not' not in json.dumps(db.get(Document,id).pages)
