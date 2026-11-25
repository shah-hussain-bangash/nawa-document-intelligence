# UAE Sovereign Agentic AI — Complete Security Setup Guide

Version 1.0 | 6 November 2026 | Proposed controls; implementation/validation pending.

## 01 / Define the security scope and data boundary

### Entry conditions
Complete before adding providers or sensitive data. The current repository is a documented design, not a secured deployed application.

### Setup steps

1. Create an asset register covering identities, documents, extracted text, embeddings, cases, approvals, model requests, logs, backups and build artifacts. Name an owner for each.
2. Classify data as public/synthetic, internal, confidential or restricted using an organisation-approved scheme. Do not present these suggested labels as a legal standard.
3. Select the operating profile: public/synthetic sandbox, verified UAE-residency-constrained deployment, or restricted/private inference. Document which destinations are allowed per classification.
4. Map storage, OCR, embeddings, inference, telemetry, recovery and support access separately. Record region/country, provider, retention, subprocessors and operator access evidence.
5. Threat-model cross-tenant disclosure, prompt injection, malicious files, forged/stale approvals, secret leakage, duplicate effects and supply-chain compromise. Assign mitigation and verification owners.
6. Keep real awards, payments and government integrations outside the sandbox. Any production processing requires its own data-owner, security and applicable legal authorisation.
7. Create a security backlog with control IDs, owner, dependency, implementation status and test evidence. Mark every control pending until demonstrated.

### Verify before continuing
Review the full architecture data flow with a second reader. Every asset and outbound destination has an owner, classification and processing decision; unresolved routes remain denied.

### Save as evidence
Asset register; classification/residency matrix; threat model; decision log; security acceptance checklist.

## 02 / Secure developer access and repository hygiene

### Entry conditions
Requires scope decisions. Apply before creating credentials, sample uploads or deployment pipelines.

### Setup steps

1. Use named developer accounts with MFA and least privilege. Restrict repository/cloud administration and document account recovery without sharing a single privileged identity.
2. Use a supported operating system and tools. Pin supported runtime/dependency versions during implementation and install from approved sources with TLS/checksum verification enabled.
3. Add ignore rules for environment secrets, local databases, uploads, indexes, model caches, logs and private artifacts. Track a non-secret configuration example instead.
4. Enable secret scanning where available, and scan proposed commits and repository history using a vetted tool. A local ignore file cannot remove a previously committed secret.
5. If a secret was exposed, revoke/rotate it first, identify use and access, then handle history cleanup through repository procedure. Deleting the file is insufficient.
6. Require relevant CI checks and review before merging to the protected release branch. Keep user changes intact and inspect diffs before staging or committing.
7. Use synthetic/public fixtures, never real identity or banking documents as convenient test data. Review third-party model/parser licences for the intended distribution.

### Verify before continuing
Run a secret scan over the intended publication scope. Confirm local secret files are ignored, release permissions are limited and dependency verification is not bypassed.

### Save as evidence
Repository rules; access/MFA record; scan results; locked dependency plan; developer onboarding checklist.

## 03 / Set up configuration, secrets and service identities

### Entry conditions
Requires an inventory of applications, providers and their actual permissions. Never enter secret values in this PDF, source control or chat.

### Setup steps

1. Separate public settings from credentials. URLs containing passwords are secrets too. Define required setting names, validation, owners and scope.
2. Inspect existing environment bindings by name and readiness only. Test the specific authorised operation before requesting a new credential; proxy-backed authentication may not appear as a raw token.
3. For local development use a supported local secret mechanism or an ignored, access-restricted file. Bind local services to loopback; avoid broad credential sharing.
4. For deployed services use an approved secret manager and short-lived workload identities where possible. Give API, worker, migration job and CI distinct permissions.
5. Grant the model route only its required provider permission. Use separate development, staging and production-like bindings and spending controls.
6. Implement configuration validation and log redaction. Errors must identify the missing setting name without printing values, connection strings, headers or entire environment dumps.
7. Document rotation: create replacement, deploy binding, verify new use, revoke old credential and inspect failures. Maintain an emergency revocation route.

### Verify before continuing
Search logs, image configuration and CI artifacts for accidental values using approved tooling. Revoke a test service permission and confirm the affected operation fails safely.

### Save as evidence
Secret-name inventory; service-permission matrix; safe environment example; configuration validation and rotation test.

## 04 / Configure network boundaries and TLS

### Entry conditions
Requires selected deployment profile and service inventory. Local loopback development and public HTTPS deployment have different controls.

### Setup steps

1. Draw permitted ingress/egress: browser to gateway, gateway to API, API/worker to private data services, and governed routes to approved inference/OCR/telemetry.
2. Expose only intended ingress. Keep database, queue, object management and identity administration off the public Internet. Use explicit security groups/firewall rules.
3. Terminate trusted HTTPS at the supported gateway and encrypt internal connections where the threat model/profile requires it. Configure certificate renewal and expiry alerts.
4. Preserve cloud-session proxy/CA settings. Never bypass a destination denial by direct networking or disable TLS verification to make a provider call succeed.
5. Validate outbound destinations and redirects, block metadata/private service access for untrusted URL fetches and omit remote-import features until SSRF controls are tested.
6. Set proxy request/body/time limits and trusted forwarded-header handling. Do not trust arbitrary X-Forwarded-* headers from public clients.
7. Use exact environment origins for CORS and OIDC redirects. Enable HSTS only after HTTPS and subdomain implications have been validated; do not blindly preload local/demo domains.

### Verify before continuing
From permitted and forbidden network locations, test required service reachability and denial. Verify certificates and provider calls through the approved route with validation enabled.

### Save as evidence
Network flow matrix; ingress/egress rules; TLS renewal configuration; connectivity tests and exceptions.

## 05 / Configure OIDC identity and privileged accounts

### Entry conditions
Requires private identity administration and exact application URLs. Keycloak is one candidate; equivalent approved OIDC providers can satisfy the same controls.

### Setup steps

1. Create separate development/staging/deployed realms or equivalent isolation. Use named administrators, MFA and least privilege; remove bootstrap access after setup.
2. Register the application using the appropriate confidential-backend or public-client design. Set exact redirect/logout URIs; avoid broad wildcard redirects.
3. Use Authorization Code flow with PKCE where appropriate. Do not use deprecated implicit/password flows as a shortcut for browser login.
4. Configure access/session lifetime and refresh behaviour from risk and usability needs. Protect recovery flows and administrative endpoints.
5. In the backend verify signature against trusted keys, permitted algorithms, issuer, audience, expiry and relevant claims. Distinguish an access token from an ID token.
6. Map identity by stable issuer/subject. Resolve tenant memberships and business roles server-side; do not trust a mutable email or browser-selected tenant alone.
7. Test signing-key rotation, provider unavailability, expired/revoked membership and wrong-audience/issuer tokens. Define revocation semantics for existing sessions and queued work.

### Verify before continuing
Log in with each synthetic role, then demonstrate that wrong-issuer, wrong-audience, expired and tampered tokens cannot access protected resources. Confirm key rotation does not disable verification.

### Save as evidence
Identity-provider configuration export without secrets; client settings; claim mapping; authentication integration tests.

## 06 / Secure browser sessions, CSRF and web delivery

### Entry conditions
Requires a chosen browser-auth design. This guide recommends evaluating a backend-for-frontend session for the same-origin console.

### Setup steps

1. If using backend sessions, exchange tokens server-side and keep them out of routine browser storage. Use opaque, rotated session identifiers with server-side invalidation.
2. Set cookies Secure on HTTPS, HttpOnly, an appropriate SameSite policy and narrow path/domain. Avoid sharing session cookies across unrelated subdomains.
3. Protect cookie-authenticated state-changing requests with the framework-supported CSRF mechanism and origin validation. SameSite alone is not a complete CSRF design.
4. If a public-client token design is selected, document XSS exposure, token storage and renewal controls. Never claim localStorage is a secure token vault.
5. Restrict CORS to exact origins and required methods/headers. Never combine arbitrary origin reflection with credentialed access.
6. Set a tested content security policy, frame protection, nosniff and appropriate referrer policy. Remove inline/eval permissions where feasible rather than copying a permissive template.
7. Escape model/document content and sanitise any rendered HTML/Markdown. Treat filenames, extracted text, comments and citations as untrusted; isolate unsafe document previews.

### Verify before continuing
Test missing/invalid CSRF tokens, cross-origin credentialed requests, stored-script payloads and logout/session revocation. Verify cookie/security headers in the actual deployed browser flow.

### Save as evidence
Session design ADR; cookie/CORS/CSRF configuration; browser security tests; CSP findings and fixes.

## 07 / Implement tenant and resource authorisation

### Entry conditions
Requires verified identity and stored membership. Apply to every API, worker, tool, download, citation and export.

### Setup steps

1. Define a deny-by-default matrix for requester, analyst, reviewer, tenant administrator and auditor. Separate platform administration from permission to read all tenant contents.
2. Construct trusted request scope from the verified identity and current membership. A tenant ID in a URL/header/body requests scope; it does not prove access.
3. Authorise both action and resource. Check document ACL/classification, case membership and reviewer duties rather than relying only on broad role names.
4. Use tenant-aware database references and repository APIs. Carry validated scope into jobs and reconstruct it from trusted records rather than serialising a browser claim.
5. Scope caches, search results, signed downloads, analytics, evaluation runs and feedback. Recheck access when a citation or original file is opened.
6. Handle revocation and long-running runs: revalidate membership and evidence permissions on resume and before tool/approval execution.
7. Test ID substitution, enumeration, cross-tenant list/search/export, administrator overreach and membership changes. Use independent identities, not only mock role strings.

### Verify before continuing
All cross-tenant attempts deny contents across API, worker, cache, retrieval and storage paths. Deactivated users cannot resume work or approve an old pending case.

### Save as evidence
Permission matrix; central policy API; scoped repository contracts; negative-access test suite.

## 08 / Harden PostgreSQL, database roles and row policies

### Entry conditions
Requires trusted scope and tenant-aware schema. Row-level security is defence in depth, not a substitute for application authorisation.

### Setup steps

1. Separate migration owner, runtime API/worker and reporting roles. Runtime roles must not be superusers, table owners or BYPASSRLS roles.
2. Restrict network connections, require appropriate transport security and manage authentication via the selected secret/workload identity mechanism. Avoid shared administrative connections.
3. Use parameterised queries, validated filters and least-privilege grants. Apply tenant-aware foreign keys/constraints and indexes to prevent unintended cross-tenant references.
4. Add row policies to each relevant tenant table and test reads, writes, joins and vector queries. Consider FORCE ROW LEVEL SECURITY while understanding owner/superuser bypass behaviour.
5. Set tenant context transaction-locally from server-verified scope and clear it through transaction lifecycle. Test pooled connections, background tasks and missing scope.
6. Scope object keys, audit tables and checkpoint stores too. Document necessary privileged maintenance paths and prevent them from becoming ordinary request paths.
7. Back up through approved roles and locations, audit administrative access and test schema migrations in an isolated database before promotion.

### Verify before continuing
Run isolation tests using the actual non-owner runtime role. With no tenant context, no rows are accessible; after connection reuse, previous tenant rows remain inaccessible.

### Save as evidence
Role/grant inventory; RLS migrations; pool/reset tests; privileged-path exceptions; tested recovery account process.

## 09 / Secure uploads, object storage and parser execution

### Entry conditions
Requires authorisation and private storage. Uploaded files are hostile inputs even when their filenames look harmless.

### Setup steps

1. Create private storage with public access blocked, encryption and version/lifecycle rules. Service identities receive only required object actions and prefixes.
2. Generate storage keys server-side. Validate actual media content, configured size/page limits and supported parsers; never use a client filename as a filesystem path.
3. Quarantine uploads pending validation/scanning policy. Reject unsupported/encrypted/unsafe files according to the documented contract without exposing parser internals.
4. Run parsing/OCR with least privilege, restricted network/filesystem access and CPU/memory/time limits. Do not mount cloud credentials or privileged container sockets into parser jobs.
5. Issue short-lived signed downloads only after current resource authorisation. URLs are bearer access until expiry; keep them out of logs and avoid overly long validity.
6. Protect preview rendering: safe content type/disposition and isolation as needed. Do not execute macros/scripts or trust text/HTML from extracted files.
7. Test malformed PDFs, large scans, archive expansion where supported, path-like names, cross-tenant object references and interrupted uploads. Keep failed versions non-searchable.

### Verify before continuing
An unauthorised user cannot obtain or reuse another tenant file link through the application. Unsafe files fail within limits and parser failure cannot reach secrets or private metadata endpoints.

### Save as evidence
Upload limits; storage/IAM rules; parser isolation profile; scanning policy; malicious-file and download tests.

## 10 / Protect RAG, embeddings, evidence and deletion

### Entry conditions
Requires document provenance and tested tenant authorisation. Derived AI data retains the source data sensitivity.

### Setup steps

1. Apply tenant, ACL, classification and policy-effective-date restrictions before passages enter model context. Recheck permissions when resolving citations.
2. Keep immutable document/pipeline/model versions and evidence page/table spans. Track superseded policies and surface conflicting evidence instead of merging it silently.
3. Govern embedding and reranking destinations separately from chat inference. Vectors and extracted text can carry sensitive information and need access/retention controls.
4. Treat retrieved passages as data, never instructions. Enforce tool and approval boundaries independently of prompt wording.
5. Validate every citation against permitted retrieved evidence. Refuse fabricated references and distinguish insufficient evidence from technical failure.
6. Propagate ACL revocation, withdrawal and deletion to text, chunks, vectors, caches and derived outputs. Verify results stop appearing rather than trusting a job status alone.
7. Define backup retention/legal-hold exceptions separately. After restore, reapply deletion and revocation records; do not promise immediate erasure from every historical backup.

### Verify before continuing
Adversarial queries cannot retrieve another tenant or withdrawn document. Cached answers and citation links honour current access. Source changes do not silently preserve outdated approval evidence.

### Save as evidence
Retrieval filter tests; provenance/citation validator; revocation/deletion verification; derived-data retention map.

## 11 / Secure model routes, prompts and sensitive outputs

### Entry conditions
Requires the classification/destination matrix and approved provider credentials. Use synthetic prompts for initial connectivity tests.

### Setup steps

1. Enforce an allowlist of provider, model, endpoint and permitted classification at one controlled gateway. Reject unknown or unapproved routes.
2. Verify actual inference, embeddings, OCR and telemetry processing terms/location. A product name or application region alone is not a residency guarantee.
3. Use structured output and independent schema/business validation. Bound input size, output length, calls, token use, elapsed time and spend per tenant/run.
4. Use bounded retries for transient errors; malformed output receives limited correction then failure/review. Do not retry forbidden requests indefinitely.
5. Keep instructions versioned in trusted code/configuration. Delimit user/document data, but assume prompt injection can still influence the model and enforce permissions elsewhere.
6. Redact sensitive telemetry and minimise submitted data. Never reveal secrets, raw headers or private operational context in model-readable prompts.
7. Allow only classification-compatible fallbacks and fail visibly otherwise. For private inference, review model licence/artifact integrity, network exposure and hardware isolation.

### Verify before continuing
A restricted request cannot reach an unapproved endpoint through normal or fallback paths. Invalid model output cannot change permissions, totals or case state.

### Save as evidence
Provider suitability record; gateway policy; prompt/schema versions; budget/fallback tests; live synthetic integration evidence.

## 12 / Constrain agents, tools and MCP integrations

### Entry conditions
Requires working deterministic services. Orchestration exposes existing permitted capabilities; it does not create authority.

### Setup steps

1. Define typed workflow state and an explicit graph. Persist case/evidence revisions, permission context references, budgets and cancellation state.
2. Register tools with exact schemas, server-side required permissions, allowed destinations, scoped identities, timeout, retry rule and output validation.
3. Treat tool names/arguments emitted by the model as proposals. Reject unknown tools, forbidden resources, arbitrary shell/SQL execution and user-controlled destinations.
4. For MCP, authorise the selected server and every tool separately, validate remote responses and manage credentials. Protocol support is not a trust decision.
5. Bound graph steps, calls, wall time and spend. Use sandboxed execution where computation is required; never give agents broad cloud/database administrator credentials.
6. On checkpoint resume, revalidate membership, document access, case revision and pending approval. Old persisted context must not grant permanent authority.
7. Use idempotency and reconciliation for effects, and make cancellation explicit. Test malicious documents that request secrets, cross-tenant reads, arbitrary URLs or approval bypass.

### Verify before continuing
Forbidden calls fail before execution, including via injected passages. Worker restart/cancellation is safe and duplicate messages do not produce duplicate simulated outcomes.

### Save as evidence
Tool contracts/allowlist; agent budget configuration; resume checks; injection/tool-abuse and recovery test records.

## 13 / Protect approvals, arithmetic and concurrent decisions

### Entry conditions
Requires case revisions, deterministic rules and an explicit reviewer authority matrix.

### Setup steps

1. Keep permissions, eligibility rules, Decimal calculations and state transitions in tested application code. Do not ask a model to authorise its own proposal.
2. Bind approval to tenant, case revision, evidence-version set, rule/policy/checklist versions and proposed action digest. Preserve the snapshot shown to the reviewer.
3. Require an authorised reviewer, decision and reason. Enforce separation of duties when the workflow requires independent review.
4. At decision time revalidate membership, resource scope, snapshot freshness and expected revision. Reject stale or conflicting requests instead of silently regenerating approval.
5. Invalidate pending approval after a relevant evidence/rule/comparison change. Keep historical decisions immutable and distinguish them from current approval.
6. Commit decision, case transition and audit atomically where possible. Use scoped idempotency keys and optimistic concurrency for duplicate/concurrent requests.
7. Keep sandbox outcomes visibly simulated. A future real connector needs explicit action scope, destination idempotency/reconciliation and separate operating authorisation.

### Verify before continuing
Change a quotation after review request, issue two decisions concurrently and replay an old key. Only the valid current transition succeeds and all attempts are auditable.

### Save as evidence
Approval digest contract; transition rules; independent calculation fixtures; stale/concurrent/revoked-reviewer tests.

## 14 / Harden API validation and application output

### Entry conditions
Requires identity and resource policy. Apply these checks to new endpoints as they are introduced.

### Setup steps

1. Validate request/response schemas, length/range bounds, enum values, pagination and upload sizes. Reject unexpected sensitive fields and mass assignment of server-owned state.
2. Use parameterised database access and safe object-key construction. Avoid dynamic SQL/shell templates and never interpolate model output into executable commands.
3. Return consistent safe errors and correlation IDs. Apply a deliberate 404/403 resource-existence policy without exposing other tenants identifiers.
4. Rate-limit expensive operations and constrain concurrency per tenant/user. Handle 429/retry behaviour without accidentally creating duplicate work.
5. Escape HTML and sanitise Markdown. Handle CSV/spreadsheet formula injection in exported reports and restrict unsafe hyperlink protocols.
6. Authorise exports, search filters, evaluation jobs and operational endpoints. Health/readiness must avoid secret details; management/debug endpoints stay restricted.
7. Test insecure object references, unexpected fields, huge filters, injection payloads, pagination abuse and server-side URL fetching. Keep public OpenAPI exposure a deliberate choice.

### Verify before continuing
Invalid inputs fail safely, expensive operations are bounded and output rendering cannot execute stored user/model content. Protected endpoints cannot be accessed through alternate routes.

### Save as evidence
API schema/limit specification; negative-input tests; output-encoding rules; endpoint access inventory.

## 15 / Secure queues, workers, checkpoints and caches

### Entry conditions
Requires distinct service identities and durable business state. Queue/cache products are not access-control boundaries on their own.

### Setup steps

1. Keep queues and caches private, authenticated and encrypted where required. Use separate environment credentials and restrict administrative commands.
2. Use safe serialisation and validated job schemas; do not accept arbitrary pickled objects or untrusted task names. Resolve sensitive state from trusted records.
3. Include verified tenant/resource scope and idempotency identity. Recheck access when a job executes rather than assuming submission-time permission lasts indefinitely.
4. Scope cache keys/results to tenant, resource permissions and relevant evidence versions. Define expiration and explicit invalidation for ACL/source changes.
5. Use bounded retries, dead-letter/manual recovery and visible failure state. Apply parser/model resource budgets and stop retry storms.
6. Persist checkpoints securely and minimise sensitive content. Reconcile uncertain effects before replay; cancellation stops future work but cannot erase completed effects.
7. Test duplicate job delivery, connection loss, poisoned payloads, revoked membership and connection-pool reuse. Monitor queue age and stalled workflows.

### Verify before continuing
Replaying a message or restoring a worker does not leak data or repeat an outcome. Cache hits cannot bypass current permissions and failed work is discoverable.

### Save as evidence
Queue/worker permissions; payload schema; idempotency/retry policy; cache invalidation and restart tests.

## 16 / Set up redacted telemetry and protected audit evidence

### Entry conditions
Requires correlation IDs, classification policy and named operational users.

### Setup steps

1. Separate business audit events from diagnostic logs and AI traces. Define event schemas with actor/service, tenant, resource, revision, timestamp, action and outcome.
2. Avoid raw documents, prompts, credentials, headers, signed URLs and full connection strings in routine logs. Implement redaction before export, including failure paths.
3. Choose approved telemetry destinations and retention. Self-host if the selected profile requires it; observability SaaS is another data-processing provider.
4. Restrict log/audit readers and writers. An append-only application interface is insufficient for tamper protection; use separately protected integrity evidence or immutable retention where required.
5. Instrument authentication failures, denied tools, stale approvals, deletion failures, provider routing, spending, queue backlog and unusual downloads without exposing contents.
6. Configure alerts with recipients and escalation. Protect correlation IDs and user-facing error messages from becoming a resource enumeration channel.
7. Verify clock synchronisation and audit continuity across API/worker/release. Test that administrative modification is denied or detected under the selected integrity design.

### Verify before continuing
Inspect synthetic success/failure traces for redaction. Demonstrate an alert reaches its owner and auditors can reconstruct a review without unnecessary document contents.

### Save as evidence
Audit schema; retention/access rules; redaction tests; integrity-control design; alert exercises.

## 17 / Secure containers, dependencies and CI/CD

### Entry conditions
Requires locked dependencies and defined deployment identity. Build integrity protects every runtime security control.

### Setup steps

1. Use supported minimal base images and pinned tested dependencies. Keep package signatures, checksums and TLS verification enabled; review model/parser artifact sources too.
2. Run containers as non-root with minimal capabilities and resource limits. Use read-only filesystems where feasible and writable paths only for intended state.
3. Do not expose the Docker socket or privileged mode to parsers/agents. Keep build secrets out of layers; use supported ephemeral secret injection.
4. Scan dependencies/images and generate an SBOM using vetted tooling. Triage vulnerabilities; critical unresolved findings block release under the project gate.
5. Restrict CI job permissions and third-party actions, pin action revisions according to policy and protect release workflows. Do not expose secrets to untrusted pull-request code.
6. Use short-lived deployment identity where available and exact trust conditions. Separate test, staging and production-like credentials and approvals.
7. Promote the same tested artifact digest. Run schema compatibility and deployed smoke tests; preserve signing/provenance evidence appropriate to the environment.

### Verify before continuing
Image history/configuration contains no credentials; runtime is non-root and resource-limited; CI cannot deploy from an untrusted change; scan findings and artifact identity are recorded.

### Save as evidence
Container policy; SBOM/scan report; CI trust settings; artifact digest/provenance; pipeline permission review.

## 18 / Configure cloud IAM, storage, keys and private services

### Entry conditions
Requires approved region/services, budget and deployment authorisation. AWS examples map to equivalent approved cloud/private controls.

### Setup steps

1. Use a dedicated account/project/environment with named administrators and MFA. Define emergency access and review it; avoid daily root/owner operation.
2. Provision using reviewed IaC with encrypted/restricted state. Separate staging and production-like data and protect plans from leaking sensitive values.
3. Keep databases, queues and management ports private. Expose only intended TLS ingress; restrict security-group/service-to-service paths and outbound destinations.
4. Use workload roles for API, worker, migration, CI and recovery. Grant least-privilege actions/resources and constrain role trust; avoid universal wildcard policies.
5. For object storage block public access, configure encryption, versioning, lifecycle and logging. Prefix scoping helps only when trusted code/identity establishes the correct tenant.
6. Manage secrets and encryption keys with approved services and access separation. Define key rotation and recovery; losing a key can make backups unrecoverable.
7. Verify inference, backup, telemetry, support and DR locations/terms. Test actual identity and network permissions from the deployed runtime, not only desired IaC configuration.

### Verify before continuing
Unauthorised public access and cross-service roles fail, runtime reaches only required destinations and the deployed configuration matches recorded residency assumptions.

### Save as evidence
IAM/trust review; network/storage/key configuration; actual runtime tests; cloud audit and residency evidence.

## 19 / Run security tests, adversarial evaluation and release gates

### Entry conditions
Testing starts per feature; this stage assembles independent evidence for release.

### Setup steps

1. Freeze code/artifact, dependencies, schema, configuration, prompt/model/rule versions and dataset manifest. Use an isolated synthetic environment for adversarial tests.
2. Run authentication, cross-tenant, database RLS, download, cache, export, worker and reviewer tests using real runtime roles and independent identities.
3. Test malicious PDFs, parser exhaustion bounds, stored scripts, API injection, SSRF/redirect behaviour and unsafe tool proposals without attacking unrelated services.
4. Inject documents that request secrets, tool execution or approval bypass. Verify action checks hold even when a model repeats the malicious request.
5. Test stale/concurrent approvals, revoked membership, duplicate requests, process restarts, forbidden model fallback and deleted-source retrieval.
6. Review scans and sampled logs for leaked sensitive data. Track issue severity, owner, fix, regression and any explicitly accepted noncritical risk.
7. Block release on any mandatory authorisation/approval/isolation failure or unresolved critical finding. Report failed, skipped and unrun checks separately; passing finite tests is not proof of perfect security.

### Verify before continuing
All mandatory scenarios pass with reproducible evidence and known limitations. An independent reviewer can follow findings to code/configuration and retest the fix.

### Save as evidence
Security test report; red-team results; vulnerability register; release decision with artifact/environment identifiers.

## 20 / Test backups, restore, rollback and incident response

### Entry conditions
Requires operational ownership, approved backup locations and encryption key recovery.

### Setup steps

1. Define RTO/RPO and retention from business needs, then configure database/object backups, recovery credentials and monitoring. Do not invent achieved guarantees.
2. Restore into an isolated environment and verify document versions, ACLs, memberships, case revisions, approval snapshots and checkpoint consistency.
3. Reapply deletion, access revocation and legal-hold obligations. Prevent restored queues from replaying uncertain effects before reconciliation.
4. Exercise application rollback against a compatible schema. Use expand/migrate/contract changes and a documented alternative when database rollback is unsafe.
5. Write incident playbooks for credential leak, tenant disclosure, malicious upload, compromised model route and deployment failure. Assign containment, evidence, communication and recovery owners.
6. On a credential incident revoke/rotate promptly, scope access, preserve authorised evidence and redeploy clean bindings. Do not publish raw sensitive logs in issue trackers.
7. Run a tabletop and practical restore exercise. Record actual recovery times, data loss, alert delivery, decisions and gaps; fix gaps before describing the system as operationally ready.

### Verify before continuing
An operator restores a representative case, permissions and review integrity from backups and executes a tested rollback. An incident alert reaches accountable people.

### Save as evidence
Restore/rollback report; measured recovery; incident playbooks; emergency-access test; key recovery and deletion reapplication evidence.

## 21 / Launch safely and maintain the security baseline

### Entry conditions
Requires passing security gates and operator/data-owner approval for the actual deployment scope.

### Setup steps

1. Complete a launch checklist for identity, permissions, source use, model route, network, secrets, scans, backups, logging, alerting, budget and known limitations.
2. Run a deployed synthetic canary: login, case upload, cited answer, comparison, approval and audit. Confirm forbidden operations fail in the deployed environment too.
3. Start with bounded users/data and a manual fallback. A portfolio remains a sandbox until authorised for another use; do not advertise compliance from a demo.
4. Review alerts, denials, spending, failures and quality frequently during stabilisation. Set rollback/disable triggers and keep release artifacts recoverable.
5. Schedule dependency patches, credential rotation, access reviews, provider-term checks, backup restores and model/red-team regression tests according to risk.
6. Reassess threats when adding a domain, connector, model, region or classification. HR/service desk/forecasting inherit controls but need separate access/evaluation scenarios.
7. Plan retirement: revoke identities/keys, stop jobs, export authorised records, apply retention/deletion, remove infrastructure safely and confirm charges stop.

### Verify before continuing
Named operators maintain tested runbooks, access and alerts. Security status reflects actual observations and outstanding risks rather than a one-time installation claim.

### Save as evidence
Signed-off launch record; maintenance calendar; change/review process; handover and retirement checklist.

## Appendix A — Configuration contract and safe local startup

### Configuration example — non-secret values only

```
APP_ENV=local
AUTH_REQUIRED=true
OIDC_ISSUER=<trusted-issuer-url>
OIDC_AUDIENCE=<application-audience>
WEB_ORIGIN=<exact-frontend-origin>
DATA_PROFILE=synthetic_sandbox
MODEL_ROUTE=<approved-route-name>
LOG_DOCUMENT_CONTENT=false
UPLOAD_MAX_BYTES=<validated-limit>
PARSER_TIMEOUT_SECONDS=<validated-limit>
AGENT_MAX_STEPS=<validated-limit>
TENANT_BUDGET_LIMIT=<approved-budget>
```

### Do not copy these as working application settings

These are proposed setting names and placeholders, not an existing configuration API. DATABASE_URL, object-store credentials and model tokens are secrets when they contain credentials. Supply them through the selected secure mechanism. Validate exact names/defaults during implementation.

### Local network example

Bind development database, queue and admin ports to 127.0.0.1 if host access is required; otherwise keep them on an internal Compose network. Do not publish every container port. Enforce identity before shared access. A local HTTP exception must never become the deployed cookie/TLS configuration.

### Startup order

Prepare locked dependencies → start private data/identity services → load secure bindings → apply reviewed migrations → seed synthetic users/tenants → start API/worker/web → run readiness and negative-access tests. This guide does not implement the application or claim these steps already pass.

## Appendix B — Database tenant policy example

### Illustrative SQL for a new sample table

```
-- Example only: adapt to reviewed migrations.
CREATE TABLE case_scope_example (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL,
  title text NOT NULL
);
ALTER TABLE case_scope_example ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_scope_example FORCE ROW LEVEL SECURITY;
CREATE POLICY case_tenant_scope ON case_scope_example
USING (
  tenant_id = NULLIF(
    current_setting('app.tenant_id', true), ''
  )::uuid
)
WITH CHECK (
  tenant_id = NULLIF(
    current_setting('app.tenant_id', true), ''
  )::uuid
);
```

### Trusted application context

Within the transaction, use a parameterised call equivalent to SELECT set_config('app.tenant_id', :verified_tenant_id, true). The value must come from checked membership, not an unchecked request header. Transaction-local context avoids leaking across connection reuse.

### Limitations that matter

Create/grant non-owner runtime roles separately. Superusers and BYPASSRLS roles bypass policies. A compromised application role that can alter tenant context is not isolated from all tenants by this example alone. It does not implement per-document ACLs, column-level privacy or authorisation for tools/storage. Apply policies to each relevant table and test real joins, inserts, updates, workers and vector queries.

### Required proof

With runtime role and missing scope: no rows visible. With tenant A scope: only A rows visible/writable. Wrong-tenant insert/update: denied. Reused pooled connection: no prior scope. Privileged maintenance roles: documented and unavailable to request paths.

## Appendix C — Permission and approval reference

### Requester

Create/submit permitted cases and view permitted evidence. Cannot assign an arbitrary tenant, change server-owned state or approve when independent review is required.

### Analyst

Attach authorised submissions, review extraction, apply auditable corrections and request review. Cannot forge policies, reviewer identity or current approval.

### Reviewer

Inspect permitted current evidence; approve, reject or request information with a reason. Membership, separation of duties and snapshot freshness are checked at decision time.

### Tenant administrator / auditor

Tenant administrator manages scoped membership/configuration. Auditor reads permitted history without modifying cases. Neither role automatically receives unrestricted cross-tenant content access.

### Approval snapshot fields

tenant_id; case_id; case_revision; evidence_version_ids; checklist/policy/rule versions; comparison/action digest; requested_by; requested_at; expected_reviewer policy. Decision adds actor, outcome, reason and timestamp. Revalidate against current state atomically.

### Minimum immutable evidence

Keep historical approved snapshots and decision audit distinct from current case state. Record denied/stale attempts safely. A new version does not inherit a previous decision.

## Appendix D — Model and tool deny-by-default pseudocode

### Conceptual policy — not executable integration code

```
scope = verify_identity_and_membership(request)
resource = load_authorised_resource(scope, resource_id)
route = policy.permitted_route(resource.classification)
if route is None:
    deny("No approved processing route")

proposal = model_call(route, bounded_context(resource))
validate_output_schema(proposal)
if proposal.requests_tool:
    tool = allowlisted_tool(proposal.tool_name)
    authorise(scope, tool.action, proposal.resources)
    validate_tool_args_and_destination(proposal)
    enforce_runtime_and_spending_budget(scope)
    if tool.requires_approval:
        verify_current_approval_snapshot(resource, proposal)
    execute_with_idempotency_and_reconciliation(tool)
else:
    validate_citations_and_safe_rendering(proposal)
```

### Important interpretation

The model response is a proposal, never proof of access or approval. Output schema validation proves structure, not truth. Recheck scope on long-running resume. Public/private inference alternatives must satisfy the same classification policy and budgets.

### Forbidden shortcuts

No arbitrary shell/SQL tool, broad cloud administrator key, unfiltered retrieved context, unchecked callback URL, user-controlled provider endpoint or silent external fallback for restricted data. Add new connector capabilities through reviewed contracts and negative tests.

## Appendix E — Security test matrix and evidence record

### AUTH / TENANCY

Missing/expired/wrong issuer/audience token denied; disabled membership denied; cross-tenant IDs/search/citation/download/export denied; runtime row policies and pooled scope verified; cache/job paths cannot bypass permission.

### FILES / RAG

Malformed and oversized files fail safely; parser cannot reach private metadata or secrets; forged filenames cannot escape storage; withdrawn evidence disappears from retrieval; citation access rechecked; signed-link exposure/expiry understood.

### AGENTS / APPROVALS

Prompt injection cannot execute forbidden tools; model cannot self-approve; stale snapshot rejected; concurrent/duplicate decisions safe; checkpoints revalidate access; budgets and retries bounded; restricted route never uses forbidden fallback.

### APPLICATION / SUPPLY CHAIN

Stored scripts and spreadsheet formula exports handled; CSRF/CORS/session controls tested; API fields/limits enforced; dependency/image findings triaged; CI secrets not available to untrusted code; artifact identity recorded.

### OPERATIONS

Logs redact secrets/content; alert delivered; restore/rollback demonstrated; revocations/deletions reapplied; uncertain jobs reconciled; incident ownership and credential revocation exercised.

### Result template

Control ID | scenario | environment | artifact/config/model/rule versions | test data version | expected/actual | pass/fail/skip | evidence link | defect/owner | retest date. Mandatory skipped/unrun scenarios do not constitute a pass.

### Release decision

All mandatory authorisation, isolation and approval checks pass; no unresolved critical finding; real-data processing/profile approved; restoration and operational ownership proven. Report residual risks and limits honestly.

## Appendix F — Operational checklist and official references

### Regular review

Monitor alerts and failures during operation; schedule account/access review, patching, credential rotation, policy/provider changes, backup restore and adversarial regression based on risk. There is no universal rotation interval that replaces a documented operating policy.

### Incident quick reference

Contain affected access/egress → preserve authorised evidence → assess scope → revoke/rotate credentials if relevant → recover/reconcile → verify isolation and approval state → communicate under applicable obligations → document root cause and regression. Obtain qualified guidance for legal notification duties.

### Official security references

OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/ ; OWASP GenAI: https://genai.owasp.org/ ; Keycloak: https://www.keycloak.org/documentation ; PostgreSQL row security: https://www.postgresql.org/docs/current/ddl-rowsecurity.html .

### Official platform references

FastAPI security: https://fastapi.tiangolo.com/tutorial/security/ ; Docker: https://docs.docker.com/ ; AWS IAM: https://docs.aws.amazon.com/IAM/latest/UserGuide/ ; S3 security: https://docs.aws.amazon.com/AmazonS3/latest/userguide/security.html ; MCP: https://modelcontextprotocol.io/ .

### Source and verification note

Based on the project architecture, technology stack, eight specifications and 26-phase implementation guide. References are starting points, not a live verification of current product settings, service availability or applicable UAE/entity law. Validate controls against selected supported versions and obtain deployment-specific review.
