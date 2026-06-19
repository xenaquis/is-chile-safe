---
phase: 18-composite-crime-index
verified: 2026-06-19T12:00:00Z
status: gaps_found
score: 3/5 must-haves verified
overrides_applied: 0
gaps:
  - truth: "The map popup and ResultPanel composite section render the integer 0–100 score when a commune is clicked in the default (year=2025) view"
    status: failed
    reason: "ResultPanel reads data.composite_index?.[String(year)] from the individual commune JSON, which only has the key '2024'. With year initialised to 2025 (MapIsland.tsx:96), the composite block guard (ResultPanel.tsx:262) evaluates to null and the entire composite section is skipped. The user clicking any commune in the default view sees no index score, no band label, and no rank — the core UI delivery of CI-05 is invisible."
    artifacts:
      - path: "site/src/components/map/ResultPanel.tsx"
        issue: "Line 262: `data.composite_index?.[String(year)]` — year is 2025 at mount; commune JSON only has composite_index['2024']"
      - path: "site/src/components/map/MapIsland.tsx"
        issue: "Line 96: `useState(2025)` — composite data is only keyed under 2024 in commune JSONs"
    missing:
      - "Introduce a COMPOSITE_YEAR = 2024 constant in ResultPanel (mirroring commune/[slug].astro:221) and read data.composite_index?.[String(COMPOSITE_YEAR)] instead of String(year)"

  - truth: "The SII exposure denominator implementation matches the published methodology (cap at 5.0 × INE population)"
    status: failed
    reason: "composite_index.py:84 returns `ine` (INE population) when the SII/INE ratio exceeds 5.0. SOURCES.md:104 states 'value clamped to cap 5.0 before normalization'; methodology.astro:417 states 'capped at 5.0 × the commune's INE resident population'. For Providencia (ratio 5.186) the implemented denominator is 116,202 (INE) but the published rule yields 581,010 (5.0 × INE) — a ~5× difference in the homicide-rate denominator that changes the M1 metric and thus the composite score and rank for capped communes. CI-04 and CI-08 are both impacted: the data-computation contract and the methodology documentation are contradicting each other."
    artifacts:
      - path: "pipeline/composite_index.py"
        issue: "Line 84: `return ine, True` — returns raw INE population, not 5.0 × INE"
      - path: "data/SOURCES.md"
        issue: "Line 104: states 'value clamped to cap 5.0' — contradicts code"
      - path: "site/src/pages/methodology.astro"
        issue: "Line 417: states 'capped at 5.0 × the commune's INE resident population' — contradicts code"
      - path: "site/src/pages/es/metodologia.astro"
        issue: "ES methodology page mirrors the same inaccurate claim"
    missing:
      - "Decide the intended semantics: if the cap is 5.0×INE, fix code to `return SII_CAP_RATIO * ine, True`; if INE fallback is intended, correct SOURCES.md and both methodology pages to say 'falls back to the INE resident population'"

  - truth: "normalize_metric correctly winsorizes only the non-NaN values so NaN presence does not distort clip points"
    status: failed
    reason: "composite_index.py:38 calls winsorize() on a plain ndarray containing NaN values. scipy.stats.mstats.winsorize places NaN at the high end during sorting, so the upper-1% clip point can be derived from NaN positions rather than real data maxima — producing wrong winsorization limits when NaN communes coexist with extreme outliers (e.g., Sierra Gorda). The code comment 'scipy masked array handles this' is incorrect: arr is never converted to a masked array. The NaN re-injection on line 49 restores NaN positions in the output but does not fix the clip-point computation. No test exercises NaN coexisting with an outlier. CI-02 is impacted."
    artifacts:
      - path: "pipeline/composite_index.py"
        issue: "Line 38: winsorize called on plain ndarray with NaN; line 37 comment incorrectly claims masked array handling"
      - path: "pipeline/tests/test_composite.py"
        issue: "NaN test (lines 209-213) injects a single NaN into a clean series with no outlier — does not exercise the NaN+outlier interaction"
    missing:
      - "Mask NaN before winsorizing: compute arr[mask] = winsorize(arr[mask], ...) then scatter back; add a test combining NaN with a large outlier and assert clip point is derived from real data"
---

# Phase 18: Composite Crime Index — Verification Report

**Phase Goal:** Users can see each commune's overall crime exposure as a single 0–100 index score in the map, commune pages, and popup — computed from 7 hardened metrics with exposure adjustment — while every page maintains the editorial constraint that no absolute safety verdict is issued.
**Verified:** 2026-06-19
**Status:** gaps_found — 3 blockers
**Re-verification:** No — initial verification

## Code Review Findings — Independent Assessment

The phase submission included a code review (18-REVIEW.md) flagging CR-01, CR-02, and CR-03 as critical blockers. This verification independently confirmed all three against the actual codebase. One finding from CR-01 was partially inaccurate (the choropleth map itself is not broken), but a real blocking defect is present in the same area:

| CR ID | Claim | Verdict | Evidence |
|-------|-------|---------|----------|
| CR-01 | Map choropleth defaults to all-grey because 2025 payload has no `ci` | PARTIAL — choropleth is fine; ResultPanel IS broken | `site/public/data/cead/map-payload-2025.json` communas[0] has `ci=4`; payload builder reads from `composite_index[REFERENCE_YEAR]` and copies into all year payloads. BUT ResultPanel.tsx:262 reads `data.composite_index?.[String(year)]` from individual commune JSON which only has key "2024" — composite panel block returns null at year=2025. |
| CR-02 | SII cap code returns INE but docs say 5.0 × INE | CONFIRMED BLOCKER | `composite_index.py:84` returns `ine`; `SOURCES.md:104` and `methodology.astro:417` state "capped at 5.0 ×". For Providencia (ratio 5.186): code denominator = 116,202; published rule denominator = 581,010. |
| CR-03 | winsorize on plain ndarray with NaN distorts clip points | CONFIRMED — severity real but mitigated | `composite_index.py:38` calls winsorize on plain ndarray containing NaN; NaN re-injection at line 49 restores output NaN but does not fix the clip computation. No test exercises NaN+outlier path. |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Commune pages show 0–100 score + 5-band label + national/regional rank + mandatory bilingual caveat | VERIFIED | `commune/[slug].astro:221-238`: COMPOSITE_YEAR=2024 hardcoded; score rendered via `ci.score`; caveat block at line 238; `ci_caveat_text` in both locales. |
| 2 | Map choropleth toggles between composite-index mode and per-family rate mode; popup shows score | PARTIAL FAIL | Toggle is implemented (MapIsland.tsx:467-498); choropleth ci coloring works from payload ci field. BUT ResultPanel composite section never renders at default year=2025 — `data.composite_index?.[String(2025)]` is always null from commune JSON. The popup score requirement of CI-05 is not met in the default view. |
| 3 | Pipeline `build_composite_index.py` runs in isolation; distribution spread assertion passes | VERIFIED | `build_composite_index.py` exists as separate entrypoint; `test_composite.py:185-204` and `328-351` assert 25th percentile > 10% of max. |
| 4 | CI forbidden-language validator flags unqualified superlatives; npm run validate exits 0 | VERIFIED | `forbidden-language.mjs:47-60` contains `mas peligrosa`, `mas peligroso`, `el mas seguro`, `most dangerous`; wired into `all.mjs` and `npm run validate`. |
| 5 | @astrojs/check passes; methodology pages document formula/normalization/SPD switch/SII caveat; figure-registry zero-orphan; schema migration non-breaking | PARTIAL FAIL | Methodology pages exist and document the formula. BUT SOURCES.md:104 and methodology.astro:417 state SII cap = "5.0 × INE population" while code returns raw INE — documentation accuracy claim in CI-04 and CI-08 is not met. |

**Score:** 3/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/composite_index.py` | Pure compute functions with winsorization | STUB (partial) | Exists and substantive, but normalize_metric has incorrect NaN handling |
| `pipeline/build_composite_index.py` | Isolated pipeline entrypoint | VERIFIED | Exists, wired into GitHub Actions workflow |
| `pipeline/composite_config.py` | C-02 locked weight vector | VERIFIED | Exists with correct weights summing to 1.00 |
| `data/cead/comparator_table.json` | Phase 21 handoff data | VERIFIED | Exists per 18-01-SUMMARY.md |
| `site/src/components/map/MapIsland.tsx` | Mode toggle composite/family | VERIFIED (toggle) | Toggle implemented; COMPOSITE_YEAR fix needed for ResultPanel |
| `site/src/components/map/ResultPanel.tsx` | Composite index display in popup | FAILED | `composite_index?.[String(year)]` with year=2025 always null |
| `site/scripts/validate/forbidden-language.mjs` | Extended FORBIDDEN_TERMS | VERIFIED | Contains all 4 new terms |
| `site/scripts/validate/figure-registry.mjs` | F13 + F14 registered | VERIFIED | F13 and F14 present with accent-free tokens |
| `data/SOURCES.md` | Composite methodology documentation | PARTIAL FAIL | Documents methodology but SII cap description contradicts code |
| `site/src/pages/methodology.astro` | EN methodology page | PARTIAL FAIL | Exists but SII cap claim contradicts implementation |
| `site/src/pages/es/metodologia.astro` | ES methodology page | PARTIAL FAIL | Same SII cap contradiction |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| ResultPanel.tsx | commune JSON | `composite_index?.[String(year)]` | BROKEN | year=2025; JSON only has "2024" key |
| commune/[slug].astro | commune JSON | `composite_index?.[String(COMPOSITE_YEAR)]` where COMPOSITE_YEAR=2024 | WIRED | Correctly hardcodes 2024 |
| MapIsland year=2025 | map-payload-2025.json | `ci` field in comunas | WIRED | Payload builder copies 2024 ci level into all year payloads |
| figure-registry.mjs F13/F14 | data/SOURCES.md | token substring match | WIRED | Accent-free tokens confirmed present in SOURCES.md |
| forbidden-language.mjs | npm run validate | all.mjs inclusion | WIRED | Listed at all.mjs:45 |
| composite_index.py SII cap | methodology pages | documented behavior | BROKEN | Code: returns INE; docs: returns 5.0 × INE |

### Requirements Coverage

| Requirement | Description | Status | Evidence |
|------------|-------------|--------|---------|
| CI-01 | Isolated build_composite_index.py; no CEAD breakage on failure | SATISFIED | Separate entrypoint; `continue-on-error` in workflow |
| CI-02 | Winsorization / percentile-rank normalization + pytest spread assertion | PARTIAL | Spread assertion exists; winsorize NaN handling is incorrect (CR-03) |
| CI-03 | SPD VHC as M1; CEAD featured_rates.homicidios preserved | SATISFIED | M1 label consistent; featured_rates untouched per additive-only design |
| CI-04 | SII exposure denominator with documented cap | FAILED | Code and docs contradict each other on cap semantics (CR-02) |
| CI-05 | 0–100 integer + 5 bands + national/regional rank in UI (map popup, ResultPanel, commune pages) | PARTIAL | Commune pages: VERIFIED. ResultPanel in default view (year=2025): FAILED — composite block never renders. |
| CI-06 | Mandatory bilingual caveat block on all index-displaying pages | SATISFIED | Caveat present in commune pages and ResultPanel (when ci is non-null) |
| CI-07 | Choropleth toggle: index mode vs per-family rate mode | SATISFIED | Toggle implemented; choropleth correctly colored from payload ci field |
| CI-08 | Methodology pages + figure-registry zero-orphan | PARTIAL | Pages exist with composite section; figure-registry zero-orphan confirmed. SII cap documentation inaccurate. |
| CI-09 | Forbidden-language validator extended; npm run validate green | SATISFIED | All 4 new terms added; validator wired and passing |
| CI-10 | Schema migration non-breaking; @astrojs/check green; comparator_table.json emitted | SATISFIED (per SUMMARY) | 13/13 validators passed per 18-05-SUMMARY.md; comparator_table.json exists |

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `pipeline/composite_index.py:37` | Comment "scipy masked array handles this" — code never creates a masked array | BLOCKER | Incorrect code comment describing non-existent NaN safety mechanism; winsorize clip can be distorted by NaN |
| `pipeline/composite_index.py:142-145` | Dead arithmetic: `score = (weighted_sum / total_weight) * 100.0 / 100.0 * 100.0` immediately overwritten (WR-01) | WARNING | Confusing dead code |
| `site/src/components/map/ResultPanel.tsx:215-218` | `level` computed from rate quintile, same `--s1..--s5` vocabulary as composite level (WR-07) | WARNING | Two different "level" notions share visual language in one panel |
| `site/src/config/i18n.ts:152-156` | `ci_band_1..5` strings defined but never used; all consumers hardcode local arrays (IN-01) | INFO | Documentation drift risk |

### Gaps Summary

Three blocking defects prevent full goal achievement:

**Gap 1 — ResultPanel composite section invisible in default view (CR-01 variant)**

The phase goal requires the composite score to appear "in the map popup." The map popup is rendered by ResultPanel when a commune is clicked. ResultPanel.tsx:262 reads `data.composite_index?.[String(year)]` from the fetched commune JSON. The commune JSON stores composite data under the key "2024" only. With `year` initialized to `2025` in MapIsland, clicking any commune shows no composite index, no band label, and no rank — the panel composite block returns null. The static commune pages correctly hardcode `COMPOSITE_YEAR = 2024`, confirming this inconsistency. Fix: add `const COMPOSITE_YEAR = 2024` in ResultPanel and read `data.composite_index?.[String(COMPOSITE_YEAR)]`.

**Gap 2 — SII cap: code/docs mismatch (CR-02)**

CI-04 requires "a documented cap (fall back to INE population when ratio exceeds threshold)." CI-08 requires methodology pages to document the SII exposure caveat. Both are met by the documentation, but the documentation is factually wrong about what the code does. SOURCES.md and methodology.astro say the denominator is "capped at 5.0 × INE population"; the code returns raw INE population. For Providencia this is a ~5× difference in the M1 homicide rate denominator, directly changing composite score and rank. Either the code or the docs must be corrected so they agree.

**Gap 3 — normalize_metric NaN+outlier winsorization correctness (CR-03)**

CI-02 requires normalization that prevents "right-skewed micro-comuna outliers" from collapsing the scale. The winsorization exists for exactly this purpose, but when NaN communes coexist with outlier communes, the scipy winsorize clip points are computed incorrectly because NaN values sort to the high end of the array. The correctness risk is most acute when multiple NaN communes coincide with extreme outliers — a plausible real-data scenario. The existing NaN test does not cover this case.

---

_Verified: 2026-06-19_
_Verifier: Claude (gsd-verifier)_
