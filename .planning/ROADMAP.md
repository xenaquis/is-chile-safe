# ROADMAP — Chile Safety Map (ischilesafe.com)

_Last updated: 2026-06-12_

## Phases

- [x] **Phase 1: Data Foundation** - CEAD scraper extracts and validates all quantitative crime data into a stable JSON schema (completed 2026-06-13)
- [ ] **Phase 2: Astro Site + Programmatic Pages** - Static site framework deployed with bilingual programmatic pages for all 346 comunas, 16 regions, and crime types
- [ ] **Phase 3: Leaflet Map Island** - Interactive choropleth map with filters, commune popup panel, and geolocation — fully functional on mobile
- [ ] **Phase 4: Editorial Pages + AdSense** - High-priority editorial and legal pages live; editorial guardrails enforced at build time; AdSense integrated
- [ ] **Phase 5: RSS News Pipeline** - Automated RSS ingestion, DeepSeek classification, and rolling incident feed powering map pins
- [ ] **Phase 6: CI/CD + Cloudflare Deployment** - Fully automated cron pipelines deployed without rebuild loops; site live on ischilesafe.com

## Phase Details

### Phase 1: Data Foundation

**Goal**: Real CEAD crime data for all 346 comunas is available as a validated, stable JSON schema that every downstream component can consume
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):

  1. Running the scraper produces per-comuna JSON files for all 346 comunas, 16 regions, and national aggregates covering 2005–present
  2. A schema validation step rejects commits when expected commune count, required keys, or plausible rate ranges are violated — the last good JSON file is preserved
  3. The pre-aggregated map payload (`map-payload.json`) is present and under 30 KB
  4. Crime rates are expressed as rate per 100,000 inhabitants; national rankings exclude communes with fewer than 10,000 residents

**Plans**: 4 plans

- [x] 01-01-PLAN.md — Pipeline scaffold, Pydantic v2 schema gate, atomic write, pytest infra
- [x] 01-02-PLAN.md — INE communal population asset + lookup module (10k ranking filter)
- [x] 01-03-PLAN.md — CEAD HTTP client, commune catalog, HTML/decimal parser + fixture
- [x] 01-04-PLAN.md — Normalizer (trend/rank/slug/featured) + orchestrator + full /data/cead output

### Phase 2: Astro Site + Programmatic Pages

**Goal**: A pre-rendered bilingual static site is deployed on Cloudflare Pages with SEO-valid programmatic pages for all territorial entities
**Depends on**: Phase 1
**Requirements**: PAGES-01, PAGES-02, PAGES-03, PAGES-04, SEO-01, SEO-02, SEO-03, SEO-04
**Success Criteria** (what must be TRUE):

  1. An initial batch of 10–20 commune pages is live and indexed in Google Search Console before full generation is triggered
  2. Every commune page contains 500+ words with at least 5 unique data dimensions (rate vs. national average, rate vs. regional average, trend direction, dominant crime type, comparable commune)
  3. Every page has correct, reciprocal hreflang tags (EN at root, ES under `/es/`), a canonical tag, and appears in the auto-generated sitemap.xml
  4. Region pages (16 × 2 locales) and crime-type pages are accessible and contain structured Schema.org `Dataset`/`Place` data
  5. The site ships with PWA manifest and theme color; no page depends on client-side rendering for SEO-critical content

**Plans**: 6 plans

- [x] 02-01-PLAN.md — Astro scaffold + node:fs data loader + i18n/family-slugs/rollout config + slug maps + color scale + validation stubs (Wave 1)
- [x] 02-02-PLAN.md — global.css tokens + BaseLayout (hreflang/canonical/PWA meta) + 11 ported server-rendered components (Wave 2)
- [ ] 02-03-PLAN.md — Commune pages EN+ES: deterministic prose variation engine (500+ words, 5 dimensions) + rollout batch gate (Wave 3)
- [ ] 02-04-PLAN.md — Region pages EN+ES (16×2): aggregates + commune ranking table (Wave 3)
- [ ] 02-05-PLAN.md — Crime-type pages EN+ES (7×2): national family ranking + translated slugs + featured prominence (Wave 3)
- [ ] 02-06-PLAN.md — SEO finishing: rollout-gated sitemap + Schema.org + PWA manifest + hreflang/schema validators + full ROLLOUT_ALL build gate + UAT (Wave 4)

**UI hint**: yes

### Phase 3: Leaflet Map Island

**Goal**: Users can explore Chilean crime data through an interactive map on any device, including mid-range mobile
**Depends on**: Phase 1, Phase 2
**Requirements**: MAP-01, MAP-02, MAP-03, MAP-04, MAP-05, MAP-06
**Success Criteria** (what must be TRUE):

  1. The choropleth map loads and renders all 346 communes with color coding by relative incidence; switching years or crime types updates the map without a page reload
  2. Clicking a commune opens a panel showing tasa per 100k, trend direction, national ranking, sparkline (2005–present), and crime-family breakdown
  3. The GeoJSON boundary file is under 100 KB; the map renders without jank on a mid-range Android at 3G (tested manually before phase sign-off)
  4. Tapping "mostrar mi ubicación" identifies and highlights the user's commune
  5. Incident pins (NEWS layer) appear on the map with source and date when `incidents/current.json` is present (may show empty state in this phase if Phase 5 is not yet done)

**Plans**: TBD
**UI hint**: yes

### Phase 4: Editorial Pages + AdSense

**Goal**: Authoritative editorial and legal pages are live and indexed; the site qualifies for and has AdSense integrated
**Depends on**: Phase 2
**Requirements**: EDIT-01, EDIT-02, EDIT-03, EDIT-04, EDIT-05, MON-01
**Success Criteria** (what must be TRUE):

  1. All 10 priority EN editorial pages and all 10 priority ES editorial pages are accessible, contain substantive content, and are submitted to Google Search Console
  2. The methodology page explains CEAD sources, rate calculation, subregistro caveat, and comparison criteria — it is indexed before AdSense application
  3. Legal pages (Privacy Policy, Terms, About, Contact) are live and linked from the site footer
  4. The Astro build fails with a clear error message if any page contains forbidden language ("zona peligrosa", "comunas peligrosas", "ranking definitivo", "zona segura garantizada")
  5. AdSense code is integrated and serving ads after the first indexing wave is confirmed

**Plans**: TBD
**UI hint**: yes

### Phase 5: RSS News Pipeline

**Goal**: Recent crime incidents from national press are automatically classified, geolocated, and surfaced as incident pins on the map
**Depends on**: Phase 1, Phase 3
**Requirements**: NEWS-01, NEWS-02, NEWS-03, NEWS-04, NEWS-05
**Success Criteria** (what must be TRUE):

  1. The pipeline ingests RSS from BioBíoChile, Cooperativa Policial, and La Tercera; a failed feed is skipped and logged without blocking the run
  2. Each classified incident is matched against the canonical 346-commune list (temperature 0.0); incidents with no exact commune match are rejected and not committed
  3. `incidents/current.json` contains only incidents from the last 30 days; older incidents roll to monthly archive files
  4. Every published incident displays its source outlet name, source URL, and publication date on the map pin
  5. After a full pipeline run, a manual audit of 50 extracted incidents confirms no commune-hallucination errors before the pipeline is declared production-ready

**Plans**: TBD

### Phase 6: CI/CD + Cloudflare Deployment

**Goal**: The site is live on ischilesafe.com with automated pipelines that update data without developer intervention and without burning build quotas
**Depends on**: Phase 2, Phase 5
**Requirements**: INFRA-01, INFRA-02, INFRA-03
**Success Criteria** (what must be TRUE):

  1. The `news-pipeline.yml` GitHub Actions workflow runs every 4–6 hours and the `cead-scraper.yml` runs quarterly; both apply rate limiting to external endpoints
  2. After a cron data commit, Cloudflare Pages does not trigger an automatic rebuild; a Deploy Hook is invoked only when `git diff` confirms data files changed — verified by checking the CF Pages build count after the first cron run
  3. The site is accessible at ischilesafe.com with HTTPS; all ~750 HTML pages are served from Cloudflare's CDN

**Plans**: TBD

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation | 4/4 | Complete    | 2026-06-13 |
| 2. Astro Site + Programmatic Pages | 2/6 | In Progress|  |
| 3. Leaflet Map Island | 0/? | Not started | - |
| 4. Editorial Pages + AdSense | 0/? | Not started | - |
| 5. RSS News Pipeline | 0/? | Not started | - |
| 6. CI/CD + Cloudflare Deployment | 0/? | Not started | - |
