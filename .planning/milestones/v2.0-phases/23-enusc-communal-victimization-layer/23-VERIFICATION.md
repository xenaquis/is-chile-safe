---
phase: 23-enusc-communal-victimization-layer
verified: 2026-06-19T00:00:00Z
status: passed
score: 12/12
overrides_applied: 0
---

# Phase 23: ENUSC Communal Victimization Layer Verification Report

**Phase Goal:** Additive INE ENUSC 2024 SAE household-victimization (VHDV) figure on the 136 covered comuna pages; graceful "no estimate" for 210 uncovered; experimental/SAE caveat mandatory; Phase-18 outputs byte-unchanged (additive-only); graceful CI failure.
**Verified:** 2026-06-19
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | VHDV snapshot exists with 136 records, full provenance, sha256-guarded | VERIFIED | `data/snapshots/enusc_vhdv.json` — 136 records, keys `cut name vhdv_rate ci_lower ci_upper tipo_estimacion cv`, top-level provenance block present |
| 2 | vhdv_rate values are proportions 0–1 (not per-100k) | VERIFIED | Observed range 0.031–0.176 in snapshot; ATTRIBUTION.md note explicitly states "NOT per-100k" |
| 3 | Fetcher guards sha256 before parsing (KNOWN_SHA256 constant present) | VERIFIED | `pipeline/snapshots/fetch_enusc_vhdv.py` — `KNOWN_SHA256 = ad9503...` constant; `_assert_sha256` called before parse; live run downloaded and verified sha256 |
| 4 | Enrichment is additive-only; EXPECTED_COVERAGE = 136; overwrite-refusal guard present | VERIFIED | `pipeline/build_enusc_enrichment.py` — `EXPECTED_COVERAGE = 136` (line 28); coverage RuntimeError at line 85; overwrite-refusal confirmed by test |
| 5 | Graceful CI failure: enrichment exits 0 when snapshot absent; cead-scraper.yml has continue-on-error on both ENUSC steps | VERIFIED | `sys.exit(0)` on missing snapshot; workflow check confirmed: `fetch_enusc_vhdv.py` (line 36–40) and `build_enusc_enrichment.py` (line 42–44) both with `continue-on-error: true`, ordered after `scrape_cead.py` and before `build_composite_index.py` |
| 6 | Covered EN commune page renders VHDV as percentage (rate * 100, 1 decimal, %) with experimental/SAE caveat | VERIFIED | `site/src/pages/commune/[slug].astro` line 257: `{(vhdv.vhdv_rate * 100).toFixed(1)}%`; section with `enusc-vhdv-section` class; i18n key `enusc_caveat_text` wired |
| 7 | Covered ES commune page renders VHDV module with bilingual caveat | VERIFIED | `site/src/pages/es/comuna/[slug].astro` — identical pattern at lines 248–258 with ES i18n strings |
| 8 | Uncovered pages show explicit "no estimate" note (both EN and ES), no broken layout | VERIFIED | Both templates: `enusc-no-estimate` section rendered when `data.enusc_vhdv` is falsy (line 248/251 ES; 245/248 EN) |
| 9 | commune.mjs validator asserts every commune page has either `enusc-vhdv-section` or `enusc-no-estimate` | VERIFIED | `site/scripts/validate/commune.mjs` lines 270–274 and 307–311: presence check for both class names, `console.error` + failure on absence |
| 10 | F16 registered in figure-registry.mjs; zero-orphan check extended to F1-F16 | VERIFIED | `figure-registry.mjs` line 193: `id: 'F16'`; line 196: token `['## INE ENUSC SAE', 'VHDV']`; banner updated to "F1-F16" (lines 206, 251) |
| 11 | `data/SOURCES.md` has separate `## INE ENUSC SAE` section distinct from existing F11 ENUSC underreporting block | VERIFIED | `data/SOURCES.md` line 318: `## INE ENUSC SAE — communal VHDV victimization (experimental)` — separate heading, confirmed not merged with F11 block |
| 12 | EN + ES methodology pages document the ENUSC SAE VHDV indicator with correct H2 headings | VERIFIED | `methodology.astro` line 240: `Household Victimization Indicator (ENUSC 2024 SAE)`; `metodologia.astro` line 248: `Indicador de Victimización en Hogares (ENUSC 2024 SAE)` |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/snapshots/fetch_enusc_vhdv.py` | XLSX ingestion with sha256 guard + CUT join | VERIFIED | Contains `KNOWN_SHA256`, `_assert_sha256`, direct col-A CUT parse, make_slug cross-check |
| `pipeline/tests/test_fetch_enusc_vhdv.py` | 5 pytest cases covering CACHE_ONLY, sha256, column, record-count guard | VERIFIED | Exists; all 10 pipeline tests pass (`10 passed in 1.99s`) |
| `data/snapshots/enusc_vhdv.json` | 136 records, provenance block, vhdv_rate 0–1 | VERIFIED | 136 records confirmed; full provenance keys present |
| `data/snapshots/ATTRIBUTION.md` | WIRED note for enusc_vhdv.json, sha256 recorded | VERIFIED | `**WIRED to commune pages (section 6c)**` note present; sha256 matches |
| `pipeline/build_enusc_enrichment.py` | Additive enrichment; EXPECTED_COVERAGE; overwrite-refusal; graceful exit | VERIFIED | All guards present; EXPECTED_COVERAGE = 136 |
| `pipeline/tests/test_build_enusc_enrichment.py` | 5 pytest cases: graceful-degrade, coverage, additive-only, byte-unchanged, idempotent | VERIFIED | Exists; all tests pass |
| `.github/workflows/cead-scraper.yml` | ENUSC fetch+enrich steps after CEAD scraper, before composite, continue-on-error | VERIFIED | Order confirmed programmatically; CACHE_ONLY='1' set on fetch step |
| `site/src/lib/data.ts` | `enusc_vhdv?` optional field on CommuneData | VERIFIED | Line 69: `enusc_vhdv?: { ... }` |
| `site/src/config/i18n.ts` | 6 new ENUSC i18n keys in I18nStrings + EN_STRINGS + ES_STRINGS | VERIFIED | `enusc_section_heading` present in type (line 163), EN (line 329), ES (line 500) |
| `site/src/pages/commune/[slug].astro` | Section 6c EN VHDV module + no-estimate fallback | VERIFIED | `enusc-vhdv-section` + `enusc-no-estimate` both present |
| `site/src/pages/es/comuna/[slug].astro` | Section 6c ES VHDV module + no-estimate fallback | VERIFIED | Same pattern confirmed |
| `site/scripts/validate/commune.mjs` | Presence assertion for `enusc-vhdv-section` or `enusc-no-estimate` on every commune page | VERIFIED | Lines 270–311: hard assertion with console.error on failure |
| `site/scripts/validate/figure-registry.mjs` | F16 entry, F1-F16 banner | VERIFIED | F16 id and tokens at lines 193–196; banner at lines 206, 251 |
| `data/SOURCES.md` | `## INE ENUSC SAE` section (separate from F11) | VERIFIED | Line 318 confirmed |
| `site/src/pages/methodology.astro` | EN H2 "Household Victimization Indicator (ENUSC 2024 SAE)" | VERIFIED | Line 240 confirmed |
| `site/src/pages/es/metodologia.astro` | ES H2 "Indicador de Victimización en Hogares (ENUSC 2024 SAE)" | VERIFIED | Line 248 confirmed |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `fetch_enusc_vhdv.py` | `pipeline/cache/enusc_vhdv.xlsx` | `hashlib.sha256` assertion before parse | WIRED | `_assert_sha256` present; live run verified sha256 match |
| `fetch_enusc_vhdv.py` | `data/cead/meta/index.json` | `make_slug` cross-check | WIRED | Import of `make_slug` + `_build_cut_map` confirmed in source |
| `build_enusc_enrichment.py` | `data/cead/comunas/{CUT}.json` | `atomic_write_json` additive write | WIRED | `atomic_write_json` call present; additive-only pattern |
| `.github/workflows/cead-scraper.yml` | `build_enusc_enrichment.py` | `continue-on-error` step after scraper | WIRED | Both ENUSC steps confirmed after scrape_cead.py and before build_composite_index.py |
| `commune/[slug].astro` | `data.enusc_vhdv` | IIFE null-guard → section 6c | WIRED | `const vhdv = data.enusc_vhdv` → conditional rendering |
| `commune/[slug].astro` | `i18n.ts` | `t.enusc_*` keys | WIRED | Pattern `t.enusc_` confirmed at multiple lines |
| `figure-registry.mjs` | `data/SOURCES.md` | F16 token `## INE ENUSC SAE` presence check | WIRED | Token `['## INE ENUSC SAE', 'VHDV']` in registry; section confirmed in SOURCES.md |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Snapshot has 136 records, required keys, vhdv_rate in (0,1) | `python -c "import json,pathlib; ..."` | 136 records, range 0.031–0.176 | PASS |
| Pipeline pytest (fetch + enrichment tests) | `cd pipeline && python -m pytest tests/test_fetch_enusc_vhdv.py tests/test_build_enusc_enrichment.py -q` | `10 passed in 1.99s` | PASS |
| Fetcher sha256 guard: live run verified | `python pipeline/snapshots/fetch_enusc_vhdv.py` | Downloaded + sha256 verified; 136 records written | PASS |
| Workflow step order correct | `python -c "... assert k < i < j ..."` | `workflow order OK` | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| VL-01 | 23-01, 23-02 | Versioned snapshot with provenance; sha256-guarded; graceful CI failure (continue-on-error) | SATISFIED | `enusc_vhdv.json` present; sha256 guard in fetcher; both CI steps `continue-on-error: true` |
| VL-02 | 23-01, 23-02 | All 136 parsed CUTs exist in index.json; build-time coverage assertion == 136 | SATISFIED | Direct col-A CUT join; `EXPECTED_COVERAGE = 136` with RuntimeError on mismatch |
| VL-03 | 23-03 | 136 covered pages (EN+ES) show VHDV as % with experimental/SAE caveat; forbidden-language exits 0 | SATISFIED | Both templates render `(vhdv.vhdv_rate * 100).toFixed(1)%`; `enusc_caveat_text` i18n key wired |
| VL-04 | 23-03 | 210 uncovered pages show explicit "no estimate" note with no broken layout | SATISFIED | Both templates: `enusc-no-estimate` section when `data.enusc_vhdv` falsy; commune.mjs asserts presence |
| VL-05 | 23-02, 23-04 | F16 registered (zero-orphan); SOURCES.md ENUSC SAE section; methodology EN+ES documented; Phase-18 outputs byte-unchanged | SATISFIED | F16 in registry; SOURCES.md line 318; methodology H2 headings confirmed; byte-unchanged pytest passes |

---

### Anti-Patterns Found

No TBD, FIXME, or XXX markers found in phase-modified files. No stub returns. No hardcoded empty data passed to rendering paths.

---

### Human Verification Required

None. All truths were verifiable programmatically.

---

## Gaps Summary

No gaps. All 12 must-have truths verified, all 16 artifacts substantive and wired, all 5 requirements satisfied, and the 10-test pytest suite passes green.

---

_Verified: 2026-06-19_
_Verifier: Claude (gsd-verifier)_
