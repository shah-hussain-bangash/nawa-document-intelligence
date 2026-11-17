"""HTTP boundary tests with synthetic sessions; no real OIDC provider."""
import json
import base64
import http.client
import threading
import unittest
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from nawa_demo.authorization import Principal
from nawa_demo.dashboard import DashboardState
from nawa_demo.protected_api import make_protected_handler
from nawa_demo.intake_postgres import IntakeRejected
from nawa_demo.session_draft import SessionStore


class FakeScoped:
    def __init__(self):
        self.calls = []
    def list_items(self, principal):
        self.calls.append(('list', principal))
        return []
    def add_sample(self, principal, name):
        self.calls.append(('load', principal, name))
        return {'id': 'synthetic'}


class FakeIntake:
    def __init__(self):
        self.calls = []
    def submit(self, principal, filename, content):
        if filename == 'bad.pdf':
            raise ValueError('synthetic parser detail should not be disclosed')
        if filename == 'quota.txt':
            raise IntakeRejected('internal detail should not be disclosed')
        self.calls.append((principal, filename, content))
        return ('abc', True)
    def state(self, principal, document_id):
        return ('validated', 0) if document_id == 'abc' and principal.tenant == 'tenant-a' else None
    def list_documents(self, principal):
        return [{'id':'abc','filename':'synthetic.txt','state':'validated','attempts':0}] if principal.tenant == 'tenant-a' else []
    def result(self, principal, document_id):
        return None
    def link_version(self, principal, document_id, family_id, *, expected_previous):
        self.calls.append((principal, document_id, family_id, expected_previous))
        return expected_previous + 1
    def version_history(self, principal, family_id):
        return [(1, 'abc')] if family_id == 'family' and principal.tenant == 'tenant-a' else []
    def promote(self, principal, document_id):
        self.calls.append((principal, document_id))
        return {'id':'quote1', 'quotation':{'total':'1050.00'}, 'created':True}
    def requeue(self, principal, document_id, *, action, reason):
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError('A reason is required')
        self.calls.append((principal, document_id, action, reason))
        return {'id':document_id, 'state':'validated'}


class ProtectedApiTests(unittest.TestCase):
    def setUp(self):
        self.members = {('trusted', 'tenant-a'): Principal('trusted', 'tenant-a', 'analyst'),
                        ('viewer', 'tenant-a'): Principal('viewer', 'tenant-a', 'viewer')}
        self.sessions = SessionStore(lambda s, t: self.members.get((s, t)))
        self.analyst = self.sessions.issue('trusted', 'tenant-a')
        self.viewer = self.sessions.issue('viewer', 'tenant-a')
        self.scoped = FakeScoped()
        self.intake = FakeIntake()
        self.server = HTTPServer(('127.0.0.1', 0), make_protected_handler(self.scoped, self.sessions, DashboardState(), intake=self.intake))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, path, *, payload=None, cookie=None, csrf=None, origin=None, extra=None):
        headers = dict(extra or {})
        data = None
        if payload is not None:
            data = json.dumps(payload).encode()
            headers['Content-Type'] = 'application/json'
        if cookie is not None:
            headers['Cookie'] = cookie
        if csrf is not None:
            headers['X-NAWA-CSRF'] = csrf
        if origin is not None:
            headers['Origin'] = origin
        try:
            with urlopen(Request(self.url + path, data=data, headers=headers), timeout=3) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_anonymous_and_forged_headers_do_not_reach_data(self):
        status, _ = self.request('/api/quotations', extra={'X-Role': 'reviewer', 'X-Tenant': 'tenant-a'})
        self.assertEqual(status, 403)

    def test_intake_requires_session_origin_csrf_and_analyst_role(self):
        path = '/api/intake/submit'
        body = {'filename': 'sample.txt', 'content_base64': base64.b64encode(b'synthetic').decode()}
        origin = 'http://127.0.0.1:8765'
        self.assertEqual(self.request(path, payload=body, origin=origin)[0], 403)
        cookie = 'nawa_session=' + self.analyst['session']
        self.assertEqual(self.request(path, payload=body, cookie=cookie, origin=origin)[0], 403)
        self.assertEqual(self.request(path, payload=body, cookie=cookie, csrf=self.analyst['csrf'], origin='https://evil.example')[0], 403)
        self.assertEqual(self.request(path, payload=body, cookie='nawa_session='+self.viewer['session'], csrf=self.viewer['csrf'], origin=origin)[0], 403)
        self.assertEqual(self.intake.calls, [])
        status, data = self.request(path, payload=body, cookie=cookie, csrf=self.analyst['csrf'], origin=origin,
                                    extra={'X-Tenant': 'forged'})
        self.assertEqual((status, data['id']), (200, 'abc'))
        self.assertEqual(self.intake.calls[0][0].tenant, 'tenant-a')
        self.assertEqual(self.request('/api/intake/status?id=abc', cookie=cookie)[1]['state'], 'validated')
        self.assertEqual(self.request('/api/intake/result?id=abc', cookie=cookie)[0], 404)

    def test_batch_reports_individual_results_without_leaking_errors(self):
        cookie = 'nawa_session=' + self.analyst['session']
        content = base64.b64encode(b'synthetic').decode()
        body = {'files': [{'filename': 'ok.txt', 'content_base64': content},
                          {'filename': 'bad.pdf', 'content_base64': content}]}
        status, result = self.request('/api/intake/batch', payload=body, cookie=cookie,
                                      csrf=self.analyst['csrf'], origin='http://127.0.0.1:8765')
        self.assertEqual(status, 200)
        self.assertEqual(result['files'][0]['id'], 'abc')
        self.assertEqual(result['files'][1], {'error': 'Invalid or unsupported file'})
        self.assertNotIn('parser detail', json.dumps(result))
        self.assertEqual(len(self.intake.calls), 1)

    def test_quota_rejection_has_clear_safe_message(self):
        cookie = 'nawa_session=' + self.analyst['session']
        item = {'filename':'quota.txt', 'content_base64':base64.b64encode(b'synthetic').decode()}
        args = {'cookie':cookie, 'csrf':self.analyst['csrf'], 'origin':'http://127.0.0.1:8765'}
        status, result = self.request('/api/intake/submit', payload=item, **args)
        self.assertEqual((status, result), (400, {'error':'Synthetic document limit reached'}))
        status, result = self.request('/api/intake/batch', payload={'files':[item]}, **args)
        self.assertEqual((status, result['files'][0]), (200, {'error':'Synthetic document limit reached'}))

    def test_auth_config_advertises_intake_only_when_enabled(self):
        status, data = self.request('/auth/config')
        self.assertEqual(status, 200)
        self.assertIs(data['intake_enabled'], True)

    def test_version_routes_require_role_and_return_history(self):
        body = {'id': 'abc', 'family_id': None, 'expected_previous': 0}
        origin = 'http://127.0.0.1:8765'
        viewer_cookie = 'nawa_session=' + self.viewer['session']
        status, _ = self.request('/api/intake/version', payload=body, cookie=viewer_cookie,
                                 csrf=self.viewer['csrf'], origin=origin)
        self.assertEqual(status, 403)
        analyst_cookie = 'nawa_session=' + self.analyst['session']
        status, result = self.request('/api/intake/version', payload=body, cookie=analyst_cookie,
                                      csrf=self.analyst['csrf'], origin=origin)
        self.assertEqual(status, 200)
        self.assertEqual(result['version'], 1)
        self.assertEqual(len(result['family_id']), 32)
        status, history = self.request('/api/intake/versions?family=family', cookie=viewer_cookie)
        self.assertEqual((status, history['versions'][0]['id']), (200, 'abc'))

    def test_promotion_requires_analyst_and_session_csrf(self):
        origin = 'http://127.0.0.1:8765'
        body = {'id':'abc'}
        viewer_cookie = 'nawa_session=' + self.viewer['session']
        status, _ = self.request('/api/intake/promote', payload=body, cookie=viewer_cookie,
                                 csrf=self.viewer['csrf'], origin=origin)
        self.assertEqual(status, 403)
        analyst_cookie = 'nawa_session=' + self.analyst['session']
        status, _ = self.request('/api/intake/promote', payload=body, cookie=analyst_cookie, origin=origin)
        self.assertEqual(status, 403)
        status, result = self.request('/api/intake/promote', payload=body, cookie=analyst_cookie,
                                      csrf=self.analyst['csrf'], origin=origin)
        self.assertEqual((status, result['id']), (200, 'quote1'))
        self.assertEqual(self.intake.calls[-1][0].tenant, 'tenant-a')

    def test_requeue_requires_reason_analyst_and_csrf(self):
        path = '/api/intake/retry'
        body = {'id':'abc', 'reason':'Synthetic retry'}
        origin = 'http://127.0.0.1:8765'
        viewer = 'nawa_session=' + self.viewer['session']
        analyst = 'nawa_session=' + self.analyst['session']
        self.assertEqual(self.request(path, payload=body, cookie=viewer, csrf=self.viewer['csrf'], origin=origin)[0], 403)
        self.assertEqual(self.request(path, payload=body, cookie=analyst, origin=origin)[0], 403)
        self.assertEqual(self.request(path, payload={'id':'abc','reason':''}, cookie=analyst,
                                      csrf=self.analyst['csrf'], origin=origin)[0], 400)
        status, result = self.request(path, payload=body, cookie=analyst, csrf=self.analyst['csrf'], origin=origin)
        self.assertEqual((status, result['state']), (200, 'validated'))
        self.assertEqual(self.intake.calls[-1][2], 'retry')

    def test_document_list_requires_session_and_uses_session_tenant(self):
        self.assertEqual(self.request('/api/intake/documents')[0], 403)
        cookie = 'nawa_session=' + self.viewer['session']
        status, result = self.request('/api/intake/documents', cookie=cookie, extra={'X-Tenant':'forged'})
        self.assertEqual(status, 200)
        self.assertEqual(result['documents'][0]['id'], 'abc')
        self.assertEqual(self.scoped.calls, [])
        status, _ = self.request('/api/quotations', cookie='nawa_session=fake; nawa_session=other')
        self.assertEqual(status, 403)

    def test_logout_requires_csrf_and_revokes_session(self):
        cookie = 'nawa_session=' + self.analyst['session']
        status, _ = self.request('/auth/logout', payload={}, cookie=cookie,
                                 csrf='wrong', origin='http://127.0.0.1:8765')
        self.assertEqual(status, 403)
        self.assertEqual(self.request('/api/quotations', cookie=cookie)[0], 200)
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        connection.request('POST', '/auth/logout', headers={'Cookie': cookie,
                           'Origin':'http://127.0.0.1:8765', 'X-NAWA-CSRF':self.analyst['csrf']})
        response = connection.getresponse()
        self.assertEqual(response.status, 303)
        self.assertTrue(any('nawa_session=;' in value for value in response.headers.get_all('Set-Cookie')))
        response.read()
        connection.close()
        self.assertEqual(self.request('/api/quotations', cookie=cookie)[0], 403)

    def test_session_and_tenant_come_from_server(self):
        status, _ = self.request('/api/quotations', cookie='nawa_session=' + self.analyst['session'],
                                 extra={'X-Tenant': 'tenant-b', 'X-Role': 'reviewer'})
        self.assertEqual(status, 200)
        self.assertEqual(self.scoped.calls[-1][1].tenant, 'tenant-a')
        self.assertEqual(self.scoped.calls[-1][1].role, 'analyst')

    def test_writes_require_correct_origin_csrf_and_role(self):
        path, body = '/api/load-sample', {'name': 'english_quote.txt'}
        analyst_cookie = 'nawa_session=' + self.analyst['session']
        for origin, csrf in [(None, self.analyst['csrf']), ('https://evil.example', self.analyst['csrf']),
                             ('http://127.0.0.1:8765', None), ('http://127.0.0.1:8765', 'wrong')]:
            status, _ = self.request(path, payload=body, cookie=analyst_cookie, csrf=csrf, origin=origin)
            self.assertEqual(status, 403)
        status, _ = self.request(path, payload=body, cookie='nawa_session='+self.viewer['session'],
                                 csrf=self.viewer['csrf'], origin='http://127.0.0.1:8765')
        self.assertEqual(status, 403)
        self.assertEqual(self.scoped.calls, [])
        status, _ = self.request(path, payload=body, cookie=analyst_cookie,
                                 csrf=self.analyst['csrf'], origin='http://127.0.0.1:8765')
        self.assertEqual(status, 200)
        self.assertEqual(self.scoped.calls[-1][0], 'load')

    def test_revoked_membership_and_unknown_route_fail_closed(self):
        cookie = 'nawa_session=' + self.analyst['session']
        del self.members[('trusted', 'tenant-a')]
        self.assertEqual(self.request('/api/quotations', cookie=cookie)[0], 403)
        self.assertEqual(self.request('/api/not-a-route', payload={}, cookie=cookie,
                                      csrf=self.analyst['csrf'], origin='http://127.0.0.1:8765')[0], 404)
        self.assertEqual(self.scoped.calls, [])

    def test_auth_callback_sets_session_and_rejects_bad_state(self):
        sessions = self.sessions
        class FakeFlow:
            def begin(self):
                return {'authorization_url':'https://id.example/authorize?state=state123', 'state_cookie':'state123'}
            def callback(self, *, state, state_cookie, code):
                if (state, state_cookie, code) != ('state123', 'state123', 'valid-code'):
                    raise ValueError('Invalid callback')
                return sessions.issue('trusted', 'tenant-a')
        server = HTTPServer(('127.0.0.1', 0), make_protected_handler(self.scoped, sessions, DashboardState(), flow=FakeFlow()))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
            conn.request('GET', '/auth/login')
            response = conn.getresponse()
            self.assertEqual(response.status, 303)
            self.assertTrue(any('nawa_oidc_state=state123' in value and 'HttpOnly' in value
                                for value in response.headers.get_all('Set-Cookie')))
            response.read()
            conn.request('GET', '/auth/callback?state=state123&code=valid-code',
                         headers={'Cookie':'nawa_oidc_state=wrong'})
            response = conn.getresponse()
            self.assertEqual(response.status, 403)
            response.read()
            conn.request('GET', '/auth/callback?state=state123&code=valid-code',
                         headers={'Cookie':'nawa_oidc_state=state123'})
            response = conn.getresponse()
            self.assertEqual(response.status, 303)
            cookies = response.headers.get_all('Set-Cookie')
            self.assertTrue(any(value.startswith('nawa_session=') and 'HttpOnly' in value for value in cookies))
            self.assertTrue(any(value.startswith('nawa_csrf=') and 'HttpOnly' not in value for value in cookies))
            response.read()
            conn.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == '__main__':
    unittest.main()

