"""Initialize only the dedicated Phase 13 synthetic QA database."""
import json
import os
from pathlib import Path

import psycopg
from .intake_migrate import apply_intake_migrations
from .migrate import migrate

ISSUER = 'https://localhost:19443/realms/nawa-phase13'


def main():
    if (os.environ.get('NAWA_INTAKE') != 'synthetic' or os.environ.get('NAWA_AUTH') != 'oidc'
            or os.environ.get('NAWA_STORAGE') != 'postgres'
            or os.environ.get('POSTGRES_DB') != 'nawa_phase13_qa_demo'):
        raise ValueError('Dedicated synthetic Phase 13 QA database required')
    users = json.loads(Path('/identity/fixture.json').read_text(encoding='utf-8'))['users']
    with psycopg.connect(host=os.environ['POSTGRES_HOST'], dbname=os.environ['POSTGRES_DB'],
                         user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'],
                         connect_timeout=5) as conn:
        migrate(conn)
        apply_intake_migrations(conn)
        conn.execute('INSERT INTO nawa_tenants (id) VALUES (%s) ON CONFLICT DO NOTHING', ('tenant-a',))
        for user in users:
            if user['role'] not in ('analyst', 'reviewer'):
                continue
            conn.execute('INSERT INTO nawa_identities (issuer,subject) VALUES (%s,%s) ON CONFLICT DO NOTHING',
                         (ISSUER, user['subject']))
            conn.execute('''INSERT INTO nawa_memberships (issuer,subject,tenant_id,role) VALUES (%s,%s,%s,%s)
                ON CONFLICT (issuer,subject,tenant_id) DO UPDATE SET role=EXCLUDED.role,active=true''',
                (ISSUER, user['subject'], 'tenant-a', user['role']))
    print('Dedicated synthetic Phase 13 QA database initialized.')


if __name__ == '__main__':
    main()

