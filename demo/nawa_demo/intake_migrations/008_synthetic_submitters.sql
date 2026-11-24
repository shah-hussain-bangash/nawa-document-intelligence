-- Disposable synthetic QA only. Existing documents receive no inferred submitter.
CREATE TABLE nawa_synthetic_intake_submitters (
    tenant_id text NOT NULL,
    document_id uuid NOT NULL,
    actor_hash char(64) NOT NULL CHECK (actor_hash ~ '^[0-9a-f]{64}$'),
    recorded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, document_id, actor_hash),
    FOREIGN KEY (tenant_id, document_id)
        REFERENCES nawa_intake_documents(tenant_id, id) ON DELETE RESTRICT
);
