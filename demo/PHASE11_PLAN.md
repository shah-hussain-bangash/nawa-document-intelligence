# Phase 11: PostgreSQL persistence plan

Status: design in progress; database integration is not yet implemented.

## Goal and boundaries

Persist synthetic quotations, extracted evidence and review events across application and database restarts. Preserve the existing memory-only mode and its API behaviour. Do not expose PostgreSQL on a host network port, store source files without a retention decision, or claim authentication, secure auditing or production readiness.

## Baseline and dependencies

The Phase 10 dashboard stores quotation objects and review ledgers in `DashboardState`. The browser keeps its own list of quotation IDs and therefore needs a list endpoint and startup reload for persistent records. Review state is verified by replaying the hash-linked ledger; the hashes are not a tamper-proof audit system. The existing local database smoke test establishes volume persistence only, not application integration. The separate v0.6.6 application and its database are not migration sources for this demo.

## Implementation sequence

1. Design a versioned migration mechanism and PostgreSQL schema for quotations, source metadata, extracted evidence and review events. Record migration checksums and reject changed applied migrations. Keep uploaded originals out of storage until an explicit retention design exists.
2. Add a repository interface with an unchanged in-memory implementation and an explicitly enabled PostgreSQL implementation. Use bounded connection timeouts, parameterized queries and transactions. Fail closed with a safe error if PostgreSQL is configured but unavailable; never silently fall back to memory.
3. Store a review transition atomically with an expected-revision check under a row lock. Validate the existing review ledger before accepting or displaying it; test concurrent decisions and stale updates.
4. Add a quotation list endpoint and restore the browser list on load. Clearly disclose whether memory or PostgreSQL storage is active. Never treat a restarted application as proof that the database was restored from backup.
5. Add an opt-in Compose configuration with internal database networking, persistent storage, health checks and a non-committed development secret. Preserve the existing Phase 10 Compose path and avoid taking over the separately created `nawa-postgres` container or its volume.
6. Add PostgreSQL integration tests to CI. Exercise clean migration and repeat migration, Arabic/English persistence, transaction rollback, revision conflicts, malformed input, database failure and recovery. Test the UI/API after application and database restart.
7. Document configuration, migration, safe backup/restore and limitations. Verify a restore into an isolated new database before claiming recovery. Record the commit and successful CI run.

## Acceptance gate

Phase 11 is complete only when synthetic quotation and review data survive both application and database restarts; migrations, concurrency and failure paths pass; the existing memory mode remains usable; the README and recovery instructions are updated; and the corresponding CI run succeeds. PostgreSQL installation or this plan alone does not close the phase.
