---
phase: 14
slug: homicide-as-a-first-class-category
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-16
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (pipeline, Python 3.12) + node scripts/validate/*.mjs (build) + `tsc --noEmit` (frontend types) |
| **Config file** | none dedicated — pytest run from repo root with `pipeline` on path; site validators are `node site/scripts/validate/*.mjs` |
| **Quick run command** | `python -m pytest pipeline/tests/ -x` |
| **Full suite command** | `python -m pytest pipeline/tests/ && cd site && npx tsc --noEmit && npm run build && node scripts/validate/map.mjs && node scripts/validate/forbidden-language.mjs` |
| **Estimated runtime** | ~90 seconds (pytest ~5s; build + validators ~60-80s) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest pipeline/tests/ -x` (pipeline tasks) or `cd site && npx tsc --noEmit` (frontend tasks)
- **After every plan wave:** Run the full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 0 | HOM-01 | T-14-01/02 | latin-1 decode, single courtesy-paced request pair to gov server | manual (live) | `python pipeline/experiments/test_subgroup101.py` (human-observed) | ❌ W0 creates | ⬜ pending |
| 14-01-02 | 01 | 0 | HOM-01 | T-14-01 | trimmed static fixtures, no live re-fetch | unit | fixture-presence check (verify block) | ❌ W0 creates | ⬜ pending |
| 14-01-03 | 01 | 0 | HOM-01 | — | RED scaffold asserts homicide keys | unit (RED) | `python -m pytest pipeline/tests/test_scrape_cead.py -q` | ❌ W0 creates | ⬜ pending |
| 14-02-01 | 02 | 1 | HOM-01 | T-14-03 | parametric medida + confirmed subgroup param | unit | `python -m pytest pipeline/tests/test_schema.py -q` + import check | ✅ | ⬜ pending |
| 14-02-02 | 02 | 1 | HOM-01 | T-14-03/04 | null-vs-0 invariant, type-validated entries | unit | `python -m pytest pipeline/tests/test_scrape_cead.py pipeline/tests/test_normalizer.py pipeline/tests/test_output.py -q` | ✅ (14-01 GREEN) | ⬜ pending |
| 14-02-03 | 02 | 1 | HOM-01 | T-14-04/06 | budget guard, courtesy delays preserved | integration | data-presence + 30KB assertion (verify block) | ✅ | ⬜ pending |
| 14-03-01 | 03 | 2 | HOM-01 | T-14-07 | build fails if homicide data missing | build validator | `node site/scripts/validate/map.mjs` | ✅ | ⬜ pending |
| 14-03-02 | 03 | 2 | HOM-01 | T-14-07 | public mirror carries homicide data | build validator | `node site/scripts/validate/map.mjs` (no FAIL) | ✅ | ⬜ pending |
| 14-04-01 | 04 | 3 | HOM-01 | T-14-09 | `?? 0` degrade, independent quantile scale | type check | `cd site && npx tsc --noEmit` | ✅ | ⬜ pending |
| 14-04-02 | 04 | 3 | HOM-01 | T-14-10 | sober CEAD-cited bilingual copy | type check | `cd site && npx tsc --noEmit` + homicidios-present grep | ✅ | ⬜ pending |
| 14-05-01 | 05 | 4 | HOM-01 | — | honest tooltip, familyIndex null sentinel | type check | `cd site && npx tsc --noEmit` + chip-present grep | ✅ | ⬜ pending |
| 14-05-02 | 05 | 4 | HOM-01 | T-14-11 | `?? 0` degrade, exclusive selection | type check | `cd site && npx tsc --noEmit` + crimeIsHomicide grep | ✅ | ⬜ pending |
| 14-06-01 | 06 | 5 | HOM-02 | T-14-13 | `!== undefined` 0-vs-missing, no family regression | type check | `cd site && npx tsc --noEmit` + EN/ES copy grep | ✅ | ⬜ pending |
| 14-06-02 | 06 | 5 | HOM-02 | T-14-14 | forbidden-language gate (no peligroso/seguro) | build validator | `cd site && npm run build && node scripts/validate/map.mjs && node scripts/validate/forbidden-language.mjs` | ✅ | ⬜ pending |
| 14-06-03 | 06 | 5 | HOM-02 | — | visual/E2E homicide layer + panel + zero-state | manual (browser) | human-verify checkpoint | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pipeline/experiments/test_subgroup101.py` — live runtime experiment confirming the subgroup-101 POST param + rate/count behavior (14-01 Task 1)
- [ ] `pipeline/tests/fixtures/cead_subgroup101_rate_sample.html` + `_count_sample.html` — captured offline fixtures for parser tests (14-01 Task 2)
- [ ] `pipeline/tests/test_scrape_cead.py` — RED scaffold for homicide_rate/homicide_count keys + 30KB budget; turned GREEN by 14-02 (14-01 Task 3)

*Existing infrastructure (pytest, node validators, tsc) covers all other phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live CEAD subgroup-101 param confirmation | HOM-01 | Requires a live network call to the CEAD government server; result must be observed | Run `python pipeline/experiments/test_subgroup101.py`; confirm HTTP 200, commune rows, plausible rate/count ranges; record working param (14-01 Task 1) |
| Homicide chip + independent choropleth + panel figure render | HOM-01/HOM-02 | Visual/interactive map behavior (Leaflet recolor, panel render, zero-state copy) not assertable headlessly | Run dev server, follow 14-06 Task 3 how-to-verify steps across /map/ and /es/mapa/ |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (the two live/visual tasks are explicit manual-only with human-check)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (test_scrape_cead.py + fixtures created in 14-01)
- [x] No watch-mode flags
- [x] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-16
