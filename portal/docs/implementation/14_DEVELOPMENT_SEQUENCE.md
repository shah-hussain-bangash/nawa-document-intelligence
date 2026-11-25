# Development sequence after UI approval

This sequence is a practical implementation backlog. It supplements, rather than
replaces, the 26-phase assessment in `08_UAE_UI_AND_GAP_REVIEW.md`. Each release
needs executable code, relevant tests, a demonstrated UI journey and explicit limits.

| Step | Scope | Current state / next gate |
|---|---|---|
| 01 | Source-linked quotation drafts | v0.4 baseline delivered for labelled English/Arabic text; user review and manual completion required |
| 02 | Evidence version and correction history | Next: immutable versions, persisted extraction/correction provenance, reviewer snapshot references and withdrawal/revision tests |
| 03 | Document intelligence | OCR/table adapters, scan samples, Arabic review corpus and extraction quality evaluation |
| 04 | Retrieval and knowledge | Approved embedding route, pgvector/hybrid benchmark, effective-date policy filters and answer/citation feedback |
| 05 | Durable execution | Queue/checkpoints, bounded retries/recovery, tool scope and idempotency tests under failure |
| 06 | Identity and access | Verify existing OIDC adapter with a chosen provider, provisioning, revocation and database isolation hardening |
| 07 | Evaluation and observability | Reviewed bilingual held-out set, accuracy/abstention metrics, latency/cost measures and redacted traces |
| 08 | Cloud and operations | Approved deployment profile/account, IaC, staging, key/storage/egress controls, backup/restore and rollback evidence |
| 09 | Pilot and expansion | User acceptance, reviewed domain workflows, service/HR extensions and ongoing operations |

Steps overlap where dependencies require it; identity, audit and security tests
continue with every feature. Live services and real records require their actual
provider/data/deployment decisions. Local templates do not complete those gates.
