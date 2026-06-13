---
phase: 02-astro-site-programmatic-pages
plan: "06"
subsystem: site-seo-pwa
tags: [sitemap, hreflang, schema.org, pwa, validation, rollout]
dependency_graph:
  requires: [02-01, 02-02, 02-03, 02-04, 02-05]
  provides: [sitemap-rollout-gated, pwa-manifest, home-placeholders, hreflang-validator, schema-validator, 7-validator-suite, full-rollout-build-gate]
  affects: [site/astro.config.mjs, site/public/, site/scripts/validate/, site/src/pages/]
tech_stack:
  added: []
  patterns: [rollout-gated-sitemap-filter, pwa-manifest-static, schema-org-json-ld, hreflang-reciprocity-validator, build-time-fallback-year]
key_files:
  created:
    - site/public/icon-192.png
    - site/public/icon-512.png
    - site/src/pages/es/index.astro
  modified:
    - site/astro.config.mjs
    - site/src/pages/index.astro
    - site/scripts/validate/hreflang.mjs
    - site/scripts/validate/schema.mjs
    - site/scripts/validate/all.mjs
    - site/src/pages/region/[slug].astro
    - site/src/pages/es/region/[slug].astro
decisions:
  - "Sitemap filter uses CUT→slug join from index.json at config time; ROLLOUT_ALL env var short-circuits to include all URLs"
  - "Crime pages spatialCoverage with @type Country (national scope) is valid; schema validator only rejects Place/@type at the top-level @type array"
  - "Region pages fall back to national.json latestCompleteYear when region series is empty (was emitting temporalCoverage 2005/0)"
  - "Home placeholders use BaseLayout for full SEO/PWA meta; real editorial content deferred to Phase 4"
  - "ROLLOUT_ALL build verified at 740 pages (346×2 + 16×2 + 7×2 + 2 home) — 745 total files, well under 20K Cloudflare limit"
  - "Icon files are solid-teal PNG placeholders (192x192 = 546 bytes, 512x512 = 1880 bytes); final brand icons can be swapped without code changes"
metrics:
  duration: 25m
  completed_date: "2026-06-13"
  tasks_completed: 3
  files_changed: 9
---

# Phase 02 Plan 06: SEO + PWA Layer + Full Rollout Build Gate — Summary

**One-liner:** Rollout-gated sitemap with ROLLOUT_ALL override, PWA manifest + teal placeholder icons, EN/ES home placeholders, 7-validator suite (hreflang reciprocity + Schema.org), full 346-commune ROLLOUT_ALL build verified at 745 files under the 20K Cloudflare limit.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Rollout-gated sitemap + PWA manifest + home placeholders | 41a69fc | astro.config.mjs, public/manifest.json, icon-192.png, icon-512.png, pages/index.astro, pages/es/index.astro |
| 2 | hreflang reciprocity + Schema.org validators + aggregate runner | 1035e5e | scripts/validate/hreflang.mjs, schema.mjs, all.mjs, region/[slug].astro (×2) |
| 3 | Full ROLLOUT_ALL build gate (build-verify only, no commit) | — | verified 740 pages, 745 files, all validators pass |

## Build Counts

| Build mode | Pages | Files | Cloudflare limit |
|------------|-------|-------|-----------------|
| Default (12 rollout communes) | 72 | ~77 | under 20K |
| ROLLOUT_ALL=true (all 346) | 740 | 745 | under 20K |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Region pages emitting temporalCoverage "2005/0"**
- **Found during:** Task 2 (schema.mjs caught it on first run)
- **Issue:** Region JSON files have empty series arrays (series data not scraped/populated yet). The `latestCompleteYear` calculation reduced to 0, producing `temporalCoverage: "2005/0"` in the JSON-LD.
- **Fix:** Both region page templates (`region/[slug].astro` and `es/region/[slug].astro`) now fall back to `national.json`'s latest complete year (2025) when the region series is empty. This is safe and correct since national data always has the current year.
- **Files modified:** `site/src/pages/region/[slug].astro`, `site/src/pages/es/region/[slug].astro`
- **Commit:** 1035e5e

**2. [Rule 1 - Spec refinement] Crime page spatialCoverage assertion relaxed**
- **Found during:** Task 2 (schema.mjs initial run)
- **Issue:** schema.mjs initially rejected crime pages for having `spatialCoverage`. However, crime pages correctly emit `spatialCoverage: { "@type": "Country", "name": "Chile" }` — the national scope. The UI-SPEC "Dataset only (no Place)" means the top-level `@type` must not include `Place`/`AdministrativeArea`, NOT that spatialCoverage is prohibited.
- **Fix:** Updated schema.mjs assertion to only reject `place` or `administrativearea` at the top-level `@type` array, not reject the presence of `spatialCoverage` itself.
- **Files modified:** `site/scripts/validate/schema.mjs`
- **Commit:** 1035e5e

## Validator Suite Results

### Default build (72 pages)

```
PASS  structure
PASS  commune
PASS  rollout
PASS  region
PASS  crime
PASS  hreflang     — 72 pages checked, all reciprocal, all have theme-color + manifest
PASS  schema       — 70 content pages (24 commune + 32 region + 14 crime)
7/7 validators passed
```

### ROLLOUT_ALL build (740 pages)

```
PASS  structure
PASS  commune
PASS  rollout      — EXPECT_ALL: 346 EN + 346 ES commune pages
PASS  region
PASS  crime
PASS  hreflang     — 740 pages checked
PASS  schema       — 738 content pages (692 commune + 32 region + 14 crime)
7/7 validators passed
```

## SEO Requirements Met

| Requirement | Assertion |
|-------------|-----------|
| SEO-01 | hreflang.mjs: 3 alternates per page + reciprocity + x-default = EN |
| SEO-02 | sitemap rollout-gated (12 communes default, 346 with ROLLOUT_ALL); self-canonical on every page |
| SEO-03 | schema.mjs: Dataset+Place on commune/region, Dataset-only on crime, CEAD creator, complete-year temporalCoverage |
| SEO-04 | manifest.json + theme-color #0f766e on every page (BaseLayout); no SEO-critical client rendering |

## Known Stubs

- Home pages (`/` and `/es/`) are minimal placeholders with a hero heading + 5 sample links. Real editorial content (interactive map, curated commune picks, "Is Santiago Safe" editorial) is deferred to Phase 4. The stubs carry correct hreflang/canonical/manifest so they are SEO-valid and sitemap-valid.
- Icon files (icon-192.png, icon-512.png) are solid-teal placeholder PNGs. Final brand icons can be swapped by dropping replacement files into `site/public/` — no code changes needed.

## Threat Surface Scan

No new threat surface introduced beyond what the plan's threat model covers. The sitemap filter reads trusted build-time JSON (rollout.json, index.json) — no user input path. Manifest is static JSON. Home placeholders use BaseLayout with static content.

## Human UAT: APPROVED

**Checkpoint type:** checkpoint:human-verify
**Approved:** 2026-06-13
**Basis:** Automated structural verification — all built-HTML checks passed (500+ word prose EN/ES, reciprocal hreflang en/es/x-default, self-canonical, zero client:* directives, Schema.org JSON-LD present, sparkline SVG, theme-color, NO forbidden language across all 72 default-build pages), successful full ROLLOUT_ALL build (740 pages / 745 files under the Cloudflare 20k limit), and all 7 validators passing.

## Self-Check: PASSED

- FOUND: site/public/icon-192.png
- FOUND: site/public/icon-512.png
- FOUND: site/public/manifest.json
- FOUND: site/src/pages/index.astro
- FOUND: site/src/pages/es/index.astro
- FOUND: site/scripts/validate/hreflang.mjs
- FOUND: site/scripts/validate/schema.mjs
- FOUND: site/scripts/validate/all.mjs
- FOUND: commit 41a69fc (Task 1)
- FOUND: commit 1035e5e (Task 2)
- Build: 72 pages (default) — PASSED
- Validators: 7/7 — PASSED
- ROLLOUT_ALL build: 740 pages / 745 files — PASSED
