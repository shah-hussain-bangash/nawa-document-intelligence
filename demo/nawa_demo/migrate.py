"""Apply checksum-tracked PostgreSQL migrations for the synthetic demo.

Requires psycopg 3. This tool does not create or reset a database.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

MIGRATIONS = Path(__file__).with_name('migrations')


def migration_files():
    files = sorted(MIGRATIONS.glob('[0-9][0-9][0-9]_*.sql'))
    if not files:
        raise RuntimeError('No database migrations found')
    return [(p.name, p.read_bytes()) for p in files]


def migrate(connection):
    """Apply all pending migrations atomically, rejecting modified history."""
    files = migration_files()
    with connection.transaction():
        with connection.cursor() as cursor:
            # Serialize concurrent migration attempts in this database.
            cursor.execute('SELECT pg_advisory_xact_lock(%s)', (6892110311,))
            cursor.execute('''CREATE TABLE IF NOT EXISTS nawa_schema_migrations (
                name text PRIMARY KEY, checksum text NOT NULL,
                applied_at timestamptz NOT NULL DEFAULT now())''')
            cursor.execute('SELECT name, checksum FROM nawa_schema_migrations')
            applied = dict(cursor.fetchall())
            known = {name for name, _ in files}
            if set(applied) - known:
                raise RuntimeError('Database contains unknown migrations')
            pending_seen = False
            for name, content in files:
                checksum = hashlib.sha256(content).hexdigest()
                if name in applied:
                    if pending_seen or applied[name] != checksum:
                        raise RuntimeError('Migration history mismatch')
                    continue
                pending_seen = True
                cursor.execute(content.decode('utf-8'))
                cursor.execute('INSERT INTO nawa_schema_migrations (name, checksum) VALUES (%s, %s)',
                               (name, checksum))
