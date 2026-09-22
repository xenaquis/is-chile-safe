---
phase: 21-commune-comparator-a-vs-b-seo
plan: "01"
subsystem: comparator-foundation
tags: [comparator, prose-engine, i18n, build-validator, file-budget]
dependency_graph:
  requires: [phase-18]
  provides: [comparator-pairs-allowlist, comparison-prose-engine, avs-b-budget-validator, comparator-i18n-keys]
  affects: [phase-21-plan-02, phase-21-plan-03]
tech_stack:
  added: []
  patterns: [same-region-pair-generation, directional-prose-engine, file-budget-assertion]
key_files:
  created:
    - scripts/generate-pairs.mjs
    - data/comparator-pairs.json
    - site/src/lib/comparisonProse.ts
    - site/scripts/validate/avs-b-budget.mjs
  modified:
    - site/package.json
    - site/src/config/i18n.ts
decisions:
  - "All 5,031 same-region pairs used as the allowlist (vs. CONTEXT.md estimate of ~3,400) — fits budget (11,944 projected files vs. 18,000 limit); staged via enabled flag"
  - "meta description template uses national ranks embedded to guarantee 140+ chars even for short commune names"
  - "Region size for Block 5 prose read from index.json at SSG time via process.cwd()-anchored path, cached in module scope"
metrics:
  duration: "~25 minutes"
  completed: "2026-06-20"
  tasks_completed: 3
  files_created: 4
  files_modified: 2
---

# Phase 21 Plan 01: Pair Allowlist, Prose Engine, Budget Validator Summary

Wave 0 foundation for the A-vs-B comparator: 5,031-pair same-region allowlist with 20 pairs enabled for Wave-1 staged rollout, bilingual directional prose engine generating 400–500 non-swappable words per pair (EN 480, ES 571 verified), build-time file-budget validator asserting < 18,000 dist files, and 15 comparator i18n keys in both EN_STRINGS and ES_STRINGS.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Pair-allowlist generator + committed allowlist + build wiring | 6f6be97 | scripts/generate-pairs.mjs, data/comparator-pairs.json, site/package.json |
| 2 | buildComparisonProse() — 5-block directional non-swappable engine | d0823e4 | site/src/lib/comparisonProse.ts |
| 3 | avs-b-budget validator + 15 i18n keys | 05bee3e | site/scripts/validate/avs-b-budget.mjs, site/src/config/i18n.ts |

## Verification Results

- `node scripts/generate-pairs.mjs` exits 0; generates 5,031 pairs, 20 enabled, projected full build = 11,944 files (margin 6,056)
- `npx tsx` prose smoke test: EN=480 words, ES=571 words, non-swappable, no forbidden language, meta=147 chars — all pass
- `node site/scripts/validate/avs-b-budget.mjs` exits 0 (current dist has 1,214 files, margin 16,786)
- 15 i18n keys verified in both EN_STRINGS and ES_STRINGS

## Decisions Made

1. **5,031 same-region pairs as full allowlist** — RESEARCH.md computed this as the real universe; it fits the Cloudflare 18k limit with margin; CONTEXT.md "~3,400" was conservative. Staged rollout via `enabled` flag keeps initial deploy to 20 pairs.
2. **meta description template** — embeds both names, scores, and national ranks (#X and #Y of 346 communes) to guarantee 140+ chars even for short commune names like "Maipú".
3. **Region size lookup** — cached `_regionSizeCache` in comparisonProse.ts reads index.json via `process.cwd()`-anchored path at SSG time, mirroring data.ts DATA_ROOT pattern.

## Deviations from Plan

None — plan executed exactly as written. The only iteration was on the meta description template length (initial drafts fell below 140 chars for short commune names; added rank context to reach 147 chars).

## Known Stubs

None — this plan is foundation-only (generator, prose engine, validator, i18n keys). No UI surfaces or page routes are created in this plan; those are Plans 02 and 03.

## Threat Flags

None — all files operate on committed repo JSON at build time; no network, no user input, no new endpoints.

## Self-Check: PASSED

All created files exist. All commits verified:
- 6f6be97: scripts/generate-pairs.mjs, data/comparator-pairs.json, site/package.json
- d0823e4: site/src/lib/comparisonProse.ts
- 05bee3e: site/scripts/validate/avs-b-budget.mjs, site/src/config/i18n.ts
