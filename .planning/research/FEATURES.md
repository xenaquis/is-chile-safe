# Feature Research

**Domain:** Composite crime/safety index + place comparator + A-vs-B programmatic SEO pages
**Milestone:** v2.0 — Composite Index, Comparators & Launch
**Researched:** 2026-06-19
**Confidence:** HIGH (composite index methodology — OECD, Numbeo, academic literature) / HIGH (comparator UX patterns — direct competitor analysis) / MEDIUM (A-vs-B SEO differentiation — verified with multiple programmatic SEO sources)

---

> **Scope note:** This file covers only NEW features for v2.0. All v1.x features
> (choropleth by rate/100k, 346 comuna pages, 16 region pages, crime-type ranking
> pages, news incident pins, methodology page, AdSense) are already shipped and are
> NOT re-researched here. The v1.0 competitor/RSS research is preserved at the
> bottom of this file under "Prior Research (v1.0)".

---

## Context: v2.0 Feature Tracks

Three tracks, one hard dependency chain:

| Track | Content | Depends On |
|-------|---------|------------|
| 1 — Composite Crime Index | Exposure-adjusted 0–100 index per comuna; SPD VHC homicide input; SII exposure denominator; index-driven choropleth | SPD + SII data (hardened in Phase 17 Wave 0) |
| 2 — Commune Comparator + A-vs-B SEO | Interactive 2–3-column comparator; programmatic long-tail pages ("Providencia o Ñuñoa?") | **Track 1 must ship first** — comparator headline number is the composite index |
| 3 — Go-live / Launch ops | CF deploy hook, live news run, GSC submission, AdSense activation | Existing code is ready; one human action (set CF_DEPLOY_HOOK_URL) unblocks all |

---

## Feature Landscape

### Table Stakes — Track 1: Composite Crime Index

Features users expect from any "safety index." Missing these = the index feels untrustworthy or meaningless.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Single numeric index per comuna on a bounded 0–100 scale | Any "safety index" must produce a number users can compare at a glance. No number = not an index. Numbeo, BestPlaces, NeighborhoodScout all use 0–100. | MEDIUM | Higher = more crime exposure (Numbeo convention). Round to integer for headline display; one decimal only in per-family comparator breakdown. |
| Labeled band (Very Low / Low / Moderate / High / Very High) | Raw numbers ("43.7") are meaningless without context. Every major index uses categorical bands to give instant orientation. | LOW | Five bands map to the existing 5-level choropleth color palette. Must be consistent across map popup, commune page, comparator page. |
| Per-family breakdown contributing to the index | Users ask "what type of crime drives this?" A black-box headline number alone erodes trust. Numbeo shows 15 subscores; BestPlaces shows sub-rates for violent/property. | MEDIUM | Show each CEAD crime family's weighted contribution. A bar or proportional indicator suffices. Ties to existing `by_family` data. |
| Inline methodology disclosure (not just /methodology) | When a composite number appears, lay users ask "what does this include?" Without at least a tooltip or one-sentence note, the number feels arbitrary. The OECD Handbook on Composite Indicators mandates this transparency. | LOW | "Composite of 7 crime families + SPD homicide, adjusted by economic exposure (SII 2024). See full methodology →". Pre-rendered static HTML. |
| Data year label on every index display | CEAD is annual. Showing a composite without a year misleads users about currency. | LOW | "2024 data, updated quarterly" — already a pattern on the site. |
| Rank on index (national + regional) | If there is a composite score, users immediately want to know "how does this compare to other comunas?" A score without rank context feels unfinished. | LOW | Reuse national_rank / regional_rank schema from existing commune JSON. |
| SPD homicide explicitly disclosed as an input | Homicide is the highest-severity crime and already a first-class category on the map (Phase 14). Disclosing it builds credibility. | LOW | Surface the SPD VHC source in the inline methodology note. Source already snapshotted in Phase 17 Wave 0. |
| Index shown in map popup / ResultPanel | If a user clicks a commune on the choropleth, they must see the index in the popup alongside individual rates. Hiding it behind navigation breaks the flow. | LOW | Extend existing ResultPanel component. Static value from commune JSON. |
| National + regional rank on the index | Score alone gives no relational context. Rank ("73rd safest of 346") is the single cheapest way to contextualize the number. | LOW | Derivable at build time from sorted index values. |

### Table Stakes — Track 2: Commune Comparator (Interactive)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Side-by-side comparison of at least 2 comunas | The defining feature of a comparator. Numbeo, AreaVibes, BestPlaces, City-Data all do minimum 2-up. Without it, there is no comparator product. | MEDIUM | Two-column layout. Three columns as enhancement (low incremental cost). |
| Composite index as headline row | The entire point of Track 1 is to produce a single comparable number. If the comparator does not show it prominently at the top, Track 1 has no visible payoff. Hard dependency. | LOW | Requires Track 1 complete. |
| Per-family crime rate breakdown, one row per family | Users comparing two places want to know "X is safer for property crime but worse for drugs." Row-by-row breakdown is table stakes for crime comparators. Highlight the row where the two comunas diverge most. | MEDIUM | Uses existing `by_family` data. |
| Trend indicator (improving / stable / worsening) per family | A snapshot without trend direction is incomplete. Trend arrows or mini-sparklines are standard in comparison UX. | MEDIUM | Computable from existing time-series data. |
| "Compare to national average" as a pseudo-option | BestPlaces, NeighborhoodScout, USAFacts all offer this. Most common user intent: "Is Providencia better or worse than average Chile?" | LOW | National average is already in the data pipeline. Treat as a virtual "column" or reference line. |
| Commune search with autocomplete | Without search, the comparator requires knowing an exact name. All major comparators use autocomplete. | MEDIUM | 346 comunas. Reuse existing commune directory / CUT lookup. Vanilla JS, no heavy library needed. |
| Pre-rendered static fallback content on the comparator page | The interactive tool is a React island; its content is client-only and invisible to Google. The comparator page itself must contain pre-rendered static content (description, how-to-use, featured-pairs list) to be indexable. | LOW | Standard Astro pattern: static HTML shell + `client:load` island. |

### Table Stakes — Track 2: A-vs-B Programmatic SEO Pages

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Unique composite index difference statement in prose | Every A-vs-B page must open with a real sentence like "Providencia (index: 31) shows lower composite crime exposure than Ñuñoa (index: 44) for 2024." Without it, the page is a swapped-slug template with no unique content — Google SpamBrain deindexes these. | LOW | Generated from data at Astro build time. |
| Per-family rate comparison table (with "lower" indicator per row) | The data table with both comunas side by side + a winner indicator per row is the content heart of a comparison page. AreaVibes and BestPlaces both do this. | LOW | Static build-time from commune JSON. All 7 values vary per pair. |
| Trend narrative per family in prose | Mechanically-generated but factual prose ("Providencia's robbery rate has fallen 18% since 2021 while Ñuñoa's has risen 4%") is the cheapest way to differentiate pages in the same template set. Trend direction and year crossover differ per pair. | MEDIUM | Requires a prose-template engine using real series data — not canned boilerplate. This is the primary thin-content prevention mechanism for this page type. |
| National rank for both comunas | "Providencia ranks #47 nationally; Ñuñoa ranks #89" — data that varies per pair and provides factual differentiation. | LOW | Already in commune JSON. |
| Regional context (same or different region + regional average) | "Both in Región Metropolitana — regional average index: 58" adds context and differs per pair. | LOW | Derivable from CUT at build time. |
| Bilingual output (ES + EN) | Site is bilingual from day one. English queries ("Providencia vs Nunoa crime") and Spanish queries both exist. | MEDIUM | Translate template strings; data values are locale-neutral numbers. |
| Internal cross-links: → each commune page + crime-family ranking pages | Comparison pages are discovery surfaces; without outbound links they are dead-ends that hurt crawl equity. | LOW | Add to static page template. |
| Canonical + hreflang tags, with A-vs-B / B-vs-A convention | Generating both directions (A-vs-B and B-vs-A) creates duplicate-signal issues unless one is canonicalized or suppressed. | LOW | Establish alphabetical-slug ordering convention: the page always orders the two slugs alphabetically in the URL. Only generate one direction. Self-canonical on that URL. |

### Table Stakes — Track 3: Go-Live / Launch Ops

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| CF_DEPLOY_HOOK_URL secret set + manual CF "Create deployment" | Without this, the production site is still the v1.0 prototype from before Phase 10–20 work. One human action (copy Deploy Hook URL from Cloudflare dashboard → paste into repo secret) unblocks all downstream steps. | LOW (human) | Documented in DEPLOYMENT.md. See memory `prod-deploy-hook-secret-gap`. |
| Live news pipeline run + 50-incident commune-assignment audit | The Phase 16 news pipeline has never run in production. Must validate commune assignment accuracy on real traffic before go-live. | LOW (human) | Needs DEEPSEEK_API_KEY set as repo secret. Then manually trigger `scrape-news.yml`. |
| GSC submission + sitemap ping | Without explicit sitemap submission, Google's crawl lag is 2–8 weeks. Submitting via GSC reduces this to days. | LOW (human) | Site already generates sitemap.xml via @astrojs/sitemap. |
| AdSense + Consent Mode activation | Monetization is gated on ADSENSE_ENABLED env var. Flip only after: (a) live deploy confirmed, (b) CI forbidden-language validator passes (hardened in Phase 20). | LOW (human + env var) | Consent Mode wiring is a pending todo (`adsense-consent-mode-phase6`). |

---

### Differentiators (Competitive Advantage)

Features beyond table stakes that create real competitive separation for v2.0.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Exposure-adjusted index using SII economic activity denominator | Standard per-100k uses resident population. Tourist-heavy or commercial comunas (Las Condes, Santiago Centro) look artificially dangerous because crimes happen to non-residents. Adjusting by SII empresas + trabajadores dependientes surfaces true exposure. No Chilean crime site does this. | HIGH | SII PUB_COMU.xlsb data snapshotted in Phase 17 Wave 0. Needs `pyxlsb`. Caveat: SII measures firm domicile, not foot traffic — disclose the limitation inline. |
| SPD VHC homicide as direct index input (not CEAD proxy) | CEAD homicide (grupo 101) undercounts. SPD Violencia Homicida Consumada (prevenciondehomicidios.cl) is the Fiscalía-validated official truth at comuna level, 2018–2025. No other public Chilean safety site uses SPD VHC directly. | MEDIUM | Parser needed; source already snapshotted in Phase 17 Wave 0. |
| Index-driven choropleth with toggle (index mode vs rate/100k mode) | Letting users switch between "composite exposure index" and "raw rate/100k for a crime family" on the same map is educationally powerful and differentiates from single-metric maps. Users who understand crime statistics can drill into raw rates; casual users see the composite. | MEDIUM | Toggle state in the Leaflet island. Two pre-computed color scales. `L.geoJSON` color function changes on toggle event. |
| 3-commune comparison | Most comparators stop at 2 columns. Adding a third covers the "I'm choosing between three neighborhoods" use case for expats, students, and relocation consultants. | LOW (incremental over 2) | Layout adds a third column. Data logic is identical. |
| "Compare to regional average" option | Most comparators offer only national average. Regional average is meaningful in Chile where crime patterns cluster by macro-region (RM vs Araucanía vs Atacama vs Antofagasta). | LOW | Regional aggregate already computed in pipeline. |
| Trend-aware prose on A-vs-B pages that differs per pair | Sentences like "Providencia's robbery rate fell 18% since 2021 while Ñuñoa's rose 4%" are factual, unique per page-pair, and not found anywhere else for Chilean comunas. This is the primary competitive moat against generic comparison-template sites. | MEDIUM | Requires prose-template engine reading real `series.by_family` trend data. |
| Bilingual A-vs-B static pages for a curated set of top-traffic pairs | "Providencia o Las Condes?", "¿Ñuñoa o Maipú?" are real queries with near-zero competition in either language. No competitor produces static bilingual comparison pages for Chilean comunas. | HIGH (volume + template) | Generate for rollout/editorial-priority pairs first (top ~100–200 pairs involving highest-traffic comunas). Do NOT generate all 346×345 pairs — see anti-features. |
| Methodology transparency inline on every composite index display | The OECD Handbook on Composite Indicators and academic literature agree: indices without inline methodology caveats lose public trust. Showing it inline (not just on /methodology) is rare among public-facing crime sites. Already done in v1.x for rates; extend to the new composite. | LOW | Tooltip or expandable "How is this calculated?" Pre-rendered in static HTML, not client-only. |

---

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Absolute "Safest / Most Dangerous" verdict on comparator or index page | Users want a simple answer. | Violates the locked editorial constraint. Creates legal/reputational risk. Inaccurate: a composite index with uncertainty cannot support a definitive verdict — PMC research shows ~30% of entities change star band year-to-year due to statistical noise alone. | Use relative framing: "X shows a lower composite exposure index than Y for the most recent available year." Never "X is safe." |
| All 346×345 = ~119,000 A-vs-B page pairs at launch | Maximum SEO footprint. | (a) Cloudflare Pages free tier is 20,000 files. 119K pages blows the limit immediately. (b) Most low-traffic pairs would be thin content — two very similar comunas produce near-zero variation in trend narrative and rank context. Google SpamBrain deindexes bulk identical-structure pages detected as doorway pages. | Generate only for rollout/editorial-priority pairs (top ~100–200 pairs involving the 40–50 highest-traffic comunas). Expand progressively after GSC confirms initial batch is indexing without thin-content signals. At 2 pages per pair (EN + ES) = 400 new pages for 200 pairs, well within 20K headroom. |
| Confidence intervals / error bars displayed on each index score | Statistically correct; the OECD Handbook recommends it. | For lay users (tourists, expats), "42.3 ± 8.1" creates confusion, not insight. PMC research on composite performance indicators shows confidence intervals can make the entire index feel meaningless ("between two and four stars" problem). Also: CEAD data has no statistical sampling uncertainty — the error is systematic (under-reporting), not random. | Display a data vintage caveat ("based on 2024 CEAD data, updated quarterly") + link to /methodology. Discuss systematic caveats (under-reporting) on the methodology page, not inline. |
| Real-time / live index updates | Users associate "live" with freshness and trust. | CEAD updates quarterly; SPD VHC is annual; SII exposure data is annual. The composite cannot update more frequently than its slowest input. Claiming real-time would be misleading. | State data vintage clearly. The news pin layer already provides the "what's happening now" freshness signal — keep the two layers separate in user communication. |
| User-configurable weighting sliders | Advanced users want to personalize ("I care more about property crime than violence"). | (a) Static pre-rendering cannot serve user-configured index values without client-only JS that makes the content invisible to Google. (b) Most users lack the domain knowledge to weight meaningfully — it creates false precision. (c) High complexity, minimal benefit. | Pre-compute one well-justified weighting scheme (see Composite Index Design below), explain it fully in /methodology, and expose the per-family breakdown so users can draw their own relative conclusions. |
| Raw crime counts (not rates) in the comparator | "Providencia had 3,240 robberies vs Ñuñoa's 1,820" feels concrete. | Counts mislead when comunas have different populations. Providencia (~140k residents) vs many comunas with 10–30k. Count comparisons make large comunas look dangerous for the wrong structural reason. Already an established pitfall in the project (STATE.md accumulated context). | Always rate/100k or composite index. Note the population of each comuna in the comparator for context. |
| Interactive A-vs-B comparator via URL parameters as the only SEO strategy | Simpler to build than N static pages. | URL-parameter content is not indexed by Google. The entire SEO value of A-vs-B pages comes from static pre-rendering. | Dual approach: static pre-rendered pages for top-N pairs (indexable, SEO job) + interactive React island for arbitrary on-the-fly comparison (UX job). Both coexist, serve different purposes, and must not replace each other. |
| Star ratings (1–5 stars) per commune instead of numeric index + bands | Stars are immediately intuitive for consumer contexts (Yelp, Google Maps). | (a) Stars imply a review/opinion, not a measurement. Crime data is not a product to rate. (b) Stars compress the 0–100 scale into 5 buckets, losing differentiation for comunas in the middle. (c) "2-star neighborhood" is editorial judgment the site explicitly avoids. | Use the labeled-band system (Very Low / Low / Moderate / High / Very High) — descriptive of crime exposure level, not evaluative of place quality. |
| Choropleth switching to show the raw composite score as fill color with no binning | "More accurate" representation without rounding. | Unbinned continuous scales are notoriously difficult to read on choropleths. Small polygon color differences become imperceptible. Cartographic literature consistently recommends 4–7 bins for choropleth data. | Use 5-band binning (matching the existing palette) for choropleth fill. Show the exact score in the popup for users who want the number. |

---

## Feature Dependencies

```
[Phase 17 Wave 0 data snapshots: SPD VHC homicide xlsx, SII PUB_COMU.xlsb]
    └──required by──> [Composite Crime Index (Track 1)]

[Composite Crime Index (Track 1)]
    └──required by──> [Commune Comparator — headline row]
    └──required by──> [A-vs-B pages — index difference statement]
    └──required by──> [Index-driven choropleth toggle]
    └──provides──> [composite_index, index_band, index_year fields in commune JSON]

[Existing commune JSON (by_family rates, series, national_rank, regional_rank)]
    └──enhances──> [Per-family breakdown in comparator]
    └──enhances──> [Trend-aware prose engine on A-vs-B pages]
    └──enhances──> [Rank context rows on A-vs-B pages]

[Composite Crime Index — locked commune JSON schema]
    └──required by──> [Track 2 implementation start]
    (Do not begin Track 2 before the index schema is locked)

[Interactive Comparator tool (React island, client:load)]
    └──complements──> [A-vs-B static SEO pages] (different user jobs: UX vs indexability)
    └──must coexist with──> [A-vs-B static pages] (they do not replace each other)

[A-vs-B URL convention (alphabetical slug ordering)]
    └──required by──> [Canonical + hreflang correctness]
    (Prevents A-vs-B / B-vs-A duplicate ranking-signal split)

[Go-live: CF_DEPLOY_HOOK_URL secret set]
    └──unblocks──> [Live news pipeline run]
    └──unblocks──> [GSC submission]
    └──unblocks──> [AdSense activation]

[Phase 20 forbidden-language CI validator]
    └──required by──> [AdSense activation] (must confirm no policy-violating language before flip)
```

### Dependency Notes

- **Track 1 before Track 2 (hard):** The comparator headline number and the A-vs-B page opening prose are both meaningless without a computed composite index. Do not begin Track 2 implementation before the Track 1 commune JSON schema is locked and populated.
- **Existing data is the foundation of Track 2:** The comparator and A-vs-B pages are primarily a presentation layer over already-hardened data (by_family rates, series, ranks). Track 2 is a new surface, not a new data pipeline.
- **Interactive comparator and static A-vs-B pages are distinct products:** The interactive tool answers exploratory "let me try arbitrary pairs" queries (client-side island, not indexed). The static pages answer specific "A vs B [place name]" search queries (pre-rendered, indexed). They must coexist.
- **A-vs-B volume is gated by Cloudflare free-tier:** 20,000 files total; existing build is ~792 pages (~19,200 headroom). At 2 pages per pair (EN + ES), the limit is ~9,600 pairs. Editorial-priority rollout (top ~200 pairs) uses 400 pages — well within budget.

---

## Composite Index Design Specifics

### Scale

Use **0–100 Crime Exposure Index** (higher = higher exposure, more crime relative to population/economic activity). This is the Numbeo convention and the most widely understood direction for a crime index among global users.

Five bands (matching existing 5-level choropleth palette):
- 0–20: Very Low
- 21–40: Low
- 41–60: Moderate
- 61–80: High
- 81–100: Very High

Display integer in headline contexts ("Santiago Centro: 67"). Display one decimal only in comparator per-family breakdown where fine differences matter.

### Exposure Denominator

Use SII `PUB_COMU.xlsb` (empresas + trabajadores dependientes per comuna) as the economic exposure proxy. This is imperfect — SII measures firm domicile, not actual foot traffic — but is the best available open Chilean dataset and is already snapshotted. Must disclose the limitation inline: "Exposure proxy: registered firms and workers per SII 2024 data; see methodology."

Alternative denominator (population from INE) remains available as a fallback if SII proves insufficient for some comunas.

### Weighting

Pre-compute one justified weighting scheme. Recommended approach: weight homicide highest (irreversibility of outcome; typically 3–5× weight vs property crime in academic composite indices), then violent crime families (vida/lesiones, robos violentos, armas, VIF), then property crimes, then incivilidades. Document exact weights in /methodology. Do NOT build user-configurable weight sliders.

### Anti-Spurious-Precision Rule

Never display more precision than the data can support. The composite index should be displayed as an integer in all headline, map popup, and band-label contexts. One-decimal precision is acceptable only in side-by-side comparator rows where a 0.3-point difference between two similar comunas is the meaningful signal.

---

## A-vs-B Page Content Specification (Anti-Thin-Content)

Industry consensus (verified with seomatic.ai, ultraseosolutions.com, blogseo.io): each programmatic page needs at minimum 3 "uniqueness blocks" where content varies meaningfully per page, beyond just the template variables. Pages with fewer meaningful variation points are classified as thin/doorway pages and deindexed.

For A-vs-B pages, the minimum uniqueness blocks are:

1. **Index difference statement** (varies per pair): "Providencia (index: 31) shows lower composite crime exposure than Ñuñoa (index: 44) as of 2024, placing it in the Low band vs Ñuñoa's Moderate band."
2. **Per-family comparison table** (all 7 rate values vary per pair): table with both comunas' rates + "lower" indicator per row. This alone is strong content because all 14 data cells differ.
3. **Trend narrative for at least one diverging family** (varies per pair): prose describing a family where the two comunas diverge in trend direction, with year and percentage. "While both comunas saw overall crime fall between 2019 and 2024, robbery in Providencia rose 12% over this period while Ñuñoa saw a 6% decline."
4. **National rank row** (varies per pair): both comunas' national rank on the index.
5. **Regional context** (varies per pair): same-region or cross-region flag + regional average.

Target: minimum 300 words of prose per page (excluding the table). The trend narrative is the primary prose differentiator and the most likely to pass Google's quality signals.

**Publication strategy:** Stage-publish in batches of 20 pairs and verify GSC indexing before expanding. Never launch all pairs at once (seomatic.ai: "Rushed publishing replicates systemic bugs across the entire program before detection").

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Composite index per comuna (0–100 + bands) | HIGH | MEDIUM | P1 |
| SPD VHC homicide as index input | HIGH | MEDIUM | P1 |
| SII exposure adjustment | HIGH | HIGH | P1 |
| Inline methodology disclosure on index | HIGH | LOW | P1 |
| Index in map popup / ResultPanel | HIGH | LOW | P1 |
| Index-driven choropleth toggle | HIGH | MEDIUM | P1 |
| National + regional rank on index | MEDIUM | LOW | P1 |
| Go-live: CF deploy hook + secrets (human) | HIGH | LOW (human) | P1 |
| 2-column interactive comparator | HIGH | MEDIUM | P1 (after Track 1) |
| A-vs-B static pages for top editorial pairs | HIGH | HIGH | P1 (after Track 1) |
| Trend-aware prose engine for A-vs-B | HIGH | MEDIUM | P1 (thin-content prevention) |
| Bilingual A-vs-B pages (EN + ES) | HIGH | MEDIUM | P1 |
| Per-family breakdown in comparator | HIGH | LOW | P1 |
| "Compare to national average" pseudo-column | MEDIUM | LOW | P2 |
| 3-column comparator | LOW | LOW | P2 |
| "Compare to regional average" option | MEDIUM | LOW | P2 |
| GSC submission + sitemap ping (human) | HIGH | LOW (human) | P1 |
| AdSense + Consent Mode activation (human) | MEDIUM | LOW (human) | P2 (after go-live confirmed) |
| A-vs-B expansion beyond top-N pairs | MEDIUM | HIGH | P3 (after GSC validation of initial batch) |

---

## Competitor Feature Analysis (v2.0 additions)

| Feature | Numbeo (global) | BestPlaces.net (US) | AreaVibes (US) | Our v2.0 Approach |
|---------|-----------------|---------------------|----------------|-------------------|
| Index scale | 0–100 (perception-based) | 100 = US national avg | 0–100 livability | 0–100 Crime Exposure Index (official counts, not perception) |
| Exposure adjustment | None | None | None | SII economic activity denominator — differentiator |
| Data source | User surveys | FBI UCR | Multiple | CEAD official + SPD VHC (official police counts + homicide truth) |
| Family breakdown | 15 survey questions | Violent / Property | Category breakdown | 7 CEAD families + SPD homicide |
| Trend display | YoY change shown | Historical comparison | YoY % | Trend arrows + sparklines (existing) + prose narrative on A-vs-B pages |
| Side-by-side comparator | Yes (2 cities, client-only) | Yes (2 cities) | Yes (2 cities + livability score) | 2–3 comunas + national average pseudo-column |
| A-vs-B static pages | None (client-only comparator) | None | None | YES — static bilingual pre-rendered pages (SEO gap in Chilean market) |
| Methodology transparency | Separate page only | Footnote | Minimal | Inline note on every index display + full /methodology (already built) |
| Locale | EN only | EN only | EN only | Bilingual ES/EN — unique in Chilean market |

---

## Editorial / Legal Constraint Checklist

Carry into every phase of v2.0. The CI validator (Phase 20) enforces the forbidden-language rule at build time.

- Never use absolute "seguro / peligroso / safe / dangerous" verdicts about any territory on any page
- Every displayed composite index number must cite: (a) the data year, (b) a link to /methodology
- A-vs-B pages must use relative framing ("X shows lower exposure than Y") not absolute verdicts
- Band labels describe crime exposure level, not place quality: "Moderate crime exposure" not "moderately dangerous neighborhood"
- SPD VHC and SII sources must be cited on every page that uses them as inputs (pattern from data/SOURCES.md)
- Hybrid rollout constraint: A-vs-B pages may only link to commune pages that are in the rollout set. If a pair involves a non-rollout commune, either omit the link to that commune's page or exclude the pair from the static set entirely. Never 404 to a non-existent commune page.
- Every programmatic page must contain real differentiated prose — the Astro build must refuse to generate pages that would produce fewer than N uniqueness blocks (enforce via build-time assertion, not manual review)

---

## Sources

- [Numbeo Crime Indices Explained](https://www.numbeo.com/crime/indices_explained.jsp) — scale 0–100, 5 bands, methodology, safety vs crime index duality (HIGH confidence)
- [OECD Handbook on Constructing Composite Indicators](https://www.oecd.org/content/dam/oecd/en/publications/reports/2008/08/handbook-on-constructing-composite-indicators-methodology-and-user-guide_g1gh9301/9789264043466-en.pdf) — normalization, weighting, transparency requirements for composite indicators (HIGH confidence)
- [PMC: The problem with composite indicators](https://pmc.ncbi.nlm.nih.gov/articles/PMC6559782/) — confidence interval communication pitfalls for lay users; ~30% of entities change band due to statistical noise alone (HIGH confidence)
- [PNAS/PMC: Activity-adjusted crime rates](https://pmc.ncbi.nlm.nih.gov/articles/PMC9674247/) — exposure denominator methodology using mobility data; why population alone misleads (HIGH confidence)
- [Seomatic: Programmatic SEO Mistakes](https://seomatic.ai/blog/programmatic-seo-mistakes) — thin content triggers, canonical configuration, intent mismatch (MEDIUM confidence)
- [UltraSEO: How Programmatic SEO Led to Google Deindexing](https://www.ultraseosolutions.com/how-programmatic-seo-led-to-google-deindexing-and-the-recovery/) — recovery case study; pages 95% identical = deindex risk (MEDIUM confidence)
- [BlogSEO: Programmatic SEO Quality Rules](https://www.blogseo.io/blog/programmatic-seo-quality-rules-avoid-thin-content) — 3-uniqueness-block minimum; data-first not template-first (MEDIUM confidence)
- [AreaVibes Crime Comparison](https://www.areavibes.com/crime-comparison/) — UX pattern reference: 2-city comparator, murder/assault/robbery/burglary/vehicle theft breakdown (MEDIUM confidence — landing page only, not results page)
- [BestPlaces Crime](https://www.bestplaces.net/crime/) — national-average-as-100 scale pattern, violent/property sub-rate breakdown (MEDIUM confidence)
- [Bridge Legal: What the Crime Index Means](https://bridgelegal.org/what-crime-index-means-how-it-is-used/) — lay user communication of crime indices; weighting approach (MEDIUM confidence)

---

## Prior Research (v1.0, 2026-06-12)

The v1.0 feature research (competitor landscape, RSS feed viability, v1.0 MVP feature set) is preserved below. This research informed Phases 1–17 which are now shipped.

<details>
<summary>v1.0 Feature Research (click to expand)</summary>

**Domain:** Crime-data visualization + programmatic SEO platform (bilingual, Chile-specific)
**Researched:** 2026-06-12

All features listed in the v1.0 research (choropleth map, CEAD scraper, RSS pipeline, programmatic commune/region pages, editorial pages, methodology page, AdSense integration, etc.) are now SHIPPED as of v1.2/v1.3. They are not re-listed here to avoid confusion with the v2.0 roadmap.

Key v1.0 finding preserved for context: **Comparison widget was listed as an anti-feature in v1.0** ("High UI complexity; users can open two tabs") and deferred as "Create static comparison pages for high-traffic pairs." This is now the explicit Track 2 goal for v2.0 — the anti-feature was correctly deferred, not rejected.

</details>

---

*Feature research for: Chile Safety Map v2.0 — Composite Index, Comparators & Launch*
*Researched: 2026-06-19*
