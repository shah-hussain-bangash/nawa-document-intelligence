"""CI-only browser check of the experimental tracked-submitter policy.

Uses a disposable database, freshly generated identity provider and test CA.
"""
import json
import os
from pathlib import Path
import subprocess
from uuid import uuid4

from playwright.sync_api import sync_playwright
from .phase13_browser_oidc_check import ISSUER, login, require_ci


def fixture_memberships(action, analyst_subject, outsider_subject, reviewer_subject):
    require_ci()
    code = '''import os, sys, psycopg
if (os.environ.get('GITHUB_ACTIONS') != 'true'
        or os.environ.get('NAWA_SYNTHETIC_EVIDENCE') != 'ci'
        or os.environ.get('NAWA_SYNTHETIC_SUBMITTER_POLICY') != 'require_tracked'
        or os.environ.get('POSTGRES_DB') != 'nawa_phase13_qa_demo'):
    raise SystemExit(1)
with psycopg.connect(host=os.environ['POSTGRES_HOST'],dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],password=os.environ['POSTGRES_PASSWORD'],connect_timeout=5) as conn:
    issuer, analyst, outsider, reviewer, action = sys.argv[1:]
    tenant = 'tenant-strict-ui'
    if action == 'setup':
        conn.execute('INSERT INTO nawa_tenants (id) VALUES (%s)', (tenant,))
        for subject, role in ((analyst, 'analyst'), (outsider, 'analyst'), (reviewer, 'reviewer')):
            conn.execute('INSERT INTO nawa_memberships (issuer,subject,tenant_id,role) VALUES (%s,%s,%s,%s)',
                         (issuer, subject, tenant, role))
    elif action == 'change_role':
        result = conn.execute("UPDATE nawa_memberships SET role='reviewer' WHERE issuer=%s AND subject=%s AND tenant_id=%s",
                              (issuer, analyst, tenant))
        if result.rowcount != 1: raise ValueError('Fixture membership unavailable')
    elif action == 'cleanup':
        conn.execute('DELETE FROM nawa_memberships WHERE issuer=%s AND tenant_id=%s AND subject IN (%s,%s,%s)',
                     (issuer, tenant, analyst, outsider, reviewer))
    else:
        raise ValueError('Invalid fixture operation')
'''
    subprocess.run(['docker', 'compose', '-p', 'nawa-phase13-ci', '-f', 'compose.phase13-qa.yaml',
                    'exec', '-T', 'nawa', 'python', '-c', code,
                    ISSUER, analyst_subject, outsider_subject, reviewer_subject, action],
                   check=True, capture_output=True, timeout=30)


def main():
    require_ci()
    users = json.loads(Path('.data/phase13-identity/fixture.json').read_text(encoding='utf-8'))['users']
    users = {user['role']:user for user in users}
    analyst, starter, reviewer = users['analyst'], users['outsider'], users['reviewer']
    fixture_memberships('setup', analyst['subject'], starter['subject'], reviewer['subject'])
    contexts = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                uploader_context, uploader = login(browser, analyst, tenant='tenant-strict-ui')
                contexts.append(uploader_context)
                filename = 'strict-' + uuid4().hex[:12] + '.txt'
                sample = Path('demo/samples/english_quote.txt').read_bytes()
                sample += ('\n# synthetic-strict-' + uuid4().hex + '\n').encode()
                uploader.locator('#upload').set_input_files({'name':filename,'mimeType':'text/plain','buffer':sample})
                uploader.get_by_role('button', name='Add selected file').click()
                uploader.locator('#items').get_by_text(filename).wait_for(state='visible', timeout=50000)

                starter_context, starter_page = login(browser, starter, tenant='tenant-strict-ui', role='analyst')
                contexts.append(starter_context)
                starter_page.get_by_role('button', name='Open review for ' + filename).click(timeout=15000)
                starter_page.get_by_role('button', name='Start review').click(timeout=15000)
                starter_page.get_by_text('Status: pending_review · revision 1').wait_for(state='visible', timeout=15000)

                uploader_context.close()
                contexts.remove(uploader_context)
                fixture_memberships('change_role', analyst['subject'], starter['subject'], reviewer['subject'])
                uploader_reviewer_context, uploader_reviewer = login(browser, analyst, tenant='tenant-strict-ui', role='reviewer')
                contexts.append(uploader_reviewer_context)
                uploader_reviewer.get_by_role('button', name='Open review for ' + filename).click(timeout=15000)
                uploader_reviewer.get_by_text('Status: pending_review · revision 1').wait_for(state='visible', timeout=15000)
                uploader_reviewer.get_by_placeholder('Explain your decision').fill('Synthetic attempted approval')
                uploader_reviewer.get_by_role('button', name='Approve', exact=True).click()
                uploader_reviewer.get_by_text('Decision denied.', exact=False).wait_for(state='visible', timeout=15000)

                reviewer_context, reviewer_page = login(browser, reviewer, tenant='tenant-strict-ui')
                contexts.append(reviewer_context)
                reviewer_page.get_by_role('button', name='Open review for ' + filename).click(timeout=15000)
                reviewer_page.get_by_text('Status: pending_review · revision 1').wait_for(state='visible', timeout=15000)
                reviewer_page.get_by_placeholder('Explain your decision').fill('Independent synthetic review')
                reviewer_page.get_by_role('button', name='Approve', exact=True).click()
                reviewer_page.get_by_text('Status: approved · revision 2').wait_for(state='visible', timeout=15000)
                reviewer_page.reload(wait_until='domcontentloaded')
                reviewer_page.get_by_role('button', name='Open review for ' + filename).click(timeout=15000)
                reviewer_page.get_by_text('Status: approved · revision 2').wait_for(state='visible', timeout=15000)
            finally:
                for context in contexts:
                    context.close()
                browser.close()
    finally:
        fixture_memberships('cleanup', analyst['subject'], starter['subject'], reviewer['subject'])
    print('PASS: synthetic browser uploader denied; independent reviewer approved and reopened.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Synthetic strict browser check failed:', type(exc).__name__, '(details withheld).')
        raise SystemExit(1) from None
