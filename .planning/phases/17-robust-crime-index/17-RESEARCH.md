# Phase 17: Data Quality, Source Traceability & Methodology — Research

**Researched:** 2026-06-18
**Domain:** Data-quality verification, source attribution, methodology rewrite, reproducible pipeline snapshots
**Confidence:** HIGH — all findings derived from direct codebase inspection; no external lookups needed

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-SCOPE:** focused data-quality/traceability/methodology pass; composite index + schema migration deferred to Phase 18. No displayed-metric change.
- **D-ORDER:** this phase (17) runs BEFORE Phase 16 (news) so the source registry + methodology are authoritative before news adds its own attribution.
- **D-SOURCES (from Wave 0, authoritative):**
  - Homicide truth = SPD VHC (`prevenciondehomicidios.cl`, comuna-level, 2018–2025). CEAD grupo 101 mixes homicidio+femicidio and ignores `subgrupo[]` → cite SPD as the authoritative homicide source.
  - Secuestro = Fiscalía/Ministerio Público (regional granularity only; absent from CEAD taxonomy entirely). Region-level attribution.
  - Exposure proxy = SII `PUB_COMU.xlsb` (trabajadores dependientes / FTE per comuna, 2005–2024) — snapshot now for Phase 18; document the HQ/domicile caveat.
  - CEAD remains the source for the displayed incidence rates (casos policiales, `tipoVal=1,2`, `medida=2`), host = `cead.minsegpublica.gob.cl`.
- **D-VERIFY:** use **BrowserOS** to visually verify the rewritten methodology pages (EN+ES) render with working clickable source links, and that sampled commune/ranking figures still cite source+year correctly.

### Claude's Discretion
- Location/format of `data/SOURCES.md` registry.
- Exact section structure within the rewritten methodology pages (must preserve bilingual parity and include all caveats listed in DQ-03).
- Whether to add a lightweight Python test for the 3 snapshot scripts, or rely only on the build+validate chain.

### Deferred Ideas (OUT OF SCOPE)
- Exposure-adjusted composite index + the SII denominator formula.
- Homicide metric switch to SPD in the map/panel (display change).
- `featured_rates` → 7-metric schema migration (lesiones 103/104/105, secuestro metric, dropping the `vida` aggregate).
- Index-driven choropleth, dual index+count display, multi-measure aggregation in the displayed number.
- News-layer work (Phase 16, runs AFTER this phase).
- Secuestro comuna-level source (S5b).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DQ-01 | Data-quality verification report `17-DATA-QUALITY.md` — cross-check every surfaced metric/series against source using offline CEAD cache + Wave 0 facts; re-verify 4 anomalies; partial-year flags on every surfaced figure; range/sanity checks pass; tipoVal semantics + drug scope confirmed | Cache files in `pipeline/cache/` are sufficient for offline verification without live gov requests. Section DQ-01 maps all computation paths. |
| DQ-02 | Canonical source registry `data/SOURCES.md`; fix wrong CEAD host (`cead.ministeriointerior.gob.cl` → `cead.minsegpublica.gob.cl`) everywhere it appears | 4 occurrences of the wrong host enumerated below. |
| DQ-03 | Methodology EN + ES rewrite — bilingual parity, clickable sources, all caveats, legal-safe tone; BrowserOS visual verification | Both pages are self-contained `.astro` files; `forbidden-language.mjs` validator (#9) provides the gate; no shared component exists — edits needed in both files in parallel. |
| DQ-04 | Reproducible normalized snapshots (SPD homicide, SII exposure, Fiscalía secuestro) under `data/`; fetch/normalize scripts in `pipeline/`; reference-only, not wired to UI | `pyxlsb` + `pandas` + `openpyxl` already in `requirements.txt`; cache files `spd_vhc.xlsx` + `sii_pub_comu.xlsb` already in `pipeline/cache/` from Wave 0; pattern shown in Section DQ-04. |
</phase_requirements>

---

## Summary

Phase 17 is a data-correctness + attribution pass over an existing, working site. No schema changes, no displayed-metric changes. The research is fully codebase-driven: all key facts (anomalies, host strings, methodology structure, partial-year guard logic, pipeline conventions) are confirmed from the live repo.

The single most important implementation-time insight: **the CEAD cache in `pipeline/cache/` (`cead_15_*.html` pattern, ~199 files) already contains all-commune data** — the CEAD endpoint ignores the `region[]` param and returns all 346 communes per `familia+year` request. This means DQ-01 verification runs fully offline against the cache, with no Chilean-gov egress required from the cloud sandbox. The DQ-01 script should re-parse those same HTML files using `pipeline/cead/parser.parse_cead_table()` and compare parsed values against the committed `data/cead/comunas/*.json` files.

The methodology pages (`site/src/pages/methodology.astro` and `site/src/pages/es/metodologia.astro`) are **fully self-contained** — same 6 H2 sections, duplicated (not shared-component). Both must be edited in the same task to maintain bilingual parity. The forbidden-language validator (#9 in `all.mjs`) runs against `dist/` HTML after build, which is the correct gate.

The wrong CEAD host appears in **4 files** (enumerated below). Two of them are the methodology pages (DQ-03 overlap); two are `terms.astro`/`terminos.astro` (bonus fix).

**Primary recommendation:** DQ-01 (verification report) → DQ-02 (source registry + host fix) → DQ-03 (methodology rewrite) → DQ-04 (snapshot scripts) → chained build+validate+BrowserOS.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Data-quality verification (DQ-01) | Python pipeline (`pipeline/`) | Static JSON store (`data/cead/`) | Offline re-parse of cache vs committed JSONs; no frontend involvement |
| Source registry (DQ-02) | Static repo artifact (`data/SOURCES.md`) | — | Reference document; consumed by methodology page + future phases |
| Host-string fixes (DQ-02) | Astro pages + terms pages | — | Simple string replacement in 4 `.astro` files |
| Methodology rewrite (DQ-03) | Astro pages (`site/src/pages/`) | Build validator (`site/scripts/validate/`) | Page content change + validator gate; no React islands involved |
| Snapshot scripts (DQ-04) | Python pipeline (`pipeline/snapshots/`) | Static JSON store (`data/snapshots/`) | New subdir of pipeline following existing conventions |
| Build + validate gate | npm scripts (`site/`) | — | `npm run build && npm run validate` — must be one chained command (OneDrive desync) |
| Visual verification | BrowserOS | — | Locked in D-VERIFY |

---

## DQ-01: Data-Quality Verification Harness

### Cache structure and offline re-parse strategy

The CEAD cache lives at `pipeline/cache/` (git-ignored). Files follow naming:
- `cead_15_{familia_id}_{year}.html` — all 346 communes per familia/year (region "15" is a dummy; endpoint ignores it)
- `cead_subgroup101_{year}_{measure_key}.html` — homicide grupo 101, medida=1 (count) or medida=2 (rate)

Coverage as of 2026-06-16:
- Region 15 × 7 familias × years 2005–2026 = up to 154 files (some years may be missing)
- Subgroup 101 × 22 years × 2 measures = up to 44 files
- Total: ~199 HTML files currently cached

All 346 communes appear in every `cead_15_*.html` file (confirmed: both Providencia and San Joaquín found in `cead_15_1_2024.html`, which has 440 `<tr>` tags).

**Offline re-parse tool:** `pipeline/cead/parser.parse_cead_table(html)` returns `[{name, values: {year: 'NNN,0000000000'}}]`. Use `pipeline/cead/parser.parse_cead_float()` to convert. Use `pipeline/cead/_match_cut(name, catalog)` to join to CUT (this is already battle-tested).

**DQ-01 script pattern:**
```python
# pipeline/scripts/verify_data_quality.py
# Re-parse cache → compare against data/cead/comunas/*.json → emit 17-DATA-QUALITY.md
from pipeline.cead.parser import parse_cead_table, parse_cead_float
from pipeline.cead.client import load_cached

# For each familia × year:
html = load_cached(f"cead_15_{familia_id}_{year}.html")
if html:
    rows = parse_cead_table(html)  # [{name, values}]
    # Compare vs committed JSON for sampled communes
```

### The 4 anomalies — what they are and where they live in the data

**Providencia (CUT 13123):**
- `featured_rates.propiedad` = 4,423.5/100k in 2024
- `data/cead/comunas/13123.json` — `series[year=2024].by_family.propiedad`
- Explanation: floating-population denominator. Providencia is a business/daytime hub; CEAD uses INE resident population (~82k) but daytime population is 3–4× higher. Rate is mathematically correct; the denominator is resident-only. Document in methodology.
- No code fix needed; explanation required.

**Lo Barnechea (CUT 13115):**
- Similar pattern to Providencia: high-income residential + business area produces unusual rate patterns
- `data/cead/comunas/13115.json`
- Verify: `series[year=2024].rate_per_100k` = 2,544.8; this is the total family sum. No anomaly in the total but individual family rates need sanity check.

**San Joaquín (CUT 13129):**
- `featured_rates.homicidios_count` 2024=11, 2025=1
- **Root cause:** The partial-year guard in `scrape_cead.py::mark_partial_year()` marks only the **current calendar year** (2026 when pipeline ran 2026-06-16) as partial. Year 2025 is treated as complete even though CEAD may not have closed the 2025 annual series.
- The series record for 2025: `partial=False` — this is technically correct per the current implementation (pipeline ran June 2026; 2025 is a "past year"). But from a data-quality perspective, 2025 CEAD data (and SPD 2025) is noted as unconsolidated in Wave 0.
- **Action:** DQ-01 must document this explicitly. The partial-year guard is operating as designed, but the design assumption (all past years are consolidated) may not hold for the most recent scrape year. The methodology should add a note: "2025 data is included but may not represent the complete closed annual series."

**Recoleta (CUT 13127):**
- `featured_rates.homicidios_count` 2024=34 → rate=17.3/100k
- Verify: population ~196k; 34/196000×100000 = 17.3 — mathematically correct.
- Highest homicide rate in the national dataset for 2024. A sanity check: does this match SPD VHC data for Recoleta? (SPD file is at `pipeline/cache/spd_vhc.xlsx` — can cross-check offline.)

### Partial-year guard analysis

Location: `pipeline/scrape_cead.py::mark_partial_year()` (lines 66–89).

Logic: `is_partial = run_date < datetime.date(current_year, 12, 31)` where `current_year = run_date.year`. Applied per series year: only marks `year == current_year`.

With the pipeline run on 2026-06-16:
- Year 2026: `partial=True` ✓
- Year 2025: `partial=False` (treated as complete)
- Trend + national_rank use the latest non-partial year = 2025 for all communes.

**Downstream consumers of `partial`:**
1. `filter_series_for_trend()` — excludes partial years from trend computation
2. `_write_all_outputs()` — last_complete_year derived from non-partial records
3. Frontend sparkline (in the map island) — needs verification that it respects `partial`

**Drug scope confirmation:** CEAD `drogas` family = familia 4 (id 4xx groups) = Ley 20.000 grupos. Drug consumption = grupo 702 under incivilidades. Already confirmed in `quick-260616-klv`. The `by_family.drogas` in commune JSONs is Ley 20.000 only. Document explicitly in methodology.

**tipoVal confirmation:** Additive, confirmed in Wave 0 (S4). The pipeline uses `tipoVal='1,2'` (casos policiales = denuncias + detenciones). See `pipeline/cead/client.py` line 113: `"tipoVal": "1,2"`. The methodology correctly says "casos policiales — both formal complaints and arrests" but does NOT name the `tipoVal` codes or explain additivity. Add in DQ-03.

### Evidence report format — `17-DATA-QUALITY.md`

Location: `.planning/phases/17-robust-crime-index/17-DATA-QUALITY.md`

Structure:
```markdown
# 17-DATA-QUALITY.md — Phase 17 Data Quality Evidence Report

## Summary: N checks, N passed, N flags

## Check 1: CEAD host string [PASS/FAIL]
## Check 2: tipoVal semantics confirmed [PASS]
## Check 3: partial-year guard coverage [PASS with caveat]
## Check 4: drug scope (Ley 20.000 only) [PASS]
## Check 5: Providencia propiedad rate 4,423/100k — explained [PASS — by design]
## Check 6: Lo Barnechea rate patterns [PASS/FAIL + evidence]
## Check 7: San Joaquín homicide 2025=1 count [DOCUMENTED — partial year caveat]
## Check 8: Recoleta homicide 2024=34 — cross-check vs SPD VHC [PASS/FAIL + evidence]
## Check 9: national/regional aggregation = population-weighted mean [PASS — quick-260616-klv]
## Check 10: range/sanity — rates in [0, 100000] for all communes [PASS/FAIL]
```

---

## DQ-02: Source Registry and Host String Fixes

### Wrong host occurrences — complete enumeration

`cead.ministeriointerior.gob.cl` appears in **4 source files**:

| File | Line(s) | Context |
|------|---------|---------|
| `site/src/pages/methodology.astro` | line 71 | `(<code>cead.ministeriointerior.gob.cl</code>)` |
| `site/src/pages/es/metodologia.astro` | line 64 | `(<code>cead.ministeriointerior.gob.cl</code>)` |
| `site/src/pages/terms.astro` | lines 65–66 | `<a href="https://cead.ministeriointerior.gob.cl">` |
| `site/src/pages/es/terminos.astro` | lines 71–72 | `<a href="https://cead.ministeriointerior.gob.cl">` |

Correct host (confirmed from `pipeline/cead/client.py` line 27): `cead.minsegpublica.gob.cl`

The `methodology.astro` and `metodologia.astro` fixes overlap with DQ-03 (methodology rewrite). The `terms.astro` and `terminos.astro` fixes are a separate, simpler task within DQ-02.

Planning note: The `terms.astro` / `terminos.astro` host fix should be its own atomic step (not bundled with the full methodology rewrite) so it can be committed and verified independently.

### Canonical source registry — recommended location and format

Location: `data/SOURCES.md` (repo root of the `data/` tree, not `.planning/`)

Rationale: The `data/` directory is the project's canonical data store (per CLAUDE.md: "JSON in repo as data store"). `SOURCES.md` is the provenance companion to that store. It is committed to git, visible to anyone who clones the repo, and referenced from the methodology pages.

Format pattern:
```markdown
# Data Sources — ischilesafe.com

## CEAD (displayed incidence rates)

- **Full name:** Centro de Estudios y Análisis del Delito
- **Host:** `cead.minsegpublica.gob.cl`
- **Endpoint:** `https://cead.minsegpublica.gob.cl/wp-content/themes/gobcl-wp-master/data/get_estadisticas_delictuales.php`
- **Measure:** casos policiales (`tipoVal=1,2` = denuncias + detenciones; additive)
- **Metric:** tasa por 100.000 habitantes (`medida=2`); INE population denominator
- **Coverage:** 346 comunas × familias 1–7 × 2005–present
- **Drug scope:** Familia 4 = Ley 20.000 grupos (criminal drug offences); drug consumption = grupo 702 (incivilidades) — distinct categories
- **Vintage:** updated annually; last pipeline run [date]

## SPD — Homicidio (reference snapshot, not displayed)
...

## SII — Exposure proxy (reference snapshot, not displayed)
...

## Fiscalía — Secuestro (reference snapshot, not displayed)
...

## chilemapas (map geometry)
...
```

---

## DQ-03: Methodology Rewrite

### Page structure — current state

Both pages are self-contained `.astro` files with **identical 6-section H2 structure** (no shared component):

| # | EN H2 | ES H2 |
|---|-------|-------|
| 1 | Data source: CEAD | Fuente de datos: CEAD |
| 2 | Map boundaries: chilemapas | Geometría del mapa: chilemapas |
| 3 | How the rate is calculated | Cómo se calcula la tasa |
| 4 | Underreporting (cifra negra) | Subregistro (cifra negra) |
| 5 | Trend formula | Fórmula de tendencia |
| 6 | Comparison criteria | Criterios de comparación |
| 7 | What this site does NOT say | Lo que este sitio NO dice |

Note: section numbers above disagree with the file comment (which lists 6 sections) because "Map boundaries" was added in Phase 10 without updating the comment.

### Changes needed per section (DQ-03)

**Section 1 — Data source: CEAD (EN) / Fuente de datos: CEAD (ES)**

All of these changes cluster here:
1. Replace wrong host `cead.ministeriointerior.gob.cl` → `cead.minsegpublica.gob.cl` (make it a clickable `<a>` link, not just `<code>`)
2. Add `tipoVal=1,2` semantics: "We use casos policiales, which combines denuncias (formal complaints, `tipoVal=1`) and detenciones flagrantes (flagrante arrests, `tipoVal=2`). These two measures are additive at the offence level."
3. Add drug-scope caveat: "The 'drogas' (drugs) category covers criminal offences under Ley 20.000 (drug trafficking and related crimes). Drug consumption offences appear under the 'incivilidades' category."
4. Name SPD, SII, Fiscalía as the authoritative sources for the figures they underpin, with clickable links: SPD homicide → `https://prevenciondehomicidios.cl`, SII exposure → `https://www.sii.cl/sobre_el_sii/estadisticas_de_empresas.html`, Fiscalía secuestro → `https://www.fiscaliadechile.cl/persecucion-penal/estadisticas`

**Section 3 — Rate calculation**

Add floating-population denominator caveat: "Communes that serve as major business or commercial hubs (e.g., Providencia, Las Condes) may show higher reported rates partly because the INE resident-population denominator undercounts the daytime working population. The rate is mathematically correct using the official INE figure; the caveat is that the denominator is resident-based, not activity-based."

**Add partial-year note (best placed after rate calculation):**

Current text says "partial years... are excluded from rates and rankings." This is only true for 2026 (current calendar year). 2025 data IS included and is treated as complete. Add: "The most recent annual series included in this build is [year]. Data for years before the current calendar year is treated as complete; if CEAD has not yet closed the [year] annual series, some figures may differ from the final published values."

**Section 4 — Underreporting**

No structural change needed. (Homicide reliability note is already there and remains valid.)

**What this site does NOT say**

No structural change needed — but ensure the methodology does not introduce any absolute-safety language in the new sections. The `forbidden-language.mjs` validator (#9) will catch this automatically after build.

### Bilingual parity strategy

No shared component exists. The parity pattern established in the codebase is: **write EN first, immediately write ES mirror, commit both in one task.** The planner should structure DQ-03 as a single task that edits both files atomically, not two separate tasks, to prevent drift.

### Forbidden-language validator — invocation

**Validator:** `site/scripts/validate/forbidden-language.mjs` (validator #9 in `all.mjs`)

**When invoked:** as part of `npm run validate` (which runs `node scripts/validate/all.mjs`). Must have a fresh `dist/` from `npm run build`.

**Invocation (OneDrive-safe, chained):**
```bash
cd site && npm run build && npm run validate
```

This is the correct chained command per the OneDrive build-artifacts-desync memory — build and validate must be one chained command so `dist/` is not swept between processes.

**The validator scans `dist/` visible text** after stripping script/style blocks. It will catch any forbidden term added to the methodology pages. Terms include `'the safest'`, `'dangerous zone'`, `'zona segura'`, etc.

---

## DQ-04: Snapshot Scripts — Implementation Pattern

### Available assets from Wave 0

The following files already exist in `pipeline/cache/` (from Wave 0 probes):
- `pipeline/cache/spd_vhc.xlsx` — SPD VHC microdata, 8,669 rows, columns include `COMUN_AGR`, `ID_ANO`
- `pipeline/cache/sii_pub_comu.xlsb` — SII PUB_COMU, 6,940 rows, 2005–2024, 347 comunas

Fiscalía secuestro: no raw download file in cache; regional figures from PDFs/press releases (868 in 2024). The normalize script will embed the known regional series from Wave 0.

### Recommended directory layout

```
pipeline/
  snapshots/
    __init__.py
    fetch_spd_homicide.py       # download + normalize VHC xlsx → data/snapshots/spd_homicide.json
    fetch_sii_exposure.py       # download + normalize PUB_COMU.xlsb → data/snapshots/sii_exposure.json
    fetch_fiscalia_secuestro.py # embed known regional series → data/snapshots/fiscalia_secuestro.json

data/
  snapshots/
    spd_homicide.json           # {source, vintage, fetched, records: [{cut, name, year, homicides}]}
    sii_exposure.json           # {source, vintage, fetched, records: [{cut, name, year, empresas, trabajadores}]}
    fiscalia_secuestro.json     # {source, vintage, fetched, records: [{region, year, secuestros}]}
    ATTRIBUTION.md              # one-liner per file: source name, URL, licence, vintage
```

### Script pattern — reuse existing pipeline conventions

All existing pipeline scripts share these conventions (from `probe_spd_homicide.py`, `probe_sii_comu.py`, `scrape_cead.py`):

```python
"""
pipeline/snapshots/fetch_spd_homicide.py

Reproducible fetch + normalize of SPD VHC homicide microdata.

Source: Subsecretaría de Prevención del Delito / Centro para la Prevención de Homicidios
URL: https://prevenciondehomicidios.cl/wp-content/uploads/2026/03/Base_de_Datos_VHC_2018_2025.xlsx
Vintage: 2018–2025 (partial 2025)
Licence: Datos Abiertos Gobierno de Chile

Output: data/snapshots/spd_homicide.json
  {
    "source": "SPD VHC",
    "source_url": "https://prevenciondehomicidios.cl/...",
    "vintage": "2018-2025",
    "fetched": "YYYY-MM-DD",
    "caveat": "2025 partial/unconsolidated; COMUN_AGR is name string, joined to CUT via data/cead/meta/catalog.json",
    "records": [{"cut": "13101", "name": "Santiago", "year": 2024, "homicides": 31}]
  }

Usage:
  python pipeline/snapshots/fetch_spd_homicide.py
  CACHE_ONLY=1 python pipeline/snapshots/fetch_spd_homicide.py  # re-parse from cache/spd_vhc.xlsx
"""
import pathlib, json, datetime, os
import requests
import pandas as pd

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
CACHE = REPO_ROOT / "pipeline" / "cache"
OUT_DIR = REPO_ROOT / "data" / "snapshots"
URL = "https://prevenciondehomicidios.cl/wp-content/uploads/2026/03/Base_de_Datos_VHC_2018_2025.xlsx"

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE / "spd_vhc.xlsx"

    if not os.environ.get("CACHE_ONLY") or not dest.exists():
        r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0 (compatible; IsChileSafe; +https://ischilesafe.com)"}, timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)

    df = pd.read_excel(dest, sheet_name="Base de Datos")
    # aggregate: count rows per COMUN_AGR × ID_ANO
    agg = df.groupby(["COMUN_AGR", "ID_ANO"]).size().reset_index(name="homicides")

    # join to CUT via catalog
    catalog = json.loads((REPO_ROOT / "data/cead/meta/catalog.json").read_text(encoding="utf-8"))
    # ... name→CUT join with normalization ...

    records = [...]
    out = {
        "source": "SPD VHC",
        "source_url": URL,
        "vintage": "2018-2025",
        "fetched": datetime.date.today().isoformat(),
        "caveat": "2025 partial/unconsolidated; COMUN_AGR joined to CUT via catalog name normalization",
        "records": records,
    }
    (OUT_DIR / "spd_homicide.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
```

### SPD name→CUT join

`COMUN_AGR` is a name string (e.g., "Santiago", "San Joaquín"). The CUT join must use the same slug normalization as `pipeline/cead/normalizer.make_slug()` to handle diacritics. The catalog at `data/cead/meta/catalog.json` maps CUT→name (or `data/cead/meta/index.json` maps CUT + name + slug). Use `make_slug(COMUN_AGR)` == `make_slug(commune_name)` for matching. Document unmatched names.

### SII script specifics

- Source: `pipeline/cache/sii_pub_comu.xlsb` (already downloaded; re-download if not present)
- Engine: `pyxlsb` (already in `requirements.txt`)
- Header row: index 4 (confirmed in Wave 0 `probe_sii_comu.py`)
- Columns of interest: `Comuna del domicilio o casa matriz`, `Número de empresas`, `Número de trabajadores dependientes informados`, `Trabajadores ponderados por meses trabajados`
- Drop the `Sin Información` bucket row (CUT unmatchable)
- Caveat: empresa HQ/domicile, not physical establishment location

### Fiscalía script (regional, no download)

No downloadable dataset was found in Wave 0 (PDFs only). The `fetch_fiscalia_secuestro.py` script embeds the known regional series as a static dict and writes it to JSON:
- 2024: 868 nationally (top regions: RM Sur, RM Centro Norte, Valparaíso)
- Attribution: Fiscalía de Chile Boletín Estadístico, `https://www.fiscaliadechile.cl/persecucion-penal/estadisticas`
- Note in output JSON: "Regional granularity only; fiscalía regions ≠ administrative regions (RM split); comuna-level not available (S5b deferred)"

### OneDrive build desync — DQ-04 validation

The snapshot files go to `data/snapshots/` (not `dist/`). The existing build validators do not scan `data/`. Validation for DQ-04 is:
1. **File-existence check:** assert `data/snapshots/spd_homicide.json`, `sii_exposure.json`, `fiscalia_secuestro.json` exist with non-empty `records` arrays
2. **Schema check in script:** the script itself validates output before writing (raise on empty records)
3. **Build+validate chain is still required** to confirm the methodology page changes don't break existing validators

---

## Standard Stack (this phase)

### Python (snapshot scripts)
| Library | Version (requirements.txt) | Use |
|---------|---------------------------|-----|
| requests | 2.34.2 | HTTP download for SPD + SII |
| pandas | 2.3.3 | DataFrame aggregation (VHC row-count, SII reshape) |
| openpyxl | 3.1.5 | Read `.xlsx` (SPD VHC) |
| pyxlsb | 1.0.10 | Read `.xlsb` (SII PUB_COMU) |
| tenacity | 9.1.4 | Retry for HTTP (reuse pattern from cead/client.py) |

All already in `pipeline/requirements.txt`. No new dependencies.

### Astro (methodology rewrite)
Standard project Astro 6.4.x. The methodology pages use `EditorialLayout` and plain HTML with `<a>`, `<code>`, `<ul>`, `<ol>` — no React islands, no client-side JS. Standard Astro static pre-rendering.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CEAD HTML parsing | Custom regex parser | `pipeline/cead/parser.parse_cead_table()` | Already battle-tested; handles latin-1, CEAD's float format |
| Name→CUT join | String comparison | `pipeline/cead/normalizer.make_slug()` + index.json | Diacritic normalization already solved |
| Atomic JSON write | `f.write()` | `pipeline/shared/atomic_write.atomic_write_json()` | Crash-safe; already used everywhere |
| Forbidden-language check | Manual grep | `forbidden-language.mjs` validator | Already integrated in `all.mjs` #9; runs against built dist/ |
| Partial-year detection | Custom date logic | `scrape_cead.mark_partial_year()` | Already exists; DQ-01 should call it or reference its logic |

---

## Common Pitfalls

### Pitfall 1: Editing only one of the two methodology files

`methodology.astro` and `es/metodologia.astro` are fully duplicated (no shared component). An edit to one that is not mirrored in the other causes bilingual parity failure. The planner must structure DQ-03 as a single atomic task that edits both files.

### Pitfall 2: OneDrive build artifact desync

`dist/` is swept between separate shell processes. The correct command is always:
```bash
cd site && npm run build && npm run validate
```
Never `npm run build` then (in a new shell) `npm run validate`.

### Pitfall 3: Wrong CEAD host in terms pages

`terms.astro` and `terminos.astro` also contain the wrong host. These are separate pages not touched by the methodology rewrite. A DQ-02 task must fix them. Don't forget them.

### Pitfall 4: SPD COMUN_AGR name normalization

The SPD VHC uses Chilean commune names with diacritics (San Joaquín, Ñuñoa, etc.). The name→CUT join must use `make_slug()` or equivalent NFD normalization — a bare `.lower()` comparison will fail ~30 of 315 communes. Also: ~31 communes with zero homicides 2018–2025 will be absent from SPD; the snapshot should represent them as missing (not zero) to distinguish "no homicides" from "no data."

### Pitfall 5: SII `Sin Información` row

`PUB_COMU.xlsb` has a `Sin Información` commune bucket that must be dropped before JSON output. It has no CUT and represents unattributed records.

### Pitfall 6: SII header row index

The SII file has a header on row index 4 (not 0). Using `pd.read_excel(..., engine='pyxlsb')` without specifying `header=4` will produce incorrect column names. See `probe_sii_comu.py` for the confirmed reading pattern.

### Pitfall 7: Committing large raw files

`spd_vhc.xlsx` (~547KB) and `sii_pub_comu.xlsb` (~1.2MB) must NOT be committed to git. They stay in `pipeline/cache/` (git-ignored). Only the normalized JSON snapshots under `data/snapshots/` are committed.

### Pitfall 8: 2025 partial-year communication

The current partial-year guard only marks 2026 partial (pipeline run in June 2026). 2025 is treated as complete and IS surfaced in rankings/trends. The methodology must accurately state which year is the "latest complete year" surfaced, and add a note that recent-year data may not yet be the final closed annual series from CEAD. Do NOT change the partial-year guard logic (that is a schema/display change, deferred to Phase 18).

---

## Code Examples

### Offline CEAD cache re-parse (for DQ-01)
```python
# Source: pipeline/cead/client.py::load_cached + pipeline/cead/parser.parse_cead_table
from pipeline.cead.client import load_cached
from pipeline.cead.parser import parse_cead_table, parse_cead_float

familia_id = 1   # vida
year = 2024
html = load_cached(f"cead_15_{familia_id}_{year}.html")
if html:
    rows = parse_cead_table(html)
    # rows: [{"name": "Santiago", "values": {"2024": "19481,9263369949", ...}}, ...]
    for row in rows:
        rate_str = row["values"].get(str(year))
        rate = parse_cead_float(rate_str)  # → 19481.93 or None
```

### Reading committed commune JSON (for DQ-01 cross-check)
```python
import json, pathlib
d = json.loads(pathlib.Path(f"data/cead/comunas/{cut}.json").read_text(encoding="utf-8"))
series = {s["year"]: s for s in d["series"]}
rate_2024 = series.get(2024, {}).get("rate_per_100k")
hom_2024 = d["featured_rates"].get("homicidios", {}).get("2024")
```

### Methodology page `<a>` link pattern (Astro)
```astro
<!-- Source-cited link: always rel="noopener noreferrer" on external links -->
<a href="https://cead.minsegpublica.gob.cl/estadisticas-delictuales/"
   rel="noopener noreferrer"
   target="_blank">cead.minsegpublica.gob.cl</a>
```

### Chained build+validate (OneDrive-safe)
```bash
cd site && npm run build && npm run validate
```

---

## Project Constraints (from CLAUDE.md)

- **Legal tone:** never classify any commune/city/region as "safe" or "dangerous" in absolute terms; always attribute sources. The `forbidden-language.mjs` validator enforces this automatically.
- **Static pre-rendered HTML:** methodology pages must remain Astro `.astro` files rendered to static HTML — no client-side rendering of any content critical to SEO or attribution.
- **$0 infrastructure:** no new services, APIs, or paid tools needed in this phase.
- **Python conventions:** Pydantic v2 syntax only; no v1 `@validator` or `parse_obj`.
- **Data store:** small normalized JSON committed to `data/`; raw xlsx/xlsb stay in `pipeline/cache/` (git-ignored).
- **Scraping courtesy:** delays between requests; respect robots/ToS. The snapshot scripts should add `time.sleep(1)` if fetching from gov endpoints.
- **DeepSeek model IDs:** `deepseek-v4-flash` / `deepseek-v4-pro` only — never `deepseek-chat` / `deepseek-reasoner`. (Not relevant to this phase — no LLM calls.)

---

## Validation Architecture

`workflow.nyquist_validation: true` in `.planning/config.json` → include this section.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x (`pipeline/pytest.ini`) + Node.js validators (`site/scripts/validate/all.mjs`) |
| Config file | `pipeline/pytest.ini` |
| Quick run command | `cd site && npm run build && npm run validate` |
| Full suite command | `cd pipeline && pytest tests/ && cd ../site && npm run build && npm run validate` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Signal | File Exists? |
|--------|----------|-----------|-----------------|-------------|
| DQ-01 | `17-DATA-QUALITY.md` exists; all checks pass/documented | Script output | `test -f .planning/phases/17-robust-crime-index/17-DATA-QUALITY.md && grep -c "PASS" ... ` | ❌ Wave 0 gap — new script |
| DQ-01 | Partial-year flag present on 2026 in all 346 commune JSONs | Python assert | `python -c "import json,pathlib; [assert any(s.get('partial') for s in json.loads(f.read_text('utf-8'))['series'] if s['year']==2026) for f in pathlib.Path('data/cead/comunas').glob('*.json')]"` | ✅ existing data |
| DQ-01 | No 2025 series entry shows `partial=True` (design verified) | Python assert | Inline python check in DQ-01 script | ✅ existing data |
| DQ-02 | Wrong host string absent from all built HTML | grep on dist/ | `grep -r "ministeriointerior.gob.cl" site/dist/ && echo FOUND || echo CLEAN` | ✅ after build |
| DQ-02 | `data/SOURCES.md` exists and contains all 4 source entries | file-existence + grep | `test -f data/SOURCES.md && grep -c "minsegpublica" data/SOURCES.md` | ❌ Wave 0 gap — new file |
| DQ-03 | Methodology pages render with correct host in browser | BrowserOS visual | BrowserOS navigate + screenshot `methodology/` and `es/metodologia/` | ❌ Wave 0 gap — BrowserOS task |
| DQ-03 | No forbidden language in methodology pages | `forbidden-language.mjs` | `cd site && npm run build && npm run validate` (validator #9) | ✅ existing validator |
| DQ-03 | Methodology pages contain clickable links to CEAD, SPD, SII, Fiscalía | grep on source | `grep -c "prevenciondehomicidios.cl" site/src/pages/methodology.astro` | ❌ Wave 0 gap — new content |
| DQ-04 | `data/snapshots/spd_homicide.json` exists, non-empty records | file + schema | `python -c "import json,pathlib; d=json.loads(pathlib.Path('data/snapshots/spd_homicide.json').read_text('utf-8')); assert len(d['records'])>200"` | ❌ Wave 0 gap — new file |
| DQ-04 | `data/snapshots/sii_exposure.json` exists, non-empty records | file + schema | `python -c "import json,pathlib; d=json.loads(pathlib.Path('data/snapshots/sii_exposure.json').read_text('utf-8')); assert len(d['records'])>200"` | ❌ Wave 0 gap — new file |
| DQ-04 | `data/snapshots/fiscalia_secuestro.json` exists | file + schema | `test -f data/snapshots/fiscalia_secuestro.json` | ❌ Wave 0 gap — new file |
| DQ-04 | Build + validate chain passes after snapshot files committed | `npm run validate` | `cd site && npm run build && npm run validate` | ✅ existing validators |

### Sampling Rate

- **Per task commit:** `cd site && npm run build && npm run validate`
- **Per wave merge:** full pytest + build + validate
- **Phase gate:** build green + all 12 validators pass + BrowserOS visual check of EN/ES methodology pages before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `pipeline/scripts/verify_data_quality.py` — offline cross-check script → produces `17-DATA-QUALITY.md`
- [ ] `pipeline/snapshots/fetch_spd_homicide.py` + `fetch_sii_exposure.py` + `fetch_fiscalia_secuestro.py`
- [ ] `data/snapshots/` directory + 3 JSON files
- [ ] `data/SOURCES.md` — canonical source registry
- [ ] `.planning/phases/17-robust-crime-index/17-DATA-QUALITY.md` — evidence report

---

## Security Domain

`security_enforcement: true` in config. ASVS Level 1.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth in this phase |
| V3 Session Management | No | No sessions |
| V4 Access Control | No | Static files only |
| V5 Input Validation | Partial | Snapshot scripts parse external xlsx/xlsb — use pandas with explicit dtype where possible; validate record counts before writing output |
| V6 Cryptography | No | No crypto |

Relevant threat for snapshot scripts: malformed xlsx/xlsb from government sources. Mitigate with `try/except` around `pd.read_excel()` and schema validation before writing output. Do not commit raw downloaded files.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | snapshot scripts | ✓ | 3.x (miniconda) | — |
| pandas | SII xlsb parse | ✓ | 2.3.3 (requirements.txt) | — |
| pyxlsb | SII xlsb parse | ✓ | 1.0.10 (requirements.txt) | — |
| openpyxl | SPD xlsx parse | ✓ | 3.1.5 (requirements.txt) | — |
| Node.js / npm | build + validate | ✓ | (project already uses) | — |
| BrowserOS MCP | DQ-03 visual verify | Must confirm at runtime | port 9200 | — |
| Gov egress (SPD, SII) | DQ-04 download | ❌ from sandbox | — | Use `pipeline/cache/spd_vhc.xlsx` + `sii_pub_comu.xlsb` already downloaded in Wave 0 |

**Missing dependencies with fallback:**
- SPD VHC xlsx + SII PUB_COMU xlsb: already in `pipeline/cache/` from Wave 0. Snapshot scripts should implement `CACHE_ONLY=1` env flag to re-parse from cache without re-downloading. This makes DQ-04 fully runnable from the sandbox.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pipeline/cache/spd_vhc.xlsx` is the correct VHC file (URL confirmed Wave 0, file present) | DQ-04 | Low — file existence verified |
| A2 | `pipeline/cache/sii_pub_comu.xlsb` header row index = 4 (confirmed Wave 0 probe) | DQ-04 | Low — confirmed by probe_sii_comu.py |
| A3 | Fiscalía secuestro 2024=868 national figure is correct (from Wave 0 press release/PDF) | DQ-04 | Low-medium — secondary source; methodology should cite the Fiscalía URL not the number directly |
| A4 | BrowserOS is available at port 9200 at execution time | DQ-03 verification | Medium — user must ensure BrowserOS is running before Wave 4 |
| A5 | The `catalog.json` commune names can be normalized with `make_slug()` to match SPD `COMUN_AGR` strings | DQ-04 | Medium — some names may differ (e.g., "Ñuñoa" vs edge cases); the script should log unmatched names |

---

## Sources

### Primary (HIGH confidence — codebase inspection)

All findings in this document are `[VERIFIED]` by direct file reads in this session:
- `pipeline/cead/client.py` — CEAD host, endpoint, tipoVal, headers
- `pipeline/scrape_cead.py` — partial-year guard implementation (`mark_partial_year`)
- `data/cead/comunas/13123.json`, `13115.json`, `13129.json`, `13127.json` — anomaly commune data
- `site/src/pages/methodology.astro` + `es/metodologia.astro` — page structure, current host string
- `site/src/pages/terms.astro` + `es/terminos.astro` — additional wrong-host occurrences
- `site/scripts/validate/all.mjs` + `forbidden-language.mjs` — validator #9 invocation
- `pipeline/requirements.txt` — available packages
- `pipeline/cache/` listing — cache file naming and coverage
- `.planning/phases/17-robust-crime-index/17-01-SUMMARY.md` + `17-02-SUMMARY.md` — Wave 0 domain facts

---

## RESEARCH COMPLETE
