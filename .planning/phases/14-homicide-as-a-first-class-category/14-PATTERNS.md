# Phase 14: Homicide as a First-Class Category — Pattern Map

**Mapped:** 2026-06-16
**Files analyzed:** 11 (8 modified, 3 data artifacts)
**Analogs found:** 11 / 11

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pipeline/cead/client.py` | service | request-response | itself (`fetch_communes_batch`) | exact — add sibling function |
| `pipeline/cead/normalizer.py` | utility | transform | itself (`compute_level`, `attach_featured`) | exact — extend existing function |
| `pipeline/scrape_cead.py` | service | batch | itself (family fetch loop lines 343–403) | exact — add parallel loop |
| `pipeline/shared/schema.py` | model | transform | itself (`MapPayloadEntry`, `YearRecord`) | exact — extend Pydantic models |
| `site/src/components/map/FiltersRow.tsx` | component | request-response | itself (`CHIP_DEFS` array) | exact — append one entry |
| `site/src/components/map/ChoroplethLayer.ts` | utility | transform | itself (`buildStyleMapFromFamily` lines 86–105) | exact — add sibling function |
| `site/src/components/map/MapIsland.tsx` | component | event-driven | itself (chip effect lines 277–290, year effect lines 229–272) | exact — add state + branch |
| `site/src/components/map/ResultPanel.tsx` | component | request-response | itself (panel sections, `CommuneData` type lines 52–65) | exact — add section, extend type |
| `site/src/lib/familyDefs.ts` | utility | transform | itself (FAMILY_LABELS_EN/ES, FAMILY_DEFS_EN/ES) | exact — add `homicidios` key |
| `site/src/lib/data.ts` | utility | transform | itself (`CommuneData.featured_rates` line 44) | exact — add `homicidios_count` field |
| `site/scripts/validate/map.mjs` | utility | batch | itself (Check 1 pattern lines 48–93) | exact — add Check 8 + 9 |

---

## Pattern Assignments

### `pipeline/cead/client.py` — Add `fetch_subgroup_batch`

**Analog:** `pipeline/cead/client.py::fetch_communes_batch` (lines 82–129)

**Existing function signature to mirror** (lines 82–87):
```python
def fetch_communes_batch(
    session: requests.Session,
    cut_codes: list[str],
    year: int,
    familia_id: int,
) -> str:
```

**POST payload pattern to extend** (lines 110–123):
```python
payload: dict = {
    "medida": "2",
    "tipoVal": "1,2",
    "anio[]": str(year),
    "familia[]": str(familia_id),
    "seleccion": "1",
    "descarga": "true",
}
payload["comuna[]"] = [str(cut) for cut in cut_codes]
payload["region[]"] = str(cut_codes[0])[:2]
response = session.post(_DATA_ENDPOINT, data=payload, timeout=30)
response.raise_for_status()
return response.content.decode("latin-1")
```

**New function — copy this structure, add `subgrupo[]` and `medida` param:**
```python
def fetch_subgroup_batch(
    session: requests.Session,
    cut_codes: list[str],
    year: int,
    familia_id: int,
    subgrupo_id: int,
    medida: str = "2",   # "2"=rate per 100k, "1"=absolute count
) -> str:
    payload: dict = {
        "medida": medida,           # parametric — not hardcoded "2"
        "tipoVal": "1,2",
        "anio[]": str(year),
        "familia[]": str(familia_id),
        "subgrupo[]": str(subgrupo_id),   # NEW — subgroup selector
        "seleccion": "1",
        "descarga": "true",
    }
    payload["comuna[]"] = [str(cut) for cut in cut_codes]
    payload["region[]"] = str(cut_codes[0])[:2]
    response = session.post(_DATA_ENDPOINT, data=payload, timeout=30)
    response.raise_for_status()
    return response.content.decode("latin-1")
```

**EXECUTOR NOTE (Wave 0 prerequisite):** Run the live test in RESEARCH.md §CEAD Subgroup-101
before coding. If `subgrupo[]` returns empty table, try `grupo[]`. Confirm
`medida=1` returns small integers (case counts) and `medida=2` returns floats
(rates). Use separate cache keys `cead_subgroup101_{year}_rate.html` vs `_count.html`.

---

### `pipeline/cead/normalizer.py` — Extend `attach_featured`

**Analog:** `pipeline/cead/normalizer.py::attach_featured` (lines 213–233)

**Existing function body** (lines 228–233):
```python
featured: dict[str, dict] = {
    "propiedad": dict(commune_data.get("propiedad_by_year", {})),
    "homicidios": dict(commune_data.get("homicidios_by_year", {})),
    "secuestros": dict(commune_data.get("secuestros_by_year", {})),
}
return featured
```

**Extension — add `homicidios_count` key (Option A, non-breaking):**
```python
featured: dict[str, dict] = {
    "propiedad": dict(commune_data.get("propiedad_by_year", {})),
    "homicidios": dict(commune_data.get("homicidios_by_year", {})),
    "homicidios_count": dict(commune_data.get("homicidios_count_by_year", {})),  # NEW
    "secuestros": dict(commune_data.get("secuestros_by_year", {})),
}
return featured
```

**`compute_level` signature reuse** (lines 171–206) — call with non-zero homicide rates only:
```python
def compute_level(rate: float, all_rates: list[float]) -> int:
    # Existing — reuse directly; pass [r for r in all_hom_rates if r > 0] as all_rates
    # when computing homicide level, so zero-homicide communes cluster at level 1
```

---

### `pipeline/scrape_cead.py` — Add subgroup fetch loop + extend `build_map_payload`

**Analog A: Family fetch loop** (lines 343–403) — structure for new subgroup loop:

**Accumulator init pattern** (lines 339–341):
```python
accumulator: dict[str, dict[int, dict[str, float | None]]] = {
    cut: {} for cut in catalog
}
```
Copy this verbatim for `homicide_accumulator`:
```python
homicide_accumulator: dict[str, dict[int, dict]] = {cut: {} for cut in catalog}
```

**Cache/fetch/sleep pattern** (lines 358–375):
```python
cache_key = f"cead_{region_id}_{familia_id}_{year}.html"
html = load_cached(cache_key)
if html is None:
    html = fetch_communes_batch(session, cut_codes=list(catalog.keys()),
                                year=year, familia_id=familia_id)
    cache_raw(cache_key, html)
    time.sleep(2.5)  # D-03: courtesy delay
```
Mirror for subgroup (two variants per year — rate then count):
```python
cache_key_rate = f"cead_subgroup101_{year}_rate.html"
html_rate = load_cached(cache_key_rate)
if html_rate is None:
    html_rate = fetch_subgroup_batch(session, list(catalog.keys()),
                                     year, familia_id=1, subgrupo_id=101, medida="2")
    cache_raw(cache_key_rate, html_rate)
    time.sleep(2.5)
```

**Row accumulation pattern** (lines 382–391):
```python
rows = parse_cead_table(html)
for row in rows:
    cut = _match_cut(row["name"], catalog)
    if cut is None:
        continue
    accumulator[cut].setdefault(year, {})
    rate_str = row["values"].get(str(year)) or row["values"].get(year)
    rate = parse_cead_float(rate_str) if rate_str else None
    accumulator[cut][year][familia_key] = rate
```
Mirror for homicide (separate `rate` and `count` fields in accumulator dict):
```python
for row in rows_rate:
    cut = _match_cut(row["name"], catalog)
    if cut is None: continue
    rate_str = row["values"].get(str(year)) or row["values"].get(year)
    rate = parse_cead_float(rate_str) if rate_str else None
    homicide_accumulator[cut].setdefault(year, {})["rate"] = rate
```

**`attach_featured` call site** (lines 437–450) — the gap to fill:
```python
featured = attach_featured({
    "propiedad_by_year": { ... },
    "vida_by_year": { ... },
    "homicidios_by_year": {},      # <-- CURRENTLY HARDCODED EMPTY (line 448)
    "secuestros_by_year": {},
})
```
Replace with:
```python
homicidios_by_year = {
    yr: data["rate"]
    for yr, data in homicide_accumulator.get(cut, {}).items()
    if data.get("rate") is not None
}
homicidios_count_by_year = {
    yr: int(round(data["count"]))
    for yr, data in homicide_accumulator.get(cut, {}).items()
    if data.get("count") is not None
}
featured = attach_featured({
    "propiedad_by_year": { ... },
    "vida_by_year": { ... },
    "homicidios_by_year": homicidios_by_year,
    "homicidios_count_by_year": homicidios_count_by_year,  # new key
    "secuestros_by_year": {},
})
```

**Analog B: `build_map_payload` entry assembly** (lines 133–138):
```python
by_family_list = [int(round(by_family[k])) if by_family[k] is not None else None for k in _FK]
comunas.append({
    "id": r["id"],
    "rate": int(round(rate)),
    "level": level,
    "by_family": by_family_list,
})
```
Extend with homicide fields after the existing append block:
```python
featured = r.get("featured_rates", {})
hom_rate_dict = featured.get("homicidios", {})
hom_count_dict = featured.get("homicidios_count", {})
hom_rate = hom_rate_dict.get(str(year)) or hom_rate_dict.get(year)
hom_count = hom_count_dict.get(str(year)) or hom_count_dict.get(year)
comunas.append({
    "id": r["id"],
    "rate": int(round(rate)),
    "level": level,
    "by_family": by_family_list,
    "homicide_rate": int(round(hom_rate)) if hom_rate is not None else None,   # NEW
    "homicide_count": int(hom_count) if hom_count is not None else None,        # NEW
})
```

**Budget guard (line ~269):** After building payload, assert `len(json.dumps(payload)) < 30720`.
Current size is 27,527 bytes; headroom is ~3,193 bytes. If over budget, drop
`homicide_count` from the payload entry (panel reads it from per-commune JSON anyway).

---

### `pipeline/shared/schema.py` — Extend Pydantic models

**Analog: `MapPayloadEntry`** (lines 99–110):
```python
class MapPayloadEntry(BaseModel):
    id: str
    rate: float
    level: int
    by_family: list[float | None]

    @field_validator("level")
    @classmethod
    def level_must_be_1_to_5(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError(f"level must be 1–5, got {v}")
        return v
```
Add two optional fields (no validator needed — nullable ints):
```python
class MapPayloadEntry(BaseModel):
    id: str
    rate: float
    level: int
    by_family: list[float | None]
    homicide_rate: int | None = None    # NEW — rate per 100k, null if no data
    homicide_count: int | None = None   # NEW — absolute cases, null if no data

    @field_validator("level")
    ...
```

**Analog: `YearRecord`** (lines 40–44):
```python
class YearRecord(BaseModel):
    year: int
    rate_per_100k: float
    by_family: dict[str, float | None]
    partial: bool = False
```
No change needed to `YearRecord` — homicide count rides in `featured_rates.homicidios_count`
(a dict on `ComunaRecord.featured_rates`), not in the per-year series entry.

---

### `site/src/components/map/FiltersRow.tsx` — Add 8th chip to `CHIP_DEFS`

**Analog: existing chip entries** (lines 30–39):
```tsx
const CHIP_DEFS: ChipDef[] = [
  { key: null,              familyIndex: null, labelEs: 'Todos',         labelEn: 'All types',       featured: false },
  { key: 'vida',            familyIndex: 0,    labelEs: 'Vida y convi…', labelEn: 'Life crimes',     featured: true  },
  { key: 'propiedad',       familyIndex: 5,    labelEs: 'Propiedad',     labelEn: 'Property crimes', featured: true  },
  // ... 5 more family chips
  { key: 'armas',           familyIndex: 4,    labelEs: 'Armas',         labelEn: 'Weapons',         featured: false },
];
```

**New 8th entry — append after `armas`:**
```tsx
{ key: 'homicidios', familyIndex: null, labelEs: 'Homicidios', labelEn: 'Homicide', featured: true },
```

Key design decisions:
- `familyIndex: null` — homicide is NOT a `by_family` array index; `null` signals the new code path in MapIsland
- `featured: true` — renders accent-dot (consistent with `vida`, `propiedad`)
- `key: 'homicidios'` — sentinel string; `FAMILY_DEFS_EN['homicidios']` / `FAMILY_DEFS_ES['homicidios']` must exist in `familyDefs.ts` for the `title` tooltip (line 80 lookup: `FAMILY_DEFS_EN[key]`)

**Chip rendering pattern** (lines 78–98) — unchanged; the `featured && !isActive` accent-dot
renders automatically from the `featured: true` flag. The `onFamilyChange(isActive ? null : key, isActive ? null : familyIndex)` call passes `familyIndex: null` to MapIsland for the homicide chip.

---

### `site/src/components/map/ChoroplethLayer.ts` — Add `buildStyleMapFromHomicide`

**Analog: `buildStyleMapFromFamily`** (lines 86–105) — exact structural copy with `homicide_rate` field instead of `by_family[familyIndex]`:

```typescript
// EXISTING — copy this structure:
export function buildStyleMapFromFamily(
  comunas: CommunaPayload[],
  familyIndex: number
): Map<string, L.PathOptions> {
  const rates = comunas.map((c) => c.by_family[familyIndex] ?? 0);
  const positiveRates = rates.filter((r) => r > 0);
  const breaks = computeQuantileBreaks(positiveRates, 5);
  const m = new Map<string, L.PathOptions>();
  for (const c of comunas) {
    const rate = c.by_family[familyIndex] ?? 0;
    const level = levelFromBreaks(rate, breaks);
    m.set(c.id, {
      fillColor: INCIDENCE_COLORS[level - 1]!,
      fillOpacity: 0.55,
      color: '#ffffff',
      weight: 1.2,
    });
  }
  return m;
}
```

**New function:**
```typescript
export function buildStyleMapFromHomicide(
  comunas: CommunaPayload[]
): Map<string, L.PathOptions> {
  const rates = comunas.map((c) => c.homicide_rate ?? 0);  // reads new field
  const positiveRates = rates.filter((r) => r > 0);
  const breaks = computeQuantileBreaks(positiveRates, 5);   // same util, non-zero only
  const m = new Map<string, L.PathOptions>();
  for (const c of comunas) {
    const rate = c.homicide_rate ?? 0;
    const level = levelFromBreaks(rate, breaks);
    m.set(c.id, {
      fillColor: INCIDENCE_COLORS[level - 1]!,
      fillOpacity: rate === 0 ? 0.25 : 0.55,  // visually distinguish zero-homicide communes
      color: '#ffffff',
      weight: 1.2,
    });
  }
  return m;
}
```

**`CommunaPayload` interface extension** (lines 13–18):
```typescript
// EXISTING:
export interface CommunaPayload {
  id: string;
  rate: number;
  level: 1 | 2 | 3 | 4 | 5;
  by_family: number[];
}

// EXTENDED:
export interface CommunaPayload {
  id: string;
  rate: number;
  level: 1 | 2 | 3 | 4 | 5;
  by_family: number[];
  homicide_rate: number | null;    // NEW
  homicide_count: number | null;   // NEW (may be absent if payload over budget — guard with ??)
}
```

**Imports** (line 11) — no new imports needed; `computeQuantileBreaks` and `levelFromBreaks`
are already imported from `./colors`.

---

### `site/src/components/map/MapIsland.tsx` — Add homicide state + branch

**Analog A: State declarations** (lines 94–103):
```typescript
const [year, setYear] = useState(2025);
const [crimeFamily, setCrimeFamily] = useState<string | null>(null);
const [crimeFamilyIndex, setCrimeFamilyIndex] = useState<number | null>(null);
const [showEvents, setShowEvents] = useState(false);
// ...
```
Add one new state variable after `crimeFamilyIndex`:
```typescript
const [crimeIsHomicide, setCrimeIsHomicide] = useState(false);
```

**Analog B: Crime-type chip effect** (lines 277–290) — the effect to branch:
```typescript
useEffect(() => {
  const communas = payloadRef.current;
  if (!layerRef.current || !communas) return;
  const geoLayer = layerRef.current!;

  if (crimeFamilyIndex !== null) {
    styleMapRef.current = buildStyleMapFromFamily(communas, crimeFamilyIndex);
  } else {
    styleMapRef.current = buildStyleMapFromLevel(communas);
  }

  applyStyleMap(geoLayer, styleMapRef);
}, [crimeFamilyIndex]);
```
Replace with a branched effect that also depends on `crimeIsHomicide`:
```typescript
useEffect(() => {
  const communas = payloadRef.current;
  if (!layerRef.current || !communas) return;
  const geoLayer = layerRef.current!;

  if (crimeIsHomicide) {
    styleMapRef.current = buildStyleMapFromHomicide(communas);   // NEW branch
  } else if (crimeFamilyIndex !== null) {
    styleMapRef.current = buildStyleMapFromFamily(communas, crimeFamilyIndex);
  } else {
    styleMapRef.current = buildStyleMapFromLevel(communas);
  }

  applyStyleMap(geoLayer, styleMapRef);
}, [crimeFamilyIndex, crimeIsHomicide]);   // add crimeIsHomicide to dep array
```

**Analog C: Year effect — also needs the homicide branch** (lines 258–263):
```typescript
if (crimeFamilyIndex !== null) {
  styleMapRef.current = buildStyleMapFromFamily(payload.comunas, crimeFamilyIndex);
} else {
  styleMapRef.current = buildStyleMapFromLevel(payload.comunas);
}
```
Add homicide branch here as well (same three-way logic).

**`onFamilyChange` handler** — the handler that `FiltersRow` calls (lines 49–50 of FiltersRow Props):
```typescript
// The prop signature in MapIsland that passes to FiltersRow:
onFamilyChange: (key: string | null, index: number | null) => void;
```
Update handler body to also set `crimeIsHomicide`:
```typescript
function handleFamilyChange(key: string | null, index: number | null) {
  setCrimeFamily(key);
  setCrimeFamilyIndex(index);
  setCrimeIsHomicide(key === 'homicidios');   // NEW
}
```

**Import addition** — add `buildStyleMapFromHomicide` to the import from `./ChoroplethLayer` (line 24–29):
```typescript
import {
  mountChoroplethLayer,
  buildStyleMapFromLevel,
  buildStyleMapFromFamily,
  buildStyleMapFromHomicide,   // NEW
  applyStyleMap,
  highlightSelected,
  type CommunaPayload,
} from './ChoroplethLayer';
```

---

### `site/src/components/map/ResultPanel.tsx` — Add homicide figure section

**Analog A: `CommuneData` interface** (lines 52–65) — extend `featured_rates`:
```typescript
// EXISTING (lines 52–65):
interface CommuneData {
  id: string;
  name: string;
  // ...
  series: SeriesEntry[];
  last_updated?: string;
  incidents?: Incident[];
  // NOTE: featured_rates NOT typed here — accessed as any from the JSON
}
```
The `CommuneData` in `ResultPanel.tsx` does NOT currently type `featured_rates`.
It is accessed from the raw JSON fetch response. Add it:
```typescript
interface CommuneData {
  // ... existing fields ...
  featured_rates?: {
    homicidios?: Record<string, number>;
    homicidios_count?: Record<string, number>;  // NEW — absolute case count by year
    propiedad?: Record<string, number>;
    secuestros?: Record<string, number>;
  };
}
```

**Analog B: Fetch pattern** (lines 107–126) — unchanged; panel already fetches
`/data/cead/comunas/${cut}.json` on open. No new fetch needed for homicide.

**Analog C: Panel section pattern** — observe the existing rate display pattern at lines 165–198.
The homicide section goes AFTER the family bars section (after PanelFamilyBars render at ~line 309):
```tsx
{/* Homicide breakdown (D-06/D-07) */}
{(() => {
  const hom = (data as CommuneData).featured_rates?.homicidios;
  const homCount = (data as CommuneData).featured_rates?.homicidios_count;
  const homRate = hom ? (hom[String(year)] ?? null) : null;
  const count = homCount ? (homCount[String(year)] ?? null) : null;
  const hasData = homRate !== null;
  return (
    <div className="panel-section">
      <h4>{lang === 'es' ? `Homicidios (${year})` : `Homicide (${year})`}</h4>
      {hasData ? (
        <div>
          <span className="stat-mid">{Math.round(homRate).toLocaleString('es-CL')}</span>
          {lang === 'es' ? ' por 100.000 hab.' : ' per 100,000 inhab.'}
          {count !== null && (
            <span className="stat-sub">
              {' '}({count} {lang === 'es' ? (count === 1 ? 'caso' : 'casos') : (count === 1 ? 'case' : 'cases')})
            </span>
          )}
        </div>
      ) : (
        <p style={{ color: 'var(--muted)' }}>
          {lang === 'es' ? `Sin casos reportados — CEAD ${year}` : `No reported cases — CEAD ${year}`}
        </p>
      )}
      <div className="official-row" style={{ fontSize: '0.78rem', marginTop: 4 }}>
        {lang === 'es'
          ? `Fuente: CEAD, subgrupo 101 Delitos contra la Vida (${year})`
          : `Source: CEAD, subgroup 101 Life Crimes (${year})`}
      </div>
    </div>
  );
})()}
```

**PanelFamilyBars regression guard:** `PanelFamilyBars` receives `byFamilyArray`
(7-element array, computed at lines 183–185 from `recordToArray`). Nothing in
Phase 14 touches that component or that array. The `by_family` array in the
per-commune JSON remains 7-element; the homicide section is purely additive.

---

### `site/src/lib/familyDefs.ts` — Add `homicidios` key to all four dicts

**Analog: existing family entry pattern** (lines 18–59):
```typescript
// FAMILY_LABELS_EN pattern:
vida: 'Life Crimes',

// FAMILY_DEFS_EN pattern (sober, non-alarmist, CEAD-cited):
vida: 'Reported offences against life and physical integrity, including homicide and serious assault, sourced from official CEAD police statistics.',

// FAMILY_LABELS_ES:
vida: 'Delitos contra la Vida',

// FAMILY_DEFS_ES:
vida: 'Delitos reportados contra la vida e integridad física, incluyendo homicidios y lesiones graves, según estadísticas policiales oficiales del CEAD.',
```

**New entries to add to each dict:**
```typescript
// FAMILY_LABELS_EN — add:
homicidios: 'Homicide',

// FAMILY_DEFS_EN — add (subgroup-honest, non-alarmist):
homicidios: 'Reported homicide cases disaggregated by commune, sourced from CEAD official police statistics (subgroup 101 within the Life Crimes family).',

// FAMILY_LABELS_ES — add:
homicidios: 'Homicidios',

// FAMILY_DEFS_ES — add:
homicidios: 'Casos de homicidio reportados desagregados por comuna, según estadísticas policiales oficiales del CEAD (subgrupo 101 dentro de Delitos contra la Vida).',
```

**`FAMILY_ORDER` — do NOT add `homicidios`.** It is used for crime-type SEO pages
(Phase 15), not for the filter chip. The homicide chip key is looked up via
`FAMILY_DEFS_EN[key]` / `FAMILY_DEFS_ES[key]` in FiltersRow line 80 — those dicts
are `Record<string, string>` (open), not constrained to `FAMILY_ORDER`. Adding
`homicidios` to the four label/def dicts is sufficient.

---

### `site/src/lib/data.ts` — Extend `CommuneData.featured_rates`

**Analog: existing type** (lines 44–48):
```typescript
export interface CommuneData extends CommuneMeta {
  // ...
  featured_rates: {
    propiedad: Record<string, number>;
    homicidios: Record<string, number>;
    secuestros: Record<string, number>;
  };
  // ...
}
```

**Extension — add `homicidios_count`:**
```typescript
featured_rates: {
  propiedad: Record<string, number>;
  homicidios: Record<string, number>;
  homicidios_count: Record<string, number>;  // NEW — absolute cases by year
  secuestros: Record<string, number>;
};
```

This is a build-time type used by Astro SSG pages. The `loadCommune()` function
(lines 157–178) reads the raw JSON and spreads it as `CommuneData` — no logic change
needed, just the type. At runtime the panel fetches the commune JSON directly
(not via `loadCommune`), so the ResultPanel uses its own local `CommuneData` interface.

---

### `site/scripts/validate/map.mjs` — Add Check 8 + Check 9

**Analog: Check 1 pattern** (lines 48–93) — `existsSync` guard, `JSON.parse`, assertion, `pass`/`fail`:
```javascript
if (!existsSync(TOPO_PATH)) {
  fail('TopoJSON exists', `File not found: ...`);
} else {
  const data = JSON.parse(readFileSync(TOPO_PATH, 'utf8'));
  // ... assertions ...
  pass('label');
}
```

**New checks to append at bottom of map.mjs (after existing Check 6/7):**
```javascript
// ---------------------------------------------------------------------------
// Check 8: homicide_rate field present in map-payload
// ---------------------------------------------------------------------------
const MAP_PAYLOAD_PATH = path.join(REPO_ROOT, 'data', 'cead', 'map-payload.json');
if (existsSync(MAP_PAYLOAD_PATH)) {
  const payload = JSON.parse(readFileSync(MAP_PAYLOAD_PATH, 'utf8'));
  const sample = payload.comunas?.slice(0, 10) ?? [];
  const hasHomicide = sample.some(c => 'homicide_rate' in c);
  if (!hasHomicide) {
    fail('homicide in payload', 'map-payload.json comunas missing homicide_rate — subgroup-101 scrape not run');
  } else {
    pass('homicide_rate in map-payload');
  }
}

// ---------------------------------------------------------------------------
// Check 9: Santiago (13101) has non-empty homicidios in featured_rates
// ---------------------------------------------------------------------------
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

## Shared Patterns

### CEAD Courtesy Delay
**Source:** `pipeline/scrape_cead.py` line 375
**Apply to:** All new CEAD fetch calls in the subgroup-101 loop
```python
time.sleep(2.5)  # D-03: courtesy delay — always after cache_raw(), never skip
```

### Latin-1 Decode
**Source:** `pipeline/cead/client.py` line 128
**Apply to:** `fetch_subgroup_batch` return value
```python
return response.content.decode("latin-1")  # NOT response.text — charset detection guesses wrong
```

### `parse_cead_float` + `_match_cut`
**Source:** `pipeline/scrape_cead.py` lines 385–391
**Apply to:** Homicide accumulator row processing
```python
cut = _match_cut(row["name"], catalog)
if cut is None:
    continue
rate_str = row["values"].get(str(year)) or row["values"].get(year)
rate = parse_cead_float(rate_str) if rate_str else None
```

### `pass` / `fail` validator helpers
**Source:** `site/scripts/validate/map.mjs` lines 36–43
**Apply to:** Check 8 and Check 9
```javascript
function pass(label) { console.log(`PASS [${label}]`); }
function fail(label, msg) { console.error(`FAIL [${label}]: ${msg}`); failures++; }
```

### i18n bilingual strings
**Source:** `site/src/components/map/ResultPanel.tsx` (throughout), e.g. line 134:
```tsx
{lang === 'es' ? 'Cargando datos de la comuna' : 'Loading commune data'}
```
**Apply to:** All new panel strings in the homicide section (D-07 + editorial rule).
Pattern: always `{lang === 'es' ? 'ES text' : 'EN text'}` inline.

### `null` vs `0` in homicide data
**Source:** RESEARCH.md §Pitfall 5 (critical invariant)
**Apply to:** All pipeline code writing homicide values
- `0.0` / `0` = CEAD confirmed zero cases for that year — store explicitly
- absent key = CEAD returned `"-"` or no data — do NOT store, leave key absent
- In TypeScript: check `hom[String(year)] !== undefined`, not truthiness

---

## No Analog Found

All files in Phase 14 have strong in-codebase analogs. No new packages or file roles
without precedent.

---

## Metadata

**Analog search scope:** `pipeline/`, `site/src/components/map/`, `site/src/lib/`,
`site/scripts/validate/`, `pipeline/shared/`
**Files read:** 11 source files
**Pattern extraction date:** 2026-06-16
