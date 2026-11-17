-- Run only in a newly initialized synthetic test database.
INSERT INTO nawa_tenants(id) VALUES ('tenant-a'), ('tenant-b');
INSERT INTO nawa_intake_documents(id, tenant_id, filename, sha256, size_bytes)
VALUES ('00000000-0000-0000-0000-000000000001', 'tenant-a', 'sample.txt', repeat('a',64), 12);
DO $$ BEGIN
  BEGIN
    INSERT INTO nawa_intake_documents(id, tenant_id, filename, sha256, size_bytes)
    VALUES ('00000000-0000-0000-0000-000000000002', 'tenant-a', 'duplicate.txt', repeat('a',64), 12);
    RAISE EXCEPTION 'duplicate document unexpectedly accepted';
  EXCEPTION WHEN unique_violation THEN NULL; END;
  BEGIN
    INSERT INTO nawa_intake_jobs(id, tenant_id, document_id, state)
    VALUES ('00000000-0000-0000-0000-000000000003', 'tenant-b', '00000000-0000-0000-0000-000000000001', 'received');
    RAISE EXCEPTION 'cross-tenant reference unexpectedly accepted';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;
  BEGIN
    INSERT INTO nawa_intake_jobs(id, tenant_id, document_id, state)
    VALUES ('00000000-0000-0000-0000-000000000004', 'tenant-a', '00000000-0000-0000-0000-000000000001', 'completed');
    RAISE EXCEPTION 'completed job without result unexpectedly accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;
END $$;
INSERT INTO nawa_intake_jobs(id, tenant_id, document_id, state)
VALUES ('00000000-0000-0000-0000-000000000005', 'tenant-a', '00000000-0000-0000-0000-000000000001', 'received');
UPDATE nawa_intake_jobs SET state='processing', attempts=1, claim_token_hash=repeat('b',64), lease_until=now()+interval '1 minute';
UPDATE nawa_intake_jobs SET state='completed', claim_token_hash=NULL, lease_until=NULL, result='{"synthetic":true}'::jsonb;
SELECT state, attempts, result->>'synthetic' AS synthetic_result FROM nawa_intake_jobs;
