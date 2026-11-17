-- Synthetic intake prototype. Apply only to a dedicated test database.

CREATE TABLE nawa_intake_documents (
    id uuid PRIMARY KEY,
    tenant_id text NOT NULL REFERENCES nawa_tenants(id) ON DELETE RESTRICT,
    filename text NOT NULL CHECK (length(filename) BETWEEN 1 AND 100),
    sha256 char(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    size_bytes bigint NOT NULL CHECK (size_bytes BETWEEN 1 AND 4194304),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, sha256),
    UNIQUE (tenant_id, id)
);

CREATE TABLE nawa_intake_jobs (
    id uuid PRIMARY KEY,
    tenant_id text NOT NULL,
    document_id uuid NOT NULL,
    state text NOT NULL CHECK (state IN ('received', 'validated', 'processing', 'retry-pending', 'completed', 'failed')),
    attempts integer NOT NULL DEFAULT 0 CHECK (attempts BETWEEN 0 AND 3),
    claim_token_hash char(64) CHECK (claim_token_hash ~ '^[0-9a-f]{64}$'),
    lease_until timestamptz,
    result jsonb CHECK (result IS NULL OR jsonb_typeof(result) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, document_id) REFERENCES nawa_intake_documents(tenant_id, id) ON DELETE RESTRICT,
    UNIQUE (tenant_id, document_id),
    CHECK ((state = 'processing' AND claim_token_hash IS NOT NULL AND lease_until IS NOT NULL)
        OR (state <> 'processing' AND claim_token_hash IS NULL AND lease_until IS NULL)),
    CHECK ((state = 'completed' AND result IS NOT NULL) OR (state <> 'completed' AND result IS NULL))
);

CREATE INDEX nawa_intake_jobs_ready ON nawa_intake_jobs (tenant_id, state, created_at);

-- A document may belong to one synthetic version family per tenant. Each
-- revision references an existing immutable-by-convention source record.
CREATE TABLE nawa_intake_versions (
    tenant_id text NOT NULL,
    family_id uuid NOT NULL,
    version integer NOT NULL CHECK (version > 0),
    document_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, family_id, version),
    UNIQUE (tenant_id, document_id),
    FOREIGN KEY (tenant_id, document_id) REFERENCES nawa_intake_documents(tenant_id, id) ON DELETE RESTRICT
);

-- A completed intake source can be promoted to one tenant-owned quotation.
CREATE UNIQUE INDEX nawa_quotation_tenants_pair ON nawa_quotation_tenants (tenant_id, quotation_id);
CREATE TABLE nawa_intake_promotions (
    tenant_id text NOT NULL,
    document_id uuid NOT NULL,
    quotation_id text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, document_id),
    UNIQUE (tenant_id, quotation_id),
    FOREIGN KEY (tenant_id, document_id) REFERENCES nawa_intake_documents(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, quotation_id) REFERENCES nawa_quotation_tenants(tenant_id, quotation_id) ON DELETE RESTRICT
);

-- Synthetic operator actions; privileged database users can alter them.
CREATE TABLE nawa_intake_admin_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id text NOT NULL,
    document_id uuid NOT NULL,
    action text NOT NULL CHECK (action IN ('revalidate', 'retry')),
    actor_hash char(64) NOT NULL CHECK (actor_hash ~ '^[0-9a-f]{64}$'),
    reason text NOT NULL CHECK (length(reason) BETWEEN 1 AND 500),
    created_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, document_id) REFERENCES nawa_intake_documents(tenant_id, id) ON DELETE RESTRICT
);

-- Proposed worker claim: use a short transaction and SELECT ... FOR UPDATE
-- SKIP LOCKED, generate a fresh random token and store only its hash, then
-- atomically set processing, increment attempts, and set a lease. Completion
-- must check tenant, token hash, lease and state while holding the row lock.
-- Source-file storage and SQL cannot commit atomically: crashed submissions
-- require explicit reconciliation. No access control is implied by tenant_id;
-- verified, active membership must be enforced by the application on every call.

