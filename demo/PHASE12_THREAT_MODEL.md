# Phase 12 threat model: synthetic localhost prototype

Status: engineering review, not an independent security assessment. Applies only to the opt-in local OIDC prototype in this branch. The unauthenticated demo mode remains unsuitable for sensitive data.

## Assets and trust boundaries

- Assets: quotation fields and evidence, review events, tenant membership, session verifiers, CSRF tokens and local test identity material.
- Boundaries: browser to local application; application to a configured HTTPS identity issuer; application to PostgreSQL; and an operator to the synthetic fixture and backup files.
- The prototype assumes a trusted single-user workstation, trusted issuer configuration, and operator-controlled database and fixture files. It does not assume browser headers, request bodies or document content are trustworthy.

## Threats and controls

| Threat | Implemented prototype control | Verification or residual risk |
| --- | --- | --- |
| Forged identity or authorization response | Signed ID-token validation, pinned issuer and audience, PKCE, one-use state and nonce, trusted HTTPS issuer origin. | Synthetic signed-token and local Keycloak tests passed. No independent protocol assessment; availability and key rotation need broader testing. |
| Cross-site requests and stolen or replayed session | Opaque random session identifiers, hashed server-side verifiers, expiration, logout, origin checks and session-bound CSRF on writes. | Session and HTTP boundary tests passed. Local application HTTP and non-Secure cookies are acceptable only for this isolated synthetic test; real deployment requires HTTPS and secure cookie configuration. |
| Forged role, tenant or reviewer identity | Server membership lookup; server derives tenant and review actor; role and membership rechecked during database operations. | Synthetic tests cover forged headers, unauthorized role actions and local membership deactivation. There is no organizational provisioning or MFA. |
| Cross-tenant object access or ownership changes | SQL scopes quotation operations by tenant; membership and ownership rows are locked for protected operations. | Isolated PostgreSQL tests cover other-tenant access. No database RLS or defense against privileged DB clients; independent isolation review remains necessary. |
| Accidental demo/authenticated database sharing | Database-mode startup guard and explicit refusal to auto-assign unowned legacy records. | Tested for this application version. Older application versions and privileged DB clients may bypass this guard. Separate databases and credentials are mandatory. |
| Malicious upload and document content | Existing bounded synthetic TXT/PDF parser and safe text rendering remain. | This is not a hardened file-processing sandbox; arbitrary hostile files and real documents are out of scope. |
| Identity-provider compromise or account disable | Trusted issuer restriction, local membership recheck, and sessions capped at five minutes and at the ID-token expiry. | The application does not immediately synchronize provider-side account disablement. An operator must deactivate local membership; provider logout does not necessarily follow app logout. |
| Credential leakage through fixtures or logs | Fixture data excluded from Git and Docker build context; no tokens or passwords printed by test scripts. | The QA application container can read synthetic test credentials for automation. Do not reuse the fixture for real accounts; local files and backups require OS access controls. |
| Tampered review history | Hash-linked event replay and revision checks. | A DB administrator can rewrite history and hashes. This is not an immutable or independently protected audit log. |
| Availability and recovery | Fail-closed identity checks, short connection timeouts, bounded login-attempt and session stores. | State is process-local and lost at restart; multi-worker operation, provider outages, throttling and distributed recovery are not validated. |

## Release decisions still open

Real browser sign-in with an appropriately trusted local certificate has not been verified. Do not bypass browser certificate warnings. MFA, identity-provider revocation synchronization, provisioning and offboarding, durable sessions, database isolation, privacy/retention, independent security review, and operational ownership remain separate work. Phase 18 is the planned broader hardening and security assessment; this prototype does not establish regulatory compliance or production readiness.
