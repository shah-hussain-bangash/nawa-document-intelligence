# Synthetic CI: explaining the skipped tests

This evidence is specific to integration draft commit [`91106b0`](https://github.com/shah-hussain-bangash/nawa-document-intelligence/commit/91106b023f58440a5d0de0e122947d263d1f8040) and [workflow run 45130219409](https://github.com/shah-hussain-bangash/nawa-document-intelligence/actions/runs/45130219409). It does not establish production readiness or the status of later commits.

The general Linux job ran 368 tests and reported 45 skipped. Comparing each skipped unittest identity against successful results in other jobs in the **same run** found:

| Reason skipped in general job | Count | Where those same tests passed |
| --- | ---: | --- |
| PostgreSQL integration not configured | 12 | [PostgreSQL integration job](https://github.com/shah-hussain-bangash/nawa-document-intelligence/actions/runs/45130219409/job/137543768495) |
| Isolated PostgreSQL test not configured | 32 | [Phase 13 PostgreSQL job](https://github.com/shah-hussain-bangash/nawa-document-intelligence/actions/runs/45130219409/job/137543768277) |
| Windows job object only | 1 | [Windows synthetic intake job](https://github.com/shah-hussain-bangash/nawa-document-intelligence/actions/runs/45130219409/job/137543768397) |

The [machine-readable mapping](ci-skip-coverage-2026-11-23.json) records the 45 test identities, skip reasons and matching jobs. The separate jobs have their own test counts and skips; do not add them as if every invocation were a distinct test. The Windows job also skips tests that are specific to Linux.

One passing PostgreSQL test deliberately **demonstrates a remaining recovery risk**: a stale database restore can revive an unobserved session. Its `ok` result means the test reproduced that behavior, not that recovery is safe. Likewise, the browser job uses disposable synthetic identity and certificate fixtures; it does not prove company certificate trust or a production deployment. OCR accuracy, independent bilingual review, distributed identity and coordinated recovery remain open.
