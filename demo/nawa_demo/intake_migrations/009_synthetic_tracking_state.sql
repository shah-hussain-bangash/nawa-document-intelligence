-- Disposable synthetic QA only. Never infer complete history for existing sources.
CREATE TABLE nawa_synthetic_intake_tracking (
    tenant_id text NOT NULL,
    document_id uuid NOT NULL,
    complete boolean NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, document_id),
    FOREIGN KEY (tenant_id, document_id)
        REFERENCES nawa_intake_documents(tenant_id, id) ON DELETE RESTRICT
);
