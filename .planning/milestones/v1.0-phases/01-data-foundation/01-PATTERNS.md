# Phase 1: Data Foundation - Pattern Map

**Mapped:** 2026-06-12
**Files analyzed:** 11 new files (pipeline modules + data outputs)
**Analogs found:** 0 true analogs (greenfield Python pipeline) / 11 total

---

## Overview

This is a near-greenfield repo. The only existing code is a React/JSX prototype in
`ischilesafe.com/` with placeholder data. There are **no existing Python files** to copy
patterns from. All patterns below come from two verified sources:

1. **RESEARCH.md code examples** — verified live against CEAD endpoints on 2026-06-12.
2. **`ischilesafe.com/data.js`** — the prototype's data shape, which defines the downstream
   contract the pipeline JSON must eventually satisfy.

---

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `pipeline/scrape_cead.py` | entrypoint/orchestrator | batch | none | no-analog |
| `pipeline/cead/client.py` | HTTP client | request-response | `como scrap.txt` snippet | reference-only |
| `pipeline/cead/catalog.py` | HTTP client | request-response | `como scrap.txt` snippet | reference-only |
| `pipeline/cead/parser.py` | transform/utility | batch | none | no-analog |
| `pipeline/cead/normalizer.py` | transform/utility | batch | `ischilesafe.com/data.js` (output contract) | contract-only |
| `pipeline/shared/schema.py` | model/validator | batch | none | no-analog |
| `pipeline/shared/atomic_write.py` | utility | file-I/O | none | no-analog |
| `pipeline/shared/population.py` | utility | file-I/O | none | no-analog |
| `pipeline/requirements.txt` | config | — | none | no-analog |
| `pipeline/tests/conftest.py` | test | — | none | no-analog |
| `pipeline/tests/test_*.py` (8 files) | test | — | none | no-analog |

---

## Pattern Assignments

### `pipeline/cead/client.py` (HTTP client, request-response)

**Analog:** None in codebase. Pattern sourced from RESEARCH.md (verified live 2026-06-12).

**Imports pattern:**
```python
import requests
import time
import pathlib
import json
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
```

**Session setup pattern** (RESEARCH.md "Full Session Setup"):
```python
def make_cead_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; IsChileSafe data pipeline; +https://ischilesafe.com)',
        'Referer': 'https://cead.minsegpublica.gob.cl/estadisticas-delictuales/',
        'Origin': 'https://cead.minsegpublica.gob.cl',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
    })
    # Warm up session to get wpdm_client cookie — without this, Azure gateway returns 403
    session.get('https://cead.minsegpublica.gob.cl/estadisticas-delictuales/', timeout=15)
    return session
```

**Batch commune fetch pattern** (RESEARCH.md "Pattern 1"):
```python
def fetch_communes_batch(session, cut_codes: list[str], year: int, familia_id: int) -> str:
    """Fetch rates for a batch of communes. Returns raw HTML."""
    payload = {
        'medida': '2',          # rates per 100k — always use medida=2 (D-10)
        'tipoVal': '1,2',       # police cases only (D-08)
        'anio[]': str(year),
        'familia[]': str(familia_id),
        'seleccion': '1',       # territorial breakdown
        'descarga': 'true',     # HTML-in-Excel format; use descarga=true for row classes
    }
    for cut in cut_codes:
        payload.setdefault('comuna[]', [])
        payload['comuna[]'].append(str(cut))  # MUST be strings — int silently fails (Pitfall 7)
    payload['region[]'] = str(cut_codes[0])[:2]  # first 2 digits of CUT

    response = session.post(
        'https://cead.minsegpublica.gob.cl/wp-content/themes/gobcl-wp-master/data/get_estadisticas_delictuales.php',
        data=payload,
        timeout=30
    )
    response.raise_for_status()
    return response.content.decode('latin-1')  # MUST use latin-1 — r.text guesses wrong (Pitfall 3)
```

**Rate limiting pattern:**
```python
# Between region batches — 2-3 s delay (D-03)
time.sleep(2.5)
```

**Tenacity retry pattern:**
```python
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((requests.Timeout, requests.HTTPError)),
)
def _post_with_retry(session, url, data):
    response = session.post(url, data=data, timeout=30)
    response.raise_for_status()
    return response
```

**Raw response caching pattern (D-04):**
```python
CACHE_DIR = pathlib.Path(__file__).parent.parent / 'cache'

def cache_raw(filename: str, content: str) -> None:
    """Cache raw HTML response to pipeline/cache/ (git-ignored). Never commit this dir."""
    CACHE_DIR.mkdir(exist_ok=True)
    (CACHE_DIR / filename).write_text(content, encoding='utf-8')

def load_cached(filename: str) -> str | None:
    path = CACHE_DIR / filename
    return path.read_text(encoding='utf-8') if path.exists() else None
```

---

### `pipeline/cead/catalog.py` (HTTP client, request-response)

**Analog:** None in codebase. Pattern sourced from RESEARCH.md "Pattern 2".

**Commune catalog fetch pattern:**
```python
def get_commune_catalog(session) -> dict[str, str]:
    """Returns {cut_code: commune_name} for all 346 communes."""
    response = session.post(
        'https://cead.minsegpublica.gob.cl/wp-content/themes/gobcl-wp-master/data/ajax_2.php',
        data={'region': '13', 'seleccion': '101'},  # seleccion=101 returns ALL 346 communes
        timeout=15
    )
    data = response.json()
    return {
        json.loads(c)['comDelId']: json.loads(c)['comDelNombre']
        for c in data['ComunasDel']
    }
    # NOTE A1: Assumption — seleccion=101 returns all 346 regardless of region param.
    # If it returns a subset, loop over all 16 region IDs and merge.
```

**Region ID map (from `como scrap.txt`, confirmed in RESEARCH.md):**
```python
REGION_IDS = {
    15: "Arica y Parinacota", 1: "Tarapacá", 2: "Antofagasta",
    3: "Atacama", 4: "Coquimbo", 5: "Valparaíso", 13: "Metropolitana",
    6: "O'Higgins", 7: "Maule", 16: "Ñuble", 8: "Biobío",
    9: "La Araucanía", 14: "Los Ríos", 10: "Los Lagos",
    11: "Aysén", 12: "Magallanes"
}
FAMILIA_IDS = {1: "vida", 2: "robos_violentos", 3: "vif", 4: "drogas",
               5: "armas", 6: "propiedad", 7: "incivilidades"}
```

---

### `pipeline/cead/parser.py` (transform/utility, batch)

**Analog:** None in codebase. Pattern sourced from RESEARCH.md "Pattern 5".

**Imports pattern:**
```python
from bs4 import BeautifulSoup
import re
```

**HTML table parse pattern:**
```python
def parse_cead_table(html: str) -> list[dict]:
    """
    Parse CEAD response. MIME is vnd.ms-excel but body is always HTML.
    Row classes: formato_4 = commune row (use these, not formato_1/2/3).
    """
    soup = BeautifulSoup(html, 'lxml')
    tables = soup.find_all('table')
    data_table = tables[-1]  # last table is always the data table

    headers = []
    rows = []
    for tr in data_table.find_all('tr'):
        cells = [td.get_text(strip=True) for td in tr.find_all(['th', 'td'])]
        if not headers and any(c.isdigit() for c in cells):
            headers = cells  # year row e.g. ['', '2022', '2023', '2024']
            continue
        if cells and cells[0] not in ('', 'DELITOS O FALTAS', 'UNIDAD TERRITORIAL'):
            row_class = tr.get('class', [])
            rows.append({
                'name': cells[0],
                'class': row_class,
                'values': {headers[i]: cells[i] for i in range(1, len(cells)) if i < len(headers)}
            })
    return rows
```

**Decimal parsing utility (Pitfall 2 — CRITICAL):**
```python
def parse_cead_float(value: str) -> float | None:
    """
    CEAD uses Chilean locale: period = thousands separator, comma = decimal.
    '1.154,3537' → 1154.3537. '-' means no data → None.
    """
    v = value.strip()
    if v in ('', '-', 'S/I', 'N/A'):
        return None
    return float(v.replace('.', '').replace(',', '.'))
```

---

### `pipeline/cead/normalizer.py` (transform/utility, batch)

**Analog:** `ischilesafe.com/data.js` — defines downstream consumption contract (read-only reference).

**Downstream contract from `data.js` (lines 14–69):**

The prototype consumes per-commune objects with these fields that the pipeline JSON must support:
- `id` (string slug in prototype → CUT string in pipeline, D-17)
- `name` (string)
- `region` (string)
- `lat`, `lng` (centroid coordinates)
- `level` (1–5 quintile — derived from rate quintile at map-payload generation)
- `trend` (-1/0/1 in prototype → `"up"/"stable"/"down"` in pipeline schema per D-13)

The pipeline uses CUT codes (`"13101"`) not slugs as the primary `id`. The `slug` is a
derived field for URL generation. Level quintile is computed in the normalizer when
building `map-payload.json`.

**Trend calculation pattern** (RESEARCH.md "Trend Calculation"):
```python
def compute_trend(series: list[dict], threshold_pct: float = 5.0) -> str:
    """
    Compute 3-year trend as 'up'/'down'/'stable' (D-13).
    series: list of {'year': int, 'rate_per_100k': float}, sorted ascending.
    threshold_pct: ±5% is the default; adjust after validating against sample communes (A5).
    """
    if len(series) < 4:
        return 'stable'  # not enough data
    recent = sorted(series, key=lambda x: x['year'])[-4:]  # last 4 years (3-year delta)
    rate_start = recent[0]['rate_per_100k']
    rate_end = recent[-1]['rate_per_100k']
    if rate_start == 0:
        return 'stable'
    pct_change = (rate_end - rate_start) / rate_start * 100
    if pct_change > threshold_pct:
        return 'up'
    elif pct_change < -threshold_pct:
        return 'down'
    return 'stable'
```

**Slug generation pattern** (RESEARCH.md "Slug Generation"):
```python
import unicodedata, re

def make_slug(name: str) -> str:
    """Convert 'Ñuñoa' → 'nunoa', 'O'Higgins' → 'ohiggins'. D-17."""
    normalized = unicodedata.normalize('NFD', name)
    ascii_name = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    slug = re.sub(r"[^a-z0-9]+", '-', ascii_name.lower()).strip('-')
    return slug
```

**Rank calculation pattern (D-12):**
```python
def compute_ranks(records: list[dict], year: int) -> list[dict]:
    """
    Assign national and regional ranks. Communes with low_population=True get rank=None.
    Rank by rate_per_100k descending (highest rate = rank 1).
    """
    eligible = [(i, r) for i, r in enumerate(records)
                if not r['low_population'] and r['series']]
    # National rank
    eligible_sorted = sorted(eligible, key=lambda x: _latest_rate(x[1], year), reverse=True)
    for rank, (i, _) in enumerate(eligible_sorted, 1):
        records[i]['national_rank'] = rank
    # ... regional rank same pattern scoped to region_id
    return records
```

**Featured flag pattern (D-06):**
```python
FEATURED_FAMILIES = {'propiedad', 'vida'}  # vida includes homicides; propiedad = property crimes
FEATURED_SUBGROUPS = {
    'homicidios': 101,   # Homicidios y femicidios — confirm subgroup ID (A4)
    'secuestros': None,  # Kidnappings — subgroup ID to be confirmed in Wave 0 (Open Question 3)
}
```

---

### `pipeline/shared/schema.py` (model/validator, batch)

**Analog:** None in codebase. Pattern sourced from RESEARCH.md "Pattern 3".

**Pydantic v2 model pattern — use v2 syntax exclusively (RESEARCH.md "State of the Art"):**
```python
from pydantic import BaseModel, field_validator, model_validator
from typing import Literal

class YearRecord(BaseModel):
    year: int
    rate_per_100k: float
    by_family: dict[str, float | None]  # keys match FAMILIA_IDS values
    partial: bool = False               # True if scrape date is before Dec 31 of that year (Open Question 2)

class ComunaRecord(BaseModel):
    id: str           # CUT code e.g. "13101" (D-17)
    name: str
    slug: str         # e.g. "santiago" (D-17)
    region_id: str    # e.g. "13"
    population: int
    low_population: bool          # True if population < 10,000 (D-12)
    national_rank: int | None     # null if low_population (D-12)
    regional_rank: int | None
    trend: Literal["up", "down", "stable"]   # (D-13)
    featured_rates: dict          # homicides, kidnappings, property rates by year
    series: list[YearRecord]
    last_updated: str             # ISO date

    @field_validator('id')
    @classmethod
    def id_must_be_cut(cls, v):
        if not (v.isdigit() and 4 <= len(v) <= 5):
            raise ValueError(f'Invalid CUT code: {v}')
        return v

class MapPayloadEntry(BaseModel):
    id: str           # CUT code
    rate: float       # total rate_per_100k for the reference year
    level: int        # 1–5 quintile (1=lowest, 5=highest) — matches prototype data.js field
    by_family: dict[str, float | None]  # 7 family rates (D-09)

class MapPayload(BaseModel):
    generated: str    # ISO datetime
    year: int
    comunas: list[MapPayloadEntry]
```

**All-or-nothing validation gate (D-14):**
```python
def validate_all_communes(all_communes: list[dict]) -> list[ComunaRecord]:
    """Validate all records. Raise on ANY error — do not write partial output (D-14)."""
    if len(all_communes) != 346:
        raise ValueError(f'Expected 346 communes, got {len(all_communes)}')

    records = [ComunaRecord.model_validate(c) for c in all_communes]  # v2 syntax

    # Plausibility range check (D-16) — first run uses broad absolute limits
    for r in records:
        for yr in r.series:
            if yr.rate_per_100k < 0:
                raise ValueError(f'Negative rate for {r.id} in {yr.year}')
            if yr.rate_per_100k > 20000:  # 0–20,000 per 100k absolute limit (Open Question 4)
                raise ValueError(f'Implausible rate {yr.rate_per_100k} for {r.id}')

    return records
```

---

### `pipeline/shared/atomic_write.py` (utility, file-I/O)

**Analog:** None in codebase. Pattern sourced from RESEARCH.md "Pattern 4".

**Atomic write pattern — use `os.replace()` not `open(path, 'w')` (works on both POSIX and Windows):**
```python
import json, os, pathlib

def atomic_write_json(path: pathlib.Path, data: dict | list) -> None:
    """
    Write JSON atomically: temp file → os.replace().
    Prevents partial reads if pipeline crashes mid-write.
    Works on Windows (os.replace) and POSIX alike.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    os.replace(tmp, path)  # atomic on same filesystem (POSIX + Windows)
```

---

### `pipeline/shared/population.py` (utility, file-I/O)

**Analog:** None in codebase.

**Population lookup pattern (D-11, D-12):**
```python
import json, pathlib
from functools import lru_cache

DATA_DIR = pathlib.Path(__file__).parent.parent.parent / 'data'

@lru_cache(maxsize=1)
def load_population() -> dict[str, int]:
    """
    Load INE communal population projections from /data/ine/poblacion_comunal.json.
    Returns {cut_code: population_2024}.
    File is a static committed asset — no scraping (D-11).
    """
    path = DATA_DIR / 'ine' / 'poblacion_comunal.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    return {str(entry['cut']): int(entry['population_2024']) for entry in data}

LOW_POPULATION_THRESHOLD = 10_000  # D-12

def is_low_population(cut_code: str) -> bool:
    pop = load_population()
    return pop.get(cut_code, 0) < LOW_POPULATION_THRESHOLD
```

---

### `pipeline/scrape_cead.py` (entrypoint/orchestrator, batch)

**Analog:** None in codebase. Pattern sourced from ARCHITECTURE.md + RESEARCH.md.

**Orchestrator pattern:**
```python
#!/usr/bin/env python3
"""
CEAD scraper entrypoint. Runs the full pipeline:
  1. Fetch commune catalog (ajax_2.php)
  2. For each region × family × year: fetch batch, parse, accumulate
  3. Normalize all records (trend, rank, slug, featured flags)
  4. Validate with Pydantic (all-or-nothing — D-14)
  5. Write atomically to /data/cead/ (only if validation passes)

Exit codes: 0 = success, 1 = validation failure or scrape error (D-14).
"""
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def main() -> int:
    try:
        # ... pipeline steps
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1  # GitHub Actions marks run as failed; no commit happens

if __name__ == '__main__':
    sys.exit(main())
```

**Conditional commit guard (ARCHITECTURE.md):**
```yaml
# In .github/workflows/cead-scraper.yml
- name: Commit if changed
  id: commit
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add data/
    if git diff --staged --quiet; then
      echo "changed=false" >> $GITHUB_OUTPUT
    else
      git commit -m "data: CEAD update [skip ci]"
      git push
      echo "changed=true" >> $GITHUB_OUTPUT
    fi
```

---

### `pipeline/tests/conftest.py` and `pipeline/tests/test_*.py` (test, batch)

**Analog:** None in codebase.

**Test fixture pattern (pytest):**
```python
# conftest.py
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / 'fixtures'

@pytest.fixture
def sample_cead_html():
    """Fixture: real CEAD response HTML captured from live endpoint."""
    return (FIXTURES_DIR / 'cead_response_sample.html').read_text(encoding='utf-8')

@pytest.fixture
def sample_commune_dict():
    """Fixture: minimal valid commune dict for Pydantic validation tests."""
    return {
        'id': '13101', 'name': 'Santiago', 'slug': 'santiago',
        'region_id': '13', 'population': 404495, 'low_population': False,
        'national_rank': 1, 'regional_rank': 1, 'trend': 'down',
        'featured_rates': {}, 'series': [{'year': 2024, 'rate_per_100k': 11181.0,
        'by_family': {}, 'partial': False}], 'last_updated': '2026-06-12'
    }
```

**Test pattern for validation gate (D-14):**
```python
# test_schema.py
from pipeline.shared.schema import validate_all_communes

def test_count_validation_rejects_less_than_346(sample_commune_dict):
    with pytest.raises(ValueError, match='Expected 346'):
        validate_all_communes([sample_commune_dict] * 200)

def test_missing_key_rejected(sample_commune_dict):
    bad = {k: v for k, v in sample_commune_dict.items() if k != 'name'}
    with pytest.raises(Exception):  # ValidationError from Pydantic
        validate_all_communes([bad] * 346)
```

---

## Shared Patterns

### HTTP Headers (Required for All CEAD Requests)

**Source:** RESEARCH.md "Full Session Setup" + Pitfall 1
**Apply to:** `pipeline/cead/client.py`, `pipeline/cead/catalog.py`

Without `Referer` and `Origin` headers matching the CEAD domain, Azure Application
Gateway returns HTTP 403 on every request. These headers must be set on the session
object once, not repeated per request.

```python
REQUIRED_HEADERS = {
    'Referer': 'https://cead.minsegpublica.gob.cl/estadisticas-delictuales/',
    'Origin': 'https://cead.minsegpublica.gob.cl',
    'Content-Type': 'application/x-www-form-urlencoded',
}
```

### Decimal Parsing (Required for All CEAD Numeric Values)

**Source:** RESEARCH.md Pitfall 2
**Apply to:** `pipeline/cead/parser.py`, any module that touches raw CEAD values

```python
def parse_cead_float(value: str) -> float | None:
    v = value.strip()
    if v in ('', '-', 'S/I', 'N/A'):
        return None
    return float(v.replace('.', '').replace(',', '.'))
```

### Latin-1 Decoding (Required for All CEAD Response Bodies)

**Source:** RESEARCH.md Pitfall 3
**Apply to:** `pipeline/cead/client.py`

Never use `response.text` — use `response.content.decode('latin-1')`. Otherwise
commune names with accents (Ñuñoa, Aysén, Copiapó) are corrupted.

### Exit-on-Failure Pattern (All Validation Errors)

**Source:** RESEARCH.md + D-14
**Apply to:** `pipeline/scrape_cead.py`, any module that validates data

```python
import sys
# On validation failure:
logger.error(f"Validation failed: {e}")
sys.exit(1)  # Non-zero exit → GitHub Actions marks job failed → no git commit
```

### Pydantic v2 Syntax (Not v1)

**Source:** RESEARCH.md "State of the Art"
**Apply to:** `pipeline/shared/schema.py`

Use `model_validate()` not `parse_obj()`. Use `@field_validator` not `@validator`.
Use `model_config` not `class Config`. The installed version is pydantic 2.13.4.

---

## Downstream Data Contract

The pipeline JSON must eventually support the prototype's consumption shape from
`ischilesafe.com/data.js`. Key mappings:

| Prototype field (`data.js`) | Pipeline field | Notes |
|-----------------------------|----------------|-------|
| `id` (slug string) | `slug` (derived from `name`) | Prototype used slugs; pipeline uses CUT as primary `id` per D-17 |
| `level` (1–5 integer) | Computed at map-payload write time (quintile of `rate_per_100k`) | Not stored per-commune; computed when writing `map-payload.json` |
| `trend` (-1/0/1) | `trend` ("up"/"down"/"stable") | Map island will need to translate string → integer if reusing prototype rendering code |
| `region` (string name) | `region_id` (string code, e.g. "13") | Full region name derivable from the region ID catalog |
| `lat`, `lng` (centroid) | Not in CEAD data — sourced from GeoJSON centroid | Phase 3 concern; pipeline can leave centroid as null or derive from GeoJSON |

---

## No Analog Found

All Phase 1 files are greenfield. No existing Python pipeline code exists in the repo.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `pipeline/scrape_cead.py` | orchestrator | batch | No pipeline entrypoints exist |
| `pipeline/cead/client.py` | HTTP client | request-response | No HTTP clients exist |
| `pipeline/cead/catalog.py` | HTTP client | request-response | No HTTP clients exist |
| `pipeline/cead/parser.py` | transform | batch | No parsers exist |
| `pipeline/cead/normalizer.py` | transform | batch | No normalizers exist |
| `pipeline/shared/schema.py` | model | batch | No Pydantic models exist |
| `pipeline/shared/atomic_write.py` | utility | file-I/O | No write utilities exist |
| `pipeline/shared/population.py` | utility | file-I/O | No data utilities exist |
| All test files | test | — | No tests exist |

**Planner should use RESEARCH.md patterns and the code excerpts in this document
as the primary source for all implementation patterns in Phase 1.**

---

## Metadata

**Analog search scope:** `ischilesafe.com/` (only existing code directory)
**Files scanned:** 7 prototype files (app.jsx, data.js, geo-data.js, map-view.jsx,
home-view.jsx, components.jsx, tweaks-panel.jsx) + `como scrap.txt`
**Pattern extraction date:** 2026-06-12
**Primary pattern source:** RESEARCH.md (verified live against CEAD 2026-06-12)
**Secondary pattern source:** `ischilesafe.com/data.js` (downstream JSON contract)
