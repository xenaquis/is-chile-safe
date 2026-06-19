---
phase: 15-crime-type-seo-ranking-pages
plan: "01"
subsystem: validators, lib
tags: [seo, familyDefs, methodology, crime-ranking]
dependency_graph:
  requires: []
  provides: [seo-validator-crime-ranking-samples, ranking-methodology-copy]
  affects: [site/scripts/validate/seo.mjs, site/src/lib/familyDefs.ts]
tech_stack:
  added: []
  patterns: [firstSubdir-guard-pattern, Record-string-string-export]
key_files:
  modified:
    - site/scripts/validate/seo.mjs
    - site/src/lib/familyDefs.ts
decisions:
  - RANKING_METHODOLOGY records use Option B (separate from FAMILY_DEFS) for richer methodology text
  - All methodology strings verified clean against forbidden-language.mjs before commit
metrics:
  duration: "12m"
  completed: "2026-06-16"
  tasks: 2
  files: 2
---

# Phase 15 Plan 01: Wave 0 Foundation — SEO Validator + Methodology Copy Summary

**One-liner:** SEO validator extended with guarded crime-ranking namespace samples; bilingual 8-key methodology records added to familyDefs.ts citing CEAD subgroup 101, denuncias framing, and full family aggregates.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | Extend seo.mjs SAMPLES with crime-ranking firstSubdir heuristic | 20f08ef | site/scripts/validate/seo.mjs |
| 2 | Add bilingual RANKING_METHODOLOGY entries to familyDefs.ts | 6e5bb1a | site/src/lib/familyDefs.ts |

## What Was Built

**Task 1 — seo.mjs:**
- Added `enCrimeRankingDir` + `esCrimeRankingDir` dir variables after existing crime dirs
- Added `firstCrimeRankingEn` + `firstCrimeRankingEs` firstSubdir calls
- Appended two guarded spread entries to SAMPLES for `/crime-ranking/<first> (EN)` and `/ranking-delito/<first> (ES)` — guarded so pre-Phase-15 builds skip, not fail

**Task 2 — familyDefs.ts:**
- Exported `RANKING_METHODOLOGY_EN` and `RANKING_METHODOLOGY_ES`, each keyed by 8 family keys: `homicidios, robos_violentos, drogas, propiedad, vif, armas, incivilidades, vida`
- Every entry: names the CEAD delitos in that family aggregate, states figures are denuncias not convictions, cites CEAD — Ministry of Interior and Public Security
- `homicidios` explicitly references CEAD subgroup 101 within the Life Crimes family
- `propiedad` and `incivilidades` describe the full family aggregate per CONTEXT decision (no sub-type-only relabeling)
- All strings clean: no forbidden-language terms ('safe', 'dangerous', 'peligros*', etc.)

## Verification

- Task 1 automated check: PASS (crime-ranking + ranking-delito literals present; firstCrimeRankingEn/Es appear >=4 times)
- Full build: 774 pages built in 21.4s — no errors
- Full validator suite: 12/12 validators PASS (including seo.mjs, forbidden-language, crime)
- No regression to existing pages

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — this plan is pure foundation/utility (no UI rendering).

## Threat Flags

None — no new network endpoints, auth paths, or trust boundaries introduced. T-15-01 (editorial-guard bypass) mitigated: all methodology strings verified against forbidden-language.mjs before commit.

## Self-Check: PASSED

- site/scripts/validate/seo.mjs: exists, modified
- site/src/lib/familyDefs.ts: exists, modified
- Commit 20f08ef exists: feat(15-01): extend seo.mjs SAMPLES
- Commit 6e5bb1a exists: feat(15-01): add RANKING_METHODOLOGY_EN/ES
