# Phase 4: Permission-filtered BM25 document retrieval (synthetic baseline)

A **reproducible retrieval baseline**, **not** an LLM, RAG answer generator, authentication provider, or production authorization system. This uses Python standard-library BM25 and the existing PyMuPDF dependency for optional direct PDF page indexing.

## What it does

- Tokenizes English/Arabic text, normalizes Arabic-Indic digits and Unicode presentation forms with NFKC.
- Computes BM25 scores with a deterministic tie-break; returns cited passages with `document_id`, `version`, `page`, `source`, `method`, and verbatim text.
- **Filters by tenant and allowed principal before computing index statistics**. Access context must be provided by a trusted service; CLI inputs are a **simulation**, NOT authentication.
- Evaluates a **three-question synthetic** relevance set using macro Recall@5; scores are not representative of real-world quotation retrieval.
- Optionally indexes **selectable-text PDFs by page** with `pdf_page_passages()`. OCR is not silently enabled; empty image-only pages are not indexed.

## Run

From the repository root, after `python3 -m pip install -r demo/requirements-pdf.txt`:

```bash
cd demo
python3 -m nawa_demo.retrieval_cli search --tenant demo-a --principal reviewer-a --query 'شركة المثال الضريبة ٤٥'
python3 -m nawa_demo.retrieval_cli search --tenant demo-a --principal reviewer-a --query 'English Supplies total'
python3 -m nawa_demo.retrieval_cli evaluate
python3 -m unittest discover -s tests -v
```

## Important boundaries

- Sample passage metadata are synthetic and must not be mistaken for verified OCR/PDF evidence. Use `method=synthetic` for corpus fixtures.
- No embeddings, LLMs, answer synthesis, fine-grained bounding boxes, model evaluation, real document authorization, audit logs, document lifecycle/version enforcement, or deployment.
- The `--principal` flag allows any caller to CLAIM an identity. **Do not expose this CLI as a multiuser API**; obtain verified identity and document ACLs from your backend instead.
- Tokenization is deliberately simple. It is not Arabic stemming, morphological analysis, transliteration, or cross-language retrieval. Arabic queries generally require matching Arabic tokens.
- No keyword match yields no results (rather than invented passages). No similarity score is a calibrated probability.
- Before using real documents, implement trusted identity enforcement, ACL changes/revocation, deletion propagation, storage boundaries, and security tests.
