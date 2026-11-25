"""Exercise the real parser subprocess with Windows-style redirected encodings."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from uae_ai.rag.ocr import capabilities
from uae_ai.db import Document
from test_workspace import app, client, login

ROOT = Path(__file__).resolve().parents[2]


def run_parser(path, encoding):
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "backend/src"),
        "PYTHONIOENCODING": encoding,
        "OCR_MODE": "auto",
        "OCR_LANGUAGES": "eng+ara",
        "OMP_THREAD_LIMIT": "1",
    }
    result = subprocess.run(
        [sys.executable, "-m", "uae_ai.rag.parser", str(path)],
        env=env, capture_output=True, timeout=120, check=True,
    )
    # Match the worker's UTF-8 reader even when the child's stdout uses cp1252.
    return json.loads(result.stdout.decode("utf-8"))


@pytest.mark.parametrize("encoding", ["cp1252", "ascii", "utf-8"])
def test_parser_round_trips_unicode_through_redirected_stdout(tmp_path, encoding):
    text = "المورد: شركة تجريبية\nSupplier: Example — quotation 😀\n"
    source = tmp_path / "source.txt"
    source.write_text(text, encoding="utf-8")
    result = run_parser(source, encoding)
    assert result["status"] == "ready"
    assert result["pages"][0]["text"] == text


@pytest.mark.parametrize("language, expected", [("en", "12500"), ("ar", "المورد")])
def test_scanned_pdf_parser_with_legacy_stdout(language, expected):
    if not capabilities()["ready"]:
        pytest.skip("Tesseract and Poppler are optional system dependencies")
    result = run_parser(ROOT / f"data/samples/scanned-quotation-{language}.pdf", "cp1252")
    assert result["status"] == "ready"
    assert result["pages"][0]["method"] == "ocr"
    assert expected in result["pages"][0]["text"]


def test_retry_existing_arabic_scan_preserves_source_under_legacy_stdout(client, app, monkeypatch):
    if not capabilities()["ready"]:
        pytest.skip("Tesseract and Poppler are optional system dependencies")
    original_run = subprocess.run

    def legacy_output(args, **kwargs):
        if "uae_ai.rag.parser" in args:
            kwargs["env"] = {**kwargs["env"], "PYTHONIOENCODING": "cp1252"}
        return original_run(args, **kwargs)

    monkeypatch.setattr("uae_ai.worker.subprocess.run", legacy_output)
    login(client)
    contents = (ROOT / "data/samples/scanned-quotation-ar.pdf").read_bytes()
    response = client.post("/api/v1/documents", data={"category": "Quotation", "classification": "synthetic"},
                           files={"file": ("scanned-quotation-ar.pdf", contents, "application/pdf")})
    assert response.status_code == 202
    document_id = response.json()["id"]
    before = client.get(f"/api/v1/documents/{document_id}").json()
    assert before["status"] == "ready"
    with app.state.session_factory() as db:
        doc = db.get(Document, document_id)
        doc.status, doc.pages = "failed", []
        db.commit()
    assert client.post(f"/api/v1/documents/{document_id}/retry").status_code == 202
    after = client.get(f"/api/v1/documents/{document_id}").json()
    assert after["status"] == "ready" and "المورد" in after["pages"][0]["text"]
    assert after["version"] == before["version"]
    assert client.get(f"/api/v1/documents/{document_id}/versions/1/download").content == contents
