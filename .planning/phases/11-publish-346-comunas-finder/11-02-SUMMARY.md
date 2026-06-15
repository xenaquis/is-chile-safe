---
phase: 11-publish-346-comunas-finder
plan: "02"
subsystem: build-pipeline + ranking-templates
tags: [rollout, cross-env, ranking-tables, un-gate, region, crime]
dependency_graph:
  requires: [11-01]
  provides: [rollout-346-build-default, un-gated-region-tables, un-gated-crime-tables]
  affects:
    - site/package.json
    - site/src/pages/region/[slug].astro
    - site/src/pages/es/region/[slug].astro
    - site/src/pages/crime/[family].astro
    - site/src/pages/es/delito/[family].astro
tech_stack:
  added: [cross-env@10.1.0]
  patterns: [env-var-via-cross-env, full-rankingRows-passthrough]
key_files:
  modified:
    - site/package.json
    - site/src/pages/region/[slug].astro
    - site/src/pages/es/region/[slug].astro
    - site/src/pages/crime/[family].astro
    - site/src/pages/es/delito/[family].astro
decisions:
  - "cross-env@10.1.0 used (not bare VAR=val) so build works on both Windows/PowerShell (dev) and Linux CI/Cloudflare identically"
  - "rollout.json enabled[] left vestigial — not expanded; ROLLOUT_ALL=true env var is the single flip mechanism"
  - "Dead .rollout-note CSS left in <style> blocks (harmless) — plan permits either removal or retention"
metrics:
  duration: "~15m"
  completed: "2026-06-15"
  tasks: 3
  files: 5
---

# Phase 11 Plan 02: Rollout Flip + Un-gate Ranking Tables Summary

ROLLOUT_ALL=true set as committed build default via cross-env; all four ranking templates (region EN/ES, crime EN/ES) now pass full rankingRows and emit no gating note — every comuna is linked from every ranking table.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Commit ROLLOUT_ALL=true as build default via cross-env | 228a6af | site/package.json, site/package-lock.json |
| 2 | Un-gate EN + ES region ranking tables | 4dddfb3 | site/src/pages/region/[slug].astro, site/src/pages/es/region/[slug].astro |
| 3 | Un-gate EN + ES crime-type ranking tables | 3a24bb8 | site/src/pages/crime/[family].astro, site/src/pages/es/delito/[family].astro |

## What Was Built

### Task 1 — ROLLOUT_ALL=true build default
- `cross-env@10.1.0` installed as devDependency (legitimacy pre-verified in threat register T-11-SC)
- `build` script changed from `astro build` to `cross-env ROLLOUT_ALL=true astro build`
- `prebuild` (sync-data.mjs) lifecycle preserved; `astro.config.mjs` and `rollout.json` untouched
- From now on, `npm run build` on any machine — Windows PowerShell or Linux CI — emits all 346 EN + 346 ES comuna pages

### Task 2 — Region ranking tables (EN + ES)
Both `region/[slug].astro` and `es/region/[slug].astro`:
- Deleted `rolloutCuts`/`displayedRows`/`hiddenCount` blocks (6 lines each)
- Removed `loadRolloutCuts` from data.ts import lists
- Changed `<CommuneRankingTable rows={displayedRows} …>` to `rows={rankingRows}`
- Deleted `{hiddenCount > 0 && (<p class="rollout-note">…</p>)}` JSX blocks
- Sort, JSON-LD, sparkline, StatCard sections untouched

### Task 3 — Crime-type ranking tables (EN + ES)
Both `crime/[family].astro` and `es/delito/[family].astro`:
- Deleted `rolloutCuts`/`displayedRows`/`hiddenCount` blocks (5 lines each)
- Removed `loadRolloutCuts` from data.ts import lists
- `<tbody>` now maps over `rankingRows` (all eligible + low-pop communes)
- Low-pop footnote guard changed from `displayedRows.some(...)` to `rankingRows.some(...)`
- Deleted rollout-note JSX blocks
- Region-breakdown bars, JSON-LD, hero sections untouched

## Verification

- `node -e` build-script assertion: PASSED (`cross-env ROLLOUT_ALL=true astro build` present; cross-env in devDeps)
- `npm ls cross-env` from site/: shows `cross-env@10.1.0`
- `grep -rn "displayedRows|hiddenCount|loadRolloutCuts" src/pages/region/ src/pages/es/region/`: returns nothing
- `grep -rn "displayedRows|hiddenCount|loadRolloutCuts" src/pages/crime/ src/pages/es/delito/`: returns nothing
- Full-build confirmation (346×2 pages, sitemap 770 locs) deferred to Plan 04 per plan spec

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All four templates now link all communes from rankingRows. The full-build confirmation in Plan 04 will verify the 346×2 output end-to-end.

## Threat Flags

No new security-relevant surface introduced. Changes are purely build-script and template un-gating over trusted repo data.

## Self-Check: PASSED

- site/package.json: modified (228a6af) — build script confirmed `cross-env ROLLOUT_ALL=true astro build`
- site/package-lock.json: updated (228a6af) — cross-env@10.1.0 locked
- site/src/pages/region/[slug].astro: modified (4dddfb3)
- site/src/pages/es/region/[slug].astro: modified (4dddfb3)
- site/src/pages/crime/[family].astro: modified (3a24bb8)
- site/src/pages/es/delito/[family].astro: modified (3a24bb8)
- All commit hashes verified in git log
