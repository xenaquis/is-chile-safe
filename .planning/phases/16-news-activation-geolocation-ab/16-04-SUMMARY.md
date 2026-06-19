---
phase: 16-news-activation-geolocation-ab
plan: "04"
subsystem: frontend-news
tags: [news, incidents, bilingual, nav, sitemap, i18n]
dependency_graph:
  requires: [16-03]
  provides: [news-surface-frontend, incident-comuna-links]
  affects: [PageHeader, IncidentsList, IncidentPinLayer, sitemap]
tech_stack:
  added: []
  patterns: [EditorialLayout two-file bilingual pattern, existsSync build-time fallback, escHtml defense-in-depth]
key_files:
  created:
    - site/src/pages/news.astro
    - site/src/pages/es/noticias.astro
  modified:
    - site/src/components/map/IncidentsList.tsx
    - site/src/components/map/IncidentPinLayer.ts
    - site/src/components/PageHeader.astro
    - site/src/config/i18n.ts
    - site/astro.config.mjs
decisions:
  - newsHref hardcoded per-locale in PageHeader (getRelativeLocaleUrl does not translate ES slugs — Pitfall 3)
  - esPath "/es/noticias/" hardcoded in both news page files (localized-slug pitfall)
  - escHtml applied to incident.slug in IncidentPinLayer popup for defense-in-depth (T-16-12)
  - existsSync + try/catch fallback in both news pages prevents build crash if current.json absent
metrics:
  duration: 12m
  completed: "2026-06-18"
  tasks: 3
  files: 7
---

# Phase 16 Plan 04: News Surface Frontend Summary

**One-liner:** Bilingual /news/ + /es/noticias/ pages with freshness indicator, incident→source + incident→comuna links in popup/list/page, nav_news i18n string, News nav link, and sitemap rule.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add slug+cut to Incident interfaces; render comuna link in popup + list | 7de437d | IncidentsList.tsx, IncidentPinLayer.ts |
| 2 | Build bilingual news pages /news/ + /es/noticias/ with freshness | 854f098 | news.astro, es/noticias.astro |
| 3 | Wire nav_news i18n string, News nav link, sitemap entries | c683966 | i18n.ts, PageHeader.astro, astro.config.mjs |

## What Was Built

**Task 1 — Incident interface extensions + comarca links:**
- `IncidentsList.tsx`: added `slug?: string` and `cut?: string` to the `Incident` interface. Below the existing source `<a>` (unchanged, keeps `rel="noopener noreferrer"`), added a slug-guarded locale-aware `<a class="event-commune-link">` rendering `View commune` (EN) / `Ver comuna` (ES) pointing to `/commune/{slug}/` or `/es/comuna/{slug}/`.
- `IncidentPinLayer.ts`: added `slug?: string` to the `Incident` interface; derived `communeBase` per locale before the incident loop (Pitfall 5); built a slug-guarded HTML string with `escHtml(incident.slug)` for defense-in-depth (T-16-12); injected as `<div class="ev-meta">` in the popup.

**Task 2 — Bilingual news pages:**
- `site/src/pages/news.astro` — EN page at `/news/`; reads `data/incidents/current.json` via `existsSync` + `readFileSync` at build time; `generated` rendered as `<time datetime={...}>Updated {date}</time>`; incident list with source link (`↗`, `rel="noopener noreferrer"`) + slug-guarded commune link; empty-state fallback; `EditorialLayout` with hardcoded `enPath="/news/"` `esPath="/es/noticias/"`.
- `site/src/pages/es/noticias.astro` — ES parity page at `/es/noticias/`; identical structure with ES locale date formatting, `title_es`, `Fuente:`, `Ver comuna`, `/es/comuna/{slug}/`; hardcoded `esPath="/es/noticias/"` (never `getRelativeLocaleUrl`).

**Task 3 — Nav + i18n + sitemap:**
- `i18n.ts`: added `nav_news: string` to `I18nStrings` interface; `nav_news: 'News'` in `EN_STRINGS`; `nav_news: 'Noticias'` in `ES_STRINGS`.
- `PageHeader.astro`: added `const newsHref = locale === 'en' ? '/news/' : '/es/noticias/';` (hardcoded — Pitfall 3); added `<a href={newsHref} class="nav-link">{t.nav_news}</a>` after methodology link in `<nav>`.
- `astro.config.mjs`: added explicit early `if (/\/news\/$/.test(url) || /\/es\/noticias\/$/.test(url)) return true;` in `sitemapFilter` before the default return.

## Verification

- `npm run build && npm run validate` — 12/12 validators passed (commune, rollout, region, crime, hreflang, schema, map, forbidden-language, coverage, spine, seo + 12th).
- `dist/news/index.html` and `dist/es/noticias/index.html` confirmed built.
- `nav_news` appears 3× in i18n.ts (interface + EN + ES).
- `newsHref` appears in PageHeader.astro.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. The news pages read real `current.json` data (19 incidents from Phase 16-03). Empty-state fallback is intentional, not a stub.

## Threat Flags

No new threat surface beyond what the plan's threat model covers (T-16-10 through T-16-SC all mitigated).

## Self-Check: PASSED

- `site/src/pages/news.astro` — FOUND
- `site/src/pages/es/noticias.astro` — FOUND
- `site/src/components/map/IncidentsList.tsx` — FOUND (contains `slug`, `comuna`)
- `site/src/components/map/IncidentPinLayer.ts` — FOUND (contains `slug`, `communeBase`)
- `site/src/config/i18n.ts` — FOUND (contains `nav_news` ×3)
- `site/src/components/PageHeader.astro` — FOUND (contains `newsHref`)
- `site/astro.config.mjs` — FOUND (contains `/news/` sitemap rule)
- Commits 7de437d, 854f098, c683966 — all present in git log
