-- Synthetic demonstration data only. Uploaded source files are not stored.
CREATE TABLE nawa_quotations (
    id text PRIMARY KEY CHECK (id ~ '^[0-9a-f]{12}$'),
    quotation jsonb NOT NULL CHECK (jsonb_typeof(quotation) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE nawa_reviews (
    quotation_id text PRIMARY KEY REFERENCES nawa_quotations(id) ON DELETE RESTRICT,
    revision integer NOT NULL CHECK (revision > 0),
    ledger jsonb NOT NULL CHECK (jsonb_typeof(ledger) = 'object'),
    updated_at timestamptz NOT NULL DEFAULT now()
);
