# Synthetic data

Runtime seeding lives in `backend/src/uae_ai/seed.py`. For each of two independent
tenants it creates five role identities, ten procurement cases, ten fictional
policies and twenty fictional quotations, plus six service requests. It writes
the original text sources into the configured evidence directory.

All organisations, policies and decisions are learning samples, not official UAE
government or employment rules. The source register is the `POLICIES` list and
the synthetic quotation generation code; no personal/banking records are used.
Seeding is idempotent and disabled in production mode. Existing populated tenants
are preserved. This dataset is not a representative production benchmark.

Upload `.txt` or text-based `.pdf` files you are authorised to process. To replace
synthetic records with real data, first complete the permission, classification,
retention, model-route and deployment reviews in the security guide.
