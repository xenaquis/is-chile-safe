---
phase: 21-commune-comparator-a-vs-b-seo
plan: "03"
subsystem: comparator-pages
tags: [comparator, a-vs-b, seo, static-pages, hreflang, spine-validator]
dependency_graph:
  requires: [phase-21-plan-01]
  provides: [avs-b-en-pages, avs-b-es-pages, comparator-pairs-links, spine-assertion-m, hreflang-compare-symmetry]
  affects: [cloudflare-deploy, seo-comparator-traffic]
tech_stack:
  added: []
  patterns: [programmatic-static-pages, thin-content-gate, same-region-pair-links, spine-validator-extension]
key_files:
  created:
    - site/src/pages/compare/[pair].astro
    - site/src/pages/es/comparar/[pair].astro
    - site/src/components/ComparatorPairsLinks.astro
  modified:
    - site/src/pages/commune/[slug].astro
    - site/src/pages/es/comuna/[slug].astro
    - site/scripts/validate/hreflang.mjs
    - site/scripts/validate/spine.mjs
decisions:
  - "Low-population fallback: when a commune has no non-low-pop same-region neighbors (e.g. Arica in region 15), fall back to all same-region communes to guarantee spine assertion M passes on all 346 pages"
  - "Compare links use sorted CUT slug regardless of enabled status — spine validator checks href prefix only, not live page existence (broken-link tolerance per plan)"
  - "No jsonLd prop on A-vs-B BaseLayout — JSON-LD deferred out of Phase 21 per 21-RESEARCH.md Q3"
metrics:
  duration: "~35 minutes"
  completed: "2026-06-20"
  tasks_completed: 3
  files_created: 3
  files_modified: 4
---

# Phase 21 Plan 03: A-vs-B Programmatic Pages, Cross-Link Injection, Validator Extension Summary

20 enabled bilingual A-vs-B comparison pages at /compare/{cutA}-vs-{cutB}/ and /es/comparar/{cutA}-vs-{cutB}/, with CMP-04 thin-content gate (≥300 words verified at 885 words sample), reciprocal hreflang, all 346 commune pages injected with 3–5 same-region pair links, and extended validators (hreflang EN/ES symmetry + spine assertion M).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | EN + ES A-vs-B page templates with thin-content gate | 7a717d3 | site/src/pages/compare/[pair].astro, site/src/pages/es/comparar/[pair].astro |
| 2 | ComparatorPairsLinks snippet + commune-page injection (EN+ES) | bd9cc25 | site/src/components/ComparatorPairsLinks.astro, commune/[slug].astro, es/comuna/[slug].astro |
| 3 | Extend hreflang.mjs (compare symmetry) + spine.mjs (assertion M) | a61c143 | site/scripts/validate/hreflang.mjs, site/scripts/validate/spine.mjs |

## Verification Results

- `npm run build` succeeds — 831 pages built (20 EN + 20 ES A-vs-B pairs + 346×2 commune pages)
- EN pair count: 20, ES pair count: 20 — symmetric
- Sample A-vs-B page word count: 885 words (well above 300-word CMP-04 floor)
- All 346 EN commune pages contain `href="/compare/"` — 0 missing
- All 346 ES commune pages contain `href="/es/comparar/"` — 0 missing
- `node scripts/validate/hreflang.mjs` exits 0 with PASS including compare symmetry
- `node scripts/validate/spine.mjs` exits 0 with PASS [M] comparator-spoke on all commune pages

## Decisions Made

1. **Low-population fallback for isolated communes** — Arica (region 15, Arica y Parinacota) is the only non-low-population commune in its region. The candidate filter fell back from `!low_population` to all same-region communes to guarantee at least one `/compare/` link renders on every commune page. This is a correctness fix (Rule 1 auto-fix) rather than an architectural change.

2. **Pair links use canonical sorted-CUT slugs regardless of enabled status** — the spine assertion checks for `href="/compare/"` prefix presence, not whether the linked page actually exists in dist/. This is per the plan's "broken-link tolerance for not-yet-enabled pairs during staged rollout" constraint.

3. **No jsonLd prop on A-vs-B pages** — explicitly omitted. BaseLayout's `jsonLd` prop is optional. A-vs-B Schema.org JSON-LD is deferred out of Phase 21 per 21-RESEARCH.md Q3 and 21-CONTEXT.md.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Arica commune missing comparator link due to all-low-population region**
- **Found during:** Task 2 verify (1 EN + 1 ES commune page missing href="/compare/")
- **Issue:** `nearestComparables`-style filter excluded all low_population communes; Arica is the only non-low-pop commune in region 15 — filter returned empty, rendering no links
- **Fix:** Added fallback: when non-low-pop same-region candidates are empty, use all same-region communes (including low_population) to ensure at least one link renders
- **Files modified:** commune/[slug].astro, es/comuna/[slug].astro
- **Not a separate commit** — fixed before Task 2 commit

## Known Stubs

None — all 20 enabled A-vs-B pages render real data from CEAD commune JSON and the composite index. The per-family table shows "—" for the Chile avg. column because national per-family averages require an extra data call not in scope for this plan; this is documented in the template as intentional (only the aggregate national average is loaded via `loadNationalAverage()`).

## Threat Flags

None — all files operate on committed repo JSON at build time; no new network endpoints, no user input, no new auth paths. CUT slugs are numeric strings (auto-escaped by Astro). See threat model in 21-03-PLAN.md for T-21-07/08/09/SC coverage.

## Self-Check: PASSED

All created files exist:
- site/src/pages/compare/[pair].astro — FOUND
- site/src/pages/es/comparar/[pair].astro — FOUND
- site/src/components/ComparatorPairsLinks.astro — FOUND

All commits verified:
- 7a717d3: feat(21-03): EN+ES A-vs-B page templates with CMP-04 thin-content gate
- bd9cc25: feat(21-03): ComparatorPairsLinks snippet + commune-page injection (EN+ES)
- a61c143: feat(21-03): extend hreflang.mjs (compare symmetry) + spine.mjs (assertion M)
