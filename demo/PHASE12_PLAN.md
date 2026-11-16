# Phase 12: identity and server-side authorization

Status: design in progress; no authentication or authorization has been added yet.

## Scope and compatibility

Develop in an isolated copy of the synthetic Document Intelligence demo. Preserve the Phase 11 single-user mode for local demonstrations and make authenticated mode explicit and fail-closed. An unauthenticated mode is not secure and must remain localhost-only, synthetic-only, and clearly labeled. Do not copy credentials, databases, uploads or .env files from the separate v0.6.6 project.

## Existing evidence and candidate architecture

The separate v0.6.6 project has a local Keycloak/OIDC implementation with PKCE, state and nonce checks, issuer/audience validation, server-side sessions and user membership checks. Its reported local identity tests are useful design evidence, not proof this application is secure. Evaluate its dependencies and implementation before reuse; do not run both applications against the same database or identity fixture.

Use an established, maintained OIDC client and a local, isolated Keycloak test realm if compatible with the dashboard architecture. Use authorization code flow with PKCE, strict issuer and audience validation, bounded one-use state/nonce, TLS validation, server-managed opaque sessions, secure cookies appropriate to the deployment, session expiration and logout/revocation handling. Do not log tokens, credentials, document text or secrets. Browser state-changing requests need CSRF protection in addition to Origin checks. No default password or unauthenticated fallback in authenticated mode.

## Access model

Use stable issuer-and-subject identity, explicit membership and server-assigned tenant/role mappings. Start with separate viewer, analyst and reviewer capabilities. Verify the exact permission matrix before implementation. Do not accept actor, tenant, role, or permissions supplied by clients as authoritative. Derive review actor from the authenticated session. Restrict all list, quotation, compare, review and future evidence endpoints by tenant and role, including direct object IDs. Apply tenant constraints in database access, not only in the browser. Do not call a simulated hash ledger tamper-proof.

Existing Phase 11 records have no tenant identity. Do not automatically attach them to a tenant. Provide a documented, explicit development-data migration or use a fresh isolated database for Phase 12 testing. No changes to existing volumes without a backup and a reviewed migration.

## Test and acceptance gates

- Anonymous requests are denied in authenticated mode; memory demo mode is explicitly separate.
- Invalid issuer, audience, nonce, state, expired token, replayed callback, revoked user and expired session fail closed.
- Forged actor or role values cannot override server identity; direct object IDs and comparisons cannot cross tenant boundaries.
- Viewer write, analyst approval and reviewer escalation are denied according to the approved matrix; each allowed action is covered.
- CSRF and cross-origin requests fail; logout and revocation prevent subsequent writes.
- Concurrency, migrations, readiness, storage failure and Phase 11 regressions remain covered.
- Execute a real local identity-provider flow and record CI, versioned configuration and synthetic end-to-end evidence. Document threat model, risks, limitations and recovery before calling the phase complete.

## Out of scope for this gate

Production identity onboarding, MFA policy, independent security assessment, public deployment and regulatory certification require separate organizational approval and evidence.
