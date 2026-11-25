# Workflow and Approval Specification

Procurement lifecycle, roles and exception handling

Version 1.0 | 6 November 2026 | Proposed development baseline

## 1. Workflow contract

The first workflow is procurement intake → document ingestion → evidence retrieval → extraction → deterministic checks → comparison draft → human review → simulated outcome. Every step receives a tenant-scoped case and records an auditable result.
The LLM may extract, summarise and recommend. Application code controls permissions, arithmetic, state transitions and approvals. No retrieved text or model output can authorise a tool or change a review decision.

## 2. Required inputs and outputs

Inputs: requester, tenant, case purpose, checklist version, applicable policy date, supplier submissions and evaluation criteria. Each quotation records its currency and validity date when available. Missing required inputs cause a request for information, not invented defaults.
Outputs: source-linked fields, missing/expired-item checklist, comparable totals, exclusions, cited draft, review decision and a simulated recommendation report. Record source versions and the rule/model/prompt versions used.

## 3. State model

States: draft, submitted, processing, needs_information, awaiting_review, approved_simulation, rejected, cancelled and failed. Draft → submitted requires valid intake. Submitted → processing starts a run. Processing → awaiting_review requires a valid comparison; incomplete evidence goes to needs_information.
Only an authorised reviewer moves awaiting_review to approved_simulation or rejected. A request for changes moves it to needs_information. Corrected submissions create a new case revision and return to processing. Terminal records remain historical; reopening creates a linked revision rather than rewriting the previous decision.

## 4. Approval integrity

Bind each approval request to tenant, case ID and revision, evidence-version set, checklist/policy versions, comparison digest and proposed action. Show this information and cited evidence to the reviewer. Require a decision, reason and verified actor identity.
Accept a decision only when the reviewer still has permission and the expected revision matches. Enforce separation of duties when configured. Updating evidence or rules invalidates the pending approval; the API returns a conflict for a stale decision. Never carry an approval silently onto a regenerated recommendation.

## 5. Role and action rules

Requester creates and submits cases. Analyst attaches permitted documents, corrects extracted fields and submits a draft for review. Reviewer approves, rejects or requests information. Tenant administrator controls membership and approved configuration. Auditor reads permitted evidence and history.
Every API route and worker/tool entry point performs server-side authorisation. A caller-supplied tenant identifier is a requested scope, not proof of membership. Check object access on downloads and citation resolution as well as on search.

## 6. Calculations and evidence rules

Use decimal quantities, explicit rounding rules and currency codes. Separate net price, tax, delivery charges and total. Compare like-for-like units and identify excluded line items. Do not mix currencies unless an authorised rate source and effective date are supplied.
Distinguish failed checks from missing evidence and extraction uncertainty. A compliance-looking summary is advisory; versioned deterministic rules and a reviewer determine the sandbox outcome.

## 7. Recovery, retries and cancellation

Checkpoint before and after durable steps. Use idempotency keys for run creation and decision requests. Retry only transient failures with bounded backoff; malformed output gets bounded correction attempts, then an explicit failure or reviewer task.
On restart, reload the checkpoint, revalidate access and evidence, then continue. Reconcile any uncertain tool outcome before retrying. Cancellation is cooperative: stop future steps, record completed work and do not claim already completed effects were undone.

## 8. Audit events and notifications

Record case creation, submission, upload/version change, extraction correction, rule execution, draft generation, review request, decision, retry, cancellation and outcome. Include actor or service identity, tenant, resource, old/new revision, timestamp, outcome and correlation ID.
Keep raw sensitive contents out of operational logs. Notifications in the first release are in-app or simulated. A real email/ERP connector requires a separate permissioned action contract and delivery reconciliation.

## 9. Acceptance scenarios

WF-01: complete valid case reaches a reviewed simulated outcome. WF-02: missing supplier evidence triggers needs_information. WF-03: reviewer rejection is preserved. WF-04: changed quotation invalidates approval. WF-05: two concurrent reviewer decisions produce one accepted transition and one conflict.
WF-06: duplicate request creates no duplicate run/outcome. WF-07: cross-tenant access fails. WF-08: worker restart resumes safely. WF-09: malicious document instructions cannot invoke tools. WF-10: expired reviewer membership blocks resume. Retain test evidence for each scenario.
