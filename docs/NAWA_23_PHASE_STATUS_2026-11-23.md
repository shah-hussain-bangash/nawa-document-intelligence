# NAWA: 23-phase evidence check

**Snapshot:** 23 November 2026. This describes the public `nawa-document-intelligence` repository, not the separate v0.6.6 workspace. Main was [`e1e902a`](https://github.com/shah-hussain-bangash/nawa-document-intelligence/commit/e1e902ae195c5fb55fd32970c70e33438961d517); the integration draft [#11](https://github.com/shah-hussain-bangash/nawa-document-intelligence/pull/11) was [`a77855d`](https://github.com/shah-hussain-bangash/nawa-document-intelligence/commit/a77855dfa1067cda49190ca6795b525a49132ada). The separate 23-phase roadmap was unavailable at its previously supplied location, so its definitions and acceptance criteria could not be checked.

**Status meanings:** “Synthetic demo on main” means a numbered guide and related code are present on main; it does not certify the phase against the missing roadmap or establish production readiness. “Draft” means unmerged work, with only the described synthetic evidence. “Unknown” means the phase definition or acceptance evidence is unavailable here.

| Phase | Evidence found | Status and boundary |
| --- | --- | --- |
| 1 | No authoritative phase-specific acceptance criteria found. | Unknown. |
| 2 | [Quotation comparison baseline](https://github.com/shah-hussain-bangash/nawa-document-intelligence/blob/e1e902ae195c5fb55fd32970c70e33438961d517/demo/README.md); the Phase 3 guide says it builds on Phase 2. | Synthetic text baseline on main; full Phase 2 criteria unknown. |
| 3 | [Arabic PDF text and optional OCR guide](https://github.com/shah-hussain-bangash/nawa-document-intelligence/blob/e1e902ae195c5fb55fd32970c70e33438961d517/demo/README_PHASE3.md). | Synthetic demo on main; representative Arabic OCR accuracy is not established. |
| 4 | [Permission-filtered BM25 guide](https://github.com/shah-hussain-bangash/nawa-document-intelligence/blob/e1e902ae195c5fb55fd32970c70e33438961d517/demo/README_PHASE4.md). | Synthetic offline demo on main; not production authentication. |
| 5 | [Extractive Q&A guide](https://github.com/shah-hussain-bangash/nawa-document-intelligence/blob/e1e902ae195c5fb55fd32970c70e33438961d517/demo/README_PHASE5.md). | Synthetic demo on main; lexical evidence is not semantic verification. |
| 6 | [Optional generation guide](https://github.com/shah-hussain-bangash/nawa-document-intelligence/blob/e1e902ae195c5fb55fd32970c70e33438961d517/demo/README_PHASE6.md). | Synthetic and opt-in demo on main; the [case study](https://github.com/shah-hussain-bangash/nawa-document-intelligence/blob/e1e902ae195c5fb55fd32970c70e33438961d517/docs/07-case-study/NAWA_CASE_STUDY.md) records a false field/value relationship passing lexical checks. |
| 7 | [Evaluation guide](https://github.com/shah-hussain-bangash/nawa-document-intelligence/blob/e1e902ae195c5fb55fd32970c70e33438961d517/demo/README_PHASE7.md). | Scripted synthetic evaluation on main; independent bilingual evaluation remains open. |
| 8 | [Human review guide](https://github.com/shah-hussain-bangash/nawa-document-intelligence/blob/e1e902ae195c5fb55fd32970c70e33438961d517/demo/README_PHASE8.md). | Offline synthetic review on main; not a production audit service. |
| 9 | [Local dashboard guide](https://github.com/shah-hussain-bangash/nawa-document-intelligence/blob/e1e902ae195c5fb55fd32970c70e33438961d517/demo/README_PHASE9.md). | Synthetic local dashboard on main; not authenticated multiuser deployment. |
| 10 | [Docker demo guide](https://github.com/shah-hussain-bangash/nawa-document-intelligence/blob/e1e902ae195c5fb55fd32970c70e33438961d517/demo/README_PHASE10.md). | Synthetic local Docker demo on main; [smoke check passed](https://github.com/shah-hussain-bangash/nawa-document-intelligence/actions/runs/44885327974). |
| 11 | [PostgreSQL guide](https://github.com/shah-hussain-bangash/nawa-document-intelligence/blob/e1e902ae195c5fb55fd32970c70e33438961d517/demo/README_PHASE11.md). | Opt-in synthetic persistence on main; [hosted checks passed](https://github.com/shah-hussain-bangash/nawa-document-intelligence/actions/runs/44885327975). Existing-data migration and production recovery are not established. |
| 12 | [Identity draft #2](https://github.com/shah-hussain-bangash/nawa-document-intelligence/pull/2). | Draft. Synthetic browser identity was also exercised in downstream tests; company-trusted certificates and production identity review remain open. |
| 13 | [Intake draft #3](https://github.com/shah-hussain-bangash/nawa-document-intelligence/pull/3). | Draft. Synthetic intake and recovery evidence exist; review of migration and coordinated recovery remains open. |
| 14 | [Retrieval draft #4](https://github.com/shah-hussain-bangash/nawa-document-intelligence/pull/4). | Draft. Independent retrieval and answer evaluation, authorization and source lifecycle review remain open. |
| 15 | [OCR draft #5](https://github.com/shah-hussain-bangash/nawa-document-intelligence/pull/5). | Draft. OCR remains review-only; an independently reviewed Arabic/English financial-field evaluation remains open. |
| 16 | Roadmap definition and acceptance evidence not available. | Unknown. |
| 17 | Roadmap definition and acceptance evidence not available. | Unknown. |
| 18 | Roadmap definition and acceptance evidence not available. | Unknown. |
| 19 | Roadmap definition and acceptance evidence not available. | Unknown. |
| 20 | Roadmap definition and acceptance evidence not available. | Unknown. |
| 21 | Roadmap definition and acceptance evidence not available. | Unknown. |
| 22 | Roadmap definition and acceptance evidence not available. | Unknown. |
| 23 | Roadmap definition and acceptance evidence not available. | Unknown. |

## Current integration evidence

[Draft #11 at `a77855d`](https://github.com/shah-hussain-bangash/nawa-document-intelligence/pull/11) combines downstream synthetic experiments. Its [synthetic workflow](https://github.com/shah-hussain-bangash/nawa-document-intelligence/actions/runs/45120226579) passed browser and PostgreSQL jobs, but this does not merge earlier drafts or validate existing data. The exact-line structured field check is offline and review-only; the existing generated-answer checker is unchanged.

The original v0.6.6 Windows portal has its own previously reported tests and saved records. This repository snapshot does not establish which capabilities or changes are installed there.

## What is needed to finish the requested plan

1. Obtain the original 23-phase roadmap and map each phase's stated acceptance criteria to a current revision and actual evidence.
2. Review the stacked drafts and their overlaps, identity/certificate decisions, migration and recovery design, worker origin, and bilingual evaluation before claiming an integrated release.
3. Record what has been implemented, tested, independently reviewed and deployed as separate outcomes. Agree the release milestone and its remaining UI work from that evidence.

Do not describe all 23 phases as complete, or represent synthetic results as production assurance. No action in this report changes existing `.env` files, uploads, database volumes or the separate v0.6.6 workspace.
