import hashlib
import time
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from uae_ai.db import Case, Run, Approval
from uae_ai.graphs.procurement import evidence_digest, compare_quotes
from test_workspace import app,client,login,new_case


def test_interrupted_run_can_replay_only_after_lease_expiry(client,app):
    login(client);case=new_case(client);request_key='interrupted-run-synthetic'
    key=hashlib.sha256(('operations:operations-analyst:'+request_key).encode()).hexdigest()
    with app.state.session_factory() as db:
        saved=db.get(Case,case['id']);saved.status='processing'
        fingerprint=evidence_digest(db,saved)
        job=Run(tenant_id='operations',case_id=saved.id,actor_id='operations-analyst',request_key=key,fingerprint=fingerprint,revision=saved.revision,status='processing',snapshot=fingerprint,steps=[],execution_token='dead-worker',execution_until=int(time.time())+60)
        db.add(job);db.commit();id=job.id
    route=f'/api/v1/cases/{case["id"]}/runs'
    assert client.post(route,headers={'Idempotency-Key':request_key}).status_code==409
    with app.state.session_factory() as db:
        db.get(Run,id).execution_until=0;db.commit()
    response=client.post(route,headers={'Idempotency-Key':request_key})
    assert response.status_code==200,response.text
    assert response.json()['case']['status']=='awaiting_review'
    with app.state.session_factory() as db:
        job=db.get(Run,id)
        assert len(job.steps)==3 and job.execution_token==''
        approvals=db.scalars(select(Approval).where(Approval.run_id==id)).all()
        assert len(approvals)==1
        original=approvals[0]
        db.add(Approval(tenant_id=original.tenant_id,case_id=original.case_id,run_id=id,revision=1,snapshot=fingerprint,requested_by='operations-analyst'))
        with pytest.raises(IntegrityError):db.commit()


def test_stale_executor_cannot_publish_after_lease_reclaimed(client,app,monkeypatch):
    login(client);case=new_case(client)
    def reclaimed(db,case,run):
        with app.state.session_factory() as other:
            other.get(Run,run.id).execution_token='replacement-worker';other.commit()
        return compare_quotes(case)
    monkeypatch.setattr('uae_ai.api.workspace.execute_graph',reclaimed)
    response=client.post(f'/api/v1/cases/{case["id"]}/runs',headers={'Idempotency-Key':'stale-executor-key'})
    assert response.status_code==409,response.text
    with app.state.session_factory() as db:
        assert db.get(Case,case['id']).status=='processing'
        assert db.scalar(select(Approval).where(Approval.case_id==case['id'])) is None
