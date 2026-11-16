"""Operator-only local synthetic membership management, not an HTTP API.

Requires pre-existing tenant and identity records. It never accepts passwords
or tokens and never deletes quotation data. This is not an enterprise identity
provisioning system and should not be used with real users.
"""
from __future__ import annotations

import argparse
import os
from urllib.parse import urlsplit

from .authorization import PERMISSIONS


def _validate(issuer, subject, tenant):
    if not all(isinstance(x, str) and x.strip() == x and x for x in (issuer, subject, tenant)):
        raise ValueError('Invalid membership identifier')
    route = urlsplit(issuer)
    if (route.scheme != 'https' or not route.hostname or route.username or route.password
            or route.query or route.fragment or len(issuer) > 2048
            or len(subject) > 512 or len(tenant) > 128
            or any('\x00' in x for x in (issuer, subject, tenant))):
        raise ValueError('Invalid membership identifier')


def grant(connection, *, issuer, subject, tenant, role):
    """Grant one new membership; never silently reactivate or change a role."""
    _validate(issuer, subject, tenant)
    if not isinstance(role, str) or role not in PERMISSIONS:
        raise ValueError('Invalid role')
    with connection.transaction():
        with connection.cursor() as cur:
            cur.execute('SELECT active FROM nawa_tenants WHERE id=%s FOR UPDATE', (tenant,))
            tenant_row = cur.fetchone()
            cur.execute('SELECT active FROM nawa_identities WHERE issuer=%s AND subject=%s FOR UPDATE',
                        (issuer, subject))
            identity_row = cur.fetchone()
            if not tenant_row or not tenant_row[0] or not identity_row or not identity_row[0]:
                raise ValueError('Active tenant and identity must be provisioned first')
            cur.execute('SELECT 1 FROM nawa_memberships WHERE issuer=%s AND subject=%s AND tenant_id=%s',
                        (issuer, subject, tenant))
            if cur.fetchone():
                raise ValueError('Membership already exists; no change was made')
            cur.execute('INSERT INTO nawa_memberships (issuer, subject, tenant_id, role) VALUES (%s,%s,%s,%s)',
                        (issuer, subject, tenant, role))


def revoke(connection, *, issuer, subject, tenant):
    """Deactivate one membership; do not delete identity, session or data rows."""
    _validate(issuer, subject, tenant)
    with connection.transaction():
        with connection.cursor() as cur:
            cur.execute('''UPDATE nawa_memberships SET active=false
                WHERE issuer=%s AND subject=%s AND tenant_id=%s AND active=true RETURNING tenant_id''',
                        (issuer, subject, tenant))
            return cur.fetchone() is not None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('grant', 'revoke'))
    parser.add_argument('--issuer', required=True)
    parser.add_argument('--subject', required=True)
    parser.add_argument('--tenant', required=True)
    parser.add_argument('--role', choices=tuple(PERMISSIONS))
    args = parser.parse_args()
    if (args.operation == 'grant') != bool(args.role):
        parser.error('grant requires --role; revoke must not include --role')
    import psycopg
    try:
        with psycopg.connect(host=os.environ['POSTGRES_HOST'], dbname=os.environ['POSTGRES_DB'],
                             user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'],
                             connect_timeout=5) as conn:
            if args.operation == 'grant':
                grant(conn, issuer=args.issuer, subject=args.subject, tenant=args.tenant, role=args.role)
                print('Synthetic membership granted.')
            else:
                changed = revoke(conn, issuer=args.issuer, subject=args.subject, tenant=args.tenant)
                print('Synthetic membership revoked.' if changed else 'No active membership was changed.')
    except Exception:
        raise SystemExit('Membership operation failed; details withheld.') from None


if __name__ == '__main__':
    main()
