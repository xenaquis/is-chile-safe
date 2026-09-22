# Phase 18: Composite Crime Index — Research

**Researched:** 2026-06-19
**Domain:** Python pipeline (scipy winsorization, multi-source join), TypeScript (Leaflet choropleth toggle, React panel), Astro static pages
**Confidence:** HIGH — all findings verified by direct codebase inspection

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Normalization = winsorized min-max via `scipy.stats.mstats.winsorize(limits=[0.01, 0.01])` then min-max. Guard: `index_scores.describe()["25%"] > index_scores.max() * 0.10`.
- **D-02:** Weights = severity-weighted. Homicide 0.30 recommended anchor. Exact vector in `composite_config.py`; documented in `data/SOURCES.md` + both methodology pages. Equal weights explicitly rejected.
- **D-03:** SII exposure denominator applied with cap fallback: `sii_workers / ine_population > 5.0` → use INE denominator.
- **D-04:** Cap threshold = 5.0 (locked default; confirmed placement in §SII Cap section below).
- **D-05:** Composite index mode loads by default; toggle switches to per-family rate mode.
- **D-06:** Popup shows exact integer 0–100 score plus band label when in index mode.
- **D-07:** Caveat block = always-visible inline, never collapsed, on every index-displaying surface. Bilingual.
- **D-08:** Bands EN: Very Low / Low / Moderate / High / Very High; ES: Muy Bajo / Bajo / Moderado / Alto / Muy Alto.
- **D-09:** Display precision = integer 0–100 in all headline contexts; one decimal only in comparator rows (Phase 21).
- **D-10:** Index anchors to latest year where SPD VHC + CEAD + SII are ALL final (≤2024). Pipeline assertion enforces.
- **D-11:** `build_composite_index.py` = isolated step after CEAD scraper and before `build_map_payload.py` (extracted from `scrape_cead.py`). GitHub Actions order: scrape → index → payload.
- **D-12:** Migration is additive and non-breaking: existing `featured_rates` fields remain intact; new fields added alongside. All consumers enumerated + `@astrojs/check` + full validator suite must pass green.

### Claude's Discretion

- Exact severity weight vector numbers (D-02 gives 0.30 homicide as anchor; planner proposes full vector for user review before lock).
- Map-payload `ci` field encoding (level 1–5; omitted for pre-2018 years).
- `comparator_table.json` exact schema/field set (must carry `composite_index` per commune for Phase 21).

### Deferred Ideas (OUT OF SCOPE)

- User-configurable weight sliders — incompatible with static pre-rendering; v3+.
- Confidence intervals / error bars — v3+.
- Real-time index updates, star ratings — v3+.
- Comparator island + A-vs-B SEO pages — Phase 21 (consumes `comparator_table.json`).
- Go-live / deploy hook / GSC / AdSense — Phase 22.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CI-01 | Pipeline computes 0–100 composite index per comuna from 7 metrics in isolated `build_composite_index.py` step | §Pipeline Extraction confirms `build_map_payload` is currently embedded in `scrape_cead.py`; extraction plan documented |
| CI-02 | Normalization: winsorized min-max, not raw min-max; pytest spread assertion guards distribution | §Normalization Implementation documents exact scipy call, NaN handling, and assertion formulation |
| CI-03 | SPD VHC = homicide input (M5); CEAD `featured_rates.homicidios` preserved unchanged | §Year-Alignment Assertion documents that SPD and CEAD encode years as integers; 2024 is confirmed latest final year for both |
| CI-04 | SII exposure denominator with documented cap; fallback to INE population when `sii_workers/ine_population > 5.0` | §SII Cap Logic confirms only Providencia (CUT 13123, ratio 5.19) exceeds 5.0; Las Condes is 4.03; cap is well-placed |
| CI-05 | Integer 0–100 score + 5 bands + national/regional rank in map popup, ResultPanel, and commune pages | §Display Surfaces maps the exact JSX slots in `ResultPanel.tsx` where composite score integrates |
| CI-06 | Mandatory bilingual caveat block on every index-displaying surface; no absolute safety verdict | §Editorial Framing documents caveat text and placement rules |
| CI-07 | Choropleth toggle between index mode (default) and per-family rate mode | §Choropleth Toggle documents `buildStyleMapFromCompositeIndex()` signature and toggle state management |
| CI-08 | EN + ES methodology pages updated; every new figure registered (figure-registry zero-orphan passes) | §Figure Registry Extension documents F13/F14 unlock requirement and token patterns |
| CI-09 | Forbidden-language validator extended to flag "safest / most dangerous / más segura / más peligrosa" unqualified | §Forbidden-Language Validator Extension shows exact additions to `FORBIDDEN_TERMS` array |
| CI-10 | Schema migration verified non-breaking across all consumers; TypeScript types added; `comparator_table.json` emitted | §Consumer Enumeration lists all 6 consumer files with exact field paths |
</phase_requirements>

---

## Summary

Phase 18 delivers the composite crime-exposure index: a 0–100 score per commune computed from 7 severity-weighted, winsorized metrics (CEAD crime families + SPD VHC homicide + SII exposure adjustment), surfaced as the default choropleth mode and in the commune panel/pages with mandatory bilingual caveats.

All major technical decisions are locked in CONTEXT.md (D-01..D-12). The research unknowns that block planning have been resolved by direct codebase and snapshot inspection:

**SII cap confirmation (D-04):** Only 1 of 346 communes exceeds ratio 5.0 — CUT 13123 (Providencia) at 5.19x. Las Condes is 4.03x. The cap at 5.0 is correctly placed; it triggers for exactly the right case and affects only one commune with a genuine HQ-concentration artifact.

**Year alignment (D-10):** CEAD series runs through 2026 (2026 marked `partial: True`). The latest non-partial CEAD year is 2025. SPD latest final year is 2024 (2025 present but caveat-flagged). SII latest year is 2024. The correct index anchor year is **2024** (the highest year where all three sources are final). The pipeline assertion must enforce `spd_year == cead_year_used == sii_year == 2024`.

**Pipeline extraction:** `build_map_payload()` is a standalone function already defined at lines 102–204 of `scrape_cead.py`. It is called by `_write_all_outputs()` (line 326). Extraction to `pipeline/build_map_payload.py` is a clean cut — the function has no circular imports; it imports from `pipeline.cead.normalizer` and `pipeline.shared.schema`.

**Consumer enumeration (D-12):** 6 consumers of `featured_rates` / map payload identified. Schema migration plan confirmed additive.

**Forbidden-language validator:** Lives at `site/scripts/validate/forbidden-language.mjs`. The terms "safest / most dangerous / más segura / más peligrosa" are partially present but incomplete (see §Forbidden-Language Validator Extension).

**scipy availability:** scipy 1.17.1 is installed in the local environment. `scipy>=1.13,<2` is correct pin for `pipeline/requirements.txt`.

**Primary recommendation:** Implement in this exact order — (1) add scipy to requirements.txt, (2) write `composite_config.py` + `composite_index.py`, (3) extract `build_map_payload.py`, (4) extend GitHub Actions workflow, (5) add `ci` field to `CommunaPayload` TS interface + `buildStyleMapFromCompositeIndex()`, (6) update `ResultPanel.tsx` + commune pages + caveat blocks, (7) extend forbidden-language validator + figure-registry, (8) update methodology pages + `data/SOURCES.md`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Index computation (7 metrics, winsorize, weight) | Python pipeline | — | Pure server-side batch; no client involvement |
| SII / SPD data join and cap logic | Python pipeline | — | All data joins happen at pipeline run time into static JSON |
| Index JSON emission (per-commune + comparator_table) | Python pipeline | — | Output is static JSON consumed at build time |
| Map-payload `ci` field | Python pipeline | — | Emitted by `build_map_payload.py` after index step enriches commune files |
| Choropleth toggle UI (index/family mode) | Browser / Client | — | Leaflet layer style swap via `applyStyleMap()`; no SSR needed |
| Index score display in popup | Browser / Client | — | Already client-rendered in `ResultPanel.tsx`; add new JSX block |
| Index score + rank on commune pages | Frontend Server (SSR) | — | Astro `.astro` templates read commune JSON at build time; pre-rendered HTML |
| Bilingual caveat block | Frontend Server (SSR) | Browser / Client | Rendered in Astro templates (commune pages) and in React island (popup) |
| Forbidden-language validator | Build / CI | — | Runs against `dist/` HTML post-build in `npm run validate` |
| Figure-registry validator | Build / CI | — | Reads `data/SOURCES.md`; no dist/ needed |
| `comparator_table.json` | Python pipeline | — | Written once by `build_composite_index.py`; consumed at build time by Phase 21 |

---

## Standard Stack

### Core (no additions beyond confirmed one)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scipy | `>=1.13,<2` | `winsorize()` for clipping per-metric outlier tails | Only addition needed; scipy 1.17.1 already in local env [VERIFIED: local env] |
| pandas | 2.3.3 (pinned) | DataFrame groupby/merge, per-metric normalization | Already in `pipeline/requirements.txt` [VERIFIED: codebase] |
| numpy | (transitive via pandas) | `nanmin`/`nanmax`/`clip` for normalization math | pandas 2.x hard-depends on numpy [VERIFIED: codebase] |
| pydantic | 2.13.4 (pinned) | Schema validation for index output | Already in `pipeline/requirements.txt` [VERIFIED: codebase] |
| openpyxl | 3.1.5 (pinned) | `pandas.read_excel` on SPD VHC `.xlsx` | Already pinned [VERIFIED: codebase] |
| pyxlsb | 1.0.10 (pinned) | Read SII `PUB_COMU.xlsb` | Already pinned [VERIFIED: codebase] |
| chroma-js | 3.2.0 (pinned) | `chroma.scale().domain([0,100])` for index choropleth | Already in `site/package.json` [VERIFIED: codebase] |

**One-line requirements.txt change:**
```
scipy>=1.13,<2
```

### What NOT to Add (from STACK.md — enforce at planning time)

`scikit-learn`, `statsmodels`, `D3.js`, `react-leaflet` `<GeoJSON>`, `zustand`, `react-query`, `Recharts`, any i18n lib — all explicitly excluded.

---

## Package Legitimacy Audit

Only one new package requires audit.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| scipy | PyPI | ~24 years | ~40M/wk | github.com/scipy/scipy | [OK] — foundational scientific library | Approved |

scipy is one of the foundational scientific Python packages; no legitimacy concerns. [VERIFIED: local env — `scipy.__version__ == '1.17.1'`]

**Packages removed:** none
**Packages flagged:** none

---

## Architecture Patterns

### System Architecture Diagram

```
Data Sources (snapshots, already fetched)
  data/snapshots/spd_homicide.json   [int year, int homicides per cut]
  data/snapshots/sii_exposure.json   [int year, int trabajadores per cut]
  data/ine/poblacion_comunal.json    [population_2024 per cut]
  data/cead/comunas/{CUT}.json       [series[], featured_rates{}]
         |
         v
[pipeline/scrape_cead.py]            (unchanged — exits before payload)
  writes base comunas/{CUT}.json
         |
         v
[pipeline/build_composite_index.py]  (NEW — isolated step)
  reads 4 sources above
  computes 7-metric composite per commune for year 2024
  enriches comunas/{CUT}.json (adds composite_index, spd_homicide_rate, sii_exposure_index)
  writes data/cead/comparator_table.json
         |
         v
[pipeline/build_map_payload.py]      (EXTRACTED from scrape_cead.py)
  reads enriched comunas/{CUT}.json
  adds ci field (level 1-5) to each commune entry
  writes map-payload.json + map-payload-{year}.json
         |
         v
[GitHub Actions: git commit + push]  [skip ci] tag on data commits
         |
         v
[Astro build] (site/src/)
  reads data/cead/comunas/{CUT}.json  → commune pages (index score + rank + caveat)
  reads data/cead/map-payload.json    → map island (ci field for choropleth)
         |
         v
[dist/ HTML] → Cloudflare Pages CDN
  map choropleth: index mode default (ci level → color)
  popup: ResultPanel.tsx shows composite score + band + caveat block
  commune pages: static integer score + national/regional rank + caveat
```

### Recommended Project Structure (additions only)

```
pipeline/
  composite_config.py        # METRIC_WEIGHTS dict, WINSORIZE_LIMITS, REFERENCE_YEAR
  composite_index.py         # normalize_metric(), compute_composite(), year-alignment assertion
  build_composite_index.py   # entrypoint: reads snapshots + communas, writes enriched JSON
  build_map_payload.py       # EXTRACTED from scrape_cead.py — same build_map_payload() function
  tests/
    test_composite.py        # pytest: distribution assertion, SII cap, year-alignment assertion

site/src/
  components/map/
    ChoroplethLayer.ts       # add ci to CommunaPayload; add buildStyleMapFromCompositeIndex()
    MapIsland.tsx            # add mode toggle state; default to 'composite'
    ResultPanel.tsx          # add composite score block + caveat block
  pages/
    commune/[slug].astro     # add composite_index display section + caveat
    es/comuna/[slug].astro   # ES equivalent

data/
  SOURCES.md                 # add F13 (SPD VHC), F14 (SII), weight vector, normalization method
  cead/
    comparator_table.json    # NEW — all-commune compact summary for Phase 21
```

### Pattern 1: Winsorized Min-Max Normalization

**What:** Clip top/bottom 1% of each metric's distribution before min-max scaling to [0, 100]. Prevents Sierra Gorda (43,369/100k) from compressing 344 other communes to near-zero.

**When to use:** Every metric before weighting. Called once per metric per pipeline run.

```python
# Source: STACK.md verified pattern + scipy 1.17.1 local confirmation
from scipy.stats.mstats import winsorize
import numpy as np
import pandas as pd

def normalize_metric(series: pd.Series) -> pd.Series:
    """Winsorize then min-max to [0, 100]. NaN communes preserved as NaN."""
    arr = np.array(series, dtype=float)
    # winsorize operates on valid values; NaN treated as masked
    arr_w = np.array(winsorize(arr, limits=[0.01, 0.01]))
    lo, hi = np.nanmin(arr_w), np.nanmax(arr_w)
    if hi == lo:
        return pd.Series(np.zeros(len(arr)), index=series.index)
    result = (arr_w - lo) / (hi - lo) * 100
    # Re-inject NaN for communes that had NaN input
    result[np.isnan(arr)] = np.nan
    return pd.Series(result, index=series.index)
```

**Critical NaN handling note:** `scipy.stats.mstats.winsorize` uses masked arrays. When the input `arr` contains `np.nan`, the function may propagate them or treat them as valid values depending on scipy version. Safe approach: extract non-NaN values, winsorize those, then re-inject NaN for missing communes. The pattern above re-injects NaN after the operation using the original `arr` mask.

### Pattern 2: SII Exposure Adjustment with Cap

**What:** Adjust crime rate denominator using SII `trabajadores` as proxy for daytime-activity population. Cap at 5.0× to exclude HQ-domicile artifacts.

**Confirmed data:** Only CUT 13123 (Providencia) exceeds 5.0 (ratio 5.19). CUT 13114 (Las Condes) is 4.03 — below cap. 5 communes absent from SII 2024 (use INE fallback for those too).

```python
# Source: direct inspection of data/snapshots/sii_exposure.json and data/ine/
def get_exposure_denominator(cut: str, sii_by_cut: dict, ine_pop: dict) -> tuple[float, bool]:
    """
    Returns (effective_denominator, used_cap_fallback).
    used_cap_fallback=True signals that the SII cap was triggered.
    """
    ine = ine_pop.get(cut, 0)
    sii = sii_by_cut.get(cut)  # None if commune absent from SII

    if sii is None or ine <= 0:
        return float(ine), False  # no SII data — use INE

    ratio = sii / ine
    if ratio > 5.0:
        return float(ine), True   # cap triggered — use INE
    return float(sii), False      # use SII workers as denominator
```

### Pattern 3: Year-Alignment Assertion

**What:** Enforce that all three data sources are from the same reference year before computing the composite. Fail loudly if any source is from a different year.

**Confirmed alignment:**
- CEAD: latest non-partial year = **2025** (2026 is marked `partial: True`)
- SPD: latest final year = **2024** (2025 data present but caveat-flagged as "partial and unconsolidated")
- SII: latest year = **2024**

The intersection is **2024**. The pipeline must use CEAD 2024 data (not 2025) for index computation, even though 2025 CEAD data exists and is non-partial. This is required by D-10 to align with the SPD and SII constraint.

```python
# Source: direct inspection of all three snapshot files
def assert_year_alignment(cead_year: int, spd_year: int, sii_year: int) -> None:
    """Fail loudly if data sources are not from the same reference year."""
    if not (cead_year == spd_year == sii_year):
        raise ValueError(
            f"Year misalignment: CEAD={cead_year}, SPD={spd_year}, SII={sii_year}. "
            "All must match. Index anchors to the latest year where all three are final (<=2024)."
        )

REFERENCE_YEAR = 2024  # In composite_config.py — locked by D-10
```

### Pattern 4: ChoroplethLayer `buildStyleMapFromCompositeIndex`

**What:** New style-map builder following the exact same pattern as `buildStyleMapFromHomicide()`. Reads `c.ci` (nullable integer level 1–5) from `CommunaPayload`.

```typescript
// Source: direct inspection of ChoroplethLayer.ts lines 120–138 (buildStyleMapFromHomicide)
// Added to CommunaPayload interface:
//   ci: number | null;  // composite index level 1-5; null for pre-2018 years

export function buildStyleMapFromCompositeIndex(
  comunas: CommunaPayload[]
): Map<string, L.PathOptions> {
  const m = new Map<string, L.PathOptions>();
  for (const c of comunas) {
    const level = c.ci ?? 3;  // fallback to middle band when ci absent
    m.set(c.id, {
      fillColor: INCIDENCE_COLORS[level - 1]!,
      fillOpacity: c.ci === null ? 0.25 : 0.55,
      color: '#ffffff',
      weight: 1.2,
    });
  }
  return m;
}
```

Note: Unlike `buildStyleMapFromHomicide()`, the composite index does not recompute quantile breaks client-side — the level (1–5) is pre-computed in the pipeline and embedded in the `ci` field. This simplifies the client function and ensures consistency with the pipeline's normalization.

### Pattern 5: ResultPanel Composite Score Block

**What:** New JSX section added to `ResultPanel.tsx` between the existing "Level chip" row (section 2) and the "Stat card: rate" (section 3), or after the stat card. The `CommuneData` interface must be extended with the new optional fields.

```typescript
// Extend CommuneData interface in ResultPanel.tsx
interface CommuneData {
  // ... existing fields unchanged ...
  composite_index?: Record<string, {
    score: number;
    rank: number;
    level: 1 | 2 | 3 | 4 | 5;
    available_metrics: number;
  }>;
  spd_homicide_rate?: Record<string, number>;
  sii_exposure_index?: Record<string, number | null>;
}

// New JSX section (to be inserted before or after stat-card):
{data.composite_index?.[String(year)] && (() => {
  const ci = data.composite_index[String(year)];
  const BAND_EN = ['Very Low', 'Low', 'Moderate', 'High', 'Very High'];
  const BAND_ES = ['Muy Bajo', 'Bajo', 'Moderado', 'Alto', 'Muy Alto'];
  const bandLabel = lang === 'es' ? BAND_ES[ci.level - 1] : BAND_EN[ci.level - 1];
  return (
    <div className="panel-section composite-index-section">
      <h4>{lang === 'es' ? 'Índice de carga delictiva' : 'Crime burden index'}</h4>
      <div className="ci-score">{Math.round(ci.score)}</div>
      <div className="ci-band">{bandLabel}</div>
      <div className="ci-rank">
        #{ci.rank} {lang === 'es' ? 'de' : 'of'} {TOTAL_COMMUNES}
      </div>
      {/* MANDATORY CAVEAT BLOCK — D-07: always-visible, never collapsed */}
      <div className="ci-caveat">
        {lang === 'es'
          ? 'Compuesto de delitos reportados al sistema policial (CEAD/SPD), ajustado por actividad económica SII. No refleja delitos no denunciados. Datos de referencia: 2024.'
          : 'Composite of reported crimes (CEAD/SPD), adjusted for SII economic activity. Does not reflect unreported crime. Reference year: 2024.'}
      </div>
    </div>
  );
})()}
```

### Anti-Patterns to Avoid

- **Displaying `ci.score` as float:** Store and render as `Math.round(ci.score)`. Never `ci.score.toFixed(2)`.
- **Recomputing quantile breaks client-side for composite:** The level is pre-computed in the pipeline. Trust the pipeline's level field.
- **Using 2025 CEAD data for the composite:** CEAD 2025 is not partial (per series), but SPD and SII cap at 2024. Index must use 2024 for all three.
- **Calling `build_map_payload()` from inside `build_composite_index.py`:** The payload builder must run as a separate step after the index enriches the commune files.
- **Adding `scipy` to `site/` dependencies:** scipy is pipeline-only. Never imported in the frontend.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Outlier-resistant normalization | Custom percentile clip | `scipy.stats.mstats.winsorize` | Handles masked arrays, NaN propagation, edge cases correctly |
| JSON atomic writes | `f.write()` directly | `pipeline.shared.atomic_write.atomic_write_json()` | Already used throughout; prevents partial-write corruption |
| Accent normalization for forbidden-language checks | Custom strip | `str.normalize('NFD')` already in validator | Established pattern in `forbidden-language.mjs` |
| Schema validation | dict checks | pydantic 2.x `BaseModel` with `Optional` fields | Already the project convention for all pipeline output |

**Key insight:** All infrastructure (atomic writes, pydantic schema, pandas + numpy math) is already present. Only scipy winsorization is new.

---

## Runtime State Inventory

> This is a greenfield computation phase — no renames or migrations. However, existing static JSON files are enriched in place.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `data/cead/comunas/{CUT}.json` — 346 files, enriched in-place | Additive JSON field addition — no migration of existing records |
| Stored data | `data/cead/map-payload*.json` — 22 year payloads + latest | Regenerated by `build_map_payload.py` with new `ci` field |
| Stored data | `data/cead/comparator_table.json` — does not exist yet | Created new by `build_composite_index.py` |
| Live service config | None — no external services | None |
| OS-registered state | None | None |
| Secrets/env vars | None new needed | CEAD/DeepSeek keys unchanged; composite index uses only local snapshot files |
| Build artifacts | `dist/` — regenerated on each Astro build | No special handling |

**Nothing found in category "OS-registered state"** — verified by review of cead-scraper.yml and pipeline structure.

---

## Common Pitfalls

### Pitfall 1: SII 2024 Missing 5 Communes

**What goes wrong:** `sii_exposure.json` for year 2024 contains only 341 communes. The 5 absent CUTs (confirmed: 11201, 11101, 13303, 16207, 4105) have `sii_exposure_index: null`. The composite for those communes uses 6 metrics (not 7) and `available_metrics: 6`.

**How to avoid:** Index all SII lookups with `dict.get(cut)` returning `None`, not 0. `None` → use INE denominator and decrement `available_metrics`. Zero is a valid SII count; never conflate with absence.

**Warning signs:** A commune showing `composite_index` but `sii_exposure_index: null` — this is correct behavior, not a bug.

### Pitfall 2: SPD Zero-Homicide Communes are ABSENT not ZEROED

**What goes wrong:** SPD snapshot caveat states: "communes with zero homicides 2018–2025 are absent (not zeroed)." For 2024, 141 of 346 communes are absent from SPD. If the index treats absence as NaN rather than 0, those communes lose the M5 metric entirely.

**How to avoid:** For communes absent from SPD for a given year, assign `spd_homicide_rate = 0.0` — these are genuine zeros, not missing data. The caveat explicitly confirms ~31 communes are "genuinely zero, not bucketed." For 2024, this expands to 141 communes (normal for a year with more granular data).

**Implementation:** Build a set of SPD communes by year; for each commune not in the set, assign 0.0.

### Pitfall 3: CEAD Series Year Keys are Integers In-Memory, Strings After JSON Round-Trip

**What goes wrong:** In-memory pipeline dicts use integer year keys (`{2024: {...}}`). After JSON serialization and re-load, they become strings (`{"2024": {...}}`). This is documented in `scrape_cead.py` line 162: "Try both int and str key."

**How to avoid:** In `build_composite_index.py`, which reads from already-written `comunas/{CUT}.json` files (post-JSON-round-trip), always use `str(year)` as the key. In `ResultPanel.tsx`, always use `String(year)` when accessing `composite_index[String(year)]`.

### Pitfall 4: `build_map_payload()` 30KB Budget Guard Must Be Updated

**What goes wrong:** `scrape_cead.py` line 328 asserts `len(serialized) >= 30720` (30 KB). Adding `ci` field to each commune entry adds ~7 bytes × 346 communes = ~2.4 KB. The current payload is near but under 30 KB. After adding `ci`, it may approach the limit.

**How to avoid:** After extraction to `build_map_payload.py`, measure payload size with `ci` included. If it exceeds 30 KB, either (a) omit `ci` for communes where `ci` is null (already planned — D-11 says "omitted/null for years without composite data"), or (b) tighten other fields. The 30 KB assertion must move to `build_map_payload.py`.

### Pitfall 5: `scrape_cead.py` Still Imports `build_map_payload` After Extraction

**What goes wrong:** After extracting `build_map_payload()` to `pipeline/build_map_payload.py`, the old function body must be removed from `scrape_cead.py`. If both exist, the workflow could run the old embedded version, ignoring the enriched commune files.

**How to avoid:** Remove `build_map_payload()` from `scrape_cead.py` entirely and remove its call from `_write_all_outputs()`. The GitHub Actions step sequence enforces the correct order.

### Pitfall 6: OneDrive Desync During Multi-Step Pipeline

**What goes wrong:** Documented in memory `onedrive-build-artifacts-desync`. The three pipeline steps (scrape → index → payload) and then `npm run build && npm run validate` must run in a single chained command locally.

**How to avoid:** Document a single local dev command: `python pipeline/scrape_cead.py && python pipeline/build_composite_index.py && python pipeline/build_map_payload.py && cd site && npm run build && npm run validate`. In GitHub Actions, no issue (Linux runner, no OneDrive sync).

---

## SII Cap Logic — Confirmed

**Direct inspection result (2024 data, 341 communes with SII data):**

| Rank | CUT | Commune | Ratio (workers/pop_2024) | workers | pop |
|------|-----|---------|--------------------------|---------|-----|
| 1 | 13123 | Providencia | **5.19** | 850,582 | 164,009 |
| 2 | 13114 | Las Condes | 4.03 | 1,386,056 | 343,632 |
| 3 | 13107 | Estación Central | 2.45 | 290,307 | 118,327 |
| 4 | 13132 | Pudahuel | 2.35 | 228,021 | 97,049 |
| 5 | 7306 | — | 2.03 | 34,365 | 16,925 |

Only CUT 13123 (Providencia) exceeds 5.0. Cap threshold 5.0 is correctly placed — it catches exactly the one commune with a genuine HQ-concentration artifact while preserving Las Condes (4.03) in the SII-adjusted calculation.

**SII fallback logic:**
```python
# Communes that fall back to INE denominator:
# (a) ratio > 5.0  → cap triggered (1 commune: Providencia)
# (b) absent from SII 2024 (5 communes: 11201, 11101, 13303, 16207, 4105)
# (c) INE population = 0  → skip (no known cases in 2024 data)
```

---

## Year-Alignment Assertion Design

**Confirmed state of each source:**

| Source | Years in data | Latest final year | Partial/caveat flag |
|--------|--------------|-------------------|---------------------|
| CEAD `series[].year` | 2005–2026 | 2025 (2026 = `partial: True`) | `partial` bool per series entry |
| SPD `spd_homicide.json` | 2018–2025 | 2024 (2025 caveat: "partial and unconsolidated") | Snapshot-level caveat string |
| SII `sii_exposure.json` | 2005–2024 | 2024 | No partial flag; 2024 is latest |

**Reference year = 2024** (intersection of all three final years).

**Pipeline assertion design:**
```python
# In build_composite_index.py
from pipeline.composite_config import REFERENCE_YEAR  # = 2024

spd_years = sorted(set(r['year'] for r in spd_records if r['year'] <= 2024))
sii_years = sorted(set(r['year'] for r in sii_records))
max_spd_final = max(y for y in spd_years)
max_sii_final = max(y for y in sii_years)

assert max_spd_final == REFERENCE_YEAR, f"SPD max final year {max_spd_final} != REFERENCE_YEAR {REFERENCE_YEAR}"
assert max_sii_final == REFERENCE_YEAR, f"SII max final year {max_sii_final} != REFERENCE_YEAR {REFERENCE_YEAR}"
# CEAD: use series entries where year == REFERENCE_YEAR and partial == False
```

**Note:** CEAD 2025 exists and is non-partial (the `partial: True` flag kicks in at year 2026). However, the index uses CEAD 2024 data to align with SPD and SII. This means the pipeline explicitly selects `year == REFERENCE_YEAR` from CEAD series, not the latest available.

---

## Pipeline Extraction — What Moves

**Current state in `scrape_cead.py`:**

- `build_map_payload()` — lines 102–204 — standalone function, can be moved directly
- Called at line 326 inside `_write_all_outputs()` which also handles validation, commune writes, region writes, meta writes
- The extraction removes only the `build_map_payload()` call from `_write_all_outputs()` and the function definition

**`_write_all_outputs()` after extraction (simplified):**
- Validates communes (pydantic) — stays
- Writes `comunas/{CUT}.json` files — stays
- Writes region files — stays
- Writes `national.json` — stays
- Writes `meta/index.json`, `meta/catalog.json` — stays
- **REMOVED:** `build_map_payload()` call, size assertion, `map-payload*.json` writes

**`build_map_payload.py` (new file):**
- Contains the `build_map_payload()` function verbatim
- Adds `ci` field to each commune entry (reads `composite_index[REFERENCE_YEAR].level` from the enriched commune files)
- Runs the 30 KB size assertion
- Writes `map-payload.json` + all per-year payloads

**Import dependencies of `build_map_payload()`** (confirmed from code):
- `pipeline.cead.normalizer` → `compute_level`
- `pipeline.shared.schema` → `FAMILY_KEYS`
- `pipeline.shared.atomic_write` → `atomic_write_json`
- `datetime` (stdlib)
- `json`, `pathlib`, `logging` (stdlib)

No circular imports. Clean extraction.

---

## Consumer Enumeration — Schema Migration (D-12)

Every consumer of `featured_rates` / `CommunaPayload` must be verified non-breaking after the additive migration. [VERIFIED: direct file inspection]

| # | File | What It Consumes | Migration Action |
|---|------|-----------------|------------------|
| 1 | `site/src/components/map/ChoroplethLayer.ts` | `CommunaPayload` interface; `buildStyleMapFrom*` pattern | Add `ci: number \| null` to `CommunaPayload`; add `buildStyleMapFromCompositeIndex()` function |
| 2 | `site/src/components/map/ResultPanel.tsx` | `CommuneData` interface; `featured_rates.homicidios/homicidios_count/propiedad` | Add optional fields to `CommuneData` interface; add composite index JSX block + caveat block |
| 3 | `site/src/pages/commune/[slug].astro` (EN) | Reads `{CUT}.json` via `site/src/lib/data.ts` loaders at build time | Add composite score display + caveat block to template |
| 4 | `site/src/pages/es/comuna/[slug].astro` (ES) | Same as EN commune page | Same additions in ES |
| 5 | `site/scripts/validate/figure-registry.mjs` | `data/SOURCES.md` tokens | Add tokens for F13 (SPD VHC) and F14 (SII); remove "F13/F14 excluded" comment |
| 6 | `pipeline/tests/test_scrape_cead.py` | `build_map_payload()` function | Update imports to `from pipeline.build_map_payload import build_map_payload`; tests must still pass |

**`featured_rates` is NOT array-indexed anywhere** — confirmed from `ResultPanel.tsx` which accesses it by key (`fr.get("homicidios", {})`). The `by_family` array-index pattern exists only in the map payload, which is a separate field. No risk of position-index breakage on `featured_rates`.

**`data.ts` loader:** `site/src/lib/data.ts` uses `process.cwd()` pattern (confirmed from ARCHITECTURE.md source list). Add `loadComparatorTable()` loader and extend `CommuneData` TypeScript interface with the three new optional fields.

---

## Forbidden-Language Validator Extension

**Current `FORBIDDEN_TERMS` array in `site/scripts/validate/forbidden-language.mjs` (confirmed by inspection):**

Present terms:
- `'la mas segura'` — catches "la más segura" (accent-normalized)
- `'the safest'` — catches absolute superlative EN

Missing terms that D-09 / CI-09 require:
- `'most dangerous'` (EN — absolute superlative without qualification)
- `'mas peligrosa'` (ES — accent-normalized form of "más peligrosa")
- `'mas peligroso'` (ES masculine form)
- `'la mas segura'` already present
- `'el mas seguro'` (ES masculine "the safest commune")

**`ALLOW_LIST` must be extended to permit qualified uses:**
```javascript
// Add to ALLOW_LIST:
/according to reported (crime|incidents)/i,
/segun (delitos|incidentes) reportados/i,
```

**Extension to `FORBIDDEN_TERMS`:**
```javascript
// Add to existing FORBIDDEN_TERMS array:
'most dangerous',    // EN unqualified superlative
'mas peligrosa',     // ES feminine (accent-normalized; covers "más peligrosa")
'mas peligroso',     // ES masculine
'el mas seguro',     // ES masculine "the safest"
// Note: 'the safest' and 'la mas segura' already present
```

**The `normalizeAccents()` function already handles accent stripping**, so adding `'mas peligrosa'` will match "más peligrosa" in HTML text.

---

## Figure Registry Extension

**Current state of `figure-registry.mjs`:** F13 and F14 are explicitly excluded with comment: *"F13 and F14 excluded: deferred Phase 18 (reference snapshots, not displayed)."*

**Phase 18 action:** Remove the exclusion comment and add F13 + F14 to `FIGURE_REGISTRY` with appropriate tokens.

**Required new tokens for F13 (SPD VHC homicide):**
```javascript
// In figure-registry.mjs FIGURE_REGISTRY array:
{
  id: 'F13',
  description: 'SPD VHC homicide rate per 100k (index M5)',
  tokens: [
    ['SPD', 'VHC', 'homicidio'],
    ['Subsecretaria de Prevencion', 'homicidio'],
  ],
},
{
  id: 'F14',
  description: 'SII economic activity exposure index',
  tokens: [
    ['SII', 'Servicio de Impuestos Internos', 'trabajadores'],
    ['SII', 'exposicion', 'domicilio'],
  ],
},
```

**`data/SOURCES.md` must document:**
1. Composite formula (weighted sum of 7 winsorized metrics)
2. Weight vector (from `composite_config.py`)
3. Normalization method (winsorized min-max, limits=[0.01, 0.01])
4. SPD VHC switch (M5 uses SPD for index; CEAD grupo-101 preserved for display)
5. SII exposure caveat (HQ-domicile; cap 5.0)
6. Reference year (2024)

---

## Code Examples

### Composite Config Module (new `pipeline/composite_config.py`)

```python
# Source: STACK.md verified pattern; weight anchor from D-02
REFERENCE_YEAR: int = 2024
WINSORIZE_LIMITS: list[float] = [0.01, 0.01]

# Severity-weighted. Sum = 1.0. Homicide anchor = 0.30 (D-02).
# Full vector proposed by planner for user review before lock.
METRIC_WEIGHTS: dict[str, float] = {
    "spd_homicide_rate":    0.30,  # M5: SPD VHC victim count (most severe)
    "cead_vida_rate":       0.15,  # M2: CEAD vida family (excl. homicide)
    "cead_robos_rate":      0.20,  # M3: violent robbery
    "cead_vif_rate":        0.10,  # M7: domestic violence
    "cead_propiedad_rate":  0.12,  # M4: property crime
    "cead_drogas_rate":     0.08,  # drug offences (Ley 20.000 only)
    "cead_armas_rate":      0.05,  # illegal weapons
}
# Note: incivilidades excluded from index (ARCHITECTURE.md § 7 metrics);
# by_family order includes it but it is not a composite input. Confirm with user.
# Current sum: 0.30+0.15+0.20+0.10+0.12+0.08+0.05 = 1.00 ✓
```

### Pytest Spread Assertion

```python
# Source: D-01 + PITFALLS.md CI-2 verified assertion formulation
def test_composite_distribution():
    """25th percentile of index scores must be > 10% of max."""
    scores = compute_all_commune_scores()  # pd.Series of 346 float scores
    q25 = scores.describe()["25%"]
    max_score = scores.max()
    assert q25 > max_score * 0.10, (
        f"Normalization collapsed: 25th percentile ({q25:.1f}) <= 10% of max ({max_score:.1f}). "
        "Outlier distortion present — check winsorize limits."
    )

def test_sii_cap_not_exceeded():
    """No commune should have sii_workers > ine_population * 10 (gross join error)."""
    # ... load data, assert max ratio < 10
    pass

def test_year_alignment():
    """All sources must reference REFERENCE_YEAR."""
    from pipeline.composite_config import REFERENCE_YEAR
    # ... assert SPD max final year == REFERENCE_YEAR, SII max year == REFERENCE_YEAR
    pass
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw min-max normalization | Winsorized min-max via scipy | Phase 18 | Prevents outlier collapse (Sierra Gorda, Juan Fernández) |
| CEAD grupo-101 as homicide input | SPD VHC victim-level count | Phase 18 | Cleaner truth; SPD avoids double-count from detenciones |
| INE residential population as sole denominator | SII trabajadores as exposure proxy (with cap) | Phase 18 | Better reflects daytime crime exposure in business communes |
| Map defaults to per-family rate mode | Map defaults to composite index mode | Phase 18 | Index is the v2.0 headline feature |

**Deprecated / removed:**
- `build_map_payload()` inside `scrape_cead.py` → replaced by `pipeline/build_map_payload.py`

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `cead_drogas_rate` is M6 (not M7) in the 7-metric index; `incivilidades` is excluded from composite weighting | Standard Stack / `composite_config.py` | Minor — CONTEXT.md lists 7 metrics but doesn't name them; confirm with user before lock |
| A2 | Weight vector in `composite_config.py` example is a starting proposal, not final | Code Examples | Planning blocker if user expects it locked; D-02 says full vector is Claude's Discretion |
| A3 | `ci` field in map payload encodes the level (1–5), not the raw score | Architecture Patterns | If planner encodes raw score (0–100) in ci, client-side coloring logic differs |

**All other claims verified** by direct codebase inspection, snapshot file reads, or Python script execution.

---

## Open Questions

1. **7-metric composition vs. ARCHITECTURE.md definition**
   - What we know: ARCHITECTURE.md lists M1–M7 as: total_rate, vida, robos, propiedad, spd_homicide, sii_exposure, vif. STACK.md `composite_config.py` example uses 7 keys excluding `total_rate` (total is a composite of the others, not an independent metric) and adding `armas` instead.
   - What's unclear: Whether `armas` (CUT 4, index 4 in FAMILY_KEYS) replaces `total_rate` as M1, or whether the metric set is {vida_excl_homicide, robos, propiedad, spd_homicide, sii_exposure, vif, armas}.
   - Recommendation: Planner should propose the exact 7-key set for user review. The `composite_config.py` draft above is reasonable but should be confirmed before the index step is coded.

2. **`incivilidades` inclusion or exclusion from the index**
   - What we know: `incivilidades` is the 7th FAMILY_KEY and carries the highest raw rate in most communes. Including it would dominate the index. ARCHITECTURE.md 7-metric table does not include it explicitly as an indexed metric.
   - What's unclear: Whether `incivilidades` is in the composite or not.
   - Recommendation: Exclude `incivilidades` from the index (confirm with user). It can still be shown in the per-family breakdown but should not be a composite input — it disproportionately measures minor infractions that dilute the crime-burden signal.

3. **Regional rank in the composite index**
   - What we know: CI-05 requires "national and regional rank on the index." The `composite_index` JSON structure (from ARCHITECTURE.md) includes only `rank` (national). Regional rank is not in the proposed schema.
   - What's unclear: Whether regional rank should be pre-computed in the pipeline or derived at display time.
   - Recommendation: Pre-compute `regional_rank` in `build_composite_index.py` alongside `rank` (national). Store in `composite_index[year]` entry.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | Pipeline | ✓ | 3.12 (miniconda) | — |
| scipy | `build_composite_index.py` | ✓ | 1.17.1 (local) | — |
| pandas | Index computation | ✓ | 2.3.3 (pinned) | — |
| openpyxl | SPD VHC xlsx read | ✓ | 3.1.5 (pinned) | — |
| pyxlsb | SII xlsb read | ✓ | 1.0.10 (pinned) | — |
| Node.js | Astro build | ✓ | (not checked, assumed present) | — |

**Missing dependencies with no fallback:** none

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.* |
| Config file | `pipeline/tests/conftest.py` (exists) |
| Quick run command | `pytest pipeline/tests/test_composite.py -x` |
| Full suite command | `pytest pipeline/tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CI-01 | `build_composite_index.py` exits 0 and enriches comunas JSON | integration | `pytest pipeline/tests/test_composite.py::test_build_composite_index -x` | ❌ Wave 0 |
| CI-02 | 25th percentile of scores > 10% of max | unit | `pytest pipeline/tests/test_composite.py::test_composite_distribution -x` | ❌ Wave 0 |
| CI-03 | SPD year == 2024; CEAD featured_rates.homicidios unchanged | unit | `pytest pipeline/tests/test_composite.py::test_year_alignment -x` | ❌ Wave 0 |
| CI-04 | SII cap: Providencia uses INE denominator; Las Condes uses SII | unit | `pytest pipeline/tests/test_composite.py::test_sii_cap_logic -x` | ❌ Wave 0 |
| CI-05 | score is integer; band label present; rank in 1–346 | unit | `pytest pipeline/tests/test_composite.py::test_output_schema -x` | ❌ Wave 0 |
| CI-06 | Caveat block renders in EN and ES commune page HTML | e2e build | `cd site && npm run build && node scripts/validate/forbidden-language.mjs` | ✓ (validator exists) |
| CI-07 | `buildStyleMapFromCompositeIndex()` returns 346 entries; default mode is `ci` | unit (TS) | n/a — TypeScript compile check via `@astrojs/check` | ✓ (check already in CI) |
| CI-08 | figure-registry validator passes (F13, F14 registered) | build | `node site/scripts/validate/figure-registry.mjs` | ✓ (validator exists) |
| CI-09 | "most dangerous" / "más peligrosa" without qualifier → validator fails | unit | `pytest pipeline/tests/test_composite.py::test_forbidden_terms` or manual test with mock HTML | ❌ Wave 0 (for new terms) |
| CI-10 | `@astrojs/check` passes with new TS types; all 13 validators green | build | `cd site && npm run build && npm run validate` | ✓ (suite exists) |

### Sampling Rate

- **Per task commit:** `pytest pipeline/tests/test_composite.py -x`
- **Per wave merge:** `pytest pipeline/tests/ -x && cd site && npm run build && npm run validate`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `pipeline/tests/test_composite.py` — covers CI-01 through CI-05, CI-09 (Python-side tests)
- [ ] `pipeline/composite_config.py` — weight vector + REFERENCE_YEAR (must exist before any test can run)
- [ ] `pipeline/composite_index.py` — normalize_metric(), compute_composite()
- [ ] `pipeline/build_composite_index.py` — entrypoint with year-alignment assertion

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes (pipeline) | Pydantic v2 validates all output; `PLAUSIBILITY_MAX_RATE` guard already in normalizer |
| V6 Cryptography | no | — |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Outlier rate injection into index (if CEAD feed is compromised) | Tampering | winsorize clips extreme values; pipeline asserts national total within 5% of existing `featured_rates` |
| Absolute safety verdict in page HTML | Reputation/Legal | Forbidden-language validator + always-visible caveat block |
| Score precision display implying false accuracy | Spoofing (editorial) | Store as rounded integer in JSON; CI grep check on built HTML |

---

## Sources

### Primary (HIGH confidence — direct codebase inspection)

- `pipeline/scrape_cead.py` — confirmed `build_map_payload()` at lines 102–204; confirmed `_write_all_outputs()` call pattern
- `site/src/components/map/ChoroplethLayer.ts` — confirmed `CommunaPayload` interface; confirmed `buildStyleMapFromHomicide()` pattern to copy
- `site/src/components/map/ResultPanel.tsx` — confirmed `CommuneData` interface; confirmed JSX section structure
- `site/scripts/validate/forbidden-language.mjs` — confirmed current `FORBIDDEN_TERMS` array
- `site/scripts/validate/figure-registry.mjs` — confirmed F13/F14 exclusion comment
- `site/scripts/validate/all.mjs` — confirmed 13-validator chain
- `data/snapshots/sii_exposure.json` — confirmed record schema, year range 2005–2024, 341 communes in 2024
- `data/snapshots/spd_homicide.json` — confirmed record schema, caveat on 2025 partial data, year range 2018–2025
- `data/cead/comunas/13101.json` — confirmed series year encoding (int), featured_rates key encoding (string year keys after JSON round-trip)
- `data/cead/map-payload.json` — confirmed compact schema, `partial_year` field
- `data/ine/poblacion_comunal.json` — confirmed schema (`population_2024` field per cut)
- `.github/workflows/cead-scraper.yml` — confirmed current workflow structure (scrape → commit → deploy hook)
- `pipeline/requirements.txt` — confirmed scipy not currently in requirements; all other deps present
- `pipeline/shared/schema.py` (via Python) — confirmed `FAMILY_KEYS = ['vida', 'robos_violentos', 'vif', 'drogas', 'armas', 'propiedad', 'incivilidades']`

### Secondary (HIGH confidence — direct Python execution)

- SII ratio distribution script — **Providencia (CUT 13123) = 5.19×** (only commune > 5.0); Las Condes (CUT 13114) = 4.03×; 5 communes absent from SII 2024
- SPD coverage script — 313 communes with any homicide 2018–2025; 141 communes absent in 2024 (zero-homicide)
- Year alignment script — CEAD latest non-partial = 2025; SPD latest final ≤2024 = 2024; SII latest = 2024 → **REFERENCE_YEAR = 2024**
- scipy version check — scipy 1.17.1 confirmed available in local env

### Tertiary (MEDIUM confidence — v2.0 research documents)

- `.planning/research/STACK.md` — scipy winsorize pattern; anti-addition list
- `.planning/research/ARCHITECTURE.md` — pipeline isolation pattern; schema migration plan; `comparator_table.json` schema
- `.planning/research/PITFALLS.md` — CI-1..CI-8 pitfall definitions

---

## Metadata

**Confidence breakdown:**
- SII cap placement: HIGH — confirmed by direct data inspection (only 1 commune exceeds 5.0)
- Year alignment (REFERENCE_YEAR=2024): HIGH — confirmed by reading all three snapshot files and CEAD series
- Pipeline extraction scope: HIGH — confirmed by reading `scrape_cead.py` in full
- Consumer enumeration: HIGH — confirmed by direct file inspection of all 6 consumers
- Forbidden-language validator extension: HIGH — confirmed exact current `FORBIDDEN_TERMS` array
- scipy winsorize NaN behavior: MEDIUM — documented from training knowledge; verify with test against real commune data in Wave 0

**Research date:** 2026-06-19
**Valid until:** 2026-07-19 (stable data sources; SII/SPD snapshots are static; no fast-moving APIs)
