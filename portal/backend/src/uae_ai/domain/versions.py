"""Evidence version snapshots and source-bound extraction review checks."""
from pathlib import Path
from decimal import Decimal
from uuid import uuid5, NAMESPACE_URL
from sqlalchemy import select, update
from fastapi import HTTPException
from uae_ai.db import Document, DocumentVersion, Extraction, ExtractionReview, Case, Approval, Run


def snapshot(db, doc, storage_key=None):
    row = db.scalar(select(DocumentVersion).where(DocumentVersion.document_id==doc.id, DocumentVersion.version==doc.version))
    if row is None:
        row = DocumentVersion(id=str(uuid5(NAMESPACE_URL, f'nawa:{doc.id}:v{doc.version}')), tenant_id=doc.tenant_id,
            document_id=doc.id, version=doc.version, filename=doc.filename, content_hash=doc.content_hash,
            storage_key=storage_key or doc.id+Path(doc.filename).suffix.lower(), pages=doc.pages,
            status=doc.status, size=doc.size, created_by=doc.created_by, created_at=doc.created_at)
        db.add(row)
        db.flush()
    elif row.status != 'ready' and row.content_hash == doc.content_hash:
        row.pages, row.status = doc.pages, doc.status
    return row


def current_versions(db, ids, user):
    result={}
    for id in ids:
        doc=db.get(Document,id)
        if not doc or doc.tenant_id!=user.tenant_id:
            raise HTTPException(404,'Source not found.')
        snapshot(db,doc)
        result[id]=doc.version
    return result


def quote_values(quote):
    result={k:str(quote[k]) if quote.get(k) is not None else None for k in ['supplier','amount','currency','tax_percent','delivery_days','valid_until']}
    for key in ['amount','tax_percent']:
        if result[key] is not None: result[key]=format(Decimal(result[key]),'.2f')
    return result


def prepare_quotes(db, quotes, user):
    result=[]
    for item in quotes:
        q=item.model_dump(mode='json')
        doc=db.get(Document,q['document_id'])
        if q.get('source_version') not in {None, doc.version}:
            raise HTTPException(409,'A quotation uses an older source version. Review the latest evidence before saving.')
        q['source_version']=doc.version
        if q.get('review_id'):
            review=db.get(ExtractionReview,q['review_id'])
            extraction=db.get(Extraction,review.extraction_id) if review else None
            version=db.get(DocumentVersion,extraction.version_id) if extraction else None
            if not review or review.tenant_id!=user.tenant_id or not version or version.document_id!=doc.id or version.version!=doc.version or review.values!=quote_values(q):
                raise HTTPException(409,'The reviewed draft no longer matches this quotation or source. Review again or enter values manually.')
        result.append(q)
    return result


def require_current_case(db, case):
    for id in case.document_ids:
        doc=db.get(Document,id)
        if doc and case.evidence_versions.get(id,doc.version)!=doc.version:
            raise HTTPException(409,'Evidence has a newer version. Edit and save the case against current sources before comparison.')


def invalidate_pending(db, doc):
    for case in db.scalars(select(Case).where(Case.tenant_id==doc.tenant_id)).all():
        if doc.id in case.document_ids and case.status not in {'approved_simulation','rejected','cancelled'}:
            db.execute(update(Approval).where(Approval.case_id==case.id,Approval.status=='pending').values(status='invalidated'))
            db.execute(update(Run).where(Run.case_id==case.id,Run.status.in_(['awaiting_review','processing'])).values(status='cancelled'))
            case.status='needs_information'
            case.comparison={}
            case.revision+=1


def bootstrap_versions(db):
    for doc in db.scalars(select(Document)).all():
        snapshot(db,doc)
    for case in db.scalars(select(Case)).all():
        if not case.evidence_versions:
            case.evidence_versions={id:db.get(Document,id).version for id in case.document_ids if db.get(Document,id)}
    db.commit()
