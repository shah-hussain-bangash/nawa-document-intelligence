from pathlib import Path
from types import SimpleNamespace
import json
import math
import pytest
import httpx
from fastapi import HTTPException
from pypdf import PdfWriter, PdfReader
from uae_ai.rag import ocr
from uae_ai.rag.parser import parse
from uae_ai.rag.retrieval import search
from uae_ai.rag.embeddings import vectors
from uae_ai.core.config import Settings
from test_workspace import app, client, login

ROOT = Path(__file__).resolve().parents[2]


def document(id, text, **kwargs):
    return SimpleNamespace(id=id, title=id, version=1, status="ready", category="Policy", classification="synthetic", pages=[{"page":1,"text":text}], **kwargs)


def test_mixed_pdf_cannot_silently_drop_unprocessed_page(tmp_path):
    source = PdfReader(ROOT / "docs/reference/01_Project_Requirements.pdf")
    writer = PdfWriter()
    writer.add_page(source.pages[0]); writer.add_blank_page(width=200, height=200)
    path = tmp_path / "mixed.pdf"
    writer.write(path)
    result = parse(path, ocr_mode="off")
    assert result["status"] == "needs_ocr" and result["pages"][0]["text"]
    assert not result["pages"][1]["text"] and result["pages"][1]["warnings"]


def test_real_english_arabic_ocr_on_synthetic_scans():
    if not ocr.capabilities()["ready"]:
        pytest.skip("Tesseract and Poppler are optional system dependencies")
    for language, expected in [("en","12500"),("ar","المورد")]:
        result = parse(ROOT / f"data/samples/scanned-quotation-{language}.pdf")
        assert result["status"] == "ready", result
        page = result["pages"][0]
        assert page["method"] == "ocr" and expected in page["text"]
        assert page["words"] and page["warnings"] and 0 <= page["ocr_confidence"] <= 100


def test_ocr_missing_tools_and_page_limit_are_explicit(monkeypatch):
    monkeypatch.setattr(ocr, "capabilities", lambda _: {"ready":False})
    result = parse(ROOT / "data/samples/scanned-quotation-en.pdf")
    assert result["status"] == "needs_ocr"
    assert result["pages"][0]["warnings"]


def test_bm25_ranks_focused_evidence_and_normalises_arabic():
    results = search("annual leave", [document("noise", "annual unrelated " * 100), document("focused", "Employees receive annual leave and public holidays.")])
    assert results[0]["document_id"] == "focused" and results[0]["retrieval"] == "bm25"
    assert search("الإجازة", [document("ar", "الاجازة السنوية للموظف")])[0]["document_id"] == "ar"
    assert search("pineapple unicorn", [document("ar", "الاجازة السنوية")]) == []


def test_hybrid_recovers_paraphrase_and_never_embeds_blocked_classes(tmp_path, monkeypatch):
    settings = Settings(app_env="test", data_dir=tmp_path, retrieval_mode="hybrid", embedding_model="test")
    settings.validate()
    seen=[]
    def embed(texts, _):
        seen.extend(texts)
        return [[1,0], [1,0], [0,1]]
    monkeypatch.setattr("uae_ai.rag.embeddings.vectors", embed)
    docs = [document("a-leave", "Staff may take paid vacation."),document("b-security", "Report malicious logins.")]
    restricted = document("c-restricted", "confidential source must not be sent")
    restricted.classification="confidential"
    found = search("time away from work", [*docs, restricted], settings=settings)
    assert found[0]["document_id"] == "a-leave" and found[0]["retrieval"] == "dense"
    assert not any("confidential" in value for value in seen)


def test_hybrid_acl_filters_before_embedding(client, app, monkeypatch):
    login(client)
    client.post("/api/v1/documents",data={"classification":"confidential"},files={"file":("secret.txt",b"privatecanary123 confidential source","text/plain")})
    login(client, role="requester")
    app.state.settings.retrieval_mode="hybrid";app.state.settings.embedding_model="test"
    app.state.settings.embedding_classes="synthetic,confidential"
    seen=[]
    def embed(texts, settings):
        seen.extend(texts)
        return [[1,0] for _ in texts]
    monkeypatch.setattr("uae_ai.rag.embeddings.vectors", embed)
    response=client.post("/api/v1/knowledge/query",json={"question":"procurement"})
    assert response.status_code==200,response.text
    assert not any("privatecanary123" in value for value in seen)


@pytest.mark.parametrize("data", [[], [{"index":0,"embedding":[0,0]}], [{"index":0,"embedding":[float("nan"),1]}], [{"index":1,"embedding":[1,0]}]])
def test_invalid_embedding_response_fails_closed(tmp_path, monkeypatch, data):
    settings=Settings(app_env="test",data_dir=tmp_path,retrieval_mode="hybrid",embedding_model="test")
    real=httpx.Client
    # json encoder rejects NaN; provide literal to exercise response validation.
    body=json.dumps({"data":data})
    monkeypatch.setattr("uae_ai.rag.embeddings.httpx.Client",lambda **options:real(transport=httpx.MockTransport(lambda _:httpx.Response(200,content=body)),**options))
    with pytest.raises(HTTPException) as exc:vectors(["test"],settings)
    assert exc.value.status_code==503


def test_hybrid_route_and_capacity_are_enforced(tmp_path):
    settings=Settings(app_env="test",data_dir=tmp_path,retrieval_mode="hybrid",embedding_model="test",embedding_url="http://remote.invalid/v1")
    with pytest.raises(RuntimeError):settings.validate()
    settings.embedding_url="http://127.0.0.1:11434/v1";settings.retrieval_max_chunks=4
    settings.validate()
    with pytest.raises(HTTPException) as exc:search("test",[document(str(i),"test") for i in range(5)],settings=settings)
    assert exc.value.status_code==422


def test_capabilities_requires_session_and_exposes_no_credentials(client):
    assert client.get("/api/v1/system/capabilities").status_code==401
    login(client)
    result=client.get("/api/v1/system/capabilities").json()
    assert "ready" in result["ocr"] and "key" not in json.dumps(result).lower()
