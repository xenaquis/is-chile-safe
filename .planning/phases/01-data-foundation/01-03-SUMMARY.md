---
phase: 01-data-foundation
plan: "03"
subsystem: pipeline/cead
tags: [cead, http-client, parser, data-ingestion]
dependency_graph:
  requires: [01-01, 01-02]
  provides: [pipeline/cead/client.py, pipeline/cead/catalog.py, pipeline/cead/parser.py, pipeline/tests/fixtures/cead_response_sample.html]
  affects: [01-04]
tech_stack:
  added: [requests, tenacity, beautifulsoup4, lxml]
  patterns: [session-warmup, tenacity-retry, latin1-decode, chilean-decimal-parse, lxml-table-parse]
key_files:
  created:
    - pipeline/cead/__init__.py
    - pipeline/cead/client.py
    - pipeline/cead/catalog.py
    - pipeline/cead/parser.py
    - pipeline/tests/fixtures/cead_response_sample.html
    - pipeline/tests/test_client.py
    - pipeline/tests/test_catalog.py
    - pipeline/tests/test_parser.py
  modified: []
decisions:
  - "_post_with_retry uses tenacity @retry decorator; inter-batch sleep belongs to orchestrator not client"
  - "parse_cead_float maps '', '-', 'S/I', 'N/A' all to None — treat all missing markers uniformly"
  - "Fixture captured live from CEAD 2026-06-12 with 3 RM communes; single request per courtesy (D-03)"
metrics:
  duration: "~20 minutes"
  completed: "2026-06-12"
---

# Phase 1 Plan 3: CEAD HTTP Client, Catalog, Parser Summary

CEAD ingestion layer with verified HTTP session (Referer/Origin/latin-1), commune catalog (ajax_2.php), and HTML table parser with Chilean decimal handling — all tested offline against a live-captured fixture.

## Tasks Completed

| Task | Description | Commit | Status |
|------|-------------|--------|--------|
| 1 | CEAD HTTP client + catalog (RED tests) | 49e8254 | Done |
| 1 | CEAD HTTP client + catalog (GREEN impl) | da42dac | Done |
| 2 | CEAD HTML parser + fixture (RED tests) | f5d0906 | Done |
| 2 | CEAD HTML parser + fixture (GREEN impl) | 0920fe8 | Done |
| 3 | checkpoint:human-verify (live endpoint confirmation) | — | PENDING |

## What Was Built

### pipeline/cead/client.py
- `make_cead_session()`: requests.Session with Referer/Origin/UA/Content-Type/Accept-Language headers + warm-up GET to obtain wpdm_client cookie (Pitfall 1 mitigation)
- `fetch_communes_batch(session, cut_codes, year, familia_id) -> str`: POSTs to get_estadisticas_delictuales.php with `medida='2'`, `tipoVal='1,2'`, `seleccion='1'`, `descarga='true'`, `anio[]`, `familia[]`, `comuna[]` (str-coerced CUT codes), `region[]` (first 2 digits). Decodes `response.content.decode('latin-1')` (Pitfall 3)
- `_post_with_retry(session, url, data)`: tenacity `@retry` with `wait_exponential(min=4, max=30)`, `stop_after_attempt(3)`, `retry_if_exception_type((requests.Timeout, requests.HTTPError))`
- `cache_raw(filename, content)` / `load_cached(filename)`: write/read to `pipeline/cache/` (git-ignored, D-04)

### pipeline/cead/catalog.py
- `get_commune_catalog(session) -> dict[str, str]`: POSTs ajax_2.php with `seleccion='101'`, parses ComunasDel JSON array (each entry is a JSON-encoded string with comDelId/comDelNombre)
- `REGION_IDS: dict[int, str]`: 16 official region entries
- `FAMILIA_IDS: dict[int, str]`: 7 crime families — `{1:"vida", 2:"robos_violentos", 3:"vif", 4:"drogas", 5:"armas", 6:"propiedad", 7:"incivilidades"}`

### pipeline/cead/parser.py
- `parse_cead_float(value: str) -> float | None`: Chilean locale ('1.154,3537' → 1154.3537); maps `''`, `'-'`, `'S/I'`, `'N/A'` to None (Pitfall 2 — critical, all CEAD numeric values go through this)
- `parse_cead_table(html: str) -> list[dict]`: BeautifulSoup + lxml, takes last table, detects year header row (4-digit cells), emits `{name, class, values: {year: str}}` rows, skips `DELITOS O FALTAS` / `UNIDAD TERRITORIAL` / empty labels

### pipeline/tests/fixtures/cead_response_sample.html
- **Live capture** from CEAD endpoint on 2026-06-12 via HTTP 200 response
- Communes: Santiago (13101), Cerrillos (13102), Puente Alto (13201), year 2024, familia 6 (propiedad)
- Contains 3 formato_4 commune rows with Chilean-decimal rate values (e.g. `'2.959,1026988104'`)

## Test Results

```
64 passed in 0.39s  (28 prior + 36 new)
```

- test_client.py: 22 tests — payload parameters, string CUT codes, latin-1 decode, header assertions, cache roundtrip
- test_catalog.py: 8 tests — ComunasDel parsing, REGION_IDS (16 entries), FAMILIA_IDS (7 entries), endpoint URL
- test_parser.py: 14 tests — parse_cead_float (8 cases), parse_cead_table (6 cases against live fixture)

## Live Endpoint Validation (Task 3 Checkpoint)

A single live call was made during Task 2 to capture the fixture:
- Endpoint: `get_estadisticas_delictuales.php`
- Parameters: cut_codes=['13101','13102','13201'], year=2024, familia_id=6
- Result: **HTTP 200**, 5893 bytes of HTML
- Parsed: 3 formato_4 commune rows (Santiago, Cerrillos, Puente Alto) with 2024 rate values

The human checkpoint (Task 3) is required to confirm the full parameter set remains valid before Plan 04 depends on them.

## Deviations from Plan

None — plan executed exactly as written.

The fixture was captured live (not synthetic) since the endpoint was reachable. Task 3 checkpoint is a blocking human verification as specified.

## Known Stubs

None — all parser output is real CEAD data.

## Threat Flags

None — no new network endpoints or trust boundaries introduced beyond what the plan specified.

## Self-Check: PASSED

- pipeline/cead/__init__.py: FOUND
- pipeline/cead/client.py: FOUND (contains `decode('latin-1')`, `comuna[]`, `medida`, `descarga`, tenacity `@retry`)
- pipeline/cead/catalog.py: FOUND (contains REGION_IDS with 16 entries, FAMILIA_IDS with 7 entries)
- pipeline/cead/parser.py: FOUND (contains `parse_cead_float`, `parse_cead_table`)
- pipeline/tests/fixtures/cead_response_sample.html: FOUND (live capture, 3 formato_4 rows)
- Commits 49e8254, da42dac, f5d0906, 0920fe8: all present in git log
- 64 tests pass
