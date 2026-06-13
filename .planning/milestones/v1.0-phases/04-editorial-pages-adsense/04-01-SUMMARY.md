---
phase: 04-editorial-pages-adsense
plan: "01"
subsystem: validation
tags: [validator, editorial-safety, forbidden-language, structure]
dependency_graph:
  requires: []
  provides: [forbidden-language-gate, phase4-structure-assertions]
  affects: [site/scripts/validate/]
tech_stack:
  added: []
  patterns: [hreflang.mjs scaffold pattern, NFD accent normalisation, lookahead/lookbehind word boundaries]
key_files:
  created:
    - site/scripts/validate/forbidden-language.mjs
  modified:
    - site/scripts/validate/all.mjs
    - site/scripts/validate/structure.mjs
decisions:
  - "Sentinel-gated Phase-4 block in structure.mjs: no-op until methodology/index.html exists, preventing false failures before editorial pages are built"
  - "ALLOW_LIST uses a ~100-char context window after each match (not full-page scan) to limit qualifying-phrase scope"
  - "FORBIDDEN_TERMS kept accent-free; NFD normalisation applied at match time to both text and terms (Pitfall 2)"
metrics:
  duration: "20m"
  completed: "2026-06-13"
  tasks: 3
  files: 3
---

# Phase 04 Plan 01: Forbidden-Language Gate + Structure Assertions Summary

Build-time EDIT-05 forbidden-language validator registered as #9 in the 9-validator suite; structure.mjs extended with sentinel-gated Phase-4 page-existence assertions.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | Create forbidden-language.mjs validator | 8f5c73f | site/scripts/validate/forbidden-language.mjs |
| 2 | Register forbidden-language.mjs as validator #9 | f6d1dd3 | site/scripts/validate/all.mjs |
| 3 | Extend structure.mjs with Phase-4 assertions | e7d0f5b | site/scripts/validate/structure.mjs |

## Verification

`npm run build && node scripts/validate/all.mjs` — **9/9 PASS** against existing Phase 2/3 dist/ (74 pages).

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes introduced. Validator reads only repo-authored dist/ HTML (trust boundary: build pipeline → dist/).

## Self-Check: PASSED

- `site/scripts/validate/forbidden-language.mjs` — FOUND
- `site/scripts/validate/all.mjs` contains `forbidden-language.mjs` — VERIFIED
- `site/scripts/validate/structure.mjs` contains `PHASE4_DIST_PAGES` — VERIFIED
- Commits 8f5c73f, f6d1dd3, e7d0f5b — all in git log
