---
phase: 18-composite-crime-index
verified: 2026-06-19T21:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 3/5
  gaps_closed:
    - "Gap 1 (CI-05): ResultPanel now reads composite_index[String(COMPOSITE_YEAR)] with COMPOSITE_YEAR=2024 constant — composite section renders correctly in default map view"
    - "Gap 2 (CI-04, CI-08): SOURCES.md:104 and both methodology pages now state '5.0 is a fallback trigger threshold, not a multiplier applied to INE' — code and docs agree"
    - "Gap 3 (CI-02): normalize_metric masks NaN before winsorizing (arr[mask] pattern); new test test_normalize_nan_outlier_clip asserts clip point from real data when NaN+outlier coexist"
  gaps_remaining: []
  regressions: []
---

# Phase 18: Composite Crime Index — Re-Verification Report

**Phase Goal:** Users can see each commune's overall crime exposure as a single 0–100 index score in the map, commune pages, and popup — computed from 7 hardened metrics with exposure adjustment — while every page maintains the editorial constraint that no absolute safety verdict is issued.
**Verified:** 2026-06-19
**Status:** passed
**Re-verification:** Yes — after gap closure (18-06, 18-07, 18-08 + CR-01 fix)

## Summary of Re-Verification

Three gap-closure plans were executed since the initial verification. All three targeted defects are confirmed fixed in the live codebase. The full pipeline test suite (194/194) passes. Advisory concerns from 18-REVIEW.md (WR-01 through WR-04) are documentation-accuracy warnings; none block a CI requirement.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Commune pages show 0–100 score + 5-band label + national/regional rank + mandatory bilingual caveat | VERIFIED | `commune/[slug].astro:221` COMPOSITE_YEAR=2024; score, band, rank, caveat all rendered. Unchanged from initial pass. |
| 2 | Map popup (ResultPanel) renders composite section with score, band label, and ranks when mode=composite | VERIFIED | `ResultPanel.tsx:39-41`: `const COMPOSITE_YEAR = 2024` introduced; line 267 reads `data.composite_index?.[String(COMPOSITE_YEAR)]` — no longer keyed on the mutable `year` state (which was 2025). Guard at line 268 now resolves to a real ci object for all communes that have 2024 data. |
| 3 | Pipeline normalize_metric winsorizes only non-NaN values; NaN+outlier test passes | VERIFIED | `composite_index.py:45-46`: `arr_w[mask] = np.array(winsorize(arr[mask], ...))` — winsorize is called exclusively on the non-NaN subset. `test_normalize_nan_outlier_clip` (test_composite.py:216) asserts non-NaN max == 100.0 and NaN index remains NaN. Test passes. |
| 4 | SII exposure denominator semantics match published methodology: ratio > 5.0 triggers INE fallback (threshold, not multiplier) | VERIFIED | `composite_index.py:90-91`: returns `ine, True` when ratio > SII_CAP_RATIO. `SOURCES.md:104`: "5.0 is a fallback trigger threshold, not a multiplier". `methodology.astro:417-419` and `metodologia.astro:434-436`: same corrected wording. Code and all three docs now agree. |
| 5 | Forbidden-language validator extended; methodology pages correct SPD attribution; @astrojs/check and all validators pass | VERIFIED | `methodology.astro:116`: "Subsecretaría de Prevención del Delito (SPD)" — CR-01 fixed. `forbidden-language.mjs` contains all 4 new terms. 194/194 pipeline tests pass. |

**Score:** 5/5 truths verified

### Gap Closure Evidence

#### Gap 1 — ResultPanel COMPOSITE_YEAR constant (18-06)

`ResultPanel.tsx` lines 39–41:
```typescript
// This constant mirrors commune/[slug].astro:COMPOSITE_YEAR and must be updated
// when a new index vintage is published.
const COMPOSITE_YEAR = 2024;
```
Line 267: `const ci = data.composite_index?.[String(COMPOSITE_YEAR)];`

Previously keyed on `String(year)` where `year` was initialized to 2025 — always null. Now hardcoded to 2024 matching the commune JSON keys.

#### Gap 2 — SII cap semantics alignment (18-07)

`SOURCES.md:104`: "the metric falls back to the INE resident population as the denominator (5.0 is a fallback trigger threshold, not a multiplier)."

`methodology.astro:417-419`: "when the ratio of SII workers to INE resident population exceeds 5.0, the metric falls back to the INE resident population as the denominator (5.0 is a fallback trigger threshold, not a multiplier applied to INE)."

`metodologia.astro:434-436` (ES): "la métrica recurre a la población residente INE como denominador (5,0 es un umbral de activación del recurso, no un multiplicador aplicado a la población INE)."

All three match `composite_index.py:90-91`: `return ine, True`.

#### Gap 3 — NaN-safe winsorization + test (18-08)

`composite_index.py:36-56`: mask computed before winsorize; `arr_w = np.full_like(arr, np.nan)`; only `arr_w[mask]` is populated from winsorize output. The incorrect comment "scipy masked array handles this" is gone; correct comment at line 43-44 explains the NaN-masking rationale.

`test_composite.py:216-253`: `test_normalize_nan_outlier_clip` constructs a series with both NaN (at index 3) and a Sierra-Gorda-scale outlier (value 9999), asserts NaN output preserved and non-NaN max == 100.0 (clip from real data, not NaN position). Passes.

### Requirements Coverage

| Requirement | Description | Status | Evidence |
|------------|-------------|--------|---------|
| CI-01 | Isolated build_composite_index.py; no CEAD breakage on failure | SATISFIED | Separate entrypoint confirmed; `continue-on-error` in workflow. Unchanged. |
| CI-02 | Winsorization / percentile-rank normalization; NaN-safe; pytest spread assertion | SATISFIED | Gap 3 closed: NaN masking before winsorize; `test_normalize_nan_outlier_clip` passes; spread assertion at test_composite.py:185-204 passes. |
| CI-03 | SPD VHC as M1; CEAD featured_rates.homicidios preserved | SATISFIED | Unchanged from initial pass. |
| CI-04 | SII exposure denominator with documented cap; code/docs agreement | SATISFIED | Gap 2 closed: all three doc surfaces now say "fallback trigger threshold, not a multiplier" matching code behavior. |
| CI-05 | 0–100 integer + 5 bands + national/regional rank in UI (map popup, commune pages) | SATISFIED | Gap 1 closed: ResultPanel COMPOSITE_YEAR=2024 constant; composite block now renders in default map view. Commune pages unchanged (already correct). |
| CI-06 | Mandatory bilingual caveat block on all index-displaying pages | SATISFIED | Unchanged from initial pass. |
| CI-07 | Choropleth toggle: index mode vs per-family rate mode | SATISFIED | Unchanged from initial pass. |
| CI-08 | Methodology pages document formula/normalization/SPD switch/SII caveat; figure-registry zero-orphan | SATISFIED | Gap 2 closed: SII caveat now accurate. CR-01 fixed: SPD expansion now correct on both EN and ES pages. |
| CI-09 | Forbidden-language validator extended; npm run validate green | SATISFIED | Unchanged from initial pass. |
| CI-10 | Schema migration non-breaking; @astrojs/check green; comparator_table.json emitted | SATISFIED | 194/194 pipeline tests pass. Unchanged from initial pass. |

### Advisory Concerns (Non-Blocking)

The following findings from 18-REVIEW.md are noted as advisory. None block a CI requirement — the composite score, ordering, and UI delivery are all correct. They are documentation-accuracy issues and one editorial edge case.

| ID | Concern | Classification | Impact |
|----|---------|---------------|--------|
| WR-01 | normalize_metric scales to [0, 100] but SOURCES.md/methodology pages say [0, 1] | WARNING — doc/code drift | No effect on ordering or user-visible scores; credibility-page accuracy defect |
| WR-02 | Published formula omits absent-metric weight redistribution actually performed | WARNING — doc/code drift | Affects communes missing a metric (e.g. SII-absent communes); formula description incorrect |
| WR-03 | All-absent commune (available_metrics=0) silently scored 0.0 and ranked lowest-crime | WARNING — editorial/correctness risk | CLAUDE.md constraint: no territory should imply "safest" with no-data; low probability in practice |
| WR-04 | available_metrics overloaded as SII data-quality flag, not literal summed-metric count | WARNING — maintainability | Semantic confusion for future maintainers; no user-visible defect |

These four items are candidates for a follow-on documentation-hardening task. They do not affect goal achievement for Phase 18.

### Pipeline Test Results (Spot-Check)

| Suite | Command | Result | Status |
|-------|---------|--------|--------|
| Composite-only | `python -m pytest pipeline/tests/test_composite.py -q` | 9 passed | PASS |
| Full pipeline | `python -m pytest pipeline/tests/ -q` | 194 passed, 12 warnings | PASS |

### Anti-Patterns — Regression Check

No new anti-patterns introduced by the three gap-closure plans. The incorrect comment at `composite_index.py:37` ("scipy masked array handles this") was removed as part of Gap 3 closure.

---

_Verified: 2026-06-19_
_Verifier: Claude (gsd-verifier)_
