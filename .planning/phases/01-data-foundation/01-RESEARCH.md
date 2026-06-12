# Phase 1: Data Foundation - Research

**Researched:** 2026-06-12
**Domain:** Python data pipeline — CEAD scraping, Pydantic validation, static JSON generation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Primary method: Excel bulk download (`descarga=true`) — minimizes requests to CEAD and avoids fragile HTML parsing.
- **D-02:** Automatic fallback to HTML table scraping (`get_estadisticas_delictuales.php` + bs4/lxml) in the same run if Excel fails or changes format. The quarterly run must not die from a format change.
- **D-03:** Polite rate limiting: 2–3 s fixed delay between requests + retry with exponential backoff (tenacity).
- **D-04:** Raw responses (Excel/HTML) cached in a local folder git-ignored (debug and re-parsing without re-scraping). The repo only versions normalized JSON.
- **D-05:** Taxonomy: 7 families + 22 groups. Subgroups NOT stored in general, with selective exception (D-06).
- **D-06:** Featured categories: **homicides, kidnappings, and property crimes**. If CEAD exposes homicides/kidnappings only at subgroup level, include those specific subgroups. Schema marks these categories with `featured` flag.
- **D-07:** Temporal granularity: annual series 2005–present only. No quarterly/monthly in MVP.
- **D-08:** Data type: only police cases (`tipoVal=1,2`). No separate series for reports/arrests.
- **D-09:** `map-payload.json`: last complete year, with total rate + 7 family rates per commune (<30 KB). Pipeline also writes `map-payload-{año}.json` per year.
- **D-10:** Rates per 100k: use official CEAD rates (`medida=2`) — consistency with cited source. Do not calculate own rates.
- **D-11:** Communal population: official INE projections as a static reference file committed in `/data/` (no additional scraping). Used ONLY for ranking filter and page context.
- **D-12:** Communes <10,000 inhabitants: excluded from national/regional rankings (`rank: null` + flag `low_population: true`), but their files still contain rates — pages will show the rate with a volatility caveat.
- **D-13:** Trend (`trend`): % variation of total rate over the last 3 years with threshold (~5%): `up`/`down`/`stable`.
- **D-14:** All-or-nothing policy: any Pydantic schema violation (count ≠ 346 communes, missing keys, implausible rates) → non-zero exit, no commit, last good JSON intact.
- **D-15:** Alerts: native GitHub Actions email on failure + workflow creates/updates a GitHub issue automatically with the error log.
- **D-16:** Rate plausibility: validation against historical range per commune/family (e.g., ±3x of historical maximum); first run uses broad absolute limits and sets the historical baseline.
- **D-17:** Canonical commune ID: official CUT code (Código Único Territorial INE, e.g., `13101` = Santiago) as `id`, plus `slug` derived from name for URLs.

### Claude's Discretion

- Exact internal structure of Pydantic models, field naming, and layout of `/data/cead/meta/` (catalog.json, index.json) — follow the proposed schema in `.planning/research/ARCHITECTURE.md` as a base.
- Handling of the current partial year (include marked as partial or exclude) — decide based on how CEAD exposes it.
- Exact trend threshold and exact plausibility margins — fix in planning with real data.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | Python scraper extracts police case frequencies and rates from CEAD endpoints for 346 communes, 16 regions, and national total, all years (2005–present), and 7 crime families | CEAD endpoint verified live — `get_estadisticas_delictuales.php` with `medida=2`, `tipoVal=1,2`, `anio[]`, `region[]`, `familia[]`, `seleccion=1`, `descarga=true`. Commune-level data confirmed by passing `comuna[]` array. |
| DATA-02 | Each scrape validated with Pydantic schema (346 communes present, expected keys, rates within plausible ranges); on failure pipeline exits with error without committing, preserving last good JSON | Pydantic v2.x pattern documented. All-or-nothing pattern with atomic writes validated in ARCHITECTURE.md. |
| DATA-03 | Normalized data as static versioned JSON in repo: one file per commune, per region, national aggregate, pre-aggregated map payload (~28 KB) | Schema design documented in ARCHITECTURE.md. File layout confirmed. |
| DATA-04 | Rate per 100,000 inhabitants is the canonical metric; national rankings apply minimum population filter (10,000 inhabitants) and never sort by absolute count | CEAD confirmed to serve rates directly via `medida=2`. INE population projections dataset identified for the filter. |
</phase_requirements>

---

## Summary

This phase is a greenfield Python pipeline that scrapes CEAD (Chile's official crime statistics center) and writes normalized, validated JSON to the repo. The CEAD endpoints are confirmed accessible as of 2026-06-12 — live testing in this research session confirmed the exact working parameter names and how to retrieve per-commune data.

The critical live-validation finding is that the endpoint uses singular parameter names (`anio`, `region`, `familia`) in its JavaScript form code, but the **array-suffixed versions (`anio[]`, `region[]`, `familia[]`, `comuna[]`) also work and are required to get per-commune breakdown data**. When `comuna[]` is passed as an array of CUT codes, the response includes a row per commune (not just aggregated regional rows). This changes the scraping strategy from "loop over each commune one at a time" to "batch multiple communes per request."

The `ajax_2.php` endpoint with `seleccion=101` returns all 346 communes with their CUT codes as `comDelId` — confirmed match with official CUT values (Santiago=13101, Antofagasta=2101, etc.). This endpoint is the canonical source for the commune ID catalog.

**Primary recommendation:** Batch communes by region (e.g., all RM communes in one request) using `comuna[]` arrays, with 2–3 s delay between regions. The `descarga=true` flag returns an HTML table (not a real Excel file — the MIME type is `vnd.ms-excel` but body is HTML). Use BeautifulSoup + lxml to parse. Use `medida=2` for all data pulls to get CEAD's own rate-per-100k values.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CEAD HTTP client | Pipeline (Python) | — | One-way data ingestion; no frontend involvement |
| HTML table parsing | Pipeline (Python) | — | bs4+lxml; output is normalized dict, not raw HTML |
| Pydantic schema validation | Pipeline (Python) | — | Gate before any write; all-or-nothing |
| Atomic JSON write | Pipeline (Python) | — | Write to temp file, rename to final; prevents partial reads |
| JSON data store | `/data/` directory in repo | — | Version-controlled; consumed read-only by Astro build |
| INE population lookup | Pipeline (Python) | Astro build | Static file; pipeline uses it for ranking filter; Astro uses it for page context |
| map-payload aggregation | Pipeline (Python) | — | Pre-computed; Astro and client map consume it directly |
| meta/index.json (commune catalog) | Pipeline (Python) | Phase 5 (DeepSeek) | Canonical source for all 346 CUT codes + slugs |

---

## Standard Stack

### Core Python Libraries

| Library | Version (verified) | Purpose | Why Standard |
|---------|-------------------|---------|--------------|
| requests | 2.34.2 (latest) | HTTP POST to CEAD endpoints | Standard HTTP; handles sessions, timeouts; CEAD uses POST forms |
| beautifulsoup4 | 4.15.0 (latest) | Parse CEAD HTML table responses | `descarga=true` returns HTML-in-Excel wrapper; bs4 + lxml is fastest |
| lxml | 6.1.1 (latest) | bs4 parser backend | 5–10x faster than html.parser for large HTML tables |
| pydantic | 2.13.4 (latest) | Schema validation before write | v2 model syntax; field validators; `model_validate()` for dicts |
| tenacity | 9.1.4 (latest) | Retry with exponential backoff | Rate limiting and transient CEAD errors without boilerplate |
| python-dotenv | 1.2.2 (latest) | Load env vars in dev | Keeps keys out of code; GitHub Actions uses repo secrets |
| openpyxl | 3.1.5 (latest) | Parse Excel if CEAD ever returns real .xlsx | Defense-in-depth; CEAD currently returns HTML-as-Excel but format may change |

[VERIFIED: PyPI registry] — all packages confirmed via `pip index versions` on 2026-06-12.

**Installation:**
```bash
pip install requests==2.34.* beautifulsoup4==4.15.* lxml==6.* pydantic==2.* tenacity==9.* python-dotenv==1.* openpyxl==3.*
```

Or pin in `requirements.txt`:
```
requests==2.34.2
beautifulsoup4==4.15.0
lxml==6.1.1
pydantic==2.13.4
tenacity==9.1.4
python-dotenv==1.2.2
openpyxl==3.1.5
```

---

## Package Legitimacy Audit

> slopcheck was run on all packages on 2026-06-12.

| Package | Registry | slopcheck | Disposition |
|---------|----------|-----------|-------------|
| requests | PyPI | [OK] | Approved |
| beautifulsoup4 | PyPI | [OK] | Approved |
| lxml | PyPI | [OK] | Approved |
| pydantic | PyPI | [OK] | Approved |
| tenacity | PyPI | [OK] | Approved |
| python-dotenv | PyPI | [OK] (flagged "python-" prefix pattern, but established) | Approved |
| openpyxl | PyPI | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
CEAD Server (PHP endpoints)
    │  POST get_estadisticas_delictuales.php
    │  params: medida=2, tipoVal=1,2, anio[], region[], familia[], comuna[], descarga=true
    ▼
pipeline/cead/client.py
    │  2–3 s delay between batches
    │  tenacity retry on 5xx / timeout
    │  cache raw HTML to /pipeline/cache/ (git-ignored)
    ▼
pipeline/cead/parser.py
    │  BeautifulSoup + lxml
    │  Extract: commune name, rate value per year per crime family
    │  Encoding: latin-1 → utf-8
    ▼
pipeline/cead/normalizer.py
    │  Map CEAD name → CUT code (via catalog from ajax_2.php)
    │  Generate slug from normalized name
    │  Calculate trend (3-year % change, ±5% threshold)
    │  Apply featured flag for homicides/kidnappings/property
    │  Apply low_population flag from INE data
    │  Calculate national/regional ranks (exclude <10k population)
    ▼
pipeline/shared/schema.py  (Pydantic models)
    │  ComunaRecord, RegionRecord, NationalRecord, MapPayload, MetaIndex
    │  model_validate() — raises ValidationError on any bad data
    │  Exit code 1 if validation fails; do not write any file
    ▼
Atomic write: write to /data/cead/comunas/.{cut}.json.tmp → rename to {cut}.json
    │  346 commune files
    │  16 region files
    │  national.json
    │  map-payload.json + map-payload-{year}.json per year
    │  meta/index.json + meta/catalog.json
    ▼
git diff --staged --quiet || git commit + git push
    │  Only if files actually changed
    ▼
POST to Cloudflare Pages Deploy Hook
    │  Only if commit happened
```

### Recommended Project Structure

```
pipeline/
├── scrape_cead.py          # entrypoint — orchestrates full run
├── cead/
│   ├── __init__.py
│   ├── client.py           # HTTP client: POST endpoints, rate limiting, caching
│   ├── catalog.py          # ajax_2.php call: get all 346 CUT codes + names
│   ├── parser.py           # HTML table parser (BeautifulSoup + lxml)
│   └── normalizer.py       # raw rows → normalized dicts (trend, ranks, flags)
├── shared/
│   ├── __init__.py
│   ├── schema.py           # Pydantic models for all output JSON types
│   ├── atomic_write.py     # write-to-temp-then-rename pattern
│   └── population.py       # INE population lookup (from /data/ine/poblacion.json)
├── cache/                  # git-ignored; raw HTML responses
│   └── .gitkeep
├── requirements.txt
└── pyproject.toml          # optional, for tooling config
data/
├── cead/
│   ├── comunas/
│   │   └── {cut}.json      # e.g., 13101.json
│   ├── regions/
│   │   └── {region_id}.json
│   ├── national.json
│   ├── map-payload.json
│   ├── map-payload-{year}.json  # one per year, same schema
│   └── meta/
│       ├── index.json      # 346 entries: cut, name, slug, region_id, population, low_population
│       └── catalog.json    # crime taxonomy: 7 families, 22 groups, featured flags
└── ine/
    └── poblacion_comunal.json  # static; sourced from INE projections dataset
```

### Pattern 1: Batched Commune Requests

**What:** Pass multiple `comuna[]` values per POST request to get commune-level data efficiently.
**When to use:** Always — this is the only way to get per-commune data from the endpoint.

```python
# Source: verified live against CEAD endpoint 2026-06-12
import requests, time

def fetch_communes_batch(session, cut_codes: list[str], year: int, familia_id: int) -> str:
    """Fetch rates for a batch of communes. Returns raw HTML."""
    payload = {
        'medida': '2',          # rates per 100k
        'tipoVal': '1,2',       # police cases
        'anio[]': str(year),
        'familia[]': str(familia_id),
        'seleccion': '1',       # by territorial unit
        'descarga': 'true',     # HTML-in-Excel format
    }
    # Add all commune CUT codes as array
    for cut in cut_codes:
        payload.setdefault('comuna[]', [])
        payload['comuna[]'].append(cut)
    # Add region for context
    region = str(cut_codes[0])[:2]  # first 2 digits of CUT
    payload['region[]'] = region

    response = session.post(
        'https://cead.minsegpublica.gob.cl/wp-content/themes/gobcl-wp-master/data/get_estadisticas_delictuales.php',
        data=payload,
        timeout=30
    )
    response.raise_for_status()
    return response.content.decode('latin-1')
```

### Pattern 2: Commune Catalog via ajax_2.php

**What:** Get the canonical list of all 346 communes with CUT codes in one call.
**When to use:** At the start of every run to build the CUT→name mapping table.

```python
# Source: verified live against CEAD endpoint 2026-06-12
import json

def get_commune_catalog(session) -> dict[str, str]:
    """Returns {cut_code: commune_name} for all 346 communes."""
    response = session.post(
        'https://cead.minsegpublica.gob.cl/wp-content/themes/gobcl-wp-master/data/ajax_2.php',
        data={'region': '13', 'seleccion': '101'},  # returns ALL 346 communes
        timeout=15
    )
    data = response.json()
    return {
        json.loads(c)['comDelId']: json.loads(c)['comDelNombre']
        for c in data['ComunasDel']
    }
```

### Pattern 3: Pydantic Validation Gate

**What:** Validate all output before writing any file. Exit non-zero on any violation.
**When to use:** Always — single gate protects all 346 output files.

```python
# Source: based on Pydantic v2 docs + D-14 decision
from pydantic import BaseModel, field_validator, model_validator
from typing import Literal

class CrimeFamilyRates(BaseModel):
    vida: float | None
    robos_violentos: float | None
    vif: float | None
    drogas: float | None
    armas: float | None
    propiedad: float | None
    incivilidades: float | None

class YearRecord(BaseModel):
    year: int
    rate_per_100k: float
    by_family: CrimeFamilyRates

class ComunaRecord(BaseModel):
    id: str           # CUT code e.g. "13101"
    name: str
    slug: str
    region_id: str
    population: int
    low_population: bool
    national_rank: int | None  # null if low_population
    regional_rank: int | None
    trend: Literal["up", "down", "stable"]
    featured_rates: dict  # homicides, kidnappings, property
    series: list[YearRecord]
    last_updated: str  # ISO date

    @field_validator('id')
    @classmethod
    def id_must_be_cut(cls, v):
        if not (v.isdigit() and 4 <= len(v) <= 5):
            raise ValueError(f'Invalid CUT code: {v}')
        return v

def validate_and_write(all_communes: list[dict]) -> None:
    """Validate all records. Raise on ANY error — do not write partial output."""
    if len(all_communes) != 346:
        raise ValueError(f'Expected 346 communes, got {len(all_communes)}')

    records = [ComunaRecord.model_validate(c) for c in all_communes]  # raises on bad data

    # Plausibility check: total rate must be > 0 for communes with data
    for r in records:
        for yr in r.series:
            if yr.rate_per_100k < 0:
                raise ValueError(f'Negative rate for {r.id} in {yr.year}')
            if yr.rate_per_100k > 50000:  # absolute upper bound for first run
                raise ValueError(f'Implausible rate {yr.rate_per_100k} for {r.id}')

    # All passed — now write atomically
    for record in records:
        _atomic_write(record)
```

### Pattern 4: Atomic Write

**What:** Write to `.{filename}.tmp`, then `os.rename()` to final path.
**When to use:** Every JSON write in the pipeline.

```python
import json, os, pathlib

def atomic_write_json(path: pathlib.Path, data: dict) -> None:
    """Write JSON atomically: temp file → rename. Prevents partial reads."""
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, path)  # atomic on same filesystem
```

### Pattern 5: HTML Table Parsing (CEAD Response)

**What:** Parse the HTML table returned by CEAD (even with `descarga=true`, the response is HTML).
**When to use:** Always — CEAD never returns real Excel despite the MIME type claim.

```python
# Source: verified live 2026-06-12 — CEAD returns HTML table wrapped in Excel MIME
from bs4 import BeautifulSoup

def parse_cead_table(html: str) -> list[dict]:
    """
    Parse CEAD response. Response is iso-8859-1 HTML table.
    Table structure: header row with years, then rows with territory name + rate per year.
    Row classes: formato_1 (country), formato_2 (region), formato_3 (province), formato_4 (commune)
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

### Anti-Patterns to Avoid

- **Loop over each commune individually:** One POST per commune × 346 × 7 families × 20 years = 48,440 requests. Use `comuna[]` batching by region instead (~16 batches × 7 × 20 = 2,240 requests).
- **Committing raw HTML to git:** Bloats the repo. Cache locally in `/pipeline/cache/` (git-ignored); commit only normalized JSON.
- **Using `descarga=false`:** Returns shorter HTML that lacks row-level CSS classes needed to distinguish commune rows from province/region rows. Use `descarga=true`.
- **Parsing decimal numbers with float():** CEAD uses comma as decimal separator (`1.154,35`). Strip periods (thousand separators) and replace commas with dots before `float()`.
- **Using `anio[]` with a Python list for multiple years in a single request for per-commune data:** Test showed this works for region-level; verify it works per-commune before relying on it for efficiency.

---

## CEAD Endpoint Live Validation Summary

> [VERIFIED: live HTTP testing 2026-06-12]

| Finding | Detail |
|---------|--------|
| Base URL | `https://cead.minsegpublica.gob.cl/wp-content/themes/gobcl-wp-master/data/` |
| Auth required | None — but requires `Referer` and `Origin` headers matching the CEAD domain |
| Bare requests (no headers) | Return HTTP 403 from Azure Application Gateway |
| With correct headers | HTTP 200; content encodes as `iso-8859-1` |
| `descarga=true` format | MIME: `application/vnd.ms-excel` but body is HTML table — parse with BeautifulSoup |
| `descarga=false` format | Shorter HTML; fewer row classes — less useful for parsing |
| Commune-level data | Requires `comuna[]` array param; without it, only region-level rows appear |
| `ajax_2.php` commune catalog | `seleccion=101` returns `ComunasDel` array with all 346 communes + CUT codes as `comDelId` |
| CUT code match | Confirmed: CEAD `comDelId` values equal official INE CUT codes |
| `get_estadisticas_delictuales_mapa.php` | Returns HTTP 500 — **not usable** as of 2026-06-12 |
| Decimal separator | Comma (`,`) as decimal, period (`.`) as thousands: `1.154,3537` |
| Encoding issue | Response encoding is `latin-1`; decode with `.encode('latin-1').decode('utf-8', errors='replace')` or `r.content.decode('latin-1')` |
| `seleccion` param values | `1` = by territory, `2` = by crime family, `3` = by victim demographics |
| `medida` param values | `1` = frequency (absolute count), `2` = rate per 100k inhabitants |
| `tipoVal` param value | `'1,2'` = police cases (the correct value for D-08) |

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Retry with backoff | Custom sleep/loop | `tenacity` | Handles jitter, max attempts, specific exception types |
| JSON schema validation | Custom dict key checks | `pydantic` v2 | Type coercion, field validators, clear error messages |
| HTML parsing | Regex on HTML | `beautifulsoup4` + `lxml` | Regex breaks on whitespace variation; bs4 handles malformed HTML |
| Atomic file write | `open(path, 'w')` | `write to .tmp + os.replace()` | `open()` leaves partial file on crash; `os.replace()` is atomic on POSIX and Windows |
| Rate limiting | `time.sleep()` inline | tenacity `wait_fixed` or explicit `time.sleep()` between batch loops | Either is fine; the important thing is 2–3 s between CEAD requests |
| URL slug generation | Custom regex | `unicodedata.normalize('NFD')` + re.sub | Chilean commune names have accents (Ñuñoa, Aysén) — standard slug logic misses these |

**Key insight:** The CEAD endpoint is a government server with no documented rate limits or SLA. Defensive coding (retry, validation, caching raw responses) is not optional.

---

## Common Pitfalls

### Pitfall 1: HTTP 403 Without Proper Headers

**What goes wrong:** Raw `requests.post()` to CEAD endpoints returns `403 Forbidden` from Azure Application Gateway.
**Why it happens:** The gateway checks `Referer` and `Origin` headers to confirm the request comes from the CEAD website.
**How to avoid:** Set `Referer: https://cead.minsegpublica.gob.cl/estadisticas-delictuales/` and `Origin: https://cead.minsegpublica.gob.cl` in all requests. Use a `requests.Session()` with these headers set once.
**Warning signs:** HTTP 403 in response; response body contains Azure Application Gateway error page.

### Pitfall 2: Decimal Parsing Failure

**What goes wrong:** `float('1.154,3537')` raises `ValueError`. All CEAD numeric values use Chilean locale formatting.
**Why it happens:** CEAD uses period as thousands separator and comma as decimal separator.
**How to avoid:** `float(value.replace('.', '').replace(',', '.'))` before converting. Write a `parse_cead_float()` utility used everywhere.
**Warning signs:** `ValueError: could not convert string to float` during parsing.

### Pitfall 3: Latin-1 Encoding Corruption

**What goes wrong:** `r.text` in Python interprets the response as UTF-8 (or incorrect encoding), producing garbage characters for `á`, `é`, `ñ`, `ó` in commune names.
**Why it happens:** CEAD responses are `iso-8859-1` but `requests` may guess wrong.
**How to avoid:** Use `r.content.decode('latin-1')` explicitly, or set `r.encoding = 'latin-1'` before accessing `r.text`.
**Warning signs:** Commune names appear as `Regi??n` or `Coquimbo` with corrupted vowels; `slug` generation produces wrong values.

### Pitfall 4: Missing Commune Count Validation

**What goes wrong:** CEAD silently returns fewer rows (e.g., network timeout cuts response mid-table). Pipeline writes 200 commune files and exits 0. Site serves incomplete rankings.
**Why it happens:** HTTP 200 does not guarantee full response body for large HTML responses.
**How to avoid:** After parsing, assert `len(parsed_communes) == 346` before running Pydantic validation. This is D-14 — exit non-zero if count is wrong.
**Warning signs:** Map shows blank areas; `meta/index.json` has fewer than 346 entries.

### Pitfall 5: `get_estadisticas_delictuales_mapa.php` Is Broken

**What goes wrong:** Code tries to use the mapa endpoint (as documented in `como scrap.txt`) and gets HTTP 500 on every call.
**Why it happens:** This endpoint was returning 500 as of research date — likely a server-side PHP error in the current deployment.
**How to avoid:** Do not use the mapa endpoint. Use `get_estadisticas_delictuales.php` with `seleccion=1` and `comuna[]` arrays for all data.
**Warning signs:** HTTP 500 with WordPress error page in response body.

### Pitfall 6: `seleccion` Param Confusion

**What goes wrong:** Using `seleccion=2` (by crime family) when you want territorial breakdown, or vice versa. The response table structure is completely different for each value.
**Why it happens:** The param name doesn't describe what it does.
**How to avoid:** Use `seleccion=1` for territorial (commune) breakdown. Use `seleccion=2` for crime family breakdown at a single territory. Build separate parser functions for each table structure.

### Pitfall 7: Forgetting to Pass the Commune CUT Codes as Strings

**What goes wrong:** `payload['comuna[]'] = [13101, 13102]` (integers) fails silently — CEAD returns only the region-level row.
**Why it happens:** POST form data must be strings; requests coerces ints but the server may reject them silently.
**How to avoid:** Always use `str(cut_code)` when building the payload.

---

## Code Examples

### Full Session Setup

```python
# Source: verified live against CEAD 2026-06-12
import requests

def make_cead_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; IsChileSafe data pipeline; +https://ischilesafe.com)',
        'Referer': 'https://cead.minsegpublica.gob.cl/estadisticas-delictuales/',
        'Origin': 'https://cead.minsegpublica.gob.cl',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
    })
    # Warm up session to get cookie (wpdm_client cookie)
    session.get('https://cead.minsegpublica.gob.cl/estadisticas-delictuales/', timeout=15)
    return session
```

### Trend Calculation (D-13)

```python
# Source: ASSUMED — implements D-13 spec; exact threshold TBD in planning
def compute_trend(series: list[dict], threshold_pct: float = 5.0) -> str:
    """
    Compute 3-year trend as 'up'/'down'/'stable'.
    series: list of {'year': int, 'rate_per_100k': float}, sorted ascending.
    """
    if len(series) < 4:
        return 'stable'  # not enough data
    recent = sorted(series, key=lambda x: x['year'])[-4:]  # last 4 years
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

### Slug Generation for Chilean Names

```python
# Source: ASSUMED — standard pattern for Spanish/Chilean text normalization
import unicodedata, re

def make_slug(name: str) -> str:
    """Convert 'Ñuñoa' → 'nunoa', 'O'Higgins' → 'ohiggins'"""
    normalized = unicodedata.normalize('NFD', name)
    ascii_name = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    slug = re.sub(r"[^a-z0-9]+", '-', ascii_name.lower()).strip('-')
    return slug
```

---

## INE Population Data

**Source needed (D-11):** Official INE communal population projections 2002–2035.

**Finding:** A processed dataset is available at `https://github.com/bastianolea/censo_proyecciones_poblacion/raw/main/datos/datos_procesados/censo_proyecciones_año.csv` — approximately 11,000 rows covering all 346 communes from 2002 to 2035. [CITED: github.com/bastianolea/censo_proyecciones_poblacion]

The authoritative source is the INE official page at `https://www.ine.gob.cl/estadisticas/sociales/demografia-y-vitales/proyecciones-de-poblacion` — direct download links to Excel/CSV are behind a navigation UI. [CITED: ine.gob.cl]

**Recommended approach for D-11:** Download the CSV from the bastianolea repo (which processes the official INE source data), verify a sample against INE official publications, and commit the 2024 population values as `/data/ine/poblacion_comunal.json`. This is a one-time task — no scraping pipeline needed.

**Key field:** Year 2024 population per commune is what the pipeline needs for the `low_population` flag (>10,000 threshold, D-12) and for page context.

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| CEAD mapa endpoint for commune-level data | Main endpoint with `comuna[]` array (mapa returns 500) | Requires batching by region; more requests but works |
| pydantic v1 `class Config` / `@validator` | pydantic v2 `model_config` / `@field_validator` | v2 is current; do NOT use v1 syntax |
| `requests.get()` without session | `requests.Session()` with warm-up GET | Session preserves cookie; warm-up avoids 403 |

**Deprecated/outdated:**
- `get_estadisticas_delictuales_mapa.php`: returns 500 as of research date — do not use.
- CEAD mapa endpoint with `medida`, `tipoVal` etc.: confirmed non-functional.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `seleccion=101` in `ajax_2.php` always returns all 346 communes (not a subset) | CEAD Live Validation | If CEAD filters by region param, need to loop over all 16 regions to collect full catalog |
| A2 | Batching all communes from one region in a single `comuna[]` request is performant and returns all communes reliably | Pattern 1 | May need to reduce batch size if server times out on large batches |
| A3 | CEAD rates (`medida=2`) are computed using the same INE population projections we're using for the filter | Standard Stack | If CEAD uses different population data, our rate calculations and CEAD's won't match — verify against one known commune |
| A4 | The `delitos-select` values 101 (Homicidios y femicidios) and 102 (Violaciones) are stable subgroup IDs for D-06 featured categories | Code Examples | If IDs change, the featured flag logic breaks silently |
| A5 | Trend threshold of 5% (D-13) is appropriate for Chilean crime rate volatility | Code Examples | If threshold is too sensitive or insensitive, trends will be misleading — verify against 3 sample communes with known direction |
| A6 | INE CSV from bastianolea/censo_proyecciones_poblacion accurately mirrors official INE data | INE Population section | Processed third-party repo — verify 5 commune values against official INE page before committing |

---

## Open Questions (RESOLVED)

1. **Batch size for commune arrays** — **RESOLVED in Plan 01-03**
   - What we know: Passing 5 RM communes in `comuna[]` worked in live testing
   - What's unclear: Maximum reliable batch size before the server times out or truncates output
   - Resolution: Plan 03's client batches all communes per region (largest is RM with ~52 communes), with a documented fallback to batches of 20 if timeouts occur. Confirmed live at the Plan 03 checkpoint.

2. **2026 partial year handling (Claude's Discretion)** — **RESOLVED in Plan 01-04 Task 2**
   - What we know: CEAD `temporalidad-select` includes 2026; live data exists
   - What's unclear: Whether 2026 data is partial (mid-year) or complete
   - Resolution: 2026 is included with a `partial: true` flag on `YearRecord` when the scrape date is before December 31, and excluded from trend calculation. Implemented in Plan 04 Task 2.

3. **Featured subgroup IDs for homicides/kidnappings (D-06)** — **CONDITIONALLY RESOLVED (Plan 01-03 checkpoint + Plan 01-04 fallback)**
   - What we know: `delitos-select` has value `101` for "Homicidios y femicidios" (confirmed)
   - What's unclear: Whether secuestros (kidnappings) has a visible, stable subgroup ID
   - Resolution: Homicides = ID 101 confirmed. The kidnappings subgroup ID is confirmed at Plan 03's live-endpoint checkpoint; Plan 04's normalizer keeps the kidnappings entry keyed with a documented "pending" state if still unconfirmed — homicide/property featured rates are never dropped. Uncertainty handled without scope reduction.

4. **Rate plausibility baseline (D-16)** — **RESOLVED in Plan 01-01 Task 2**
   - What we know: First run must establish the baseline; broad absolute limits for first run
   - What's unclear: What absolute limits are reasonable (D-16 says "broad absolute limits")
   - Resolution: First run uses absolute limits 0–20,000 per 100k via the named constant `PLAUSIBILITY_MAX_RATE = 20000` in Plan 01 Task 2; tighten to ±3x historical maximum after the baseline is established.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Pipeline runtime | ✓ | 3.13.13 (local); 3.12 on GitHub Actions ubuntu-latest | — |
| pip | Package install | ✓ | current | — |
| Node.js | Not required in this phase | ✓ | 22.21.1 | — |
| Internet access to CEAD | Scraper | ✓ | Confirmed live | Graceful fail + GitHub issue alert |
| GitHub Actions | CI/CD (Phase 6 scope) | N/A | N/A | Run locally with `python pipeline/scrape_cead.py` |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (standard Python; install if not present) |
| Config file | `pipeline/pytest.ini` — Wave 0 gap |
| Quick run command | `pytest pipeline/tests/ -x -q` |
| Full suite command | `pytest pipeline/tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | Scraper produces output for 346 communes | integration (live) | `pytest pipeline/tests/test_scraper.py::test_produces_346_communes` | ❌ Wave 0 |
| DATA-01 | Correct parameter names sent to CEAD endpoint | unit (mock) | `pytest pipeline/tests/test_client.py::test_request_params` | ❌ Wave 0 |
| DATA-02 | Pydantic validation rejects record with missing key | unit | `pytest pipeline/tests/test_schema.py::test_missing_key_rejected` | ❌ Wave 0 |
| DATA-02 | Pydantic validation rejects fewer than 346 communes | unit | `pytest pipeline/tests/test_schema.py::test_count_validation` | ❌ Wave 0 |
| DATA-02 | Pipeline exits non-zero on validation failure | unit | `pytest pipeline/tests/test_schema.py::test_nonzero_exit_on_failure` | ❌ Wave 0 |
| DATA-03 | map-payload.json is under 30 KB | unit | `pytest pipeline/tests/test_output.py::test_map_payload_size` | ❌ Wave 0 |
| DATA-03 | Atomic write: no partial files on crash | unit | `pytest pipeline/tests/test_atomic_write.py::test_atomic_write` | ❌ Wave 0 |
| DATA-04 | Trend calculated correctly for known series | unit | `pytest pipeline/tests/test_normalizer.py::test_trend_up_down_stable` | ❌ Wave 0 |
| DATA-04 | Low-population communes excluded from rankings | unit | `pytest pipeline/tests/test_normalizer.py::test_low_pop_rank_null` | ❌ Wave 0 |

### Wave 0 Gaps

- [ ] `pipeline/tests/__init__.py` — test package
- [ ] `pipeline/tests/conftest.py` — fixtures (mock CEAD response HTML, sample commune dicts)
- [ ] `pipeline/tests/test_client.py` — HTTP client unit tests with mocked `requests`
- [ ] `pipeline/tests/test_parser.py` — HTML parser unit tests with fixture HTML
- [ ] `pipeline/tests/test_schema.py` — Pydantic validation tests
- [ ] `pipeline/tests/test_normalizer.py` — trend, slug, rank logic tests
- [ ] `pipeline/tests/test_atomic_write.py` — atomic write test
- [ ] `pipeline/tests/test_output.py` — output file size and structure tests
- [ ] Framework install: `pip install pytest` — if not already in requirements.txt

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Pipeline has no user authentication |
| V3 Session Management | No | Stateless cron pipeline |
| V4 Access Control | No | No access control layer |
| V5 Input Validation | Yes | Pydantic model validation on all parsed CEAD output |
| V6 Cryptography | No | No encryption in this phase |
| V7 Error/Logging | Yes | Non-zero exit on schema failure; error log to GitHub issue |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| CEAD endpoint returns malicious/corrupted data | Tampering | Pydantic validation + plausibility range checks before any write |
| API key exposure | Information Disclosure | `DEEPSEEK_API_KEY` not used in this phase; `GITHUB_TOKEN` auto-managed by Actions |
| Unbounded file write | Denial of Service | 346 files × known max size; validate count before writing |
| Scraping too aggressively (DoS of government server) | Repudiation | 2–3 s delay between batches; 16 region batches per full run |

---

## Sources

### Primary (HIGH confidence)
- Live HTTP testing against CEAD endpoints, 2026-06-12 — endpoint behavior, parameter names, response format, encoding
- PyPI registry — `pip index versions` for all package versions
- slopcheck v0.6.1 — package legitimacy scan
- `.planning/research/ARCHITECTURE.md` — schema design, file layout
- `.planning/research/PITFALLS.md` — domain pitfalls
- `.planning/research/STACK.md` — Python stack decisions

### Secondary (MEDIUM confidence)
- [github.com/bastianolea/censo_proyecciones_poblacion](https://github.com/bastianolea/censo_proyecciones_poblacion) — communal population CSV processed from official INE data
- [Pydantic v2 docs](https://docs.pydantic.dev/latest/) — model_validate, field_validator syntax [ASSUMED — not fetched via Context7 in this session]

### Tertiary (LOW confidence)
- `como scrap.txt` — original scrapeability analysis (endpoint list confirmed accurate; mapa endpoint now broken)

---

## Metadata

**Confidence breakdown:**
- CEAD endpoint behavior: HIGH — verified live in this session
- Standard Stack (Python libs): HIGH — verified via PyPI registry + slopcheck
- Architecture patterns: HIGH — based on verified live behavior + ARCHITECTURE.md
- INE population data: MEDIUM — source identified but direct official download URL not confirmed; third-party repo identified as proxy

**Research date:** 2026-06-12
**Valid until:** 2026-09-12 (CEAD endpoint behavior may change without notice; re-validate before each quarterly run)
