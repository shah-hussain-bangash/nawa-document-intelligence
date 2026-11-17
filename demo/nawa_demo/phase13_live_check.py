"""Automated local synthetic Keycloak/intake check; not a browser login test."""
import base64
import json
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

from . import phase12_live_check as oidc


def main():
    oidc.ISSUER = 'https://localhost:19443/realms/nawa-phase13'
    oidc.ORIGIN = 'http://127.0.0.1:19765'
    fixture = json.loads(Path('/identity/fixture.json').read_text(encoding='utf-8'))
    users = {user['role']: user for user in fixture['users']}
    for _ in range(60):
        try:
            _, opener = oidc.client()
            status, _, _ = oidc.request(opener, oidc.ISSUER + '/.well-known/openid-configuration')
            if status == 200:
                break
        except Exception:
            pass
        time.sleep(2)
    else:
        raise AssertionError('Synthetic identity provider unavailable')

    jar, analyst = oidc.login(users['analyst'])
    status, _, body = oidc.request(analyst, oidc.APP + '/auth/config')
    if status != 200 or json.loads(body).get('intake_enabled') is not True:
        raise AssertionError('Synthetic intake unavailable')
    csrf = next(cookie.value for cookie in jar if cookie.name == 'nawa_csrf')
    headers = {'Content-Type': 'application/json', 'Origin': oidc.ORIGIN, 'X-NAWA-CSRF': csrf}
    sample = Path('/app/demo/samples/english_quote.txt').read_bytes() + ('\n# qa-' + uuid4().hex + '\n').encode()
    body = json.dumps({'filename': 'synthetic.txt', 'content_base64': base64.b64encode(sample).decode()}).encode()
    status, _, _ = oidc.request(analyst, oidc.APP + '/api/intake/submit', data=body,
                                headers={'Content-Type':'application/json', 'Origin':oidc.ORIGIN})
    if status != 403:
        raise AssertionError('Missing CSRF token was accepted')
    status, _, result = oidc.request(analyst, oidc.APP + '/api/intake/submit', data=body, headers=headers)
    if status != 200:
        raise AssertionError('Synthetic upload failed')
    document_id = json.loads(result)['id']
    for _ in range(10):
        subprocess.run([sys.executable, '-m', 'nawa_demo.intake_worker_cli'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=35)
        status, _, result = oidc.request(analyst, oidc.APP + '/api/intake/status?id=' + document_id)
        if status == 200 and json.loads(result)['state'] == 'completed':
            break
    else:
        raise AssertionError('Synthetic worker did not complete document')
    status, _, result = oidc.request(analyst, oidc.APP + '/api/intake/result?id=' + document_id)
    if status != 200 or json.loads(result)['result']['total'] != '1050.00':
        raise AssertionError('Synthetic result mismatch')

    review_jar, reviewer = oidc.login(users['reviewer'])
    review_csrf = next(cookie.value for cookie in review_jar if cookie.name == 'nawa_csrf')
    status, _, _ = oidc.request(reviewer, oidc.APP + '/api/intake/submit', data=body,
                                headers={**headers, 'X-NAWA-CSRF':review_csrf})
    if status != 403:
        raise AssertionError('Reviewer upload was not denied')
    print('Synthetic Phase 13 QA passed: Keycloak login, CSRF, upload, worker, result and role denial.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Synthetic Phase 13 QA failed:', type(exc).__name__, '(details withheld).')
        raise SystemExit(1) from None

