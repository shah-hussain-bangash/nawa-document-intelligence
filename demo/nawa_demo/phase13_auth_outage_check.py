"""CI-only authenticated outage check for the disposable Phase 13 stack.

The test CA is trusted only by this process. This does not test a browser or
change the operating-system certificate store.
"""
import base64
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import ssl
import subprocess
import time
from urllib.request import ProxyHandler, HTTPCookieProcessor, HTTPSHandler, build_opener

from . import phase12_live_check as oidc

COMPOSE = ['docker', 'compose', '-p', 'nawa-phase13-ci', '-f', 'compose.phase13-qa.yaml']


def client():
    jar = CookieJar()
    context = ssl.create_default_context(cafile='.data/phase13-identity/ca.pem')
    return jar, build_opener(ProxyHandler({}), HTTPCookieProcessor(jar),
                             HTTPSHandler(context=context), oidc.NoRedirect())


def compose(*args):
    subprocess.run([*COMPOSE, *args], check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=45)


def wait_ready(opener):
    for _ in range(30):
        try:
            status, _, _ = oidc.request(opener, oidc.APP + '/api/ready')
            if status == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError('Synthetic QA database did not recover')


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('NAWA_PHASE13_CI_QA') != '1':
        raise ValueError('Only the disposable GitHub Phase 13 QA stack is supported')
    oidc.ISSUER = 'https://localhost:19443/realms/nawa-phase13'
    oidc.ORIGIN = oidc.APP = 'http://127.0.0.1:19765'
    oidc.client = client
    users = json.loads(Path('.data/phase13-identity/fixture.json').read_text(encoding='utf-8'))['users']
    analyst_user = next(user for user in users if user['role'] == 'analyst')
    document_id = json.loads(Path('/tmp/nawa13-before.json').read_text(encoding='utf-8'))['document_id']
    jar, analyst = oidc.login(analyst_user)
    csrf = next(cookie.value for cookie in jar if cookie.name == 'nawa_csrf')
    headers = {'Content-Type':'application/json', 'Origin':oidc.ORIGIN, 'X-NAWA-CSRF':csrf}
    url = oidc.APP + '/api/intake/result?id=' + document_id
    status, _, body = oidc.request(analyst, url)
    if status != 200 or json.loads(body)['result']['total'] != '1050.00':
        raise AssertionError('Synthetic result unavailable before outage')
    stopped = False
    try:
        # The command can fail after Docker has already stopped the service.
        stopped = True
        compose('stop', 'db')
        status, _, body = oidc.request(analyst, url)
        if status != 503 or json.loads(body) != {'error':'Intake unavailable'}:
            raise AssertionError('Authenticated read did not fail safely')
        payload = json.dumps({'filename':'outage.txt',
                              'content_base64':base64.b64encode(b'synthetic').decode()}).encode()
        status, _, body = oidc.request(analyst, oidc.APP + '/api/intake/submit', data=payload, headers=headers)
        if status != 503 or json.loads(body) != {'error':'Quotation storage unavailable'}:
            raise AssertionError('Authenticated write did not fail safely')
    finally:
        if stopped:
            compose('start', 'db')
            wait_ready(analyst)
    status, _, body = oidc.request(analyst, url)
    if status != 200 or json.loads(body)['result']['total'] != '1050.00':
        raise AssertionError('Synthetic result unavailable after recovery')
    print('PASS: authenticated synthetic reads and writes fail safely during a database outage and recover afterward.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Synthetic outage check failed:', type(exc).__name__, '(details withheld).')
        raise SystemExit(1) from None

