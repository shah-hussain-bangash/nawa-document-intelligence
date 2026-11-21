"""Draft protected API handler. Not wired into the dashboard entrypoint.

The supplied session service must resolve current server-side membership, and
the scoped service must enforce tenant boundaries in every database operation.
No unauthenticated fallback is allowed for protected paths.
"""
from http.cookies import SimpleCookie, CookieError
import json
from urllib.parse import urlsplit, parse_qs

from .dashboard import MAX_BODY, make_handler
from .session_draft import SessionError
from .scoped_state import AccessDenied


def make_protected_handler(scoped, sessions, health_state, *, flow=None, secure_cookies=False,
                           allowed_origin='http://127.0.0.1:8765'):
    Base = make_handler(health_state)

    class Handler(Base):
        def _cookie(self, name):
            raw = self.headers.get('Cookie', '')
            if sum(part.strip().startswith(name + '=') for part in raw.split(';')) != 1:
                raise SessionError('Session unavailable')
            cookie = SimpleCookie()
            try:
                cookie.load(raw)
            except CookieError:
                raise SessionError('Session unavailable') from None
            if name not in cookie:
                raise SessionError('Session unavailable')
            return cookie[name].value

        def _session(self):
            return self._cookie('nawa_session')

        def _redirect(self, location, cookies):
            if '\r' in location or '\n' in location:
                raise ValueError('Invalid redirect')
            self.send_response(303)
            self.send_header('Location', location)
            self.send_header('Cache-Control', 'no-store')
            for cookie in cookies:
                self.send_header('Set-Cookie', cookie)
            self.send_header('Content-Length', '0')
            self.end_headers()

        def _set_cookie(self, name, value, *, http_only, max_age):
            flags = '; Path=/; SameSite=Lax; Max-Age=' + str(max_age)
            if http_only:
                flags += '; HttpOnly'
            if secure_cookies:
                flags += '; Secure'
            return name + '=' + value + flags

        def _principal(self, action):
            return sessions.authorize_current(self._session(), action, csrf=self.headers.get('X-NAWA-CSRF'))

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/auth/config':
                return self._json({'mode': 'oidc'})
            if path == '/auth/login' and flow is not None:
                try:
                    result = flow.begin()
                    return self._redirect(result['authorization_url'],
                        [self._set_cookie('nawa_oidc_state', result['state_cookie'], http_only=True, max_age=300)])
                except Exception:
                    return self._json({'error': 'Sign-in unavailable'}, 503)
            if path == '/auth/callback' and flow is not None:
                try:
                    query = parse_qs(urlsplit(self.path).query, keep_blank_values=True)
                    if len(query.get('code', [])) != 1 or len(query.get('state', [])) != 1:
                        raise ValueError('Invalid callback')
                    tokens = flow.callback(state=query['state'][0], state_cookie=self._cookie('nawa_oidc_state'),
                                           code=query['code'][0])
                    return self._redirect('/', [
                        self._set_cookie('nawa_oidc_state', '', http_only=True, max_age=0),
                        self._set_cookie('nawa_session', tokens['session'], http_only=True, max_age=tokens['max_age']),
                        self._set_cookie('nawa_csrf', tokens['csrf'], http_only=False, max_age=tokens['max_age'])])
                except Exception:
                    return self._json({'error': 'Sign-in could not be completed'}, 403)
            if path == '/auth/me':
                try:
                    principal = self._principal('view')
                    return self._json({'tenant': principal.tenant, 'role': principal.role})
                except (SessionError, AccessDenied):
                    return self._json({'error': 'Authentication or permission required'}, 403)
                except Exception:
                    return self._json({'error': 'Identity service unavailable'}, 503)
            if path == '/api/quotations':
                try:
                    principal = self._principal('list')
                    return self._json({'quotations': scoped.list_items(principal), 'storage': 'postgres'})
                except (SessionError, AccessDenied):
                    return self._json({'error': 'Authentication or permission required'}, 403)
                except Exception:
                    return self._json({'error': 'Quotation storage unavailable'}, 503)
            # Only static files, public sample names and readiness can be served
            # by the base handler; no other base API path is reachable here.
            if path in ('/', '/app.js', '/style.css', '/favicon.ico', '/api/samples', '/api/ready'):
                return super().do_GET()
            return self._json({'error': 'Not found'}, 404)

        def do_POST(self):
            path = urlsplit(self.path).path
            if path == '/auth/logout':
                try:
                    if self.headers.get('Origin') != allowed_origin:
                        raise SessionError('Request denied')
                    sessions.logout(self._session(), self.headers.get('X-NAWA-CSRF'))
                    return self._redirect('/', [self._set_cookie('nawa_session', '', http_only=True, max_age=0),
                                                self._set_cookie('nawa_csrf', '', http_only=False, max_age=0)])
                except SessionError:
                    return self._json({'error': 'Authentication or permission required'}, 403)
                except Exception:
                    return self._json({'error': 'Identity service unavailable'}, 503)
            actions = {'/api/load-sample': 'load', '/api/upload': 'load', '/api/compare': 'compare',
                       '/api/review/start': 'review_start', '/api/review/show': 'review_view',
                       '/api/review/decide': 'decide', '/api/review/correct': 'correct'}
            action = actions.get(path)
            if action is None:
                return self._json({'error': 'Not found'}, 404)
            try:
                # All POST requests require an expected browser origin. State
                # changes additionally require the session-bound CSRF token.
                if self.headers.get('Origin') != allowed_origin:
                    return self._json({'error': 'Request denied'}, 403)
                principal = self._principal(action)
                if self.headers.get_content_type() != 'application/json':
                    raise ValueError('Content-Type must be application/json')
                length = int(self.headers.get('Content-Length', '-1'))
                if length < 1 or length > MAX_BODY:
                    raise ValueError('Request body size invalid')
                payload = json.loads(self.rfile.read(length).decode('utf-8'))
                if not isinstance(payload, dict):
                    raise ValueError('Expected JSON object')
                if action == 'load':
                    if path == '/api/upload':
                        result = scoped.add_upload(principal, payload.get('filename'), payload.get('content_base64'))
                    else:
                        result = scoped.add_sample(principal, payload.get('name'))
                elif action == 'compare':
                    result = scoped.compare(principal, payload.get('ids'))
                elif action == 'review_start':
                    result = scoped.review_start(principal, payload.get('id'))
                elif action == 'review_view':
                    result = scoped.review_show(principal, payload.get('id'))
                elif action == 'decide':
                    result = scoped.review_decision(principal, payload)
                else:
                    result = scoped.review_correction(principal, payload)
                return self._json(result)
            except (SessionError, AccessDenied):
                return self._json({'error': 'Authentication or permission required'}, 403)
            except (ValueError, TypeError, KeyError, UnicodeError):
                return self._json({'error': 'Invalid or unavailable request'}, 400)
            except Exception:
                return self._json({'error': 'Quotation storage unavailable'}, 503)

    return Handler
