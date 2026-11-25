# Cursor-ready v0.1.1 — checked package and runtime

Validated on 6 November 2026 using Linux, Python 3.12.14 and Node.js 24.22.1.
Native Windows and macOS execution is not claimed; configuration, commands and
compatibility fixes for those platforms are included.

## Reproducibility check

The v0.1.1 ZIP was extracted into a new directory whose path contained spaces
and Arabic characters. There was no `.env`, `.venv`, application database or
`node_modules` in the extraction. No developer virtual environment or installed
frontend directory was copied into it.

Executed from that extracted project:

1. `python3 nawa.py setup` — passed. Created a clean virtual environment, installed
   hash-locked Python packages and locked npm packages, initialised ignored local
   configuration, created the data directory, migrated the database and built UI.
2. `python3 nawa.py run --api-port 8001 --web-port 5174` — passed. API and frontend
   started on matched alternative ports. READY appeared only after direct and
   proxied API readiness succeeded.
3. `python3 nawa.py smoke --url http://localhost:5174 --workflow` — passed.
   Verified login, tenant workspace, actual citations, new case, deterministic
   comparison, independent reviewer and approved simulated outcome.
4. Chromium browser journey against the extracted app — passed all ten pages,
   document upload, cited search, creation/comparison/review, mobile navigation
   and Arabic RTL, with no uncaught JavaScript exceptions.
5. `python3 nawa.py check` — **41 tests passed**, plus fresh migration/schema
   checks, TypeScript/production build and frontend formatting.
6. Ctrl+C — stopped launcher-owned services and preserved saved records.

The test suite includes 28 original application/security tests and 13 startup/tool
tests (including parameterised cases). One upstream LangGraph/LangChain pending
deprecation warning remains; it is reported rather than suppressed.

## Review fixes

- The prior launcher could print a URL before a child failure and did not refuse
  occupied ports. It now fails with a nonzero exit code and cleans up its services.
- Vite no longer silently switches port and breaks Origin/proxy configuration.
- The clean setup explicitly creates required data directories before migration.
- Cursor-specific workspace/tasks/debug/rules and one-command tooling are present.
- `.env` loading is UTF-8/BOM aware, literal, non-executing and does not print values.
- OS-specific parser and browser executable assumptions have explicit fallbacks.

## What these checks do not establish

No real cloud deployment, live IdP/model integration, OCR/semantic retrieval,
independent security assessment or regulatory approval was supplied by this review.
The package runs the documented local synthetic sandbox; remaining enterprise
work is listed in the document map and operations guide. A successful Cursor
setup is not proof that those services are deployed or compliant.

The current archive also includes ordered files, source hashes, all 14 input PDFs,
setup instructions and the application source, while excluding credentials,
runtime records, virtual environments and installed node modules.
