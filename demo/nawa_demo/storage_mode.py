"""Prevent accidental use of one database in both prototype access modes.

This is a startup guard in this application version, not database RLS. An older
application or privileged database client can bypass it. Use separate DBs and
credentials, and never treat it as a production isolation boundary.
"""


def claim_database_mode(connect, requested):
    if requested not in ('demo', 'oidc'):
        raise ValueError('Invalid database mode')
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (6892110313,))
            cur.execute('SELECT mode FROM nawa_database_mode WHERE singleton = true FOR UPDATE')
            row = cur.fetchone()
            if row is not None:
                if row[0] != requested:
                    raise RuntimeError('Database belongs to a different access mode')
                return
            cur.execute('SELECT EXISTS (SELECT 1 FROM nawa_quotation_tenants)')
            has_owned = cur.fetchone()[0]
            cur.execute('''SELECT EXISTS (SELECT 1 FROM nawa_quotations q
                LEFT JOIN nawa_quotation_tenants t ON t.quotation_id=q.id WHERE t.quotation_id IS NULL)''')
            has_unassigned = cur.fetchone()[0]
            if requested == 'demo' and has_owned:
                raise RuntimeError('Tenant-owned records require an authenticated database')
            if requested == 'oidc' and has_unassigned:
                raise RuntimeError('Legacy quotations require an explicit migration or a fresh database')
            cur.execute('INSERT INTO nawa_database_mode (singleton, mode) VALUES (true, %s)', (requested,))
