---
phase: 25-ui-ux-360-remediation-prod-diagnostic-2026-07-02-p0-soft-404
plan: "08"
subsystem: seo-structured-data, region-pages
tags: [json-ld, structured-data, region, rankings, copy-polish, p2-2, p2-3]
dependency_graph:
  requires: [25-01, 25-06]
  provides: [home-websiteorg-jsonld, rankings-16-region-links, region-kpi-direction, region-chart-footnote, region-map-cta]
  affects: [dist/index.html, dist/rankings/index.html, dist/region/**/index.html, dist/es/region/**/index.html]
tech_stack:
  added: []
  patterns: [schema-org-builders, astro-static-jsonld]
key_files:
  created: []
  modified:
    - site/src/lib/jsonld.ts
    - site/src/pages/index.astro
    - site/src/pages/rankings.astro
    - site/src/pages/region/[slug].astro
    - site/src/pages/es/region/[slug].astro
decisions:
  - buildWebSite and buildOrganization added to jsonld.ts following existing builder shape (returns Record<string,unknown>, uses BASE_URL const)
  - rankings.astro loads all 16 regions via loadRegion(1..16) at build time; 2-column CSS list
  - Region map placeholder replaced inline (not via MapPlaceholderSlot) to support per-region ?region= query param
  - Chart title hardcoded to 2026* (not dynamic) to reflect partial-year bar that Sparkline always renders
metrics:
  duration: "~20m"
  completed: "2026-07-02"
  tasks_completed: 2
  files_modified: 5
---

# Phase 25 Plan 08: Home JSON-LD + Rankings Region Links + Region Copy Polish Summary

Home page now carries WebSite+Organization JSON-LD structured data; /rankings/ links all 16 region pages; region KPI shows "(1 = highest reported)" direction; evolution chart title is "(2005–2026*)" with a partial-year footnote; map placeholder is a dashed-border CTA card linking to /map/?region={slug}.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Home WebSite+Organization JSON-LD; /rankings/ 16 region links (P2-2) | fa0deb2 | jsonld.ts, index.astro, rankings.astro |
| 2 | Region page copy polish — KPI direction, chart 2026*, placeholder CTA (P2-3) | cc69106 | region/[slug].astro (EN+ES) |

## Verification

```
npm run build && npm run validate
→ 834 pages built
→ 14/14 validators PASSED (including forbidden-language green)
→ dist/index.html: "WebSite" ✓, "Organization" ✓
→ dist/rankings/index.html: 16 /region/ links ✓
→ dist/region/metropolitana/index.html: "1 = highest reported" ✓, "2026*" ✓, "partial year data (Jan–Jun)" ✓
```

## Deviations from Plan

### Auto-applied

**1. [Rule 2 - Missing functionality] ES region page parity**
- Found during: Task 2
- Issue: Plan listed `region/[slug].astro` but the ES mirror `es/region/[slug].astro` needed identical treatment
- Fix: Applied all Task 2 changes to both EN and ES region pages (KPI sublabel in ES, ES footnote, ES map placeholder with /es/mapa/?region=... hardcoded)
- Files: site/src/pages/es/region/[slug].astro
- Commit: cc69106

**2. [Rule 2 - Missing functionality] Map placeholder inline (not via MapPlaceholderSlot)**
- Found during: Task 2
- Issue: MapPlaceholderSlot didn't accept a custom href/region param; it always links to /map/ or /es/mapa/ without query string
- Fix: Replaced component call with inline `<a href="/map/?region={slug}" class="map-placeholder-card">` + CSS in both EN/ES region templates
- MapPlaceholderSlot component itself was not modified (still used by commune and crime pages)

## Known Stubs

None. All map placeholder links point to live /map/ and /es/mapa/ pages; ?region= param is for future map deep-link implementation (map already exists at /map/).

## Threat Flags

None beyond plan's threat register. JSON-LD strings are static literals; no user input involved.

## Self-Check: PASSED

- fa0deb2 exists in git log ✓
- cc69106 exists in git log ✓
- dist/index.html contains WebSite + Organization ✓
- dist/rankings/index.html contains ≥16 /region/ hrefs ✓
- dist/region/metropolitana/index.html contains "1 = highest reported" ✓
- 14/14 validators green ✓
