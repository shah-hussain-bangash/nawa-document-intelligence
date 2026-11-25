"""Run after starting API + web: python tests/e2e/browser_journey.py.
Uses system Chromium or PLAYWRIGHT_CHROMIUM_EXECUTABLE when supplied.
"""
import os
import shutil
from pathlib import Path
from uuid import uuid4
from playwright.sync_api import sync_playwright

BASE = os.getenv("WEB_TEST_URL", "http://127.0.0.1:5173")
ARTIFACTS = Path("artifacts/screenshots")
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main():
    case_title = f"Browser verification procurement {uuid4().hex[:6]}"
    with sync_playwright() as p:
        executable = os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE") or shutil.which("chromium") or shutil.which("chromium-browser")
        launch = {"headless": True}
        if executable:
            launch["executable_path"] = executable
        if os.getenv("NAWA_BROWSER_NO_SANDBOX") == "true" or hasattr(os, "getuid") and os.getuid() == 0:
            launch["args"] = ["--no-sandbox"]
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 1440, "height": 1120}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE)
        page.get_by_role("button", name="Enter workspace", exact=True).click()
        page.get_by_role("heading", name="Your operations, in focus.").wait_for()
        page.screenshot(path=str(ARTIFACTS/"01-overview-desktop.png"), full_page=True)
        page.get_by_role('button', name='Pending reviews', exact=False).click()
        assert 'status=awaiting_review' in page.url
        page.get_by_label('Sort cases').select_option('budget')
        page.get_by_label('My cases', exact=True).check()
        page.get_by_label('My cases', exact=True).uncheck()
        page.goto(BASE+'/documents')
        page.get_by_label('Processing status').select_option('ready')
        page.get_by_label('Processing status').select_option('all')
        for path, title in [("/procurement", "Procurement"), ("/documents", "Evidence library"), ("/agents", "Agent workflows"), ("/analytics", "Operational intelligence"), ("/service", "Service desk"), ("/security", "Security center"), ("/audit", "Audit trail"), ("/settings", "Workspace preferences")]:
            page.goto(BASE+path)
            page.get_by_role("heading", name=title, exact=True).first.wait_for()
            assert page.locator("main").is_visible(), path
        page.goto(BASE+"/knowledge")
        page.get_by_role("button", name="What does the procurement policy require?", exact=True).click()
        page.locator(".citation-card").first.wait_for()
        assert page.locator(".citation-card").count() > 0
        page.screenshot(path=str(ARTIFACTS/"02-knowledge-citations.png"), full_page=True)
        page.goto(BASE+"/documents")
        page.get_by_role("button", name="Upload document", exact=True).click()
        filename = f"browser-evidence-{uuid4().hex[:6]}.txt"
        page.get_by_label("Choose document file").set_input_files({"name": filename, "mimeType": "text/plain", "buffer": b"Synthetic source for the browser journey. Two quotations and independent human review are required."})
        page.get_by_role("button", name="Upload", exact=True).click()
        page.get_by_role("dialog").wait_for(state="hidden")
        page.locator('button.table-case').filter(has_text=filename).wait_for()
        page.goto(BASE+"/procurement")
        page.get_by_role("button", name="New case", exact=True).click()
        dialog=page.get_by_role("dialog")
        dialog.get_by_label("Title", exact=True).fill(case_title)
        dialog.get_by_label("Budget", exact=True).fill("15000")
        dialog.locator('.evidence-choices input[type="checkbox"]').first.check()
        dialog.get_by_role("button", name="Add two quotations").click()
        for i, section in enumerate(dialog.locator(".quote-form").all()):
            section.get_by_label("Supplier", exact=True).fill(f"UI Supplier {i+1}")
            section.get_by_label("Net amount", exact=True).fill(str(3000+i*500))
            section.get_by_label("Source document", exact=True).select_option(index=i+1)
        dialog.get_by_role("button", name="Create case", exact=True).click()
        page.get_by_role("heading", name=case_title, exact=True).wait_for()
        page.get_by_role("button", name="Run comparison", exact=True).click()
        page.get_by_text("This case is waiting for an independent reviewer.", exact=False).wait_for()
        page.screenshot(path=str(ARTIFACTS/"03-procurement-comparison.png"), full_page=True)
        with page.expect_popup() as popup:
            page.get_by_role('link', name='Print / Save PDF', exact=True).click()
        report = popup.value
        report.get_by_role('heading', name='Procurement evidence report', exact=True).wait_for()
        assert 'SHA-256:' in report.locator('body').inner_text()
        report.pdf(path=str(ARTIFACTS/'procurement-report.pdf'))
        report.close()
        page.get_by_label("Close dialog").click()
        page.get_by_label("Account menu").click()
        page.get_by_role("button", name="Sign out", exact=True).click()
        page.get_by_label("Workspace role").select_option("reviewer")
        page.get_by_role("button", name="Enter workspace", exact=True).click()
        page.get_by_role("heading", name="Your operations, in focus.").wait_for()
        page.goto(BASE+"/procurement")
        page.get_by_role("button", name=case_title, exact=False).first.click()
        page.get_by_label("Decision reason", exact=True).fill("Verified both source-linked quotations and the independent comparison.")
        page.get_by_role("button", name="Approve simulation", exact=True).click()
        page.get_by_role("button", name="Confirm decision", exact=True).click()
        page.get_by_role("heading", name="Simulation approved", exact=True).wait_for()
        page.get_by_label("Close dialog").click()
        page.goto(BASE)
        page.set_viewport_size({"width":390,"height":844})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile horizontal overflow"
        page.screenshot(path=str(ARTIFACTS/"04-overview-mobile.png"), full_page=True)
        page.get_by_label("Open navigation").click()
        page.get_by_role("link", name="Documents", exact=True).click()
        page.get_by_role("heading", name="Evidence library").wait_for()
        assert not page.locator('.sidebar').evaluate("el => el.classList.contains('is-open')")
        page.get_by_label("Switch language").click()
        assert page.locator("html").get_attribute("dir") == "rtl"
        page.screenshot(path=str(ARTIFACTS/"05-arabic-mobile.png"), full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "RTL horizontal overflow"
        assert not errors, errors
        browser.close()
        print("PASS: all pages, cited search, upload, create/run/review, mobile navigation and Arabic RTL; no browser exceptions.")


if __name__ == "__main__":
    main()
