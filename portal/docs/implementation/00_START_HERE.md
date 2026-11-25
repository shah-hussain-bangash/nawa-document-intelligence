# Current release — v0.6.0

Start with `20_V060_OCR_HYBRID_AND_RECOVERY.md` for safe Cursor upgrade and free
local OCR/hybrid/identity/recovery/backup commands. Guide 18 tracks all 26 phases
and remaining code, quality and deployment acceptance. Earlier release notes
below are historical and do not override the current guide.

# v0.4 Step 01 — New functional capability

Read `13_STEP_01_QUOTATION_DRAFTS.md` for the source extraction walkthrough and
upgrade instructions. Read `14_DEVELOPMENT_SEQUENCE.md` for the next increments.

# Nawa source code: start here

For the latest Cursor-ready v0.1.1 package, begin with root `RUN_IN_CURSOR.md`.
`python nawa.py setup`, `run`, `doctor`, `check` and `smoke` now wrap installation,
startup and verification. The older v0.1.0 PDF is preserved as history; the Cursor
guide and v0.1.1 validation/release notes describe the current commands.

Nawa is an independent, evidence-led operations sandbox built from your 14 PDFs.
It is a working React/FastAPI application, not a government service or certified
sovereign platform. The original PDFs remain planning inputs; the implementation
map and README describe what this release actually implements.

## Read and run in this sequence

1. Read the root README for features, prerequisites and exact startup commands.
2. Read `01_DOCUMENT_MAP.md` to understand every supplied PDF and its code mapping.
3. Read `.env.example`, `pyproject.toml`, `requirements.lock`, and the frontend
   package manifest/lockfile for configuration and dependencies.
4. Read `backend/src/uae_ai/core/config.py`, then `db.py` and the Alembic migration.
5. Read `core/security.py` and `api/auth.py`: sessions, CSRF, roles and OIDC.
6. Read `domain/schemas.py`: typed request contracts and financial bounds.
7. Read `seed.py`: fictional sources, cases, two tenants and separate identities.
8. Read `rag/parser.py`, `worker.py`, then `rag/retrieval.py`: evidence ingestion,
   provenance, local retrieval and the optional approved hosted-model route.
9. Read `graphs/procurement.py`: deterministic Decimal rules and bounded LangGraph.
10. Read `api/workspace.py` and `main.py`: API routes, revisions, approval integrity,
    tenant scope, lifecycle and application boundary controls.
11. Read `ml/forecast.py`: an honest synthetic temporal baseline, not a trained
    production forecasting model.
12. Read frontend `main.tsx`, `types.ts`, `api.ts`, `context.ts`, `i18n.tsx` and
    `ui.tsx`: application types, transport, state, localisation and primitives.
13. Read `App.tsx`, `pages.tsx`, `workflows.tsx` and `styles.css`: the professional
    console, routes, forms, dialogs, evidence and review experiences.
14. Read integration tests, the browser journey and `03_VALIDATION.md`.
15. Read Dockerfiles, Compose files, CI and `02_OPERATIONS_AND_LIMITS.md` before
    attempting any deployment outside your local synthetic environment.

`SOURCE_MANIFEST.md` enumerates the actual delivered files in reading order.
`openapi.json` is exported from the application, not a speculative API sketch.

## First hands-on journey

Sign in as Analyst in Emirates Operations. Open a draft case, inspect original
quotation text, then run comparison. Switch to Reviewer using sign out/sign in,
open that case and record a reason and decision. The result is an approved
simulation, with no purchasing/payment action. Revise evidence on another pending
case and verify the old approval disappears. Ask the assistant about procurement
requirements and open its source citations.

## Role-based learning

- Requester: create a draft case and service request; cannot run or approve cases.
- Analyst: upload evidence, correct supplied quotation fields and run comparisons.
- Reviewer: inspect evidence and decide independently; cannot prepare runs.
- Auditor: read permitted cases/evidence/audit; no business mutations.
- Tenant admin: combined scoped privileges, but cannot approve their own run.

Research Lab is a separate seeded tenant. Switching to it demonstrates isolated
records. Local demo login deliberately permits selecting these fictional
identities; it is disabled when APP_ENV=production.
