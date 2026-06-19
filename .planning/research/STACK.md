# Technology Stack — v2.0 Additions

**Project:** Chile Safety Map (ischilesafe.com)
**Milestone:** v2.0 Composite Index, Comparators & Launch
**Researched:** 2026-06-19
**Scope:** Stack additions only — existing working stack is NOT re-researched.

---

## Verdict Up Front

The existing stack covers almost everything. Only one new Python dep is justified (`scipy` for
winsorization). All three feature tracks (composite index pipeline, index-driven choropleth,
comparator island, A-vs-B programmatic pages) are buildable with current stack + stdlib +
numpy (already pulled transitively by pandas). No new frontend deps needed.

---

## Existing Stack — What Is Already Available

These are confirmed present and sufficient for the new features. Do not add alternatives.

### Python pipeline (`pipeline/requirements.txt` — confirmed pinned)

| Package | Pinned version | Relevant capability for v2.0 |
|---------|---------------|------------------------------|
| pandas | 2.3.3 | DataFrame groupby, merge, percentile/rank, `read_excel` for `.xlsx` (SPD VHC) |
| pyxlsb | 1.0.10 | Read `.xlsb` binary workbooks — SII `PUB_COMU.xlsb` confirmed readable in Phase-17 Wave-0 recon |
| openpyxl | 3.1.5 | Engine for `pandas.read_excel` on `.xlsx` (SPD VHC homicide data) |
| pydantic | 2.13.4 | Schema + validation for composite index output; v2 syntax established |
| tenacity | 9.1.4 | Retry logic (no change) |
| pytest | 8.* | Unit tests for index math |

**numpy** is available as a transitive dependency of pandas 2.x. No explicit pin needed in
`requirements.txt` — pandas guarantees numpy is installed. numpy provides: `np.percentile`,
`np.clip`, `np.log1p`, `np.nanmin`, `np.nanmax`, `np.nanstd` — all needed for normalization
math without any additional library.

### Frontend (`site/package.json` — confirmed pinned)

| Package | Pinned version | Relevant capability for v2.0 |
|---------|---------------|------------------------------|
| astro | 6.4.6 | Programmatic page generation for A-vs-B pages via `getStaticPaths` |
| @astrojs/react | 5.0.7 | React islands for comparator UI |
| react / react-dom | 19.2.7 | Comparator component state management |
| leaflet | 1.9.4 | Index-driven choropleth via native `L.geoJSON()` (same pattern as current) |
| chroma-js | 3.2.0 | Color scale for composite index — `chroma.scale().domain([0, 100])` |
| topojson-client | 3.1.0 | Geometry decoding (unchanged) |
| @astrojs/sitemap | 3.7.3 | Auto-includes A-vs-B pages in sitemap (no change needed) |

---

## New Dependency Required

### `scipy` — winsorization (Python pipeline only)

**Why needed:** Composite crime rates across 346 comunas have extreme outliers. Micro-comunas
like Juan Fernández and Sierra Gorda reach 43,369 per-100k (confirmed — PLAUSIBILITY_MAX_RATE
was raised for this in v1.2). Without winsorization, one or two outlier comunas collapse all
others to the bottom of a min-max scale, making the index useless for differentiation.
`scipy.stats.mstats.winsorize` is the canonical, battle-tested implementation.

Pure-numpy winsorization with `np.percentile` + `np.clip` is technically possible but requires
careful edge-case handling (NaN propagation, limits type coercion, masked-array behavior) that
scipy already solves. On a published safety metric, correctness outweighs dep minimalism.

**Scope:** `pipeline/` only. Never imported in `site/`.

**Version pin:** `scipy>=1.13,<2` — scipy 1.13 is current stable. scipy 2.0 has not been
released; upper bound guards against unknown breaking changes.

**Integration point:** `pipeline/composite_index.py` (new file).

```python
from scipy.stats.mstats import winsorize
rate_winsorized = winsorize(rate_series, limits=[0.01, 0.01])  # clip top/bottom 1%
```

**What scipy does NOT replace:** Nothing currently in the pipeline. It adds winsorization that
is not otherwise available without manual implementation risk.

---

## What Does NOT Need to Be Added

Explicit anti-additions list. Reference this when scope-creep arises during planning.

| Proposed dep | Verdict | Reason |
|---|---|---|
| `scikit-learn` | DO NOT ADD | `StandardScaler`/`MinMaxScaler` are sklearn features, but the same math is 2 lines of numpy. Pulling ~35 MB for one scaler is unjustified. |
| `statsmodels` | DO NOT ADD | No regression, time-series decomposition, or inference. Weights are config-defined, not derived statistically. |
| `pingouin` / `factor_analyzer` | DO NOT ADD | No factor analysis or PCA. Index weights are defined by editorial/methodological config, not data-derived. |
| `pyarrow` | DO NOT ADD | No parquet/columnar format. JSON-in-repo is the data store. pandas reads all inputs fine without arrow. |
| Recharts / Nivo / Chart.js / Victory | DO NOT ADD | Comparator visuals use HTML tables or simple inline SVG. No new charting library for MVP comparator. |
| D3.js (site) | DO NOT ADD | `chroma-js` already handles scale math. Leaflet handles rendering. D3 would duplicate both. |
| `react-leaflet` (site) | DO NOT ADD | Explicitly excluded in CLAUDE.md "What NOT to Use": `<GeoJSON>` component triggers re-render on every hover with 346 features. Use native `L.geoJSON()` inside `useEffect`. |
| `zustand` / `jotai` / Redux (site) | DO NOT ADD | Comparator state is 2–3 selected comunas — trivially covered by React `useState` in a single island. |
| `react-query` / `swr` (site) | DO NOT ADD | No dynamic data fetching. All comparator data is baked into static JSON at build time. |
| Any additional i18n lib | DO NOT ADD | Astro built-in i18n with `getRelativeLocaleUrl()` + locale-keyed JSON strings handles comparator page strings. Two locales do not justify a new dep. |
| `toml` / `tomllib` (pipeline) | DO NOT ADD | Python 3.11+ stdlib includes `tomllib` if TOML config is desired. If using a plain Python dict in `composite_config.py`, no import needed at all. |
| Any backend / database | DO NOT ADD | Composite index is computed once at pipeline run time, output to static JSON in `data/`. No runtime server. |
| `openpyxl` (new addition) | ALREADY PRESENT | Pinned at 3.1.5 — covers SPD VHC xlsx. |
| `pyxlsb` (new addition) | ALREADY PRESENT | Pinned at 1.0.10 — covers SII PUB_COMU.xlsb. |

---

## Composite Index Math — Pure Pandas + Numpy (No Extra Deps Beyond scipy)

```python
# pipeline/composite_index.py  (new file)
import numpy as np
import pandas as pd
from scipy.stats.mstats import winsorize
from pipeline.composite_config import METRIC_WEIGHTS, WINSORIZE_LIMITS

def normalize_metric(series: pd.Series) -> pd.Series:
    """Winsorize then min-max normalize to [0, 100]."""
    arr = np.array(series, dtype=float)
    arr_w = np.array(winsorize(arr, limits=WINSORIZE_LIMITS))
    lo, hi = np.nanmin(arr_w), np.nanmax(arr_w)
    if hi == lo:
        return pd.Series(np.zeros(len(arr)), index=series.index)
    return pd.Series((arr_w - lo) / (hi - lo) * 100, index=series.index)

def compute_composite(df: pd.DataFrame) -> pd.Series:
    """Weighted sum of normalized metrics. df columns = metric keys."""
    total = pd.Series(0.0, index=df.index)
    for metric, weight in METRIC_WEIGHTS.items():
        total += weight * normalize_metric(df[metric])
    return total
```

z-score normalization is equally achievable with `(x - np.nanmean(x)) / np.nanstd(x)` —
pure numpy, no additional dep. The choice between z-score and min-max is a methodology
decision for Phase 18 planning, not a stack decision.

---

## Weighting Config — Pure Python Module

```python
# pipeline/composite_config.py  (new file)
METRIC_WEIGHTS = {
    "homicide_rate":   0.30,   # SPD VHC truth (highest weight, most serious)
    "robbery_rate":    0.20,   # CEAD robos_violentos
    "vif_rate":        0.15,   # CEAD violencia intrafamiliar
    "property_rate":   0.15,   # CEAD propiedad
    "drug_rate":       0.10,   # CEAD drogas (Ley 20.000 only — caveat documented)
    "weapons_rate":    0.05,
    "incivility_rate": 0.05,
}
WINSORIZE_LIMITS = [0.01, 0.01]   # clip top/bottom 1% of each metric
```

No config file format dep needed. A Python module is sufficient and is already the
project's convention for pipeline constants.

---

## A-vs-B Programmatic Pages — Astro `getStaticPaths` (No New Dep)

Standard pattern already used for 346 comunas. Extend to pairwise pages:

```
site/src/pages/compare/[slugA]/[slugB].astro   (EN)
site/src/pages/es/comparar/[slugA]/[slugB].astro   (ES)
```

**Critical constraint:** 346^2 / 2 ≈ 59,685 possible pairs. The Cloudflare Pages free tier
allows 20,000 files per deployment. Current build generates ~791 pages. Adding full cross
pairs would exceed the limit. Phase 18/comparator planning must decide the pair strategy:

- Same-region pairs only: ~500–1,000 pairs — safe
- Top-50 comunas cross-paired: ~1,225 pairs — safe
- Full cross: ~59K pairs — exceeds free tier limit, requires paid CF plan (100K limit)

This is a scope/SEO decision for the roadmap, not a stack problem.

---

## Index-Driven Choropleth — Existing Leaflet + chroma-js Pattern

No new deps. The current choropleth uses `L.geoJSON()` + `chroma-js` for family rates.
The composite index choropleth is identical in structure, switching the value source:

```javascript
// site/src/components/MapIsland.jsx — extend existing switch/layer logic
const indexScale = chroma.scale(['#0f766e', '#ef4444']).domain([0, 100]);

const indexLayer = L.geoJSON(topoData, {
  renderer: L.canvas(),   // existing canvas renderer — keep scoped to this layer
  style: (feature) => ({
    fillColor: indexScale(feature.properties.composite_index ?? 50).hex(),
    // ... existing weight/opacity/stroke props
  }),
  onEachFeature: (feature, layer) => { /* existing popup logic */ }
});
```

`composite_index` per-comuna is baked into `feature.properties` at build time by
`site/scripts/sync-data.mjs` reading `data/index.json` alongside existing `data/comunas/{cut}.json`.

---

## Comparator Island — React `useState` Only (No New Dep)

```jsx
// site/src/components/ComparatorIsland.jsx  (new file)
import { useState } from 'react';

export default function ComparatorIsland({ allComunas, locale }) {
  const [selected, setSelected] = useState([]);   // max 3 CUTs
  // ... render side-by-side metric table
  // Data loaded from allComunas prop (passed from Astro page at build time)
}
```

All data is passed as a prop from the Astro page (static, build-time). No runtime fetch,
no state manager, no query library.

---

## Schema Migration (`featured_rates` → 7-metric) — Pydantic v2 Only

Add fields to the existing Pydantic model in `pipeline/models.py`. Pydantic 2.13.4 handles
optional fields with defaults for backward compatibility with pre-migration JSON files.

```python
# pipeline/models.py — extend ComunaStats or equivalent
class FeaturedRates(BaseModel):
    homicide_rate: float | None = None      # SPD VHC (new)
    robbery_rate: float | None = None
    vif_rate: float | None = None
    property_rate: float | None = None
    drug_rate: float | None = None
    weapons_rate: float | None = None
    incivility_rate: float | None = None
    composite_index: float | None = None    # final weighted score 0–100 (new)
    exposure_proxy: float | None = None     # SII empresas+trabajadores (new, informational)
```

No new dep. Pydantic v2 syntax is already established as the project convention.

---

## Integration Points Summary

| Track | Dir | New files | New dep |
|---|---|---|---|
| Composite index computation | `pipeline/` | `composite_index.py`, `composite_config.py`, `tests/test_composite.py` | `scipy` (winsorize) |
| SII xlsb ingestion | `pipeline/` | Extend existing CEAD scraper or new `ingest_sii.py` | None (pyxlsb present) |
| SPD VHC xlsx ingestion | `pipeline/` | Extend or new `ingest_spd.py` | None (openpyxl present) |
| Index JSON output | `data/` | `data/index.json` (new, same pattern as communas) | None |
| Schema migration | `pipeline/` | `models.py` (extend) | None |
| Index-driven choropleth | `site/src/components/` | `MapIsland.jsx` (extend existing) | None |
| sync-data bridge | `site/scripts/` | `sync-data.mjs` (extend to include `data/index.json`) | None |
| Comparator island | `site/src/components/` | `ComparatorIsland.jsx` (new React island) | None |
| A-vs-B programmatic pages | `site/src/pages/` | `compare/[slugA]/[slugB].astro` + ES equivalent | None |

---

## Updated `pipeline/requirements.txt` — One Line Change

```
# Add to existing pinned file:
scipy>=1.13,<2
```

All other entries remain as-is.

---

## Confidence Assessment

| Area | Confidence | Notes |
|---|---|---|
| Existing stack coverage | HIGH | Both `requirements.txt` and `package.json` read directly from repo |
| numpy availability | HIGH | Pandas 2.x hard-depends on numpy — this is a documented guarantee |
| scipy winsorize API | HIGH | `scipy.stats.mstats.winsorize` is stable across scipy 0.x → 1.x; no breaking change expected |
| Cloudflare file limits | HIGH | 20K free / 100K paid confirmed in CLAUDE.md from Jan 2026 changelog |
| A-vs-B page count risk | HIGH | 59K pairs clearly exceeds free tier; same-region strategy mitigates |
| Pydantic v2 schema extension | HIGH | Established pattern in existing pipeline; optional fields with defaults are stable |

---

## Sources

- `pipeline/requirements.txt` — direct read; pandas 2.3.3, pyxlsb 1.0.10, openpyxl 3.1.5, pydantic 2.13.4 confirmed
- `site/package.json` — direct read; astro 6.4.6, react 19.2.7, leaflet 1.9.4, chroma-js 3.2.0 confirmed
- `.planning/STATE.md` Phase-17 Wave-0 decisions — SII xlsb confirmed readable, SPD VHC xlsx column structure (`COMUN_AGR`, `ID_ANO`) confirmed, CEAD tipoVal additive rule documented
- `pipeline/cache/xlsx_sources_recon.txt` — actual SPD VHC and SII column schemas from live file reads
- CLAUDE.md "What NOT to Use" — react-leaflet `<GeoJSON>` excluded, deprecated model IDs excluded
- CLAUDE.md Cloudflare Pages Limits — 20K free / 100K paid, 20 min build timeout
- scipy `winsorize` docs (training data, HIGH confidence — stable API since scipy 0.14)
- pandas numpy dependency guarantee: pandas 2.x `pyproject.toml` lists numpy as required dep
