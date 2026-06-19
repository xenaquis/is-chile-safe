---
phase: 18-composite-crime-index
reviewed: 2026-06-19T00:00:00Z
depth: standard
files_reviewed: 23
files_reviewed_list:
  - .github/workflows/cead-scraper.yml
  - data/SOURCES.md
  - pipeline/build_composite_index.py
  - pipeline/build_map_payload.py
  - pipeline/composite_config.py
  - pipeline/composite_index.py
  - pipeline/requirements.txt
  - pipeline/scrape_cead.py
  - pipeline/tests/test_composite.py
  - pipeline/tests/test_scrape_cead.py
  - pipeline/tests/test_workflow_order.py
  - site/scripts/validate/figure-registry.mjs
  - site/scripts/validate/forbidden-language.mjs
  - site/src/components/map/ChoroplethLayer.ts
  - site/src/components/map/Legend.tsx
  - site/src/components/map/MapIsland.tsx
  - site/src/components/map/ResultPanel.tsx
  - site/src/components/map/map.css
  - site/src/config/i18n.ts
  - site/src/pages/commune/[slug].astro
  - site/src/pages/es/comuna/[slug].astro
  - site/src/pages/es/metodologia.astro
  - site/src/pages/methodology.astro
findings:
  critical: 3
  warning: 8
  info: 5
  total: 16
status: issues_found
---

# Phase 18: Code Review Report

**Reviewed:** 2026-06-19
**Depth:** standard
**Files Reviewed:** 23
**Status:** issues_found

## Summary

Reviewed the composite crime-exposure index implementation: the pure-compute module, the entrypoint, the map-payload integration, the workflow wiring, the frontend choropleth/panel surfaces, and the methodology pages. The code is well-documented and TDD-backed, but the adversarial pass surfaced three blocking defects and several quality issues.

The most serious problems are correctness defects in the composite distribution mode of the live map (the default `year` state is 2025 but the composite index is only computed for the 2024 reference year, so the default map view degrades every commune to the null/level-3 fallback), a contradiction between the SII "cap" the code implements (INE fallback) and what every methodology page and SOURCES.md tells users (clamp to 5.0 × population), and a NaN-handling assumption in `normalize_metric` that is not exercised by any test and is fragile across scipy versions.

## Critical Issues

### CR-01: Default map year (2025) never has composite-index data — index mode is broken on load

**File:** `site/src/components/map/MapIsland.tsx:96`, `site/src/components/map/MapIsland.tsx:243-294`
**Issue:** The map mounts in `mode='composite'` (line 105) with `year` initialized to `2025` (line 96). The composite index is computed and persisted **only** for `REFERENCE_YEAR = 2024` (`composite_config.py:15`, `build_composite_index.py:365`). The map-payload `ci` field is read from `composite_index[str(REFERENCE_YEAR)]` (`build_map_payload.py:154-159`), so `map-payload-2025.json` will contain **no `ci` values**. The year-filter effect (line 251) fetches `map-payload-${year}.json` = `map-payload-2025.json` and rebuilds the composite style map from `payload.comunas` whose `ci` is null, so `buildStyleMapFromCompositeIndex` (`ChoroplethLayer.ts:148-162`) drives **every commune** to the level-3 grey fallback with 0.25 opacity. The default landing view of the new feature is therefore entirely greyed-out. The ResultPanel composite section (`ResultPanel.tsx:261-262`) is also gated on `data.composite_index?.[String(year)]` with `year=2025`, so the panel composite block never renders in the default state either.
**Fix:** Decouple the composite layer's data year from the user-facing `year` selector. Either always source `ci` from the `REFERENCE_YEAR` payload when `mode==='composite'`, or initialize the composite read to 2024:
```ts
// In buildStyleMapFromCompositeIndex consumers and ResultPanel:
const COMPOSITE_YEAR = 2024; // ci is only computed for REFERENCE_YEAR
const ci = data.composite_index?.[String(COMPOSITE_YEAR)];
// In MapIsland, when mode==='composite' use the 2024 payload's ci, not map-payload-${year}.
```
Note the static commune pages already hardcode `COMPOSITE_YEAR = 2024` (`commune/[slug].astro:221`), confirming the live map's use of `year` is the inconsistency.

### CR-02: SII "cap" implementation contradicts the published methodology (silent denominator inflation)

**File:** `pipeline/composite_index.py:82-85`, `data/SOURCES.md:104`, `site/src/pages/methodology.astro:417`, `site/src/pages/es/metodologia.astro:434`
**Issue:** Both methodology pages and SOURCES.md state the SII metric "is capped at 5.0 × the commune's INE resident population" / "value clamped to `cap 5.0`". The code does something materially different: when `sii/ine > 5.0` it **falls back to the INE population** as the denominator (`return ine, True`), not `5.0 * ine`. For Providencia (the documented trigger, ratio 5.19) the implemented denominator is `ine` (116,202) whereas the published rule yields `5.0 * ine` (581,010) — a ~5× difference in the homicide-rate denominator, which directly changes the M1 metric and thus the composite score and rank for the capped commune. This is a user-facing accuracy claim that the code does not honor. Either the code or the docs are wrong; they must agree.
**Fix:** Decide the intended semantics and align both. If the cap is meant to clamp the ratio:
```python
ratio = sii / ine
if ratio > SII_CAP_RATIO:
    return SII_CAP_RATIO * ine, True   # clamp to 5.0× population, per published methodology
return float(sii), False
```
If INE fallback is actually intended, correct SOURCES.md and both methodology pages to say "falls back to the INE resident population" rather than "capped at 5.0×".

### CR-03: `normalize_metric` relies on scipy winsorize ignoring NaN, but never tests the NaN+outlier interaction

**File:** `pipeline/composite_index.py:35-51`
**Issue:** `winsorize(arr, limits=[0.01, 0.01])` is called on a raw `np.array(dtype=float)` that may contain `NaN` (the docstring at lines 26-28 explicitly says NaN communes flow through here). `scipy.stats.mstats.winsorize` computes percentile cut points; with `NaN` present in a plain ndarray (not a masked array), the sort/percentile logic places NaN at the high end, so the upper-1% clip can be driven by NaN positions rather than real maxima — producing wrong winsorization limits for the real data, silently. The code comment claims "scipy masked array handles this" but `arr` is **not** a masked array. The only NaN test (`test_normalize_spread`, lines 209-213) injects a single NaN into a clean ascending series with **no outlier**, so it never exercises the path where NaN interacts with the percentile clip that the function exists to perform. This is a correctness risk on the real 346-commune data where missing metrics coexist with extreme outliers (Sierra Gorda).
**Fix:** Winsorize only the non-NaN values, then scatter back:
```python
arr = np.asarray(series, dtype=float)
mask = ~np.isnan(arr)
arr_w = arr.copy()
arr_w[mask] = np.asarray(winsorize(arr[mask], limits=list(WINSORIZE_LIMITS)))
lo, hi = np.nanmin(arr_w), np.nanmax(arr_w)
...
```
Add a test combining a NaN with a large outlier and assert the clip point is computed from real data only.

## Warnings

### WR-01: `compute_composite` contains dead/confusing arithmetic that obscures the real formula

**File:** `pipeline/composite_index.py:142-146`
**Issue:** Line 143 computes `score = (weighted_sum / total_weight) * 100.0 / 100.0 * 100.0` and is immediately overwritten by line 146 `score = weighted_sum / total_weight`. The first assignment is dead code, and `* 100.0 / 100.0 * 100.0` is a no-op-plus-bug expression that a reader will trip over. It also means the "redistribute weight proportionally" comment sits next to an expression that is never used.
**Fix:** Delete lines 142-145; keep only `score = weighted_sum / total_weight`.

### WR-02: `_load_spd_homicide` is dead code duplicating `_load_spd_homicide_from` (and the same for SII/INE)

**File:** `pipeline/build_composite_index.py:74-124`, `403-435`
**Issue:** `_load_spd_homicide`, `_load_sii_exposure`, `_load_ine_population` (lines 74-124) are never called — `run_composite_index` uses the `_from(root)` variants (lines 242-244). Two parallel loaders with subtly different error messages invite drift: if the snapshot schema changes, only one set gets updated and the stale pair silently misleads the next maintainer.
**Fix:** Delete the three unused loaders (74-124) and keep the `_from` variants as the single source of truth.

### WR-03: `available_metrics` can be double-counted / decremented below the real count

**File:** `pipeline/build_composite_index.py:319-322`
**Issue:** `compute_composite` already excludes metrics whose normalized value is None/NaN from `available` (`composite_index.py:131-137`). For an SII-absent commune the homicide denominator falls back to INE, so `spd_homicide_rate` is still present and counted. The code then unconditionally does `available = max(0, available - 1)` for every SII-absent commune. But SII is **not one of the 7 weighted metrics** (it is only the homicide denominator), so decrementing `available_metrics` conflates "missing a weighted metric" with "used INE fallback for the denominator". A commune missing SII still has all 7 weighted metrics available; reporting `available_metrics == 6` misrepresents data completeness to downstream consumers. The test (`test_composite.py:418`) bakes in this behavior, so the test is asserting a debatable semantic, not catching a bug.
**Fix:** Either track a separate `sii_fallback: bool` flag for transparency, or document explicitly that `available_metrics` counts "data-quality points" rather than weighted-metric availability. Do not silently fold a denominator-source signal into a metric-count field.

### WR-04: Map-payload size guard message is stale and misleading

**File:** `pipeline/build_map_payload.py:233-237`
**Issue:** The hard limit was raised to `35840` (35 KB) at line 233, but the success log at line 237 still prints `"size: %d bytes (< 30720 limit OK)"`. An operator reading logs sees a 30720 limit that is no longer enforced. Worse, the comment at lines 225-229 says the omit-when-null path "provides no savings here" because all 346 communes were enriched — but per CR-01 the **2025** payload has no `ci` at all, so the budget math and the limit choice are reasoning about the wrong year.
**Fix:** Update the log string to reference 35840, and re-evaluate the size budget against the actual per-year payloads (only the 2024 payload carries `ci`).

### WR-05: `_assign_levels` quintile fallback can still return NaN-derived level 3 silently

**File:** `pipeline/build_composite_index.py:179-197`
**Issue:** When `qcut` drops duplicate bin edges, the fallback uses `pd.cut(pcts, bins=[0,0.2,...,1.0], include_lowest=True)`. Values exactly at a boundary or any residual NaN are coerced to level 3 at line 197 (`int(l) if not pd.isna(l) else 3`). Defaulting genuinely-unclassifiable communes to the middle band (3) is a silent data-quality masking decision with no log line. With heavily-tied composite scores (plausible when many communes hit the 0.0 floor from `compute_composite` returning `0.0`), a large block can be mislabeled level 3.
**Fix:** Log a warning with the count of communes that hit the NaN→3 fallback so the masking is auditable, and consider whether tied-at-zero communes should be level 1 rather than 3.

### WR-06: `_run_pipeline` `break` after the first region means region-loop variable is misleading and fragile

**File:** `pipeline/scrape_cead.py:276-333`
**Issue:** The region `for` loop unconditionally `break`s after the first iteration (line 333), relying on assumption A1 ("CEAD returns all communes regardless of region filter"). The `region_cuts` computed at lines 280-283 is never used inside the loop body (the fetch uses `list(catalog.keys())`), so it is dead computation, and the loop structure pretends to iterate 16 regions while running exactly once. If A1 is ever false the silent single-pass will drop 15 regions of data and only fail at the 346-count validation much later, with a confusing error.
**Fix:** Remove the dead `region_cuts` computation and the loop-with-immediate-break; fetch once explicitly with a comment that A1 makes the region parameter irrelevant. If A1 must be guarded, assert the returned row count instead of relying on a downstream count check.

### WR-07: ResultPanel derives a second, unrelated "level" from rate and uses it for the composite comparison bar

**File:** `site/src/components/map/ResultPanel.tsx:215-218`, `324`
**Issue:** `level` is computed as a crude `rate / maxRate` quintile (lines 215-218) — this is the per-family rate level, NOT the composite index level (`ci.level`). That same `level` then colors the comparison bar (`background: var(--s${level})`, line 324) which sits in the rate stat card. This is internally consistent for the rate card, but the panel simultaneously shows `ci.level`-derived band labels in the composite section. Two different "level" notions in one panel with the same visual vocabulary (`--s1..--s5` color dots) will mislead users into thinking the rate-derived chip reflects the composite index.
**Fix:** Rename the local to `rateLevel` and ensure the composite section's color cues derive from `ci.level`, not the rate quintile, so the two surfaces are visually distinguishable.

### WR-08: Homicide rate rounded to integer in map-payload loses all sub-1.0 homicide rates

**File:** `pipeline/build_map_payload.py:115`, `147`
**Issue:** `homicide_rate_val = int(round(h_rate_raw))` rounds the per-100k homicide rate to an integer. Most communes have homicide rates between 0 and ~5 per 100k; a commune with a genuine rate of 0.4 rounds to `0`, which `buildStyleMapFromHomicide` (`ChoroplethLayer.ts:125-134`) treats identically to a true zero (lightest bucket, 0.25 opacity). This erases the distinction between low-but-nonzero and zero homicide communes on the map. The per-100k rate is precisely the small-magnitude quantity where integer rounding destroys signal.
**Fix:** Preserve one decimal (`Math.round(x*10)/10` equivalent, store as float) for `hr`, or store as count-derived value; the 30/35 KB budget can absorb one decimal place for one field across 346 communes.

## Info

### IN-01: `ci_band_1..5` i18n strings are defined but never used (dead config)

**File:** `site/src/config/i18n.ts:152-156`, `310-314`, `471-475`
**Issue:** `ci_band_1` through `ci_band_5` are declared in the `I18nStrings` interface and populated in both locales, but every consumer hardcodes local `BAND_EN`/`BAND_ES`/`BAND_EN_PAGE`/`BAND_ES_PAGE` arrays instead (`ResultPanel.tsx:123-124`, `commune/[slug].astro:224`, `es/comuna/[slug].astro:227`). The canonical i18n strings are dead and will drift from the hardcoded copies.
**Fix:** Use `[t.ci_band_1, ...]` (or build the array from the strings) in all four places and delete the local arrays.

### IN-02: Band label vocabularies are inconsistent across surfaces

**File:** `site/src/components/map/ResultPanel.tsx:123-124` vs `site/src/config/i18n.ts:310-314`
**Issue:** ResultPanel's `BAND_EN` = ['Very Low','Low','Moderate','High','Very High'] matches `ci_band_*`, but the Legend's `legend_qual_*` uses ['Very low','Low','Medium','High','Very high'] (`i18n.ts:255-259`). In composite mode the legend title is "Crime Index" but the band labels shown are the Medium-vocabulary family labels, while the panel shows Moderate-vocabulary composite labels. Same concept, two label sets, on screen at once.
**Fix:** Standardize composite-mode legend labels on the `ci_band_*` vocabulary.

### IN-03: `assert_year_alignment` is effectively a tautology as wired

**File:** `pipeline/build_composite_index.py:252-255`
**Issue:** `cead_year`, `spd_year`, and `sii_year` are all set to `REFERENCE_YEAR` (lines 252, and the `_from` loaders hardcode `year_to_use = REFERENCE_YEAR`). The alignment assertion therefore compares three copies of the same constant and can never fail in production — it only guards the test fixtures. The "fail loudly if sources disagree" intent (D-10) is not actually achieved because the actual data year is never derived from the records; it is forced to 2024.
**Fix:** Derive each year from its snapshot's records (max year present, or the year actually selected) before asserting alignment, so a snapshot that lacks 2024 fails the alignment check rather than the later `KeyError`/empty-dict path.

### IN-04: `figure-registry.mjs` F15 token group will match incidental prose

**File:** `site/scripts/validate/figure-registry.mjs:188`
**Issue:** F15 passes if SOURCES.md contains both `'RSS'` and `'news'` anywhere. These are common substrings (`news` matches inside many words); the check is weak provenance validation that would pass even if the news-layer attribution section were deleted, as long as the words appear elsewhere.
**Fix:** Anchor the token to a heading marker (e.g. `'## News feeds'`) as other figures do.

### IN-05: `mark_partial_year` mutates input in place while also returning it

**File:** `pipeline/scrape_cead.py:67-90`
**Issue:** The function mutates `series` in place (line 89) and returns the same list (line 90). Callers (`scrape_cead.py:417`) reassign the return value, which reads as if a new list is produced, masking the in-place mutation. Low risk here since the caller owns `series`, but the dual contract is a foot-gun for future reuse.
**Fix:** Either mutate-and-return-None, or copy-and-return; pick one contract and document it.

---

_Reviewed: 2026-06-19_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
