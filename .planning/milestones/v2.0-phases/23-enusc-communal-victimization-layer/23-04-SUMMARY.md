---
phase: 23-enusc-communal-victimization-layer
plan: "04"
subsystem: docs-registry-methodology
tags: [figure-registry, sources, methodology, enusc, vhdv, validation]
dependency_graph:
  requires: ["23-03"]
  provides: ["VL-05 acceptance gate — F16 zero-orphan, SOURCES.md distinct section, EN/ES methodology documentation, Phase-18 byte-unchanged confirmation"]
  affects: ["site/scripts/validate/figure-registry.mjs", "data/SOURCES.md", "site/src/pages/methodology.astro", "site/src/pages/es/metodologia.astro"]
tech_stack:
  added: []
  patterns: ["figure-registry token group extension", "SOURCES.md distinct section per figure", "methodology H2 additive section"]
key_files:
  created: []
  modified:
    - site/scripts/validate/figure-registry.mjs
    - data/SOURCES.md
    - site/src/pages/methodology.astro
    - site/src/pages/es/metodologia.astro
decisions:
  - "F16 registered with two token groups: ['## INE ENUSC SAE','VHDV'] and ['ENUSC','Victimizacion en Hogares','SAE'] — both satisfied by the new SOURCES.md section"
  - "SOURCES.md section kept separate from F11 ## ENUSC underreporting block — two distinct registrations for two distinct uses of ENUSC data"
  - "Methodology sections are additive H2 blocks inserted after the existing underreporting (cifra negra) H2 — no existing content touched"
  - "Full gate: 204/204 pytest (incl. test_phase18_byte_unchanged) + 13/13 Node validators green — Phase-18 outputs confirmed byte-unchanged"
metrics:
  duration: "~8 minutes"
  completed: "2026-06-19"
  tasks_completed: 3
  files_changed: 4
---

# Phase 23 Plan 04: Phase Closure — F16 Registry, SOURCES.md, Methodology Documentation Summary

**One-liner:** F16 registered (two token groups, zero-orphan), separate INE ENUSC SAE section added to SOURCES.md, EN+ES methodology pages document VHDV indicator with experimental/coverage caveats, full gate green (204 pytest + 13 validators, Phase-18 byte-unchanged).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Register F16 + add distinct INE ENUSC SAE section to SOURCES.md | bb6e984 | figure-registry.mjs, data/SOURCES.md |
| 2 | Document indicator on EN + ES methodology pages | a69ab21 | methodology.astro, es/metodologia.astro |
| 3 | Full-suite gate + Phase-18 byte-unchanged verification | (no code change) | — |

## What Was Built

### Task 1: F16 Registration

Added F16 entry to `FIGURE_REGISTRY` array in `site/scripts/validate/figure-registry.mjs`:
- `id: 'F16'`, description: "ENUSC SAE VHDV household victimization rate (experimental, 2024)"
- Token group 1: `['## INE ENUSC SAE', 'VHDV']`
- Token group 2: `['ENUSC', 'Victimizacion en Hogares', 'SAE']`
- Note distinguishing from F11 (underreporting claims)
- Console banner updated from "F1-F15" to "F1-F16"

Added distinct `## INE ENUSC SAE — communal VHDV victimization (experimental)` section to `data/SOURCES.md` with full attribution: publisher INE, landing page, file URL with sfvrsn caveat, measure semantics (proportion 0-1 NOT per-100k), experimental status, vintage 2024, sha256, used-by chain, licence, and explicit "Distinct from" reference to F11 block.

### Task 2: Methodology Documentation

Added separate H2 sections to both methodology pages after the existing ENUSC/cifra-negra section:
- EN: `<h2 id="enusc-vhdv">Household Victimization Indicator (ENUSC 2024 SAE)</h2>`
- ES: `<h2 id="enusc-vhdv">Indicador de Victimización en Hogares (ENUSC 2024 SAE)</h2>`

Both sections cover: VHDV proportion-of-households measure, SAE method, INE experimental status, 136/346 coverage limit, explicit statement that it is additive and NOT merged with CEAD per-100k index, attributed INE source link. No forbidden verdict language.

### Task 3: Full-Suite Gate

- `python -m pytest tests/ -q` → 204 passed (including test_phase18_byte_unchanged, test_enusc_coverage, test_enusc_graceful)
- `npm run validate` → 13/13 validators PASS (figure-registry F16 zero-orphan, forbidden-language, commune enusc presence)
- No code changes — verification-only task

## Verification Results

| Check | Result |
|-------|--------|
| `node figure-registry.mjs` | PASS — 16/16 figures, zero orphans |
| `python -m pytest tests/ -q` | 204 passed, 0 failed |
| `npm run build && npm run validate` | 13/13 PASS, 791 pages built |
| dist/methodology/index.html contains "ENUSC 2024 SAE" | PASS |
| dist/es/metodologia/index.html contains "ENUSC 2024 SAE" | PASS |
| forbidden-language | PASS — 793 pages, 0 forbidden terms |
| Phase-18 byte-unchanged | CONFIRMED — test_phase18_byte_unchanged green |

## Deviations from Plan

None — plan executed exactly as written. All three tasks completed within scope; no architectural decisions required; no bugs found. The figure-registry validator immediately passed after the two edits, confirming token alignment between SOURCES.md and the registry entry.

## Known Stubs

None. This plan is documentation-only (registry + sources + methodology). No data rendering paths were modified.

## Threat Flags

None. All mitigations in the threat register were applied:
- T-23-10 (F16 token drift): figure-registry zero-orphan validator confirmed passing
- T-23-11 (methodology verdict language): forbidden-language validator confirmed 0 violations across 793 pages
- T-23-12 (Phase-18 output regression): test_phase18_byte_unchanged green in 204-test suite

## Self-Check: PASSED

- `site/scripts/validate/figure-registry.mjs` — modified, F16 entry present
- `data/SOURCES.md` — modified, `## INE ENUSC SAE` section present
- `site/src/pages/methodology.astro` — modified, "ENUSC 2024 SAE" present
- `site/src/pages/es/metodologia.astro` — modified, "ENUSC 2024 SAE" present
- Commit bb6e984 — verified in git log
- Commit a69ab21 — verified in git log
