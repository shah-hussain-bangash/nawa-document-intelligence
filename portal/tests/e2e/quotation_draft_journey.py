import os
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE = os.getenv("WEB_TEST_URL", "http://127.0.0.1:5173")
Path("artifacts/screenshots").mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
 launch = {"headless": True}
 executable = os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE') or shutil.which('chromium') or shutil.which('chromium-browser')
 if executable: launch['executable_path'] = executable
 if os.getenv('NAWA_BROWSER_NO_SANDBOX') == 'true' or hasattr(os, 'getuid') and os.getuid() == 0: launch['args'] = ['--no-sandbox']
 b=p.chromium.launch(**launch)
 page=b.new_page(viewport={'width':1440,'height':1080})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(BASE)
 page.get_by_role('button',name='Enter workspace',exact=True).click()
 page.get_by_role('heading',name='Your operations, in focus.').wait_for()
 page.get_by_role('button',name='New case',exact=True).click()
 outer=page.get_by_role('dialog').first
 outer.get_by_role('button',name='Add two quotations',exact=True).click()
 quote=outer.locator('.quote-form').first
 options=quote.get_by_label('Source document').locator('option').all()
 source=next(o.get_attribute('value') for o in options if '·' in o.inner_text())
 quote.get_by_label('Source document').select_option(source)
 quote.get_by_role('button',name='Extract from source',exact=True).click()
 preview=page.get_by_role('dialog').last
 preview.get_by_role('heading',name='Review extracted quotation',exact=True).wait_for()
 assert preview.locator('blockquote').count()>=6
 assert preview.get_by_role('button',name='Apply reviewed draft').is_disabled()
 page.screenshot(path='artifacts/screenshots/extraction-reviewed-draft.png',full_page=True)
 preview.get_by_label('Correction / review reason').fill('Checked the source passages and confirmed the draft values.')
 preview.get_by_label('I reviewed these values against the source.').check()
 preview.get_by_role('button',name='Apply reviewed draft',exact=True).click()
 assert quote.get_by_label('Supplier',exact=True).input_value()
 assert quote.get_by_label('Net amount',exact=True).input_value()
 assert quote.get_by_label('Currency',exact=True).input_value()=='AED'
 assert quote.get_by_label('Tax percentage',exact=True).input_value()=='5.00'
 assert quote.get_by_label('Valid until',exact=True).input_value()
 # Closing nested review is not allowed to submit the underlying case form.
 quote.get_by_role('button',name='Extract from source',exact=True).click()
 preview=page.get_by_role('dialog').last
 preview.get_by_label('Close dialog').click()
 assert page.get_by_role('dialog').count()==1
 page.set_viewport_size({'width':390,'height':844})
 quote.get_by_role('button',name='Extract from source',exact=True).click()
 preview=page.get_by_role('dialog').last
 preview.get_by_role('heading',name='Review extracted quotation').wait_for()
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.screenshot(path='artifacts/screenshots/extraction-mobile.png',full_page=True)
 preview.get_by_label('Close dialog').click()
 # A policy has no labelled quote fields: inherited defaults must be cleared.
 policy = next(o.get_attribute('value') for o in quote.get_by_label('Source document').locator('option').all() if 'Procurement operating framework' in o.inner_text())
 quote.get_by_label('Source document').select_option(policy)
 quote.get_by_role('button',name='Extract from source',exact=True).click()
 preview=page.get_by_role('dialog').last
 preview.get_by_role('heading',name='Review extracted quotation').wait_for()
 preview.get_by_label('Correction / review reason').fill('Checked the source passages and confirmed the draft values.')
 preview.get_by_label('I reviewed these values against the source.').check()
 preview.get_by_role('button',name='Apply reviewed draft',exact=True).click()
 for label in ['Supplier','Net amount','Currency','Tax percentage','Delivery days','Valid until']:
  assert quote.get_by_label(label,exact=True).input_value() == '', label
 assert not errors,errors
 b.close();print('PASS: extraction passages, review gate, apply, unknown fields clear defaults, no accidental submit, mobile')
