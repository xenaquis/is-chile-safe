---
phase: 11-publish-346-comunas-finder
plan: "04"
subsystem: validation
tags: [coverage-validator, full-build, phase-gate]
dependency_graph:
  requires: [11-01, 11-02, 11-03]
  provides: [phase-11-gate-pass]
  affects: [ci-pipeline, cloudflare-pages-deploy]
tech_stack:
  added: []
  patterns: [ROLLOUT_ALL propagation in validator suite]
key_files:
  modified:
    - site/scripts/validate/all.mjs
decisions:
  - "all.mjs propagates ROLLOUT_ALL=true to child validator processes — the committed build permanently uses this flag via cross-env, so validators must be aware of it to assert the correct row counts"
metrics:
  duration: "~25m"
  completed: "2026-06-15"
  tasks: 2 auto + 1 checkpoint (approved 2026-06-15)
  files: 1
---

# Phase 11 Plan 04: Wire Coverage Validator + Full Build Gate Summary

**One-liner:** Registered coverage.mjs in the 10-validator suite and ran the committed full ROLLOUT_ALL=true build; 10/10 validators green; build under 2 minutes; awaiting human reachability checkpoint.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Register coverage.mjs in validator suite | e64bf54 | site/scripts/validate/all.mjs |
| 2 | Full build + coverage isolated run + full suite | 75875fc | site/scripts/validate/all.mjs |

## Task 3 Status — APPROVED (2026-06-15)

**Human reachability checkpoint: PASSED.** Verified via BrowserOS against `astro dev` (ROLLOUT_ALL=true), both locales, then approved by human.

| # | Check | Result |
|---|-------|--------|
| 1 | Directory renders + count + regions | EN "346 of 346" / ES "346 de 346"; 346 unique links each; 16 region sections (sum = 346); A-Z + By-region toggle + search box |
| 2 | Search filter (accent-insensitive) | "vina" → only Viña del Mar; "nunoa" → only Ñuñoa |
| 3 | Small/remote comunas reachable | Camiña, Camarones, Río Verde, Lago Verde, Antártica — all 200 + real `<h1>` |
| 4 | No-JS full list | raw HTML (no JS) contains all 692 commune-link refs; no gating string |
| 5 | Map + region/crime, no gating note | /map/ + /es/mapa/ 200; region 52 rows; crime pages 346 rows; no "Showing N of M / Mostrando N de M" anywhere |

**Full dead-link sweep:** 346/346 EN comuna pages = 200, 346/346 ES comuna pages = 200 — **0 dead links**.

## Build Results (Task 2)

**Build wall-clock:** ~90 seconds (build started 16:55:39, last route ~16:56:15) — well under the 20-minute CI/Cloudflare budget.

**coverage.mjs isolated run (4 checks):**
- PASS [A] route-count: EN=346 ES=346 (both === 346)
- PASS [B] no-orphan-link: 0 dead commune links across 772 HTML files
- PASS [C] sitemap-coverage: 346 EN + 346 ES commune locs; directory URLs present
- PASS [D] directory-completeness: 346 distinct /commune/ hrefs in EN directory; 346 distinct /es/comuna/ hrefs in ES directory

**Full validator suite (10/10):**
- PASS structure
- PASS commune
- PASS rollout (346 by default, no EXPECT_ALL)
- PASS region
- PASS crime
- PASS hreflang
- PASS schema
- PASS map
- PASS forbidden-language
- PASS coverage

**Dist contents verified:**
- dist/commune/: 346 directories
- dist/es/comuna/: 346 directories
- dist/communes/index.html: exists (EN directory page, 276 KB)
- dist/es/comunas/index.html: exists (ES directory page, 278 KB)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] region.mjs validator env mismatch — ROLLOUT_ALL not propagated**
- **Found during:** Task 2 (first all.mjs run: 9/10 FAIL on region)
- **Issue:** `all.mjs` spawned child validators with `{ ...process.env }` only. `region.mjs` checks `process.env.ROLLOUT_ALL === 'true'` to determine expected row count. Without it, it expected 4 rollout communes in Metropolitana but the build (ROLLOUT_ALL=true via cross-env) emitted 52. The validator correctly tests what the build emits — the bug was in the spawn env.
- **Fix:** Added `ROLLOUT_ALL: 'true'` to the env passed to child processes in all.mjs. This is not EXPECT_ALL (which the plan prohibits) — it's the build-time flag permanently baked into `npm run build`.
- **Files modified:** site/scripts/validate/all.mjs
- **Commit:** 75875fc

## Known Stubs

None — all data is wired from real CEAD index.json.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes introduced.

## Self-Check

- [x] site/scripts/validate/all.mjs modified (contains 'coverage.mjs' in VALIDATORS array)
- [x] Commit e64bf54 exists (Task 1 — register coverage.mjs)
- [x] Commit 75875fc exists (Task 2 — fix + full suite green)
- [x] 10/10 validators passed
- [x] Build under 20-minute budget (~90 seconds)

## Self-Check: PASSED
