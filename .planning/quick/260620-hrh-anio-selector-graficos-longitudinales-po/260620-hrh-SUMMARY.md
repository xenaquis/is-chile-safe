---
phase: quick-260620-hrh
plan: 01
subsystem: commune-pages
tags: [year-selector, longitudinal-charts, svg, vanilla-js, i18n, seo]
dependency_graph:
  requires: []
  provides: [year-selector-commune, crime-family-charts, FAMILY_LABELS_PAGE]
  affects: [commune-EN, commune-ES, FamilyBreakdownBars, Sparkline, familyDefs]
tech_stack:
  added: [CrimeFamilyCharts.astro]
  patterns: [vanilla-js-json-island, static-svg-charts, progressive-enhancement]
key_files:
  created:
    - site/src/components/CrimeFamilyCharts.astro
  modified:
    - site/src/lib/familyDefs.ts
    - site/src/components/FamilyBreakdownBars.astro
    - site/src/components/Sparkline.astro
    - site/src/config/i18n.ts
    - site/src/pages/commune/[slug].astro
    - site/src/pages/es/comuna/[slug].astro
decisions:
  - Inline rate StatCard (not via component) to allow id hooks without modifying StatCard interface
  - yearI18n block placed after `const t = EN_STRINGS/ES_STRINGS` to avoid temporal dead zone
  - FAMILY_LABELS_PAGE hoisted verbatim from FamilyBreakdownBars; FamilyBreakdownBars now imports it
  - data-year on Sparkline rects for active-year toggle via vanilla JS
  - data-family on FamilyBreakdownBars fill/val spans for family bar updates
metrics:
  duration: ~25min
  completed: 2026-06-20
  tasks: 3
  files: 6
---

# Quick 260620-hrh: Year Selector + Longitudinal Crime Charts per Commune — Summary

**One-liner:** Vanilla-JS year selector (2005–present) + 8 static SVG polyline mini-charts (7 crime families + homicide) on every EN and ES commune page, with server-rendered default year and zero client:* directives.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Hoist FAMILY_LABELS_PAGE + create CrimeFamilyCharts | 1c6bed2 | familyDefs.ts, CrimeFamilyCharts.astro, FamilyBreakdownBars.astro, Sparkline.astro |
| 2 | Add i18n strings | 3e94da2 | i18n.ts |
| 3 | Wire year selector + charts into both commune pages | ff57ba9 | [slug].astro (EN + ES) |

## What Was Built

- **CrimeFamilyCharts.astro** — zero-JS server-rendered component with 7 family polyline charts + 1 homicide chart. Each chart scales to its own max. Partial years at 0.5 opacity. Bilingual aria-labels. Responsive CSS grid.
- **Year selector** — `<label>` + `<select id="year-select">` above KeyStatsRow. Options populated from all series years (descending). Default = `latestCompleteYear` in static HTML (SEO intact).
- **Vanilla JS** — parses `#year-data` and `#year-i18n` JSON islands; updates rate card, family heading, family bars (value + width %), homicide section, Sparkline active rect on selector change. Zero page reload. Zero framework.
- **JSON islands** — `#year-data` (all years × {rate, byFamily, homRate, homCount}) and `#year-i18n` (template strings + locale) embedded via `set:html`. No {expr} in executable scripts.
- **Shared infra** — `FAMILY_LABELS_PAGE` hoisted to familyDefs.ts; `data-family` attrs on FamilyBreakdownBars spans; `data-year` attrs on Sparkline rects.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Temporal dead zone — t used before initialization**
- **Found during:** Task 3, first build attempt
- **Issue:** `yearI18n` block was placed before `const t = EN_STRINGS/ES_STRINGS`, causing ReferenceError at render time
- **Fix:** Moved `yearI18n` to after the `const t` declaration in both pages
- **Files modified:** commune/[slug].astro, es/comuna/[slug].astro
- **Commit:** included in ff57ba9

**2. [Rule 2 - Missing functionality] Inline rate StatCard**
- **Found during:** Task 3 planning
- **Issue:** StatCard component has no id-prop interface; plan required `id="rate-value"` and `id="rate-label"` hooks. Modifying StatCard would affect all pages.
- **Fix:** Rendered rate card inline with `.stat-card`/`.stat-value`/`.stat-label` classes (identical to StatCard output) + ids. Other two stat cards stay as StatCard components.
- **Files modified:** commune/[slug].astro, es/comuna/[slug].astro

## Verification Results

- `astro check`: 9 pre-existing errors (ComparatorPairsLinks, RankingTableEnhancer, news, RankingRow type) — unchanged count, no new errors introduced
- `npm run build`: clean, no errors
- `npm run validate`: PASS on all 10 suites (crime, hreflang, schema, map, forbidden-language, coverage, spine, seo, figure-registry, avs-b-budget)
- Built EN/ES commune pages contain: `year-select`, `year-data`, `year-i18n`, `crime-family-charts`
- Built pages contain 0 `client:` directives

## Known Stubs

None — all data wired from real `data.series` and `featured_rates`.

## Threat Flags

None — pure frontend rendering change; no new endpoints or auth paths.

## Self-Check: PASSED

- CrimeFamilyCharts.astro: FOUND
- familyDefs.ts exports FAMILY_LABELS_PAGE: FOUND (grep confirmed)
- Commits 1c6bed2, 3e94da2, ff57ba9: all present in git log
- Built dist/commune/algarrobo/index.html contains all required markers: CONFIRMED
- validate: all PASS
