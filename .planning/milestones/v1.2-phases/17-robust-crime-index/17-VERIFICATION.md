---
status: passed
phase: 17-robust-crime-index
gate: phase-verification
requirements: [DQ-01, DQ-02, DQ-03, DQ-04]
verified: 2026-06-18
re_verified: 2026-06-18T00:00:00Z
method: chained build+validate + dist host gate + snapshot schema checks + BrowserOS visual (EN+ES) + commune spot-check
score: 4/4 requirements verified
---

# Phase 17 — Verification Gate

**Phase Goal:** Every quantitative figure on the site is verifiably correct and traceable to its authoritative source, and the methodology explicitly names and links each source — without re-architecting the metric. FOCUSED scope: composite index / schema migration deferred to Phase 18.

**Result: PASSED.** All four requirements attested with concrete codebase evidence. No displayed metric, choropleth, or data schema changed (focused scope honored).

## Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every surfaced figure re-derived from CEAD cache with zero unexplained delta | VERIFIED | `17-DATA-QUALITY.md`: 8 PASS, 2 DOCUMENTED, 0 FAIL; harness runs offline |
| 2 | Wrong host `ministeriointerior.gob.cl` absent from all source pages | VERIFIED | `grep -r ministeriointerior.gob.cl site/src/` → ABSENT |
| 3 | Correct host `minsegpublica.gob.cl` present in both methodology pages + SOURCES.md | VERIFIED | Confirmed in `methodology.astro`, `es/metodologia.astro`, `data/SOURCES.md` |
| 4 | All four source links (CEAD, SPD, SII, Fiscalía) present with full URL parity EN+ES | VERIFIED | All four domains confirmed in both `.astro` files |
| 5 | Snapshots committed with correct record counts; no raw xlsx/xlsb in repo | VERIFIED | spd=1534, sii=6820, fiscalia=5 records; no `.xls*` in `data/snapshots/` |
| 6 | Scope guardrail: `data/cead/`, `featured_rates`, `by_family` untouched | VERIFIED | 346 commune JSONs intact; snapshot files marked REFERENCE-ONLY, unwired |

**Score:** 4/4 requirements verified (6/6 observable truths)

## Automated gate

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Chained `npm run build && npm run validate` (OneDrive-safe, single invocation) | exit 0, all validators green | 790 pages built (22.76s); **12/12 validators PASS** incl. #9 forbidden-language | PASS |
| Dist host gate | `ministeriointerior.gob.cl` absent from `site/dist/**/*.html` | CLEAN across 790 HTML files | PASS |
| Correct host present | `minsegpublica.gob.cl` in built methodology HTML | present | PASS |
| `data/snapshots/spd_homicide.json` | >200 records | 1534 records (nested under `records` key in dict) | PASS |
| `data/snapshots/sii_exposure.json` | >200 records | 6820 records | PASS |
| `data/snapshots/fiscalia_secuestro.json` | exists, non-empty regional records | 5 records | PASS |

## BrowserOS visual check (checkpoint, APPROVED)

Driven inline at `http://127.0.0.1:9200/mcp` against the local Astro preview (`http://localhost:4323/`). Screenshots: `.../Temp/browseros-shots/methodology-en.png`, `metodologia-es.png`.

- **EN `/methodology/`** — renders host `cead.minsegpublica.gob.cl` (no `ministeriointerior`); four clickable source links present and correctly targeted: CEAD, SPD (`prevenciondehomicidios.cl`), SII (`sii.cl`), Fiscalia (`fiscaliadechile.cl`). All caveats visible: casos-policiales `tipoVal=1,2` semantics, partial-year, drug scope (Ley 20.000 grupo 401 vs Incivilidades 702), floating-population denominator, low-count volatility. Legal-safe "What this site does NOT say" section present.
- **ES `/es/metodologia/`** — full parity with EN: same host, same four links, same caveats, same legal-safe framing.
- **Commune spot-check** (`/commune/providencia/`) — cites "Rate per 100,000 inhabitants (2025)" and "Source: CEAD ... See our Methodology"; relative (not absolute) framing; Providencia's elevated rate matches the documented floating-population anomaly.

## Per-requirement attestation

| Req | Statement | Evidence | Status |
|-----|-----------|----------|--------|
| **DQ-01** | Every surfaced figure verified vs authoritative source; 4 anomalies re-derived + explained; partial-year flags present | `17-DATA-QUALITY.md`: **8 PASS, 2 DOCUMENTED, 0 FAIL**; harness `pipeline/scripts/verify_data_quality.py` (751 lines, imports `parse_cead_table` + `load_cached`); `data/cead/` + `pipeline/cead/` untouched (read-only) | PASS |
| **DQ-02** | Canonical source registry exists; wrong CEAD host corrected everywhere | `data/SOURCES.md` (201 lines, 5 data classes w/ host+URL+vintage+licence+semantics); `ministeriointerior.gob.cl` absent from `site/src/`; methodology + terms pages corrected | PASS |
| **DQ-03** | Bilingual methodology rewritten: correct host, measure semantics, all caveats, named authoritative sources, clickable links; legal-safe | validator #9 PASS; BrowserOS EN+ES render confirmed; 7 H2 parity; all 4 source links (`minsegpublica`, `prevenciondehomicidios`, `sii.cl`, `fiscaliadechile`) confirmed in both `.astro` files via independent grep | PASS |
| **DQ-04** | Reproducible normalized snapshots committed (SPD/SII/Fiscalia), reference-only | 3 JSON snapshots (1534 / 6820 / 5 records) + `data/snapshots/ATTRIBUTION.md` (50 lines); 3 `pipeline/snapshots/*.py` scripts; no raw xlsx/xlsb committed; not wired to any displayed metric | PASS |

## Scope-guardrail attestation

No change to the **displayed metric**, the **map choropleth metric**, or the **data schema** (`featured_rates` / `by_family`). 346 commune JSONs confirmed intact. Composite index, homicide-metric switch, and the 7-metric schema migration remain deferred to Phase 18. Snapshots under `data/snapshots/` are reference-only and unwired.

## Requirements Coverage

| Requirement | PLAN | Description | Status |
|-------------|------|-------------|--------|
| DQ-01 | 17-01-PLAN.md | Offline data-quality harness + evidence report | SATISFIED |
| DQ-02 | 17-02-PLAN.md (implied) | Canonical source registry + host correction | SATISFIED |
| DQ-03 | 17-03-PLAN.md (implied) | Bilingual methodology rewrite | SATISFIED |
| DQ-04 | 17-04/05-PLAN.md (implied) | Reproducible reference snapshots | SATISFIED |

---

_Initial verification: 2026-06-18 (orchestrator — BrowserOS inline)_
_Goal-backward re-verification: 2026-06-18 (gsd-verifier — independent codebase checks)_
_Verifier: Claude (gsd-verifier)_
