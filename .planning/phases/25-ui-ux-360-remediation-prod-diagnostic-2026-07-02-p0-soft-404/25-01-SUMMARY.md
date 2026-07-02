---
phase: 25-ui-ux-360-remediation-prod-diagnostic-2026-07-02-p0-soft-404
plan: "01"
subsystem: frontend
tags: [seo, favicon, nav, breakpoints, 404]
dependency_graph:
  requires: []
  provides: [real-404-page, brand-favicon, tablet-nav-fix]
  affects: [site/src/layouts/BaseLayout.astro, site/src/components/PageHeader.astro, site/src/pages/index.astro]
tech_stack:
  added: []
  patterns: [png-in-ico-minimal-header, astro-404-static-page, css-flex-wrap-stacking]
key_files:
  created:
    - site/src/pages/404.astro
    - site/public/favicon.svg
    - site/public/favicon.ico
    - site/public/apple-touch-icon.png
    - site/scripts/gen-favicon.mjs
  modified:
    - site/src/layouts/BaseLayout.astro
    - site/src/components/PageHeader.astro
    - site/src/config/i18n.ts
    - site/src/pages/index.astro
decisions:
  - "ICO generated with already-installed sharp + pure-Node 22-byte ICO header (no new npm deps)"
  - "index.astro lead-tables-grid converted from CSS grid to flexbox with flex-wrap:wrap to enable 900px stacking rule"
  - "404 page uses BaseLayout directly (not EditorialLayout) — simpler, no extra layout dependency"
metrics:
  duration: "~8 minutes"
  completed: "2026-07-02"
  tasks: 3
  files: 9
---

# Phase 25 Plan 01: P0 Critical Fixes (soft-404, favicon, tablet breakpoint) Summary

Three P0 fixes from the 2026-07-02 production audit landed as independent atomic commits, each addressing a distinct critical flaw.

## One-liner

Real dist/404.html (kills soft-404 catch-all), brand pin-glyph favicon (svg+ico+apple-touch with #0f766e), nav hamburger raised to ≤1099px + home lead tables stacking at ≤900px.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Real 404 page (P0-1) | d1df2a3 | site/src/pages/404.astro |
| 2 | Favicon assets + head links (P0-3) | b144f99 | public/favicon.{svg,ico,png}, BaseLayout.astro |
| 3 | Tablet breakpoint fix (P0-2) | 8cad080 | PageHeader.astro, i18n.ts, index.astro |

## Verification Results

- `dist/404.html` exists; contains "Page not found" AND "Página no encontrada"; no noindex; CTA hrefs `/`, `/map/`, `/rankings/`, `/es/`, `/es/mapa/`, `/es/rankings/` present
- `dist/favicon.svg` contains `#0f766e`
- `dist/favicon.ico` first 4 bytes: `00 00 01 00` (valid ICO)
- `dist/apple-touch-icon.png` (180×180) exists
- `dist/index.html` has 2× `rel="icon"` + 1× `rel="apple-touch-icon"`
- `PageHeader.astro` has exactly 4× `min-width: 1100px`, 0× `min-width: 640px`
- `i18n.ts` glossary_link EN = `'Glossary'`, ES = `'Glosario'`
- `index.astro` has `flex-wrap: wrap` on `.lead-tables-grid` + `@media (max-width: 900px) { .lead-table-col { width: 100%; } }`
- `npm run build && npm run validate`: 834 pages built, 14/14 validators passed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Refactor] CSS grid → flexbox for lead-tables-grid**
- **Found during:** Task 3 analysis
- **Issue:** The existing `.lead-tables-grid` used `display: grid` with a 767px breakpoint, but the acceptance criteria required `flex-wrap: wrap` on the parent and `.lead-table-col { width: 100% }` at 900px — the grid approach would not satisfy the exact criteria.
- **Fix:** Converted `.lead-tables-grid` to `display: flex; flex-wrap: wrap` + added `flex: 1 1 400px; min-width: 0` on `.lead-table-col`. Added the 900px stacking rule as specified.
- **Files modified:** site/src/pages/index.astro
- **Commit:** 8cad080

## Known Stubs

None.

## Threat Flags

None. 404 page content is static literal copy (no user input rendered). No new network endpoints introduced.

## Self-Check: PASSED

- site/src/pages/404.astro — FOUND
- site/public/favicon.svg — FOUND
- site/public/favicon.ico — FOUND
- site/public/apple-touch-icon.png — FOUND
- site/src/layouts/BaseLayout.astro — modified (FOUND)
- Commits d1df2a3, b144f99, 8cad080 — FOUND in git log
- 14/14 validators PASSED
