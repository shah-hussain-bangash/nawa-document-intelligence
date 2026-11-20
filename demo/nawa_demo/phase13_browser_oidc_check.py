"""CI-only browser-driven OIDC test for a disposable synthetic identity stack.

The CI runner trusts its freshly generated test CA in an ephemeral NSS store.
No user-system trust store, real identity provider or real records are used.
"""
import argparse
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from playwright.sync_api import Error, sync_playwright

APP = 'http://127.0.0.1:19765'
ISSUER = 'https://localhost:19443/realms/nawa-phase13'


def require_ci():
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('NAWA_PHASE13_CI_QA') != '1':
        raise ValueError('Only the disposable GitHub Phase 13 QA stack is supported')


def login(browser, user):
    context = browser.new_context(ignore_https_errors=False)
    page = context.new_page()
    if context.cookies() or page.request.get(APP + '/auth/me').status != 403:
        raise AssertionError('A new browser context must start without a session')
    page.goto(APP + '/auth/login', wait_until='domcontentloaded', timeout=30000)
    identity = urlparse(page.url)
    issuer = urlparse(ISSUER)
    if (identity.scheme != 'https' or identity.netloc != issuer.netloc or
            not identity.path.startswith(issuer.path + '/') or
            parse_qs(identity.query).get('code_challenge_method') != ['S256']):
        raise AssertionError('Unexpected identity endpoint or PKCE method')
    page.locator('#username').fill(user['username'])
    page.locator('#password').fill(user['password'])
    page.locator('#kc-login').click()
    page.wait_for_url(APP + '/**', timeout=30000)
    identity_response = page.request.get(APP + '/auth/me')
    if identity_response.status != 200 or identity_response.json() != {'tenant':'tenant-a', 'role':user['role']}:
        raise AssertionError('Synthetic browser identity did not match expected membership')
    return context, page


def expect_untrusted(browser):
    context = browser.new_context(ignore_https_errors=False)
    try:
        page = context.new_page()
        try:
            page.goto(ISSUER + '/.well-known/openid-configuration', timeout=30000)
        except Error as error:
            if 'ERR_CERT_AUTHORITY_INVALID' in str(error):
                return
            raise AssertionError('Unexpected browser TLS failure') from None
        raise AssertionError('Browser unexpectedly trusted the new synthetic CA')
    finally:
        context.close()


def synthetic_review_journey(analyst_page, reviewer_page):
    """Upload, correct and approve one synthetic quote through the browser UI."""
    sample = Path('demo/samples/english_quote.txt').read_bytes()
    if b'Grand Total: 1050.00' not in sample:
        raise AssertionError('Synthetic quotation fixture changed')
    sample = sample.replace(b'Grand Total: 1050.00', b'Grand Total: 1051.00')
    sample += ('\n# browser-oidc-' + uuid4().hex + '\n').encode()
    filename = 'browser-oidc-review.txt'
    analyst_page.locator('#intakePanel').wait_for(state='visible', timeout=15000)
    analyst_page.locator('#intakeFiles').set_input_files({'name':filename, 'mimeType':'text/plain', 'buffer':sample})
    analyst_page.locator('#intakeSubmit').click()
    result = analyst_page.locator('#intakeResults .row').first
    result.wait_for(state='visible', timeout=15000)
    match = re.search(r'ID: ([0-9a-f]{32})', result.inner_text())
    if not match:
        raise AssertionError('Synthetic browser intake did not return a document ID')
    document_id = match.group(1)
    analyst_page.locator('#intakeRefresh').click()
    row = analyst_page.locator('#intakeJobs .row').filter(has_text=document_id)
    row.wait_for(state='visible', timeout=15000)
    row.get_by_role('button', name='Use document').click()
    for _ in range(60):
        analyst_page.locator('#intakeCheck').click()
        analyst_page.wait_for_timeout(500)
        if 'completed' in analyst_page.locator('#intakeStatus').inner_text():
            break
        time.sleep(0.5)
    else:
        raise AssertionError('Synthetic browser intake did not complete')
    analyst_page.locator('#intakePromote').click()
    analyst_page.locator('#items').get_by_text(filename).wait_for(state='visible', timeout=15000)
    analyst_page.locator('#review').get_by_role('button', name='Start review').click(timeout=15000)
    analyst_page.locator('#review').get_by_text('Status: pending_review · revision 1').wait_for(state='visible', timeout=15000)
    analyst_page.locator('#details').get_by_text('Line 6: Grand Total: 1051.00').wait_for(state='visible', timeout=15000)
    analyst_page.locator('#review select').select_option('total')
    analyst_page.get_by_placeholder('Corrected value').fill('1050.00')
    analyst_page.get_by_placeholder('Reason for correction').fill('Synthetic arithmetic correction')
    analyst_page.get_by_placeholder('Evidence line number').fill('3')
    analyst_page.get_by_placeholder('Verbatim excerpt from source (reviewer assertion)').fill('Forged synthetic source line')
    analyst_page.locator('#review').get_by_role('button', name='Record correction').click()
    analyst_page.get_by_text('Invalid or unavailable request', exact=True).wait_for(state='visible', timeout=15000)
    analyst_page.locator('#review').get_by_text('Status: pending_review · revision 1').wait_for(state='visible', timeout=15000)
    analyst_page.get_by_placeholder('Verbatim excerpt from source (reviewer assertion)').fill('Subtotal: 1000.00')
    analyst_page.locator('#review').get_by_role('button', name='Record correction').click()
    analyst_page.locator('#review').get_by_text('Status: pending_review · revision 2').wait_for(state='visible', timeout=15000)
    reviewer_page.reload(wait_until='domcontentloaded')
    reviewer_page.locator('#items').get_by_text(filename).click(timeout=15000)
    reviewer_page.locator('#review').get_by_text('Status: pending_review · revision 2').wait_for(state='visible', timeout=15000)
    reviewer_page.get_by_placeholder('Explain your decision').fill('Synthetic reviewer checked correction')
    reviewer_page.locator('#review').get_by_role('button', name='Approve', exact=True).click()
    reviewer_page.locator('#review').get_by_text('Status: approved · revision 3').wait_for(state='visible', timeout=15000)
    reviewer_page.reload(wait_until='domcontentloaded')
    reviewer_page.locator('#items').get_by_text(filename).click(timeout=15000)
    reviewer_page.locator('#review').get_by_text('Status: approved · revision 3').wait_for(state='visible', timeout=15000)
    # Compare the approved correction with a second synthetic quotation.
    analyst_page.locator('#sample').select_option('arabic_quote.txt')
    analyst_page.locator('#loadSample').click()
    analyst_page.get_by_role('checkbox', name='Compare arabic_quote.txt').wait_for(state='visible', timeout=15000)
    analyst_page.get_by_role('checkbox', name='Compare ' + filename).check()
    analyst_page.get_by_role('checkbox', name='Compare arabic_quote.txt').check()
    analyst_page.locator('#compareBtn').click()
    analyst_page.locator('#comparison').get_by_text(
        'Example English Supplies — AED 1050.00 — Valid · approved review revision 3', exact=True
    ).wait_for(state='visible', timeout=15000)
    analyst_page.locator('#comparison').get_by_text(
        'Lowest valid total: شركة المثال للتوريدات', exact=True
    ).wait_for(state='visible', timeout=15000)


def synthetic_pdf_review_journey(analyst_page, reviewer_page, *, filename, global_line, page, sample_name=None, sample_bytes=None):
    """Exercise a synthetic PDF source check in the browser."""
    sample = sample_bytes if sample_bytes is not None else (Path('demo/samples/pdf') / sample_name).read_bytes()
    analyst_page.locator('#intakeFiles').set_input_files({'name':filename, 'mimeType':'application/pdf', 'buffer':sample})
    analyst_page.locator('#intakeSubmit').click()
    result = analyst_page.locator('#intakeResults .row').filter(has_text=filename).first
    result.wait_for(state='visible', timeout=15000)
    match = re.search(r'ID: ([0-9a-f]{32})', result.inner_text())
    if not match:
        raise AssertionError('Synthetic PDF intake did not return a document ID')
    document_id = match.group(1)
    analyst_page.locator('#intakeRefresh').click()
    row = analyst_page.locator('#intakeJobs .row').filter(has_text=document_id)
    row.wait_for(state='visible', timeout=15000)
    row.get_by_role('button', name='Use document').click()
    for _ in range(60):
        analyst_page.locator('#intakeCheck').click()
        analyst_page.wait_for_timeout(500)
        if 'completed' in analyst_page.locator('#intakeStatus').inner_text():
            break
        time.sleep(0.5)
    else:
        raise AssertionError('Synthetic PDF intake did not complete')
    analyst_page.locator('#intakePromote').click()
    analyst_page.locator('#items').get_by_text(filename).wait_for(state='visible', timeout=15000)
    analyst_page.locator('#review').get_by_role('button', name='Start review').click(timeout=15000)
    analyst_page.locator('#review').get_by_text('Status: pending_review · revision 1').wait_for(state='visible', timeout=15000)
    analyst_page.locator('#review select').select_option('total')
    analyst_page.get_by_placeholder('Corrected value').fill('945')
    analyst_page.get_by_placeholder('Reason for correction').fill('Synthetic format correction')
    analyst_page.get_by_placeholder('Evidence line number').fill(str(global_line))
    analyst_page.get_by_placeholder('Verbatim excerpt from source (reviewer assertion)').fill('Grand Total: 945.00')
    analyst_page.locator('#review').get_by_role('button', name='Record correction').click()
    analyst_page.locator('#review').get_by_text('Status: pending_review · revision 2').wait_for(state='visible', timeout=15000)
    analyst_page.get_by_text(f'Correction recorded, revision 2 · retained PDF text matched: page {page}, line 6',
                             exact=True).wait_for(state='visible', timeout=15000)
    reviewer_page.reload(wait_until='domcontentloaded')
    reviewer_page.locator('#items').get_by_text(filename).click(timeout=15000)
    reviewer_page.locator('#review').get_by_text('Status: pending_review · revision 2').wait_for(state='visible', timeout=15000)
    reviewer_page.get_by_placeholder('Explain your decision').fill('Synthetic reviewer checked formatting')
    reviewer_page.locator('#review').get_by_role('button', name='Approve', exact=True).click()
    reviewer_page.locator('#review').get_by_text('Status: approved · revision 3').wait_for(state='visible', timeout=15000)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expect-untrusted', action='store_true')
    args = parser.parse_args()
    require_ci()
    users = json.loads(Path('.data/phase13-identity/fixture.json').read_text(encoding='utf-8'))['users']
    users = {user['role']:user for user in users}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            if args.expect_untrusted:
                expect_untrusted(browser)
                print('PASS: browser rejected the untrusted synthetic identity certificate.')
                return
            analyst, analyst_page = login(browser, users['analyst'])
            reviewer, reviewer_page = login(browser, users['reviewer'])
            try:
                if analyst is reviewer:
                    raise AssertionError('Browser contexts are not isolated')
                # A genuine reviewer session must not gain analyst upload privileges.
                status = reviewer_page.evaluate('''async () => {
                    const csrf = document.cookie.split('; ').find(x => x.startsWith('nawa_csrf='));
                    if (!csrf) return 0;
                    const r = await fetch('/api/intake/submit', {method:'POST',
                        headers:{'Content-Type':'application/json', 'X-NAWA-CSRF':decodeURIComponent(csrf.split('=')[1])},
                        body:JSON.stringify({filename:'synthetic.txt', content_base64:'eA=='})});
                    return r.status;
                }''')
                if status != 403:
                    raise AssertionError('Synthetic reviewer upload permission was not denied')
                synthetic_review_journey(analyst_page, reviewer_page)
                synthetic_pdf_review_journey(analyst_page, reviewer_page,
                    sample_name='arabic_text_supplier.pdf', filename='browser-synthetic-arabic.pdf', global_line=6, page=1)
                synthetic_pdf_review_journey(analyst_page, reviewer_page,
                    sample_name='second_page_supplier.pdf', filename='browser-synthetic-multipage.pdf', global_line=7, page=2)
                analyst_page.get_by_role('checkbox', name='Compare browser-synthetic-multipage.pdf').check()
                analyst_page.get_by_role('checkbox', name='Compare arabic_quote.txt').check()
                analyst_page.locator('#compareBtn').click()
                analyst_page.locator('#comparison').get_by_text(
                    'Example Page Two Supplies — AED 945 — Valid · approved review revision 3 · retained PDF text matched: page 2, line 6',
                    exact=True).wait_for(state='visible', timeout=15000)
                import pymupdf
                document = pymupdf.open()
                document.new_page().insert_text((50, 60), 'Synthetic cover')
                sheet = document.new_page()
                for index, line in enumerate(('Supplier: Browser New Supplier', 'Currency: AED',
                        'Subtotal: 900.00', 'VAT Rate: 5', 'VAT Amount: 45.00', 'Grand Total: 945.00')):
                    sheet.insert_text((50, 60 + index * 25), line)
                generated_pdf = document.tobytes()
                document.close()
                synthetic_pdf_review_journey(analyst_page, reviewer_page,
                    sample_bytes=generated_pdf, filename='browser-new-synthetic.pdf', global_line=7, page=2)
                analyst_page.get_by_role('checkbox', name='Compare browser-new-synthetic.pdf').check()
                analyst_page.get_by_role('checkbox', name='Compare arabic_quote.txt').check()
                analyst_page.locator('#compareBtn').click()
                analyst_page.locator('#comparison').get_by_text(
                    'Browser New Supplier — AED 945 — Valid · approved review revision 3 · retained PDF text matched: page 2, line 6',
                    exact=True).wait_for(state='visible', timeout=15000)
                # Logout invalidates the server-side session, including a replayed cookie.
                old = next(cookie for cookie in analyst.cookies() if cookie['name'] == 'nawa_session')
                status = analyst_page.evaluate('''async () => {
                    const csrf = document.cookie.split('; ').find(x => x.startsWith('nawa_csrf='));
                    if (!csrf) return 0;
                    const r = await fetch('/auth/logout', {method:'POST',
                        headers:{'X-NAWA-CSRF':decodeURIComponent(csrf.split('=')[1])}});
                    return r.status;
                }''')
                if status != 200 or analyst_page.request.get(APP + '/auth/me').status != 403:
                    raise AssertionError('Synthetic browser logout failed')
                replay = browser.new_context(ignore_https_errors=False)
                try:
                    replay.add_cookies([{'name':'nawa_session', 'value':old['value'], 'url':APP, 'httpOnly':True}])
                    if replay.request.get(APP + '/auth/me').status != 403:
                        raise AssertionError('Logged-out synthetic session was reusable')
                finally:
                    replay.close()
                if reviewer_page.request.get(APP + '/auth/me').status != 200:
                    raise AssertionError('Other synthetic browser session was affected')
            finally:
                reviewer.close()
                analyst.close()
        finally:
            browser.close()
    print('PASS: trusted synthetic browser sign-in, TXT and PDF review, roles and logout replay checks.')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as exc:
        # Assertion messages above are static and contain no fixture values.
        print('Synthetic browser OIDC check failed:', str(exc))
        raise SystemExit(1) from None
    except Exception as exc:
        print('Synthetic browser OIDC check failed:', type(exc).__name__, '(details withheld).')
        raise SystemExit(1) from None
