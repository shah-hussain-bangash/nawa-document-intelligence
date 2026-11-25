"""Run with WEB_TEST_URL after setup/start; tests persisted corrections and versions."""
import os,shutil
from pathlib import Path
from uuid import uuid4
from playwright.sync_api import sync_playwright,expect
BASE=os.getenv('WEB_TEST_URL','http://127.0.0.1:5173')
OUT=Path('artifacts/screenshots');OUT.mkdir(parents=True,exist_ok=True)
TEXT=b'Supplier: Browser Example\nNet amount: 12500.00 AED\nTax: 5%\nDelivery: 14 days\nValid until: 2027-12-31'
with sync_playwright() as p:
 launch={'headless':True}
 executable=os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE') or shutil.which('chromium') or shutil.which('chromium-browser')
 if executable:launch['executable_path']=executable
 if os.getenv('NAWA_BROWSER_NO_SANDBOX')=='true' or hasattr(os,'getuid') and os.getuid()==0:launch['args']=['--no-sandbox']
 browser=p.chromium.launch(**launch)
 page=browser.new_page(viewport={'width':1440,'height':1080});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(BASE);page.get_by_role('button',name='Enter workspace',exact=True).click()
 page.get_by_role('heading',name='Your operations, in focus.').wait_for()
 page.goto(BASE+'/documents');page.get_by_role('button',name='Upload document',exact=True).click()
 name='version-test-'+uuid4().hex[:6]+'.txt'
 page.get_by_label('Choose document file').set_input_files({'name':name,'mimeType':'text/plain','buffer':TEXT})
 page.get_by_role('button',name='Upload',exact=True).click();page.get_by_role('dialog').wait_for(state='hidden')
 page.locator('button.table-case').filter(has_text=name).wait_for()
 page.goto(BASE+'/procurement');page.get_by_role('button',name='New case',exact=True).click()
 outer=page.get_by_role('dialog').first;outer.get_by_role('button',name='Add two quotations').click()
 quote=outer.locator('.quote-form').first
 source=next(o.get_attribute('value') for o in quote.get_by_label('Source document').locator('option').all() if name in o.inner_text())
 quote.get_by_label('Source document').select_option(source)
 quote.get_by_role('button',name='Extract from source',exact=True).click()
 preview=page.get_by_role('dialog').last;preview.get_by_label('Reviewed Net amount',exact=True).fill('12600.00')
 preview.get_by_label('Correction / review reason').fill('Checked the source; analyst correction recorded for testing.')
 preview.get_by_label('I reviewed these values against the source.').check()
 preview.get_by_role('button',name='Apply reviewed draft',exact=True).click()
 expect(quote.get_by_label('Net amount',exact=True)).to_have_value('12600.00')
 outer.get_by_role('button',name='Cancel',exact=True).click()
 page.goto(BASE+'/documents');page.locator('button.table-case').filter(has_text=name).click()
 dialog=page.get_by_role('dialog');dialog.get_by_role('button',name='Extraction history',exact=True).click()
 dialog.get_by_text('Checked the source; analyst correction recorded for testing.',exact=True).wait_for()
 assert '12500.00' in dialog.inner_text() and '12600.00' in dialog.inner_text()
 page.screenshot(path=str(OUT/'v050-correction-history.png'),full_page=False)
 dialog.get_by_label('New version file').set_input_files({'name':'updated-source.txt','mimeType':'text/plain','buffer':TEXT.replace(b'12500',b'13000')})
 dialog.get_by_role('button',name='Upload new version',exact=True).click()
 expect(dialog.get_by_label('Source version')).to_have_value('2')
 expect(dialog.locator('.document-detail-heading .badge')).to_have_text('Ready',timeout=30000)
 dialog.get_by_role('button',name='Read source',exact=True).click()
 expect(dialog.locator('.source-pages')).to_contain_text('13000.00')
 dialog.get_by_label('Source version').select_option('1')
 expect(dialog.locator('.source-pages')).to_contain_text('12500.00')
 assert '/versions/1/download' in dialog.get_by_role('link',name='Download source',exact=True).get_attribute('href')
 page.screenshot(path=str(OUT/'v050-historical-source.png'),full_page=False)
 page.set_viewport_size({'width':390,'height':844})
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.screenshot(path=str(OUT/'v050-history-mobile.png'),full_page=False)
 assert not errors,errors
 browser.close();print('PASS: uploaded source, persisted reviewed correction, replacement v2, old v1 pages/download and mobile history')
