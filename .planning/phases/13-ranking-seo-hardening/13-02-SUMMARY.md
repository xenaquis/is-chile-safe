---
phase: 13-ranking-seo-hardening
plan: "02"
subsystem: seo-meta
tags: [seo, opengraph, twitter, og-image, locale, baselayout]
one_liner: "OG/Twitter meta injected site-wide via BaseLayout pageType prop wired across 3 layouts and 10 page templates"

dependency_graph:
  requires: ["13-01"]
  provides: ["13-03"]
  affects: ["site/src/layouts/BaseLayout.astro", "site/src/layouts/HomeLayout.astro", "site/src/layouts/EditorialLayout.astro"]

tech_stack:
  added: []
  patterns:
    - "OG_IMAGE_BY_TYPE map keyed by pageType → absolute /og/<type>.png URL"
    - "pageType enum propagated from page template through layout wrappers to BaseLayout"
    - "ogType=article for editorial only; website elsewhere (Pitfall 4 override for rankings)"
    - "ogLocale=en_US/es_CL derived from lang prop; ogLocaleAlt for alternate"

key_files:
  created: []
  modified:
    - site/src/layouts/BaseLayout.astro
    - site/src/layouts/HomeLayout.astro
    - site/src/layouts/EditorialLayout.astro
    - site/src/pages/index.astro
    - site/src/pages/es/index.astro
    - site/src/pages/commune/[slug].astro
    - site/src/pages/es/comuna/[slug].astro
    - site/src/pages/region/[slug].astro
    - site/src/pages/es/region/[slug].astro
    - site/src/pages/crime/[family].astro
    - site/src/pages/es/delito/[family].astro
    - site/src/pages/rankings.astro
    - site/src/pages/es/rankings.astro

decisions:
  - "pageType defaults to 'default' in BaseLayout (maps to /og/default.png) — safe fallback for any page not in the enum"
  - "EditorialLayout defaults pageType='editorial'; explicit prop from caller overrides (enables rankings override)"
  - "jsonLd Props type widened to object|object[]|null in BaseLayout + both wrapper layouts; emission block unchanged (Plan 03 will handle arrays)"

metrics:
  duration: "~12 minutes"
  completed: "2026-06-15"
  tasks_completed: 3
  files_modified: 13
---

# Phase 13 Plan 02: OG/Twitter Meta Site-Wide Summary

OG/Twitter meta injected site-wide via BaseLayout pageType prop wired across 3 layouts and 10 page templates, with all 12 validators passing and per-type og:image correctly resolved.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | OG/Twitter meta block + pageType prop + widened jsonLd type in BaseLayout | e5c156e | site/src/layouts/BaseLayout.astro |
| 2 | Forward pageType through HomeLayout + EditorialLayout | 8b64b59 | site/src/layouts/HomeLayout.astro, site/src/layouts/EditorialLayout.astro |
| 3 | Set pageType on all page templates | 4f2ddc5 | 10 page template files |

## Verification

Build + seo.mjs + all.mjs chained in one command:

- seo.mjs: PASSED (13/13 OG assertions, 13/13 ld+json quality checks)
- all.mjs: 12/12 validators passed
- rankings/index.html: og:type=website, og:image=https://ischilesafe.com/og/ranking.png (Pitfall 4 confirmed)
- EN pages: og:locale=en_US, og:url no /es/ prefix
- ES pages: og:locale=es_CL, og:url contains /es/
- editorial pages (is-chile-safe): og:type=article, og:image=.../og/editorial.png

## What Was Built

**BaseLayout.astro:**
- New `pageType` prop (enum + 'default' fallback)
- `OG_IMAGE_BY_TYPE` map → absolute `https://ischilesafe.com/og/<type>.png`
- OG meta block (og:site_name/title/description/type/url/image/width/height/locale/alternate) after canonical link
- Twitter Card meta (twitter:card=summary_large_image/title/description/image)
- `jsonLd` Props type widened to `object | object[] | null` (emission unchanged)

**HomeLayout.astro + EditorialLayout.astro:**
- `pageType` prop added and forwarded to BaseLayout
- `jsonLd` Props type widened to `object | object[] | null`
- EditorialLayout defaults `pageType = 'editorial'`

**Page templates (10 files):**
- `index.astro` + `es/index.astro`: `pageType="home"`
- `commune/[slug].astro` + `es/comuna/[slug].astro`: `pageType="commune"`
- `region/[slug].astro` + `es/region/[slug].astro`: `pageType="region"`
- `crime/[family].astro` + `es/delito/[family].astro`: `pageType="crime"`
- `rankings.astro` + `es/rankings.astro`: `pageType="ranking"` (overrides editorial default)

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all OG meta emits real per-locale values from existing title/description/canonicalPath props.

## Threat Flags

None — no new network endpoints or auth paths introduced. OG meta derives from build-time static data; Astro auto-escapes `<meta content=...>` attribute values.

## Self-Check: PASSED

- site/src/layouts/BaseLayout.astro: EXISTS
- site/src/layouts/HomeLayout.astro: EXISTS
- site/src/layouts/EditorialLayout.astro: EXISTS
- Commit e5c156e: EXISTS
- Commit 8b64b59: EXISTS
- Commit 4f2ddc5: EXISTS
- seo.mjs: PASSED
- all.mjs 12/12: PASSED
