import hashlib
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select, update
from uae_ai.core.security import current_user, get_db, scoped, can_read, require, audit
from uae_ai.db import Document, DocumentVersion, Extraction, ExtractionReview, User, uid
from uae_ai.api.workspace import row_view, document_view
from uae_ai.domain.files import read_document
from uae_ai.domain.versions import snapshot, invalidate_pending, quote_values
from uae_ai.domain.schemas import ExtractionReviewRequest
from uae_ai.worker import ingest

router=APIRouter(prefix='/api/v1',tags=['Evidence history'])


def accessible(db,id,user):
    doc=scoped(db,Document,id,user)
    if not can_read(doc,user): raise HTTPException(404,'Document not found.')
    return doc


def get_version(db,doc,number):
    row=db.scalar(select(DocumentVersion).where(DocumentVersion.document_id==doc.id,DocumentVersion.version==number,DocumentVersion.tenant_id==doc.tenant_id))
    if not row: raise HTTPException(404,'Version not found.')
    return row


@router.get('/documents/{id}/versions')
def versions(id: str,user=Depends(current_user),db=Depends(get_db)):
    doc=accessible(db,id,user)
    return [row_view(v,['tenant_id','pages','storage_key']) for v in db.scalars(select(DocumentVersion).where(DocumentVersion.document_id==doc.id).order_by(DocumentVersion.version.desc()).limit(100))]


@router.get('/documents/{id}/versions/{number}')
def version(id: str,number: int,user=Depends(current_user),db=Depends(get_db)):
    doc=accessible(db,id,user)
    row=get_version(db,doc,number)
    return {**document_view(doc),**row_view(row,['tenant_id','storage_key','id']),'page_count':len(row.pages)}


@router.get('/documents/{id}/versions/{number}/download')
def download_version(id: str,number: int,request: Request,user=Depends(current_user),db=Depends(get_db)):
    doc=accessible(db,id,user)
    row=get_version(db,doc,number)
    path=request.app.state.settings.data_dir/'uploads'/row.storage_key
    if not path.is_file(): raise HTTPException(404,'The original file is not available.')
    return FileResponse(path,filename=row.filename,media_type='application/octet-stream',headers={'Cache-Control':'no-store'})


@router.post('/documents/{id}/versions',status_code=202)
async def upload_version(id: str,request: Request,background: BackgroundTasks,expected_version: int=Form(...),file: UploadFile=File(...),user=Depends(current_user),db=Depends(get_db)):
    require(user,'analyst','admin')
    doc=accessible(db,id,user)
    if doc.version!=expected_version or doc.status in {'queued','processing'}:
        raise HTTPException(409,'The source changed or is still processing. Refresh before adding a version.')
    name,suffix,content=await read_document(file)
    snapshot(db,doc)
    next_version=doc.version+1
    key=f'{doc.id}-v{next_version}-{uid()}{suffix}'
    path=request.app.state.settings.data_dir/'uploads'/key
    claim=db.execute(update(Document).where(Document.id==id,Document.version==expected_version,Document.status==doc.status).values(version=next_version,filename=name,content_hash=hashlib.sha256(content).hexdigest(),pages=[],status='queued',size=len(content),processing_token='',processing_until=0,processing_attempts=0))
    if not claim.rowcount: raise HTTPException(409,'Another source update was accepted first.')
    try:
        with path.open('xb') as stream: stream.write(content)
        db.refresh(doc)
        snapshot(db,doc,key)
        invalidate_pending(db,doc)
        audit(db,user,'Document version added',doc.id,version=next_version)
        db.commit()
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    background.add_task(ingest,request.app.state.session_factory,request.app.state.settings,doc.id)
    return document_view(doc)


@router.get('/documents/{id}/extractions')
def extraction_history(id: str,user=Depends(current_user),db=Depends(get_db)):
    doc=accessible(db,id,user)
    rows=db.scalars(select(Extraction).join(DocumentVersion,Extraction.version_id==DocumentVersion.id).where(DocumentVersion.document_id==doc.id,Extraction.tenant_id==user.tenant_id).order_by(Extraction.created_at.desc()).limit(30)).all()
    return [{**row_view(e,['tenant_id']), 'reviews':[{**row_view(r,['tenant_id']),'actor_name':db.get(User,r.actor_id).name if db.get(User,r.actor_id) and db.get(User,r.actor_id).tenant_id==user.tenant_id else 'Former member'} for r in db.scalars(select(ExtractionReview).where(ExtractionReview.extraction_id==e.id).order_by(ExtractionReview.created_at.desc()).limit(30))]} for e in rows]


@router.post('/extractions/{id}/reviews',status_code=201)
def review_extraction(id: str,body: ExtractionReviewRequest,user=Depends(current_user),db=Depends(get_db)):
    require(user,'analyst','admin')
    extraction=scoped(db,Extraction,id,user)
    version=scoped(db,DocumentVersion,extraction.version_id,user)
    doc=accessible(db,version.document_id,user)
    if doc.version!=version.version or doc.status!='ready':
        raise HTTPException(409,'This extraction is from an outdated or unready source. Extract the current version again.')
    values=quote_values(body.values.model_dump(mode='json'))
    original={key:field['value'] for key,field in extraction.payload['fields'].items()}
    changes={key:{'before':original.get(key),'after':value} for key,value in values.items() if original.get(key)!=value}
    review=ExtractionReview(tenant_id=user.tenant_id,extraction_id=extraction.id,actor_id=user.id,values=values,changes=changes,reason=body.reason)
    db.add(review)
    audit(db,user,'Extraction review recorded',extraction.id,version=version.version,corrections=len(changes))
    db.commit()
    return row_view(review,['tenant_id'])
