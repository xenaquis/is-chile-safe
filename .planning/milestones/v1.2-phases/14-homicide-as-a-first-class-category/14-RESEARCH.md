# Phase 14: Homicide as a First-Class Category — Research

**Researched:** 2026-06-16
**Domain:** CEAD subgroup scraping (Python pipeline) + choropleth bucketing + map filter/panel (React/Leaflet)
**Confidence:** HIGH for codebase-verified findings; MEDIUM for CEAD live-endpoint behavior (requires runtime confirmation)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Scrape CEAD subgroup 101 in this phase; two-stage: data first, UI second.
- **D-02:** Full historical series 2005–2025; store into each comuna's `series` AND `featured_rates.homicidios_by_year`.
- **D-03:** Fetch BOTH measures — rate (`medida=2`) AND absolute count (`medida=1`). Roughly doubles subgroup request count. Keep existing courtesy delays. Research checkpoint: confirm the exact CEAD param for subgroup 101 and whether count+rate need two requests or one.
- **D-04:** Homicide appears as an 8th chip in `FiltersRow.tsx`; reuses `featured` accent-dot treatment.
- **D-05:** Homicide layer gets an independent color scale. Research: recommend bucketing method for sparse, right-skewed, low-count distribution.
- **D-06:** Separate homicide figure in `ResultPanel.tsx`; no regression to family bars.
- **D-07:** Panel shows rate-per-100k + absolute count + CEAD year. Zero must be explicit "no reported cases," non-alarmist.

### Claude's Discretion
- Exact bucketing algorithm for D-05 (research-recommended).
- Whether 8th chip reuses `featured` flag path or new field in `CHIP_DEFS`.
- Panel layout/placement of homicide figure within `ResultPanel.tsx`.

### Deferred Ideas (OUT OF SCOPE)
- `secuestros` subgroup as first-class category (subgroup ID unconfirmed).
- Crime-type SEO ranking pages for homicide (Phase 15, CSEO-01/02).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HOM-01 | `homicidios` (subgrupo destacado 101) seleccionable como filtro/capa propia con su coroplético, distinto de "vida"; pipeline emite la tasa de homicidios por comuna al map-payload. | §CEAD Subgroup Fetch, §Payload Shape, §Choropleth Bucketing, §Frontend Wiring |
| HOM-02 | El panel de comuna muestra cifra/desglose de homicidios separado (no solo "vida" agregada), con fuente CEAD + año; sin regresión al render de familias. | §ResultPanel Integration, §Payload Shape, §Schema Changes |
</phase_requirements>

---

## Summary

Phase 14 has two hard-sequential stages: (1) CEAD subgroup-101 data acquisition — scraping homicide rates AND counts for all 346 comunas across 2005–2025, normalizing into the per-commune JSON files, and emitting a new `homicide` field in the map-payload; then (2) the frontend — an 8th chip in `FiltersRow`, an independent choropleth for the homicide layer, and a homicide figure in `ResultPanel`.

The codebase is well-structured for this extension. The pipeline has a clear fetch+accumulate loop in `scrape_cead.py::_run_pipeline` that only needs a parallel subgroup-101 loop added. The normalizer already has `FEATURED_SUBGROUPS = {"homicidios": 101}` and `attach_featured` expects `homicidios_by_year` — the scaffolding is there, the data just isn't scraped yet. The frontend `CHIP_DEFS` and `ChoroplethLayer.ts` have clean extension points: homicide is NOT a family so it cannot use `familyIndex` → `by_family[N]`; instead it requires a dedicated `homicide_rate` field on each payload entry, and `buildStyleMapFromFamily` is replaced by a new `buildStyleMapFromHomicide` function that reads that field.

**Primary recommendation:** Add a `subgroup-101` fetch loop parallel to the existing family loop in `scrape_cead.py`. Extend the map-payload `CommunaPayload` entry with `homicide_rate: number | null`. Use **quantile bucketing on non-zero values only** for the choropleth, which already exists in `computeQuantileBreaks`. The 8th chip in `CHIP_DEFS` uses `familyIndex: null` and a new sentinel key `'homicidios'` to trigger the homicide code path in `MapIsland`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Subgroup-101 CEAD scrape | Pipeline (Python) | — | Rate+count fetched from CEAD POST endpoint, normalized to JSON |
| Homicide series storage | Pipeline (Python) | — | Written to `data/cead/comunas/{cut}.json` featured_rates + series |
| Map-payload emission | Pipeline (Python) | — | `build_map_payload` emits compact per-year JSON; homicide_rate added here |
| Choropleth layer/buckets | Browser (React island) | — | `ChoroplethLayer.ts` `buildStyleMapFrom*` functions, client-side quantile |
| 8th filter chip | Browser (React island) | — | `FiltersRow.tsx` CHIP_DEFS array |
| Panel homicide figure | Browser (React island) | — | `ResultPanel.tsx` reads per-commune JSON `featured_rates.homicidios` |
| Build validation | Build-time (Node.js) | — | `site/scripts/validate/map.mjs` new assertion |

---

## Standard Stack

No new packages required. All dependencies already present: [VERIFIED: codebase inspection]

| Tool | File | Already Installed |
|------|------|-------------------|
| `requests` + `tenacity` | pipeline/cead/client.py | Yes |
| `beautifulsoup4` + `lxml` | pipeline/cead/parser.py | Yes |
| `chroma-js` | site/src/components/map/colors.ts | Yes |
| React + Leaflet | site/src/components/map/ | Yes |

---

## CEAD Subgroup-101 Scrape Mechanics (D-03 Research Checkpoint)

### What the current code does

`pipeline/cead/client.py::fetch_communes_batch` (line 82) sends a POST to
`get_estadisticas_delictuales.php` with these relevant params: [VERIFIED: file inspection]

```python
payload = {
    "medida": "2",          # rates per 100k
    "tipoVal": "1,2",       # police cases
    "anio[]": str(year),
    "familia[]": str(familia_id),   # 1-7 — the ONLY crime selector
    "seleccion": "1",
    "descarga": "true",
}
```

There is NO `subgrupo[]` parameter in the current call. The `scrape_cead.py` family fetch loop (lines 343–403) iterates `FAMILIA_IDS` (1–7) and only passes `familia_id`.

### How subgroup 101 fits into the CEAD taxonomy

From `como scrap.txt` (the original scraping analysis): [VERIFIED: file inspection]

```
medida     = 1 (frecuencia) | 2 (tasa c/100k hab)
familia[]  = 1-7, 99
grupo[]    = (opcional)
subgrupo[] = (opcional)
```

The CEAD endpoint accepts an optional `subgrupo[]` parameter alongside `familia[]`. Homicide (subgrupo 101) lives inside **familia 1** ("Delitos contra la vida" = `vida`). Subgrupo 101 is labeled `homicidios` in the CEAD taxonomy (confirmed by `normalizer.py line 27`: `FEATURED_SUBGROUPS = {"homicidios": 101}`). [VERIFIED: file inspection]

**The catalog.py `seleccion=101` is a completely different parameter** — it is sent to `ajax_2.php` (the catalog endpoint) to get the commune list, not to the data endpoint. Do not confuse the two. [VERIFIED: catalog.py inspection, lines 67-69]

### Hypothesis: how to fetch subgroup 101

**ASSUMED** — cannot confirm against live CEAD without a live request:

To target subgroup 101, the POST to `get_estadisticas_delictuales.php` likely requires:

```python
payload = {
    "medida": "2",           # for rate
    "tipoVal": "1,2",
    "anio[]": str(year),
    "familia[]": "1",        # vida family — subgrupo 101 is inside familia 1
    "subgrupo[]": "101",     # the homicide subgroup
    "seleccion": "1",        # commune-level
    "descarga": "true",
}
```

For absolute count (`medida=1`), the same POST with `"medida": "1"`.

### Whether count + rate need one or two requests

**ASSUMED** — cannot confirm without live testing:

Based on how CEAD generally works (single `medida` value per request), count and rate likely require **two separate requests** — one with `medida=2` (rate) and one with `medida=1` (count). The `parse_cead_table` function will parse either response identically; the difference is in what the numbers mean.

### Runtime experiment required (executor MUST run)

This is a **hard prerequisite** before coding the fetch loop. The executor must run:

```python
# pipeline/scratch/test_subgroup101.py  (delete after confirming)
import sys; sys.path.insert(0, '.')
from pipeline.cead.client import make_cead_session, _DATA_ENDPOINT
import requests, json

session = make_cead_session()

# Test A: rata subgrupo 101
r = session.post(_DATA_ENDPOINT, data={
    "medida": "2",
    "tipoVal": "1,2",
    "anio[]": "2024",
    "familia[]": "1",
    "subgrupo[]": "101",
    "seleccion": "1",
    "descarga": "true",
    "comuna[]": ["13101", "13102"],
    "region[]": "13",
})
print("STATUS A:", r.status_code, "SIZE:", len(r.content))
open("pipeline/cache/test_subgroup101_rate.html", "wb").write(r.content)

# Test B: frecuencia subgrupo 101
r2 = session.post(_DATA_ENDPOINT, data={
    "medida": "1",
    "tipoVal": "1,2",
    "anio[]": "2024",
    "familia[]": "1",
    "subgrupo[]": "101",
    "seleccion": "1",
    "descarga": "true",
    "comuna[]": ["13101", "13102"],
    "region[]": "13",
})
print("STATUS B:", r2.status_code, "SIZE:", len(r2.content))
open("pipeline/cache/test_subgroup101_count.html", "wb").write(r2.content)
```

Confirm: (1) response has commune rows (`formato_4`), (2) numbers are plausible homicide rates (single digits per 100k for Santiago), (3) medida=1 returns absolute counts (small integers: 1–50 range). If `subgrupo[]` does not work, try `grupo[]` instead.

### Fallback hypothesis

If `subgrupo[]` is rejected by the endpoint, the alternative is `grupo[]`. The CEAD taxonomy has groups between families and subgroups; homicide subgroup 101 may belong to a group with a different integer ID. The executor must inspect the HTML response from the failing request and check if CEAD returns any data at all or an empty table.

---

## Payload Shape: Adding Homicide Without Breaking by_family Contract

### Current payload entry [VERIFIED: codebase + live data inspection]

```json
{
  "id": "5602",
  "rate": 10567,
  "level": 5,
  "by_family": [1994, 295, 1043, 129, 221, 3301, 3584]
}
```

`by_family` is a **7-element ordered int array** matching `FAMILY_KEYS`:
`["vida", "robos_violentos", "vif", "drogas", "armas", "propiedad", "incivilidades"]`
[VERIFIED: schema.py FAMILY_KEYS, scrape_cead.py line 133]

Current payload size: **27,527 bytes** (limit: 30,720 bytes = 30 KB). Adding homicide leaves **3,193 bytes of headroom**. [VERIFIED: live measurement]

### Decision: homicide rides as a SEPARATE field, NOT `by_family[7]`

Appending to `by_family` would break the array-index contract used by `FiltersRow.tsx` (`familyIndex` maps to array position) and `ChoroplethLayer.ts::buildStyleMapFromFamily`. It would also break `PanelFamilyBars.tsx` which expects exactly 7 entries. [VERIFIED: FiltersRow.tsx lines 30-39, ChoroplethLayer.ts line 90]

**Recommended payload extension:**

```json
{
  "id": "13101",
  "rate": 8432,
  "level": 3,
  "by_family": [1442, 2118, 359, 76, 49, 6273, 9163],
  "homicide_rate": 12,
  "homicide_count": 8
}
```

Both values as integers (same rounding as existing `by_family` entries). A `null` value when data is missing (not 0, to distinguish "scraped zero" from "no data").

**Budget impact:** 2 extra integers per commune × 346 communes ≈ +3,000 bytes maximum (each `,"homicide_rate":NNN,"homicide_count":NN` is ~30 chars worst case). This stays under the 30 KB limit. [ASSUMED — estimate; executor must verify with actual data]

### Schema changes required

**`pipeline/shared/schema.py` — `MapPayloadEntry`:** Add two optional fields:

```python
class MapPayloadEntry(BaseModel):
    id: str
    rate: float
    level: int
    by_family: list[float | None]
    homicide_rate: int | None = None
    homicide_count: int | None = None
```

**`pipeline/shared/schema.py` — `YearRecord`:** Add homicide_count to the per-year commune record (rate already lives in `featured_rates.homicidios`):

```python
class YearRecord(BaseModel):
    year: int
    rate_per_100k: float
    by_family: dict[str, float | None]
    partial: bool = False
    homicide_count: int | None = None   # NEW — absolute cases from medida=1
    homicide_rate: float | None = None  # NEW — rate per 100k from medida=2
```

Alternatively, store both in `featured_rates.homicidios_by_year` as a dict of `{year: {rate, count}}`. The CONTEXT.md normalizer shows `featured_rates.homicidios` currently stores `{year: rate}`. For D-07 (panel needs both), the per-commune JSON must carry both rate and count. Two approaches:
- Option A: `featured_rates.homicidios` stays `{year: rate}` and a NEW `featured_rates.homicidios_count` carries `{year: count}`.
- Option B: `featured_rates.homicidios` becomes `{year: {rate, count}}` — breaking change to the existing key contract.

**Recommendation (Claude's Discretion):** Option A — non-breaking, simpler schema evolution. The `attach_featured` function in `normalizer.py` already returns `featured_rates.homicidios = dict(commune_data.get("homicidios_by_year", {}))`. Adding a parallel `homicidios_count` key is minimal. The `CommuneData` TypeScript interface in `data.ts` (line 44) types `homicidios: Record<string, number>` — adding `homicidios_count: Record<string, number>` is a one-line extension.

---

## Pipeline Changes: Where to Add the Subgroup Fetch

### New function in `pipeline/cead/client.py`

Add alongside `fetch_communes_batch`:

```python
def fetch_subgroup_batch(
    session: requests.Session,
    cut_codes: list[str],
    year: int,
    familia_id: int,
    subgrupo_id: int,
    medida: str = "2",   # "2"=rate, "1"=count
) -> str:
    """Fetch CEAD data for a specific subgroup (e.g. homicidios=101).

    Unlike fetch_communes_batch which takes familia_id only, this adds
    subgrupo[] to target the specific subgroup within the family.
    medida="2" for rate per 100k; medida="1" for absolute count.
    """
    payload: dict = {
        "medida": medida,
        "tipoVal": "1,2",
        "anio[]": str(year),
        "familia[]": str(familia_id),
        "subgrupo[]": str(subgrupo_id),
        "seleccion": "1",
        "descarga": "true",
    }
    payload["comuna[]"] = [str(cut) for cut in cut_codes]
    payload["region[]"] = str(cut_codes[0])[:2]

    response = _post_with_retry(session, _DATA_ENDPOINT, payload)
    return response.content.decode("latin-1")
```

### New accumulator loop in `scrape_cead.py::_run_pipeline`

After the existing family loop (lines 343–403), add a parallel subgroup loop. The subgroup fetch only needs to cover familia=1 (vida) + subgrupo=101 (homicidios). It iterates the same years (2005–2025) with the same courtesy delay:

```python
# --- Subgroup-101 (homicidios) fetch ---
# Accumulator: {cut: {year: {rate: float|None, count: int|None}}}
homicide_accumulator: dict[str, dict[int, dict]] = {cut: {} for cut in catalog}

for year in range(start_year, current_year + 1):
    # Fetch rate (medida=2)
    cache_key_rate = f"cead_subgroup101_{year}_rate.html"
    html_rate = load_cached(cache_key_rate)
    if html_rate is None:
        html_rate = fetch_subgroup_batch(session, list(catalog.keys()), year,
                                         familia_id=1, subgrupo_id=101, medida="2")
        cache_raw(cache_key_rate, html_rate)
        time.sleep(2.5)

    # Fetch count (medida=1)
    cache_key_count = f"cead_subgroup101_{year}_count.html"
    html_count = load_cached(cache_key_count)
    if html_count is None:
        html_count = fetch_subgroup_batch(session, list(catalog.keys()), year,
                                          familia_id=1, subgrupo_id=101, medida="1")
        cache_raw(cache_key_count, html_count)
        time.sleep(2.5)

    rows_rate = parse_cead_table(html_rate)
    rows_count = parse_cead_table(html_count)

    # Merge into accumulator
    for row in rows_rate:
        cut = _match_cut(row["name"], catalog)
        if cut is None: continue
        rate_str = row["values"].get(str(year))
        rate = parse_cead_float(rate_str) if rate_str else None
        homicide_accumulator[cut].setdefault(year, {})["rate"] = rate

    for row in rows_count:
        cut = _match_cut(row["name"], catalog)
        if cut is None: continue
        count_str = row["values"].get(str(year))
        count_raw = parse_cead_float(count_str) if count_str else None
        count = int(round(count_raw)) if count_raw is not None else None
        homicide_accumulator[cut].setdefault(year, {})["count"] = count
```

Then in the commune-building loop (lines 410–465), populate `homicidios_by_year` and `homicidios_count_by_year` from `homicide_accumulator[cut]`:

```python
homicidios_by_year = {
    yr: data["rate"]
    for yr, data in homicide_accumulator.get(cut, {}).items()
    if data.get("rate") is not None
}
homicidios_count_by_year = {
    yr: data["count"]
    for yr, data in homicide_accumulator.get(cut, {}).items()
    if data.get("count") is not None
}

featured = attach_featured({
    "propiedad_by_year": {...},
    "vida_by_year": {...},
    "homicidios_by_year": homicidios_by_year,    # was {}
    "secuestros_by_year": {},
})
# Add count separately:
featured["homicidios_count"] = homicidios_count_by_year
```

### `build_map_payload` extension in `scrape_cead.py` (line 88)

After computing `by_family_list`, add:

```python
# Homicide rate+count for map payload (D-03 / D-07)
featured = r.get("featured_rates", {})
homicidios_by_year = featured.get("homicidios", {})
homicidios_count_by_year = featured.get("homicidios_count", {})
hom_rate = homicidios_by_year.get(str(year)) or homicidios_by_year.get(year)
hom_count = homicidios_count_by_year.get(str(year)) or homicidios_count_by_year.get(year)

comunas.append({
    "id": r["id"],
    "rate": int(round(rate)),
    "level": level,
    "by_family": by_family_list,
    "homicide_rate": int(round(hom_rate)) if hom_rate is not None else None,
    "homicide_count": int(hom_count) if hom_count is not None else None,
})
```

---

## Choropleth Bucketing for Homicide Rates (D-05)

### Nature of the distribution

Homicide rates in Chilean comunas are:
- **Sparse:** many small comunas have 0 homicides in a given year (population < 5,000 makes any homicide produce a rate spike, e.g. 1 case in pop=2,000 → 50/100k)
- **Right-skewed:** most comunas cluster 0–15/100k; outlier comunas (rural high-crime or high-transient-population) reach 50–100/100k
- **Low count:** Santiago 2024 likely ~5-12/100k; national average is on the order of 5/100k — vs family rates of 200–10,000/100k

[ASSUMED — based on known Chilean homicide statistics; actual distribution must be measured from scraped data]

### Recommendation: quantile bucketing on non-zero values only

**Use the existing `computeQuantileBreaks` function from `colors.ts`** (which the current choropleth already uses for the main layer), applied ONLY to non-zero homicide rates. This is:

1. **Already implemented:** `computeQuantileBreaks(rates.filter(r => r > 0), 5)` — identical to line 187-189 of `MapIsland.tsx`.
2. **Handles the zero-cluster correctly:** all comunas with `homicide_rate === 0` or `null` fall into level 1 (lowest), rendered with `INCIDENCE_COLORS[0]` (lightest teal). The legend can label level 1 as "0 or no data."
3. **Self-calibrating:** if 60% of comunas have 0 homicides, the 5 quantile buckets are computed across the 40% that have non-zero rates — spreading meaningful variation across the full color scale rather than collapsing everything to bucket 1.

**Why NOT Jenks/natural-breaks:** Jenks requires a dedicated library (e.g. `simple-statistics`). The project has no such dependency. Quantile on non-zero values achieves the same goal (spreading the distribution) without a new package.

**Why NOT fixed thresholds (e.g. 0, 3, 6, 12, 25/100k):** CEAD data quality and Chilean homicide trends may shift; fixed thresholds require manual maintenance. Quantile is self-calibrating and consistent with the existing pattern.

### Zero-homicide communes: display treatment

- `homicide_rate === 0` or `homicide_rate === null`: map to level 1 (lightest color, `INCIDENCE_COLORS[0]`)
- Panel: render as explicit `"0 casos reportados (CEAD {year})"` / `"0 reported cases (CEAD {year})"` — never blank
- A `null` value means "data not scraped / CEAD returned no data" — render as `"—"` rather than "0" to avoid implying confirmed zero

### Python-side level computation for homicide

Add a new `compute_homicide_level` function to `normalizer.py` (or reuse `compute_level` with a separate `all_rates` list):

```python
def compute_homicide_level(rate: float | None, all_hom_rates: list[float]) -> int:
    """Compute 1-5 level for homicide rate using non-zero quantile bucketing."""
    if rate is None or rate == 0:
        return 1
    non_zero = [r for r in all_hom_rates if r > 0]
    return compute_level(rate, non_zero)  # reuse existing compute_level
```

This is called during `build_map_payload` when computing `homicide_level` (a third optional field on the payload entry — needed for the choropleth when the homicide layer is active). However, client-side quantile computation in `colors.ts::computeQuantileBreaks` already handles this. **Recommendation (Claude's Discretion):** do NOT add `homicide_level` to the payload; instead compute it client-side in `MapIsland` the same way `buildStyleMapFromFamily` computes levels on the fly. Keeps the payload smaller.

---

## Frontend Wiring

### FiltersRow.tsx: 8th chip

`CHIP_DEFS` (line 30) is a plain array. Add one entry: [VERIFIED: FiltersRow.tsx inspection]

```tsx
{ key: 'homicidios', familyIndex: null, labelEs: 'Homicidios', labelEn: 'Homicide', featured: true },
```

`familyIndex: null` signals to `MapIsland` that this is NOT a `by_family` index. The `key: 'homicidios'` sentinel drives a new code path.

The `onFamilyChange` callback in `MapIsland` receives `(key, index)`. The existing crime-family effect (line 277) branches on `crimeFamilyIndex !== null`. When `key === 'homicidios'`, both `familyIndex` should be `null` AND a new state variable `crimeIsHomicide: boolean` should be set. Alternatively, use `crimeFamilyIndex === -1` as a sentinel (avoids a new state variable). [Claude's Discretion]

The `title` tooltip lookup at line 80 (`FAMILY_DEFS_EN[key]` / `FAMILY_DEFS_ES[key]`) will need homicide entries added to `familyDefs.ts`.

### familyDefs.ts: add homicide label and definition

Current exports: `FAMILY_ORDER`, `FAMILY_LABELS_EN`, `FAMILY_LABELS_ES`, `FAMILY_DEFS_EN`, `FAMILY_DEFS_ES`. [VERIFIED: familyDefs.ts inspection]

Add to each dict:

```typescript
// FAMILY_LABELS_EN
homicidios: 'Homicide',

// FAMILY_LABELS_ES
homicidios: 'Homicidios',

// FAMILY_DEFS_EN (sober, non-alarmist, CEAD-cited)
homicidios: 'Reported homicide cases disaggregated by commune, sourced from CEAD official police statistics (subgroup 101 within Life Crimes family).',

// FAMILY_DEFS_ES
homicidios: 'Casos de homicidio reportados desagregados por comuna, según estadísticas policiales oficiales del CEAD (subgrupo 101 dentro de Delitos contra la Vida).',
```

`FAMILY_ORDER` does NOT need homicidios — it is used for crime-type SEO pages (Phase 15), not for the filter chip. [VERIFIED: familyDefs.ts line 7]

### ChoroplethLayer.ts: new buildStyleMapFromHomicide

Add alongside `buildStyleMapFromFamily` (line 86): [VERIFIED: ChoroplethLayer.ts inspection]

```typescript
/**
 * Build style map from homicide_rate field on payload entries.
 * Uses quantile bucketing on non-zero rates — independent of main scale.
 */
export function buildStyleMapFromHomicide(
  comunas: CommunaPayload[]
): Map<string, L.PathOptions> {
  const rates = comunas.map((c) => (c as HomicidePayload).homicide_rate ?? 0);
  const positiveRates = rates.filter((r) => r > 0);
  const breaks = computeQuantileBreaks(positiveRates, 5);
  const m = new Map<string, L.PathOptions>();
  for (const c of comunas) {
    const rate = (c as HomicidePayload).homicide_rate ?? 0;
    const level = levelFromBreaks(rate, breaks);
    m.set(c.id, {
      fillColor: INCIDENCE_COLORS[level - 1]!,
      fillOpacity: rate === 0 ? 0.25 : 0.55,  // visually distinguish zero-homicide
      color: '#ffffff',
      weight: 1.2,
    });
  }
  return m;
}
```

The `CommunaPayload` type in `ChoroplethLayer.ts` (line 13) must be extended:

```typescript
export interface CommunaPayload {
  id: string;
  rate: number;
  level: 1 | 2 | 3 | 4 | 5;
  by_family: number[];
  homicide_rate: number | null;    // NEW
  homicide_count: number | null;   // NEW
}
```

### MapIsland.tsx: homicide chip effect

The crime-family chip effect at line 277 currently reads `crimeFamilyIndex`. For homicide, the pattern is:

```typescript
// Add a new boolean state:
const [crimeIsHomicide, setCrimeIsHomicide] = useState(false);

// In the onFamilyChange handler passed to FiltersRow:
function handleFamilyChange(key: string | null, index: number | null) {
  setCrimeFamily(key);
  setCrimeFamilyIndex(index);
  setCrimeIsHomicide(key === 'homicidios');
}

// In the chip recolor effect:
if (crimeIsHomicide) {
  styleMapRef.current = buildStyleMapFromHomicide(communas);
} else if (crimeFamilyIndex !== null) {
  styleMapRef.current = buildStyleMapFromFamily(communas, crimeFamilyIndex);
} else {
  styleMapRef.current = buildStyleMapFromLevel(communas);
}
```

Also update the `Legend` component to show the homicide-specific breaks when `crimeIsHomicide` is true — pass `isHomicide` flag or re-compute `breaks` from homicide rates.

### ResultPanel.tsx: homicide figure (D-06/D-07)

`CommuneData` in `data.ts` already types `featured_rates.homicidios: Record<string, number>`. [VERIFIED: data.ts line 44]

The `ResultPanel` component fetches `/data/cead/comunas/{cut}.json` on open (line 113). After adding `homicidios_count` to `featured_rates`, the panel can render the figure.

**Recommended placement:** After the family breakdown section (section 6), before incidents (section 7). Add a new section:

```tsx
{/* 6b. Homicide breakdown */}
{(() => {
  const hom = data.featured_rates?.homicidios;
  const homCount = data.featured_rates?.homicidios_count;
  const homRate = hom ? hom[String(year)] ?? null : null;
  const count = homCount ? homCount[String(year)] ?? null : null;
  return (
    <div className="panel-section">
      <h4>{lang === 'es' ? `Homicidios (${year})` : `Homicide (${year})`}</h4>
      {homRate !== null ? (
        <div>
          <span className="stat-mid">{Math.round(homRate).toLocaleString('es-CL')}</span>
          {lang === 'es' ? ' por 100.000 hab.' : ' per 100,000 inhab.'}
          {count !== null && (
            <span className="stat-sub">
              {' '}({count} {lang === 'es' ? 'caso' + (count === 1 ? '' : 's') : count === 1 ? 'case' : 'cases'})
            </span>
          )}
        </div>
      ) : (
        <p style={{color: 'var(--muted)'}}>
          {lang === 'es'
            ? `Sin casos reportados — CEAD ${year}`
            : `No reported cases — CEAD ${year}`}
        </p>
      )}
      <div className="official-row" style={{fontSize: '0.78rem', marginTop: 4}}>
        {lang === 'es'
          ? `Fuente: CEAD, subgrupo 101 Delitos contra la Vida (${year})`
          : `Source: CEAD, subgroup 101 Life Crimes (${year})`}
      </div>
    </div>
  );
})()}
```

**PanelFamilyBars regression guard:** `PanelFamilyBars` receives `byFamily: number[]` (7-element array). Nothing in this phase touches that array or that component. The family bars continue to show the 7 aggregated family rates including `vida` (which includes homicide). The new homicide section is additive. [VERIFIED: ResultPanel.tsx line 309, PanelFamilyBars import]

---

## Build Validator Changes

`site/scripts/validate/map.mjs` currently checks: TopoJSON budget, map page existence, island markers, aria-labels, zero-React guard, runtime data assets. [VERIFIED: map.mjs inspection]

Add two new assertions (can be added as Check 8 at the bottom of map.mjs):

```javascript
// Check 8: Homicide data presence in map-payload
const MAP_PAYLOAD_PATH = path.join(REPO_ROOT, 'data', 'cead', 'map-payload.json');
if (existsSync(MAP_PAYLOAD_PATH)) {
  const payload = JSON.parse(readFileSync(MAP_PAYLOAD_PATH, 'utf8'));
  const sample = payload.comunas?.slice(0, 10) ?? [];
  const hasHomicide = sample.some(c => 'homicide_rate' in c);
  if (!hasHomicide) {
    fail('homicide data in payload', 'map-payload.json comunas missing homicide_rate field — subgroup-101 scrape may not have run');
  } else {
    pass('homicide data in payload');
  }
}

// Check 9: Homicide data in a sample commune file (13101 = Santiago)
const SANTIAGO_PATH = path.join(REPO_ROOT, 'data', 'cead', 'comunas', '13101.json');
if (existsSync(SANTIAGO_PATH)) {
  const com = JSON.parse(readFileSync(SANTIAGO_PATH, 'utf8'));
  const hom = com.featured_rates?.homicidios ?? {};
  if (Object.keys(hom).length === 0) {
    fail('homicide in 13101.json', 'Santiago featured_rates.homicidios is empty — subgroup-101 scrape needed');
  } else {
    pass(`homicide in 13101.json (${Object.keys(hom).length} years)`);
  }
}
```

---

## Common Pitfalls

### Pitfall 1: `subgrupo[]` param does not work — CEAD rejects or ignores it

**What goes wrong:** POST to `get_estadisticas_delictuales.php` with `subgrupo[]=101` returns an empty HTML table or the full `vida` family aggregate (ignoring the subgroup filter).

**Why it happens:** CEAD endpoint parameters are undocumented; `subgrupo[]` was identified from the original scraping analysis (`como scrap.txt`) but not confirmed with a live request.

**How to avoid:** Run the runtime experiment (see §CEAD Subgroup-101) before writing the fetch loop. If `subgrupo[]` returns 0 rows, try `grupo[]` instead. If neither works, the fallback is to fetch `familia[]=1` (vida full aggregate) and check if CEAD offers a subgroup drill-down via a different parameter combination.

**Warning signs:** Response HTML table has 0 `formato_4` rows, or all values are identical to `familia=1` (full vida aggregate).

### Pitfall 2: `medida=1` (count) vs `medida=2` (rate) confusion in parser

**What goes wrong:** `parse_cead_table` returns the same structure regardless of `medida`. If you accidentally write the count response values into the `rate` field, you get raw case numbers (e.g., 15) stored as rates (should be ~5/100k for Santiago).

**How to avoid:** Use separate cache keys (`cead_subgroup101_{year}_rate.html` vs `_count.html`) and separate accumulator fields (`"rate"` vs `"count"`). Assert plausibility: rates for homicide should be < 200/100k even for high-crime comunas; counts should be < 1000.

**Warning signs:** Map shows Santiago with `homicide_rate=15` but expected `~5.0`; the `15` is actually the absolute case count.

### Pitfall 3: `homicide_rate` breaks 30KB payload limit

**What goes wrong:** Adding two int fields per commune to 346 entries pushes the payload over 30,720 bytes.

**How to avoid:** Current payload is 27,527 bytes with 3,193 bytes of headroom. Two ints per commune × 346 ≈ max ~3,000 bytes. It is tight. Use `None` (serialized as `null`, 4 bytes) for missing values — do NOT use `0` which is ambiguous. After adding the fields, re-run the `len(serialized) >= 30720` check in `scrape_cead.py::_write_all_outputs` (line 269).

**Warning signs:** Pipeline fails with `ValueError: map-payload.json exceeds 30 KB limit`.

**Mitigation if over budget:** Emit `homicide_rate` only (drop `homicide_count` from payload; the count is already in the per-commune `/data/cead/comunas/{cut}.json` file which the panel fetches separately). The panel reads the per-commune file anyway for the count display; the payload only needs the rate for choropleth coloring.

### Pitfall 4: `featured` accent-dot on homicide chip looks like a family chip

**What goes wrong:** Setting `featured: true` on the homicide chip renders the same accent-dot as `vida` and `propiedad`. Users may think homicide is an 8th sibling crime family.

**How to avoid:** Add a `title` attribute (already done via `FAMILY_DEFS_EN/ES`) that reads "Subgroup of Life Crimes — homicide cases only." The chip label in ES should be "Homicidios" (not "Delitos contra la vida"). Do not label it "Vida con homicidios" or similar.

### Pitfall 5: `null` vs `0` in `featured_rates.homicidios`

**What goes wrong:** Zero-homicide year scraped as `medida=2` returns `"0,0"` which `parse_cead_float` correctly parses as `0.0`. A commune with NO CEAD data returns `"-"` which parses to `None`. If you store both as `{}` (empty dict), the panel cannot distinguish.

**How to avoid:** Store `0.0` and `0` explicitly (they mean "CEAD reported zero cases"). Store `None` as an absent key (year not in dict). In the panel, check `year in featured_rates.homicidios` (Python) / `hom[String(year)] !== undefined` (TypeScript) — not truthiness check which conflates 0 with missing.

---

## Architecture Patterns

### Recommended File Change List

**Pipeline (Python):**
- `pipeline/cead/client.py` — Add `fetch_subgroup_batch()` function
- `pipeline/cead/normalizer.py` — Add `compute_homicide_level()` (optional, only if emitting level in payload)
- `pipeline/scrape_cead.py` — Add homicide accumulator loop; extend `build_map_payload`; populate `featured_rates.homicidios_count`
- `pipeline/shared/schema.py` — Extend `MapPayloadEntry` with `homicide_rate`, `homicide_count`; extend `YearRecord` if storing per-year count there

**Static data:**
- `data/cead/comunas/{346 files}.json` — Re-scraped; `featured_rates.homicidios` populated
- `data/cead/map-payload.json` and `map-payload-{year}.json` — Regenerated with `homicide_rate`, `homicide_count`

**Frontend (TypeScript/TSX):**
- `site/src/components/map/FiltersRow.tsx` — Add 8th entry to `CHIP_DEFS`
- `site/src/components/map/ChoroplethLayer.ts` — Extend `CommunaPayload` interface; add `buildStyleMapFromHomicide()`
- `site/src/components/map/MapIsland.tsx` — Add `crimeIsHomicide` state; branch chip effect; update `onFamilyChange`
- `site/src/components/map/ResultPanel.tsx` — Add homicide figure section; extend `CommuneData` type usage
- `site/src/lib/familyDefs.ts` — Add `homicidios` key to FAMILY_LABELS and FAMILY_DEFS (both locales)
- `site/src/lib/data.ts` — Extend `CommuneData.featured_rates` type to include `homicidios_count`

**Validators:**
- `site/scripts/validate/map.mjs` — Add Check 8 (payload has `homicide_rate`) and Check 9 (13101.json has homicide years)

### System Architecture Diagram

```
[CEAD endpoint]
     |
     | POST medida=2 familia=1 subgrupo=101
     | POST medida=1 familia=1 subgrupo=101
     v
[fetch_subgroup_batch()] -- latin-1 decode --> [parse_cead_table()]
     |                                                |
     v                                               v
[homicide_accumulator]              {rate: float, count: int} per cut per year
     |
     v
[_run_pipeline() commune assembly]
     |-- featured_rates.homicidios = {year: rate}
     |-- featured_rates.homicidios_count = {year: count}
     v
[data/cead/comunas/{cut}.json]  <-- read at runtime by ResultPanel (panel figure)
     |
[build_map_payload()]
     |-- homicide_rate: int|null
     |-- homicide_count: int|null  (optional, only if budget permits)
     v
[data/cead/map-payload-{year}.json]  <-- fetched by MapIsland on year change
     |
     v
[MapIsland.tsx]
     |-- crimeIsHomicide=true? --> buildStyleMapFromHomicide()
     |                                 --> computeQuantileBreaks(nonZeroRates, 5)
     |                                 --> INCIDENCE_COLORS[level-1]
     v
[ChoroplethLayer / applyStyleMap]  -- in-place setStyle, no re-mount

[FiltersRow]  8th chip 'homicidios' featured=true
     --> onFamilyChange('homicidios', null)
     --> setCrimeIsHomicide(true)

[ResultPanel]
     |-- fetches /data/cead/comunas/{cut}.json
     |-- reads featured_rates.homicidios[year] → rate
     |-- reads featured_rates.homicidios_count[year] → count
     |-- renders "X por 100.000 hab. (Y casos) — CEAD 2024"
     |-- or "Sin casos reportados — CEAD 2024"
```

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (pipeline), node scripts/validate/*.mjs (build) |
| Config file | pytest.ini or pyproject.toml (pipeline); package.json scripts (site) |
| Quick run command | `pytest pipeline/tests/ -x` |
| Full suite command | `pytest pipeline/tests/ && npm run build && node scripts/validate/map.mjs` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HOM-01 | `homicide_rate` present in map-payload for all 346 comunas | Build validator | `node scripts/validate/map.mjs` | ✅ (add Check 8) |
| HOM-01 | Homicide chip triggers choropleth recolor (homicide layer) | Manual/E2E | Browser inspect map | — |
| HOM-02 | Homicide figure renders in ResultPanel | Manual/E2E | Click Santiago commune, check panel | — |
| HOM-02 | Family bars unchanged (no regression) | Manual | Click Santiago, verify 7 bars still present | — |
| HOM-01 | Subgroup-101 scrape populates `featured_rates.homicidios` | Pipeline unit | `pytest pipeline/tests/test_scrape_cead.py -k homicide` | ❌ Wave 0 |
| HOM-01 | Payload stays under 30 KB after homicide fields added | Pipeline check | `pytest pipeline/tests/test_output.py` | ✅ (existing, verify coverage) |

### Runtime Research Checkpoints (must complete BEFORE coding fetch loop)

1. **Subgroup param confirmation:** Run `test_subgroup101.py` (see §CEAD Subgroup-101) — confirm `subgrupo[]=101` returns non-empty commune rows with plausible homicide rates.
2. **Two-request confirmation:** Verify `medida=1` and `medida=2` return different numeric ranges for the same subgroup (count ~0–50, rate ~0–100).
3. **Zero-commune behavior:** Verify that a commune with no 2024 homicides returns `"0,0"` (not `"-"`) in both medida=1 and medida=2 responses.

### Wave 0 Gaps

- [ ] `pipeline/tests/test_scrape_cead.py` — add test for `homicide_accumulator` population and `featured_rates.homicidios` non-empty after pipeline run (requires mocked HTML fixture)
- [ ] `pipeline/cache/test_subgroup101_rate.html` and `_count.html` — runtime experiment artifacts (git-ignored, but executor creates during Wave 0 confirmation)

---

## Security Domain

No new external input, no user-controlled data, no auth. This phase is data-pipeline + static JSON + React island with same-origin fetch. No new ASVS categories introduced beyond existing pipeline (CEAD scraping already handles timeout/retry). [VERIFIED: code inspection]

The homicide `homicide_rate` and `homicide_count` values in the payload are integer-clamped at pipeline time; no raw user input reaches the JSON.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | Pipeline scraping | ✅ | 3.12 (GitHub Actions) | — |
| CEAD endpoint | Subgroup-101 fetch | ✅ (assumed live) | — | Use cache from prior run |
| `requests` + `beautifulsoup4` | fetch_subgroup_batch | ✅ | installed | — |
| `chroma-js` | buildStyleMapFromHomicide | ✅ | installed | — |
| Network access to CEAD | Executor dev machine | ASSUMED | — | Use CI with real secrets |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | CEAD `get_estadisticas_delictuales.php` accepts `subgrupo[]` as a POST parameter to filter within a family | CEAD Subgroup Fetch | Entire scrape approach needs alternative (try `grupo[]`, or accept vida aggregate) |
| A2 | `medida=1` (count) and `medida=2` (rate) require two separate POST requests | CEAD Subgroup Fetch | If one request returns both, fetch loop can be simplified (halved) |
| A3 | Zero-homicide communes return `"0,0"` (not `"-"`) for both medida values | Pitfall 5 | Stored as `None` instead of `0`, panel shows "no data" for communes that actually had 0 homicides |
| A4 | Adding `homicide_rate` + `homicide_count` to 346 commune entries stays under 30 KB payload limit | Payload Shape | Pipeline fails at budget assertion; need to drop `homicide_count` from payload and rely on per-commune JSON for the count |
| A5 | Chilean homicide rates are in the 0–100/100k range for all comunas | Choropleth Bucketing | Quantile buckets may still be skewed; may need to cap outliers |

---

## Open Questions

1. **Does `subgrupo[]=101` work as a CEAD POST parameter?**
   - What we know: the original scrap analysis lists `subgrupo[]` as optional; `normalizer.py` hardcodes `homicidios: 101`.
   - What's unclear: no confirmed live test with this parameter.
   - Recommendation: Executor runs `test_subgroup101.py` before any coding (Wave 0, Day 1).

2. **Should `homicide_count` be in the map-payload or only in per-commune JSON?**
   - What we know: payload headroom is ~3 KB; panel fetches per-commune JSON anyway.
   - What's unclear: whether MapIsland or Legend ever needs the count directly.
   - Recommendation: Start without `homicide_count` in payload (only `homicide_rate`); add it only if panel UX requires it in a "before panel opens" context.

3. **Should the homicide chip deactivate the active family chip, or can both be active simultaneously?**
   - What we know: current chip logic is exclusive (one active at a time per `crimeFamily === key` check).
   - What's unclear: whether "homicide layer + vida chip active" is a useful state.
   - Recommendation: Keep exclusive-selection pattern; clicking homicide deactivates any active family chip.

---

## Sources

### Primary (HIGH confidence — codebase inspection)
- `pipeline/cead/client.py` — `fetch_communes_batch` signature, POST payload params (lines 110-129)
- `pipeline/cead/catalog.py` — `seleccion=101` is catalog-only, not data endpoint (lines 67-69)
- `pipeline/cead/normalizer.py` — `FEATURED_SUBGROUPS = {"homicidios": 101}` (line 27); `attach_featured` (lines 213-233)
- `pipeline/scrape_cead.py` — family loop (lines 343-403); hardcoded `homicidios_by_year: {}` (line 448); `build_map_payload` (lines 88-145)
- `pipeline/shared/schema.py` — `FAMILY_KEYS`, `MapPayloadEntry`, `ComunaRecord` schemas
- `site/src/components/map/FiltersRow.tsx` — `CHIP_DEFS` array (lines 30-39)
- `site/src/components/map/ChoroplethLayer.ts` — `buildStyleMapFromFamily` (line 86); `CommunaPayload` type (line 13)
- `site/src/components/map/MapIsland.tsx` — chip effect (lines 277-290); year effect (lines 229-272)
- `site/src/components/map/ResultPanel.tsx` — `CommuneData` type (lines 52-65); family bars (line 309)
- `site/src/lib/familyDefs.ts` — all FAMILY_* exports (confirmed no `homicidios` key present)
- `site/src/lib/data.ts` — `CommuneData.featured_rates` type (line 44)
- `site/scripts/validate/map.mjs` — existing checks (7 total); extension points
- `data/cead/comunas/13101.json` — confirmed `featured_rates.homicidios = {}` (live data)
- `data/cead/map-payload.json` — confirmed shape `{id, rate, level, by_family[7]}`; size 27,527 bytes

### Secondary (MEDIUM confidence — original scraping analysis)
- `como scrap.txt` — CEAD endpoint parameter list including `subgrupo[]` (not live-confirmed)

### Tertiary (LOW confidence — assumed)
- Homicide rate distribution assumptions (Chilean homicide ~5/100k national average)

---

## Metadata

**Confidence breakdown:**
- Codebase findings: HIGH — all file paths, line numbers, function signatures verified by direct inspection
- CEAD subgroup-101 param: LOW — `subgrupo[]=101` inferred from `como scrap.txt` + `normalizer.py` constant; not confirmed with live request
- Payload budget: MEDIUM — current size measured exactly (27,527 bytes); homicide field size estimated
- Choropleth bucketing: HIGH — recommendation directly reuses existing `computeQuantileBreaks` already in the codebase

**Research date:** 2026-06-16
**Valid until:** 2026-07-16 (CEAD endpoint parameters could change; re-verify if pipeline fails)
