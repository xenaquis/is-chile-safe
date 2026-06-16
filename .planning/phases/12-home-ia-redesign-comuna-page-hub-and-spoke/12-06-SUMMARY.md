---
phase: 12-home-ia-redesign-comuna-page-hub-and-spoke
plan: "06"
subsystem: validator
tags: [validation, spine, ia, cross-links, rankings]
dependency_graph:
  requires: ["12-03", "12-04", "12-05"]
  provides: ["IA-01", "IA-02", "IA-03"]
  affects: ["site/scripts/validate/spine.mjs", "site/scripts/validate/all.mjs"]
tech_stack:
  added: []
  patterns: ["coverage.mjs ESM validator pattern (collectHtmlFiles, failures counter, process.exit)"]
key_files:
  created:
    - site/scripts/validate/spine.mjs
  modified:
    - site/scripts/validate/all.mjs
decisions:
  - "spine.mjs mirrors coverage.mjs structure exactly (imports, SITE_ROOT/DIST_DIR, collectHtmlFiles, failures counter, exit pattern)"
  - "JSDoc block comment used {slug} instead of * glob to avoid */ early-close syntax error in Node.js ESM parser"
  - "Assertion I and J scan all commune dirs; offender list capped at 5 for readability"
  - "Assertion L samples home + map + one commune per locale (not all 346) — sufficient coverage for nav presence"
metrics:
  duration: "12m"
  completed: "2026-06-16"
  tasks_completed: 2
  tasks_total: 3
  files_changed: 2
---

# Phase 12 Plan 06: Spine Validator + Full Gate Summary

**One-liner:** spine.mjs validator enforcing IA-01/02/03 cross-link reciprocity (assertions F-L) registered in all.mjs; 11/11 validators green against 774-page ROLLOUT_ALL build.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create spine.mjs with IA-01/02/03 assertions | 96e3bba | site/scripts/validate/spine.mjs |
| 2 | Register spine.mjs in validator suite + run full gate | 9273a81 | site/scripts/validate/all.mjs |

## Assertions Implemented

| ID | Name | What It Checks |
|----|------|----------------|
| F | map-spoke targets exist | dist/map/index.html + dist/es/mapa/index.html present |
| G | rankings pages exist | dist/rankings/index.html + dist/es/rankings/index.html present |
| H | rankings in sitemap | sitemap-0.xml contains /rankings/ and /es/rankings/ <loc> entries |
| I | breadcrumb reciprocity | Every EN commune page has href="/communes/"; every ES page has href="/es/comunas/" |
| J | map-spoke on ficha | Every EN commune page contains /map/?cut=; ES contains /es/mapa/?cut= |
| K | home single H1 | dist/index.html and dist/es/index.html each have exactly 1 <h1> occurrence |
| L | rankings nav site-wide | Sampled pages (home, map, one commune) contain the rankings nav href |

## Full Suite Result

```
11/11 validators passed
PASS  structure
PASS  commune
PASS  rollout
PASS  region
PASS  crime
PASS  hreflang
PASS  schema
PASS  map
PASS  forbidden-language
PASS  coverage
PASS  spine
```

Build: 774 pages in ~33s under ROLLOUT_ALL=true.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] JSDoc block comment `*/` early-close syntax error**
- **Found during:** Task 1 verification (spine.mjs first run)
- **Issue:** The JSDoc comment used `commune/*/index.html` which caused Node.js ESM parser to treat `*/` as end-of-block-comment, turning the rest of the comment into code (SyntaxError: Unexpected identifier 'contains')
- **Fix:** Replaced `*/` glob notation in JSDoc with `{slug}` placeholder in the comment text
- **Files modified:** site/scripts/validate/spine.mjs (JSDoc lines only)
- **Commit:** 96e3bba (fixed inline before commit; no separate fix commit needed)

## Awaiting

**Task 3: Human smoke check** — checkpoint:human-verify (surfaced separately below).

## Known Stubs

None. spine.mjs reads real dist/ HTML artifacts and exits with pass/fail.

## Threat Flags

None. spine.mjs reads only local build-produced dist/ files; no network access, no user input.

## Self-Check: PASSED

- site/scripts/validate/spine.mjs: EXISTS
- site/scripts/validate/all.mjs: MODIFIED (spine.mjs in VALIDATORS array)
- Commit 96e3bba: EXISTS
- Commit 9273a81: EXISTS
- Full suite: 11/11 PASS
