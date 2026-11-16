"""Phase 9 localhost-only, in-memory synthetic quotation demonstration.

No authentication, secure audit storage, or production upload support.
"""
from __future__ import annotations

import base64
import binascii
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import tempfile
from urllib.parse import urlsplit
from uuid import uuid4

from .core import extract
from .pdf_ingest import extract_pdf
from .review import begin, correct, decide, inspect

MAX_BODY = 8 * 1024 * 1024
SAMPLES = Path(__file__).resolve().parents[1] / 'samples'
WEB_DIR = Path(__file__).resolve().parents[1] / 'web'
WEB = WEB_DIR / 'index.html'
ALLOWED_SAMPLES = ('english_quote.txt', 'arabic_quote.txt', 'incorrect_vat_quote.txt')


def _public_quote(q):
    return {key: q[key] for key in ('document', 'supplier', 'currency', 'subtotal',
                                   'vat_rate_percent', 'vat_amount', 'total', 'checks', 'evidence')}


class DashboardState:
    """Ephemeral app state; review data are not written to disk."""
    def __init__(self):
        self.items = {}
        self.ledgers = {}

    def list_items(self):
        return [{'id': item_id, 'quotation': _public_quote(q)} for item_id, q in self.items.items()]

    def ready(self):
        return None

    def add_sample(self, name):
        if name not in ALLOWED_SAMPLES:
            raise ValueError('Only allowlisted synthetic samples are available')
        q = extract(SAMPLES / name)
        return self._add(q)

    def add_upload(self, filename, content_base64):
        if not isinstance(filename, str) or not filename or len(filename) > 100:
            raise ValueError('A short filename is required')
        if Path(filename).name != filename or filename.startswith('.') or '/' in filename or '\\' in filename:
            raise ValueError('Filename must not contain directory components')
        suffix = Path(filename).suffix.lower()
        if suffix not in ('.txt', '.pdf'):
            raise ValueError('Only UTF-8 .txt or selectable-text .pdf files are supported')
        if not isinstance(content_base64, str) or len(content_base64) > MAX_BODY:
            raise ValueError('File content too large')
        try:
            content = base64.b64decode(content_base64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError('Invalid base64 upload') from exc
        if len(content) > 4 * 1024 * 1024 or not content:
            raise ValueError('File must be between 1 byte and 4 MiB')
        with tempfile.TemporaryDirectory(prefix='nawa_dashboard_') as tmp:
            file = Path(tmp) / filename
            file.write_bytes(content)
            q = extract_pdf(file) if suffix == '.pdf' else extract(file)
        return self._add(q)

    def _add(self, quote):
        if len(self.items) >= 20:
            raise ValueError('Demo limit: 20 quotations per session')
        item_id = uuid4().hex[:12]
        self.items[item_id] = quote
        return {'id': item_id, 'quotation': _public_quote(quote)}

    def compare(self, ids):
        if not isinstance(ids, list) or len(ids) < 2 or len(ids) > 20 or len(set(ids)) != len(ids):
            raise ValueError('Select at least two distinct quotations')
        quotes = [self.get_quote(item_id) for item_id in ids]
        valid = [q for q in quotes if all(q['checks'].values())]
        ranked = sorted(valid, key=lambda q: (Decimal(q['total']), q['supplier'].casefold()))
        return {'quotations': [{**_public_quote(q), 'id': item_id} for item_id, q in zip(ids, quotes)],
                'lowest_valid_total': ranked[0]['supplier'] if ranked else None,
                'note': 'Synthetic AED price-only comparison, not a purchasing recommendation'}

    def get_quote(self, item_id):
        if not isinstance(item_id, str) or item_id not in self.items:
            raise ValueError('Quotation not found in this session')
        return self.items[item_id]

    def review_start(self, item_id):
        q = self.get_quote(item_id)
        if item_id in self.ledgers:
            raise ValueError('Review already initialized for quotation')
        record = begin(q)
        self.ledgers[item_id] = record
        return inspect(record)

    def review_show(self, item_id):
        if item_id not in self.ledgers:
            raise ValueError('Review is not initialized')
        return inspect(self.ledgers[item_id])

    def review_decision(self, payload):
        item_id = payload.get('id')
        self.review_show(item_id)
        record = decide(self.ledgers[item_id], actor=payload.get('actor'),
                        decision=payload.get('decision'), reason=payload.get('reason'),
                        expected_revision=payload.get('expected_revision'))
        self.ledgers[item_id] = record
        return inspect(record)

    def review_correction(self, payload):
        item_id = payload.get('id')
        self.review_show(item_id)
        record = correct(self.ledgers[item_id], actor=payload.get('actor'),
                         field=payload.get('field'), value=payload.get('value'),
                         reason=payload.get('reason'), source=payload.get('source'),
                         line=payload.get('line'), quote=payload.get('quote'),
                         expected_revision=payload.get('expected_revision'))
        self.ledgers[item_id] = record
        return inspect(record)


def make_handler(state):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'NAWA-Demo'

        def _headers(self, status, content_type, length):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(length))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Content-Security-Policy', "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
            self.end_headers()

        def _json(self, result, status=200):
            encoded = json.dumps(result, ensure_ascii=False, allow_nan=False).encode('utf-8')
            self._headers(status, 'application/json; charset=utf-8', len(encoded))
            self.wfile.write(encoded)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/':
                data = WEB.read_bytes()
                self._headers(200, 'text/html; charset=utf-8', len(data))
                self.wfile.write(data)
            elif path in ('/app.js', '/style.css'):
                data = (WEB_DIR / path.lstrip('/')).read_bytes()
                content_type = 'text/javascript; charset=utf-8' if path.endswith('.js') else 'text/css; charset=utf-8'
                self._headers(200, content_type, len(data))
                self.wfile.write(data)
            elif path == '/api/samples':
                self._json({'samples': list(ALLOWED_SAMPLES), 'mode': 'local_synthetic_demo'})
            elif path == '/api/ready':
                try:
                    state.ready()
                    self._json({'status': 'ready'})
                except Exception:
                    self._json({'error': 'Quotation storage unavailable'}, 503)
            elif path == '/api/quotations':
                try:
                    self._json({'quotations': state.list_items(), 'storage': getattr(state, 'storage_mode', 'memory')})
                except Exception:
                    self._json({'error': 'Quotation storage unavailable'}, 503)
            elif path == '/favicon.ico':
                self._headers(204, 'image/x-icon', 0)
            else:
                self._json({'error': 'Not found'}, 404)

        def do_POST(self):
            try:
                # Deny browser cross-origin writes; local clients without Origin can still use API.
                origin = self.headers.get('Origin')
                if origin not in (None, 'http://127.0.0.1:8765'):
                    raise ValueError('Cross-origin requests are not accepted')
                if self.headers.get_content_type() != 'application/json':
                    raise ValueError('Content-Type must be application/json')
                length = int(self.headers.get('Content-Length', '-1'))
                if length < 1 or length > MAX_BODY:
                    raise ValueError('Request body size invalid')
                payload = json.loads(self.rfile.read(length).decode('utf-8'))
                if not isinstance(payload, dict):
                    raise ValueError('Expected JSON object')
                path = urlsplit(self.path).path
                if path == '/api/load-sample':
                    result = state.add_sample(payload.get('name'))
                elif path == '/api/upload':
                    result = state.add_upload(payload.get('filename'), payload.get('content_base64'))
                elif path == '/api/compare':
                    result = state.compare(payload.get('ids'))
                elif path == '/api/review/start':
                    result = state.review_start(payload.get('id'))
                elif path == '/api/review/show':
                    result = state.review_show(payload.get('id'))
                elif path == '/api/review/decide':
                    result = state.review_decision(payload)
                elif path == '/api/review/correct':
                    result = state.review_correction(payload)
                else:
                    return self._json({'error': 'Not found'}, 404)
                return self._json(result)
            except (ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError) as exc:
                return self._json({'error': str(exc)}, 400)
            except Exception:
                return self._json({'error': 'Quotation storage unavailable'}, 503)

        def log_message(self, format, *args):
            # Suppress request URLs from casual terminal logs.
            return

    return Handler


def main():
    import argparse
    p = argparse.ArgumentParser(description='NAWA Phase 9 localhost-only synthetic web dashboard')
    p.add_argument('--port', type=int, default=8765)
    args = p.parse_args()
    if not 1024 <= args.port <= 65535:
        p.error('port must be between 1024 and 65535')
    state = DashboardState()
    # Port 8765 is required for browser Origin checks in this minimal demo.
    if args.port != 8765:
        p.error('this demo uses fixed port 8765 for Origin validation')
    with HTTPServer(('127.0.0.1', args.port), make_handler(state)) as server:
        print('NAWA synthetic dashboard: http://127.0.0.1:8765 (Ctrl+C to stop)', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
