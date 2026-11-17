-- Add validated state and synthetic requeue events without modifying source data.
ALTER TABLE nawa_intake_jobs DROP CONSTRAINT nawa_intake_jobs_state_check;
ALTER TABLE nawa_intake_jobs ADD CONSTRAINT nawa_intake_jobs_state_check
    CHECK (state IN ('received', 'validated', 'processing', 'retry-pending', 'completed', 'failed'));

-- Privileged database users can alter these synthetic events.
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
