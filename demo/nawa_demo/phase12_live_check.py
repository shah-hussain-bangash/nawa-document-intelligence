"""Run synthetic local Keycloak/NAWA checks without printing private material.

Only works in the isolated Phase 12 QA topology. The CA is explicitly trusted
for this process, not installed into the operating system. Never use real users.
"""
import hashlib
from html.parser import HTMLParser
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import ssl
import time
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, ProxyHandler, HTTPCookieProcessor, HTTPSHandler, HTTPRedirectHandler, build_opener
import psycopg

from .migrate import migrate

APP = 'http://127.0.0.1:8765'
ORIGIN = 'http://127.0.0.1:18765'
ISSUER = 'https://localhost:18443/realms/nawa-phase12'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None


class LoginForm(HTMLParser):
    def __init__(self, form_id='kc-form-login'):
        super().__init__()
        self.active, self.action, self.values = False, None, {}
        self.form_id = form_id
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form' and attrs.get('id') == self.form_id:
            self.active, self.action = True, attrs.get('action')
        if self.active and tag == 'input' and attrs.get('name'):
            self.values[attrs['name']] = attrs.get('value', '')
    def handle_endtag(self, tag):
        if tag == 'form': self.active = False


def client():
    jar = CookieJar()
    context = ssl.create_default_context(cafile='/identity/ca.pem')
    return jar, build_opener(ProxyHandler({}), HTTPCookieProcessor(jar), HTTPSHandler(context=context), NoRedirect())


def request(opener, url, *, data=None, headers=None):
    try:
        response = opener.open(Request(url, data=data, headers=headers or {}), timeout=15)
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read(1024 * 1024)


def login(user, *, expected=303):
    jar, opener = client()
    status, headers, _ = request(opener, APP + '/auth/login')
    if status != 303: raise AssertionError('login start')
    url = headers['Location']
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.netloc != 'localhost:18443': raise AssertionError('authorization origin')
    if parse_qs(parsed.query).get('code_challenge_method') != ['S256']: raise AssertionError('PKCE')
    status, _, html = request(opener, url)
    if status != 200: raise AssertionError('identity page')
    form = LoginForm(); form.feed(html.decode('utf-8'))
    action = urlparse(form.action or '')
    if action.scheme != 'https' or action.netloc != 'localhost:18443': raise AssertionError('login origin')
    body = urlencode({**form.values, 'username': user['username'], 'password': user['password']}).encode()
    status, headers, _ = request(opener, form.action, data=body,
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
    if status not in (302, 303): raise AssertionError('identity response')
    callback = urlparse(headers['Location'])
    # Keycloak may ask an imported synthetic user to complete their profile.
    # Only the known profile action at the trusted local issuer is permitted.
    if (callback.scheme == 'https' and callback.netloc == 'localhost:18443'
            and callback.path.endswith('/login-actions/required-action')
            and parse_qs(callback.query).get('execution') == ['VERIFY_PROFILE']):
        status, _, html = request(opener, headers['Location'])
        if status != 200: raise AssertionError('synthetic profile page')
        profile = LoginForm('kc-update-profile-form'); profile.feed(html.decode('utf-8'))
        action = urlparse(profile.action or '')
        if action.scheme != 'https' or action.netloc != 'localhost:18443':
            raise AssertionError('synthetic profile origin')
        profile.values.update({'firstName':'Synthetic', 'lastName':user['role'].capitalize(),
                               'email':user['username'] + '@example.invalid'})
        status, headers, _ = request(opener, profile.action, data=urlencode(profile.values).encode(),
                                     headers={'Content-Type':'application/x-www-form-urlencoded'})
        if status not in (302, 303): raise AssertionError('synthetic profile update')
        callback = urlparse(headers['Location'])
    if callback.scheme != 'http' or callback.netloc != '127.0.0.1:18765' or callback.path != '/auth/callback':
        raise AssertionError('callback origin')
    status, _, _ = request(opener, APP + callback.path + '?' + callback.query)
    if status != expected: raise AssertionError('callback status')
    return jar, opener


def main():
    fixture = json.loads(Path('/identity/fixture.json').read_text(encoding='utf-8'))
    users = {x['role']: x for x in fixture['users']}
    params = dict(host=os.environ['POSTGRES_HOST'], dbname=os.environ['POSTGRES_DB'],
                  user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'], connect_timeout=5)
    with psycopg.connect(**params) as conn:
        migrate(conn)
        conn.execute('INSERT INTO nawa_tenants (id) VALUES (%s) ON CONFLICT DO NOTHING', ('tenant-a',))
        for role in ('analyst', 'reviewer'):
            user = users[role]
            conn.execute('INSERT INTO nawa_identities (issuer, subject) VALUES (%s,%s) ON CONFLICT DO NOTHING',
                         (ISSUER, user['subject']))
            conn.execute('''INSERT INTO nawa_memberships (issuer, subject, tenant_id, role) VALUES (%s,%s,%s,%s)
                         ON CONFLICT (issuer, subject, tenant_id) DO UPDATE SET role=EXCLUDED.role, active=true''',
                         (ISSUER, user['subject'], 'tenant-a', role))
    for _ in range(30):
        try:
            jar, opener = client()
            status, _, _ = request(opener, ISSUER + '/.well-known/openid-configuration')
            if status == 200: break
        except Exception:
            pass
        time.sleep(2)
    else:
        raise AssertionError('local identity readiness')
    jar, analyst = login(users['analyst'])
    status, _, body = request(analyst, APP + '/auth/me')
    if status != 200 or json.loads(body)['role'] != 'analyst': raise AssertionError('analyst membership')
    status, _, _ = request(analyst, APP + '/api/load-sample', data=b'{"name":"english_quote.txt"}',
                           headers={'Content-Type':'application/json', 'Origin':ORIGIN})
    if status != 403: raise AssertionError('CSRF rejection')
    csrf = next(c.value for c in jar if c.name == 'nawa_csrf')
    headers = {'Content-Type':'application/json', 'Origin':ORIGIN, 'X-NAWA-CSRF':csrf}
    status, _, body = request(analyst, APP + '/api/load-sample', data=b'{"name":"english_quote.txt"}', headers=headers)
    if status != 200: raise AssertionError('analyst load')
    item_id = json.loads(body)['id']
    payload = json.dumps({'id':item_id}).encode()
    status, _, _ = request(analyst, APP + '/api/review/start', data=payload, headers=headers)
    if status != 200: raise AssertionError('review start')
    decision = json.dumps({'id':item_id, 'decision':'approve', 'reason':'Synthetic QA',
                           'expected_revision':1, 'actor':'forged'}).encode()
    status, _, _ = request(analyst, APP + '/api/review/decide', data=decision, headers=headers)
    if status != 403: raise AssertionError('analyst approval denial')
    review_jar, reviewer = login(users['reviewer'])
    review_csrf = next(c.value for c in review_jar if c.name == 'nawa_csrf')
    review_headers = {'Content-Type':'application/json', 'Origin':ORIGIN, 'X-NAWA-CSRF':review_csrf}
    status, _, body = request(reviewer, APP + '/api/review/decide', data=decision, headers=review_headers)
    if status != 200: raise AssertionError('reviewer approval')
    key = json.dumps([ISSUER, users['reviewer']['subject']], ensure_ascii=False, separators=(',', ':'))
    expected_actor = 'oidc:' + hashlib.sha256(key.encode()).hexdigest()
    if json.loads(body)['history'][-1]['actor'] != expected_actor: raise AssertionError('server actor')
    login(users['outsider'], expected=403)
    with psycopg.connect(**params) as conn:
        conn.execute('UPDATE nawa_memberships SET active=false WHERE issuer=%s AND subject=%s AND tenant_id=%s',
                     (ISSUER, users['reviewer']['subject'], 'tenant-a'))
    status, _, _ = request(reviewer, APP + '/api/quotations')
    if status != 403: raise AssertionError('membership revocation')
    status, _, _ = request(analyst, APP + '/auth/logout', data=b'', headers={'Origin':ORIGIN, 'X-NAWA-CSRF':csrf})
    if status != 303: raise AssertionError('logout')
    status, _, _ = request(analyst, APP + '/api/quotations')
    if status != 403: raise AssertionError('logout revocation')
    print('Local synthetic Keycloak checks passed: TLS, PKCE login, membership, CSRF, roles, actor, revocation and logout.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Local identity check failed:', type(exc).__name__, '(sensitive details withheld).')
        raise SystemExit(1) from None
