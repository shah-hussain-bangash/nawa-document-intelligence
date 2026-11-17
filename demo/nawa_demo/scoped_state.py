"""Draft tenant-scoped operations; not connected to any HTTP endpoint.

Callers must resolve Principal from verified, current server-side membership on
every request. Do not construct a Principal from client-provided role or tenant.
"""
from __future__ import annotations

import json
import hashlib
from decimal import Decimal
from uuid import uuid4

from .authorization import Principal, authorized
from .core import extract
from .dashboard import ALLOWED_SAMPLES, SAMPLES, DashboardState, _public_quote
from .identity_repository import membership_by_key
from .review import begin, correct, decide, inspect


class AccessDenied(ValueError):
    pass


class ReviewNotInitialized(ValueError):
    pass


class ScopedState:
    def __init__(self, connect):
        self._connect = connect

    @staticmethod
    def _require(principal, action):
        if not isinstance(principal, Principal) or not authorized(principal, action, tenant=principal.tenant):
            raise AccessDenied('Request denied')

    @staticmethod
    def _recheck(conn, principal, action):
        current = membership_by_key(conn, identity_key=principal.subject, tenant=principal.tenant, lock=True)
        if current != principal or not authorized(current, action, tenant=principal.tenant):
            raise AccessDenied('Request denied')

    def list_items(self, principal):
        self._require(principal, 'list')
        with self._connect() as conn:
            self._recheck(conn, principal, 'list')
            rows = conn.execute('''SELECT q.id, q.quotation FROM nawa_quotations q
                JOIN nawa_quotation_tenants t ON t.quotation_id = q.id
                WHERE t.tenant_id = %s ORDER BY q.created_at, q.id''', (principal.tenant,)).fetchall()
        return [{'id': item_id, 'quotation': _public_quote(quote)} for item_id, quote in rows]

    def _quote(self, conn, principal, item_id, *, lock=False):
        if not isinstance(item_id, str):
            raise ValueError('Quotation not found')
        statement = '''SELECT q.quotation FROM nawa_quotations q
            JOIN nawa_quotation_tenants t ON t.quotation_id = q.id
            WHERE q.id = %s AND t.tenant_id = %s'''
        # Keep the ownership mapping stable until this transaction completes,
        # including while fetching a related review or comparing quotations.
        statement += ' FOR UPDATE OF q, t' if lock else ' FOR SHARE OF q, t'
        row = conn.execute(statement, (item_id, principal.tenant)).fetchone()
        if row is None:
            raise ValueError('Quotation not found')
        return row[0]

    def get_quote(self, principal, item_id):
        self._require(principal, 'view')
        with self._connect() as conn:
            self._recheck(conn, principal, 'view')
            return _public_quote(self._quote(conn, principal, item_id))

    def add_sample(self, principal, name):
        self._require(principal, 'load')
        if name not in ALLOWED_SAMPLES:
            raise ValueError('Only allowlisted synthetic samples are available')
        quote = extract(SAMPLES / name)
        return self._add(principal, quote)

    def add_upload(self, principal, filename, content_base64):
        self._require(principal, 'load')
        owner = self
        class Parser(DashboardState):
            def _add(self, quote):
                return owner._add(principal, quote)
        return Parser().add_upload(filename, content_base64)

    def _add(self, principal, quote):
        item_id = uuid4().hex[:12]
        with self._connect() as conn:
            self._recheck(conn, principal, 'load')
            conn.execute('SELECT pg_advisory_xact_lock(%s)', (6892110312,))
            count = conn.execute('SELECT count(*) FROM nawa_quotation_tenants WHERE tenant_id = %s',
                                 (principal.tenant,)).fetchone()[0]
            if count >= 20:
                raise ValueError('Demo limit: 20 quotations per tenant')
            conn.execute('INSERT INTO nawa_quotations (id, quotation) VALUES (%s, %s::jsonb)',
                         (item_id, json.dumps(quote, ensure_ascii=False, allow_nan=False)))
            conn.execute('INSERT INTO nawa_quotation_tenants (quotation_id, tenant_id) VALUES (%s, %s)',
                         (item_id, principal.tenant))
        return {'id': item_id, 'quotation': _public_quote(quote)}

    def compare(self, principal, ids):
        self._require(principal, 'compare')
        if not isinstance(ids, list) or len(ids) < 2 or len(ids) > 20 or len(set(ids)) != len(ids):
            raise ValueError('Select at least two distinct quotations')
        with self._connect() as conn:
            self._recheck(conn, principal, 'compare')
            quotes = [self._quote(conn, principal, item_id) for item_id in ids]
        valid = [q for q in quotes if all(q['checks'].values())]
        ranked = sorted(valid, key=lambda q: (Decimal(q['total']), q['supplier'].casefold()))
        return {'quotations': [{**_public_quote(q), 'id': item_id} for item_id, q in zip(ids, quotes)],
                'lowest_valid_total': ranked[0]['supplier'] if ranked else None,
                'note': 'Synthetic AED price-only comparison, not a purchasing recommendation'}

    def review_start(self, principal, item_id):
        self._require(principal, 'review_start')
        with self._connect() as conn:
            self._recheck(conn, principal, 'review_start')
            quote = self._quote(conn, principal, item_id, lock=True)
            if conn.execute('SELECT 1 FROM nawa_reviews WHERE quotation_id = %s', (item_id,)).fetchone():
                raise ValueError('Review already initialized')
            ledger = begin(quote)
            conn.execute('INSERT INTO nawa_reviews (quotation_id, revision, ledger) VALUES (%s, %s, %s::jsonb)',
                         (item_id, 1, json.dumps(ledger, ensure_ascii=False)))
        return inspect(ledger)

    def review_show(self, principal, item_id):
        self._require(principal, 'review_view')
        with self._connect() as conn:
            self._recheck(conn, principal, 'review_view')
            self._quote(conn, principal, item_id)
            row = conn.execute('SELECT revision, ledger FROM nawa_reviews WHERE quotation_id = %s', (item_id,)).fetchone()
        if row is None:
            raise ReviewNotInitialized('Review is not initialized')
        result = inspect(row[1])
        if result['revision'] != row[0]:
            raise ValueError('Review revision mismatch')
        return result

    def _change(self, principal, payload, action):
        self._require(principal, action)
        item_id = payload.get('id')
        with self._connect() as conn:
            self._recheck(conn, principal, action)
            self._quote(conn, principal, item_id, lock=True)
            row = conn.execute('SELECT revision, ledger FROM nawa_reviews WHERE quotation_id = %s FOR UPDATE',
                               (item_id,)).fetchone()
            if row is None:
                raise ValueError('Review is not initialized')
            if inspect(row[1])['revision'] != row[0]:
                raise ValueError('Review revision mismatch')
            actor = 'oidc:' + hashlib.sha256(principal.subject.encode('utf-8')).hexdigest()
            if action == 'decide':
                updated = decide(row[1], actor=actor, decision=payload.get('decision'),
                                 reason=payload.get('reason'), expected_revision=payload.get('expected_revision'))
            else:
                updated = correct(row[1], actor=actor, field=payload.get('field'),
                                  value=payload.get('value'), reason=payload.get('reason'),
                                  source=payload.get('source'), line=payload.get('line'),
                                  quote=payload.get('quote'), expected_revision=payload.get('expected_revision'))
            result = inspect(updated)
            conn.execute('UPDATE nawa_reviews SET revision = %s, ledger = %s::jsonb, updated_at = now() WHERE quotation_id = %s',
                         (result['revision'], json.dumps(updated, ensure_ascii=False), item_id))
        return result

    def review_decision(self, principal, payload):
        return self._change(principal, payload, 'decide')

    def review_correction(self, principal, payload):
        return self._change(principal, payload, 'correct')

