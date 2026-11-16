"""PostgreSQL-backed synthetic dashboard state; no authenticated identities."""
from __future__ import annotations

import json
from uuid import uuid4

from .dashboard import DashboardState, _public_quote
from .migrate import migrate
from .review import begin, correct, decide, inspect


class PostgresState(DashboardState):
    def __init__(self, connect):
        self._connect = connect
        with self._connect() as conn:
            migrate(conn)

    def ready(self):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM nawa_quotations LIMIT 1')

    def _add(self, quote):
        item_id = uuid4().hex[:12]
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT pg_advisory_xact_lock(%s)', (6892110312,))
                cur.execute('SELECT count(*) FROM nawa_quotations')
                if cur.fetchone()[0] >= 20:
                    raise ValueError('Demo limit: 20 quotations per session')
                cur.execute('INSERT INTO nawa_quotations (id, quotation) VALUES (%s, %s::jsonb)',
                            (item_id, json.dumps(quote, ensure_ascii=False, allow_nan=False)))
        return {'id': item_id, 'quotation': _public_quote(quote)}

    def list_items(self):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id, quotation FROM nawa_quotations ORDER BY created_at, id')
                return [{'id': row[0], 'quotation': _public_quote(row[1])} for row in cur.fetchall()]

    def get_quote(self, item_id):
        if not isinstance(item_id, str):
            raise ValueError('Quotation not found in this session')
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT quotation FROM nawa_quotations WHERE id = %s', (item_id,))
                row = cur.fetchone()
        if row is None:
            raise ValueError('Quotation not found in this session')
        return row[0]

    def review_start(self, item_id):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT quotation FROM nawa_quotations WHERE id = %s FOR UPDATE', (item_id,))
                row = cur.fetchone()
                if row is None:
                    raise ValueError('Quotation not found in this session')
                cur.execute('SELECT 1 FROM nawa_reviews WHERE quotation_id = %s', (item_id,))
                if cur.fetchone():
                    raise ValueError('Review already initialized for quotation')
                ledger = begin(row[0])
                cur.execute('INSERT INTO nawa_reviews (quotation_id, revision, ledger) VALUES (%s, %s, %s::jsonb)',
                            (item_id, 1, json.dumps(ledger, ensure_ascii=False)))
        return inspect(ledger)

    def review_show(self, item_id):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT revision, ledger FROM nawa_reviews WHERE quotation_id = %s', (item_id,))
                row = cur.fetchone()
        if row is None:
            raise ValueError('Review is not initialized')
        result = inspect(row[1])
        if result['revision'] != row[0]:
            raise ValueError('Review revision mismatch')
        return result

    def _change(self, payload, operation):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT revision, ledger FROM nawa_reviews WHERE quotation_id = %s FOR UPDATE',
                            (payload.get('id'),))
                row = cur.fetchone()
                if row is None:
                    raise ValueError('Review is not initialized')
                if inspect(row[1])['revision'] != row[0]:
                    raise ValueError('Review revision mismatch')
                new = operation(row[1])
                result = inspect(new)
                cur.execute('UPDATE nawa_reviews SET revision = %s, ledger = %s::jsonb, updated_at = now() WHERE quotation_id = %s',
                            (result['revision'], json.dumps(new, ensure_ascii=False), payload.get('id')))
        return result

    def review_decision(self, payload):
        return self._change(payload, lambda record: decide(
            record, actor=payload.get('actor'), decision=payload.get('decision'),
            reason=payload.get('reason'), expected_revision=payload.get('expected_revision')))

    def review_correction(self, payload):
        return self._change(payload, lambda record: correct(
            record, actor=payload.get('actor'), field=payload.get('field'), value=payload.get('value'),
            reason=payload.get('reason'), source=payload.get('source'), line=payload.get('line'),
            quote=payload.get('quote'), expected_revision=payload.get('expected_revision')))
