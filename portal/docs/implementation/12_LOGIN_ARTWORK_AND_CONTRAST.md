# v0.3.1 — Login artwork and clearer text

Replaces the abstract login orbit with an original AI-created UAE architectural
scene inspired by Sheikh Zayed Grand Mosque. This is artistic imagery, not a
photographic record of the real skyline. Caption and alt text identify it as
artwork. PNG is bundled locally at `apps/web/public/uae-login-architecture.png`;
no external image service or credential is needed to display it.

Mobile login includes its own compact image and logo above the form. The old
mobile `nawa.` pseudo-heading is removed. The navy/gold/white system is preserved.

Contrast changes: near-white sidebar navigation; light-gold sidebar section
headings; darker sandbox notice and workspace section headings; brighter login
copy and footer. Text is separate from the artwork and blurred flag background.

## Verification

TypeScript/production build and Prettier passed. Existing Chromium journey passed
all ten routes, cited search, upload, comparison, independent review, report PDF,
mobile navigation and Arabic RTL without browser exceptions.

Targeted checks passed desktop/mobile image loading and no horizontal overflow at
390/768/1024/1440/1920px. Measured contrast of 10 selected rendered text pairs was
>=4.5:1. Sidebar links: 16.40:1; sidebar section headings: 11.04:1; sandbox strong
text: 11.10:1; sandbox explanatory text: 9.00:1; workspace eyebrow: 7.25:1.
Measurements use the solid backing colours; this is not a complete accessibility
audit or native Windows execution claim.

## Apply UI-only ZIP to v0.2/v0.3

1. Stop the running app with Ctrl+C.
2. Back up your `apps/web` folder.
3. Extract the ZIP's **apps** folder into your existing **nawa-workspace** folder.
   Merge folders and replace the included files. The ZIP includes all cumulative
   navy/gold UI files plus the new login artwork.
4. Run `py -3.12 nawa.py run --auto-ports`.
5. Open the READY URL and press Ctrl+Shift+R.

No reinstall is required: frontend dependency versions are unchanged. No backend,
`.env`, database or `.data` files are included in the UI-only ZIP. The backend
keeps its existing version when only this UI update is applied. Full source
v0.3.1 is also available for new installations, which run setup first.
