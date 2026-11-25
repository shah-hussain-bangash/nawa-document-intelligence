import json
import os
from pathlib import Path
import subprocess
import sys
import time
from sqlalchemy import select, update, or_, and_
from uae_ai.db import Document, User, Audit, make_database, uid
from uae_ai.core.config import Settings
from uae_ai.domain.versions import snapshot


def pending_condition():
    return or_(Document.status == "queued", and_(Document.status == "processing", Document.processing_until < int(time.time())))


def ingest(factory, settings, document_id):
    with factory() as db:
        token = uid()
        claimed = db.execute(update(Document).where(Document.id == document_id, pending_condition(), Document.processing_attempts < 3).values(status="processing", processing_token=token, processing_until=int(time.time())+300, processing_attempts=Document.processing_attempts+1))
        db.commit()
        if not claimed.rowcount:
            exhausted = db.execute(update(Document).where(Document.id == document_id, pending_condition(), Document.processing_attempts >= 3).values(status="failed", processing_token="", processing_until=0))
            db.commit()
            return
        doc = db.get(Document, document_id)
        creator = db.get(User, doc.created_by)
        if not creator or not creator.active or creator.role not in {"analyst", "admin"} or creator.tenant_id != doc.tenant_id:
            doc.status = "failed"
            doc.processing_token, doc.processing_until = "", 0
            db.commit()
            return
        version=snapshot(db,doc)
        expected_version=doc.version
        path = (settings.data_dir / "uploads" / version.storage_key).resolve()
        db.commit()  # Release snapshot writes before the isolated parser runs.
        try:
            parser_env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(Path(__file__).resolve().parents[1]), "LANG": "C.UTF-8"}
            for name in ("SystemRoot", "WINDIR", "TEMP", "TMP"):
                if name in os.environ:
                    parser_env[name] = os.environ[name]
            parser_env.update(OCR_MODE=settings.ocr_mode, OCR_LANGUAGES=settings.ocr_languages, OCR_MAX_PAGES=str(settings.ocr_max_pages), OMP_THREAD_LIMIT="1")
            result = subprocess.run([sys.executable, "-m", "uae_ai.rag.parser", str(path)], capture_output=True, text=True, encoding="utf-8", timeout=240, env=parser_env, check=True)
            parsed = json.loads(result.stdout)
            # A concurrent deletion cannot resurrect document contents.
            db.refresh(doc)
            if doc.status != "processing" or doc.version != expected_version or doc.processing_token != token:
                return
            db.refresh(creator)
            if not creator.active or creator.role not in {"analyst", "admin"} or creator.tenant_id != doc.tenant_id:
                raise ValueError("Document creator membership was revoked during extraction")
            if parsed["status"] not in {"ready", "needs_ocr"} or not isinstance(parsed["pages"], list):
                raise ValueError("Invalid parser result")
            saved = db.execute(update(Document).where(Document.id == doc.id, Document.status == "processing", Document.version == expected_version, Document.processing_token == token).values(pages=parsed["pages"], status=parsed["status"], processing_token="", processing_until=0))
            if not saved.rowcount:
                db.rollback()
                return
            db.add(Audit(tenant_id=doc.tenant_id, actor="Document worker", role="service", action="Document processed", resource=doc.title, details={"status": parsed["status"], "pages": len(parsed["pages"])}))
        except (subprocess.SubprocessError, ValueError, OSError, KeyError):
            db.refresh(doc)
            if doc.status == "processing" and doc.version == expected_version and doc.processing_token == token:
                db.execute(update(Document).where(Document.id == doc.id, Document.processing_token == token, Document.version == expected_version, Document.status == 'processing').values(status='failed', processing_token='', processing_until=0))
                db.add(Audit(tenant_id=doc.tenant_id, actor="Document worker", role="service", action="Document processing stopped", resource=doc.title, details={"attempt":doc.processing_attempts}))
        db.refresh(doc)
        if doc.status != 'deleted' and doc.version==expected_version:
            snapshot(db,doc)
        db.commit()


def main():
    settings = Settings()
    settings.validate()
    _, factory = make_database(settings.database_url)
    while True:
        with factory() as db:
            ids = db.scalars(select(Document.id).where(pending_condition()).limit(100)).all()
        for doc_id in ids:
            ingest(factory, settings, doc_id)
        time.sleep(2)


if __name__ == "__main__":
    main()

