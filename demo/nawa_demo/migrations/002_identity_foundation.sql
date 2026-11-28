-- Phase 12 foundation. No tenant membership or legacy quotation ownership is
-- inferred or provisioned by this migration.
CREATE TABLE nawa_tenants (
    id text PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 128),
    active boolean NOT NULL DEFAULT true
);

CREATE TABLE nawa_identities (
    issuer text NOT NULL CHECK (length(issuer) BETWEEN 1 AND 2048),
    subject text NOT NULL CHECK (length(subject) BETWEEN 1 AND 512),
    active boolean NOT NULL DEFAULT true,
    PRIMARY KEY (issuer, subject)
);

CREATE TABLE nawa_memberships (
    issuer text NOT NULL,
    subject text NOT NULL,
    tenant_id text NOT NULL REFERENCES nawa_tenants(id) ON DELETE RESTRICT,
    role text NOT NULL CHECK (role IN ('viewer', 'analyst', 'reviewer')),
    active boolean NOT NULL DEFAULT true,
    PRIMARY KEY (issuer, subject, tenant_id),
    FOREIGN KEY (issuer, subject) REFERENCES nawa_identities(issuer, subject) ON DELETE RESTRICT
);

CREATE TABLE nawa_quotation_tenants (
    quotation_id text PRIMARY KEY REFERENCES nawa_quotations(id) ON DELETE RESTRICT,
    tenant_id text NOT NULL REFERENCES nawa_tenants(id) ON DELETE RESTRICT
);

-- Opaque token verifiers only; authentication cookies and CSRF values are not
-- stored in plaintext. Rows are not usable until server integration is complete.
CREATE TABLE nawa_auth_sessions (
    token_hash text PRIMARY KEY CHECK (token_hash ~ '^[0-9a-f]{64}$'),
    csrf_hash text NOT NULL CHECK (csrf_hash ~ '^[0-9a-f]{64}$'),
    issuer text NOT NULL,
    subject text NOT NULL,
    tenant_id text NOT NULL,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    FOREIGN KEY (issuer, subject, tenant_id)
        REFERENCES nawa_memberships(issuer, subject, tenant_id) ON DELETE RESTRICT
);
