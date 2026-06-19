---
phase: 23-enusc-communal-victimization-layer
plan: "03"
subsystem: site/frontend + validators
tags: [enusc, vhdv, commune-pages, i18n, section-6c, validators, vl-03, vl-04]
dependency_graph:
  requires: [23-02]
  provides: [site/src/lib/data.ts, site/src/config/i18n.ts, site/src/pages/commune/[slug].astro, site/src/pages/es/comuna/[slug].astro, site/scripts/validate/commune.mjs]
  affects: [dist/ commune pages (EN+ES), commune.mjs validator]
tech_stack:
  added: []
  patterns: [IIFE-null-guard, additive-i18n-keys, static-astro-markup, no-client-directives]
key_files:
  created: []
  modified:
    - site/src/lib/data.ts
    - site/src/config/i18n.ts
    - site/src/pages/commune/[slug].astro
    - site/src/pages/es/comuna/[slug].astro
    - site/scripts/validate/commune.mjs
    - data/cead/comunas/{136 commune JSONs enriched}
decisions:
  - "IIFE null-guard pattern mirrors section 6b composite-index analog exactly"
  - "enusc_vhdv data written by running build_enusc_enrichment.py (deviation: enrichment was not run in 23-02, only script was built)"
  - "household % display: (vhdv_rate * 100).toFixed(1) + %; no per-100k, no raw proportion"
metrics:
  duration: "~15 minutes"
  completed: "2026-06-19"
  tasks_completed: 3
  files_created: 0
  files_modified: 5
---

# Phase 23 Plan 03: ENUSC VHDV Frontend + Validators Summary

**One-liner:** Section 6c VHDV module renders household-victimization % with INE experimental/SAE caveat on 136 covered commune pages and a bilingual no-estimate note on 210 uncovered pages, validated by extended commune.mjs + forbidden-language.mjs both exiting 0.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add enusc_vhdv type + 6 bilingual i18n keys | e60f44f | site/src/lib/data.ts, site/src/config/i18n.ts |
| 2 | Add section 6c to EN+ES commune templates; enrich 136 commune JSONs | ee91f21 | [slug].astro (EN+ES), 136 commune JSONs |
| 3 | Extend commune.mjs; run all validators | ae531de | site/scripts/validate/commune.mjs |

## Verification

- `npm run build` — 791 pages built successfully
- Build count assertion: 272 covered pages (136 EN + 136 ES) with `enusc-vhdv-section`, 420 uncovered pages (210 EN + 210 ES) with `enusc-no-estimate`
- `node scripts/validate/commune.mjs` — 346 EN + 346 ES commune dirs, PASSED
- `node scripts/validate/forbidden-language.mjs` — 793 pages scanned, 0 forbidden terms
- `npx astro check` — exit code 0, no new type errors

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 136 commune JSONs were missing enusc_vhdv field at build time**
- **Found during:** Task 2 (build verification showed 0 covered pages)
- **Issue:** Plan 23-02 built `build_enusc_enrichment.py` but did not run it; commune JSONs had no `enusc_vhdv` key
- **Fix:** Ran `python pipeline/build_enusc_enrichment.py` which enriched 136 commune JSONs and committed them
- **Files modified:** 136 `data/cead/comunas/{cut}.json` files
- **Commit:** ee91f21

## Success Criteria Verification

- [x] VL-03: EN + ES covered pages show value (household %) + 2024 + bilingual experimental/SAE caveat; forbidden-language exits 0
- [x] VL-04: EN + ES uncovered pages show explicit bilingual "no estimate (coverage: 136 comunas)" note, no broken layout, no implied value

## Known Stubs

None — all 136 covered commune pages render real ENUSC 2024 VHDV data from enriched commune JSONs.

## Threat Flags

No new security-relevant surface introduced. All injected content is auto-escaped numeric values (toFixed output) plus constant i18n strings. T-23-07 and T-23-08 mitigations confirmed active (no set:html of cell values; forbidden-language validator passed).

## Self-Check: PASSED

- site/src/lib/data.ts — enusc_vhdv? field present
- site/src/config/i18n.ts — 6 ENUSC keys in interface + EN_STRINGS + ES_STRINGS
- site/src/pages/commune/[slug].astro — section 6c with enusc-vhdv-section / enusc-no-estimate
- site/src/pages/es/comuna/[slug].astro — section 6c (ES)
- site/scripts/validate/commune.mjs — ENUSC assertion added for EN and ES loops
- Commits: e60f44f, ee91f21, ae531de — all verified in git log
