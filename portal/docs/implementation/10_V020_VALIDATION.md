# v0.2.0 verification

Verified in the managed Linux environment, Python 3.12 / Node 24:

- `python nawa.py check`: **51 passed**; new SQLite migration and Alembic
  consistency passed; TypeScript/production Vite build and Prettier passed.
- Chromium journey: all ten routes; cited query; upload; create case; two
  source-linked quotations; deterministic comparison; independent reviewer;
  simulated approval; printable report opened and generated as a PDF.
- New case metric navigation, own-case checkbox, sorting and document processing
  filters were exercised in the browser.
- 390px mobile layout, menu, Arabic RTL and horizontal-overflow checks passed.
  Additional 768/1024/1440 widths passed. Login screenshot inspected.
- Print/Save PDF button was exercised under the report Content Security Policy.
- Print endpoint tests cover unauthenticated and foreign-tenant denial, HTML
  escaping and no-store responses. Existing source ACL checks are reused.
- Available-port test reserves an occupied socket, verifies two distinct
  available replacements and confirms the existing process is not killed.

The first concurrent cloud startup timed out during shared-host resource
contention. Retrying with `--timeout 300` succeeded; checks subsequently passed.
The default timeout remains 60 seconds; slower machines may pass 300 explicitly.
One upstream LangChain pending-deprecation warning remains non-fatal.

No native Windows/macOS execution, live cloud, OCR, paid model, external S3,
independent penetration test, exhaustive accessibility audit, or measured
production performance is claimed. The user's earlier Windows v0.1 startup is
not a native Windows test of this redesign.

See `08_UAE_UI_AND_GAP_REVIEW.md` for all 26 phase statuses, remaining gates,
and data-preserving upgrade instructions.
