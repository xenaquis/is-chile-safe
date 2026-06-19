---
status: passed
phase: 17-robust-crime-index
gate: phase-verification
requirements: [DQ-01, DQ-02, DQ-03, DQ-04]
verified: 2026-06-18
method: chained build+validate + dist host gate + snapshot schema checks + BrowserOS visual (EN+ES) + commune spot-check
---

# Phase 17 — Verification Gate

**Result: PASSED.** All four requirements attested with concrete evidence. No displayed metric, choropleth, or data schema changed (focused scope honored).

## Automated gate (Task 1)

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Chained `npm run build && npm run validate` (OneDrive-safe, single invocation) | exit 0, all validators green | 790 pages built (22.76s); **12/12 validators PASS** incl. #9 forbidden-language | ✅ PASS |
| Dist host gate | `ministeriointerior.gob.cl` absent from `site/dist/**/*.html` | CLEAN across 790 HTML files | ✅ PASS |
| Correct host present | `minsegpublica.gob.cl` in built methodology HTML | present | ✅ PASS |
| `data/snapshots/spd_homicide.json` | >200 records | 1534 records | ✅ PASS |
| `data/snapshots/sii_exposure.json` | >200 records | 6820 records | ✅ PASS |
| `data/snapshots/fiscalia_secuestro.json` | exists, non-empty regional records | 5 records | ✅ PASS |

## BrowserOS visual check (Task 2 — checkpoint, APPROVED)

Driven inline at `http://127.0.0.1:9200/mcp` against the local Astro preview (`http://localhost:4323/`). Screenshots: `…/Temp/browseros-shots/methodology-en.png`, `metodologia-es.png`.

- **EN `/methodology/`** — renders host `cead.minsegpublica.gob.cl` (no `ministeriointerior`); four clickable source links present and correctly targeted: CEAD, SPD (`prevenciondehomicidios.cl`), SII (`sii.cl`), Fiscalía (`fiscaliadechile.cl`). All caveats visible: casos-policiales `tipoVal=1,2` semantics, partial-year, drug scope (Ley 20.000 grupo 401 vs Incivilidades 702), floating-population denominator, low-count volatility. Legal-safe "What this site does NOT say" section present.
- **ES `/es/metodologia/`** — full parity with EN: same host, same four links, same caveats, same legal-safe framing.
- **Commune spot-check** (`/commune/providencia/`) — cites "Rate per 100,000 inhabitants (2025)" and "Source: CEAD … See our Methodology"; relative (not absolute) framing; Providencia's elevated rate matches the documented floating-population anomaly.

## Per-requirement attestation (Task 3)

| Req | Statement | Evidence | Status |
|-----|-----------|----------|--------|
| **DQ-01** | Every surfaced figure verified vs authoritative source; 4 anomalies re-derived + explained; partial-year flags present | `17-DATA-QUALITY.md`: **8 PASS, 2 DOCUMENTED, 0 FAIL**; harness `pipeline/scripts/verify_data_quality.py` runs offline from `pipeline/cache/`; `data/cead/`+`pipeline/cead/` untouched (read-only) | ✅ PASS |
| **DQ-02** | Canonical source registry exists; wrong CEAD host corrected everywhere | `data/SOURCES.md` (5 data classes w/ host+URL+vintage+licence+semantics); dist host gate CLEAN; terms + methodology pages corrected | ✅ PASS |
| **DQ-03** | Bilingual methodology rewritten: correct host, measure semantics, all caveats, named authoritative sources, clickable links; legal-safe | validator #9 PASS; BrowserOS EN+ES render confirmed; 7 H2 parity; 4 source links each language | ✅ PASS |
| **DQ-04** | Reproducible normalized snapshots committed (SPD/SII/Fiscalía), reference-only | 3 JSON snapshots (1534 / 6820 / 5 records) + `data/snapshots/ATTRIBUTION.md`; 3 `pipeline/snapshots/*.py` with `CACHE_ONLY=1`; no raw xlsx/xlsb committed; not wired to any displayed metric | ✅ PASS |

## Scope-guardrail attestation

No change to the **displayed metric**, the **map choropleth metric**, or the **data schema** (`featured_rates` / `by_family`). Composite index, homicide-metric switch, and the 7-metric schema migration remain **deferred to Phase 18**. Snapshots under `data/snapshots/` are reference-only and unwired. `git diff` over the phase confirms `data/cead/` and the displayed-payload build were not modified by verification or snapshot work.
