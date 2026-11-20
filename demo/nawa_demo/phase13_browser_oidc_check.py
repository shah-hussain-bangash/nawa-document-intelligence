"""CI-only browser-driven OIDC test for a disposable synthetic identity stack.

The CI runner trusts its freshly generated test CA in an ephemeral NSS store.
No user-system trust store, real identity provider or real records are used.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

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
    print('PASS: trusted synthetic browser sign-in, separate roles, denial and logout replay checks.')


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
