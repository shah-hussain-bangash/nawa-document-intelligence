# v0.3 — Navy & Gold UI refinement

This release follows the user's supplied navy/gold visual reference. The sidebar
uses #0A1425, gold accents #C7A465, the main surface white #FFFFFF, and text navy
#12243F / slate #64738A. The screenshot reference is compressed, so these are
visually matched design values, not a claim of exact source-image sampling.

## Design delivered

- Deep navy sidebar and login panel, muted gold active navigation and accents.
- White workspace with a locally authored, softly blurred UAE flag background.
- White hero with UAE flag artwork and a legible foreground gradient.
- Original gold falcon-inspired SVG project mark with seven points and a small
  UAE flag detail. It is not an official national emblem or government logo.
- Consistent logo/favicon, navy buttons, gold details, navy/gold charts, clearer
  metadata and higher-contrast status labels; responsive English/Arabic layouts.
- Existing procurement/evidence/review workflows preserved. This increment is
  focused on presentation, following the user's requested order.

No external font, stock photo or background service is needed. Logo and flag
artwork are local SVGs. Decorative flag layers are non-interactive and omitted
from the accessibility tree; interface text stays outside blurred layers.

## Government reference research limitations

Attempted direct reads of https://u.ae/en, https://designsystem.gov.ae/,
https://www.tamm.abudhabi/ and https://www.digitaldubai.ae/ from the managed
workspace. All were blocked by the network proxy (CONNECT 403 Forbidden).
No live government-site inspection or exhaustive search is claimed. The supplied
reference image, original artwork and general enterprise usability principles
informed this design. Revisit official design-system guidance when access exists.

## Verified

TypeScript/production build and Prettier passed. Chromium's existing journey
passed all ten routes, cited query, upload, case creation/comparison/independent
review, printable report/PDF, mobile navigation and Arabic RTL without browser
exceptions. Additional checks verified logo/flag loading, exact CSS navy/white
values, login button, and no horizontal overflow at 390/768/1024/1440/1920px.
Six key text combinations passed >=4.5:1 contrast; this is not a full accessibility
audit. Palette checks and screenshots are from Linux Chromium, not native Windows.

## Small UI-only update for existing v0.2 installations

1. Stop your existing launcher with Ctrl+C.
2. Back up your `apps/web` folder.
3. Download `UAE-Sovereign-Agentic-AI-UI-Navy-Gold-v0.3.0.zip`.
4. Extract the ZIP's **apps** folder INTO the existing **nawa-workspace** folder.
   Merge `apps` and replace the included frontend files. Do not nest it inside
   another `nawa-workspace` folder. No backend, `.env` or `.data` is included.
5. Run `py -3.12 nawa.py run --auto-ports` and open the printed READY URL.
6. Refresh with Ctrl+Shift+R. Confirm the sidebar is navy and the logo is gold.

The frontend dependency versions are identical to v0.2; existing dependencies can
be reused for this patch. Only root frontend package version metadata changes.
The patch does not change the backend's reported version. The full source ZIP
reports v0.3 throughout. New installations use the full source ZIP and run setup.
