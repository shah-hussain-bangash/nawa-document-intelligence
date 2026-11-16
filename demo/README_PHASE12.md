# Phase 12: local synthetic identity prototype

This is a local, synthetic-data-only identity prototype. It is not a production authentication service or a security certification. The default Phase 11 demo remains unauthenticated and must stay on localhost. Phase 12's OIDC mode must be explicitly selected; it requires PostgreSQL, an approved local issuer, an exact loopback browser origin and provisioned memberships. It does not fall back to demo mode on identity failures.

## Implemented prototype

- Authorization-code sign-in with PKCE, one-use state and nonce, signed ID-token verification, strict issuer/audience checks and verified HTTPS to the identity provider.
- Opaque server-side sessions and session-bound CSRF tokens; membership and role are rechecked server-side. Sessions last at most five minutes and cannot outlive the ID token used to create them. Sessions and pending login attempts are **in process memory**: restarting the application invalidates them, and multi-worker use is unsupported.
- Server-scoped viewer, analyst and reviewer actions. Quotation ownership is associated with a tenant; existing Phase 11 records have no tenant assignment. A database containing unassigned quotations cannot be switched into authenticated mode automatically. Use a separate database or a reviewed, explicit migration.
- A database-mode startup guard prevents this application version from accidentally switching a database between demo and OIDC modes. Older application versions and privileged database clients do not enforce this guard: use separate databases and credentials, and do not treat it as database row-level security.
- Actor IDs in review events are derived from the authenticated identity, not the submitted payload. The hash-linked ledger is not tamper-proof and is not an independently protected audit store.
- An isolated Keycloak QA stack uses generated synthetic accounts, its own database, a test CA trusted only by the test process and ports bound to host loopback. The fixture file contains **synthetic passwords**; it is excluded from the image and Git, must not be shared, and the setup must never use real accounts or production credentials.

## Verification and limits

Local synthetic Keycloak testing covered certificate validation, authorization-code/PKCE login, provisioned membership, CSRF rejection, role restrictions, server-selected review actor, membership revocation and local logout. Unit tests cover nonce, issuer, audience, signature, callback replay, malformed provider responses, sessions and API boundary restrictions. PostgreSQL tests exercise tenant filtering, transactional review changes, legacy membership and role checks. These checks are not an independent penetration test, an enterprise identity rollout, MFA validation or certification.

The application itself uses HTTP and non-Secure cookies only in the explicit loopback test configuration; do not expose this mode beyond the local computer. The test certificate is not installed into the host/browser trust store. Local logout revokes the app session, not necessarily the identity-provider session. Membership deactivation is checked on requests, but identity-provider user revocation is not immediately propagated unless membership is also updated or the short session expires. Token refresh, robust identity-provider outage recovery, multi-tenant selection, durable sessions and full operational controls remain open.

The local QA database and its synthetic fixture are separate from the original `nawa-postgres` container, the Phase 11 QA database and the v0.6.6 application. The QA fixture mount exposes synthetic test passwords to the QA application container so the automated check can sign in; this arrangement must never be used for actual users. Do not publish `.data/phase12-identity`, password files, certificates' private keys, session cookies or database volumes.

## Acceptance still required

Before marking Phase 12 complete, verify all changed tests in CI, conduct a targeted security review, document the membership provisioning and revocation operating process, validate the actual browser journey in a trusted local environment, and disclose unresolved production requirements. No claim of production readiness follows from the synthetic tests.
