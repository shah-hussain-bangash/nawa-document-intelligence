"""Opt-in real OCR upload/view/download browser journey against local demo mode."""
import os
from pathlib import Path
import shutil
import time
from uuid import uuid4
from playwright.sync_api import sync_playwright

BASE=os.getenv('WEB_TEST_URL','http://127.0.0.1:5173')
OUTPUT=Path('artifacts/screenshots');OUTPUT.mkdir(parents=True,exist_ok=True)


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
        for language in ['en','ar']:
            page.goto(BASE+'/documents')
            page.get_by_role('button',name='Upload document',exact=True).click()
            name=f'scanned-{language}-{uuid4().hex[:6]}.pdf'
            page.get_by_label('Choose document file').set_input_files({'name':name,'mimeType':'application/pdf','buffer':Path(f'data/samples/scanned-quotation-{language}.pdf').read_bytes()})
            with page.expect_response(lambda response:response.request.method=='POST' and response.url.endswith('/api/v1/documents')) as uploaded:
                page.get_by_role('button',name='Upload',exact=True).click()
            id=uploaded.value.json()['id']
            page.get_by_role('dialog').wait_for(state='hidden')
            deadline=time.monotonic()+60
            while time.monotonic()<deadline:
                doc=page.request.get(BASE+f'/api/v1/documents/{id}').json()
                if doc['status'] not in {'queued','processing'}:break
                page.wait_for_timeout(300)
            assert doc['status']=='ready',doc['status']
            assert doc['pages'][0]['method']=='ocr'
            page.locator('button.table-case').filter(has_text=name).click()
            page.get_by_text('OCR text · verify against original',exact=True).wait_for()
            assert '12500' in page.locator('.source-page p').inner_text()
            assert page.locator('.source-warning').first.is_visible()
            with page.expect_download() as download:
                page.get_by_role('link',name='Download source',exact=True).click()
            assert Path(download.value.path()).read_bytes().startswith(b'%PDF-')
            page.screenshot(path=str(OUTPUT/f'v060-ocr-{language}.png'),full_page=True)
            page.get_by_label('Close dialog').click()
        assert not errors,errors
        browser.close()
    print('English/Arabic scanned upload, real OCR, review warning, source viewer and original download passed.')


if __name__=='__main__':main()
