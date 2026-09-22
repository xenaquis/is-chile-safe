# Phase 23: ENUSC Communal Victimization Layer — Pattern Map

**Mapped:** 2026-06-19
**Files analyzed:** 12 (4 new, 8 modified)
**Analogs found:** 12 / 12

## Analog Verification Flags

All analogs cited in RESEARCH.md were verified against the live codebase. One path correction:

- RESEARCH.md implies `site/src/pages/es/comuna/[slug].astro` as a peer of the EN template — **CONFIRMED EXISTS** at exactly that path.
- `pipeline/build_composite_index.py` additive enrichment block **CONFIRMED** at lines 345–388.
- `figure-registry.mjs` F-series highest ID = **F15** (line 192: "F1-F15"). F16 is confirmed free.
- `pipeline/cache/` git-ignore pattern **CONFIRMED**: `.gitignore` line 14 = `pipeline/cache/*`, line 15 = `!pipeline/cache/.gitkeep`. Raw XLSX is excluded; `pipeline/cache/.gitkeep` is the only tracked file inside.
- `data/snapshots/*.json` **CONFIRMED committed**: spd_homicide.json, sii_exposure.json, fiscalia_secuestro.json all present and tracked.
- `data/SOURCES.md` has existing `## ENUSC — underreporting / cifra negra` at line 292 (for F11). This is **distinct** from the new F16 section to add (`## INE ENUSC SAE — communal VHDV victimization (experimental)`).
- `data/snapshots/ATTRIBUTION.md` preamble says "REFERENCE-ONLY … not wired to any displayed metric." Phase 23 **breaks this convention**: `enusc_vhdv.json` IS wired to commune pages. The ATTRIBUTION.md entry must note the departure explicitly.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pipeline/snapshots/fetch_enusc_vhdv.py` | pipeline script | file-I/O + transform | `pipeline/snapshots/fetch_spd_homicide.py` | exact |
| `pipeline/build_enusc_enrichment.py` | pipeline script | CRUD (additive write) | `pipeline/build_composite_index.py` lines 345–388 | role-match |
| `data/snapshots/enusc_vhdv.json` | data artifact | — | `data/snapshots/spd_homicide.json` (shape) | exact |
| `data/snapshots/ATTRIBUTION.md` | docs | — | existing ATTRIBUTION.md blocks | exact |
| `pipeline/tests/test_fetch_enusc_vhdv.py` | test | — | `pipeline/tests/test_composite.py` | role-match |
| `pipeline/tests/test_build_enusc_enrichment.py` | test | — | `pipeline/tests/test_composite.py` | role-match |
| `site/src/pages/commune/[slug].astro` | page template | request-response (SSG) | itself (section 6b, lines 219–241) | exact (self-extension) |
| `site/src/pages/es/comuna/[slug].astro` | page template | request-response (SSG) | itself (section 6b, line 225) | exact (self-extension) |
| `site/src/config/i18n.ts` | config | — | itself (Phase 18-04 CI keys, lines 151–159) | exact (self-extension) |
| `site/src/lib/data.ts` | type definition | — | itself (composite_index field, lines 66–68) | exact (self-extension) |
| `site/scripts/validate/figure-registry.mjs` | validator | — | itself (F15 entry, lines 178–191) | exact (self-extension) |
| `data/SOURCES.md` | docs | — | itself (## ENUSC block, lines 292–316) | exact (self-extension) |
| `.github/workflows/cead-scraper.yml` | CI/CD | event-driven | itself (continue-on-error steps, lines 37–43) | exact (self-extension) |
| `site/scripts/validate/commune.mjs` | validator | — | itself (dist/ HTML inspection loop, lines 1–60+) | exact (self-extension) |
| `site/src/pages/methodology.astro` + `es/metodologia.astro` | content page | — | existing ENUSC H2 section in each file | role-match |

---

## Pattern Assignments

### `pipeline/snapshots/fetch_enusc_vhdv.py` (pipeline script, file-I/O + transform)

**Analog:** `pipeline/snapshots/fetch_spd_homicide.py`

**Imports pattern** (lines 17–34 of analog):
```python
from __future__ import annotations

import json
import logging
import os
import sys
import pathlib
import time
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd  # noqa: E402
from tenacity import retry, stop_after_attempt, wait_exponential  # noqa: E402

from pipeline.cead.normalizer import make_slug  # noqa: E402
from pipeline.shared.atomic_write import atomic_write_json  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)
```

**Path constants pattern** (lines 39–48 of analog):
```python
CACHE_DIR = REPO_ROOT / "pipeline" / "cache"
CACHE_FILE = CACHE_DIR / "spd_vhc.xlsx"
OUTPUT_FILE = REPO_ROOT / "data" / "snapshots" / "spd_homicide.json"
INDEX_FILE = REPO_ROOT / "data" / "cead" / "meta" / "index.json"
```
For ENUSC, replace with:
```python
CACHE_FILE = CACHE_DIR / "enusc_vhdv.xlsx"
OUTPUT_FILE = REPO_ROOT / "data" / "snapshots" / "enusc_vhdv.json"
KNOWN_SHA256 = "ad9503826fd21590eca7cf37629872df09f3115ad0c6d80dfe5cedcb63c3d4ba"
ENUSC_SHEET = "Hoja1"
ENUSC_HEADER_ROW = 2   # 0-indexed (pandas header=2 → row 3 in Excel)
MIN_RECORDS = 136
```

**Download with retry pattern** (lines 52–68 of analog) — copy verbatim, changing URL constant. For CACHE_ONLY mode the download is skipped entirely (URL is unstable; add a config comment):
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
def _download(url: str, dest: pathlib.Path) -> None:
    import requests
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; IsChileSafe data pipeline; +https://ischilesafe.com)"
        ),
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
    }
    log.info("Downloading %s ...", url)
    time.sleep(1)
    r = requests.get(url, headers=headers, timeout=120)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    log.info("Saved %d bytes to %s", len(r.content), dest)
```

**NEW pattern — sha256 assertion** (no existing analog; add after cache-file existence check):
```python
def _assert_sha256(path: pathlib.Path) -> None:
    import hashlib
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != KNOWN_SHA256:
        raise RuntimeError(
            f"sha256 mismatch for {path}: expected {KNOWN_SHA256}, got {digest}. "
            "INE may have republished the file. Re-verify and update KNOWN_SHA256."
        )
```

**CACHE_ONLY + file-guard pattern** (lines 82–103 of analog):
```python
def main() -> None:
    cache_only = os.environ.get("CACHE_ONLY", "").strip() in ("1", "true", "yes")

    if not cache_only:
        _download(RESOLVED_URL, CACHE_FILE)
    else:
        log.info("CACHE_ONLY=1 — skipping download, parsing %s", CACHE_FILE)

    if not CACHE_FILE.exists():
        raise FileNotFoundError(
            f"Cache file not found: {CACHE_FILE}. "
            "Manually deposit pipeline/cache/enusc_vhdv.xlsx (see ATTRIBUTION.md)."
        )

    _assert_sha256(CACHE_FILE)   # NEW: verify integrity before parse
    ...
```

**Excel parse pattern** (lines 96–110 of analog — openpyxl engine, column guard):
```python
    try:
        df = pd.read_excel(str(CACHE_FILE), sheet_name=ENUSC_SHEET,
                           header=ENUSC_HEADER_ROW, engine="openpyxl")
    except Exception as exc:
        raise RuntimeError(
            f"Failed to parse {CACHE_FILE}: {exc}. "
            "File may be corrupt or sheet name changed."
        ) from exc

    # Strip whitespace from headers (ENUSC has trailing spaces/newlines)
    df.columns = [str(c).strip() for c in df.columns]

    required_cols = {"Código comuna", "Porcentaje de hogares víctimas de delitos violentos 2024",
                     "Límite inferior", "Límite superior", "Tipo de estimación",
                     "Coeficiente de variación logarítmico"}
    missing = required_cols - set(df.columns)
    if missing:
        raise RuntimeError(f"Expected columns not found: {missing}. Found: {list(df.columns)}")
```

**Direct CUT join pattern** (replaces name→slug→CUT of SPD analog):
```python
    # ENUSC: col A is CUT as raw string digits — direct join, no slug resolution needed.
    # Name→slug resolver used ONLY as redundant cross-check (log discrepancies, don't fail).
    cut_map = _build_cut_map()   # slug → (cut, canonical_name) from index.json
    records = []
    for _, row in df.iterrows():
        cut = str(row["Código comuna"]).strip().split(".")[0]  # strip any float suffix
        name = str(row["Nombre comuna"]).strip()
        vhdv_rate = float(row["Porcentaje de hogares víctimas de delitos violentos 2024"])
        ci_lower = float(row["Límite inferior"])
        ci_upper = float(row["Límite superior"])
        tipo = str(row["Tipo de estimación"]).strip()
        cv = float(row["Coeficiente de variación logarítmico"])

        # Cross-check: name→slug should resolve to same CUT
        slug = make_slug(name)
        resolved = cut_map.get(slug)
        if resolved and resolved[0] != cut:
            log.warning("CUT mismatch for %s: col-A=%s, slug-resolved=%s", name, cut, resolved[0])

        records.append({
            "cut": cut,
            "name": name,
            "vhdv_rate": vhdv_rate,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "tipo_estimacion": tipo,
            "cv": cv,
        })
```

**Record count guard + payload write pattern** (lines 150–177 of analog):
```python
    if len(records) < MIN_RECORDS:
        raise RuntimeError(
            f"Record count guard failed: expected >={MIN_RECORDS} records, "
            f"got {len(records)}. Parse may be truncated."
        )

    payload = {
        "source": "INE — Estadisticas Experimentales: Seguridad Ciudadana (ENUSC 2024 SAE)",
        "source_url": "<resolved sfvrsn URL — see ATTRIBUTION.md>",
        "landing_page": "https://www.ine.gob.cl/estadisticas/estadisticas-experimentales/seguridad-ciudadana",
        "vintage": "2024",
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "caveat": (
            "Estadistica experimental (SAE). INE labels this 'etapa inicial de madurez'. "
            "Proportion of households reporting at least one violent crime (VHDV). "
            "136 of 346 comunas covered. NOT per-100k — proportion 0-1. "
            "Do not merge with CEAD per-100k composite."
        ),
        "records": sorted(records, key=lambda r: r["cut"]),
    }
    atomic_write_json(OUTPUT_FILE, payload)
    log.info("Wrote %d records to %s", len(records), OUTPUT_FILE)

if __name__ == "__main__":
    main()
```

---

### `pipeline/build_enusc_enrichment.py` (pipeline script, CRUD additive write)

**Analog:** `pipeline/build_composite_index.py` lines 345–388

**Additive enrichment loop pattern** (lines 349–377 of analog — the ONLY section to mirror):
```python
# From build_composite_index.py lines 349–377 — mirror exactly for ENUSC
for commune in communes:
    cut = commune["id"]

    # Additive enrichment (D-12) — do NOT touch existing fields
    commune.setdefault("composite_index", {})[str(REFERENCE_YEAR)] = composite_entry

    commune_path = data_dir / "comunas" / f"{cut}.json"
    atomic_write_json(commune_path, commune)
```

For ENUSC, the pattern becomes a simpler flat-key write (not year-keyed dict):
```python
from pipeline.shared.atomic_write import atomic_write_json

data_dir = REPO_ROOT / "data" / "cead"
snapshot = json.loads((REPO_ROOT / "data" / "snapshots" / "enusc_vhdv.json").read_text(encoding="utf-8"))
enusc_by_cut = {r["cut"]: r for r in snapshot["records"]}

resolved = 0
for cut, vhdv_data in enusc_by_cut.items():
    commune_path = data_dir / "comunas" / f"{cut}.json"
    if not commune_path.exists():
        log.warning("CUT %s not found in comunas/ — skipping", cut)
        continue
    commune = json.loads(commune_path.read_text(encoding="utf-8"))
    # VL-05 guard: assert key was absent or identical before writing
    existing = commune.get("enusc_vhdv")
    if existing is not None and existing != vhdv_data:
        raise RuntimeError(f"enusc_vhdv already set differently for CUT {cut} — refusing overwrite")
    commune["enusc_vhdv"] = {
        "vhdv_rate": vhdv_data["vhdv_rate"],
        "ci_lower": vhdv_data["ci_lower"],
        "ci_upper": vhdv_data["ci_upper"],
        "tipo_estimacion": vhdv_data["tipo_estimacion"],
        "cv": vhdv_data["cv"],
        "vintage": 2024,
    }
    atomic_write_json(commune_path, commune)
    resolved += 1

# Build-time coverage assertion (VL-02)
if resolved != EXPECTED_COVERAGE:
    raise RuntimeError(
        f"Coverage assertion failed: expected {EXPECTED_COVERAGE} CUTs resolved, "
        f"got {resolved}."
    )
log.info("Enriched %d commune files with enusc_vhdv", resolved)
```

**Script constants** (top of file, mirrors composite analog):
```python
REPO_ROOT = pathlib.Path(__file__).parent.parent
EXPECTED_COVERAGE = 136
```

**Graceful snapshot-absent handling** (VL-01):
```python
snapshot_path = REPO_ROOT / "data" / "snapshots" / "enusc_vhdv.json"
if not snapshot_path.exists():
    log.warning("enusc_vhdv.json not found — skipping enrichment (ENUSC step may have failed)")
    sys.exit(0)   # graceful degrade; continue-on-error absorbs CI failure upstream
```

---

### `data/snapshots/enusc_vhdv.json` (data artifact)

**Analog:** `data/snapshots/spd_homicide.json` shape, extended with VHDV-specific fields.

**Target shape** (derived from SPD canonical shape + ENUSC data profile):
```json
{
  "source": "INE — Estadisticas Experimentales: Seguridad Ciudadana (ENUSC 2024 SAE)",
  "source_url": "https://www.ine.gob.cl/docs/default-source/estadisticas-experimentales-seguridad-ciudadana/cuadros-estadisticos/2024/tabulados-sae--enusc-2024-vhdv.xlsx?sfvrsn=671c099f_4",
  "landing_page": "https://www.ine.gob.cl/estadisticas/estadisticas-experimentales/seguridad-ciudadana",
  "vintage": "2024",
  "fetched": "<ISO timestamp>",
  "caveat": "...",
  "records": [
    {
      "cut": "13101",
      "name": "Santiago",
      "vhdv_rate": 0.0478,
      "ci_lower": 0.042,
      "ci_upper": 0.053,
      "tipo_estimacion": "Directa y sintética",
      "cv": 0.041
    }
  ]
}
```

**ATTRIBUTION.md entry to add** (mirror existing table format from lines 9–21 of ATTRIBUTION.md), with explicit note that this snapshot IS wired to commune pages (unlike SPD/SII/Fiscalia which are REFERENCE-ONLY):
```markdown
## enusc_vhdv.json

| Field        | Value |
|--------------|-------|
| Source       | INE — Estadísticas Experimentales: Seguridad Ciudadana |
| Full URL     | https://www.ine.gob.cl/docs/default-source/.../tabulados-sae--enusc-2024-vhdv.xlsx?sfvrsn=671c099f_4 |
| Dataset name | ENUSC 2024 — VHDV (Victimización en Hogares por Delitos Violentos), modelo SAE |
| Licence      | Datos públicos del Estado de Chile (INE terms) |
| Vintage      | 2024 (SAE first published 2026-01-21) |
| Granularity  | 136 comunas (SAE communal model); 210 comunas have no estimate |
| Script       | pipeline/snapshots/fetch_enusc_vhdv.py |
| sha256       | ad9503826fd21590eca7cf37629872df09f3115ad0c6d80dfe5cedcb63c3d4ba |
| Note         | WIRED to commune pages (section 6c) — distinct from other snapshots in this directory which are REFERENCE-ONLY. The vhdv_rate is a proportion 0–1 (NOT per-100k). INE labels this "estadística experimental, etapa inicial de madurez." |
```

---

### `pipeline/tests/test_fetch_enusc_vhdv.py` (test)

**Analog:** `pipeline/tests/test_composite.py` — structure, fixture pattern, pytest import idiom.

**Test file structure pattern** (from test_composite.py lines 1–30):
```python
"""
pipeline/tests/test_fetch_enusc_vhdv.py

Tests for pipeline/snapshots/fetch_enusc_vhdv.py.

Run:
    python -m pytest pipeline/tests/test_fetch_enusc_vhdv.py -x
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile

import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
```

**Fixture pattern** (from test_composite.py lines 66–112 — temp dir + minimal fixture data):
```python
@pytest.fixture
def tmp_cache(tmp_path):
    """Copy real cache file to tmp dir for isolated tests, or create a minimal stub."""
    ...
```

**Required test cases** (VL-01 + sha256 guard):
- `test_cache_only_mode_exits_zero_with_valid_cache` — sets `CACHE_ONLY=1`, runs `main()`, asserts OUTPUT_FILE written
- `test_sha256_mismatch_raises` — writes a fake CACHE_FILE with wrong bytes, asserts `RuntimeError` with "sha256 mismatch"
- `test_missing_cache_raises_file_not_found` — CACHE_ONLY=1 with absent file, asserts `FileNotFoundError`
- `test_column_detection` — parses a minimal 3-row Excel fixture, asserts `records` contain `vhdv_rate`, `ci_lower`, `cut`
- `test_record_count_guard` — provides a truncated sheet (< 136 rows), asserts `RuntimeError` with "Record count guard"

---

### `pipeline/tests/test_build_enusc_enrichment.py` (test)

**Analog:** `pipeline/tests/test_composite.py` — particularly the fixture commune set and additive-enrichment assertions (lines 66–388).

**Required test cases** (VL-01, VL-02, VL-05):
- `test_missing_snapshot_graceful` — absent `enusc_vhdv.json`, asserts `sys.exit(0)` (graceful degrade)
- `test_coverage_assertion` — 136 records in snapshot, all CUTs exist in temp comunas/, asserts resolved == 136
- `test_additive_only` — pre-existing commune JSON with `composite_index` field; after enrichment assert `composite_index` is byte-unchanged and `enusc_vhdv` key is added
- `test_phase18_byte_unchanged` — sample of 10 communes: assert `composite_index`, `featured_rates`, `series` fields identical before/after enrichment
- `test_duplicate_write_refuses_overwrite` — run enrichment twice; second run detects existing `enusc_vhdv` key with identical value; assert no error (idempotent). Third run with modified value; assert `RuntimeError`.

---

### `site/src/pages/commune/[slug].astro` + `site/src/pages/es/comuna/[slug].astro` (page templates)

**Analog:** Section 6b in each file (EN: lines 219–241; ES: confirmed at ~line 225 same pattern).

**Exact section 6b to mirror** (from `site/src/pages/commune/[slug].astro` lines 219–241):
```astro
<!-- 6b. Composite Crime Index section (CI-05/CI-06) — static index-mode surface, no map toggle -->
{(() => {
  const COMPOSITE_YEAR = 2024;
  const ci = data.composite_index?.[String(COMPOSITE_YEAR)];
  if (!ci) return null;
  const BAND_EN_PAGE = ['Very Low', 'Low', 'Moderate', 'High', 'Very High'];
  const bandLabel = BAND_EN_PAGE[ci.level - 1] ?? '';
  return (
    <section class="panel-section composite-index-section" aria-label="Composite Crime Index">
      <h2 class="section-heading">{t.ci_section_heading}</h2>
      <div>
        <span class="ci-score-big">{Math.round(ci.score)}</span>
        <span class="ci-band-label">{bandLabel}</span>
      </div>
      <div class="ci-rank">
        {t.ci_rank_national.replace('#{rank}', `#${ci.rank}`).replace('{total}', '346')}
        {' · '}
        {t.ci_rank_regional.replace('#{rank}', `#${ci.regional_rank}`).replace('{region}', data.regionName)}
      </div>
      <div class="ci-caveat">{t.ci_caveat_text}</div>
    </section>
  );
})()}
```

**Section 6c to insert immediately after 6b** (both EN and ES templates):
```astro
<!-- 6c. ENUSC VHDV victimization module (VL-03/VL-04) -->
{(() => {
  const vhdv = data.enusc_vhdv;
  if (!vhdv) {
    return (
      <section class="enusc-no-estimate" aria-label={t.enusc_no_estimate_aria}>
        <p class="enusc-no-estimate-text">{t.enusc_no_estimate_text}</p>
      </section>
    );
  }
  return (
    <section class="panel-section enusc-vhdv-section" aria-label={t.enusc_section_aria}>
      <h2 class="section-heading">{t.enusc_section_heading}</h2>
      <div class="enusc-rate">
        {(vhdv.vhdv_rate * 100).toFixed(1)}%
        <span class="enusc-year">(2024)</span>
      </div>
      <div class="enusc-ci">
        {t.enusc_ci_label}: {(vhdv.ci_lower * 100).toFixed(1)}% – {(vhdv.ci_upper * 100).toFixed(1)}%
      </div>
      <div class="enusc-caveat">{t.enusc_caveat_text}</div>
    </section>
  );
})()}
```

**Zero `client:*` directives** — confirmed design decision. This is pure static Astro markup; no React, no JS shipped.

---

### `site/src/config/i18n.ts` (config)

**Analog:** Phase 18-04 CI keys block (lines 151–159 of i18n.ts):
```typescript
  // Phase 18-04 — composite index bands + rank + caveat
  ci_band_1: string;
  ci_band_2: string;
  ci_band_3: string;
  ci_band_4: string;
  ci_band_5: string;
  ci_rank_national: string;
  ci_rank_regional: string;
  ci_caveat_text: string;
```

**Keys to add to `I18nStrings` interface** (same comment-header pattern):
```typescript
  // Phase 23 — ENUSC SAE VHDV communal victimization module
  enusc_section_heading: string;
  enusc_section_aria: string;
  enusc_ci_label: string;
  enusc_caveat_text: string;
  enusc_no_estimate_text: string;
  enusc_no_estimate_aria: string;
```

**Add to `EN_STRINGS`** (immediately after existing CI keys block):
```typescript
  enusc_section_heading: "Household Victimization (ENUSC 2024)",
  enusc_section_aria: "ENUSC household victimization estimate",
  enusc_ci_label: "95% confidence interval",
  enusc_caveat_text:
    "INE experimental estimate (SAE-modeled). Proportion of households reporting at least one violent crime. Covers 136 of 346 comunas. Distinct from CEAD reported-crime index — measures victimization survey responses, not police denuncias. Source: INE Estadísticas Experimentales, Seguridad Ciudadana.",
  enusc_no_estimate_text:
    "No INE ENUSC victimization estimate available for this comuna (SAE model covers 136 of 346 comunas).",
  enusc_no_estimate_aria: "ENUSC no estimate available",
```

**Add to `ES_STRINGS`**:
```typescript
  enusc_section_heading: "Victimización en Hogares (ENUSC 2024)",
  enusc_section_aria: "Estimación de victimización en hogares ENUSC",
  enusc_ci_label: "Intervalo de confianza al 95%",
  enusc_caveat_text:
    "Estimación experimental de INE (modelo SAE). Proporción de hogares que reportaron al menos un delito violento. Cubre 136 de 346 comunas. Distinto del índice CEAD de delitos reportados — mide respuestas de encuesta de victimización, no denuncias policiales. Fuente: INE Estadísticas Experimentales, Seguridad Ciudadana.",
  enusc_no_estimate_text:
    "Sin estimación de victimización ENUSC disponible para esta comuna (el modelo SAE cubre 136 de 346 comunas).",
  enusc_no_estimate_aria: "Sin estimación ENUSC disponible",
```

---

### `site/src/lib/data.ts` (type definition)

**Analog:** Phase 18-04 additive field pattern (lines 66–68 of data.ts):
```typescript
  // Phase 18-04 additive field (D-12) — rides along in per-commune JSON
  composite_index?: Record<string, CompositeIndexEntry>;
```

**Add to `CommuneData` interface** immediately after `composite_index?`:
```typescript
  // Phase 23 additive field — present for 136 ENUSC-covered comunas, absent for 210
  enusc_vhdv?: {
    vhdv_rate: number;           // proportion 0–1 (e.g. 0.0478 = 4.78%); NOT per-100k
    ci_lower: number;            // 95% CI lower bound (proportion)
    ci_upper: number;            // 95% CI upper bound (proportion)
    tipo_estimacion: string;     // "Directa y sintética" | "Sintética"
    cv: number;                  // coefficient of variation (logarithmic)
    vintage: number;             // 2024
  };
```

`loadCommune()` requires **no code change** — the optional field is transparently present/absent in the JSON and TypeScript handles it via the `?` operator.

---

### `site/scripts/validate/figure-registry.mjs` (validator)

**Analog:** F15 entry (lines 178–191 of figure-registry.mjs):
```javascript
  {
    id: 'F15',
    description: 'News incidents (count, date, location from RSS feeds)',
    tokens: [
      ['RSS', 'news'],
    ],
    note: 'News layer attribution: each pin cites outlet + URL inline; SOURCES.md must reference RSS/news.',
  },
```

**F16 entry to append** to `FIGURE_REGISTRY` array (after F15):
```javascript
  {
    id: 'F16',
    description: 'ENUSC SAE VHDV household victimization rate (experimental, 2024)',
    tokens: [
      ['## INE ENUSC SAE', 'VHDV'],
      ['ENUSC', 'Victimizacion en Hogares', 'SAE'],
    ],
    note: 'INE ENUSC 2024 communal SAE estimate; labeled experimental. 136/346 comunas coverage. Distinct from F11 (underreporting claims) which uses the ## ENUSC underreporting section.',
  },
```

**Update console.log line 197** (currently says "F1-F15") to say "F1-F16".

---

### `data/SOURCES.md` (docs)

**Analog:** Existing `## ENUSC — underreporting / cifra negra` block (lines 292–316).

**New section to add** (SEPARATE from the existing block — do not merge):
```markdown
## INE ENUSC SAE — communal VHDV victimization (experimental)

**Full name:** ENUSC 2024 — Victimización en Hogares por Delitos Violentos (VHDV), modelo de Estimación en Áreas Pequeñas (SAE).

**Publisher:** Instituto Nacional de Estadísticas (INE) — Estadísticas Experimentales: Seguridad Ciudadana.

**Official landing:**
`https://www.ine.gob.cl/estadisticas/estadisticas-experimentales/seguridad-ciudadana`

**File URL (sfvrsn may rotate on republish):**
`https://www.ine.gob.cl/docs/default-source/estadisticas-experimentales-seguridad-ciudadana/cuadros-estadisticos/2024/tabulados-sae--enusc-2024-vhdv.xlsx?sfvrsn=671c099f_4`

**Measure semantics:**
Proportion of households reporting at least one violent crime (VHDV). Value is 0–1 (proportion), NOT per-100k. Do not rescale. Communal SAE estimates cover 136 of 346 comunas; the remaining 210 have no estimate.

**INE status:** Estadística experimental, "etapa inicial de madurez" (INE's own label).

**Vintage:** Reference year 2024; first published 2026-01-21.

**sha256 of ingested file:** `ad9503826fd21590eca7cf37629872df09f3115ad0c6d80dfe5cedcb63c3d4ba`

**Used by:** `data/snapshots/enusc_vhdv.json` → `data/cead/comunas/{CUT}.json` (enusc_vhdv field) → `site/src/pages/commune/[slug].astro` section 6c (F16). See also `data/snapshots/ATTRIBUTION.md`.

**Licence:** Datos públicos del Estado de Chile (INE terms).

**Distinct from:** `## ENUSC — underreporting / cifra negra` (F11 above) which references the ENUSC national survey for underreporting statistics, not the SAE communal estimates.
```

---

### `.github/workflows/cead-scraper.yml` (CI/CD)

**Analog:** Existing `continue-on-error: true` steps (lines 37–43 of cead-scraper.yml):
```yaml
      - name: Build composite index
        continue-on-error: true
        run: python pipeline/build_composite_index.py

      - name: Build map payload
        continue-on-error: true
        run: python pipeline/build_map_payload.py
```

**Two steps to insert** between "Run CEAD scraper" (line 34) and "Build composite index" (line 37):
```yaml
      - name: Build ENUSC victimization snapshot
        continue-on-error: true
        env:
          CACHE_ONLY: '1'
        run: python pipeline/snapshots/fetch_enusc_vhdv.py

      - name: Enrich commune JSONs with ENUSC VHDV
        continue-on-error: true
        run: python pipeline/build_enusc_enrichment.py
```

**Why `CACHE_ONLY: '1'` on the fetch step:** The ENUSC file has no stable URL; the cache is manually deposited. If `pipeline/cache/enusc_vhdv.xlsx` is absent, the fetcher fails loudly (sha256 or FileNotFoundError), `continue-on-error: true` absorbs the failure, and CEAD + composite index continue unaffected (VL-01).

---

### `site/scripts/validate/commune.mjs` (validator extension)

**Analog:** Existing dist/ HTML inspection loop (lines 1–60+ of commune.mjs) — the default (non-self-test) mode that reads dist/ HTML files and asserts structural requirements.

**Pattern to extend** — after the existing 500-word and forbidden-terms checks, add VHDV module assertion:
```javascript
// Assert ENUSC VHDV module presence (Phase 23 VL-03 / VL-04)
// Every commune page must have EITHER enusc-vhdv-section OR enusc-no-estimate
const hasVhdvSection = html.includes('enusc-vhdv-section');
const hasNoEstimate = html.includes('enusc-no-estimate');
if (!hasVhdvSection && !hasNoEstimate) {
  console.error(`FAIL: ${file} — missing both enusc-vhdv-section and enusc-no-estimate`);
  process.exit(1);
}
```

---

### `site/src/pages/methodology.astro` + `site/src/pages/es/metodologia.astro` (content pages)

**Analog:** Existing ENUSC section in each methodology page (for F11 underreporting claims). The new section is a SEPARATE H2 (VL-05 requires F11 and F16 registrations to be distinct and traceable).

**EN section to add** (separate H2 after the existing ENUSC underreporting section):
```astro
<h2 id="enusc-vhdv">Household Victimization Indicator (ENUSC 2024 SAE)</h2>
<p>
  The ENUSC 2024 communal household victimization rate (VHDV) is an experimental
  statistic produced by INE using Small Area Estimation (SAE) methods. It measures
  the proportion of households reporting at least one violent crime, covering 136
  of 346 comunas. INE labels this an "estadística experimental, etapa inicial de
  madurez." This indicator is displayed as an additive module on covered commune
  pages — it is NOT merged with the CEAD-based crime index (which reports
  police denuncias per 100,000 population, a distinct measurement).
  Source: <a href="https://www.ine.gob.cl/estadisticas/estadisticas-experimentales/seguridad-ciudadana">INE Estadísticas Experimentales, Seguridad Ciudadana</a>.
</p>
```

**ES section to add** (same location, ES template):
```astro
<h2 id="enusc-vhdv">Indicador de Victimización en Hogares (ENUSC 2024 SAE)</h2>
<p>
  La tasa de victimización en hogares VHDV de ENUSC 2024 es una estadística
  experimental elaborada por INE mediante métodos de Estimación en Áreas Pequeñas
  (SAE). Mide la proporción de hogares que reportaron al menos un delito violento,
  cubriendo 136 de las 346 comunas. INE la clasifica como "estadística experimental,
  etapa inicial de madurez." Este indicador se muestra como módulo adicional en
  las páginas de comunas cubiertas — NO se fusiona con el índice de criminalidad
  CEAD (que reporta denuncias policiales por 100.000 habitantes, una medición distinta).
  Fuente: <a href="https://www.ine.gob.cl/estadisticas/estadisticas-experimentales/seguridad-ciudadana">INE Estadísticas Experimentales, Seguridad Ciudadana</a>.
</p>
```

---

## Shared Patterns

### Atomic JSON write
**Source:** `pipeline/shared/atomic_write.py` — `atomic_write_json(path, data)`
**Apply to:** `fetch_enusc_vhdv.py` (output file write), `build_enusc_enrichment.py` (per-commune write)
```python
from pipeline.shared.atomic_write import atomic_write_json
atomic_write_json(output_path, payload)  # os.replace() atomic on all platforms
```

### Slug normalization
**Source:** `pipeline/cead/normalizer.py` — `make_slug(name: str) -> str`
**Apply to:** `fetch_enusc_vhdv.py` (redundant cross-check only — primary join is direct CUT from col A)
```python
from pipeline.cead.normalizer import make_slug
slug = make_slug("Ñuñoa")   # → "nunoa"
```

### Tenacity retry
**Source:** `pipeline/snapshots/fetch_spd_homicide.py` lines 52–68
**Apply to:** `fetch_enusc_vhdv.py` `_download()` function (network download path only; CACHE_ONLY mode skips this entirely)
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
def _download(url: str, dest: pathlib.Path) -> None: ...
```

### IIFE null-guard pattern in Astro
**Source:** `site/src/pages/commune/[slug].astro` lines 219–241 (section 6b)
**Apply to:** Section 6c in both EN and ES commune templates
```astro
{(() => {
  const field = data.optional_field;
  if (!field) return <fallback />;
  return <main_content />;
})()}
```

### continue-on-error CI step
**Source:** `.github/workflows/cead-scraper.yml` lines 37–43
**Apply to:** Both new ENUSC steps in cead-scraper.yml
```yaml
- name: Step name
  continue-on-error: true
  run: python pipeline/script.py
```

### i18n string registration pattern
**Source:** `site/src/config/i18n.ts` lines 151–159 (Phase 18-04 block)
**Apply to:** New ENUSC keys in `I18nStrings` interface + `EN_STRINGS` + `ES_STRINGS`
Pattern: add a `// Phase NN — description` comment header, then keys in camelCase.

---

## No Analog Found

All files in Phase 23 have close analogs in the live codebase. No files require fallback to RESEARCH.md patterns alone. The sha256 assertion function in `fetch_enusc_vhdv.py` is genuinely new (SPD/SII fetchers trust HTTP responses without hash verification), but it is a small self-contained addition documented fully in RESEARCH.md.

---

## Metadata

**Analog search scope:** `pipeline/snapshots/`, `pipeline/tests/`, `site/src/pages/`, `site/src/config/`, `site/src/lib/`, `site/scripts/validate/`, `.github/workflows/`, `data/snapshots/`, `data/SOURCES.md`
**Files read for pattern extraction:** 13
**Pattern extraction date:** 2026-06-19
