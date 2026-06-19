# Phase 18: Composite Crime Index - Pattern Map

**Mapped:** 2026-06-19
**Files analyzed:** 13 (4 new Python, 1 extracted Python, 1 new test, 4 modified TS/Astro, 2 modified validators, 1 modified workflow)
**Analogs found:** 13 / 13 (every new/modified file has a strong in-repo analog — this is a brownfield phase)

All line numbers below were verified by direct read on 2026-06-19. Excerpts are load-bearing — copy structure, adapt names.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pipeline/composite_config.py` (NEW) | config | transform | `pipeline/shared/schema.py` (FAMILY_KEYS module-const pattern) | role-match |
| `pipeline/composite_index.py` (NEW) | service | transform/batch | `pipeline/cead/normalizer.py` (pure compute fns) | role-match |
| `pipeline/build_composite_index.py` (NEW) | pipeline entrypoint | batch / file-I/O | `pipeline/scrape_cead.py` `_write_all_outputs()` + `__main__` | role-match |
| `pipeline/build_map_payload.py` (EXTRACTED) | pipeline entrypoint | batch / file-I/O | `pipeline/scrape_cead.py` `build_map_payload()` lines 102–204 (verbatim move) | exact (source) |
| `pipeline/tests/test_composite.py` (NEW) | test | request-response | `pipeline/tests/test_scrape_cead.py` (record-builder + payload assertions) | exact |
| `site/src/components/map/ChoroplethLayer.ts` (MOD) | component (layer factory) | event-driven (style swap) | `buildStyleMapFromHomicide()` lines 120–138 (same file) | exact |
| `site/src/components/map/ResultPanel.tsx` (MOD) | component (React island) | request-response (fetch-on-open) | homicide section lines 318–351 (same file) | exact |
| `site/src/pages/commune/[slug].astro` (MOD) | route (SSR template) | request-response (build-time read) | same file head + `MethodologyCaveat` import | exact |
| `site/src/pages/es/comuna/[slug].astro` (MOD) | route (SSR template) | request-response | EN `commune/[slug].astro` (ES mirror) | exact |
| `site/scripts/validate/forbidden-language.mjs` (MOD) | config (CI validator) | batch (scan dist/) | `FORBIDDEN_TERMS` + `ALLOW_LIST` arrays lines 35–66 (same file) | exact |
| `site/scripts/validate/figure-registry.mjs` (MOD) | config (CI validator) | batch (scan SOURCES.md) | `FIGURE_REGISTRY` F1–F12 entries lines 56–179 (same file) | exact |
| `.github/workflows/cead-scraper.yml` (MOD) | config (CI workflow) | event-driven (cron) | "Run CEAD scraper" step lines 33–34 (same file) | exact |
| `data/SOURCES.md` (MOD) | config (doc) | n/a | existing `## CEAD` / `## INE` section headings | role-match |

---

## Shared Patterns

These cross-cut multiple new files. Apply uniformly.

### Atomic JSON write (ALL pipeline output)
**Source:** `pipeline/shared/atomic_write.py` lines 13–35
**Apply to:** `build_composite_index.py`, `build_map_payload.py`
Never use `f.write()` / `json.dump()` to a final path. Use:
```python
from pipeline.shared.atomic_write import atomic_write_json
atomic_write_json(output_dir / "comunas" / f"{cut}.json", record)              # pretty (default)
atomic_write_json(output_dir / "map-payload.json", payload, compact=True)      # minified, size-sensitive
atomic_write_json(output_dir / "comparator_table.json", table)                 # NEW file, pretty
```
`compact=True` is the established switch for `<30 KB` payloads (used at `scrape_cead.py:347-348`).

### Repo-relative data dir with env override
**Source:** `pipeline/scrape_cead.py` lines 40–46
**Apply to:** both new entrypoints — keeps tests able to redirect output.
```python
_REPO_ROOT = pathlib.Path(__file__).parent.parent
_DEFAULT_DATA_DIR = _REPO_ROOT / "data" / "cead"
def _get_data_dir() -> pathlib.Path:
    override = os.environ.get("CEAD_DATA_DIR")
    return pathlib.Path(override) if override else _DEFAULT_DATA_DIR
```

### int-vs-str year-key dual lookup (JSON round-trip hazard — Pitfall 3)
**Source:** `pipeline/scrape_cead.py` lines 161–162
```python
# Keys may be int (in-memory) or str (after JSON round-trip)
raw = homicidios.get(year) if homicidios.get(year) is not None else homicidios.get(str(year))
```
`build_composite_index.py` reads already-written `comunas/{CUT}.json` (post round-trip) → always key with `str(REFERENCE_YEAR)`. `ResultPanel.tsx` → always `String(year)` (see homicide section line 323).

### Module-level constants as the single source of truth
**Source:** `pipeline/shared/schema.py` → `FAMILY_KEYS = ['vida','robos_violentos','vif','drogas','armas','propiedad','incivilidades']`
`composite_config.py` follows this: `REFERENCE_YEAR`, `WINSORIZE_LIMITS`, `METRIC_WEIGHTS` as module constants imported everywhere (config.py, index.py, build_*.py, test_composite.py). Weight vector is **locked by C-02** — copy verbatim.

---

## Pattern Assignments

### `pipeline/composite_config.py` (config, transform)

**Analog:** `pipeline/shared/schema.py` (`FAMILY_KEYS` module-const convention).

Module-level constants only — no functions. Weight vector is **C-02-locked** (sum = 1.00); copy these exact numbers and the 7-key set from **C-01** (incivilidades EXCLUDED):
```python
REFERENCE_YEAR: int = 2024                    # D-10 locked
WINSORIZE_LIMITS: tuple[float, float] = (0.01, 0.01)  # D-01
SII_CAP_RATIO: float = 5.0                    # D-04 locked
TOTAL_COMMUNES: int = 346

METRIC_WEIGHTS: dict[str, float] = {          # C-02 locked, sum = 1.00
    "spd_homicide_rate":   0.30,
    "cead_robos_rate":     0.20,
    "cead_vida_rate":      0.15,
    "cead_propiedad_rate": 0.12,
    "cead_vif_rate":       0.10,
    "cead_drogas_rate":    0.08,
    "cead_armas_rate":     0.05,
}
```
Note: research draft (RESEARCH §Code Examples) lists a slightly different ordering — **C-02 supersedes it.** Document verbatim in `data/SOURCES.md` + both methodology pages.

---

### `pipeline/composite_index.py` (service, pure transform)

**Analog:** `pipeline/cead/normalizer.py` — pure functions, no I/O, importable by tests.

Holds `normalize_metric()`, `get_exposure_denominator()`, `assert_year_alignment()`, `compute_composite()`. Copy the three verified function bodies from RESEARCH §Pattern 1/2/3 (winsorize+NaN re-injection, SII cap fallback, year assertion). NaN handling is the load-bearing detail:
```python
arr = np.array(series, dtype=float)
arr_w = np.array(winsorize(arr, limits=[0.01, 0.01]))
lo, hi = np.nanmin(arr_w), np.nanmax(arr_w)
result = (arr_w - lo) / (hi - lo) * 100
result[np.isnan(arr)] = np.nan   # re-inject NaN by original mask
```
SII null-vs-zero (Pitfall 1) and SPD absent-as-zero (Pitfall 2) live here: `sii_by_cut.get(cut)` returns `None` (absence) — never conflate with `0`; SPD-absent communes get `spd_homicide_rate = 0.0`.

---

### `pipeline/build_composite_index.py` (entrypoint, batch/file-I/O)

**Analog:** `pipeline/scrape_cead.py` `_write_all_outputs()` (lines 333–348) + module head (lines 20–46) + `__main__` block.

Structure to copy:
1. logging.basicConfig + `logger = logging.getLogger(__name__)` (lines 31–35)
2. `_get_data_dir()` env-override (shared pattern above)
3. Read 4 sources: `data/snapshots/spd_homicide.json`, `data/snapshots/sii_exposure.json`, `data/ine/poblacion_comunal.json`, `data/cead/comunas/{CUT}.json` (346 files)
4. `assert_year_alignment(...)` before any compute — fail loudly (RESEARCH §Year-Alignment lines 480–492)
5. Per-commune compute → enrich record in place with `composite_index`, `spd_homicide_rate`, `sii_exposure_index` (additive, D-12)
6. Write back each `comunas/{CUT}.json` via `atomic_write_json` (mirror loop at `scrape_cead.py:335-336`)
7. Write NEW `data/cead/comparator_table.json` (must carry `composite_index` per commune — Phase 21 handoff)
8. **C-03:** pre-compute BOTH `rank` (national) and `regional_rank`; store both inside the `composite_index[str(year)]` entry

Do NOT call `build_map_payload()` from here (anti-pattern, RESEARCH line 363) — it is a separate step.

---

### `pipeline/build_map_payload.py` (EXTRACTED entrypoint)

**Analog / source:** `pipeline/scrape_cead.py` `build_map_payload()` lines 102–204 — move **verbatim**, plus the orchestration at lines 323–359.

Imports the function already needs (confirmed, no circular deps):
```python
from pipeline.cead.normalizer import compute_level
from pipeline.shared.schema import FAMILY_KEYS
from pipeline.shared.atomic_write import atomic_write_json
```
Two changes on extraction:
1. **Add `ci` field** to each commune entry: read `composite_index[str(REFERENCE_YEAR)].level` (1–5) from the enriched commune file; omit/null for years without composite data (A3: encode LEVEL not raw score).
2. **Move the 30 KB assertion here** (currently `scrape_cead.py:328-331`):
```python
serialized = json.dumps(map_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
if len(serialized) >= 30720:
    raise ValueError(f"map-payload.json exceeds 30 KB limit: {len(serialized)} bytes")
```
Pitfall 4: adding `ci` (~7 B × 346 ≈ 2.4 KB) may push near 30 KB — omit `ci` when null to stay under.
Pitfall 5: REMOVE the `build_map_payload()` definition + its call (`scrape_cead.py:326`) AND the size assertion + payload writes (lines 346–359) from `scrape_cead.py` so the old embedded version cannot run.
Consumer #6: update `pipeline/tests/test_scrape_cead.py` import → `from pipeline.build_map_payload import build_map_payload`.

---

### `pipeline/tests/test_composite.py` (test)

**Analog:** `pipeline/tests/test_scrape_cead.py` lines 21–74 (`_make_records_with_homicide`, `FIXTURES_DIR`, record-builder fixtures).

Copy the record-builder helper shape (dict per commune with `id`, `series[].by_family`, `featured_rates`) — extend with `spd_homicide_rate`/`sii_exposure_index` inputs. Tests required (RESEARCH §Phase Requirements→Test Map):
- `test_composite_distribution` — spread guard: `scores.describe()["25%"] > scores.max() * 0.10` (D-01)
- `test_year_alignment` — SPD/SII/CEAD all == `REFERENCE_YEAR`
- `test_sii_cap_logic` — Providencia (CUT 13123, ratio 5.19) → INE denom; Las Condes (13114, 4.03) → SII denom
- `test_output_schema` — score is int 1–346 rank, band present, regional_rank present
Quick run: `pytest pipeline/tests/test_composite.py -x`.

---

### `site/src/components/map/ChoroplethLayer.ts` (component, event-driven)

**Analog:** `buildStyleMapFromHomicide()` lines 120–138 (same file) — the closest existing single-metric style builder.

1. Extend `CommunaPayload` interface (lines 13–22), add after `homicide_count`:
```typescript
/** Composite index level 1-5; null for pre-composite years. */
ci: number | null;
```
2. Add `buildStyleMapFromCompositeIndex()`. Unlike homicide, do NOT recompute quantile breaks client-side — the level is pre-computed in the pipeline (anti-pattern RESEARCH line 361). Copy the loop shape from lines 127–136, substituting `c.ci`:
```typescript
export function buildStyleMapFromCompositeIndex(
  comunas: CommunaPayload[]
): Map<string, L.PathOptions> {
  const m = new Map<string, L.PathOptions>();
  for (const c of comunas) {
    const level = c.ci ?? 3;
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
Mode swap reuses `applyStyleMap()` (lines 144–151) — never re-mount the layer. `MapIsland.tsx` adds toggle state defaulting to `'composite'` (D-05).

---

### `site/src/components/map/ResultPanel.tsx` (component, request-response)

**Analog:** homicide section lines 318–351 (same file) — the IIFE `(() => { ... })()` pattern, `String(year)` keying, `!== undefined` null-vs-zero guard, bilingual ternaries, `panel-section` wrapper.

1. Extend `CommuneData` interface (lines 52–71), add optional fields (D-12 additive):
```typescript
composite_index?: Record<string, {
  score: number; rank: number; regional_rank: number;
  level: 1|2|3|4|5; available_metrics: number;
}>;
spd_homicide_rate?: Record<string, number>;
sii_exposure_index?: Record<string, number | null>;
```
2. New JSX section between stat-card (sec 3) and mini-stats (sec 4). Reuse the homicide IIFE structure; render `Math.round(ci.score)` (NEVER `.toFixed` — anti-pattern); band via `BAND_EN`/`BAND_ES` arrays (D-08); national `#rank` + `regional_rank` (C-03/CI-05).
3. **Mandatory always-visible caveat** (D-07) — copy the bilingual text from RESEARCH §Pattern 5 (lines 348–352); never collapse. `TOTAL_COMMUNES = 346` const already exists (line 36).

---

### `site/src/pages/commune/[slug].astro` (route, SSR build-time)

**Analog:** same file head (lines 26–86) for data loading + `MethodologyCaveat` import (line 25) for the caveat component pattern.

1. Data loaders use `process.cwd()` via `site/src/lib/data.ts`. `loadCommune(cut)` (data.ts:167) already returns the full commune JSON — the additive `composite_index` field rides along automatically (D-12 non-breaking). Add a `loadComparatorTable()` loader to `data.ts` mirroring `loadIndex()` (data.ts:132-138, cached `readFileSync` + `JSON.parse`) if the comparator table is needed at build time.
2. Render composite score + band + national/regional rank as a static section (copy `StatCard`/`LevelChip` usage already in template).
3. **Caveat block:** clone `site/src/components/MethodologyCaveat.astro` (the established `<aside class="caveat">` + bilingual `locale` prop + `data/methodology` link pattern, lines 13–41) into an always-visible composite caveat. Strings go through `EN_STRINGS`/`ES_STRINGS` (`site/src/config/i18n.ts`) — do NOT inline raw HTML text (forbidden-language validator scans dist/).

---

### `site/src/pages/es/comuna/[slug].astro` (route, SSR)

**Analog:** the EN `commune/[slug].astro` after its edits — ES mirror. Same loaders, same composite section, ES band labels (Muy Bajo/Bajo/Moderado/Alto/Muy Alto), ES caveat string. i18n localized-slug pitfall (memory): hardcode `/es/comuna/...` cross-links; do not rely on `getRelativeLocaleUrl` for ES slugs.

---

### `site/scripts/validate/forbidden-language.mjs` (config, CI)

**Analog:** `FORBIDDEN_TERMS` array lines 35–57 + `ALLOW_LIST` lines 63–66 (same file). Accent-stripping (`normalizeAccents`, NFD) already handles `más`→`mas`.

Add to `FORBIDDEN_TERMS` (CI-09 — current array has `'the safest'` + `'la mas segura'`; these are missing):
```javascript
'most dangerous',
'mas peligrosa',
'mas peligroso',
'el mas seguro',
```
Extend `ALLOW_LIST` to permit qualified usage (D-09 — "reported/reportado"):
```javascript
/according to reported (crime|incidents)/i,
/segun (delitos|incidentes) reportados/i,
```

---

### `site/scripts/validate/figure-registry.mjs` (config, CI)

**Analog:** existing `FIGURE_REGISTRY` entries F1–F12 lines 56–179 (`{id, description, tokens:[[...]], note}` shape).

Remove the F13/F14 exclusion comment (lines 16–17, 54, 162–163) and add two entries following the F10 token-group shape (lines 136–144). Tokens must be substrings actually present in `data/SOURCES.md` after it is updated:
```javascript
{ id: 'F13', description: 'SPD VHC homicide rate per 100k (index M1)',
  tokens: [['SPD', 'homicidio'], ['Subsecretaria de Prevencion', 'homicidio']],
  note: 'SPD VHC homicide source for composite M1.' },
{ id: 'F14', description: 'SII economic-activity exposure index',
  tokens: [['SII', 'trabajadores'], ['SII', 'exposicion']],
  note: 'SII exposure denominator (cap 5.0) for composite.' },
```
Also update the header line 184 / final-message strings that hardcode "F1-F12, F15".

---

### `.github/workflows/cead-scraper.yml` (config, CI workflow)

**Analog:** "Run CEAD scraper" step lines 33–34 (same file).

Insert two steps between "Run CEAD scraper" and "Commit data if changed" (D-11 three-step order: scrape → index → payload):
```yaml
      - name: Build composite index
        run: python pipeline/build_composite_index.py

      - name: Build map payload
        run: python pipeline/build_map_payload.py
```
Keep the existing `git add data/` + commit-only-if-changed + deploy-hook gate (lines 36–52) unchanged — the new steps only add files under `data/`. If index step fails, CEAD data already refreshed in working tree but commit step still runs; planner should decide whether to `set -e` fail the job (D-11 says CEAD data should still refresh — current `run:` already fails the job on non-zero, so wrap index step with `continue-on-error` only if graceful-degrade is required).

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | None. Every file maps to an existing in-repo analog (brownfield phase). `comparator_table.json` is a NEW data file but its writer pattern is covered by `atomic_write_json` and its schema by C-03 + Phase 21 handoff requirement. |

---

## Metadata

**Analog search scope:** `pipeline/`, `pipeline/tests/`, `pipeline/shared/`, `site/src/components/map/`, `site/src/pages/commune/`, `site/src/pages/es/comuna/`, `site/src/lib/`, `site/scripts/validate/`, `.github/workflows/`
**Files read in full or targeted:** scrape_cead.py (1–215, 300–359), ChoroplethLayer.ts, ResultPanel.tsx, test_scrape_cead.py (1–80), forbidden-language.mjs, figure-registry.mjs, cead-scraper.yml, commune/[slug].astro (1–120), MethodologyCaveat.astro, atomic_write.py, data.ts (targeted grep)
**Pattern extraction date:** 2026-06-19
