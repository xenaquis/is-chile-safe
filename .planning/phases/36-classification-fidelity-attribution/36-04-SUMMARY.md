---
phase: 36-classification-fidelity-attribution
plan: 04
subsystem: news-pipeline
tags: [fidelity, kinship-guard, editorial-filter, FID-01, FID-06, FID-07, G-28, G-29, R-13, R-14, R-16, R-19]
requires:
  - phase: 36-01
    provides: "feeds.source_headline, entity-decoding strip_html, build_incident title_src"
provides:
  - "pipeline/news/fidelity.py: guard_title_en(), kinship_mismatch(), forbidden_term(), FORBIDDEN_TERMS"
  - "scrape_news OK path stores title_src (== title_es) and a guarded title_en; editorial_filter stage; per-row url_rejected/invalid_record"
  - "run summary key `fidelity` = {title_en_fallbacks, editorial_filtered} (dict, never a GITHUB_OUTPUT line)"
  - "backfill: entity-free classify input, title_src + guard + editorial_filter in run_apply, report key `fidelity`, review/audit emit title_src + guarded title_en + title_en_fallback"
  - "store.build_incident: title_src required, legacy title_es removed"
affects: [36-06, 36-07, 36-08, 36-09, 36-10]
tech-stack:
  added: []
  patterns:
    - "longest-first word-bounded alternation (JS lookaround) with consumption, so 'son-in-law' never also counts as 'son'"
    - "commune names from data/cead/meta/index.json masked on both sides before kinship matching"
key-files:
  created:
    - pipeline/news/fidelity.py
    - pipeline/tests/test_fidelity.py
  modified:
    - pipeline/scrape_news.py
    - pipeline/tests/test_scrape_news.py
    - pipeline/backfill_classifier_outage.py
    - pipeline/tests/test_backfill_classifier_outage.py
    - pipeline/news/store.py
    - pipeline/tests/test_store.py
decisions:
  - "Gendered pairs share one kinship concept (hijo/hija -> son|daughter|child): the guard targets relationship-class errors (V-06, G-27), not gender agreement."
  - "EN 'priest', bare 'ex', and 'mother' under padres were dropped from the renderings: in rule (b) they would fire on sacerdote / ex-minister headlines."
  - "matrimonio (couple/spouses/husband/wife) and infantil (child-like satisfier) were added after measuring the legacy pairs; this lowered legacy fallbacks from 8/787 to 3/787."
  - "The backfill report also gains a `fidelity` dict (same counters as the live summary), so the apply report shows how many rows fell back or were filtered."
  - "build_incident without title_src raises TypeError (missing keyword-only); an empty/blank/None title_src raises ValueError."
metrics:
  duration: "~60 min"
  completed: 2026-09-25
  tasks: 2
  files: 8
---

# Phase 36 Plan 04: title_src wiring + title_en guard + editorial filter Summary

For every new incident, live and backfill, the stored Spanish headline is now the outlet's verbatim headline (`title_src`, with `title_es == title_src`). The classifier's `title_es` is never read. `title_en` passes a deterministic kinship guard: on a mismatch or an empty value it falls back to `title_src`. A headline carrying forbidden-language wording is not published. It goes to rejected/ with stage `editorial_filter`. The backfill now classifies on entity-free descriptions (FID-06). In the live OK path, a bad row is rejected on its own and no longer aborts the run.

## Tasks

| Task | Name | Commits | Files |
| ---- | ---- | ------- | ----- |
| 1 | fidelity.py: title_en guard + editorial filter | 8783e2b (RED), 3035d90 (GREEN) | pipeline/news/fidelity.py, pipeline/tests/test_fidelity.py |
| 2 | Wire title_src + guards into scrape_news and the backfill; FID-06 backfill parity; drop legacy title_es | 1bc7bed | scrape_news.py, backfill_classifier_outage.py, store.py and their 3 test files |

## Verification

- Task 1 verify: `pytest pipeline/tests/test_fidelity.py` gave 52 passed, exit 0.
  - Negative control 1: without "yerno" in KINSHIP, the V-06 test fails (son-in-law case and the yerno form case). Reverted.
  - Negative control 2: with commune masking disabled, both the Padre Las Casas and Padre Hurtado tests fail. Reverted.
- Pin: `FORBIDDEN_TERMS` equals the forbidden-language.mjs array (23 terms). CommuneNewsSection.astro's array equals the mjs array (R-19).
- Task 2 verify chain (exact plan command):
  - targeted suites gave 183 passed;
  - both `! grep` guards passed (no `title_es=` and no `result.title_es`/`out.title_es` in scrape_news.py or backfill_classifier_outage.py);
  - full `pytest pipeline` gave **767 passed, 1 skipped, 2 xfailed, pytest rc=0**.
- test_news_health_gate.py is unedited and green.
- Task 2 negative controls:
  - Passing `result.title_en` unguarded makes `test_fid07_kinship_mismatch_falls_back_to_title_src` fail. Reverted.
  - Removing the `IncidentRecord.model_validate` guard makes `test_r14_invalid_record_rejected_per_row` fail: merge_and_write logs "failed validation — skipping write". Reverted.
- Grep over pipeline/ (non-test): the only `build_incident` callers are scrape_news.py:506 and backfill_classifier_outage.py:677. Both pass `title_src=`, and neither passes `title_es=`.
- `git status --porcelain data/` is empty; data/ was only read.
- Line endings are preserved: test_scrape_news.py and test_store.py stay CRLF, the other files stay LF.
- GITHUB_OUTPUT: the pinned test asserts that no `fidelity` line is written. Scalar lines are unchanged.

### Offline fallback measurement (premortem R-13)

The measurement is read-only, uses no LLM, and runs kinship_mismatch(title_es, title_en) over every row of data/incidents/current.json (787 rows at HEAD 434ddbe).

legacy_kinship_fallback_rate: 3/787

The rate is 0.38 %, below the 5 % informative threshold. Before the matrimonio/infantil fix the same measurement gave 8/787. The remaining hits:
- 62e84cb82fa01ae5: "parricidio" rendered as "child murder". The EN adds kinship that the source does not name, so falling back is arguably correct.
- b722565d66abb85e: "su ex" rendered as "his ex-girlfriend". Bare "ex" is not mapped, to avoid ex-ministro false positives.
- cd6f3080080e4ecd: "padre de 2 hijos" rendered as "father of 2". The EN drops "children".

The five measured false positives that were fixed: 4 × "matrimonio" → "couple" and 1 × "explotación sexual infantil" → "child". An intermediate "married" rendering caused a regression on 094afc2257fe81b6 and was removed before the commit.

## Deviations from Plan

**1. [Rule 2 - Correctness] Rendering and satisfier adjustments after measurement**
- **Found during:** the Task 2 offline measurement (the fixes live in Task 1's file)
- **Issue:** The initial KINSHIP table gave 8/787 fallbacks on the legacy pairs. Five of them were false positives (matrimonio → couple, infantil → child). "priest", bare "ex" and "mother" under padres would also fire rule (b) on non-kinship headlines.
- **Fix:** Added the concept `matrimonio` and the child satisfier `infantil`/`infantiles`, and dropped the three risky renderings. Two regression cases were added to the false-positive test (plan scope: "fix false positives inside fidelity.py").
- **Files modified:** pipeline/news/fidelity.py, pipeline/tests/test_fidelity.py
- **Commit:** 3035d90

**2. [Rule 2 - Observability] Backfill report `fidelity` key**
- **Issue:** The plan counts fallbacks and filtered rows only in the live summary. The backfill apply report had no equivalent, so a 36-10 apply could not show how many rows fell back.
- **Fix:** Added `report["fidelity"] = {title_en_fallbacks, editorial_filtered}`. It is additive, and test_apply_cli_writes_report checks key presence only.
- **Commit:** 1bc7bed

**3. Existing test fixtures adapted (not behaviour changes)**
- test_backfill `apply_case`: the n_ok_in_window01 row title became "Asalto en Las Condes - BioBioChile", so the stored headline comes from the row and not from the classifier. The n_dedup_dup00001 title now carries the near-duplicate headline, so the dedup-against-existing case still exercises dedup. A new row, n_editorial00001, covers `editorial_filter`, and `selected` changed from 13 to 14.
- test_review: the hit now comes from the row title (title_src). A new test asserts that the classifier's own title_es is never a review hit.
- test_store: legacy tests were replaced by TypeError/ValueError tests.

No file outside `files_modified` was touched.

## TDD Gate Compliance

- Task 1 has a RED commit (8783e2b, collection failed on the missing module) followed by a GREEN commit (3035d90).
- Task 2 is a single `feat` commit (1bc7bed), with no separate RED commit. Its new tests were written together with the wiring and then proven by the two negative controls above: each fails with the guard removed. This is a warning, not a gap in coverage.

## Threat Model

- T-36-09: the kinship guard falls back to the verbatim title_src, and the fallback is counted in `summary.fidelity.title_en_fallbacks`. V-06 and G-27 are tested in both unit and end-to-end tests.
- T-36-10: `forbidden_term` sends the row to rejected/ with stage `editorial_filter` and marks it seen. The term list is pinned to forbidden-language.mjs and CommuneNewsSection.astro.
- T-36-11: only one dict key was added. GITHUB_OUTPUT scalars are unchanged and the health gate is green without edits.
- No new threat surface.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: pipeline/news/fidelity.py, pipeline/tests/test_fidelity.py, and the 6 modified files
- FOUND commits: 8783e2b, 3035d90, 1bc7bed
