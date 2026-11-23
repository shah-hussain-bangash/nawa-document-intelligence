"""CI-only real-browser check against the isolated synthetic Phase 13 stack.

The session is obtained by a test client and injected into the browser. This
does not test browser OIDC login or modify any operating-system trust store.
"""
import json
import os
from pathlib import Path
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
            page.locator('#upload').set_input_files({'name':'browser-synthetic.txt',
                                                     'mimeType':'text/plain','buffer':sample})
            page.get_by_role('button', name='Add selected file').click()
            page.locator('#items').get_by_text('browser-synthetic.txt').wait_for(state='visible', timeout=50000)
            page.locator('#review').get_by_role('button', name='Start review').click(timeout=15000)
            page.locator('#review').get_by_text('Status: pending_review · revision 1').wait_for(state='visible', timeout=15000)
            page.get_by_label('Field to correct').select_option('vat_rate_percent')
            page.get_by_label('Corrected value').fill('5.0')
            page.get_by_label('Reason for correction').fill('Normalize the synthetic rate')
            page.get_by_label('Original source line').fill('4')
            page.get_by_label('Exact source excerpt').fill('VAT Rate: 5')
            # Simulate another request changing the saved revision after this
            # browser loaded it; the pending form must survive the reload.
            status = page.evaluate('''async () => {
              const list = await (await fetch('/api/quotations')).json();
              const item = list.quotations.find(x => x.quotation.document === 'browser-synthetic.txt');
              if (!item) return 0;
              const csrf = (document.cookie.split('; ').find(x => x.startsWith('nawa_csrf=')) || '').slice(10);
              const response = await fetch('/api/review/correct', {method:'POST',
                headers:{'Content-Type':'application/json', 'X-NAWA-CSRF':csrf},
                body:JSON.stringify({id:item.id,field:'total',value:'1050',reason:'Synthetic concurrent formatting',
                  source:'browser-synthetic.txt',line:6,quote:'Grand Total: 1050.00',expected_revision:1})});
              return response.status;
            }''')
            if status != 200:
                raise AssertionError('Synthetic concurrent review update failed')
            page.get_by_role('button', name='Save correction').click()
            page.locator('#review .review-error').wait_for(state='visible', timeout=15000)
            page.get_by_role('button', name='Reload saved review').click()
            page.locator('#review').get_by_text('Status: pending_review · revision 2').wait_for(state='visible', timeout=15000)
            if page.get_by_label('Corrected value').input_value() != '5.0':
                raise AssertionError('Unsaved correction was not retained after reload')
            page.get_by_role('button', name='Save correction').click()
            page.locator('#review').get_by_text('Status: pending_review · revision 3').wait_for(state='visible', timeout=15000)
            page.get_by_role('button', name='Reopen saved review').click()
            page.get_by_text('Saved review reopened from the server at revision 3.').wait_for(state='visible', timeout=15000)
            if 'Originally extracted: 5' not in page.locator('#details').inner_text():
                raise AssertionError('Original extracted value was not shown')
            page.reload(wait_until='domcontentloaded')
            page.get_by_role('button', name='Open review for browser-synthetic.txt').click(timeout=15000)
            page.locator('#review').get_by_text('Status: pending_review · revision 3').wait_for(state='visible', timeout=15000)
            details = page.locator('#details').inner_text()
            if '5.0' not in details or 'VAT Rate: 5' not in details:
                raise AssertionError('Saved value and source evidence were not restored')
            context.close()
        finally:
            browser.close()
    print('PASS: synthetic browser intake, correction and reopen with worker and PostgreSQL.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Synthetic live-browser check failed:', type(exc).__name__, '(details withheld).')
        raise SystemExit(1) from None


