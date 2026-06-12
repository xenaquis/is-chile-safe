# Feature Research

**Domain:** Crime-data visualization + programmatic SEO platform (bilingual, Chile-specific)
**Researched:** 2026-06-12
**Confidence:** HIGH (competitor analysis via direct site inspection) / MEDIUM (RSS feed viability — confirmed structure, individual URL availability needs runtime validation)

---

## Competitor Landscape Reference

Sites analyzed: CrimeGrade.org, SpotCrime, AreaVibes/CrimeoMeter, Numbeo Safety, police.uk, NeighborhoodScout.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Interactive choropleth map | Every crime-data site has one; absence = "site is broken" | MEDIUM | Leaflet + Chile GeoJSON (~222 KB); prototype already exists |
| Crime rate per 100K residents (not raw counts) | Raw counts favor large cities; users know to expect normalized rates | LOW | CEAD provides both; rate is the correct default display |
| Filter by crime type | Users arrive with a specific concern (robbery, homicide, vehicle theft) | LOW | CEAD has 7 families / 22 groups; filter UI is standard |
| Filter by year | Crime trends over time are core use case; without year range, data feels stale | LOW | CEAD data 2005–present; year dropdown or slider |
| Territorial detail page per area | SpotCrime, CrimeGrade, AreaVibes all have per-city/neighborhood pages | MEDIUM | 346 comunas + 16 regions = programmatic pages; must be pre-rendered HTML |
| Year-over-year trend indicator | "Is crime going up or down?" is the #1 question; sparkline or % delta | LOW | Derive from CEAD time series; sparkline component exists in prototype |
| Ranking of areas by crime rate | "Safest/most dangerous cities" is a top search intent on all competitors | LOW | Sort CEAD data; one ranked list page covers this |
| Methodology / data-sources page | Without it, users and Google distrust the numbers | LOW | Explain CEAD, subregistro, rate formula, LLM classification |
| Mobile-responsive layout | >60% traffic from mobile in LatAm; non-responsive = useless for tourists | MEDIUM | Astro + responsive CSS; map needs touch-friendly controls |
| Bilingual content (ES + EN) | Chilean residents (ES) + tourists/expats (EN) are both target audiences | MEDIUM | hreflang, i18n routing, translated page templates; already planned |

### Differentiators (Competitive Advantage)

Features that set this product apart from generic international crime-map sites.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Real CEAD official data (not survey-based) | Numbeo is perception-based (922 respondents for all Chile); CEAD is actual police reports covering every comuna | HIGH | CEAD scraper is the core technical bet; endpoint stability is a risk |
| Recent incident pins from Chilean news (qualitative layer) | No competitor has cuali + cuanti for Chile; pins give the "what's happening now" that aggregate stats can't | HIGH | RSS pipeline + DeepSeek v4 classification + geolocation; most complex component |
| 346-comuna granularity | Competitors show Chile at country or major-city level only; we go to every municipality | MEDIUM | GeoJSON available; programmatic page template scales automatically |
| Sober editorial framing in Spanish | No "danger zone" labels; incidencia reportada language; built for Chilean legal/cultural context | LOW | Copywriting discipline, not a technical feature; differentiates from tourist-panic sites |
| Programmatic ES + EN SEO pages for all comunas | English travel-safety queries ("is Pucón safe") have zero dedicated competition; Spanish queries are thin too | MEDIUM | Astro static generation; 346 × 2 languages + regions + crime types = 800–1200 pages |
| Geolocation "show my comuna" | Instantly contextualizes data for local users without requiring them to know their municipality name | LOW | Browser Geolocation API + point-in-polygon lookup against GeoJSON |
| Desglose by crime family within each territorial page | Visitors want to know if an area has high theft vs high violence — aggregate index hides this | LOW | CEAD data already structured this way; panel UI exists in prototype |
| Time-series chart per area per crime type | Trend context beyond a single year figure; lets users see if 2023 spike was an anomaly | MEDIUM | CEAD has multi-year data; sparkline + expandable chart |

### Anti-Features (Deliberately NOT Building)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Absolute "safe" / "dangerous" labels or grades (A–F) | CrimeGrade uses A–F; users find it intuitive | Legal and reputational risk in Chilean context; label sticks to a place regardless of nuance; invites defamation claims from municipalities | Use relative ranking + percentile language: "incidencia 23% menor al promedio regional" |
| User-submitted incident reports (Waze-style) | High engagement, real-time data | Requires backend, moderation, anti-spam, legal liability for user content, and a user base to be useful — none of which exist at MVP | Defer to v2+; news RSS layer fills the qualitative gap without user moderation burden |
| Community comments / discussion threads | Increases dwell time | Same backend/moderation requirement; easily becomes a reputational liability for a crime-data site | Static editorial context on each page covers the "what does this mean" question |
| Crime victim likelihood calculator ("1 in 46 chance") | AreaVibes offers this; sounds precise | False precision from incomplete police data; subregistro in Chile is high; calculator implies accuracy the data doesn't support | Explain subregistro explicitly on methodology page; show trend, not probability |
| Downloadable CSV / data licensing | Niche audience, revenue potential | Low-priority for AdSense-monetized MVP; CEAD data is public anyway | Link to CEAD directly; add download as v2 feature if data-professional segment emerges |
| Newsletter / crime alert emails | SpotCrime's main retention hook | Requires email infrastructure, unsubscribe compliance (CAN-SPAM/GDPR), ongoing ops cost | Static site + browser bookmarks cover the use case for MVP; revisit if returning-user metric justifies it |
| Real-time / live crime feed | Users want "right now" data | CEAD updates quarterly at best; real-time requires police API access that doesn't exist publicly in Chile | News pins update every few hours via cron — that's the practical "recent" signal |
| App Store mobile app | Extends reach | Platform fees, review process, dual codebase, maintenance; web is indexable by Google | Progressive Web App (PWA) meta tags on the responsive web app is sufficient |
| Comparison widget (City A vs City B) | AreaVibes offers side-by-side comparisons | High UI complexity; users can open two tabs; comparison pages can be programmatically generated for top pairs instead | Create static "Santiago vs Valparaíso" editorial pages for high-traffic pairs |

---

## Feature Dependencies

```
[CEAD Scraper + Static JSON]
    └──required by──> [Choropleth Map]
    └──required by──> [Territorial Detail Pages (programmatic)]
    └──required by──> [Rankings Page]
    └──required by──> [Year-over-Year Trend]
    └──required by──> [Crime-type Breakdown Panel]

[Chile GeoJSON]
    └──required by──> [Choropleth Map]
    └──required by──> [Geolocation "show my comuna"]

[RSS Pipeline + DeepSeek Classification]
    └──required by──> [Incident Pins on Map]
    └──depends on──> [CEAD taxonomy] (crime-type classification must align)

[Astro Static Site + i18n Routing]
    └──required by──> [Programmatic SEO Pages (ES + EN)]
    └──required by──> [Editorial Pages]
    └──required by──> [hreflang + Sitemap]

[Programmatic SEO Pages]
    └──requires──> [CEAD Scraper + Static JSON] (data must exist before pages generate)
    └──enhanced by──> [Incident Pins] (adds recency signal to static pages)

[AdSense Integration]
    └──requires──> [Astro Static Site] (must be live and indexed first)
    └──blocked by──> [Absolute safety labels] (AdSense policy risk; avoid inflammatory content)
```

### Dependency Notes

- **CEAD Scraper is the critical path**: Everything quantitative depends on it. It must be built and validated before map or programmatic pages.
- **GeoJSON must be locked before map work**: The boundary file determines choropleth rendering and point-in-polygon geolocation. Use the existing prototype's `geo-data.js` unless a more accurate source is found.
- **RSS pipeline can be built in parallel with CEAD work**: The two data layers are independent. DeepSeek crime-type taxonomy should mirror CEAD crime families to enable eventual cross-layer filtering.
- **Programmatic pages require static JSON to be committed to the repo**: Astro build reads JSON at build time; GitHub Actions must run CEAD scraper before triggering page build.
- **AdSense approval requires real indexed content**: Do not integrate AdSense until at least the top 10 editorial pages are live and indexed.

---

## MVP Definition

### Launch With (v1)

Minimum needed to validate SEO demand and core user value.

- [ ] CEAD scraper producing committed static JSON for all comunas and regions
- [ ] Interactive choropleth map with year + crime-type filters
- [ ] Territorial popup/panel: rate, trend arrow, ranking, sparkline, desglose by crime family
- [ ] Programmatic pages for all 346 comunas + 16 regions in ES and EN (template-based, data-real)
- [ ] Top 10 editorial pages in EN (/, /chile-crime-map/, /is-chile-safe/, /is-santiago-safe/, /safest-cities-in-chile/, /methodology/ + 4 city safety pages)
- [ ] Top 10 editorial pages in ES (mirrors)
- [ ] Methodology page with source attribution, subregistro caveat, rate formula
- [ ] hreflang, sitemap.xml, canonical tags, meta descriptions on all pages
- [ ] Geolocation "identify my comuna" button
- [ ] RSS pipeline + DeepSeek incident classification + map pins (qualitative layer)
- [ ] AdSense integration (after first indexing wave)

### Add After Validation (v1.x)

- [ ] Expanded time-series chart (click sparkline to expand full multi-year chart per crime type) — add when average session depth warrants it
- [ ] Regional news outlet coverage (SoyChile regional feeds, El Rancagüino, La Prensa Austral) — add when national feeds are stable
- [ ] "Compare two comunas" editorial pages for top traffic pairs — add when keyword data shows demand

### Future Consideration (v2+)

- [ ] User-submitted incident reports — only after backend decision and user base exists
- [ ] Email crime alerts — only if returning-user rate justifies ops cost
- [ ] Data download / API licensing — only if data-professional segment emerges in analytics
- [ ] PWA / installable app meta — low-cost enhancement once core traffic is established

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| CEAD scraper + static JSON | HIGH | HIGH | P1 |
| Choropleth map with filters | HIGH | MEDIUM | P1 |
| Programmatic comunas/regions pages | HIGH | MEDIUM | P1 |
| Territorial detail panel (rate, trend, ranking) | HIGH | LOW | P1 |
| Editorial top-10 pages (EN + ES) | HIGH | LOW | P1 |
| Methodology page | HIGH | LOW | P1 |
| i18n + hreflang + sitemap | HIGH | MEDIUM | P1 |
| Geolocation "my comuna" | MEDIUM | LOW | P1 |
| RSS pipeline + incident pins | HIGH | HIGH | P1 |
| AdSense integration | MEDIUM | LOW | P1 (post-index) |
| Expanded time-series chart | MEDIUM | MEDIUM | P2 |
| Regional RSS outlets | MEDIUM | LOW | P2 |
| Compare-two-comunas pages | MEDIUM | LOW | P2 |
| Email alerts | LOW | HIGH | P3 |
| Data download / API | LOW | MEDIUM | P3 |
| User-submitted reports | LOW | HIGH | P3 |

**Priority key:** P1 = must have for launch | P2 = add post-validation | P3 = future consideration

---

## Competitor Feature Analysis

| Feature | CrimeGrade.org | SpotCrime | Numbeo | AreaVibes | Our Approach |
|---------|---------------|-----------|--------|-----------|--------------|
| Data source | ML on police records (US) | Police agencies + news (US/intl) | User perception surveys | CrimeoMeter + census | CEAD official stats + Chilean news RSS |
| Geographic granularity | Zip code / block level | Address-level | City-level (36 Chilean cities) | Neighborhood-level | Comuna-level (346 units) |
| Chile coverage | None | Minimal | Partial (major cities only) | None | Full national coverage |
| Interactive map | Yes (shaded areas) | Yes (pins by type) | No | Yes (heat map) | Yes (choropleth + incident pins) |
| Crime-type filter | Yes | Yes (8 categories) | No | Yes | Yes (CEAD 7 families / 22 groups) |
| Year filter / trends | Projections | Limited | 5-year window | Year-over-year % | Full 2005–present time series |
| Grading system | A–F grades | None | Crime Index score | A+ to F | Relative ranking + percentile; no letter grades |
| Programmatic SEO pages | Yes (US cities) | Yes (state-browse) | City pages | City pages | 346 comunas × 2 languages + regions + crime types |
| News / incident layer | No | Yes (main feature) | No | No | Yes (RSS + LLM classification) |
| Bilingual | No | No | Some (UI only) | No | Full ES + EN with separate page trees |
| Methodology page | Yes | Minimal | Yes (caveats noted) | Minimal | Yes (detailed, covers subregistro) |
| Mobile app | No | Yes (iOS + Android) | No | No | Responsive web; no native app |
| User reports | No | No | Yes (survey) | No | No (v2+) |

---

## Chilean News RSS Feed Viability

Research finding: RSS availability varies significantly by outlet. Treat as MEDIUM confidence — URLs need runtime validation before pipeline commit.

| Outlet | RSS Status | Confirmed Feed URL / Pattern | Crime/Police Coverage | Notes |
|--------|------------|------------------------------|-----------------------|-------|
| BioBioChile | Confirmed working | `https://www.biobiochile.cl/static/feed-rss` | HIGH — top item in live feed was a crime/judicial story | Chile's largest news network by traffic (22% preference). General feed includes police/crime mix. Category feeds may exist under `/lista/tag/` structure. |
| Cooperativa.cl | Confirmed (URL structure mapped) | País: `/noticias/site/tax/port/all/rss_3___1.xml` | HIGH — "Policial" and "Seguridad Ciudadana" are explicit subcategories | RSS-a-la-carta system at `/noticias/stat/rss/rss.html`. Policial feed: `rss_3_158__1.xml`. Seguridad Ciudadana: `rss_3_174__1.xml`. Prepend `https://www.cooperativa.cl`. |
| La Tercera | Confirmed (via FeedSpot) | Nacional: `https://www.latercera.com/canal/nacional/` (append `?format=rss` or test `/feed`) | MEDIUM — Nacional section includes crime stories (observed in feed) | No dedicated policial feed; nacional RSS mixes politics, crime, society. Full feed at `/rss.xml` also observed working in live fetch. |
| Emol.com | UNKNOWN — RSS broken | Attempts redirect to `/todas/`; no working XML found | MEDIUM — major outlet, crime is core coverage | El Mercurio group. RSS appears deprecated or moved. Use HTML scraping of `/nacional/` section as fallback, or skip and use other outlets. LOW priority to resolve before launch. |
| T13.cl | UNKNOWN — no RSS found | Tag pages exist: `/etiqueta/policial`, `/etiqueta/casos-policiales` | HIGH — dedicated "Bloque Policial" TV segment; active tagging | No `/rss` or `/feed` endpoint found. May need RSS bridge (e.g., RSS.app or Feedburner wrapper) or HTML scraping of tag pages. |
| 24Horas.cl | UNKNOWN — no RSS found | `/rss` returns 404 | MEDIUM | TVN digital. No confirmed feed URL. Same fallback options as T13. |
| Meganoticias.cl | UNKNOWN | `/temas/policial/` section confirmed active | MEDIUM — dedicated policial section | No RSS endpoint confirmed. HTML scraping of `/temas/policial/` is a viable fallback. |
| SoyChile.cl | UNKNOWN | Regional policial sections exist (e.g., `/arica/Policial/`) | MEDIUM — regional coverage, good for non-Santiago comunas | No RSS confirmed. WordPress-based sites sometimes expose `/feed`; test `soychile.cl/feed`. |
| El Mostrador | Likely WordPress | `elmostrador.cl/feed/` (standard WP pattern) | LOW — investigative/political; less crime-blotter | Included in FeedSpot Chile list but not confirmed active. |
| La Nación | Confirmed (FeedSpot) | `lanacion.cl/feed/` | LOW | Smaller outlet; lower traffic. Secondary source. |

**Recommended RSS pipeline priority:**
1. BioBioChile (`/static/feed-rss`) — confirmed, high crime coverage, highest traffic
2. Cooperativa Policial (`rss_3_158__1.xml`) — confirmed structure, dedicated crime feed
3. La Tercera Nacional (`/canal/nacional/` + `?format=rss` test) — confirmed, broad coverage
4. Emol fallback — HTML scraping of `/nacional/` section if RSS stays broken
5. T13 / 24Horas — RSS bridge or HTML scraping of tag pages; add in v1.x iteration

**Deduplication is mandatory**: BioBioChile and Cooperativa often pick up the same wire-service story. DeepSeek pipeline must deduplicate by URL-normalized headline + date before committing incident JSON.

---

## Sources

- CrimeGrade.org — direct inspection (2026-06-12)
- SpotCrime.com — direct inspection (2026-06-12)
- AreaVibes Los Angeles crime page — direct inspection (2026-06-12)
- Numbeo Chile crime data — direct inspection (2026-06-12), 922 survey respondents, last update 2026-05-29
- Cooperativa RSS-a-la-carta page (`/noticias/stat/rss/rss.html`) — direct inspection, feed URL structure confirmed
- BioBioChile live RSS feed (`/static/feed-rss`) — direct inspection, content confirmed crime-inclusive
- La Tercera RSS via FeedSpot and live feed fetch — confirmed nacional feed
- FeedSpot Chile News RSS Feeds list — secondary aggregator source
- SafeWise neighborhood safety tools overview
- police.uk methodology — NextCity and ONS sources

---

*Feature research for: Chile Safety Map / ischilesafe.com*
*Researched: 2026-06-12*
