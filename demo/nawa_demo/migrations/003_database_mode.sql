-- Bind this application version's development database to one access mode.
-- Older application versions do not enforce this table; separate database
-- credentials and storage are still required as an operational boundary.
CREATE TABLE nawa_database_mode (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    mode text NOT NULL CHECK (mode IN ('demo', 'oidc'))
);
