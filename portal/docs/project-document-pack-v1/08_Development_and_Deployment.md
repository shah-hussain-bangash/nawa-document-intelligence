# Development and Deployment Guide

Implementation runbook, CI/CD and operating readiness

Version 1.0 | 6 November 2026 | Proposed development baseline

## 1. Current status and prerequisites

This is a development specification, not an executable installation guide for an existing application. The repository currently has a README and design documentation; application code, dependency locks, Compose configuration and CI are still to be implemented. Commands below describe the intended interface and are not claimed tested.
Prerequisites for the planned stack: Git, Python 3.12+, a supported Node.js LTS release, Docker Engine/Compose and sufficient local storage. Choose and pin exact versions during foundation work. Existing cloud tasks are isolated; use their checkout and do not create a worktree unless explicitly requested.

## 2. Planned repository structure

apps/web: React console. backend/src/uae_ai: API, domain services, database, retrieval, workflows, tools, policies and approvals. migrations: schema changes. tests: unit, integration, security and end-to-end suites. data/sample: synthetic fixtures only. evals: datasets and runners. infra: deployment code. docs: specifications and runbooks.
Keep secrets, uploads, generated indexes and runtime logs outside tracked source. Commit reproducible dependency manifests/locks and a non-secret environment example when implementation begins.

## 3. Configuration contract

Planned settings include DATABASE_URL, object-store endpoint/bucket, OIDC issuer/audience, approved model provider/name, EMBEDDING_MODEL, QUEUE_URL, file-size limits and telemetry destination. Credentials are secrets, even when embedded in a connection URL. Never print or commit their values.
Maintain separate local, test and deployment profiles. Validate required settings at startup, refuse unsafe defaults outside local development, and declare model-egress and data-location policy explicitly.

## 4. Intended setup and startup sequence

Foundation work must implement and verify this sequence: install locked backend/frontend dependencies; create local non-secret configuration; start database/storage/identity/queue services; apply migrations; seed synthetic records; start API/worker/web; then run readiness and smoke tests.
The planned interfaces are docker compose up -d, alembic upgrade head and project-documented seed/start commands. They are not usable until those files and application modules exist. Replace this section with exact working-directory commands and verified output during Stage 1; do not copy placeholder commands into a production runbook.

## 5. Validation and CI/CD

CI should validate schemas and formatting, relevant type checks, unit/integration/security tests, migration compatibility, frontend build, container build and vulnerability findings. Live-model evaluations run in a controlled job with secrets, budgets and versioned datasets; mock tests are not evidence of live model quality.
An end-to-end smoke test creates a synthetic case, processes documents, gets a cited comparison, pauses for review, accepts an authorised decision and verifies audit history. Include denied-access and stale-approval cases. Preserve real exit status and report skipped tests separately.

## 6. Deployment process

Select the approved residency profile before provisioning. Use infrastructure as code, TLS ingress, private database/storage access, least-privilege identities, managed secrets and immutable container artifacts. Verify model/OCR/telemetry destinations independently of the application region.
Deploy to staging, migrate safely, seed only synthetic demo data, run readiness/functional checks and inspect redacted telemetry. Production promotion requires authorised deployment scope and the security/evaluation evidence in the companion specifications.

## 7. Monitoring and recovery

Observe API errors/latency, dependency readiness, worker queue age, ingestion failures, workflow retries, review backlog, provider timeouts, tokens and spending. Alert on abnormal denial patterns, stalled runs and budget thresholds. Document recipients and escalation before operational use.
Back up database and object versions with an approved retention/location policy. Restore to an isolated environment, verify referential integrity, document access and a representative case, then reapply deletion/revocation obligations. A backup job succeeding does not prove restore readiness.

## 8. Rollback and incident operations

Before release record application artifact, migration version, configuration and model/prompt/rule versions. Roll back only to a compatible schema; use expand/contract migrations and a tested recovery procedure. Stop new work and reconcile uncertain actions before replaying jobs.
Incident sequence: contain exposure, preserve authorised evidence, identify affected data/runs, rotate compromised credentials, recover services, validate isolation and document root cause. Keep sensitive artifacts out of public issue trackers.

## 9. Handover and readiness checklist

Required evidence: clean-machine setup, dependency locks, current API/schema docs, passing functional/security tests, evaluation report, secrets inventory without values, validated egress/residency profile, monitored deployment, restore/rollback demonstration and known-limitations list.
Stage 1 is the immediate next increment: implement health endpoints, settings, database migration, synthetic case persistence, a simple web case list and CI. This guide becomes a verified operating runbook only after those steps are implemented and exercised.
