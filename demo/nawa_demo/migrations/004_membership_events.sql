-- Local synthetic audit records. Operators remain self-asserted and database
-- owners can alter these records; this is not a protected production audit log.
CREATE TABLE nawa_membership_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    issuer text NOT NULL,
    subject text NOT NULL,
    tenant_id text NOT NULL,
    action text NOT NULL CHECK (action IN ('grant', 'revoke')),
    role text NOT NULL CHECK (role IN ('viewer', 'analyst', 'reviewer')),
    operator_name text NOT NULL CHECK (length(operator_name) BETWEEN 1 AND 200),
    reason text NOT NULL CHECK (length(reason) BETWEEN 1 AND 500),
    created_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (issuer, subject, tenant_id)
        REFERENCES nawa_memberships(issuer, subject, tenant_id) ON DELETE RESTRICT
);
