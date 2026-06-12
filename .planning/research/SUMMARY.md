# Project Research Summary

**Project:** Is Chile Safe (ischilesafe.com)
**Domain:** Bilingual crime-data visualization + programmatic SEO static site (Chile)
**Researched:** 2026-06-12
**Confidence:** HIGH (stack, architecture, pitfalls) / MEDIUM (RSS feed viability)

## Executive Summary

This project is a static data-publishing platform combining a government crime-statistics scraper, an AI-powered news incident pipeline, and programmatic bilingual SEO page generation for all 346 Chilean comunas. Experts in this domain build it as a fully pre-rendered static site (Astro SSG) hosted on a global CDN (Cloudflare Pages), with all dynamic behavior isolated to client-side React islands for the interactive map. Data ingestion runs on GitHub Actions cron jobs that commit JSON files to the repo, triggering rebuilds only when new data is confirmed — keeping infrastructure cost at zero.

The recommended approach is: (1) build and validate the CEAD scraper first, since every quantitative feature depends on it; (2) define the shared JSON data schema before either the pipeline or the Astro site consumes it; (3) generate programmatic pages with rich, contextually unique content per comuna — not thin name-swapped templates — to pass Google's scaled content abuse threshold; (4) wire up the RSS + DeepSeek news pipeline in parallel once the schema is stable. The entire stack is open-source, requires no paid backend, and is deployable within Cloudflare's free tier for the projected page count (~750 HTML pages).

The two highest-consequence risks are: thin programmatic content triggering Google deindexing (recovery takes 4-8 weeks and kills SEO before it starts), and a GitHub Actions → Cloudflare Pages infinite rebuild loop burning through the 500 free builds/month in days. Both are design decisions made once, early, and difficult to fix retroactively. A third systemic risk is LLM geolocation hallucination in the news pipeline: DeepSeek must classify against a closed 346-item canonical commune list, not open-ended extraction, or incident pins will silently accumulate geographic errors that damage credibility.

## Key Findings

### Recommended Stack

Astro 6.4.x is the unambiguous choice: it pre-renders all pages to static HTML (mandatory for SEO indexability), has native i18n routing for the two-locale requirement, and its islands architecture lets Leaflet/React run only on pages that need the map — the other ~740 pages ship zero React JS. The Python scraper stack (requests + BeautifulSoup4/lxml + feedparser + openai SDK pointed at DeepSeek) is standard and well-validated. DeepSeek's API is OpenAI-compatible, so no custom SDK is needed.

**Core technologies:**
- Astro 6.4.x: Static site framework, programmatic pages, i18n routing — pre-renders HTML; islands model minimizes JS payload
- @astrojs/react 5.x + React 19.x: Interactive islands only (map, charts) — hydrated client-side, SSR by default
- Leaflet 1.9.x: Choropleth map + incident pins — use native `L.geoJSON()` not react-leaflet's `<GeoJSON>` component to avoid per-hover re-render jank
- Python (requests, bs4/lxml, feedparser): CEAD scraper + RSS ingestion — standard for POST-form government endpoints
- openai SDK v1.x (DeepSeek backend): LLM classification/geolocation — use `deepseek-v4-flash`; `deepseek-chat` is deprecated 2026-07-24
- Cloudflare Pages: Static hosting and CDN — truly free at this file count (~1,500 files vs 20,000-file free limit)
- GitHub Actions: Cron-based data ingestion + conditional deploys — GITHUB_TOKEN commits do NOT trigger push workflows (loop-safe)

**Critical version notes:** Node.js 20+ required by Astro 6. `deepseek-chat` model ID stops working 2026-07-24 — never commit it to code.

### Expected Features

The product competes against CrimeGrade, Numbeo, and SpotCrime, none of which have real official data at commune granularity for Chile. The key competitive moat is CEAD-sourced per-100k rates at the 346-comuna level combined with a bilingual programmatic SEO footprint no competitor has attempted.

**Must have (table stakes):**
- Interactive choropleth map with year and crime-type filters — absence signals "broken" to users
- Crime rate per 100,000 residents as the primary metric — raw counts are statistically meaningless
- Programmatic territorial pages for all 346 comunas + 16 regions (ES + EN) — core SEO vehicle
- Year-over-year trend indicator + sparkline — "is it getting better?" is the primary user question
- Safest/most dangerous rankings (rate-normalized, minimum population filter)
- Methodology page with subregistro caveat — required for user trust and AdSense approval
- Bilingual content (ES + EN) with correct hreflang
- Mobile-responsive layout — >60% LatAm traffic is mobile

**Should have (competitive differentiators):**
- RSS news pipeline + DeepSeek incident pins on map — qualitative recency layer no competitor offers for Chile
- 346-comuna granularity (competitors show Chile at city or country level only)
- Geolocation "identify my comuna" button
- Crime-family breakdown panel within each territorial page
- Sober editorial framing (no "danger zone" labels) — required for AdSense

**Defer to v2+:**
- User-submitted incident reports (requires backend, moderation, user base)
- Email crime alerts (requires email infrastructure + unsubscribe compliance)
- Data download / API licensing
- Native mobile app (responsive web + PWA meta is sufficient)

### Architecture Approach

The system is a four-layer pipeline: (1) Ingestion — Python cron jobs on GitHub Actions that POST to CEAD PHP endpoints and fetch RSS feeds, classify via DeepSeek, and commit normalized JSON to the repo; (2) Data store — version-controlled JSON files in `/data/`, split into per-entity detail files (one per comuna) and a pre-aggregated map payload; (3) Build — Astro SSG reads JSON at build time, embeds structured data in HTML for SEO, bundles Leaflet React island for client-side interactivity; (4) Delivery — Cloudflare Pages CDN. CF Pages auto-build via Git integration must be DISABLED; the pipeline explicitly POSTs a Deploy Hook only when data actually changed.

**Major components:**
1. CEAD Scraper (Python) — POST to government PHP endpoints, parse HTML tables, validate with Pydantic, write per-comuna JSON
2. RSS News Pipeline (Python + DeepSeek) — fetch RSS feeds, classify incidents against closed 346-commune list, dedup, write rolling 30-day `incidents/current.json`
3. GitHub Actions Workflows — two separate cron jobs (quarterly CEAD, every 4-6h news); commit with GITHUB_TOKEN; conditionally POST to CF Deploy Hook
4. Astro SSG Site — generates ~750 HTML pages; embeds SEO-critical data in HTML; bundles Leaflet island for client-only hydration
5. Leaflet React Island — choropleth + incident pins; loads `map-payload.json` (~6-8 KB gzipped) and `current.json` client-side
6. Cloudflare Pages CDN — serves all static assets; Cache-Control: map-payload 1h, incidents 30min

### Critical Pitfalls

1. **Thin programmatic content deindexed by Google** — Every commune page must have 500+ words with 5+ unique data dimensions (rate vs. national/regional average, trend direction, dominant crime types, regional context, comparable commune). Deploy in batches of 10-20 first; verify GSC indexing before generating all 346.

2. **CEAD endpoint silently returns wrong data** — Validate after every scrape: expected keys present, commune count equals 346, rates within plausible bounds. Exit non-zero on failure; never commit bad data; keep previous good JSON intact.

3. **GitHub Actions → Cloudflare Pages infinite rebuild loop** — Disable CF Pages Git auto-build. Use GITHUB_TOKEN for all data commits. POST to Deploy Hook only when `git diff --staged --quiet` confirms data changed.

4. **LLM assigns incidents to wrong communes** — Supply the full 346-commune list in the DeepSeek prompt as closed valid values. Temperature 0.0. Reject incidents whose extracted commune name does not exactly match the canonical list.

5. **Frequency vs. rate ranking error** — Encode `rate_per_100k` as the canonical metric in the pipeline data contract; never sort by absolute counts. Apply a minimum population filter (10,000 residents) for national rankings.

## Implications for Roadmap

### Phase 1: Data Foundation — CEAD Scraper + Schema
**Rationale:** Everything quantitative depends on real CEAD data. The JSON schema must be defined before both pipeline and site consume it; changing it after both sides are built is expensive. This is the critical path.
**Delivers:** Per-comuna JSON files (346), per-region files (16), national aggregates, pre-aggregated map payload, Pydantic schema models, pipeline validation.
**Avoids:** Silent CEAD schema drift (Pitfall 2), frequency-vs-rate error (Pitfall 5) — bake validation in from day one.
**Research flag:** Live endpoint validation of exact POST parameters and response schema before pipeline implementation.

### Phase 2: Astro Site Shell + Programmatic Page Generator
**Rationale:** Once a single real `{id}.json` file exists, the full page generation machinery and bilingual routing can be built and validated. Content template must be defined before generating all 346 pages — fixing thin content after generation is costly.
**Delivers:** Astro project with i18n routing, `getStaticPaths()` for all 346×2 commune + 16×2 region pages, templates with 5+ unique data dimensions per page, hreflang, sitemap.xml, canonical tags.
**Uses:** Astro 6.4.x built-in i18n, `prefixDefaultLocale: false` (EN at root paths), @astrojs/sitemap.
**Avoids:** Thin content Google deindexing (Pitfall 1), hreflang misconfiguration — run hreflang validator on 5 sample pages before generating all 700+.

### Phase 3: Leaflet Map Island
**Rationale:** Depends on `map-payload.json` (Phase 1) and the GeoJSON boundary file. Geometry simplification must happen before building the island, not as a later optimization.
**Delivers:** Interactive choropleth with year and crime-type filters, commune popup panel, geolocation button.
**Uses:** Leaflet 1.9.x with native `L.geoJSON()`, quantile/log color scale, `client:only="react"` on the map island.
**Avoids:** Mobile map unusability — simplify GeoJSON to <100 KB with mapshaper; memoize style functions; test on real mid-range Android at 3G before declaring done.

### Phase 4: Editorial Pages + AdSense Setup
**Rationale:** Top editorial pages provide the content depth needed for Google indexing and AdSense approval. Methodology page must be live and indexed before AdSense application.
**Delivers:** 20 high-priority editorial pages (EN + ES), methodology page with subregistro caveat, legal pages (Privacy Policy, Terms, About, Contact), AdSense integration after first indexing wave.
**Avoids:** AdSense rejection, territorial stigmatization risk — define editorial style guide (no absolute superlatives) with automated build checks before template writing.

### Phase 5: RSS News Pipeline + Incident Pins
**Rationale:** Can only be built after the shared schema is stable (Phase 1) and the site can display incident pins (Phase 3). The news layer shares the commune taxonomy, so the canonical commune list must be finalized before the LLM prompt is written.
**Delivers:** RSS ingestion from BioBioChile, Cooperativa Policial, La Tercera Nacional; DeepSeek v4-flash classification and geolocation; two-pass deduplication; rolling 30-day `incidents/current.json`; incident pins on map with source links.
**Uses:** feedparser 6.x, openai SDK v1.x → `deepseek-v4-flash`, tenacity for retries.
**Avoids:** LLM commune hallucination, deduplication failure — closed-list classification, temperature 0.0, validate commune name before commit, manual audit of 50 extracted incidents before launch.
**Research flag:** RSS feed URLs for T13, 24Horas, Meganoticias, SoyChile are unconfirmed — validate at runtime; design per-feed graceful fallback.

### Phase 6: CI/CD Wiring + Cloudflare Pages Configuration
**Rationale:** Final step after both pipelines and site work locally. Must be configured before any cron jobs are enabled.
**Delivers:** `cead-scraper.yml` (quarterly cron), `news-pipeline.yml` (every 4-6h cron), conditional commit + deploy hook logic, Cloudflare Pages with Git auto-build DISABLED, Deploy Hook called explicitly only when data changed.
**Avoids:** Infinite rebuild loop — verify by checking CF Pages build count after first cron run.

### Phase Ordering Rationale

- CEAD Scraper before everything — the entire quantitative product has no content without it.
- Schema definition is part of Phase 1, not a separate phase — must be stable before Phases 2 and 5 consume it.
- Astro site (Phase 2) before the map island (Phase 3) — page generation must work before adding client-side interactivity; allows SEO crawling to begin on static pages.
- Editorial pages (Phase 4) before RSS pipeline (Phase 5) — AdSense approval needs indexed content; news pipeline adds LLM error risk that is easier to isolate once the core site is stable.
- CI/CD (Phase 6) last — avoids infinite loop risk during development.
- RSS pipeline (Phase 5) and CI/CD (Phase 6) can be partially parallelized: pipeline scripts can be built and tested locally during Phase 4.

### Research Flags

Phases needing deeper research during planning:
- **Phase 1 (CEAD Scraper):** Live endpoint validation of exact POST parameters and response schema before pipeline implementation.
- **Phase 5 (RSS Pipeline):** RSS feed URLs for T13, 24Horas, Meganoticias, SoyChile are unconfirmed — validate at pipeline-build time; design fallback paths.

Phases with standard patterns (skip research-phase):
- **Phase 2 (Astro Site):** Well-documented; follow STACK.md configuration exactly.
- **Phase 3 (Leaflet Map):** Standard patterns; STACK.md and PITFALLS.md cover all edge cases.
- **Phase 6 (CI/CD):** GITHUB_TOKEN loop-prevention is confirmed behavior; ARCHITECTURE.md workflow snippets are production-ready.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All major versions verified against npm registry and official docs June 2026; DeepSeek deprecation timeline confirmed |
| Features | HIGH (table stakes) / MEDIUM (RSS feeds) | Competitor analysis via direct site inspection; 4 of 8 RSS feed URLs need runtime validation |
| Architecture | HIGH | Loop-prevention confirmed via GitHub community discussion; CF Pages limits from official docs; schema design verified against Astro build-time memory constraints |
| Pitfalls | HIGH | Each pitfall sourced from documented incidents: Google thin-content policy, react-leaflet perf analysis, LLM geolocation research literature |

**Overall confidence:** HIGH

### Gaps to Address

- **CEAD live endpoint validation:** Confirm exact field names in current responses with a live test scrape before pipeline is built.
- **RSS feed URL confirmation:** Four outlets have unconfirmed RSS URLs; design graceful per-feed fallback (skip + log) so a broken feed does not block the whole pipeline.
- **AdSense approval timeline:** Research indicates data journalism sites pass manual review with a methodology page, but automated classifier behavior is not guaranteed; budget for one rejection + 30-day wait.
- **GeoJSON boundary file accuracy:** Prototype's `geo-data.js` (~222 KB) accuracy for all 346 comunas post-2020 boundary changes has not been validated; validate against CEAD's commune ID list during Phase 1.

## Sources

### Primary (HIGH confidence)
- Astro npm registry / official docs — v6.4.6 confirmed June 2026; i18n routing configuration
- Cloudflare Pages official limits docs — 20K file free limit, 500 builds/month, 25 MiB file max
- DeepSeek API docs — model IDs, base URL, deprecation timeline
- GitHub community discussion #74772 — GITHUB_TOKEN commit loop-prevention confirmed
- react-leaflet performance analysis (tmsvr.com) — GeoJSON re-render issue documented

### Secondary (MEDIUM confidence)
- Competitor direct inspection (CrimeGrade, SpotCrime, Numbeo, AreaVibes) — feature landscape
- BioBioChile and Cooperativa live RSS feed inspection — confirmed working feeds
- AirOps / Passionfruit / SEOmatic — programmatic SEO thin-content penalty documentation
- arXiv 2502.14660 — LLM implicit location extraction failure modes

### Tertiary (LOW confidence / needs runtime validation)
- FeedSpot Chile News RSS list — individual feed URLs need live validation
- La Tercera RSS — `?format=rss` pattern needs runtime test
- Emol RSS — appears deprecated; HTML scraping fallback documented

---
*Research completed: 2026-06-12*
*Ready for roadmap: yes*
