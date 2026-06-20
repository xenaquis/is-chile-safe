---
phase: 21-commune-comparator-a-vs-b-seo
plan: "04"
subsystem: validation
tags: [validation, comparator, seo, budget, rollout]
dependency_graph:
  requires: ["21-01", "21-02", "21-03"]
  provides: ["full-suite-green", "14-validator-suite", "prose-acceptance-sample"]
  affects: ["site/scripts/validate/all.mjs"]
tech_stack:
  added: []
  patterns: ["aggregate-validator-suite"]
key_files:
  modified:
    - site/scripts/validate/all.mjs
  created:
    - .planning/phases/21-commune-comparator-a-vs-b-seo/21-04-SUMMARY.md
key_decisions:
  - "avs-b-budget.mjs registered as validator #14 in all.mjs; 14/14 green confirmed on chained build+validate"
  - "GSC URL Inspection deferred to human operator — requires Google Search Console access"
metrics:
  duration: "12m"
  completed: "2026-06-20"
  tasks_completed: 1
  tasks_deferred_human: 2
  files_modified: 1
---

# Phase 21 Plan 04: Validator Suite Closure + Rollout Gate Summary

avs-b-budget.mjs registered as validator #14 in the aggregate suite; 14/14 validators green on the full comparator + A-vs-B build (1258 dist files, 18,000-file budget clear).

## Tasks Completed

### Task 1: Register avs-b-budget in the aggregate validator + full-suite green

- Added `avs-b-budget.mjs` to VALIDATORS array in `site/scripts/validate/all.mjs` after `figure-registry.mjs`
- Added header doc comment entry: `14. avs-b-budget.mjs — file budget < 18,000 + EN/ES compare-page count symmetry (Phase 21 CMP-05)`
- Ran full chained `npm run build && npm run validate` (OneDrive desync guard honored)
- Result: **14/14 validators passed**, dist 1258 files (limit 18000, margin 16742), 20 EN pairs === 20 ES pairs

**Commit:** 15113ac — `chore(21-04): register avs-b-budget in aggregate validator suite (14/14 green)`

### Prose Acceptance Sample (Programmatic — CMP-07 automated portion)

Programmatic acceptance check run over 10 A-vs-B pairs (all 20 enabled pairs sampled at 50% = 10 pairs). Verified:
- All 5 uniqueness blocks present: `index-diff-block`, `family-table-section`, `trend-section`, `national-rank-section`, `regional-section`
- Commune cross-links resolve (`/commune/` in EN, `/es/comuna/` in ES)
- CEAD attribution present in both locales
- hreflang alternate tags present in both locales
- EN and ES titles are distinct (no cross-locale leakage)
- No editorial "safe/dangerous" verdict in pair prose (forbidden-language validator confirmed 14/14 PASS)

Result: **10/10 pairs PASS** all programmatic checks.

## Deferred Human Verification Items

### Checkpoint: Prose Quality Acceptance (CMP-07 visual portion)

**Deferred to:** Human operator
**What:** Visual read of ≥10 enabled A-vs-B pairs (EN+ES) in browser to confirm:
- Prose reads naturally and is SUBSTANTIVELY DIFFERENT per pair
- Directional score deltas, rank positions, trend directions, dominant-family divergence are visible
- No template feel (not just swapped commune names)

**Steps for operator:**
1. `cd site && npm run build` then `npx astro preview --port 4321 --host`
2. List enabled pairs: all 20 have CUT prefix `10101-vs-10{102..210}` (Los Lagos region)
3. Open `http://localhost:4321/compare/10101-vs-10102/` and `/es/comparar/10101-vs-10102/` etc.
4. Signal: type "approved" (≥10 pairs read well, EN+ES) or list pairs needing prose fixes

### Checkpoint: GSC URL Inspection (CMP-07 rollout gate — Google Search Console)

**Deferred to:** Human operator (requires Google Search Console access)
**What:** After deploy of the ~20-pair batch via master push → Cloudflare deploy hook:
1. Open Google Search Console for ischilesafe.com
2. Run URL Inspection on at least 3 A-vs-B pages (1 EN, 1 ES, 1 cross-region if any) and 2 commune pages with compare cross-links
3. Confirm each is "URL is on Google" or "URL can be indexed" (no thin-content exclusion signals)
4. Only after confirmation expand: flip more pairs to `enabled:true` in `data/comparator-pairs.json`

**URLs to inspect (sample):**
- EN: `https://ischilesafe.com/compare/10101-vs-10102/`
- ES: `https://ischilesafe.com/es/comparar/10101-vs-10103/`
- Commune: `https://ischilesafe.com/commune/puerto-montt/` (has new compare cross-links)

## Deviations from Plan

None — plan executed exactly as written. Automated tasks completed; checkpoint tasks documented as deferred human actions per plan's `autonomous: false` instruction.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. This plan only modifies `all.mjs` (dev tooling). No threat flags.

## Self-Check

- [x] `site/scripts/validate/all.mjs` exists and contains `avs-b-budget.mjs`
- [x] Commit 15113ac confirmed in git log
- [x] 14/14 validators passed (confirmed in build output)
- [x] dist 1258 files < 18,000 limit (PASS)
- [x] 10/10 sampled pairs passed programmatic acceptance checks

## Self-Check: PASSED
