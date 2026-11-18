-- Disposable Phase 14 CI databases only. This is not a production migration.
CREATE TABLE nawa_phase14_qa_lifecycle (
    tenant_id text NOT NULL,
    document_id uuid NOT NULL,
    state text NOT NULL CHECK (state IN ('active', 'withdrawn', 'deleted')),
    PRIMARY KEY (tenant_id, document_id),
    FOREIGN KEY (tenant_id, document_id)
        REFERENCES nawa_intake_documents (tenant_id, id) ON DELETE RESTRICT
);

