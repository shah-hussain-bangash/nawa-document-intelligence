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
    promote_payload = json.dumps({'id':document_id}).encode()
    status, _, promoted_body = oidc.request(analyst, oidc.APP + '/api/intake/promote', data=promote_payload, headers=headers)
    if status != 200 or not json.loads(promoted_body)['created']:
        raise AssertionError('Synthetic review promotion failed')
    quotation_id = json.loads(promoted_body)['id']
    status, _, repeated = oidc.request(analyst, oidc.APP + '/api/intake/promote', data=promote_payload, headers=headers)
    if status != 200 or json.loads(repeated)['created'] or json.loads(repeated)['id'] != quotation_id:
        raise AssertionError('Synthetic review promotion was not idempotent')
    status, _, _ = oidc.request(analyst, oidc.APP + '/api/review/start',
                                data=json.dumps({'id':quotation_id}).encode(), headers=headers)
    if status != 200:
        raise AssertionError('Synthetic promoted review could not start')

    # This user is provisioned for tenant B only and must not sign in to A.
    oidc.login(users['outsider'], expected=403)
    app_a, origin_a = oidc.APP, oidc.ORIGIN
    oidc.APP, oidc.ORIGIN = 'http://127.0.0.1:8766', 'http://127.0.0.1:19766'
    for _ in range(30):
        try:
            status, _, _ = oidc.request(analyst, oidc.APP + '/api/ready')
            if status == 200:
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        raise AssertionError('Tenant B application unavailable')
    other_jar, other = oidc.login(users['outsider'])
    other_csrf = next(cookie.value for cookie in other_jar if cookie.name == 'nawa_csrf')
    other_headers = {'Content-Type':'application/json', 'Origin':oidc.ORIGIN, 'X-NAWA-CSRF':other_csrf}
    for endpoint in ('status', 'result'):
        status, _, _ = oidc.request(other, oidc.APP + '/api/intake/' + endpoint + '?id=' + document_id)
        if status != 404:
            raise AssertionError('Cross-tenant document access was not denied')
    status, _, other_result = oidc.request(other, oidc.APP + '/api/intake/submit', data=body, headers=other_headers)
    if status != 200 or not json.loads(other_result)['created']:
        raise AssertionError('Cross-tenant duplicate handling mismatch')
    other_document = json.loads(other_result)['id']
    if other_document == document_id:
        raise AssertionError('Tenant documents share an identifier')
    oidc.APP, oidc.ORIGIN = app_a, origin_a
    status, _, _ = oidc.request(analyst, oidc.APP + '/api/intake/status?id=' + other_document)
    if status != 404:
        raise AssertionError('Reverse cross-tenant document access was not denied')

    review_jar, reviewer = oidc.login(users['reviewer'])
    review_csrf = next(cookie.value for cookie in review_jar if cookie.name == 'nawa_csrf')
    status, _, _ = oidc.request(reviewer, oidc.APP + '/api/intake/submit', data=body,
                                headers={**headers, 'X-NAWA-CSRF':review_csrf})
    if status != 403:
        raise AssertionError('Reviewer upload was not denied')
    decision = json.dumps({'id':quotation_id, 'decision':'approve',
                           'reason':'Synthetic QA review', 'expected_revision':1}).encode()
    status, _, review_body = oidc.request(reviewer, oidc.APP + '/api/review/decide', data=decision,
                                          headers={**headers, 'X-NAWA-CSRF':review_csrf})
    if status != 200 or json.loads(review_body)['status'] != 'approved' or json.loads(review_body)['revision'] != 2:
        raise AssertionError('Synthetic reviewer decision failed')
    print('Synthetic Phase 13 QA passed: login, intake, worker, review, CSRF, role and cross-tenant denial.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Synthetic Phase 13 QA failed:', type(exc).__name__, '(details withheld).')
        raise SystemExit(1) from None

