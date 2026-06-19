---
phase: 18
slug: composite-crime-index
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-19
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (Python pipeline) + `@astrojs/check` / `npm run validate` (site) |
| **Config file** | `pipeline/tests/conftest.py` (exists) |
| **Quick run command** | `pytest pipeline/tests/test_composite.py -x` |
| **Full suite command** | `pytest pipeline/tests/ -x` |
| **Estimated runtime** | ~25 seconds (pytest); ~90 seconds with `npm run build && npm run validate` |

---

## Sampling Rate

- **After every task commit:** Run `pytest pipeline/tests/test_composite.py -x` (Python tasks) or `npx astro check` (site tasks)
- **After every plan wave:** Run `pytest pipeline/tests/ -x && cd site && npm run build && npm run validate`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | CI-02 | T-18-01 | Winsorize clips injected outlier; weights sum to 1.00, incivilidades excluded | unit | `python -m pytest pipeline/tests/test_composite.py::test_composite_config_weights_sum_to_one pipeline/tests/test_composite.py::test_composite_config_constants -x` | ❌ W0 | ⬜ pending |
| 18-01-02 | 01 | 1 | CI-03, CI-04 | T-18-02 / T-18-04 | Year-alignment fails loudly off-2024; SII cap → INE fallback (null≠zero) | unit | `python -m pytest pipeline/tests/test_composite.py::test_year_alignment pipeline/tests/test_composite.py::test_sii_cap_logic -x` | ❌ W0 | ⬜ pending |
| 18-01-03 | 01 | 1 | CI-01, CI-02, CI-04 | T-18-03 / T-18-04 | Enriched JSON additive; score roundable int 0-100; featured_rates intact | integration | `python -m pytest pipeline/tests/test_composite.py -x` | ❌ W0 | ⬜ pending |
| 18-02-01 | 02 | 2 | CI-01, CI-10 | T-18-05 / T-18-06 | Single payload owner; ci level 1-5; payload < 30 KB | integration | `python -m pytest pipeline/tests/test_scrape_cead.py -x` | ✅ (exists) | ⬜ pending |
| 18-02-02 | 02 | 2 | CI-01 | T-18-07 | Workflow order scrape→index→payload→commit; index failure does not block CEAD commit (D-11) | unit | `python -m pytest pipeline/tests/test_workflow_order.py -x` | ❌ W0 | ⬜ pending |
| 18-03-01 | 03 | 3 | CI-07 | T-18-09 | ci bounded 1-5; null → dimmed fallback, no out-of-range color index | unit (TS) | `cd site && npx astro check` | ✅ (check in CI) | ⬜ pending |
| 18-03-02 | 03 | 3 | CI-07 | T-18-08 | Composite default mode; neutral palette (not safety ramp); applyStyleMap (no re-mount) | build | `cd site && npx astro check && npm run build` | ✅ (check in CI) | ⬜ pending |
| 18-04-01 | 04 | 4 | CI-05, CI-06 | T-18-11 / T-18-12 | Integer-only score (no toFixed); always-visible bilingual caveat; composite block gated on index mode | unit (TS) | `cd site && npx astro check` | ✅ (check in CI) | ⬜ pending |
| 18-04-02 | 04 | 4 | CI-05, CI-06 | T-18-10 | EN+ES caveat in built HTML; national+regional rank; no absolute verdict | build | `cd site && npx astro check && npm run build` | ✅ (check in CI) | ⬜ pending |
| 18-05-01 | 05 | 5 | CI-09 | T-18-13 | Flags most dangerous/mas peligrosa/mas peligroso/el mas seguro; allows reported/reportado-qualified | build | `cd site && node scripts/validate/forbidden-language.mjs` | ✅ (validator exists) | ⬜ pending |
| 18-05-02 | 05 | 5 | CI-08 | T-18-14 | F13/F14 tokens resolve in SOURCES.md; zero-orphan | build | `cd site && node scripts/validate/figure-registry.mjs` | ✅ (validator exists) | ⬜ pending |
| 18-05-03 | 05 | 5 | CI-08, CI-10 | T-18-15 | All 6 consumers non-breaking; @astrojs/check + full validator suite green | build | `cd site && npm run build && npm run validate` | ✅ (suite exists) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Phase Requirements → Test/Build Map (CI-01..CI-10)

| Req ID | Behavior | Command | Owning Task |
|--------|----------|---------|-------------|
| CI-01 | `build_composite_index.py` exits 0, enriches comunas JSON; isolated payload step | `python -m pytest pipeline/tests/test_composite.py::test_build_composite_index -x` · `python -m pytest pipeline/tests/test_scrape_cead.py -x` | 18-01-03, 18-02-01 |
| CI-02 | 25th percentile of scores > 10% of max (winsorize guard) | `python -m pytest pipeline/tests/test_composite.py::test_composite_distribution -x` | 18-01-03 |
| CI-03 | SPD year == 2024; CEAD featured_rates.homicidios unchanged | `python -m pytest pipeline/tests/test_composite.py::test_year_alignment -x` | 18-01-02 |
| CI-04 | SII cap: Providencia → INE denom; Las Condes → SII denom | `python -m pytest pipeline/tests/test_composite.py::test_sii_cap_logic -x` | 18-01-02 |
| CI-05 | Integer score; band label; national + regional rank in popup/panel/pages | `python -m pytest pipeline/tests/test_composite.py::test_output_schema -x` · `cd site && npx astro check && npm run build` | 18-01-03, 18-04-01, 18-04-02 |
| CI-06 | Bilingual caveat renders in EN+ES built HTML | `cd site && npm run build && node scripts/validate/forbidden-language.mjs` | 18-04-02, 18-05-01 |
| CI-07 | `buildStyleMapFromCompositeIndex()` 346 entries; default mode composite | `cd site && npx astro check && npm run build` | 18-03-01, 18-03-02 |
| CI-08 | figure-registry passes (F13, F14 registered, zero-orphan) | `cd site && node scripts/validate/figure-registry.mjs` | 18-05-02, 18-05-03 |
| CI-09 | Unqualified superlatives flagged; qualified phrasing allowed | `cd site && node scripts/validate/forbidden-language.mjs` | 18-05-01 |
| CI-10 | @astrojs/check passes with new TS types; all validators green | `cd site && npm run build && npm run validate` | 18-05-03 |

---

## Wave 0 Requirements

Wave 0 runs at execution start (before Task 1 GREEN). These artifacts MUST exist before any behavioral test can pass:

- [ ] `pipeline/tests/test_composite.py` — stubs for CI-01..CI-05, CI-09 (created in 18-01-01; four behavioral stubs land RED, GREEN by 18-01-03)
- [ ] `pipeline/composite_config.py` — METRIC_WEIGHTS, REFERENCE_YEAR, WINSORIZE_LIMITS, SII_CAP_RATIO, TOTAL_COMMUNES (created in 18-01-01)
- [ ] `pipeline/composite_index.py` — normalize_metric, get_exposure_denominator, assert_year_alignment, compute_composite (created in 18-01-02)
- [ ] `pipeline/build_composite_index.py` — entrypoint with year-alignment assertion (created in 18-01-03)
- [ ] `pipeline/tests/conftest.py` — shared fixtures (already exists; reuse record-builder shape from test_scrape_cead.py)
- [ ] `pipeline/tests/test_workflow_order.py` — workflow-ordering test (created in 18-02-02)

*pytest framework already installed (conftest.py present). No framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Composite weight vector (C-02) is correct policy | D-02/C-02 | Editorial/policy judgement, not testable | Human reviews `composite_config.py` against C-02 at the Plan 01 checkpoint (autonomous: false) |
| Choropleth color reads as neutral, not safe/dangerous verdict | CI-07/D-07 | Visual perception | Open map in composite mode; confirm palette is the neutral incidence ramp, caveat visible |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (test_composite.py, composite_config.py, composite_index.py, build_composite_index.py, test_workflow_order.py)
- [x] No watch-mode flags (all commands single-run with `-x`)
- [ ] Feedback latency < 90s (verified at first wave execution)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-19 (plan complete; `wave_0_complete: false` until execution creates the Wave 0 test/config files)
