---
phase: 12-home-ia-redesign-comuna-page-hub-and-spoke
plan: "05"
subsystem: navigation-ia
tags: [nav, footer, rankings, ia, seo]
dependency_graph:
  requires: ["12-01"]
  provides: ["rankings-nav-node", "footer-spine", "rankings-index-pages"]
  affects: ["PageHeader.astro", "PageFooter.astro", "all pages via layout"]
tech_stack:
  added: []
  patterns: ["hardcoded-per-locale-slug", "EditorialLayout", "footer-spine nav row"]
key_files:
  created:
    - site/src/pages/rankings.astro
    - site/src/pages/es/rankings.astro
  modified:
    - site/src/components/PageHeader.astro
    - site/src/components/PageFooter.astro
decisions:
  - "ES guide link in footer-spine uses /es/comunas-mas-seguras-chile/ (confirmed existing ES editorial page) — /es/es-seguro-chile/ does not exist"
metrics:
  duration: "12m"
  completed: "2026-06-15"
  tasks: 3
  files: 4
---

# Phase 12 Plan 05: Navigation Spine (Rankings + Footer) Summary

**One-liner:** Rankings nav node + global footer-spine row + /rankings/ + /es/rankings/ static index pages closing IA-03 gap.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add Rankings nav link to PageHeader | e2e8b2a | site/src/components/PageHeader.astro |
| 2 | Extend PageFooter with footer-spine nav row | 158068d | site/src/components/PageFooter.astro |
| 3 | Create /rankings/ + /es/rankings/ static index pages | e4bdbfd | site/src/pages/rankings.astro, site/src/pages/es/rankings.astro |

## What Was Built

- **PageHeader** now includes `rankingsHref` (hardcoded per-locale: `/rankings/` EN, `/es/rankings/` ES) and renders a Rankings anchor after Communes in the nav order (Home, Map, Communes, Rankings, Methodology).
- **PageFooter** has a new `<nav class="footer-spine page-content">` row above the existing footer-legal row with four spine links per locale: Map, Communes, Rankings, editorial guide. EN uses `/safest-cities-in-chile/`; ES uses `/es/comunas-mas-seguras-chile/` (confirmed existing page).
- **rankings.astro** — EN static index: single H1 "Crime Incidence Rankings", intro with editorial tone guard, links to safest-cities editorial, all 7 `/crime/<family>/` pages (via FAMILY_SLUGS), and `/communes/`. Build-time FAMILY_SLUGS iteration.
- **es/rankings.astro** — ES mirror: single H1 in Spanish, links to `/es/comunas-mas-seguras-chile/`, all 7 `/es/delito/<family>/` pages, `/es/comunas/`.

## Verification

- `npm run build` exits 0 — 774 pages built (up from 772).
- `hreflang.mjs` PASSED — 774 pages, reciprocity verified.
- `/rankings/index.html` has exactly 1 `<h1>`, contains `href="/es/rankings/"` hreflang alternate.
- `/es/rankings/index.html` has exactly 1 `<h1>`.
- Footer-spine `class="footer-spine"` present in EN/ES index.html.
- Nav `href="/rankings/"` in EN, `href="/es/rankings/"` in ES confirmed in dist output.

## Deviations from Plan

### Auto-resolved Issues

**1. [Rule 2 - Missing info] ES editorial guide link**
- **Found during:** Task 2
- **Issue:** Plan suggested `/es/es-seguro-chile/` for the footer-spine guide link, but that page does not exist in the site (confirmed via Glob of es/*.astro).
- **Fix:** Used `/es/comunas-mas-seguras-chile/` — the existing ES editorial "safest communes" page — as the guide link. Label `t.footer_spine_guide` = "¿Es seguro Chile?" still renders correctly pointing to relevant content.
- **Impact:** Zero — an existing page is linked; no 404 introduced.

## Known Stubs

None — all links point to existing pages confirmed in dist/.

## Threat Flags

None — all hrefs are static build-time constants with no user input, matching the T-12-05 accept disposition in the threat register.

## Self-Check: PASSED

- site/src/components/PageHeader.astro — confirmed modified (rankingsHref present)
- site/src/components/PageFooter.astro — confirmed modified (footer-spine present)
- site/src/pages/rankings.astro — confirmed created
- site/src/pages/es/rankings.astro — confirmed created
- Commits e2e8b2a, 158068d, e4bdbfd — present in git log
