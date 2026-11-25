# Current operations and remaining work — v0.6.0

Start at [20_V060_OCR_HYBRID_AND_RECOVERY.md](20_V060_OCR_HYBRID_AND_RECOVERY.md)
for exact upgrade, OCR/hybrid, real identity verification, recovery and backup commands.

## Lifecycle and data

`python nawa.py setup` installs locked dependencies, validates local configuration,
backs up existing versioned SQLite before migration and builds the frontend.
`python nawa.py run --auto-ports` starts API, Vite and document worker. Ctrl+C stops
these owned processes. On Windows `stop` verifies exact project executables and
process creation time; it does not target arbitrary Cursor or Node processes.
No reboot or deletion of user data is part of normal setup/recovery.

Default storage is `.data`. Preserve `.env` separately. Never operate two releases
against the same database/evidence directory. Seeding is synthetic and idempotent.

## Authentication and authorisation

Every API request validates session membership; mutations validate CSRF and
configured browser Origin. Evidence is tenant/role scoped. Local demo sign-in is
for loopback synthetic learning only. Production refuses demo authentication,
demo seeding or an HTTP WEB_ORIGIN.

OIDC uses exact trusted issuer/subject membership, state, PKCE, nonce, signature,
audience/authorised-party and expiry validation. Discovery endpoints must share
the configured HTTPS issuer origin. Opaque session cookies keep tokens off browser
localStorage. Seven real local Keycloak flow/replay/logout/revocation checks passed;
production provisioning, MFA, recovery, trust rotation and policy remain unaccepted.
Use `python -m uae_ai.cli provision-user --help` to provision exact subjects; email
alone grants no membership. Set the absolute trusted CA-bundle path for local TLS.

## Models and parsing

Default answers return cited BM25 passages. Optional hybrid uses a bounded local
embedding route; generation is independently optional. Classification allowlists
apply before model use, and failures never choose another paid provider. Actual
semantic/generation quality remains unverified because this environment blocked
model downloads. Complete 100-case draft benchmark scores are retained, including
failed cases. They are not independently reviewed or production targets.

PDF/TXT extraction is bounded, with local English/Arabic OCR when tools are
available. Original versions, page/word provenance and review warnings are kept.
Mixed incomplete sources remain needs_ocr; arbitrary table semantics are not
inferred. Native subprocess limits do not provide full malware isolation.

## Recovery, backup and reporting

Document processing uses renewable ownership through a five-minute lease and a
maximum of three automatic claims; expired work is recovered by the worker.
Explicit retry resets attempts. Publication rechecks creator membership and source
version/token. Deterministic workflow replay uses a renewable one-minute lease,
step/final CAS guards and one approval per run. There are no external payment/tool
side effects; distributed side-effect reconciliation is not implemented.

Offline `nawa.py backup` bundles a consistent SQLite snapshot and original files
with hashes. `restore` verifies all content and creates a new directory without
replacing active data. Stop separately launched API/worker instances as well as the
normal launcher. ZIP checksums do not encrypt or authenticate backups. Coordinate
native PostgreSQL/object-store backup, retention, revocations and recovery with
operators; no production RTO/RPO is asserted.

Terminal case reports retain pinned source versions. Source withdrawal removes
active access and original/text/extraction/review content; governed legal holds,
external backup expiry and tamper-resistant audit storage remain separate work.

## Deployment boundary

`compose.production.yaml` remains a reference VM deployment with Caddy/HTTPS and
OIDC. Compose 2.24.4+ is needed for !reset. A controlled domain, clean production
DB, real identity and deployment security review are required. No account/domain
or hosting cost has been assumed. Cloud IAM/KMS, RLS/service roles, object storage,
managed queues, protected audit retention, telemetry/SLOs, load/soak, independently
reviewed model/data quality, full Arabic/accessibility, pilot/UAT and operating
ownership remain open. See the complete 26-phase status in guide 18.
