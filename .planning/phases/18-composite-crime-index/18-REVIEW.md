---
phase: 18-composite-crime-index
reviewed: 2026-06-19T18:50:48Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - site/src/components/map/ResultPanel.tsx
  - pipeline/composite_index.py
  - pipeline/tests/test_composite.py
  - site/src/pages/methodology.astro
  - site/src/pages/es/metodologia.astro
  - data/SOURCES.md
findings:
  critical: 1
  warning: 5
  info: 4
  total: 10
status: issues_found
---

# Phase 18: Code Review Report (gap-closure re-review)

**Reviewed:** 2026-06-19T18:50:48Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

This review covers the three phase-18 gap-closure edits: the composite year-key wiring in `ResultPanel.tsx` (18-06), the SII-cap documentation correction in `SOURCES.md` + both methodology pages (18-07), and the NaN-safe winsorization in `composite_index.py` plus its guarding test (18-08).

The three targeted edits themselves are largely correct. The 18-06 `COMPOSITE_YEAR = 2024` constant is consistent with the three `[slug].astro` consumers (`commune/[slug].astro:221`, `es/comuna/[slug].astro:224`) and the `ci` guard at `ResultPanel.tsx:267` is sound. The 18-08 NaN-masking logic in `normalize_metric` is correct and well-covered by `test_normalize_nan_outlier_clip`. The 18-07 SII-cap "fallback trigger, not a multiplier" wording is now consistent across `SOURCES.md:104` and both methodology pages.

However, adversarial cross-referencing surfaced one **factual attribution error that ships to users in both languages**: the methodology pages expand the acronym "SPD" to *"Servicio de Prevención y Participación Ciudadana"* in the homicide source bullet, while every other authoritative reference (SOURCES.md, the same page's composite-index section, `is-chile-safe.astro`) correctly expands SPD as *"Subsecretaría de Prevención del Delito"*. This is a credibility-page error on the exact source attribution the page exists to make trustworthy. Additional warnings concern doc/code drift in the normalization range and formula description, and silent zero-scoring of all-absent communes.

## Critical Issues

### CR-01: SPD acronym wrongly expanded as a non-existent agency on both methodology pages

**File:** `site/src/pages/methodology.astro:116` and `site/src/pages/es/metodologia.astro:111`
**Issue:** The homicide-source bullet attributes the SPD VHC dataset to the *"Servicio de Prevención y Participación Ciudadana (SPD)"*. No such agency owns this dataset. SPD is the **Subsecretaría de Prevención del Delito** — confirmed by:
- `data/SOURCES.md:11, 129, 320` (Subsecretaría de Prevención del Delito)
- the *same* methodology files, composite-index section: `methodology.astro:403` and `metodologia.astro:419` ("Subsecretaría de Prevención del Delito")
- `site/src/pages/is-chile-safe.astro:39` and `site/src/pages/es/index.astro:164`

So within one page the acronym SPD is expanded two different ways, one of them inventing an agency that does not administer the VHC homicide base. This is a factual sourcing error on a credibility/methodology page whose entire purpose is accurate attribution. The CLAUDE.md editorial constraint requires correct source attribution ("siempre atribuir fuentes").
**Fix:**
```astro
<!-- methodology.astro:116 -->
<strong>Homicides:</strong> the <strong>Subsecretaría de Prevención del Delito (SPD)</strong>
<!-- metodologia.astro:111 -->
<strong>Homicidios:</strong> la <strong>Subsecretaría de Prevención del Delito (SPD)</strong>
```
(The SOURCES.md `## SPD — homicide reference snapshot` entry also names "Centro para la Prevención de Homicidios" as the dataset host within SPD — match that phrasing if a longer expansion is desired.)

## Warnings

### WR-01: Normalization scales to [0, 100] but methodology/SOURCES document [0, 1]

**File:** `pipeline/composite_index.py:22-58` vs `data/SOURCES.md:90-91`, `site/src/pages/methodology.astro:393-394`, `site/src/pages/es/metodologia.astro:409-410`
**Issue:** `normalize_metric` rescales each metric to **[0, 100]** (`* 100.0` on line 56; docstring line 23 says "[0, 100]"; `test_composite.py:248` asserts non-NaN max `== 100.0`). The published methodology in all three docs states each metric is "rescaled to [0, 1] via min-max normalization". Because every metric is on the same scale the final composite ordering is unaffected, but the documented formula and the documented output range are both wrong relative to the shipping code — a methodology page that misstates its own normalization is a defect on a credibility page.
**Fix:** Either change the docs to "[0, 100]" (least risk) in `SOURCES.md:90-91`, `methodology.astro:393-394`, and `metodologia.astro:409-410`, or divide by 100 in code if [0,1] is the intended public contract. Pick one and make code + 3 docs agree.

### WR-02: Published formula omits the absent-metric weight redistribution actually performed

**File:** `data/SOURCES.md:71-75`, `site/src/pages/methodology.astro:372-389` vs `pipeline/composite_index.py:119-152`
**Issue:** Both docs state the composite is `sum(w_i * normalized_i)` with no mention of renormalization. `compute_composite` divides the weighted sum by `total_weight` of *present* metrics (line 150: `score = weighted_sum / total_weight`), i.e. it redistributes the weight of absent metrics — which materially changes the score for any commune missing a metric (e.g. the `available_metrics == 6` case in `test_output_schema:462`). The methodology page does not disclose this behavior, so the documented formula and the executed formula diverge for any incomplete commune.
**Fix:** Add a sentence to the composite-index sections of both methodology pages and the SOURCES "Formula" block: "Metrics absent for a commune are excluded and the remaining weights are renormalized to sum to 1, so the score stays on the same scale regardless of how many metrics are available." This matches the behavior asserted in `test_output_schema`.

### WR-03: All-absent commune is silently scored 0.0 and ranked as lowest-crime

**File:** `pipeline/composite_index.py:146-147` (consumed by `pipeline/build_composite_index.py:316-326`)
**Issue:** `compute_composite` returns `(0.0, 0)` when a commune has zero available metrics. Downstream, a 0.0 score sorts to the **bottom of the national ranking** — presented to users as the *lowest-crime* commune — and `_assign_levels` would put it in level 1 ("Very Low"/"Muy Bajo"). A commune with *no data* is thus indistinguishable from the genuinely-safest commune. Given CLAUDE.md's editorial rule against implying a territory is "safe," surfacing a no-data commune as Very Low is a correctness/editorial risk.
**Fix:** Have `compute_composite` signal no-data distinctly (e.g. return `None` score), and in `build_composite_index` skip rank/level assignment for `available_metrics == 0`, omitting the `composite_index` entry so the panel guard (`ResultPanel.tsx:267` `if (!ci) return null`) hides it. Add a test asserting an all-absent commune does not receive level 1.

### WR-04: `available_metrics` is decremented for SII absence but no longer equals the summed-metric count

**File:** `pipeline/build_composite_index.py:262-322`
**Issue:** SII is not one of the 7 `METRIC_WEIGHTS` keys — it only feeds the *denominator* of `spd_homicide_rate` via `get_exposure_denominator`. When SII is absent the code falls back to INE population and still produces a valid `spd_homicide_rate`, so `compute_composite` returns `available = 7`; the post-hoc `available = max(0, available - 1)` (line 321) then yields 6. That happens to satisfy `test_output_schema:462`, but the reported `available_metrics` no longer equals the count of metrics actually summed (still 7) — it is silently overloaded as an SII data-quality flag. A future maintainer could "fix" the apparent off-by-one and break the test/semantics.
**Fix:** Carry a separate `sii_fallback: bool` flag, or add an inline comment at lines 319-321 documenting that `available_metrics` is intentionally penalized for SII absence rather than being a literal summed-metric count.

### WR-05: Level/rate approximation in ResultPanel can contradict the authoritative composite band shown directly below it

**File:** `site/src/components/map/ResultPanel.tsx:217-223`
**Issue:** The panel derives `level` from `rate / maxRate` over the commune's *own* time series (`maxRate = Math.max(...data.series.map(s => s.rate_per_100k), 1)`), i.e. the chip reflects this commune's position within its own history, not the national distribution. The level chip (253-259) and the comparison-bar color (`var(--s${level})`, line 329) can therefore show, e.g., level 5 for a commune at its own historical peak even when nationally it is low — while the composite section right below shows the authoritative national band (`ci.level`, line 269). Two adjacent "level" signals in one panel can contradict each other. The code comment (218-219) admits it is "approximate," but shipping a misleading chip next to the real band is a UX/correctness concern.
**Fix:** When `data.composite_index?.[String(COMPOSITE_YEAR)]` is present, drive the chip and bar color from `ci.level`; otherwise keep the approximation but label it explicitly as relative-to-own-history.

## Info

### IN-01: Stale "NOT wired"/"deferred" status banner in SOURCES.md SII entry

**File:** `data/SOURCES.md:168-169`
**Issue:** The composite-index section (line 66-117) marks the index "Active (Phase 18)" with M7 wired, and the SPD entry header (line 122) was updated to "Active", but the SII snapshot entry still reads "**Status: reference snapshot — NOT wired to the displayed metric.** Deferred to Phase 18" — directly contradicting the now-active composite. Status drift in the canonical provenance registry.
**Fix:** Update the SII entry (line 168-169) to "Active (Phase 18); M7 economic-exposure denominator input," mirroring the SPD entry's correction.

### IN-02: Unused imports in the test module

**File:** `pipeline/tests/test_composite.py:20-25`
**Issue:** `os`, `shutil`, `sys`, `tempfile`, and `Any` are imported but never used (fixtures rely on `pathlib`/`tmp_path`). Dead imports.
**Fix:** Remove the unused imports.

### IN-03: Dead duplicate loaders in the composite entrypoint

**File:** `pipeline/build_composite_index.py:74-124` vs `403-435`
**Issue:** `run_composite_index` calls only the `_from` loader variants (lines 242-244). The non-`_from` originals (`_load_spd_homicide`, `_load_sii_exposure`, `_load_ine_population`, lines 74-124) are never called and duplicate the same logic, risking future divergence of the year-validation guard. (`build_composite_index.py` is outside the listed scope but is the direct consumer of the reviewed `composite_index.py`; flagged for awareness.)
**Fix:** Delete the unused originals (lines 74-124); keep the `_from` variants as the single source of truth.

### IN-04: Magic number 346 duplicated in the front-end constant

**File:** `site/src/components/map/ResultPanel.tsx:36`
**Issue:** `const TOTAL_COMMUNES = 346;` duplicates a figure that also lives in `pipeline/composite_config.py:24` and `data/SOURCES.md`. If the commune count or eligible-ranking denominator changes, the rank string ("#N of 346") could silently misstate the denominator. Low risk (count is stable) but a maintainability trap.
**Fix:** Source the total from the build/payload, or add a cross-file coupling comment as was done for `COMPOSITE_YEAR` at lines 38-41.

---

_Reviewed: 2026-06-19T18:50:48Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
