-- Synthetic intake test database only. Existing completed records remain NULL;
-- no historical origin is inferred and no existing source or result is changed.
ALTER TABLE nawa_intake_jobs
    ADD COLUMN result_origin text CHECK
        (result_origin IS NULL OR result_origin = 'synthetic_text_worker_v1');

ALTER TABLE nawa_intake_jobs
    ADD CONSTRAINT nawa_intake_result_origin_state CHECK
        (result_origin IS NULL OR state = 'completed');
