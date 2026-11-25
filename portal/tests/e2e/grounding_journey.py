"""Missing-field, supplied-field, scoped citations and historical-version UI."""
import os
from pathlib import Path
import shutil
import time
from uuid import uuid4
from playwright.sync_api import sync_playwright

BASE=os.getenv('WEB_TEST_URL','http://127.0.0.1:5173')
OUTPUT=Path('artifacts/screenshots');OUTPUT.mkdir(parents=True,exist_ok=True)
QUESTION="What is Falcon Digital's bank account number?"


def main():
    with sync_playwright() as p:
        options={'headless':True}
        executable=os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE') or shutil.which('chromium')
        if executable:options['executable_path']=executable
        if os.getenv('NAWA_BROWSER_NO_SANDBOX')=='true':options['args']=['--no-sandbox']
        browser=p.chromium.launch(**options)
        page=browser.new_page(viewport={'width':1440,'height':1100})
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(BASE)
        page.get_by_role('button',name='Enter workspace',exact=True).click()
        page.get_by_role('heading',name='Your operations, in focus.').wait_for()
        page.goto(BASE+'/knowledge')
        page.get_by_label('Question for knowledge assistant').fill(QUESTION)
        page.get_by_label('Send question').click()
        page.get_by_text('Evidence unavailable',exact=True).wait_for()
        assert page.locator('.citation-card').count()==0
        assert 'bank account number' in page.locator('.assistant-message').inner_text()
        page.screenshot(path=str(OUTPUT/'v061-missing-bank-evidence.png'),full_page=True)

        # Use an independently named, clearly synthetic supplier to keep the
        # reported missing-bank example absent in the shared demonstration DB.
        supplier='Grounding Fixture '+uuid4().hex[:7]
        content=f'SYNTHETIC TEST ONLY\nSupplier: {supplier}\nBank account number: 9911223344\n'
        page.goto(BASE+'/documents')
        page.get_by_role('button',name='Upload document',exact=True).click()
        page.get_by_label('Choose document file').set_input_files({'name':'grounding-'+uuid4().hex[:6]+'.txt','mimeType':'text/plain','buffer':content.encode()})
        with page.expect_response(lambda response:response.request.method=='POST' and response.url.endswith('/api/v1/documents')) as uploaded:
            page.get_by_role('button',name='Upload',exact=True).click()
        id=uploaded.value.json()['id']
        page.get_by_role('dialog').wait_for(state='hidden')
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            doc=page.request.get(BASE+f'/api/v1/documents/{id}').json()
            if doc['status']=='ready':break
            page.wait_for_timeout(200)
        assert doc['status']=='ready'
        page.goto(BASE+'/knowledge')
        page.get_by_label('Question for knowledge assistant').fill(f"What is {supplier}'s bank account number?")
        page.get_by_label('Send question').click()
        page.locator('.citation-card').first.wait_for()
        assert '9911223344' in page.locator('.citation-card').first.inner_text()

        # Change the source after retrieval, while retaining the old chat turn.
        session=page.request.get(BASE+'/auth/me').json()
        changed=page.request.post(BASE+f'/api/v1/documents/{id}/versions',headers={'X-CSRF-Token':session['csrf']},multipart={'expected_version':'1','file':{'name':'replaced.txt','mimeType':'text/plain','buffer':f'Supplier: {supplier}\nBank account number: not provided'.encode()}})
        assert changed.status==202
        page.locator('.citation-card').first.click()
        page.get_by_role('dialog').wait_for()
        assert '9911223344' in page.locator('.source-pages').inner_text()
        assert page.get_by_label('Source version').input_value()=='1'
        page.wait_for_timeout(2500)
        assert '9911223344' in page.locator('.source-pages').inner_text()
        assert page.get_by_label('Source version').input_value()=='1'
        page.get_by_label('Close dialog').click()
        page.get_by_label('Clear conversation').click()
        page.get_by_label('Question for knowledge assistant').fill('ما متطلبات المشتريات؟')
        page.get_by_label('Send question').click()
        page.locator('.citation-card').first.wait_for()
        assert 'دليل المشتريات التجريبي' in page.locator('.citation-card').first.inner_text()
        assert not errors,errors
        page.screenshot(path=str(OUTPUT/'v061-arabic-procurement-retained.png'),full_page=True)
        browser.close()
    print('Missing-field warning/no false citations, supported field, pinned citation after replacement and Arabic policy retrieval passed.')


if __name__=='__main__':main()
