---
phase: 02-astro-site-programmatic-pages
plan: "02"
subsystem: component-library
tags: [astro, components, hreflang, seo, svg, css, i18n]
dependency_graph:
  requires:
    - "02-01 (data.ts, colorScale.ts, i18n.ts, slugMaps.ts)"
  provides:
    - "site/src/styles/global.css — locked CSS custom property token set"
    - "site/src/layouts/BaseLayout.astro — hreflang/canonical/PWA meta shell"
    - "site/src/components/PageHeader.astro — static nav + lang toggle"
    - "site/src/components/PageFooter.astro — CEAD attribution footer"
    - "site/src/components/Sparkline.astro — inline SVG bar sparkline"
    - "site/src/components/FamilyBreakdownBars.astro — CSS percentage bar chart"
    - "site/src/components/LevelChip.astro — incidence level color dot + label"
    - "site/src/components/TrendChip.astro — trend arrow chip"
    - "site/src/components/StatCard.astro — 28px/700 stat display card"
    - "site/src/components/ComparisonCallout.astro — vs-national/regional pill"
    - "site/src/components/ComparableCommune.astro — nearest comparable commune card"
    - "site/src/components/MapPlaceholderSlot.astro — Phase 3 Leaflet mount point"
    - "site/src/components/MethodologyCaveat.astro — CEAD attribution grey box"
    - "site/src/components/CommuneRankingTable.astro — server-rendered HTML table"
    - "site/public/manifest.json — PWA manifest"
  affects:
    - "02-03..02-06 — all page plans import these components"
tech_stack:
  added: []
  patterns:
    - "hreflang en/es/x-default + self-canonical injected from enPath/esPath props in BaseLayout"
    - "JSON-LD via set:html={JSON.stringify(jsonLd)} + is:inline to prevent XSS (T-02-04)"
    - "CSS percentage string widths for FamilyBreakdownBars (Math.round(val/max*100)+'%')"
    - "Sparkline partial-year bars at opacity 0.5; active-year bar fill var(--primary)"
    - "TrendChip branches on STRING 'up'/'down'/'stable' (not numeric -1/0/1)"
    - "MapPlaceholderSlot outer div data-phase3-mount + role=img as Phase 3 contract"
key_files:
  created:
    - "site/src/styles/global.css"
    - "site/src/layouts/BaseLayout.astro"
    - "site/src/components/PageHeader.astro"
    - "site/src/components/PageFooter.astro"
    - "site/src/components/Sparkline.astro"
    - "site/src/components/FamilyBreakdownBars.astro"
    - "site/src/components/LevelChip.astro"
    - "site/src/components/TrendChip.astro"
    - "site/src/components/StatCard.astro"
    - "site/src/components/ComparisonCallout.astro"
    - "site/src/components/ComparableCommune.astro"
    - "site/src/components/MapPlaceholderSlot.astro"
    - "site/src/components/MethodologyCaveat.astro"
    - "site/src/components/CommuneRankingTable.astro"
    - "site/public/manifest.json"
  modified: []
decisions:
  - "JSON-LD uses is:inline directive to silence Astro hint about script processing while keeping set:html={JSON.stringify()} XSS-safe pattern"
  - "FamilyBreakdownBars removes EN_STRINGS/ES_STRINGS import (labels are inline FAMILY_LABELS map) — avoids unused import ts(6192)"
  - "MapPlaceholderSlot uses CSS custom properties --mobile-h/--desktop-h on the outer div for variant-specific min-heights without extra wrapper elements"
metrics:
  duration: "~25min"
  completed: "2026-06-13"
  tasks_completed: 3
  files_created: 15
---

# Phase 02 Plan 02: Component Library Summary

Server-rendered .astro component library for Chile Safety Map: global CSS token set, BaseLayout with reciprocal hreflang/canonical/PWA meta, 4 structural components (PageHeader, PageFooter, MapPlaceholderSlot, MethodologyCaveat), 5 data-viz components (Sparkline SVG, FamilyBreakdownBars, LevelChip, TrendChip, StatCard), and 3 composite components (ComparisonCallout, ComparableCommune, CommuneRankingTable) — all server-rendered, zero client:* directives.

## Outcome

All 3 tasks complete, all acceptance criteria verified:
- `npx astro check` exits 0 (0 errors, 0 warnings, 0 hints) after all tasks
- `node scripts/validate/structure.mjs` exits 0 (stub, passes smoke check)
- global.css contains --primary, --bg, --s1, --s5, --radius, Nunito Sans @import
- BaseLayout.astro contains hreflang (3 occurrences: en/es/x-default), canonical, theme-color, application/ld+json
- BaseLayout.astro uses JSON.stringify for JSON-LD (T-02-04 mitigated)
- PageHeader.astro uses getRelativeLocaleUrl and contains no client: directive
- Sparkline.astro emits SVG with rect elements; partial bars at opacity 0.5
- FamilyBreakdownBars.astro: CSS percentage widths ('+%'' string); vida/propiedad ordered first with accent dots
- TrendChip.astro branches on strings 'up'/'down'/'stable' (not numeric)
- LevelChip.astro references var(--s in dot styling
- MapPlaceholderSlot.astro: data-phase3-mount + role="img" + 320px/480px CSS variables
- ComparableCommune.astro: fallback flag selects heading; <a href> to commune page (no onClick)
- CommuneRankingTable.astro: server-side <table>; low_population rows marked with *
- MethodologyCaveat.astro: links to /methodology/ and /es/metodologia/

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | ae8c348 | global.css tokens + BaseLayout hreflang/canonical + PageHeader/PageFooter |
| Task 2 | b4d0147 | data-viz components (Sparkline, FamilyBreakdownBars, LevelChip, TrendChip, StatCard) |
| Task 3 | 0e10c3d | composite components (callouts, comparable, map slot, methodology, ranking table) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Unused import in PageFooter.astro**

- **Found during:** Task 1 astro check run
- **Issue:** EN_STRINGS/ES_STRINGS imported but not used — all copy derived at runtime
- **Fix:** Removed unused import to achieve 0 hints
- **Files modified:** site/src/components/PageFooter.astro

**2. [Rule 1 - Bug] Unused variable `currentPath` in BaseLayout.astro**

- **Found during:** Task 1 astro check run
- **Issue:** `currentPath` computed but unused (lang toggle handled via props directly)
- **Fix:** Removed the variable

**3. [Rule 2 - Missing Critical Functionality] JSON-LD script needs is:inline directive**

- **Found during:** Task 1 astro check hint
- **Issue:** `<script type="application/ld+json" set:html={...}>` triggers Astro hint about inline scripts with attributes
- **Fix:** Added `is:inline` directive — required for correct behavior; doesn't change XSS-safety of JSON.stringify pattern (T-02-04 still mitigated)
- **Files modified:** site/src/layouts/BaseLayout.astro

**4. [Rule 1 - Bug] Unused import EN_STRINGS/ES_STRINGS in FamilyBreakdownBars.astro**

- **Found during:** Task 2 astro check run
- **Issue:** Family labels are self-contained in FAMILY_LABELS map inside the component; the i18n import was redundant
- **Fix:** Removed unused import

## Known Stubs

None — all components render from props passed at build time. No hardcoded placeholder data. Methodology page links (/methodology/ and /es/metodologia/) will 404 until Phase 4; this is documented as acceptable per phase boundary.

## Threat Flags

No new security-relevant surface introduced. T-02-04 (JSON-LD injection) mitigated via JSON.stringify + is:inline. T-02-05 (XSS commune names) covered by Astro's default expression escaping; no set:html used on raw data.

## Self-Check

- site/src/styles/global.css: FOUND
- site/src/layouts/BaseLayout.astro: FOUND
- site/src/components/PageHeader.astro: FOUND
- site/src/components/PageFooter.astro: FOUND
- site/src/components/Sparkline.astro: FOUND
- site/src/components/FamilyBreakdownBars.astro: FOUND
- site/src/components/LevelChip.astro: FOUND
- site/src/components/TrendChip.astro: FOUND
- site/src/components/StatCard.astro: FOUND
- site/src/components/ComparisonCallout.astro: FOUND
- site/src/components/ComparableCommune.astro: FOUND
- site/src/components/MapPlaceholderSlot.astro: FOUND
- site/src/components/MethodologyCaveat.astro: FOUND
- site/src/components/CommuneRankingTable.astro: FOUND
- site/public/manifest.json: FOUND
- Commits ae8c348, b4d0147, 0e10c3d: FOUND

## Self-Check: PASSED
