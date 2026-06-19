---
phase: 11-publish-346-comunas-finder
plan: "03"
subsystem: directory-pages + nav
tags: [seo, directory, i18n, nav, vanilla-script, ssr]
dependency_graph:
  requires: [11-02]
  provides: [directory-en, directory-es, nav-communes-link, home-directory-link]
  affects:
    - site/src/config/i18n.ts
    - site/src/pages/communes/index.astro
    - site/src/pages/es/comunas/index.astro
    - site/src/components/PageHeader.astro
    - site/src/pages/index.astro
    - site/src/pages/es/index.astro
tech_stack:
  added: []
  patterns: [ssr-full-link-list, vanilla-inline-script, hardcoded-per-locale-href, accent-fold-filter, server-rendered-both-groupings]
key_files:
  created:
    - site/src/pages/communes/index.astro
    - site/src/pages/es/comunas/index.astro
  modified:
    - site/src/config/i18n.ts
    - site/src/components/PageHeader.astro
    - site/src/pages/index.astro
    - site/src/pages/es/index.astro
decisions:
  - "Both A-Z and by-region groupings are server-rendered in static HTML (not built by JS) — SEO-safe and no-JS-degradable; script only filters/highlights existing DOM nodes"
  - "communesHref hardcoded per locale in PageHeader (/communes/ | /es/comunas/) — getRelativeLocaleUrl does not translate ES slugs (Pitfall 3)"
  - "T-11-05 mitigated: highlight slices the trusted data-name attribute around match index, never injects raw query into innerHTML"
  - "No React island — vanilla inline script keeps Leaflet/React JS off the directory pages entirely"
metrics:
  duration: "~30m"
  completed: "2026-06-15"
  tasks: 3
  files: 6
---

# Phase 11 Plan 03: Comuna Directory Pages + Nav Link Summary

SSR directory pages /communes/ (EN) and /es/comunas/ (ES) serve all 346 comuna links in server-rendered A-Z and by-region groupings with a vanilla accent-insensitive filter/toggle script; linked from nav and both home pages.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add directory + nav i18n strings (EN + ES) | 71fc138 | site/src/config/i18n.ts |
| 2 | Create EN + ES directory pages (SSR full 346-link list + vanilla script) | 0b0377e | site/src/pages/communes/index.astro, site/src/pages/es/comunas/index.astro |
| 3 | Link directory from nav (PageHeader) and both home pages | 7d1abb7 | site/src/components/PageHeader.astro, site/src/pages/index.astro, site/src/pages/es/index.astro |

## What Was Built

### Task 1 — i18n strings
- `I18nStrings` interface extended with `nav_communes` + 8 `dir_*` keys
- `EN_STRINGS` and `ES_STRINGS` both provide every key (TypeScript parity enforced)
- `tsc --noEmit` passes with 0 errors on i18n.ts
- Sober editorial tone per D-05 (references "incidencia reportada", no "peligroso/seguro")

### Task 2 — Directory pages
Both `/communes/` and `/es/comunas/` pages:
- Frontmatter builds `rows` from `loadIndex()` (all 346) enriched with `latestCompleteYearRate(loadCommune(cut))`, `region = Math.floor(parseInt(cut,10)/1000)`, and `levelForRate(rate, allRates)`
- **A-Z block** (default visible): sorted alphabetically, grouped by first accent-folded letter, with A-Z jump index anchors
- **By-region block** (hidden by default): 16 sections ordered 1..16, using `loadRegion(String(n)).name` for headings
- Both blocks are in the `.astro` server template — crawlers and no-JS users see all 346 links
- Inline `<script>` (no island): accent-fold filter, A-Z ↔ region toggle, `<mark>` highlight (name-slice, T-11-05), live count display
- Hardcoded per-locale hrefs: EN `/commune/{slug}/`, ES `/es/comuna/{slug}/`
- Low-pop tag (`dir_lowpop_tag`) shown on `low_population` rows
- `BaseLayout` with `enPath="/communes/"` and `esPath="/es/comunas/"` for reciprocal hreflang
- `astro check` passes with 0 errors

### Task 3 — Nav + home links
- `PageHeader.astro`: `communesHref` hardcoded per locale; `{t.nav_communes}` link added after Map link (renders in desktop nav and mobile checkbox dropdown via same markup)
- EN home (`index.astro`): "Browse all 346 communes in the directory →" added to "Explore the Data" quick-links list
- ES home (`es/index.astro`): "Explora las 346 comunas en el directorio →" added to "Ciudades destacadas" list
- No `getRelativeLocaleUrl` used for directory links (Pitfall 3 avoided)
- No home H1/prose restructured (Phase 12 scope)

## Verification

- `tsc --noEmit`: 0 errors on i18n.ts (parity enforced by type system)
- `astro check`: 0 errors across 97 files (including the 2 new directory pages)
- `grep` assertions: `communesHref` + `nav_communes` in PageHeader; `/communes/` in EN home; `/es/comunas/` in ES home — all PASS
- Full dist assertion (≥346 hrefs in each directory HTML, sitemap includes directory URLs) delegated to Plan 04 coverage.mjs

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. Both directory pages use real `loadIndex()` data (346 comunas) and real `loadCommune()` rates. No hardcoded or placeholder data.

## Threat Flags

No new security-relevant surface beyond what is documented in the plan threat model:
- T-11-05 (Tampering/XSS): mitigated — `<mark>` highlight uses `name.slice()` on trusted `data-name` attribute, never `innerHTML = rawQuery`
- T-11-06 (directory exposure): accepted — intended public data

## Self-Check: PASSED

- site/src/config/i18n.ts: modified (71fc138) — nav_communes + dir_* keys in both locales
- site/src/pages/communes/index.astro: created (0b0377e) — 346 EN links server-rendered
- site/src/pages/es/comunas/index.astro: created (0b0377e) — 346 ES links server-rendered
- site/src/components/PageHeader.astro: modified (7d1abb7) — communesHref + nav_communes link
- site/src/pages/index.astro: modified (7d1abb7) — /communes/ link in quick-links
- site/src/pages/es/index.astro: modified (7d1abb7) — /es/comunas/ link in list
