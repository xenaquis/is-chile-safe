---
phase: 19-tech-debt-sweep
plan: "04"
subsystem: seo-spine
status: complete
tags: [seo, hreflang, robots-txt, glossary, redirects, vida-homicide]
dependency_graph:
  requires: []
  provides: [robots-txt, santiago-hreflang-pair, glossary-nav, homicide-redirects]
  affects: [PageHeader, PageFooter, astro.config.mjs, is-santiago-safe, mapa-seguridad-santiago, crime-family-pages]
tech_stack:
  added: []
  patterns: [astro-static-redirects, sitemap-explicit-rules, validator-redirect-skip]
key_files:
  created:
    - site/public/robots.txt
  modified:
    - site/astro.config.mjs
    - site/src/pages/is-santiago-safe.astro
    - site/src/pages/es/mapa-seguridad-santiago.astro
    - site/src/components/PageHeader.astro
    - site/src/components/PageFooter.astro
    - site/src/pages/crime/[family].astro
    - site/src/pages/es/delito/[family].astro
    - site/scripts/validate/hreflang.mjs
    - site/scripts/validate/schema.mjs
decisions:
  - "Used Astro top-level `redirects:` config for homicide redirects — emits static HTML redirect pages with meta refresh + noindex + canonical; preferred over meta-refresh in page template"
  - "Filtered vida from getStaticPaths in both crime/[family] pages to prevent redirect shadowing by a real page"
  - "Updated hreflang.mjs and schema.mjs validators to skip pages with http-equiv=refresh (static redirects are not content pages)"
metrics:
  duration: "~15 min"
  completed: "2026-06-19"
  tasks_completed: 2
  files_changed: 10
---

# Phase 19 Plan 04: SEO Spine Summary

Tightened the structural SEO spine: robots.txt with crawl allow and sitemap pointer; Santiago EN↔ES reciprocal hreflang pair (was a self-loop); glossary surfaced in nav and footer for both locales; explicit ranking sitemap inclusion rules; `/crime/homicide/` and `/es/delito/homicidios/` redirected to canonical ranking pages with vida excluded from getStaticPaths.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | robots.txt + Santiago hreflang pair + glossary spine + ranking sitemap rule | 07ecc10 | robots.txt, is-santiago-safe.astro, mapa-seguridad-santiago.astro, PageHeader.astro, PageFooter.astro, astro.config.mjs |
| 2 | Redirect /crime/homicide/ and /es/delito/homicidios/ to canonical homicide pages | 07ecc10 | astro.config.mjs, crime/[family].astro, es/delito/[family].astro, hreflang.mjs, schema.mjs |

## Verification

- Build: 791 pages + 2 static redirect pages (homicide EN+ES); 12/12 validators green
- dist/robots.txt: contains `Sitemap: https://ischilesafe.com/sitemap-index.xml`
- dist/crime/homicide/index.html: static redirect → /crime-ranking/homicide/ (meta refresh, noindex, canonical)
- dist/es/delito/homicidios/index.html: static redirect → /es/ranking-delito/homicidios/
- hreflang validator: scanned 793 HTML files, 0 failures (redirect pages skipped)
- schema validator: 692 commune + 32 region + 14 crime pages (redirect pages skipped)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Updated validators to skip static redirect pages**
- **Found during:** Task 2 validate run
- **Issue:** hreflang.mjs and schema.mjs scanned ALL HTML files in dist/, including Astro-generated static redirect pages that have no hreflang/JSON-LD. Both validators failed on /crime/homicide/index.html and /es/delito/homicidios/index.html with 10 issues.
- **Fix:** Added `if (html.includes('http-equiv="refresh"')) continue;` guard in hreflang.mjs loop; same guard in schema.mjs checkCrimeDir before checkPage call.
- **Files modified:** site/scripts/validate/hreflang.mjs, site/scripts/validate/schema.mjs
- **Commit:** 07ecc10

**2. [Rule 1 - Bug] Fixed mapa-seguridad-santiago.astro enPath pointing to non-existent /santiago-safety-map/**
- **Found during:** Task 1 pre-edit inspection
- **Issue:** ES page had `enPath="/santiago-safety-map/"` which does not exist (that URL generates a santiago-safety-map page, not the is-santiago-safe editorial). The canonical EN pair is /is-santiago-safe/.
- **Fix:** Changed enPath to "/is-santiago-safe/" — the actual EN editorial page.
- **Files modified:** site/src/pages/es/mapa-seguridad-santiago.astro
- **Commit:** 07ecc10

## Known Stubs

None.

## Threat Flags

None — changes are structural SEO signals (robots.txt, hreflang, redirects). No new network endpoints or trust boundaries introduced.

## Self-Check: PASSED

- site/public/robots.txt: exists, contains "Sitemap:"
- site/dist/robots.txt: present in built dist
- site/dist/crime/homicide/index.html: present (static redirect)
- site/dist/es/delito/homicidios/index.html: present (static redirect)
- Commit 07ecc10: present in git log
- 12/12 validators: all passed
