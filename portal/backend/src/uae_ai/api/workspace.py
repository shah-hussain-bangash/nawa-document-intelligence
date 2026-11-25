import hashlib
import json
import secrets
import time
from datetime import date
from pathlib import Path
from decimal import Decimal
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from uae_ai.core.security import audit, can_read, current_user, get_db, readable_documents, require, scoped
from uae_ai.db import Approval, Audit, Case, Document, DocumentVersion, Extraction, ExtractionReview, Run, Tenant, Ticket, now, uid
from uae_ai.domain.reports import render_report
from uae_ai.domain.extraction import extract_quotation
from uae_ai.domain.schemas import QuotationDraftRequest, CaseCreate, CaseEdit, Decision, Preferences, Question, TicketCreate, TicketUpdate
from uae_ai.graphs.procurement import evidence_digest, execute_graph
from uae_ai.ml.forecast import workload
from uae_ai.rag.retrieval import answer_question
from uae_ai.worker import ingest

from uae_ai.domain.versions import snapshot, current_versions, prepare_quotes, require_current_case
from uae_ai.domain.files import read_document

router = APIRouter(prefix="/api/v1", tags=["Workspace"])


def row_view(row, exclude=()):
    result = {column.name: getattr(row, column.name) for column in row.__table__.columns if column.name not in exclude}
    return {key: str(value) if isinstance(value, Decimal) else value for key, value in result.items()}


def document_view(doc):
    return {**row_view(doc, ["pages", "content_hash", "tenant_id", "processing_token", "processing_until"]), "page_count": len(doc.pages)}


def case_view(db, case, user=None):
    data = row_view(case, ["tenant_id"])
    approval = db.scalar(select(Approval).where(Approval.case_id == case.id, Approval.status == "pending").order_by(Approval.created_at.desc()))
    data["approval"] = row_view(approval) if approval else None
    if user is not None:
        permitted = []
        for doc_id in case.document_ids:
            doc = db.get(Document, doc_id)
            if doc and can_read(doc, user):
                permitted.append(doc_id)
        if len(permitted) != len(case.document_ids):
            data.update(quotes=[], comparison={}, document_ids=permitted, evidence_versions={id:v for id,v in case.evidence_versions.items() if id in permitted}, evidence_restricted=True)
    return data


def validate_evidence(db, ids, user, require_ready=False):
    for doc_id in ids:
        doc = scoped(db, Document, doc_id, user)
        if not can_read(doc, user):
            raise HTTPException(403, "One or more evidence documents are not accessible.")
        if require_ready and doc.status != "ready":
            raise HTTPException(409, "Wait until every evidence document has finished processing.")


@router.get("/workspace")
def workspace(request: Request, user=Depends(current_user), db=Depends(get_db)):
    tenant = db.get(Tenant, user.tenant_id)
    cases = db.scalars(select(Case).where(Case.tenant_id == user.tenant_id).order_by(Case.created_at.desc())).all()
    docs = readable_documents(db, user)
    runs = db.scalars(select(Run).where(Run.tenant_id == user.tenant_id).order_by(Run.created_at.desc()).limit(60)).all()
    events = db.scalars(select(Audit).where(Audit.tenant_id == user.tenant_id).order_by(Audit.created_at.desc()).limit(100)).all()
    tickets = db.scalars(select(Ticket).where(Ticket.tenant_id == user.tenant_id).order_by(Ticket.created_at.desc()).limit(100)).all()
    return {
        "tenant": row_view(tenant), "cases": [case_view(db, c, user) for c in cases],
        "documents": [document_view(d) for d in sorted(docs, key=lambda d: d.created_at, reverse=True)],
        "runs": [row_view(r, ["tenant_id", "snapshot", "request_key", "fingerprint"]) for r in runs],
        "events": [row_view(e, ["tenant_id"]) for e in events], "tickets": [row_view(t, ["tenant_id"]) for t in tickets],
        "analytics": workload(), "config": {"auth_mode": request.app.state.settings.auth_mode, "model_mode": request.app.state.settings.model_mode, "retrieval_mode": request.app.state.settings.retrieval_mode, "ocr_mode": request.app.state.settings.ocr_mode, "environment": request.app.state.settings.app_env, "database": request.app.state.engine.dialect.name},
        "stats": {"active_cases": sum(c.status not in {"approved_simulation", "rejected", "cancelled"} for c in cases), "pending_reviews": sum(c.status == "awaiting_review" for c in cases), "documents": len(docs), "completed": sum(c.status == "approved_simulation" for c in cases), "budget": str(sum((c.budget for c in cases), Decimal("0")))},
    }


@router.get("/cases")
def list_cases(user=Depends(current_user), db=Depends(get_db)):
    return [case_view(db, c, user) for c in db.scalars(select(Case).where(Case.tenant_id == user.tenant_id).order_by(Case.created_at.desc())).all()]


@router.post("/cases", status_code=201)
def create_case(body: CaseCreate, user=Depends(current_user), db=Depends(get_db)):
    require(user, "analyst", "requester", "admin")
    validate_evidence(db, body.document_ids, user)
    for quote in body.quotes:
        if quote.document_id not in body.document_ids:
            raise HTTPException(422, "Every quotation must reference an attached evidence document.")
    case_id = uid()
    values = body.model_dump(mode="json")
    values['quotes']=prepare_quotes(db,body.quotes,user)
    values['evidence_versions']=current_versions(db,body.document_ids,user)
    case = Case(id=case_id, tenant_id=user.tenant_id, reference=f"PR-{date.today().year}-{case_id[:6].upper()}", created_by=user.id, status="draft", revision=1, **values)
    db.add(case)
    audit(db, user, "Procurement case created", case.reference)
    db.commit()
    return case_view(db, case)


@router.get("/cases/{case_id}")
def get_case(case_id: str, user=Depends(current_user), db=Depends(get_db)):
    return case_view(db, scoped(db, Case, case_id, user), user)


@router.patch("/cases/{case_id}")
def edit_case(case_id: str, body: CaseEdit, user=Depends(current_user), db=Depends(get_db)):
    require(user, "analyst", "admin")
    case = scoped(db, Case, case_id, user)
    if case.status in {"approved_simulation", "rejected", "cancelled", "processing"}:
        raise HTTPException(409, "This case is locked. Create a new case for a different outcome.")
    validate_evidence(db, body.document_ids, user)
    if any(q.document_id not in body.document_ids for q in body.quotes):
        raise HTTPException(422, "Every quotation must reference attached evidence.")
    result = db.execute(update(Case).where(Case.id == case.id, Case.revision == body.expected_revision).values(document_ids=body.document_ids, quotes=prepare_quotes(db,body.quotes,user), evidence_versions=current_versions(db,body.document_ids,user), revision=Case.revision + 1, status="draft", comparison={}))
    if not result.rowcount:
        raise HTTPException(409, "The case changed. Refresh before saving.")
    db.execute(update(Approval).where(Approval.case_id == case.id, Approval.status == "pending").values(status="invalidated"))
    audit(db, user, "Case evidence revised", case.reference, previous_revision=body.expected_revision)
    db.commit()
    db.refresh(case)
    return case_view(db, case)


@router.post("/cases/{case_id}/runs")
def run_case(case_id: str, idempotency_key: str = Header(min_length=8, max_length=120), user=Depends(current_user), db=Depends(get_db)):
    require(user, "analyst", "admin")
    case = scoped(db, Case, case_id, user)
    validate_evidence(db, case.document_ids, user, require_ready=True)
    require_current_case(db,case)
    key = hashlib.sha256(f"{user.tenant_id}:{user.id}:{idempotency_key}".encode()).hexdigest()
    fingerprint = evidence_digest(db, case)
    execution_token = uid()
    existing = db.scalar(select(Run).where(Run.request_key == key))
    if existing:
        if existing.case_id != case.id or existing.fingerprint != fingerprint:
            raise HTTPException(409, "This request key was already used for different evidence.")
        if existing.status != "processing":
            return {"case": case_view(db, case), "run": row_view(existing)}
        claim = db.execute(update(Run).where(Run.id == existing.id, Run.status == 'processing', Run.execution_until < int(time.time())).values(execution_token=execution_token, execution_until=int(time.time())+60, steps=[]))
        if not claim.rowcount or case.status != 'processing':
            db.rollback()
            raise HTTPException(409, 'This workflow is still running. Retry after its execution lease expires if it was interrupted.')
        run = existing  # Replays deterministic nodes only; no external side effects.
    else:
        if case.status not in {"draft", "needs_information", "failed"}:
            raise HTTPException(409, "This case is already in review, running, or complete.")
        claim = db.execute(update(Case).where(Case.id == case.id, Case.revision == case.revision, Case.status == case.status).values(status="processing"))
        if not claim.rowcount:
            raise HTTPException(409, "Another run already claimed this case.")
        run = Run(tenant_id=user.tenant_id, case_id=case.id, actor_id=user.id, request_key=key, fingerprint=fingerprint, revision=case.revision, status="processing", snapshot=fingerprint, steps=[], execution_token=execution_token, execution_until=int(time.time())+60)
        db.add(run)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This run request is already being handled.") from None
    try:
        result = execute_graph(db, case, run)
    except Exception:
        db.rollback()
        db.refresh(run)
        stopped = db.execute(update(Run).where(Run.id == run.id, Run.execution_token == execution_token, Run.status == 'processing').values(status='failed', execution_token='', execution_until=0))
        if stopped.rowcount:
            db.execute(update(Case).where(Case.id == case.id, Case.revision == run.revision, Case.status == "processing").values(status="failed"))
        db.commit()
        raise HTTPException(503, "The workflow stopped safely. Retry with the same request key to inspect the result.") from None
    db.refresh(case)
    db.refresh(user)
    if not user.active or user.role not in {'analyst','admin'} or user.tenant_id != case.tenant_id or evidence_digest(db, case) != fingerprint or case.status != "processing":
        stopped = db.execute(update(Run).where(Run.id == run.id, Run.execution_token == execution_token, Run.status == 'processing').values(status='cancelled', execution_token='', execution_until=0))
        if stopped.rowcount:
            db.execute(update(Case).where(Case.id == case.id, Case.revision == run.revision, Case.status == 'processing').values(status='needs_information'))
        db.commit()
        raise HTTPException(409, "The evidence or workflow state changed; this run was stopped.")
    state = "needs_information" if result["issues"] else "awaiting_review"
    owned = db.execute(update(Run).where(Run.id == run.id, Run.execution_token == execution_token, Run.status == 'processing').values(status=state, execution_token='', execution_until=0))
    saved = db.execute(update(Case).where(Case.id == case.id, Case.revision == run.revision, Case.status == 'processing').values(status=state, comparison=result))
    if not owned.rowcount or not saved.rowcount:
        db.rollback()
        raise HTTPException(409, 'This run lost its execution lease or its case changed. Refresh before continuing.')
    if state == "awaiting_review":
        db.add(Approval(tenant_id=user.tenant_id, case_id=case.id, run_id=run.id, revision=case.revision, snapshot=fingerprint, requested_by=user.id, status="pending"))
    audit(db, user, "Workflow completed", case.reference, outcome=state, steps=len(run.steps))
    db.commit()
    return {"case": case_view(db, case), "run": row_view(run)}


@router.post("/approvals/{approval_id}/decisions")
def decide(approval_id: str, body: Decision, user=Depends(current_user), db=Depends(get_db)):
    require(user, "reviewer", "admin")
    approval = scoped(db, Approval, approval_id, user)
    case = scoped(db, Case, approval.case_id, user)
    if approval.requested_by == user.id:
        raise HTTPException(403, "Independent review is required; you cannot approve your own request.")
    outcome = {"approve": "approved", "reject": "rejected", "request_changes": "changes_requested"}[body.decision]
    if approval.status != "pending":
        if approval.status == outcome and approval.decision_by == user.id and approval.reason == body.reason and approval.revision == body.expected_revision:
            return case_view(db, case)
        raise HTTPException(409, "This approval has already been decided or invalidated.")
    validate_evidence(db, case.document_ids, user, require_ready=True)
    require_current_case(db,case)
    if body.expected_revision != case.revision or approval.revision != case.revision or approval.snapshot != evidence_digest(db, case):
        raise HTTPException(409, "Evidence changed. A new comparison and review are required.")
    claimed = db.execute(update(Approval).where(Approval.id == approval.id, Approval.status == "pending").values(status=outcome, decision_by=user.id, reason=body.reason, decided_at=now()))
    new_status = {"approve": "approved_simulation", "reject": "rejected", "request_changes": "needs_information"}[body.decision]
    changed = db.execute(update(Case).where(Case.id == case.id, Case.revision == body.expected_revision, Case.status == "awaiting_review").values(status=new_status))
    if not claimed.rowcount or not changed.rowcount:
        db.rollback()
        raise HTTPException(409, "Another decision or revision has already changed this review.")
    db.execute(update(Run).where(Run.id == approval.run_id).values(status=new_status))
    audit(db, user, "Review decision recorded", case.reference, decision=body.decision, revision=case.revision)
    db.commit()
    db.refresh(case)
    return case_view(db, case)


@router.get("/documents")
def list_documents(user=Depends(current_user), db=Depends(get_db)):
    return [document_view(d) for d in readable_documents(db, user)]


@router.post("/documents", status_code=202)
async def upload_document(request: Request, background: BackgroundTasks, file: UploadFile = File(...), category: str = Form("Policy"), classification: str = Form("internal"), user=Depends(current_user), db=Depends(get_db)):
    require(user, "analyst", "admin")
    if category not in {"Policy", "Procurement", "Quotation", "HR", "Service desk"} or classification not in {"synthetic", "internal", "confidential"}:
        raise HTTPException(422, "Unsupported category or classification.")
    name, suffix, content = await read_document(file)
    doc_id = uid()
    settings = request.app.state.settings
    path = settings.data_dir / "uploads" / (doc_id + suffix)
    path.write_bytes(content)
    roles = ["analyst", "reviewer", "admin"] if classification == "confidential" else ["analyst", "requester", "reviewer", "auditor", "admin"]
    doc = Document(id=doc_id, tenant_id=user.tenant_id, created_by=user.id, title=name, filename=name, category=category, classification=classification, allowed_roles=roles, status="queued", version=1, content_hash=hashlib.sha256(content).hexdigest(), pages=[], size=len(content), language="ar" if any("\u0600" <= c <= "\u06ff" for c in name) else "en", source="Authorised user upload")
    db.add(doc)
    db.flush()
    snapshot(db,doc)
    audit(db, user, "Document uploaded", name, classification=classification)
    db.commit()
    background.add_task(ingest, request.app.state.session_factory, settings, doc.id)
    return document_view(doc)


@router.get("/documents/{document_id}")
def get_document(document_id: str, user=Depends(current_user), db=Depends(get_db)):
    doc = scoped(db, Document, document_id, user)
    if not can_read(doc, user):
        raise HTTPException(404, "Document not found.")
    return {**document_view(doc), "pages": doc.pages}


@router.get("/documents/{document_id}/download")
def download(document_id: str, request: Request, user=Depends(current_user), db=Depends(get_db)):
    doc = scoped(db, Document, document_id, user)
    if not can_read(doc, user):
        raise HTTPException(404, "Document not found.")
    suffix = ".pdf" if doc.filename.lower().endswith(".pdf") else ".txt"
    version = snapshot(db,doc)
    path = request.app.state.settings.data_dir / "uploads" / version.storage_key
    if not path.is_file():
        raise HTTPException(404, "The source file is not available.")
    return FileResponse(path, filename=doc.filename, media_type="application/octet-stream", headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"})


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: str, request: Request, user=Depends(current_user), db=Depends(get_db)):
    require(user, "analyst", "admin")
    doc = scoped(db, Document, document_id, user)
    if not can_read(doc, user):
        raise HTTPException(404, "Document not found.")
    doc.status, doc.pages = "deleted", []
    versions=db.scalars(select(DocumentVersion).where(DocumentVersion.document_id==doc.id)).all()
    for version in versions:
        version.status,version.pages='deleted',[]
        (request.app.state.settings.data_dir/'uploads'/version.storage_key).unlink(missing_ok=True)
        for extraction in db.scalars(select(Extraction).where(Extraction.version_id==version.id)).all():
            extraction.payload={'withdrawn':True}
            for review in db.scalars(select(ExtractionReview).where(ExtractionReview.extraction_id==extraction.id)).all():
                review.values,review.changes={},{}
                review.reason='[Source withdrawn]'
    for case in db.scalars(select(Case).where(Case.tenant_id == user.tenant_id)).all():
        if document_id in case.document_ids and case.status == "awaiting_review":
            db.execute(update(Approval).where(Approval.case_id == case.id, Approval.status == "pending").values(status="invalidated"))
            case.status = "needs_information"
            case.comparison = {}
            case.revision += 1
    audit(db, user, "Document withdrawn", doc.title)
    db.commit()
    for suffix in [".pdf", ".txt"]:
        (request.app.state.settings.data_dir / "uploads" / (doc.id + suffix)).unlink(missing_ok=True)


@router.post("/documents/{document_id}/retry", status_code=202)
def retry_document(document_id: str, request: Request, background: BackgroundTasks, user=Depends(current_user), db=Depends(get_db)):
    require(user, "analyst", "admin")
    doc = scoped(db, Document, document_id, user)
    if not can_read(doc, user) or doc.status not in {"failed", "queued", "needs_ocr"}:
        raise HTTPException(409, "This document cannot be retried in its current state.")
    doc.status, doc.processing_attempts = "queued", 0
    audit(db, user, 'Document processing retried', doc.title)
    db.commit()
    background.add_task(ingest, request.app.state.session_factory, request.app.state.settings, doc.id)
    return document_view(doc)


@router.post("/knowledge/query")
def knowledge(body: Question, request: Request, user=Depends(current_user), db=Depends(get_db)):
    result = answer_question(body.question, readable_documents(db, user), request.app.state.settings, body.domain)
    audit(db, user, "Knowledge search completed", "evidence-library", mode=result["mode"], citations=len(result["citations"]), answer_status=result['status'], reason=result.get('reason'), requested_fields=result.get('requested_fields', []))
    db.commit()
    return result


@router.get("/system/capabilities")
def system_capabilities(request: Request, user=Depends(current_user)):
    from uae_ai.rag.ocr import capabilities
    settings = request.app.state.settings
    return {"ocr": {**capabilities(settings.ocr_languages), "mode": settings.ocr_mode, "max_pages": settings.ocr_max_pages},
            "retrieval": {"mode": settings.retrieval_mode, "capacity": settings.retrieval_max_chunks, "live_model_verified": False},
            "identity": {"mode": settings.auth_mode},
            "notice": "Configuration and OCR executable availability are shown here. Live identity/model checks and production acceptance are separate."}


@router.post("/tickets", status_code=201)
def create_ticket(body: TicketCreate, user=Depends(current_user), db=Depends(get_db)):
    require(user, "analyst", "requester", "reviewer", "admin")
    ticket = Ticket(tenant_id=user.tenant_id, created_by=user.name, **body.model_dump())
    db.add(ticket)
    audit(db, user, "Service request created", body.title)
    db.commit()
    return row_view(ticket, ["tenant_id"])


@router.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: str, body: TicketUpdate, user=Depends(current_user), db=Depends(get_db)):
    require(user, "analyst", "admin")
    ticket = scoped(db, Ticket, ticket_id, user)
    ticket.status = body.status
    audit(db, user, "Service request updated", ticket.title, status=body.status)
    db.commit()
    return row_view(ticket, ["tenant_id"])


@router.put("/preferences")
def preferences(body: Preferences, user=Depends(current_user), db=Depends(get_db)):
    user.preferences = body.model_dump()
    db.commit()
    return user.preferences


@router.get("/audit")
def list_audit(limit: int = 50, user=Depends(current_user), db=Depends(get_db)):
    limit = max(1, min(limit, 100))
    return [row_view(e, ["tenant_id"]) for e in db.scalars(select(Audit).where(Audit.tenant_id == user.tenant_id).order_by(Audit.created_at.desc()).limit(limit)).all()]


@router.get("/report/{case_id}")
def report(case_id: str, user=Depends(current_user), db=Depends(get_db)):
    case = scoped(db, Case, case_id, user)
    validate_evidence(db, case.document_ids, user)
    payload = {"notice": "SYNTHETIC SANDBOX — SIMULATED PROCUREMENT REPORT", "generated_at": now(), "case": case_view(db, case), "source_versions": [row_view(db.scalar(select(DocumentVersion).where(DocumentVersion.document_id==id,DocumentVersion.version==case.evidence_versions.get(id,db.get(Document,id).version))), ['tenant_id','pages','storage_key']) for id in case.document_ids], "approvals": [row_view(a) for a in db.scalars(select(Approval).where(Approval.case_id == case.id)).all()]}
    audit(db, user, "Case report exported", case.reference)
    db.commit()
    return Response(json.dumps(payload, indent=2, default=str), media_type="application/json", headers={"Content-Disposition": f'attachment; filename="{case.reference}-report.json"', "Cache-Control": "no-store"})



@router.get("/report/{case_id}/print", response_class=HTMLResponse)
def printable_report(case_id: str, user=Depends(current_user), db=Depends(get_db)):
    # Reuse the JSON export's complete object and source permission checks + audit.
    result = report(case_id, user, db)
    payload = json.loads(result.body)
    from types import SimpleNamespace
    documents = [SimpleNamespace(title=db.get(Document,v['document_id']).title, version=v['version'], content_hash=v['content_hash']) for v in payload['source_versions']]
    return HTMLResponse(render_report(payload, documents), headers={
        "Cache-Control": "no-store",
        "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-hashes' 'sha256-MguIPR6qNR8D3B+eAlK+bIRTZe8t3wkOY4B/56Me9FU='; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
    })


@router.post("/documents/{document_id}/quotation-draft")
def quotation_draft(document_id: str, body: QuotationDraftRequest, user=Depends(current_user), db=Depends(get_db)):
    require(user, "analyst", "admin")
    doc = scoped(db, Document, document_id, user)
    if not can_read(doc, user):
        raise HTTPException(404, "Document not found.")
    if doc.version != body.expected_version:
        raise HTTPException(409, "The source version changed. Refresh and review the current document.")
    if doc.status != "ready":
        raise HTTPException(409, "The source is not ready. Complete processing or provide text/OCR first.")
    result = extract_quotation(doc)
    version=snapshot(db,doc)
    extraction=Extraction(tenant_id=user.tenant_id,version_id=version.id,actor_id=user.id,extractor_version=result['extractor_version'],payload=result)
    db.add(extraction)
    db.flush()
    result={**result,'extraction_id':extraction.id}
    audit(db, user, "Quotation draft extracted", doc.id, version=doc.version, extractor=result["extractor_version"], found=sum(f["status"] == "found" for f in result["fields"].values()))
    db.commit()
    return result
