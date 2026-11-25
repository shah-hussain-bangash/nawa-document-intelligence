# Validation evidence — 6 November 2026

Historical v0.1.0 results are recorded below. For the Cursor-ready v0.1.1 release,
see `06_CURSOR_VALIDATION.md`: the expanded suite has 41 passing tests and the
new setup/run/check commands were verified from a clean ZIP extraction.

## Executed checks

| Check | Result | Scope |
|---|---|---|
| Backend integration/security suite | 28 passed | Clean Python 3.12 virtual environment using hash-locked dependencies |
| Local retrieval smoke | 6/6 passed | Developer-authored English/Arabic synthetic questions; NOT a held-out benchmark |
| TypeScript + production frontend build | Passed | Vite 7.3.7; React 19.2; updated router; split chart/vendor assets |
| Frontend formatting | Passed | Pinned Prettier check |
| npm audit, full dependency tree | 0 reported vulnerabilities at the check | A registry advisory check, not a security certification |
| Alembic upgrade + schema drift check | Passed | Fresh SQLite baseline; actual PostgreSQL container startup migration |
| Container builds | Passed | API and frontend built with TLS verification and supplied CA trust |
| Local Compose startup | Passed | PostgreSQL healthy; API healthy; Nginx serves on loopback port 8080 |
| Browser journey on development stack | Passed | Chromium, all ten routes, evidence search/upload, case comparison/review |
| Browser journey on container stack | Passed | Same workflow through built Nginx/API/PostgreSQL; mobile and Arabic RTL |
| OIDC callback validation | Passed with mocked provider | Real RSA-signed test tokens; nonce/audience/expiry/provisioning/replay checks |
| Production Compose configuration | Parsed successfully | Reference HTTPS/OIDC override only; not deployed |

The browser runner recorded no uncaught JavaScript exceptions and checked mobile
and RTL page-width overflow. It verified case creation, source-linked comparison,
role change, independent approval and the resulting simulated state. Mobile case
tables render as readable cards; other wide tables scroll within their panels.

## Security scenarios covered

Unauthenticated sessions; expired/wrong OIDC claims; unprovisioned OIDC subjects;
state replay; invalid CSRF; foreign Origin; forbidden workflow roles; cross-tenant
read/write/search/download/report; confidential source ACL and derived quote
redaction; Decimal arithmetic; independent review; admin self-approval denial;
stale approvals; duplicate runs/decisions; document withdrawal invalidating review;
file type/content validation; image-only PDF status; membership revocation;
unanswerable/injected knowledge requests; unconfigured hosted-route refusal;
invalid server-owned fields; tickets/preferences; production demo startup refusal.

## Limits of this evidence

- No real OIDC tenant, paid model, cloud account, external S3, OCR or embeddings
  service was available. Their live integration is not claimed verified.
- Tests exercise the explicit sandbox behaviour, not every future roadmap feature.
- No independent penetration test, calibrated Arabic benchmark, exhaustive
  accessibility audit or production load/restore/DR exercise is claimed.
- The source database does not implement RLS or composite foreign-key isolation.
  Application-layer tenant/ACL checks are tested; further defence is documented.
- One upstream LangGraph/LangChain pending-deprecation warning remains; the tests
  pass without suppressing it. It does not establish any application failure.
- Cloud region/terms, private networking, encryption/key operations, retention,
  immutable audit and incident ownership remain deployment-specific work.

See source tests and scripts for reproducible checks. Passing these finite checks
does not prove complete security, regulatory compliance or universal AI quality.
