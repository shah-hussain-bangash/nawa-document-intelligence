"""CI-only real-browser check against the isolated synthetic Phase 13 stack.

The session is obtained by a test client and injected into the browser. This
does not test browser OIDC login or modify any operating-system trust store.
"""
import json
import os
from pathlib import Path
import re
import time
from uuid import uuid4

from playwright.sync_api import sync_playwright
from . import phase12_live_check as oidc
from .phase13_auth_outage_check import client


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('NAWA_PHASE13_CI_QA') != '1':
        raise ValueError('Only the disposable GitHub Phase 13 QA stack is supported')
    oidc.ISSUER = 'https://localhost:19443/realms/nawa-phase13'
    oidc.ORIGIN = oidc.APP = 'http://127.0.0.1:19765'
    oidc.client = client
    users = json.loads(Path('.data/phase13-identity/fixture.json').read_text(encoding='utf-8'))['users']
    analyst = next(user for user in users if user['role'] == 'analyst')
    jar, _ = oidc.login(analyst)
    cookies = [{'name':cookie.name, 'value':cookie.value, 'url':oidc.ORIGIN,
                'httpOnly':cookie.name == 'nawa_session', 'sameSite':'Lax'}
               for cookie in jar if cookie.name in ('nawa_session', 'nawa_csrf')]
    if {cookie['name'] for cookie in cookies} != {'nawa_session', 'nawa_csrf'}:
        raise AssertionError('Synthetic session cookies unavailable')
    sample = Path('demo/samples/english_quote.txt').read_bytes() + ('\n# browser-' + uuid4().hex + '\n').encode()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            context.add_cookies(cookies)
            page = context.new_page()
            page.goto(oidc.APP, wait_until='domcontentloaded', timeout=15000)
            page.locator('#intakePanel').wait_for(state='visible', timeout=15000)
            page.locator('#intakeFiles').set_input_files({'name':'browser-synthetic.txt',
                                                          'mimeType':'text/plain','buffer':sample})
            page.locator('#intakeSubmit').click()
            result = page.locator('#intakeResults .row').first
            result.wait_for(state='visible', timeout=15000)
            match = re.search(r'ID: ([0-9a-f]{32})', result.inner_text())
            if not match:
                raise AssertionError('Synthetic browser submission did not return an ID')
            document_id = match.group(1)
            page.locator('#intakeRefresh').click()
            row = page.locator('#intakeJobs .row').filter(has_text=document_id)
            row.wait_for(state='visible', timeout=15000)
            row.get_by_role('button', name='Use document').click()
            if page.locator('#intakeId').input_value() != document_id:
                raise AssertionError('Synthetic browser selection failed')
            for _ in range(60):
                page.locator('#intakeCheck').click()
                page.wait_for_timeout(500)
                if 'completed' in page.locator('#intakeStatus').inner_text():
                    break
                time.sleep(0.5)
            else:
                raise AssertionError('Synthetic browser document did not complete')
            page.locator('#intakePromote').click()
            page.locator('#items').get_by_text('browser-synthetic.txt').wait_for(state='visible', timeout=15000)
            page.locator('#review').get_by_role('button', name='Start review').click(timeout=15000)
            page.locator('#review').get_by_text('Status: pending_review · revision 1').wait_for(state='visible', timeout=15000)
            context.close()
        finally:
            browser.close()
    print('PASS: real browser used synthetic session with live intake, worker, PostgreSQL and review.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Synthetic live-browser check failed:', type(exc).__name__, '(details withheld).')
        raise SystemExit(1) from None

