# Phase 9 — Local quotation review dashboard

**Scope:** Localhost-only, synthetic quotation demonstration. This is not a deployed production web app, login system, multiuser approval service, or secure audit store.

The dashboard reuses `core.extract`, `pdf_ingest.extract_pdf`, and Phase 8 `review.begin/correct/decide/inspect`. All uploads, extracted results, and review ledgers live **in Python process memory**, are lost when the process stops, and are **never sent to an external service**. The bundled samples have known synthetic content. Uploaded data must also be entirely synthetic.

## Run

From the repository root:

```bash
python3 -m pip install -r demo/requirements-pdf.txt
cd demo
python3 -m nawa_demo.dashboard
```

Open **http://127.0.0.1:8765** in a browser. To stop, press `Ctrl+C` in Terminal. The server binds only to `127.0.0.1`, not your public network. Do not set up a public tunnel or reverse proxy.

## Demo walkthrough

1. Load *English quotation* and *Arabic quotation* from the sample selector.
2. Click each supplier to inspect values and provenance line references.
3. Check both boxes and choose *Compare selected*. The Arabic supplier has the lowest valid synthetic AED total.
4. Load *Incorrect VAT quotation* to see failed VAT validation; that quotation is excluded from valid price ranking.
5. Select a quotation, start review, add a reviewer ID and reason, then approve or request changes. Approvals of invalid financial statements are rejected.
6. Optionally upload **your own synthetic** UTF-8 `.txt` or selectable-text `.pdf`, up to 4 MiB. No OCR in the web endpoint. The supported format still uses fixed labels and AED only.

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

## Important boundaries

- There is **no authentication**. Review actor IDs are self-asserted. There are no production permissions, roles or audit attestations.
- HTML is rendered using safe `textContent` rather than treating document text as HTML. API request bodies are capped; filename traversal is rejected; uploads use temporary files and are deleted after extraction.
- Server only listens on `127.0.0.1:8765`. Browser cross-origin POSTs are rejected by Origin checks (this is NOT a comprehensive CSRF defense or authentication mechanism); non-browser clients can call the API. Do not expose it beyond your own computer.
- Review data reside in memory, with hash-linked events but **no durable audit store**, multi-process concurrency protection, or persistent upload storage.
- The evidence line/quote attached to a review correction remains a reviewer assertion, not verified against original bytes.
- Price-only rankings are not procurement awards. An LLM is never called from this dashboard.
- This demonstrates sample ingestion, deterministic checks, comparison, and human review, not a complete Arabic/English enterprise document intelligence platform.
