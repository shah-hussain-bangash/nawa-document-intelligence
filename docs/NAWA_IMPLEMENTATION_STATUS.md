# NAWA implementation and evidence status

Checked 20 November 2026. This register identifies synthetic development evidence, not production assurance. GitHub pull requests and runs may change; check their current status before relying on it.

## Main branch

| Area | Evidence at main `823565f7c44c15b07719b91670fe8bbfb8d96521` | Boundary |
| --- | --- | --- |
| Text comparison | [Core source](../demo/nawa_demo/core.py), [samples](../demo/samples/) and [tests](../demo/tests/test_core.py). On Windows, eight core tests and both English/Arabic and invalid-VAT CLI examples were run on 20 November 2026 against the files at this revision. | Synthetic fixed-format text; price ranking is not an award decision. |
| Dashboard | [Local dashboard guide](../demo/README_PHASE9.md); [Docker guide](../demo/README_PHASE10.md). | Single-user synthetic demo; no production authentication. |
| Database and recovery | [Phase 11 guide](../demo/README_PHASE11.md); [main demo/PostgreSQL CI](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/actions/runs/43840038065); [Docker smoke CI](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/actions/runs/43840038120). | Optional development storage. Manual synthetic backup/restore was reported; original uploads are not retained and this is not an automated recovery service. |

## Stacked draft work

The following pull requests are drafts. They are based on each other, not all on main, and their checks apply to the tested revision. A passing draft check does not mean the feature is merged or production-ready.

| Draft | Current scope and outstanding work |
| --- | --- |
| [#2 Identity](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/pull/2) | Local synthetic OIDC/session prototype. A browser-driven test on the stacked PR #5 revision [`9b70fa5`](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/commit/9b70fa549805c8754a0d9a95377a62e6a4444364) passed with a disposable CI-only CA and separate analyst/reviewer contexts; see [the synthetic demo run](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/actions/runs/44680650579). Company-trusted local/staging browser sign-in and production session/tenant design remain open. |
| [#3 Intake](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/pull/3) | Synthetic intake and worker prototype. The stacked CI test used browser login, intake, reviewer-asserted correction and approval. Comparison still reads original quotation values rather than approved corrections; correction evidence text is a reviewer assertion. Migration and recovery review remain open. |
| [#4 Retrieval](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/pull/4) | Offline retrieval and grounding experiments. Authenticated retrieval, source/version rechecks, abstention and independent evaluation remain open; experimental claim checks are not an approval control. |
| [#5 OCR](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/pull/5) | Review-only OCR experiments and an intake guard. On one saved synthetic sample the English baseline matched 6/6 fields and Arabic matched 2/6; neither is a representative accuracy estimate. At [`b306837`](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/commit/b30683795278bb635cf2a6a62579086826a7e2cd), the [Phase 15 synthetic checks](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/actions/runs/44532629531) passed. A reviewed bilingual holdout, financial-field gates and independently established worker origin remain open. |
| [#7 Review-aware comparison](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/pull/7) | Stacked on #5. At [`3b8e381`](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/commit/3b8e381ba1721dfaa81a07305ddb91652cfb64b5), [synthetic browser and database checks](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/actions/runs/44683560121) passed for sign-in, correction, approval and comparison. An opt-in QA policy checks cited lines against retained hash-checked TXT sources; the default still accepts reviewer assertions. This does not prove a correction is right, and the draft has not been merged. |

## Priority open work

1. Validate local/staging identity with an approved certificate and separate users, including access revocation. The CI-only browser test covers synthetic sign-in and logout, not company trust or staging.
2. Review the draft comparison fix and TXT source-checking policy; PDF and unretained sources remain unsupported in the strict mode. Review PR dependencies and migrations and demonstrate isolated recovery. Keep existing databases and uploads unchanged during testing.
3. Keep OCR and generated claims review-only. Create independently reviewed Arabic/English evaluation data; measure financial-field failures, retrieval authorization, stale sources and abstention before considering integration.
4. Record an explicit trusted worker-origin design, staged deployment boundary, secret handling, privacy and recovery decisions before any production claim.

Do not publish sensitive inputs, credentials, reviewer data or personal identification in the public repository. This register does not assert that cloud deployments or all project phases are complete.
