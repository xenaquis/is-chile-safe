---
phase: 12-home-ia-redesign-comuna-page-hub-and-spoke
plan: "03"
subsystem: frontend/home
tags: [home, layout, i18n, ranking, search, static]
dependency_graph:
  requires: ["12-01"]
  provides: ["HomeLayout", "EN-home-hybrid-C+B", "ES-home-hybrid-C+B"]
  affects: ["site/src/layouts/HomeLayout.astro", "site/src/pages/index.astro", "site/src/pages/es/index.astro"]
tech_stack:
  added: []
  patterns: ["HomeLayout wraps BaseLayout full-width", "build-time ranking sort", "static GET search hero form"]
key_files:
  created:
    - site/src/layouts/HomeLayout.astro
  modified:
    - site/src/pages/index.astro
    - site/src/pages/es/index.astro
decisions:
  - "Used HomeLayout (new) instead of EditorialLayout to remove 720px constraint on home hub page"
  - "Excluded /es/es-seguro-chile/ guide card — page not found in dist; used only confirmed existing ES pages"
  - "Lead tables use 6 rows each (lowest+highest non-low-population communes) sorted at build time"
metrics:
  duration_minutes: 15
  completed_date: "2026-06-15"
  tasks_completed: 3
  tasks_total: 3
  files_changed: 3
---

# Phase 12 Plan 03: Home Hybrid C+B Redesign Summary

## One-liner

New HomeLayout (full-width BaseLayout wrapper) + EN/ES homes rebuilt on Hybrid C+B framing: search hero GET form, two build-time lead ranking tables (lowest/highest 6 communes), map CTA, and guide cards above the fold; condensed 2-paragraph CEAD prose below fold.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create HomeLayout.astro (wide full-bleed wrapper) | 1ed0cd3 | site/src/layouts/HomeLayout.astro |
| 2 | Rebuild EN home (index.astro) on Hybrid C+B | f132690 | site/src/pages/index.astro |
| 3 | Rebuild ES home (es/index.astro) at parity | af53bbe | site/src/pages/es/index.astro |

## Verification Results

- `npm run build` exits 0 — 772 pages built
- `node scripts/validate/structure.mjs` PASSED
- `node scripts/validate/hreflang.mjs` PASSED — 772 pages, all reciprocal alternates intact
- `dist/index.html`: 1 H1, action="/communes/", href="/map/", commune-ranking-table present, no astro-island
- `dist/es/index.html`: 1 H1, action="/es/comunas/", href="/es/mapa/", commune-ranking-table present, no astro-island

## Decisions Made

1. **HomeLayout width approach**: Used `width: 100%; padding: 0 var(--lg)` with no max-width on `.home-wide`. Inner sections control their own max-width (780px hero, 1100px tables grid, 680px map CTA) — this gives the hub page a full-bleed feel while keeping content readable.

2. **ES guide cards**: `/es/es-seguro-chile/` is NOT in dist (confirmed via `ls dist/es/`). Used only confirmed existing ES pages: `/es/mapa-delito-chile/`, `/es/mapa-seguridad-santiago/`, `/es/comunas-mas-seguras-chile/`, `/es/metodologia/`, `/es/delitos-por-comuna/`, `/es/comunas/`.

3. **Lead table row count**: 6 rows each (plan said "top-N" without specifying N). 6 rows fits well in the two-column grid layout and matches typical above-fold patterns.

## Deviations from Plan

None — plan executed exactly as written. The only practical deviation was excluding the unconfirmed ES slug `/es/es-seguro-chile/` from guide cards (Rule 2 — correctness: linking to a 404 would be a broken link).

**Deviation tracked:** `[Rule 2 - Missing critical functionality] Excluded /es/es-seguro-chile/ guide card — page does not exist in dist; replaced with /es/delitos-por-comuna/ which is confirmed present.`

## Known Stubs

None. Both home pages source real data from `loadIndex()` + `loadCommune()` + `latestCompleteYearRate()` at build time. No hardcoded empty arrays or placeholder values.

## Threat Surface Scan

No new network endpoints, auth paths, or trust boundary changes introduced. The search hero form GET-submits to `/communes/` (EN) and `/es/comunas/` (ES) which already existed and handle `?q=` safely (see T-12-01). No new threat surface vs. the plan's threat model.

## Self-Check: PASSED

- `site/src/layouts/HomeLayout.astro` exists: FOUND
- `site/src/pages/index.astro` modified: FOUND
- `site/src/pages/es/index.astro` modified: FOUND
- Commit 1ed0cd3 exists: FOUND
- Commit f132690 exists: FOUND
- Commit af53bbe exists: FOUND
