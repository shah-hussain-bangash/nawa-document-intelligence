# Security and Sovereignty Requirements

Access, data control, model routing and release evidence

Version 1.0 | 6 November 2026 | Proposed development baseline

## 1. Security objective and scope

Protect tenant documents and approval integrity while treating uploaded content, retrieved passages and model output as untrusted. The prototype must not claim UAE regulatory compliance or sovereign certification. Requirements depend on the actual organisation, data class, sector, services and legal review.
Security ownership covers application, identity, database, object storage, model providers, telemetry, CI artifacts and operator access. Record deployment-specific decisions rather than relying on a cloud region label.

## 2. Identity and authorisation

SEC-01: verify OIDC issuer, audience, signature and expiry with controlled key rotation. SEC-02: derive membership from trusted identity and stored policy. SEC-03: deny by default at API, worker and tool boundaries. SEC-04: authorise every document, citation, download and review decision.
Apply RBAC for roles and attributes for tenant/resource/classification scope. Support revocation and least-privilege service identities. Test resource enumeration, ID substitution, administrator access, expired sessions and concurrent membership changes.

## 3. Threat model

Priority threats: cross-tenant disclosure; prompt injection that proposes unauthorised actions; malicious uploads; stale or forged approvals; stolen secrets; sensitive traces; retrieval poisoning; duplicate side effects; and supply-chain compromise.
For each threat record entry point, affected asset, attacker capability, prevention, detection, recovery and residual risk. Review the model when adding a connector, model endpoint or data classification.

## 4. Model and tool controls

SEC-05: permit only approved providers for the request classification. SEC-06: constrain tools with typed schemas, server-side permission, allowlisted destinations, timeout and budget. SEC-07: model suggestions cannot grant credentials or approval. SEC-08: bind approval to current case and evidence revisions.
Separate instructions from document content and test malicious passages. Instruction separation alone is not sufficient; enforce action boundaries in code. Fail closed when a permitted model is unavailable. Any fallback must satisfy the same data-processing policy.

## 5. Sovereignty and residency matrix

For documents, embeddings, inference, OCR, logs, backups, keys and support access, record: owner, classification, processing country/region, provider/subprocessors, retention, encryption/key control, operator access, outbound route and contract evidence.
Profiles: public/synthetic sandbox; verified UAE residency-constrained deployment; or restricted private inference. Confirm service-specific availability and terms. Include disaster recovery and telemetry destinations. Do not assume a UAE web server keeps every AI request or support operation within the UAE.

## 6. Application and infrastructure controls

Use TLS, encryption at rest, managed secrets and scoped storage access. Keep secrets out of source, images and logs. Restrict network destinations; validate storage keys, uploads and parser resource use. Rate-limit costly operations and enforce tenant budgets.
Apply row-level policies where appropriate, but test bypass roles and pooled-connection scope. Protect cookies/tokens according to the selected browser-auth design; include CSRF, CORS and session controls where applicable. Scan dependencies and container images and record remediation decisions.

## 7. Audit, privacy and deletion

Record actor, tenant, resource, action, revision, time, outcome and correlation ID. Limit sensitive payloads. An append-only API is not tamper-proof storage: restrict database roles and add separately protected integrity evidence or immutable retention where required.
Define access review, redaction, retention, legal-hold and deletion processes. Test deletion across originals, chunks, vectors, caches and derived outputs. Reapply revocations after backup recovery. Keep audit retention separate from document retention.

## 8. Security acceptance and incident response

Mandatory scenarios: cross-tenant query/download denied; forbidden tool blocked; prompt injection cannot override tool policy; stale approval rejected; revoked membership denied; secret absent from logs; oversized/malformed file handled safely; and restricted request cannot escape via fallback.
Any mandatory failure blocks release. No unresolved critical finding may pass the release gate. Finite tests do not prove the absence of vulnerabilities. On incident: contain access/egress, preserve authorised evidence, assess exposure, rotate affected credentials, recover and document lessons.

## 9. Required evidence before real-data use

Obtain data-owner authorisation, deployment-specific legal/security review, residency matrix, provider terms, access matrix, threat model, test results, vulnerability triage, restore evidence and an incident contact/runbook.
Open choices include identity provider, classification scheme, retention periods, jurisdiction-specific obligations, operator access model and key custody. Until resolved, keep the deployment a synthetic/public-data sandbox and describe limitations accurately.
