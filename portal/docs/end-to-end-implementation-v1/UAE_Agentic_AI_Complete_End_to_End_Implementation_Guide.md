# UAE Sovereign Agentic AI — Complete End-to-End Implementation Guide

Version 1.0 | 6 November 2026 | Proposed plan; implementation and validation pending.

26 sequential phases, numbered 00–25, plus seven practical appendices.

## Phase 00 — Define scope, outcomes and delivery ownership

### Objective and entry conditions
Start here. Read the eight project specifications and agree that the first release is an independent procurement sandbox using public or synthetic data.

### Implementation steps

1. Write the problem statement: analysts need evidence-linked policy answers and quotation comparisons, while authorised reviewers retain responsibility for decisions. Name the first users and their pain points.
2. Choose one demonstration journey: create a case, upload quotations, retrieve applicable policy, compare evidence, request review and record a simulated outcome. Keep this journey visible in the backlog.
3. List in-scope features and explicit exclusions. Exclude real payments, awards, government-system access and unrestricted autonomous actions from the sandbox. Later domains remain named, staged deliverables.
4. Assign product, engineering, data, security and reviewer responsibilities. A solo developer may fill several roles, but independent reviewer identities must still exist in tests.
5. Record weekly development availability, hardware constraints, monthly spending limit and target deployment profile. Do not treat the original 30-week outline as a guaranteed schedule.
6. Define success measures: reviewed-case completion, citation quality, extraction accuracy, permission correctness, recovery, user corrections and cost. Separate learning outcomes from business outcomes.
7. Create a backlog with requirement IDs, priority, acceptance criteria, dependencies and evidence links. Define what counts as done and how scope changes are recorded.
8. Record assumptions and open decisions, including approved model provider, identity provider and authorised data sources. Continue synthetic-data work while deployment-specific choices remain open.

### Deliverables
Project brief; prioritised PRD; owner/decision register; risk register; acceptance checklist and first demonstration script.


### Validation and exit gate
Every MVP feature maps to a user need and a testable acceptance criterion. The first case journey has a named reviewer, explicit exclusions and a feasible resource envelope.


### Failure handling and recovery
Reduce features before weakening permission or evidence requirements. If real-data permissions are absent, retain the synthetic sandbox rather than assuming authorisation.

## Phase 01 — Map business workflow, policy and user experience

### Objective and entry conditions
Requires Phase 00 scope. Design the workflow before automating it; use representative synthetic procurement records.

### Implementation steps

1. Draw the current manual process and proposed assisted process. Identify who submits, extracts, corrects, reviews and audits each case, including handoffs and waiting states.
2. Define case states: draft, submitted, processing, needs_information, awaiting_review, approved_simulation, rejected, cancelled and failed. Document allowed transitions and terminal-state behaviour.
3. Define required intake fields, submission checklist, policy effective date, quotation validity and evaluation criteria. Mark unknown, missing and not-applicable values separately.
4. Write the authority matrix for requester, analyst, reviewer, tenant administrator and auditor. Decide where independent review is required and prohibit self-approval when configured.
5. Specify exception paths for missing documents, conflicting policy, unsupported currency, OCR failure, stale approvals, unavailable models, cancellation and concurrent decisions.
6. Sketch the case list, intake form, upload queue, evidence viewer, comparison worksheet, review queue and audit timeline. Include loading, empty, denied and failed states.
7. Design English and Arabic navigation, reading order and mixed-direction identifiers. Keep source text visible beside generated summaries and indicate when evidence is incomplete.
8. Walk one complete synthetic case through the sketches with a reviewer. Capture disagreements and refine workflow rules before implementation.

### Deliverables
Workflow/state diagrams; role-action matrix; low-fidelity screens; exception catalogue; approved synthetic case walkthrough.


### Validation and exit gate
Every state has an entry condition, permitted actor, next action and failure path. A user can locate evidence and understand what a review decision approves.


### Failure handling and recovery
Resolve unclear business rules explicitly. Do not let the model infer official eligibility rules or invent an approval hierarchy.

## Phase 02 — Set architecture, sovereignty profile and threat model

### Objective and entry conditions
Requires Phases 00-01. This phase governs all later technology and provider choices.

### Implementation steps

1. Draw component and data-flow diagrams: React console, FastAPI, domain services, worker, PostgreSQL/pgvector, object storage, identity provider, model gateway and telemetry.
2. Choose a modular application with separate API and worker processes. Identify module boundaries for cases, documents, retrieval, policies, approvals and evaluations.
3. Classify data and map every destination: documents, OCR, embeddings, inference, logs, backups, keys, support access and disaster recovery. Record owner and permitted processing locations.
4. Select a profile: public/synthetic sandbox, verified UAE residency-constrained service, or restricted/private inference. Hosting in a UAE region alone is not proof of sovereignty.
5. Record provider terms, model licences, subprocessors and allowed egress. Require equivalent policy for fallback models; restricted data must never silently leave through another endpoint.
6. Threat-model cross-tenant leakage, malicious uploads, prompt injection, stale approvals, credential exposure, poisoned policy, duplicate actions and supply-chain compromise.
7. Define controls, test scenarios, residual risks and accountable owners. Separate trusted application instructions from untrusted document content and model suggestions.
8. Write architecture decision records for tenancy, model gateway, storage, orchestration and deployment. Defer Kubernetes, multiple vector databases and streaming until justified.

### Deliverables
Architecture/data-flow diagrams; classification/residency matrix; threat model; initial ADRs; approved provider/egress requirements.


### Validation and exit gate
All data paths and trust boundaries are accounted for. The sandbox can proceed without real-data credentials. Reviewers can explain what sovereignty claims are and are not supported.


### Failure handling and recovery
If residency, contractual or operational requirements cannot be met, restrict the profile or provider. Do not bypass egress policy or disable TLS verification.

## Phase 03 — Prepare workstation, repository and reproducible tools

### Objective and entry conditions
Requires Phase 02 baseline choices. The existing repository initially contains documentation, not an application scaffold.

### Implementation steps

1. Inspect the checkout, README, agent instructions and current Git status. Preserve existing user changes. Cloud tasks are already isolated; do not create a worktree unless requested.
2. Select and record supported Python, Node.js LTS, PostgreSQL and Docker/Compose versions. Verify operating-system compatibility, disk space, memory and CPU before large installs.
3. Use one primary editor, such as VS Code or Cursor. Configure Python debugging, TypeScript support, Git and Docker integration; additional coding assistants are optional.
4. Create the repository layout described in Appendix B. Put application modules in one canonical backend path; avoid two competing API implementations.
5. Create Python and frontend dependency manifests and lockfiles. Choose one Python package workflow and one JavaScript package manager, and record frozen-install commands.
6. Create ignore rules for secrets, uploads, caches, virtual environments, generated indexes and runtime logs. Add a non-secret environment example and configuration schema.
7. Inspect existing authentication bindings by name/presence only. Verify required read-only Git access using the configured proxy before requesting any GitHub token.
8. Configure linting, formatting, type checking and useful pre-commit hooks. Write a setup README containing exact working directories and commands actually verified on this machine.

### Deliverables
Repository layout; tool/version record; locked dependencies; ignore rules; environment example; reproducible setup README.


### Validation and exit gate
A clean supported environment installs locked dependencies without changing lockfiles or bypassing verification. Git status contains only intentional changes; no secrets are tracked.


### Failure handling and recovery
Diagnose network, trust or version failures separately. Use approved registries and CA configuration; never replace checksums or turn verification off to force an install.

## Phase 04 — Build the application foundation and early CI

### Objective and entry conditions
Requires Phase 03. This is the first coding milestone; identity is added before shared or non-local exposure.

### Implementation steps

1. Implement FastAPI application creation, validated settings, versioned routing, structured safe errors, request correlation IDs and redacted logging.
2. Implement separate liveness and readiness endpoints. Liveness reports process health; readiness checks the dependencies required to serve the selected workflow without exposing secrets.
3. Create SQLAlchemy database sessions and the first Alembic migration. Add a minimal synthetic case model with UUID, revision, state and timestamps.
4. Implement local-development case create/read endpoints with typed request/response schemas and deterministic validation. Label temporary local-only authentication behaviour explicitly.
5. Build a React/TypeScript shell with navigation, API client, case list and error boundary. Validate environment-specific API configuration rather than hard-coding deployment URLs.
6. Create Compose services and health checks for the initial API/database stack. Add worker, storage and identity services when their phases require them.
7. Write integration tests for database persistence, invalid input and dependency readiness. Use disposable test data and avoid pointing tests at a production-like database.
8. Add CI jobs for locked installation, relevant lint/type checks, backend tests, migration smoke test and frontend build. Protect the main branch according to repository practice.

### Deliverables
Running local API/web/database; first migration; synthetic case persistence; CI pipeline; foundation startup instructions.


### Validation and exit gate
From a clean setup, create and retrieve a case, restart the API and confirm persistence. Confirm readiness fails when a required dependency is unavailable and CI executes real tests.


### Failure handling and recovery
Keep the scaffold local until identity and permissions are complete. A successful health response alone does not validate the business workflow.

## Phase 05 — Implement identity, sessions and membership

### Objective and entry conditions
Requires Phase 04 foundation and the Phase 02 identity decision.

### Implementation steps

1. Configure a development OIDC identity provider, such as Keycloak, with application client, exact redirect URIs and documented realm/client setup.
2. Choose the browser session architecture deliberately: backend-managed secure session or an appropriately secured public-client flow. Implement PKCE, CSRF and cookie/token controls as applicable.
3. Verify token issuer, audience, signature, expiry and intended token use. Support trusted signing-key rotation and safe handling of provider outages.
4. Create User, Tenant and Membership entities. Link identity by stable subject/issuer, not mutable email alone, and define invitation/activation/deactivation behaviour.
5. Implement login/logout, current-user and membership-selection endpoints. Tenant selection must be checked against server-side membership.
6. Seed synthetic tenants and identities for requester, analyst, reviewer and auditor. Keep bootstrap credentials outside tracked source and use a safe local reset process.
7. Implement session expiry and revocation handling. Require renewed access checks for long-running workflows and pending review operations.
8. Add integration tests for missing, invalid, expired and wrong-audience tokens, disabled membership and forbidden tenant selection. Verify unauthenticated access is denied.

### Deliverables
OIDC configuration/runbook; protected API routes; membership model; login UI; identity integration tests.


### Validation and exit gate
Known synthetic users can authenticate and select only valid memberships. Invalid tokens and disabled memberships cannot read cases or documents.


### Failure handling and recovery
Do not disable signature checks to fix login. Distinguish callback/CORS errors from provider trust or clock issues, and inspect only safe authentication metadata.

## Phase 06 — Enforce tenant isolation, permissions and audit

### Objective and entry conditions
Requires Phase 05 identity. Apply these primitives before real document ingestion or multi-user demonstrations.

### Implementation steps

1. Implement the role-action matrix as deny-by-default policies. Add resource and classification attributes where role checks alone cannot express access.
2. Resolve tenant scope from verified membership and pass explicit context through API, repositories, jobs and tools. Do not trust tenant IDs supplied by the browser.
3. Add tenant-aware foreign keys/constraints and PostgreSQL row policies where appropriate. Document bypass roles and test scope reset with pooled connections.
4. Define document ACLs for owners, groups or roles. Protect list/search, direct retrieval, citation resolution, exports and object downloads consistently.
5. Implement append-only application audit events for case, evidence, access-sensitive actions and decisions. Record actor, tenant, resource, action, revision, time, outcome and correlation ID.
6. Separate business audit retention from operational debug logs. Restrict audit readers and mutation privileges; plan separately protected integrity evidence for stronger assurance.
7. Apply rate limits and tenant budgets to expensive operations. Ensure cache keys and worker identities carry tenant/resource scope.
8. Test cross-tenant object substitution, search leakage, admin overreach, revoked permissions and direct storage references. Test tenant-scoped analytics and evaluation access too.

### Deliverables
Policy module; scoped repositories/jobs; audit schema/viewer; isolation test matrix; permission administration flow.


### Validation and exit gate
All mandatory authorisation tests pass, including pooled connections and background processing. No platform role gains universal content access merely by default.


### Failure handling and recovery
Block subsequent shared releases on any isolation failure. Do not rely on unguessable identifiers, UI hiding or database policies alone as proof of authorisation.

## Phase 07 — Collect synthetic data and establish evaluation ground truth

### Objective and entry conditions
Requires Phases 00-02; implementation of fixtures uses Phase 06 data boundaries.

### Implementation steps

1. Create the source register with owner, origin, licence/permission, classification, language, effective dates, retention and allowed processing destinations.
2. Generate the initial 30 synthetic suppliers, 10 cases, 20 quotations and 10 public/synthetic policies. Label synthetic organisations and documents clearly.
3. Include English and Arabic, born-digital PDFs, scans, tables, mixed-direction fields, expired records, missing information and conflicting policy versions.
4. Create case checklists, approval matrices and expected comparisons. Recalculate prices and dates deterministically so the ground truth does not inherit model errors.
5. Define annotation guidelines for relevant evidence, citation locations, extraction values, acceptable answer facts and required abstention. Review ambiguous labels with another reader.
6. Build at least 100 reviewed knowledge questions, balanced initially by language. Add separate extraction, workflow, permission-denied and adversarial cases.
7. Split development/validation/held-out sets by document family or case. Remove near-duplicates across splits and version the manifests and annotation changes.
8. Create seed/import tools and dataset validators. Publish generation assumptions and coverage gaps so synthetic success is not mistaken for real-world performance.

### Deliverables
Source register; synthetic fixtures; annotation guide; versioned dataset splits; expected answers/fields/citations; seed validation tools.


### Validation and exit gate
Every sample has a permitted-use basis and provenance. Labels are internally consistent, splits avoid known leakage, and both languages include failure/abstention cases.


### Failure handling and recovery
If authoritative documents are unavailable, use clearly fictional policy examples. Do not fabricate government policy or describe generated samples as official records.

## Phase 08 — Implement secure uploads, object storage and lifecycle

### Objective and entry conditions
Requires Phases 06-07. Store evidence versions before implementing retrieval.

### Implementation steps

1. Define Document, DocumentVersion and processing states. Each accepted version gets an immutable content hash, media type, size, language and internal storage reference.
2. Configure local S3-compatible storage or another approved storage implementation. Use private buckets, scoped service identities and version-safe object keys.
3. Implement authorised upload endpoints with configured size/type/page limits and actual content validation. Reject unsafe paths and unsupported files with safe, actionable errors.
4. Introduce quarantine/scanning policy and parser resource budgets. Restrict fetch-by-URL features or omit them until SSRF and egress controls are implemented.
5. Create a durable ingestion job record and enqueue by document-version/pipeline-version key. Return accepted status and expose progress rather than blocking a request on parsing.
6. Implement authorised metadata, version listing and short-lived download access. Enforce ACLs on every request, including citation-linked access.
7. Implement withdrawal, supersession, permission revocation and deletion scheduling. Plan cleanup of originals, extracted text, vectors, caches and derived artifacts.
8. Test duplicate upload behaviour, oversized/malformed files, unauthorised downloads, job-delivery failures and deletion retries. Ensure incomplete versions never become searchable.

### Deliverables
Versioned storage service; upload/status/download APIs; lifecycle schema; ingestion job plumbing; access and file-validation tests.


### Validation and exit gate
A permitted upload survives restart, has an auditable version and a visible processing state. Forbidden downloads and unsafe files are blocked; lifecycle jobs are idempotent.


### Failure handling and recovery
Keep failed items quarantined or failed with a reason. Do not mark them ready or repeatedly enqueue unbounded work; provide authorised retry after diagnosis.

## Phase 09 — Build parsing, OCR, tables and provenance

### Objective and entry conditions
Requires Phase 08 uploads and Phase 07 labelled samples.

### Implementation steps

1. Choose one parser baseline using supported/licensed libraries. Implement text PDF and TXT first; add DOCX in the documented parser contract if required.
2. Detect image-only pages and apply OCR only where needed. Install English/Arabic language resources through approved sources and preserve verification.
3. Preserve original file/version, page numbers, section identifiers, text spans and table coordinates or cell references. Keep extracted text separate from the original.
4. Represent tables structurally before flattening them. Preserve headers, units, currencies and multi-page relationships needed for quotation comparison.
5. Maintain original Arabic text and a separate normalised search representation. Evaluate punctuation, diacritics, numerals and mixed-direction fields without destroying evidence alignment.
6. Create chunking rules that preserve section/table context and provenance. Store chunk and pipeline versions so reprocessing does not silently rewrite evidence.
7. Validate parser output and mark unreadable or partial pages explicitly. Add controlled reprocessing, timeout, memory and page-count limits.
8. Benchmark on labelled clear/scanned samples by language and document type. Inspect table and OCR errors that would alter prices, identifiers or dates.

### Deliverables
Parser/OCR adapter; structured page/table output; chunk schema; provenance resolver; ingestion quality report and regression fixtures.


### Validation and exit gate
A reviewer can open each extracted field at its source page. Arabic/English scan failures are visible and page/table provenance remains correct through reprocessing.


### Failure handling and recovery
Route low-quality critical fields for human correction. Do not treat successful OCR execution as evidence that extracted values are accurate.

## Phase 10 — Implement model gateway, structured output and budgets

### Objective and entry conditions
Requires Phase 02 provider policy, Phase 06 permissions and Phase 07 synthetic data. Live credentials are needed only for the selected approved route.

### Implementation steps

1. Define provider interfaces for chat/extraction and embeddings. Keep provider-specific code behind adapters and record exact model identifiers and configuration.
2. Inspect existing credential bindings by name/presence, then test a minimal permitted operation. Declare missing secrets securely in environment settings, never in chat or source.
3. Enforce allowed provider/model and processing location by data classification. Document fallback policy and deny routes that cannot meet it.
4. Implement typed structured output with schema validation. Keep unknown values explicit and validate business fields independently from model syntax.
5. Version system prompts and template inputs. Delimit untrusted documents and ensure tools/actions remain authorised in server-side code.
6. Set per-call timeout, bounded retry, token/step limits and tenant spending budgets. Respect provider retry guidance and avoid retrying invalid permission requests.
7. Add redacted request metadata, model/version, duration, tokens, outcome and cost records. Do not log raw sensitive prompts by default.
8. Provide deterministic fixtures for unit tests and a separate budgeted live-provider smoke suite. For private inference, benchmark compatible model licence, memory and hardware before deployment.

### Deliverables
Model/embedding adapters; versioned prompts; routing/budget controls; safe telemetry; mock and live smoke-test separation.


### Validation and exit gate
Approved synthetic requests succeed with validated output. Invalid output fails safely, budgets bound work, and restricted requests cannot escape through fallback.


### Failure handling and recovery
If the route is unavailable, continue deterministic tests and record the live-integration blocker. Never claim mocked results validate real provider behaviour.

## Phase 11 — Implement permission-filtered hybrid retrieval

### Objective and entry conditions
Requires Phases 06, 09 and 10. Use Phase 07 labels to benchmark retrieval before answer generation.

### Implementation steps

1. Create versioned embedding jobs for permitted chunks. Record embedding model, dimension and pipeline version; prevent incompatible vectors from sharing an index silently.
2. Implement PostgreSQL lexical search and pgvector retrieval. Benchmark Arabic/English tokenisation and normalisation; choose language-specific alternatives only on evidence.
3. Apply tenant, ACL, classification, status and policy-effective-date constraints before candidates enter model context. Ensure version supersession is handled deliberately.
4. Implement candidate fusion and configurable top-k. Start with simple documented methods and measure gains over lexical-only and vector-only baselines.
5. Add reranking only if it improves held-out relevance within cost and latency constraints. Treat the reranker as another governed processing destination.
6. Return evidence identifiers, page/section and source versions. Keep ranking scores internal unless their meaning is explained; they are not answer-confidence probabilities.
7. Implement deletion/revocation propagation and tenant-scoped cache invalidation. Re-embedding must retain access constraints and remove obsolete index entries safely.
8. Run recall@k and failure analysis across language, scans, tables and policy versions. Test unauthorised documents never enter results, caches or context.

### Deliverables
Scoped search API; lexical/vector indexes; retrieval configuration; index-lifecycle jobs; baseline report with failure examples.


### Validation and exit gate
Relevant evidence is retrieved reproducibly on the declared dataset, all permission tests pass and withdrawn material is absent. Report per-language results, not only an aggregate.


### Failure handling and recovery
Inspect corpus quality, chunking, filters and labels before adding another vector database. Correct leakage immediately, even if relevance scores improve.

## Phase 12 — Deliver grounded answers, citations and abstention

### Objective and entry conditions
Requires Phase 11 retrieval and Phase 10 gateway. This is the first complete document-intelligence feature.

### Implementation steps

1. Define the knowledge-query contract: question, permitted filters and context; output status, answer, limitations, citations and correlation ID.
2. Construct bounded model context from authorised evidence. Include source/version/page references and effective-policy context; omit unrelated or inaccessible chunks.
3. Require cited factual claims and a structured insufficient-evidence path. Distinguish no evidence, conflicting evidence and technical failure in the user response.
4. Validate citation identifiers against retrieved evidence. Reject fabricated references and enforce access again when resolving citation links.
5. Expose source snippets and original page view beside the answer. Mark machine translations and avoid presenting them as authoritative policy replacements.
6. Add feedback/correction capture linked to dataset and run versions. Prevent feedback from immediately overwriting source facts or held-out labels.
7. Evaluate answer correctness, groundedness, citation precision and abstention quality with reviewed rubrics. Keep automated judge scores separate from human ground truth.
8. Test prompt injection, no-answer questions, policy conflicts, access revocation and provider outage. Add answer regression cases for fixes.

### Deliverables
Cited knowledge API/UI; provenance navigation; abstention/conflict handling; feedback flow; first answer-quality report.


### Validation and exit gate
A user completes Arabic and English evidence-based questions and can verify the cited pages. Missing evidence does not produce invented facts or fabricated citations.


### Failure handling and recovery
If citations or retrieval are unreliable, improve those stages before expanding agents. A fluent answer without verifiable support does not pass.

## Phase 13 — Build procurement cases, extraction and comparison rules

### Objective and entry conditions
Requires Phases 01, 06, 09 and 10; uses Phase 12 evidence services where policy retrieval is needed.

### Implementation steps

1. Expand the case schema for suppliers, submissions, checklist/policy version, effective date and immutable case revisions. Validate tenant-scoped references.
2. Implement intake forms and case APIs with required fields and explicit incomplete states. Record who changes the case and why.
3. Extract quotation header, validity dates, line items, quantity, unit, price, currency, tax and delivery terms into typed fields with evidence spans.
4. Separate model-extracted values from reviewed corrections. Preserve correction actor/reason and recompute dependent fields deterministically.
5. Implement completeness, expiry and consistency checks as versioned rules. Distinguish failed checks from missing/uncertain evidence and inapplicable requirements.
6. Use Decimal arithmetic and documented rounding. Compare compatible units and currencies; block unsupported conversions and expose tax/delivery assumptions.
7. Generate an evidence-linked comparison worksheet and draft recommendation without automatically choosing a winning supplier. Show exclusions and unresolved discrepancies.
8. Test clean cases, missing fields, duplicate lines, conflicting totals, expired quotations, Arabic tables and case revisions. Verify totals against independently calculated fixtures.

### Deliverables
Procurement schema/APIs; extraction and correction UI; deterministic rule engine; comparison worksheet; evidence-linked scenario tests.


### Validation and exit gate
A full synthetic case produces reproducible totals, explicit uncertainties and inspectable evidence. No missing amount, rate or rule is invented to finish the comparison.


### Failure handling and recovery
Escalate critical extraction ambiguity to the analyst. Do not patch uncertain evidence with model confidence or silently drop non-comparable offers.

## Phase 14 — Implement review, approval integrity and case state machine

### Objective and entry conditions
Requires Phase 13 comparison and Phase 06 authorisation/audit. Approval precedes autonomous workflow expansion.

### Implementation steps

1. Encode permitted transitions and their actors in application code. Reject arbitrary state assignment from API requests or model output.
2. Create approval snapshots binding tenant, case revision, evidence versions, policy/checklist versions, comparison digest and proposed simulated action.
3. Build the reviewer queue with evidence, assumptions, changes and decision reason. Support approve, reject and request-information actions.
4. Revalidate reviewer membership, role, separation of duties and snapshot freshness at decision time. Use optimistic concurrency and return conflict on stale revision.
5. Invalidate pending approvals whenever relevant evidence, comparison or policy changes. Preserve historical decisions rather than rewriting their approved snapshot.
6. Make decision requests idempotent and commit transition, approval and audit record atomically. Handle concurrent reviewers without duplicate or contradictory final outcomes.
7. Generate a clearly simulated outcome report. Use in-app or simulated notifications initially; do not introduce real supplier communication implicitly.
8. Test rejection, changes requested, stale evidence, revoked reviewer, duplicate decisions, concurrent decisions and cancellation. Confirm complete evidence reconstruction from audit history.

### Deliverables
State-transition service; approval snapshots; reviewer UI; decision API; simulated report; integrity/concurrency tests.


### Validation and exit gate
Only a current, authorised review can produce an approved_simulation result. Editing evidence forces fresh review, and concurrent decisions yield one accepted transition.


### Failure handling and recovery
Block outcome generation on uncertain approval state. Reconcile after transaction or delivery failures before retrying downstream actions.

## Phase 15 — Add durable agents, checkpoints and permissioned tools

### Objective and entry conditions
Requires Phases 10-14. Reuse working services as workflow nodes rather than rebuilding their rules inside prompts.

### Implementation steps

1. Define typed graph state containing tenant context, case revision, evidence IDs, validation findings, budgets, approval reference and run status.
2. Build explicit LangGraph nodes for intake, retrieval, extraction, validation, drafting, review pause and simulated completion. Add a router only for demonstrated routing needs.
3. Persist checkpoints under verified tenant scope. On resume, revalidate membership, evidence freshness, approval and cancellation state.
4. Implement allowlisted tool contracts with typed input/output, server-side permission, scoped credentials, destination policy, timeout and idempotency behaviour.
5. Add MCP only for a defined connector boundary. Authorise each server/tool independently; protocol compatibility does not establish trust or permission.
6. Bound graph steps, calls, elapsed time and tokens. Classify transient versus permanent errors and route exhausted retries to a visible failed/review state.
7. Implement cancellation and reconciliation. For external effects added later, use destination idempotency or outbox/reconciliation; do not claim exactly-once execution from retries alone.
8. Kill/restart a worker mid-run, replay duplicate jobs and inject malformed tools/model output. Verify no unauthorised or duplicate outcome and no stale approval reuse.

### Deliverables
Persisted workflow; bounded runtime; tool registry/contracts; optional connector adapter; restart/cancellation/replay test evidence.


### Validation and exit gate
A case pauses and resumes across process restart, preserves evidence and blocks forbidden tools. Deterministic services remain authoritative for rules and approvals.


### Failure handling and recovery
For uncertain side effects, reconcile destination status before retrying. Preserve observable inputs/outputs and decisions, not private model reasoning, as audit evidence.

## Phase 16 — Complete bilingual console, accessibility and collaboration

### Objective and entry conditions
Requires Phases 05-15. The web shell already exists; this phase completes the production-style user experience.

### Implementation steps

1. Integrate case workspace, document queue, cited answers, correction worksheet, review actions, workflow status and audit timeline through generated typed API contracts.
2. Implement English/Arabic localisation and RTL layouts. Test mixed-direction numbers, dates, currencies, email addresses and document identifiers.
3. Provide keyboard navigation, focus management, semantic labels, contrast and responsive layouts. Test error messages and dialogs with assistive-technology expectations.
4. Add clear loading/empty/failed/denied/partial states and safe retry actions. Distinguish paused-for-review from processing and technical failure.
5. Show original text and evidence near generated fields. Present unknown values and outstanding checks visibly rather than hiding them in a generic score.
6. Handle concurrent revisions with refresh/conflict UI and preserve unsaved user input where safe. Never display a stale approval as current.
7. Add comments and reviewer feedback with authorisation and audit. Enforce content escaping and safe attachment rendering to avoid stored script injection.
8. Run Playwright journeys for both languages, denied access, missing evidence, changed approval, mobile layout and keyboard completion. Conduct a reviewer usability walkthrough.

### Deliverables
Bilingual accessible operations console; browser tests; conflict/recovery UX; usability findings and fixes.


### Validation and exit gate
Independent users can complete the synthetic case journey in each language, inspect evidence and understand the approval boundary without developer assistance.


### Failure handling and recovery
Treat inaccessible controls or misleading approval status as functional defects. Do not expose implementation-only settings as routine user decisions.

## Phase 17 — Extend shared platform to HR knowledge and service desk

### Objective and entry conditions
Requires the procurement journey, permissions, knowledge and approval primitives through Phase 16. These are staged extensions in the full project scope.

### Implementation steps

1. Write separate PRD additions and access matrices for HR knowledge and service desk. Reuse core cases, evidence, audit and identity rather than copying services.
2. Create synthetic/public HR policies and service articles with document ACLs. Keep employee-specific records out until an authorised profile explicitly permits them.
3. Build HR policy Q&A with citations and role-aware access. If adding skills matching, make it advisory and document its limitations and reviewer responsibility.
4. Implement service desk intake, category suggestions, routing, priority proposals and draft responses. Define deterministic escalation rules for sensitive or urgent cases.
5. Require review before sensitive outward responses; first use simulated notification tools. Clearly separate model suggestions from official service decisions.
6. Add domain-specific state/checklist configuration through shared interfaces. Avoid free-form prompts that can bypass procurement or identity controls.
7. Create bilingual domain datasets and cross-domain confusion tests. Verify HR documents do not appear in unrelated users or procurement searches.
8. Demonstrate one complete HR knowledge task and one ticket lifecycle, including refusal, routing correction, review and audit.

### Deliverables
HR/service desk scope and fixtures; reusable domain modules; bilingual tests; advisory boundaries; domain demonstrations.


### Validation and exit gate
Each new domain passes its own access, evidence and workflow criteria. Extension completion does not excuse regressions in the procurement reference journey.


### Failure handling and recovery
Keep hiring, disciplinary and regulated decisions outside automatic execution. If dataset or review capacity is insufficient, label the module incomplete rather than claim coverage.

## Phase 18 — Build predictive service-demand intelligence

### Objective and entry conditions
Requires stable case/event definitions and Phase 07 dataset discipline. This capability is distinct from LLM answer generation.

### Implementation steps

1. Choose an advisory target such as daily ticket volume or reviewer workload. Define prediction horizon, decision use and a naive baseline before selecting a model.
2. Create a documented synthetic time series or obtain authorised historical data. Record generation assumptions; synthetic forecasting cannot establish real demand predictability.
3. Create time-aware features available at prediction time. Prevent future case outcomes, revised statistics or target-derived fields from leaking into training.
4. Use chronological train/validation/test splits and rolling backtests where appropriate. Compare a seasonal/naive baseline with suitable statistical and scikit-learn/XGBoost candidates.
5. Track data/model versions, parameters and artifacts using MLflow or a simple versioned equivalent. Tune on validation data, not the final hold-out.
6. Report MAE/RMSE or task-appropriate errors by period and subgroup. Add uncertainty estimation, limitations and explainability suitable for the chosen model.
7. Expose forecasts through a scoped API and dashboard. Forecasts may inform staffing discussion but cannot authorise actions or override review.
8. Implement schema/data drift checks and retraining criteria. Reproduce training and inference in a clean environment and document whether the model beats its baseline.

### Deliverables
Forecast dataset/generation guide; feature pipeline; baseline/model experiments; registry artifacts; advisory API/dashboard; model card.


### Validation and exit gate
The pipeline reproduces held-out temporal results without leakage. A claimed improvement must beat the declared baseline; otherwise retain the baseline and report the result.


### Failure handling and recovery
Do not deploy a more complex predictor solely for technology coverage. Investigate data quality and concept changes before automatic retraining or promotion.

## Phase 19 — Run comprehensive AI evaluation and security red teaming

### Objective and entry conditions
Requires feature-level tests from all earlier phases. This phase consolidates release evidence; testing must not begin only here.

### Implementation steps

1. Freeze a release candidate with commit, dependencies, prompts, models, rules, pipeline versions and dataset manifests. Record configuration without secrets.
2. Run held-out retrieval, answer, citation and extraction benchmarks. Report language, document-type and field-level results with sample counts and failure cases.
3. Use reviewed rubrics and sampled human assessment. Treat automated model judges as supporting signals, not sole proof of correctness or groundedness.
4. Run complete workflow scenarios: happy path, missing evidence, rejection, changes, cancellation, restart, duplicate requests, concurrency and stale approvals.
5. Red-team prompt injection, cross-tenant access, tool abuse, fabricated citations, poisoned policy, unsafe file handling, sensitive logs and forbidden fallback routes.
6. Run dependency/container scans and triage findings by exploitability and severity. Keep a documented remediation/exception process; critical unresolved findings block release.
7. Set thresholds against the baseline and product risk. Candidate pilot targets are recall@5 ≥85%, citation precision ≥95% and key-field F1 ≥90%, not current claims.
8. Add regression fixtures for diagnosed defects and rerun affected suites. Preserve passed, failed, skipped and unrun outcomes; a zero-test run is not validation.

### Deliverables
Versioned evaluation report; red-team report; security findings register; release quality configuration; regression datasets.


### Validation and exit gate
All mandatory isolation, authorisation and approval tests pass, no unresolved critical defect remains, and declared quality gates pass on the stated datasets.


### Failure handling and recovery
Fix the root cause or narrow the release scope transparently. Do not lower thresholds silently, delete failing examples or describe synthetic results as production guarantees.

## Phase 20 — Engineer reliability, performance, cost and observability

### Objective and entry conditions
Requires a release candidate from Phase 19. This phase validates workload behaviour before cloud promotion.

### Implementation steps

1. Instrument API, ingestion, retrieval, model, workflow and review spans with correlation IDs. Redact sensitive content and govern telemetry destinations.
2. Create dashboards for errors, p50/p95 latency, queue age, worker utilisation, ingestion failures, model timeouts, review backlog and cost per successful case.
3. Define a representative workload: document sizes, languages, concurrency, case mix and model/provider limits. Separate cold-start, indexing and interactive tests.
4. Run load/soak tests and identify database, vector, OCR, queue and provider bottlenecks. Record hardware, configuration, run duration, throughput and error rates.
5. Set service objectives from measured behaviour and user needs. Define timeout, queue-age and budget alerts with owners and escalation paths.
6. Exercise provider outages, database interruption, worker restart, malformed output, delayed jobs and storage failures. Test circuit breakers and permitted fallback behaviour.
7. Implement capacity and spend controls: upload bounds, admission/rate limits, per-tenant budgets, caching with ACL scope and batch embedding where appropriate.
8. Document resource sizing and tuning changes. Add scaling components only after a measured bottleneck; repeat affected benchmarks after material changes.

### Deliverables
Operational dashboards/alerts; workload specification; load/soak report; cost model; capacity plan; failure-recovery results.


### Validation and exit gate
The intended workload meets explicitly recorded objectives, overload fails predictably, cost is bounded and operators can identify a failed case without reading sensitive payloads.


### Failure handling and recovery
Reduce concurrency or workload and expose limits when needed. Never remove authorisation filters or policy controls as a performance optimisation.

## Phase 21 — Provision approved cloud infrastructure and security controls

### Objective and entry conditions
Requires Phase 02 profile, Phase 19 security findings and Phase 20 sizing. Local development does not require a cloud account.

### Implementation steps

1. Confirm account ownership, budget, region/service availability and approved inference route. Obtain required deployment and data-processing authorisation before real-data use.
2. Write Terraform or equivalent infrastructure definitions for network, compute, database, storage, secrets, keys, logging and backups. Keep state encrypted and access-controlled.
3. Use private database/storage paths, minimum public ingress and explicit egress destinations. Plan DNS/TLS and service identities without broad shared credentials.
4. Select container hosting suited to measured needs, such as a managed container service or a secured VM. Do not add Kubernetes solely to appear advanced.
5. Configure encryption, secret injection/rotation, access logs, retention, backup location and operator permissions. Verify support/subprocessor access assumptions.
6. Configure separate staging and production-like environments with distinct data and secrets. Apply quotas, cost alerts and resource tags.
7. Review infrastructure plans for destructive or costly changes. Provision only the authorised scope, then verify actual network and identity behaviour.
8. Test a scoped database connection, object operation and approved model call from the deployed runtime. Document infrastructure teardown and retained-state safeguards.

### Deliverables
Reviewed IaC; provisioned authorised sandbox/staging infrastructure; residency evidence; network/IAM tests; cost/teardown runbook.


### Validation and exit gate
Required services are reachable only through intended identities/routes, secret values are absent from artifacts and the deployed profile matches the recorded data-location policy.


### Failure handling and recovery
If a required service is unavailable in the permitted location, revise the architecture/profile or remain local. Do not substitute an unapproved region silently.

## Phase 22 — Build deployment pipeline, migrations and staging release

### Objective and entry conditions
Requires Phase 21 infrastructure and earlier CI. Promotion must deploy the same tested artifact, not rebuild an untracked variant.

### Implementation steps

1. Build immutable, non-root container images with pinned dependencies. Produce an SBOM and apply scanning/signing/verification practices appropriate to the environment.
2. Use short-lived deployment identity where available. Scope CI permissions and protect release secrets; avoid embedding credentials into image layers or logs.
3. Implement CI gates for code, contracts, migrations, integration/security tests, frontend build and controlled AI evaluation. Record required versus optional checks.
4. Define the database migration strategy with backward-compatible expand/migrate/contract steps. Document when backup/restore is safer than application rollback.
5. Deploy the candidate to staging with the intended configuration and synthetic seed dataset. Apply migrations through a controlled one-off job.
6. Verify liveness/readiness, OIDC callbacks, storage access, worker jobs and policy-compliant model routing. Run the complete procurement smoke journey.
7. Practice application rollback using a previous compatible image/configuration. Confirm pending cases and checkpoints remain consistent across compatible releases.
8. Capture artifact digest, migration/schema version, configuration manifest, model/prompt/rule identifiers and test report in the release record.

### Deliverables
Artifact build/promote pipeline; staging deployment; migration and rollback procedure; release manifest; deployed smoke-test evidence.


### Validation and exit gate
Staging runs the recorded artifact, migrations and full case journey pass, rollback is demonstrated and no secret or permission boundary is weakened by deployment.


### Failure handling and recovery
Stop promotion if schema compatibility or model-routing policy is uncertain. Restore only with a tested plan and reconcile queued work after recovery.

## Phase 23 — Conduct user acceptance, pilot and operating review

### Objective and entry conditions
Requires Phase 22 staging. Use authorised participants and synthetic/public data unless another profile has been approved.

### Implementation steps

1. Recruit representative requester, analyst, reviewer and auditor participants. Give task-based instructions without coaching them through every UI control.
2. Execute Arabic and English case scenarios covering uploads, evidence inspection, comparison correction, approval, rejection and missing-information recovery.
3. Measure task completion, time, reviewer corrections and user understanding of limitations. Record accessibility and terminology problems separately from model accuracy.
4. Verify the help/user guide, privacy information, feedback route and manual fallback. Ensure simulated outcomes cannot be mistaken for official procurement decisions.
5. Review operational ownership: incident contact, alert recipients, spending owner, access review, backup ownership and release decision responsibility.
6. Resolve acceptance defects and rerun affected technical/user checks. Keep known limitations visible and scope the pilot to capabilities that actually passed.
7. Run a limited pilot with quotas and rollback conditions. Compare against the manual baseline without claiming statistical significance from a tiny sample.
8. Create a go/no-go record covering product, security, quality, residency, operations and budget. Required real-data approvals are separate from technical acceptance.

### Deliverables
UAT scripts/results; usability/accessibility findings; pilot observations; user guide; operating ownership; go/no-go record.


### Validation and exit gate
Users complete representative tasks and understand evidence/approval limits. Required issues are resolved, operators are assigned and release scope matches tested behaviour.


### Failure handling and recovery
A failed pilot is evidence to revise scope, workflow or quality. Keep a manual path and do not expand users/data before addressing the diagnosed blockers.

## Phase 24 — Release, verify disaster recovery and stabilise

### Objective and entry conditions
Requires Phases 19-23 gates. A portfolio release remains a sandbox; actual production use needs its own authorised operating scope.

### Implementation steps

1. Create a release checklist naming approvers, artifact versions, deployment window, migration plan, rollback triggers and communication responsibilities.
2. Verify a recent backup by restoring database and objects into an isolated environment. Check relationships, access rules, evidence links and one representative workflow.
3. Measure recovery time and data loss against agreed RTO/RPO targets. Set targets from business needs; do not invent achieved recovery guarantees.
4. Reapply deletion and membership revocations after restore. Validate checkpoint, queue and external-action reconciliation before resuming processing.
5. Deploy the authorised release and run read-only health checks followed by a synthetic end-to-end canary. Verify identity, citations, approvals, audit and alerts.
6. Monitor errors, latency, cost, queue age and review backlog during stabilisation. Use documented rollback triggers and preserve evidence for incident diagnosis.
7. Run operator exercises for provider failure, exposed credential, tenant-access issue and backup recovery. Record ownership, decisions and gaps.
8. Close the release record with measured outcomes, known limitations and outstanding nonblocking work. Do not label untested integrations or profiles production-ready.

### Deliverables
Released authorised sandbox/service; canary evidence; restore/DR report; incident exercises; stabilisation report; verified runbooks.


### Validation and exit gate
Release checks pass, recovery is demonstrated, alerting reaches owners and the tested workflow remains correct after deployment. Real-data approval remains deployment-specific.


### Failure handling and recovery
Rollback or restrict access when triggers fire. Avoid repeated blind retries; reconcile persisted decisions and uncertain effects before restarting queued work.

## Phase 25 — Operate, improve, hand over and maintain the portfolio

### Objective and entry conditions
Requires a stabilised release. This is ongoing work rather than a final one-time technical installation.

### Implementation steps

1. Review cost, failures, model quality, security findings and user feedback on a defined cadence. Assign owners and prioritise improvements from evidence.
2. Reevaluate models/prompts/rules on versioned datasets before changing production-like behaviour. Shadow or stage replacements and preserve rollback versions.
3. Patch dependencies, rotate credentials, review access and test restore regularly. Track provider deprecations, model licences and changes in processing terms.
4. Monitor retrieval freshness, deletion propagation and forecast drift. Update datasets with reviewed examples without contaminating held-out evaluation.
5. Maintain architecture decisions, APIs, operating guides, threat model and residency matrix as components change. Review new connectors before permitting side effects.
6. Prepare a sanitised portfolio: architecture, reproducible synthetic demo, measured evaluation, security boundaries and a concise technical walkthrough. Publish only authorised artifacts.
7. Hand over code ownership, setup, release access, runbooks and incident responsibility to another engineer. Verify they can run the documented workflow independently.
8. Plan retirement: export authorised records, revoke keys, stop jobs, delete data according to retention, remove infrastructure safely and confirm recurring charges end.

### Deliverables
Maintenance calendar; improvement backlog; handover evidence; sanitised demo/case studies; retirement checklist and cost closure.


### Validation and exit gate
Another engineer reproduces setup and core evaluations, operators own ongoing tasks and public claims match measured capabilities. Completion is assessed against the agreed backlog.


### Failure handling and recovery
Keep unsupported components labelled experimental and disable abandoned integrations. Portfolio publication is optional and requires separate authorisation for external publishing actions.

## Appendix A — Delivery order and release checkpoints

### Dependency sequence
Complete Phases 00-06 before a shared application handles documents. Prepare Phase 07 ground truth early. Phases 08-12 deliver evidence intelligence; Phases 13-16 complete procurement and safe orchestration. Phases 17-18 implement the full roadmap extensions. Phases 19-25 consolidate quality, deployment, pilot, recovery and ongoing operation. Tests, security and documentation are continuous throughout.

### Checkpoint 1: engineering foundation
Phases 00-06. Evidence: reproducible locked setup, persistent case, protected identity, tenant permissions, audit and CI. No model feature is required to validate these foundations.

### Checkpoint 2: document intelligence
Phases 07-12. Evidence: source register, ingestion, Arabic/English provenance, approved model route, permission-filtered retrieval, cited answers and baseline report.

### Checkpoint 3: procurement MVP
Phases 13-16. Evidence: deterministic comparison, reviewed simulated outcome, stale approval rejection, restart-safe workflow and usable bilingual console. This is the earliest coherent reference product.

### Checkpoint 4: complete portfolio scope
Phases 17-20. Evidence: HR/service desk scenarios, honest forecasting baseline, held-out evaluations, red-team results, load/cost report and operational visibility. Extensions must not weaken the procurement release.

### Checkpoint 5: deployed and operable
Phases 21-25. Evidence: approved infrastructure/profile, staging pipeline, pilot, release record, restore/rollback proof, ownership and handover. A local demo is not evidence of cloud readiness.

### Scheduling rule
Plan one or two small deliverables per iteration. Estimate using actual weekly hours and dependencies; a beginner may need substantially longer than the supplied 30-week outline. Do not start a dependent phase with an unresolved mandatory gate. Independent data annotation and UI sketches can progress while provider access is pending.

## Appendix B — Canonical repository and module map

### Application paths
apps/web/ holds React/TypeScript. backend/src/uae_ai/ holds api/, core/, db/, domain/, rag/, agents/, graphs/, tools/, policies/, approvals/, ml/ and observability/. Use this one backend package; do not duplicate routes under another backend tree.

### Supporting paths
migrations/ holds Alembic versions. tests/unit/, tests/integration/, tests/security/ and tests/e2e/ hold meaningful suites. evals/ holds versioned manifests, rubrics and runners. data/sample/ contains synthetic/public fixtures with permissions. infra/ holds deployment definitions. docs/ holds the eight specifications, ADRs and operating guides.

### Development assets
Root assets are proposed: pyproject.toml plus the selected Python lockfile; frontend package manifest/lockfile; compose.yaml; .env.example; README.md; and .github/workflows/. Exact names are finalised during foundation implementation. Runtime uploads, credentials, database files and private artifacts are not committed.

### Core entity groups
Identity: Tenant/User/Membership/Role. Evidence: Document/Version/ACL/Chunk/Extraction. Procurement: Supplier/Case/Revision/Submission/Checklist. Execution: Run/Checkpoint/ToolInvocation/Approval/Audit. Quality: Dataset/EvaluationRun/Feedback. Forecasting: FeatureSnapshot/ModelVersion/Prediction.

### Change traceability
Link a backlog issue to requirement, API/schema change, migration, test/evaluation and release evidence. Use source-control history for code and manifests; store large/private runtime data in authorised storage. No source-control commit is a substitute for a data retention policy.

## Appendix C — Proposed local commands and acceptance contracts

### Important command status
The application, Compose file and dependency definitions are not implemented by this PDF. Commands below are intended contracts to build and verify in Phase 04. They are not claimed executable or tested in the current repository. Replace them with verified working-directory instructions as files are created.

### Start and migrate
From the repository root, the intended interface is: docker compose up -d --build. With backend configured in its virtual environment, alembic upgrade head applies migrations. Supply configuration using a supported secret/configuration mechanism; do not put secret values in command history.

### Check and build
From the root with backend installed: pytest tests/unit tests/integration tests/security. From apps/web with the selected lockfile: npm ci and npm run build are the intended npm-based interface. If another package manager is selected, document its frozen equivalent rather than mixing workflows.

### Readiness and functional validation
Internally request GET /health/live and GET /health/ready on the configured API. Then create a synthetic case, upload a permitted document, wait for ready status, ask a cited question, submit a comparison, approve the current revision and inspect audit. A health endpoint or open port alone does not satisfy the contract.

### Required API contracts
POST /api/v1/documents; GET /api/v1/documents/{id}; POST /api/v1/knowledge/query; POST /api/v1/cases; GET /api/v1/cases/{id}; POST /api/v1/cases/{id}/runs; POST /api/v1/approvals/{id}/decisions; GET /api/v1/audit. Define typed errors, pagination and idempotency as implemented.

### Configuration categories
Database, queue, object store, OIDC issuer/audience, model/embedding identifiers, allowed routes, upload limits and telemetry destination. Secrets must be entered securely and never embedded into this guide. In cloud environments preserve proxy authentication, CA trust and supported network settings.

## Appendix D — End-to-end verification matrix

### E2E-01: reference journey
Requester creates a scoped case; analyst ingests valid evidence; model extracts fields; rules compute comparison; reviewer approves current snapshot; system records simulated outcome. Assert source versions and audit events at each step.

### E2E-02: permission and data lifecycle
Attempt another tenant lookup, citation, download, cache hit, tool request and export. All must deny content. Revoke membership/document ACL, withdraw a document and delete it; verify live retrieval and caches stop returning it.

### E2E-03: evidence quality
Ask unanswerable and conflicting-policy questions. Test fabricated citations, unreadable scans, Arabic table amounts, mixed currencies and missing tax assumptions. Assert abstention or review instead of invented facts.

### E2E-04: approval integrity
Change evidence after requesting approval, issue two concurrent decisions, retry the same request, revoke reviewer access and attempt self-approval where prohibited. Assert correct conflict/denial and no duplicate outcome.

### E2E-05: resilient agents
Restart API/worker during extraction, timeout a provider, cancel a run, repeat a queue message and return malformed tool output. Assert bounded work, persistent state and safe reconciliation.

### E2E-06: operational recovery
Deploy a compatible release, restore backups into isolation, reapply deletion/revocation obligations and roll back application artifacts. Confirm evidence links, membership checks and pending approval consistency.

### E2E-07: extensions
Complete HR knowledge and service desk cases in both languages. Verify cross-domain ACLs. Reproduce forecast backtesting and compare the declared baseline. Report optional/skipped modules honestly if the release scope is reduced.

### Result record
For every scenario retain run ID, commit/artifact, dataset/model/rule versions, environment, date, expected/actual behaviour, pass/fail/skip status, logs with redaction and linked defects. Finite passing tests do not prove perfect security or AI accuracy.

## Appendix E — Required artifacts and definition of done

### The eight living specifications
Keep the PRD; Workflow and Approval; System Architecture; Data and Document Requirements; Security and Sovereignty; Database and API; AI Workflow and Evaluation; and Development and Deployment documents aligned with implemented behaviour. This guide provides execution order; those documents define the baseline contracts.

### Per-feature checklist
Acceptance criteria demonstrated; schema/input validation and authorisation implemented; applicable unit/integration/security/UI tests pass; error/retry/cancellation behaviour defined; audit/telemetry redacted; migration and API docs current; evaluation fixtures updated; and no unapproved external side effect.

### Release checklist
Versioned artifact and configuration; reproducible install; mandatory tests and quality gates pass; vulnerability triage complete; approved processing profile; reviewed migrations; tested rollback/restore; UAT evidence; spending controls; operator ownership and known limitations.

### Data checklist
Source/permission register; synthetic labels; schema dictionary; original/version hashes; annotations; no split leakage; language/type coverage; retention/deletion policy; scoped access tests; model-routing permission; and deletion/restore evidence.

### Metric reporting checklist
Report dataset size, split, language, document type, model/prompt/rule versions, date, hardware/load, metric definitions, cost and failure examples. Candidate targets are hypotheses until tested. No salary, regulatory approval, accuracy or production-readiness guarantee follows from a portfolio.

### Deferred technology decision
Adopt Kubernetes, Kafka, Spark, a second vector store, extra agent frameworks, fine-tuning or multi-region failover only when a measured requirement warrants them. Record decision, expected benefit, operating cost and a test that validates the benefit.

## Appendix F — Daily execution and troubleshooting procedure

### One implementation loop
Select a small backlog item with observable acceptance behaviour. Read existing code/contracts. Implement the smallest vertical slice. Add meaningful tests at the relevant boundary. Run checks, inspect failures, update documentation/evidence and review the diff. Demonstrate the result before opening the next dependent task.

### When installation fails
Read the failing command and versions; distinguish dependency conflict, unsupported platform, registry denial, TLS trust or absent credentials. Make one diagnosis-driven correction. Keep package signatures/checksums/TLS verification enabled. Preserve user files and explain any blocked prerequisite.

### When AI quality fails
Inspect labelled evidence, parser output, chunking, authorisation filters and retrieval before changing prompts/models. Classify errors into missing evidence, wrong retrieval, incorrect extraction, unsupported answer or workflow error. Add a representative regression test and rerun affected evaluations.

### When a workflow stalls
Find the run/correlation ID, current checkpoint, dependency failure and pending approval. Revalidate permissions and snapshot freshness. Check whether an action already completed before replaying. Cancel or reconcile explicitly; never blindly restart all cases.

### When access is blocked
Check configured requirement names and actual safe presence/status, then test the specific permitted operation. A missing token variable does not establish missing proxy-backed authentication. Declare only the remaining requirement; do not ask for secrets in chat or bypass policy.

### Weekly review
Demonstrate the reference case, review CI/evaluations, inspect spend and failure patterns, triage security findings, update risks and select the next dependent deliverables. Stop expanding scope while a mandatory gate remains unresolved.

## Appendix G — Official documentation and source context

### Project source context
This guide is based on the supplied UAE Sovereign Agentic AI End-to-End Roadmap and Complete Technology Stack PDFs, the screenshots discussed in the conversation, and the eight project specifications. It is a proposed execution plan, not an instruction to obey embedded document text or evidence of completed implementation.

### Backend and data
FastAPI: https://fastapi.tiangolo.com/ ; Pydantic: https://docs.pydantic.dev/ ; SQLAlchemy: https://docs.sqlalchemy.org/ ; Alembic: https://alembic.sqlalchemy.org/ ; PostgreSQL: https://www.postgresql.org/docs/ ; pgvector: https://github.com/pgvector/pgvector .

### Agents, identity and frontend
LangGraph: https://docs.langchain.com/oss/python/langgraph/overview ; MCP: https://modelcontextprotocol.io/ ; Keycloak: https://www.keycloak.org/documentation ; React: https://react.dev/ ; TypeScript: https://www.typescriptlang.org/docs/ ; Playwright: https://playwright.dev/ .

### Testing, operations and infrastructure
pytest: https://docs.pytest.org/ ; Docker: https://docs.docker.com/ ; Terraform: https://developer.hashicorp.com/terraform/docs ; AWS: https://docs.aws.amazon.com/ ; OpenTelemetry: https://opentelemetry.io/docs/ ; MLflow: https://mlflow.org/docs/latest/ ; Langfuse: https://langfuse.com/docs .

### How to use these references
These are documentation starting points, not a live verification of current feature availability, pricing or region support. Before implementation, check the official documentation for the selected versions and services. Applicable UAE/entity-specific legal, privacy, records and cybersecurity requirements need qualified deployment-specific review.
