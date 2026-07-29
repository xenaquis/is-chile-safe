# Project Research Summary

**Project:** Chile Safety Map - v2.0 Composite Index, Comparators and Launch
**Domain:** Bilingual crime-data visualization + programmatic SEO platform (Chile)
**Researched:** 2026-06-19
**Confidence:** HIGH

## Executive Summary

v2.0 builds three interdependent tracks on top of a fully shipped v1.3 codebase: (1) an exposure-adjusted composite crime index per commune (0-100 scale, 7 metrics, SPD VHC homicide as truth source, SII economic activity as exposure denominator); (2) an interactive commune comparator island plus a curated set of bilingual A-vs-B programmatic SEO pages built directly on that index; and (3) go-live / launch ops blocked by a single missing secret (CF_DEPLOY_HOOK_URL). The hard dependency is absolute: Track 2 cannot begin until the Track 1 index schema is locked and populated, because the comparator headline number and the A-vs-B opening prose both require a computed composite_index value per commune.

The recommended approach requires only one new Python dependency (scipy for winsorization) on top of the already-pinned stack. All index math runs in pandas + numpy + scipy in a new pipeline/build_composite_index.py script that is deliberately isolated from the stable CEAD scraper so if the index step fails, existing CEAD data still refreshes. The composite index must use percentile-rank or winsorized min-max normalization (never raw min-max) because confirmed micro-commune outliers (Sierra Gorda: 43,369 per-100k) would compress all other communes to the bottom of a raw min-max scale, producing a useless choropleth. The SII exposure adjustment is a genuine differentiator (no other Chilean crime site does this) but must be capped when sii_workers > ine_population * 10 to prevent HQ-domicile artifacts from distorting scores for Las Condes and similar business-district communes.

The highest editorial risk is that any composite score can function as an absolute safety verdict through ranking position and color alone, regardless of vocabulary. The P20 forbidden-language CI validator must be extended to catch "safest," "mas segura," "most dangerous," and "mas peligrosa" without a qualifying "reported," and every page displaying the index must render a mandatory caveat block in both languages. A-vs-B programmatic pages must be bounded to a curated priority-pair allowlist (~3,400 pairs x 2 locales = ~6,800 pages) to stay well under Cloudflare Pages 20,000-file free-tier limit and to avoid Google SpamBrain deindexing thin-content symmetric templates. The go-live sequence is gated: CF deploy hook first, Consent Mode implemented and verified before the ADSENSE_ENABLED flip, GSC sitemap submission immediately after first deploy.

---

## Key Findings

### Recommended Stack

The existing stack is sufficient for all three tracks. Only scipy>=1.13,<2 is added to pipeline/requirements.txt for scipy.stats.mstats.winsorize. numpy (already a transitive dep of pandas 2.3.3) provides all other index math. The frontend adds no new deps: the index-driven choropleth reuses the existing L.geoJSON() + chroma-js pattern; the comparator island uses React useState only; A-vs-B programmatic pages use the existing Astro getStaticPaths pattern. pyxlsb (SII .xlsb) and openpyxl (SPD VHC .xlsx) are already pinned and available.

**Core technologies (v2.0 roles):**
- scipy (new, pipeline only): winsorize per-metric distributions before min-max normalization
- pandas + numpy (existing): all index math, DataFrame groupby/merge, percentile/rank
- pydantic 2.x (existing): schema validation for composite index output; additive non-breaking field extension
- astro 6.4.6 + getStaticPaths (existing): generates ~6,800 A-vs-B pages at build time
- chroma-js 3.x + L.geoJSON() (existing): index-driven choropleth color scale, same pattern as current
- React useState (existing): comparator island, 2-3 selected communes, no state manager needed

Hard anti-additions confirmed by research: no scikit-learn, no D3.js, no react-leaflet GeoJSON component, no zustand/jotai, no react-query, no backend/database.

### Expected Features

**Must have (Track 1 - Composite Crime Index):**
- 0-100 Crime Exposure Index per commune, integer display in headline contexts
- Five labeled bands (Very Low / Low / Moderate / High / Very High) mapped to existing 5-level choropleth palette
- Per-family breakdown (7 families) showing each metric contribution to the index
- SPD VHC homicide as index input (M5), disclosed inline; CEAD grupo 101 preserved as featured_rates.homicidios for backward compatibility
- SII exposure adjustment with HQ-domicile caveat inline and on /methodology
- Mandatory caveat block on every page displaying the index (EN + ES)
- Index in map popup and ResultPanel; national + regional rank on composite index
- Index-driven choropleth with toggle (index mode vs rate/100k per family)
- Methodology page updated with composite formula, SPD switch, SII caveat

**Must have (Track 2 - Comparator + A-vs-B):**
- 2-column interactive comparator island (3 columns as low-cost enhancement)
- Composite index as headline row (hard dep on Track 1)
- Commune search with autocomplete (346 communes, vanilla JS)
- Pre-rendered static HTML shell on comparator landing page (island layered on top)
- A-vs-B programmatic pages: ~3,400 priority pairs x 2 locales = ~6,800 pages
- Minimum 5 uniqueness blocks per A-vs-B page (index diff statement, per-family table, trend narrative, national rank, regional context)
- Alphabetical slug ordering (A < B) to prevent duplicate-signal split; single canonical per pair
- Bilingual A-vs-B (EN + ES) with CUT-code URL slugs to avoid transliteration/accent issues
- hreflang reciprocity validator extended to cover A-vs-B pages
- Staged publication: 20-pair batches, verify GSC indexing before expanding

**Must have (Track 3 - Go-Live):**
- CF_DEPLOY_HOOK_URL secret set and verified with test push (step 1, not cleanup)
- Live news pipeline run + 50-incident commune assignment audit
- GSC sitemap submission immediately after first deploy
- Consent Mode v2 implemented (ad_storage: denied default) before AdSense flip

**Defer (v3+):**
- User-configurable weight sliders (static pre-rendering incompatible; false precision risk)
- Confidence intervals / error bars (confuses lay users; CEAD error is systematic not random)
- Real-time index updates (CEAD is quarterly; SPD VHC is annual)
- Star ratings (editorial judgment framing, not measurement)
- A-vs-B expansion beyond priority pairs (post-GSC validation of initial batch)

### Architecture Approach

The index pipeline is isolated as a new pipeline/build_composite_index.py script running after the CEAD scraper and before build_map_payload.py (extracted from scrape_cead.py). The three-step pipeline order (scrape -> index -> payload) is the GitHub Actions step sequence. Isolation ensures CEAD data refreshes even if index computation fails. All outputs are static JSON in data/; no runtime server is introduced.

**Major components:**
1. pipeline/build_composite_index.py (new) - reads comunas/*.json + snapshots + INE populations; winsorizes and normalizes 7 metrics; writes enriched comunas/*.json and data/cead/comparator_table.json (~86 KB raw / ~28 KB gzip)
2. pipeline/build_map_payload.py (extracted from scrape_cead.py) - reads enriched comunas/*.json; writes map-payload*.json with new ci field (composite index level 1-5; omitted for pre-2018 years)
3. site/src/components/ComparatorIsland.tsx (new) - React island; loads comparator_table.json as prop; lazy-fetches comunas/{CUT}.json for sparklines on demand; client:load on comparator pages only
4. site/src/pages/compare/[pair].astro + es/comparar/[par].astro (new) - getStaticPaths reads comparator_table.json; generates ~3,400 priority pairs each locale; proseEngine.buildComparisonProse() generates differentiated content
5. site/src/components/map/ChoroplethLayer.ts (modified) - adds ci to CommunaPayload; adds buildStyleMapFromCompositeIndex() for composite view toggle

Schema migration is additive and non-breaking: existing featured_rates fields remain intact; new fields (composite_index, spd_homicide_rate, sii_exposure_index) are added alongside with optional TypeScript types.

### Critical Pitfalls

1. **Normalization without winsorization collapses the choropleth (CI-2, CI-8)** - Sierra Gorda reaches 43,369 per-100k; raw min-max puts 95% of communes in bottom 20% of scale. Use scipy.stats.mstats.winsorize(limits=[0.01, 0.01]) then min-max, OR percentile-rank normalization. Add pytest assertion: index_scores.describe()["25%"] > index_scores.max() * 0.10.

2. **Composite index implies absolute safety verdict through information architecture alone (CI-1)** - a choropleth colored green-to-red, a ranking table sorted safest-to-most-dangerous, or a comparator saying "A is safer than B" all communicate a verdict without forbidden words. Frame as "composite reported-crime burden." Extend P20 CI validator to flag "safest," "mas segura," "most dangerous," "mas peligrosa" without qualifying "reported."

3. **A-vs-B page count explosion blows 20K Cloudflare free-tier limit (SEO-1)** - 59,685 pairs x 2 locales = 119,370 pages; 6x over limit. Use curated priority-pair allowlist (~3,400 pairs). Assert total_pages < 18,000 in Astro build. Existing build is ~792 pages; ~6,800 A-vs-B pages brings total to ~7,600.

4. **Schema migration breaks 5+ consumers of featured_rates (CI-6)** - commune panel, choropleth, Astro template, figure-registry validator, and pytest assertions all read featured_rates. Migration must enumerate all consumers, add TypeScript types, run @astrojs/check in CI, keep old fields present until all consumers are verified.

5. **CF_DEPLOY_HOOK_URL unset keeps production stale (GL-1) and AdSense Consent Mode missing risks ad suspension (GL-3)** - deploy hook must be set and tested before any v2.0 code is merged. Consent Mode v2 must be verified via Tag Assistant before ADSENSE_ENABLED is flipped. These are ordered prerequisites, not cleanup.

---

## Implications for Roadmap

The hard dependency chain is Phase 18 -> Phase 21 -> Phase 22. Go-live (Phase 22) can run in parallel with Phase 21 since it has no code dependency on the comparator.

### Phase 18: Composite Crime Index

**Rationale:** Hard prerequisite for all of Track 2. Cannot begin comparator or A-vs-B pages until the index schema is locked and comparator_table.json is written. All 8 composite-index pitfalls (CI-1 through CI-8) must be resolved here.

**Delivers:** pipeline/build_composite_index.py; enriched data/cead/comunas/*.json with composite_index, spd_homicide_rate, sii_exposure_index fields; data/cead/comparator_table.json; extracted pipeline/build_map_payload.py; updated map-payload*.json with ci field; choropleth composite view toggle; composite score in ResultPanel and commune pages; updated methodology page.

**Key decisions to lock in Phase 18 planning:**
- Normalization method: winsorized min-max (scipy) vs percentile rank; both acceptable; must be documented in SOURCES.md and /methodology
- Metric weights in composite_config.py: homicide highest (0.30 recommended), then violent families, then property, then incivilidades
- SII exposure cap threshold: sii_workers / ine_population > 5.0 triggers INE population fallback
- Reference year alignment: latest year where ALL three sources (SPD VHC, CEAD, SII) are available; pipeline assertion enforces this
- Display precision: integer in all headline contexts; one decimal only in comparator per-family rows

**Avoids:** CI-1, CI-2, CI-3, CI-4, CI-5, CI-6, CI-7, CI-8, GL-5

**Research flag:** Needs deeper research during planning. Normalization method decision, SII cap logic, and schema migration consumer enumeration are all high-risk with no existing project precedent. Recommend --research-phase 18.

### Phase 21: Commune Comparator + A-vs-B SEO Pages

**Rationale:** Requires Phase 18 complete (comparator_table.json as input). Track 2 is primarily a presentation layer over already-hardened data. The risk is SEO architecture (thin content, hreflang, page count) not data pipeline.

**Delivers:** ComparatorIsland.tsx; /compare/ and /es/comparar/ landing pages; ~6,800 A-vs-B programmatic pages for ~3,400 priority pairs; proseEngine.ts extended with buildComparisonProse(); internal links from commune pages to comparator; hreflang validator extended.

**Key decisions to lock in Phase 21 planning:**
- URL slug convention: CUT-code slugs (e.g., /compare/13110-vs-13119/) recommended to avoid transliteration and accent issues
- Priority-pair allowlist: Tier 1 (10 editorial communes x ~280 non-low-pop communes) + Tier 2 (top-50 x top-50); encoded in data/comparator-pairs.json before getStaticPaths is written
- Prose uniqueness minimum: 5 uniqueness blocks + 300+ words of non-swappable content; build-time assertion enforces this
- Staged publication: 20-pair batches; verify GSC indexing before expanding
- Internal linking: every commune page must link to 3-5 A-vs-B pairs involving that commune (SEO-4 prevention)

**Avoids:** SEO-1, SEO-2, SEO-3, SEO-4, CI-1, GL-5

**Research flag:** Standard Astro patterns are established on this project. The prose uniqueness engine (buildComparisonProse) and pair-selection allowlist logic are the main unknowns. Scope these two sub-problems in planning before committing to a page count.

### Phase 22: Go-Live / Launch Ops

**Rationale:** No code dependency on Phase 21. Can run in parallel. The CF deploy hook is the single human action unblocking all downstream production steps. Consent Mode must precede AdSense. GSC submission immediately after first deploy maximizes crawl speed.

**Delivers:** Production site live with v2.0 content; live news pipeline running; AdSense active with Consent Mode.

**Ordered steps (sequence matters):**
1. Set CF_DEPLOY_HOOK_URL secret in GitHub repo settings; verify with test push; confirm CF dashboard shows triggered build
2. Trigger manual CF deploy (or let deploy-on-code.yml fire)
3. Implement Consent Mode v2 (gtag consent default with ad_storage denied) + cookie banner
4. Verify with Google Tag Assistant: ad_storage denied fires on page load before consent
5. Live news pipeline run (DEEPSEEK_API_KEY as repo secret; trigger scrape-news.yml) + 50-incident commune audit
6. GSC submission: updated sitemap + URL Inspection for 5-10 representative A-vs-B pairs
7. Flip ADSENSE_ENABLED only after steps 1-6 confirmed
8. Monitor: verify rebuild loop not reintroduced (CF build count must not increment on data-only commits)

**Avoids:** GL-1, GL-2, GL-3, GL-4

**Research flag:** Standard patterns; no research phase needed. All steps documented in memory and PITFALLS.md.

### Phase Ordering Rationale

- Phase 18 before Phase 21 (hard): comparator_table.json and composite_index in commune JSON are Phase 18 outputs required as Phase 21 inputs. Building comparator templates before the index schema is locked guarantees a schema migration rework.
- Phase 22 parallel with Phase 21 (recommended): go-live ops have no code dependency. Setting the deploy hook and wiring Consent Mode can proceed while Phase 21 development is in progress so the first v2.0 deploy fires as soon as Phase 21 merges.
- A-vs-B staged publication after Phase 22 verification: generate the full priority-pair set in Phase 21 but publish in 20-pair batches, monitoring GSC coverage between each batch.

### Research Flags

Needs research:
- **Phase 18:** Normalization method (winsorized min-max vs percentile rank); SII cap logic; schema migration consumer enumeration; year-alignment assertion design
- **Phase 21:** Prose uniqueness engine design (buildComparisonProse must generate substantively different text per pair from real trend data); priority-pair allowlist generation logic

Standard patterns (skip research-phase):
- **Phase 22:** All steps are documented human actions; no new code patterns

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | requirements.txt and package.json read directly from repo; scipy winsorize API is stable; Cloudflare 20K limit confirmed |
| Features | HIGH | Competitive analysis covers Numbeo, BestPlaces, AreaVibes; OECD handbook on composite indicators; programmatic SEO thin-content research from multiple case studies |
| Architecture | HIGH | All file schemas read directly from repo; integration points derived from actual codebase; build order follows confirmed pipeline structure |
| Pitfalls | HIGH | All critical pitfalls derived from existing codebase state, STATE.md decisions, and prior v1.x lessons; not hypothetical |

**Overall confidence:** HIGH

### Gaps to Address

- **Normalization method final decision (Phase 18 planning):** Winsorized min-max and percentile-rank are both valid. Choice affects choropleth interpretation and must be locked before any index-driven template is written. Validate by running distribution check on actual featured_rates data.
- **Priority-pair allowlist exact count (Phase 21 planning):** The ~3,400-pair estimate must be computed from actual commune data (low_population flags, national_rank values) before getStaticPaths is written. Encode result in data/comparator-pairs.json as a planning artifact before Phase 21 execution begins.
- **SPD VHC 2025 reliability (Phase 18 execution):** Snapshot caveat flags 2025 data as partial and unconsolidated. Reference year must be 2024 at most until SPD confirms 2025 as final.
- **A-vs-B prose engine quality (Phase 21 execution):** buildComparisonProse() must produce genuinely different text per pair. Sampling check (10 random pairs) must be part of Phase 21 acceptance criteria before any A-vs-B pages are deployed.

---

## Sources

### Primary (HIGH confidence)
- pipeline/requirements.txt (direct read) - pandas 2.3.3, pyxlsb 1.0.10, openpyxl 3.1.5, pydantic 2.13.4 confirmed
- site/package.json (direct read) - astro 6.4.6, react 19.2.7, leaflet 1.9.4, chroma-js 3.2.0 confirmed
- data/cead/comunas/13101.json - confirmed featured_rates schema and series structure
- data/cead/map-payload.json - confirmed compact payload schema
- data/snapshots/spd_homicide.json - confirmed record schema + 2025 partial data caveat
- data/snapshots/sii_exposure.json - confirmed record schema + HQ-domicile caveat
- pipeline/cead/normalizer.py - confirmed CHIP_DEFS ordering (0=vida..6=incivilidades)
- .planning/STATE.md - Phase 17 Wave-0 decisions; tipoVal=1,2 rule; SII xlsb readable; SPD VHC column structure
- .planning/PROJECT.md - Phase 18 scope, SEED-001 hybrid rollout constraints, editorial communes
- CLAUDE.md - Cloudflare Pages 20K file limit, What NOT to Use, forbidden-language constraint
- OECD Handbook on Constructing Composite Indicators - normalization, weighting, transparency requirements
- PMC: The problem with composite indicators - confidence interval pitfalls; 30% of entities change band due to noise
- PNAS/PMC: Activity-adjusted crime rates - exposure denominator methodology

### Secondary (MEDIUM confidence)
- Numbeo Crime Indices Explained - 0-100 scale, 5 bands, methodology
- Seomatic: Programmatic SEO Mistakes - thin content triggers, canonical configuration
- UltraSEO: How Programmatic SEO Led to Deindexing - 95% identical pages = deindex risk
- BlogSEO: Programmatic SEO Quality Rules - 3-uniqueness-block minimum
- Memory entries: prod-deploy-hook-secret-gap, onedrive-build-artifacts-desync, i18n-localized-slug-pitfall, astro-script-no-expr-interpolation

---
*Research completed: 2026-06-19*
*Ready for roadmap: yes*