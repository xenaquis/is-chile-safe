# Roadmap — Chile Safety Map (ischilesafe.com)

_Last updated: 2026-06-15 — v1.1 Polish & QA shipped (Phases 7–9 archived); v1.2 active_

## Milestones

- ✅ **v1.0 MVP** — Phases 1–6 (shipped 2026-06-13) — full detail: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Polish & QA** — Phases 7–9 (shipped 2026-06-15) — full detail: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)
- 🔄 **v1.2 Map Fidelity, Findability & News** — Phases 10–17 (Phase 10 shipped 2026-06-15; re-scoped 2026-06-15 from live audit + IA spike; Phase 17 data-quality/traceability added 2026-06-18)

> ## ▶ AUTONOMOUS RUN ORDER (set 2026-06-18)
> Two phases remain. `/gsd-autonomous` must run them in this order:
> **1) Phase 17 — Data Quality, Source Traceability & Methodology** (focused;
> NO composite index / NO schema migration — see `17-CONTEXT.md` Scope Note),
> then **2) Phase 16 — News Activation** (API keys available → full scope incl.
> live run + DeepSeek/MiniMax A/B). Discuss artifacts are pre-staged
> (`17-CONTEXT.md`, `16-CONTEXT.md`) so discuss does not block. Use **BrowserOS**
> for the end-of-phase visual verification of both. The original ambitious
> composite-index work is deferred to **proposed Phase 18 — Composite Crime
> Index** (not in this run).

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1–6) — SHIPPED 2026-06-13</summary>

- [x] Phase 1: Data Foundation (4/4 plans) — CEAD scraper → validated per-comuna/region/national JSON schema
- [x] Phase 2: Astro Site + Programmatic Pages (6/6 plans) — bilingual static site, 740 SEO pages, 7 validators
- [x] Phase 3: Leaflet Map Island (4/4 plans) — choropleth + filters + commune panel + geolocation + incident-pin layer (visual UAT deferred)
- [x] Phase 4: Editorial Pages + AdSense (7/7 plans) — 20 editorial + 8 legal pages, forbidden-language gate (validator #9), env-gated AdSlot
- [x] Phase 5: RSS News Pipeline (4/4 plans) — RSS ingest + DeepSeek v4-flash closed-list classify + dedup + rolling incidents/current.json
- [x] Phase 6: CI/CD + Cloudflare Deployment (3/3 plans) — cron workflows + data-change-gated Deploy Hook + CI guard + DEPLOYMENT.md runbook

Full phase details, success criteria, and per-plan breakdown: **[milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)**
Audit: **[milestones/v1.0-MILESTONE-AUDIT.md](milestones/v1.0-MILESTONE-AUDIT.md)** (code-complete; live go-live = human gates in `DEPLOYMENT.md` + each phase's `*-HUMAN-UAT.md`)

</details>

<details>
<summary>✅ v1.1 Polish & QA (Phases 7–9) — SHIPPED 2026-06-15</summary>

- [x] Phase 7: E2E Review Pass (5/5 plans) — completed 2026-06-14
- [x] Phase 8: Bug Fixes & Data Correctness (5/5 plans) — completed 2026-06-15
- [x] Phase 9: UX / Readability / Accessibility Polish (5/5 plans) — completed 2026-06-15

Audit-flagged partials F-006 (ES region grammar) + WR-03 (hamburger keyboard) closed at milestone close (commit d9593a3); 09-VERIFICATION.md produced; 10/10 validators pass.

Full phase details, success criteria, and per-plan breakdown: **[milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)**
Audit: **[milestones/v1.1-MILESTONE-AUDIT.md](milestones/v1.1-MILESTONE-AUDIT.md)**

</details>

### v1.2 Map Fidelity, Findability & News

_Surfaced by the Phase-9 live review and re-scoped 2026-06-15 after a live BrowserOS audit + IA spike (spikes 001–003) + a DeepSeek/MiniMax news smoke test. Sequenced: geometry (10, done) → findability/comuna publishing (11) → home/IA + ranking SEO (12, 13) → homicide + crime-type SEO (14, 15) → news activation (16). The audit's core finding: the site has rich material but it is "lost" — only 12/346 comunas reachable, rankings don't link comunas, the news layer is built but dark._

- [x] **Phase 10: High-Resolution Commune Geometry** — Replace the 88KB heavily-simplified `communes.topo.json` with real commune boundaries so polygons read as actual comuna shapes for visual comparison; balance fidelity vs file size/Leaflet-canvas performance. (completed 2026-06-15; chilemapas GPL-3 source, 345KB raw / 85.6KB gzip, 346/0/0/0 join) [GEO-01, GEO-02]
- [x] **Phase 11: Publish All 346 Comunas + Comuna Finder** — Flip the rollout gate (12→346) so every comuna with CEAD data has a reachable page; build a searchable comuna directory (A–Z + by-region, accent-insensitive); wire region/crime ranking tables to link every comuna; sitemap covers all. Kills the "material perdido" orphan-page problem. [COMU-01, COMU-02, COMU-03] (completed 2026-06-15)
- [x] **Phase 12: Home / IA Redesign + Comuna Page Hub-and-Spoke** — Redesign the home around the approved Hybrid C+B framing (editorial/SEO-led + "busca tu comuna" search hero + map as first-class CTA); make each comuna page a hub that cross-links map ↔ regional ranking ↔ similar comunas ↔ crime-type rankings ↔ its news. Depends on Phase 11. [IA-01, IA-02, IA-03] (completed 2026-06-16)
- [x] **Phase 13: Ranking SEO Hardening** — Add OpenGraph + Twitter cards site-wide, `ItemList` JSON-LD on ranking tables and `BreadcrumbList` JSON-LD where breadcrumbs render, and tighten internal linking between rankings and comuna/region pages. Depends on Phase 11. [RSEO-01, RSEO-02] (completed 2026-06-16)
- [x] **Phase 14: Homicide as a First-Class Category** — Expose the existing per-commune `homicidios` data as its own map filter/layer + commune-panel breakdown (currently folded inside "vida"/Life crimes). (was Phase 11) [HOM-01, HOM-02] (completed 2026-06-16)
- [x] **Phase 15: Crime-Type SEO Ranking Pages** — Programmatic bilingual "las N comunas con más {delito}" ranking pages (homicide first), with correct internal linking, hreflang, sitemap, single H1, and `ItemList` JSON-LD. Depends on Phases 14 + 13. (was Phase 12) [CSEO-01, CSEO-02] (completed 2026-06-16)
- [ ] **Phase 17: Data Quality, Source Traceability & Methodology** — _(runs FIRST — see Autonomous Run Order)_ Verify every surfaced figure against its authoritative source (re-check the 4 anomalies, partial-year flags, range sanity → `17-DATA-QUALITY.md`); fix the wrong CEAD host (`ministeriointerior`→`minsegpublica`); build a canonical source registry (`data/SOURCES.md`) naming CEAD (casos policiales `tipoVal=1,2`), SPD homicide, SII exposure, Fiscalía secuestro; commit reproducible normalized source snapshots; rewrite methodology EN+ES with a **clickable link to every source**. FOCUSED — no composite index, no schema migration, no displayed-metric change (deferred to Phase 18). Wave 0 research complete. Depends on Phase 11. [DQ-01, DQ-02, DQ-03, DQ-04]
- [ ] **Phase 16: News Activation + Geolocation Redesign + Model A/B** — _(runs SECOND)_ Redesign news geolocation (LLM emits the comuna NAME → deterministic name→CUT lookup, not a raw CUT guess), build a labelled golden set + scoring to A/B DeepSeek vs MiniMax (env-configurable provider), run the pipeline for real (API keys available), link incidents to source ↗ AND to their comuna page, and add a dedicated news page. Depends on Phase 11 + Phase 17 (source registry/methodology authoritative first). [NEWS-01, NEWS-02, NEWS-03, NEWS-04]

## Phase Details

### Phase 10: High-Resolution Commune Geometry

**Goal**: Replace the heavily-simplified `communes.topo.json` (88KB) with real Chilean commune boundaries so polygons render as recognizable comuna shapes (coastline, real borders) for visual comparison on the map — while keeping the shipped asset within a file-size/performance budget that preserves smooth Leaflet-canvas rendering of all ~346 comuna polygons.
**Depends on**: Nothing (first v1.2 phase). Consumes/replaces the existing geometry asset wired into the Phase 3 Leaflet map island; output mirrored to `site/public/data/cead/geo/` and emitted to `dist/`.
**Requirements**: GEO-01, GEO-02
**Success Criteria** (what must be TRUE):

  1. `data/cead/geo/communes.topo.json` (and its `site/public/` mirror) is regenerated from an authoritative Chilean commune-boundary source (e.g. INE/BCN/IGM), covering every comuna present in the CEAD data, with each polygon keyed by the same commune code the map already joins on (no comuna dropped or mis-joined).
  2. Rendered polygons are visually recognizable as actual comuna shapes (coastline and inter-commune borders visible) versus the current blocky simplification — verified in a real browser on `/map/` and `/es/mapa/`.
  3. The shipped geometry asset stays within an agreed size/performance budget (target documented during research; tradeoff between fidelity and KB recorded), and the map retains smooth pan/zoom/hover with no perceptible interaction regression versus the current asset.
  4. The choropleth still colours every comuna that has CEAD data, the commune panel still opens for clicked polygons, and there are zero new browser console errors on the map pages.
  5. The regeneration is reproducible — a script or documented procedure produces the asset from the source data, so geometry can be refreshed rather than being a one-off manual artifact.

**Plans**: 3 plans
Plans:
**Wave 1**

- [x] 10-01-PLAN.md — Harden gates first: extend build integrity assertion (346/0 missing/0 orphan/0 dup vs index.json) + replace stale 100KB gate with dual ≤420KB raw / ≤140KB gzip budget in build script + validator [GEO-01, GEO-02]

**Wave 2** *(blocked on Wave 1 — shares build-topojson.mjs)*

- [x] 10-02-PLAN.md — Source swap + retune: commit chilemapas raw source (un-ignore), srcCodeToCut zero-pad code-join, visvalingam 10%/quantization 10000, regenerate+sync+validate chained [GEO-01, GEO-02]

**Wave 3** *(blocked on Wave 2 — verifies the shipped asset)*

- [x] 10-03-PLAN.md — Attribution credit in methodology EN+ES + HUMAN-UAT gate doc (visual recognizability + throttled-mobile perf) [GEO-01, GEO-02]

### Phase 11: Publish All 346 Comunas + Comuna Finder

**Goal**: Every comuna with CEAD data has a reachable, indexable page (no dead map clicks, no orphan rankings), and users can find any of the 346 in ≤2 interactions via a searchable directory — eliminating the "material perdido" problem where 334/346 comunas exist in data and on the map but have no page or link.
**Depends on**: Phase 10 (geometry). Touches `site/src/config/rollout.json` + `loadRolloutCuts()`, the comuna page templates, region/crime ranking tables, sitemap.
**Requirements**: COMU-01, COMU-02, COMU-03
**Success Criteria** (what must be TRUE):

  1. The rollout gate is lifted to all 346 comunas (or `ROLLOUT_ALL` equivalent): `/commune/[slug]` (EN) and `/es/comuna/[slug]` (ES) generate for every comuna with CEAD data; clicking any map polygon or ranking row reaches a real page (0 dead-links / 404s); the sitemap includes all comuna URLs in both locales.
  2. A searchable comuna directory exists (accent-insensitive search + A–Z and by-region views, 16 regions), linked from the nav and home; any comuna is reachable in ≤2 interactions; low-population comunas are included (they get a page even if excluded from rankings).
  3. Region pages and crime-type pages link every comuna in their ranking tables (no "Showing N of M — more coming soon" gating); thin-content is mitigated (each comuna page has sufficient unique data/prose + unique title/meta/canonical/hreflang), and a build validator asserts page count ≈ 346×2 and zero internal links to ungenerated comuna slugs.

**Plans**: 4 plans
Plans:
**Wave 0**

- [x] 11-01-PLAN.md — data.ts build-time memoization (build-timeout guard) + coverage.mjs scaffold + rollout.mjs 346/`=== 12` assertion update [COMU-01, COMU-03]

**Wave 1** *(blocked on Wave 0 — memoization must land before the rollout flip)*

- [x] 11-02-PLAN.md — Rollout flip: ROLLOUT_ALL=true committed build default via cross-env + un-gate the 4 ranking tables (region EN/ES, crime EN/ES) [COMU-01, COMU-03]

**Wave 2** *(blocked on Wave 1 — comuna pages must exist to link)*

- [x] 11-03-PLAN.md — Comuna directory (EN /communes/ + ES /es/comunas/): SSR full 346-link list (A–Z + by-region) + vanilla filter/toggle + nav + home links + i18n strings [COMU-02]

**Wave 3** *(blocked on Waves 0–2 — verifies the full phase)*

- [x] 11-04-PLAN.md — Register coverage.mjs in suite + full ROLLOUT_ALL build & validators (346×2 + directory + sitemap + zero orphans, <20 min) + human reachability checkpoint [COMU-01, COMU-02, COMU-03]

### Phase 12: Home / IA Redesign + Comuna Page Hub-and-Spoke

**Goal**: The site stops feeling scattered — the home presents the Hybrid C+B framing (validated in spike 001) and every comuna page is a hub that connects coherently to the rest of the site (spike 003).
**Depends on**: Phase 11 (comuna pages + finder must exist to link to). Reuses spike artifacts `.planning/spikes/001-home-hub-framing/` and `003-comuna-page-spokes/`.
**Requirements**: IA-01, IA-02, IA-03
**Success Criteria** (what must be TRUE):

  1. The home (EN `/` + ES `/es/`) is rebuilt on the Hybrid C+B framing: editorial/SEO-led above the fold (headline + lead "safest / highest incidence" rankings + guide cards), a prominent "busca tu comuna" search hero, and the national map as a first-class CTA; single H1, fully static/indexable, bilingual parity.
  2. Each comuna page is a hub cross-linking to: the map (centered on it), its regional ranking, similar/neighboring comunas, the per-crime-type rankings, and its geolocated news; with a breadcrumb Inicio › Comunas › Región › Comuna in both locales.
  3. A coherent navigation spine connects map ↔ comuna ↔ ranking ↔ region ↔ news in both locales; the primary nav includes "Comunas" (the directory); internal links are reciprocal and 404-free.

**Plans**: 6 plans
Plans:
**Wave 1** *(foundations: data helper + i18n + map focus param + finder ?q=)*

- [x] 12-01-PLAN.md — nearestComparables(cut,n) data helper + nav_rankings/footer-spine i18n strings + comuna directory honors ?q= on load (EN+ES) [IA-02, IA-03]
- [x] 12-02-PLAN.md — MapIsland.tsx reads ?cut= focus param after layer mount (D-08) [IA-02]

**Wave 2** *(pages — consume Wave 1; no file overlap, parallel-safe)*

- [x] 12-03-PLAN.md — Home rebuild on Hybrid C+B: new HomeLayout + index.astro EN/ES (search hero + two lead tables + map CTA + guide cards + condensed prose) [IA-01]
- [x] 12-04-PLAN.md — Comuna hub: upgraded breadcrumb + map/similar/crime-type spokes + regional-rank device, EN+ES (D-07/08/09/10) [IA-02]
- [x] 12-05-PLAN.md — Spine: Rankings nav + footer-spine row + new /rankings/ + /es/rankings/ index pages (D-12/13) [IA-03]

**Wave 3** *(gate — verifies the whole phase)*

- [x] 12-06-PLAN.md — spine.mjs validator (cross-link reciprocity + single-H1 + sitemap) + register in all.mjs + full build/validate gate + human map-focus smoke [IA-01, IA-02, IA-03]

### Phase 13: Ranking SEO Hardening

**Goal**: The ranking/editorial pages gain the SEO signals the audit found missing, without changing their content — richer SERP/social presentation and machine-readable rankings.
**Depends on**: Phase 11 (so internal links target real comuna pages). Touches `BaseLayout.astro` + ranking templates.
**Requirements**: RSEO-01, RSEO-02
**Success Criteria** (what must be TRUE):

  1. OpenGraph (og:title/description/image/url/type) and Twitter Card meta are injected site-wide via the base layout; validated present on sampled ranking, editorial, comuna, and region pages, with locale-correct values.
  2. `ItemList` JSON-LD wraps the ranking tables (rank position + comuna link + rate) and `BreadcrumbList` JSON-LD is emitted wherever a visual breadcrumb renders (region, crime-type, comuna pages); both validate against schema.org and a build check asserts their presence on sampled templates.

**Plans:** 3/3 plans complete

**Wave 1** *(foundation: validator + OG assets + JSON-LD lib — built before the behaviors they assert)*

- [x] 13-01-PLAN.md — Offline OG-PNG generator + 7 placeholder images, src/lib/jsonld.ts (buildItemList/buildBreadcrumb, rate OUT), new seo.mjs offline validator + register in all.mjs [RSEO-01, RSEO-02]

**Wave 2** *(RSEO-01: head meta — touches BaseLayout, must precede the JSON-LD array widen)*

- [x] 13-02-PLAN.md — OG/Twitter meta site-wide in BaseLayout + pageType prop, HomeLayout/EditorialLayout forwarding, per-type og:image, og:locale en_US/es_CL, og:type website/article [RSEO-01]

**Wave 3** *(RSEO-02: structured data — widens BaseLayout jsonLd emission, so sequential after Wave 2)*

- [x] 13-03-PLAN.md — Widen jsonLd to array-of-scripts (XSS escape preserved); ItemList (position+url+name, no rate) on home/region/crime/rankings/similar; BreadcrumbList on commune/region/crime EN+ES [RSEO-02]

### Phase 14: Homicide as a First-Class Category

**Goal**: Homicide is exposed as its own map filter/layer and commune-panel breakdown, rather than being folded inside the "vida"/Life-crimes family.
**Depends on**: Phase 10. Touches the map filters, choropleth payload, commune panel (`FiltersRow.tsx`, `ResultPanel.tsx`, map-payload build).
**Requirements**: HOM-01, HOM-02
**Success Criteria** (what must be TRUE):

  1. `homicidios` (featured subgroup 101) is selectable as its own map filter/layer with its own choropleth, distinct from "vida"; the data pipeline emits the homicide rate per comuna into the map payload.
  2. The commune detail panel shows a separate homicide figure/breakdown (not only the aggregated "vida" family), with the CEAD source + year cited; no regression to existing family rendering.

**Plans**: 6 plans
Plans:
**Wave 0** *(BLOCKING — live CEAD subgroup-101 confirmation gates all pipeline work)*

- [x] 14-01-PLAN.md — Confirm subgrupo[]=101 POST param live + rate/count request count + capture offline fixtures + RED test scaffold [HOM-01]

**Wave 1** *(blocked on 14-01 — implements against the confirmed param)*

- [x] 14-02-PLAN.md — fetch_subgroup_batch + schema + homicide accumulator loop (rate+count, 2005-2025) + map-payload homicide_rate; run scrape, populate data, re-verify 30KB budget [HOM-01]

**Wave 2** *(blocked on 14-02 — gates the data half before UI consumes it)*

- [x] 14-03-PLAN.md — Build validator Check 8/9 (homicide_rate in payload + Santiago featured_rates.homicidios) + sync data to site/public [HOM-01]

**Wave 3** *(blocked on 14-03 — Half B contract layer)*

- [x] 14-04-PLAN.md — buildStyleMapFromHomicide independent quantile scale + CommunaPayload type + bilingual homicidios label/def + data.ts type [HOM-01]

**Wave 4** *(blocked on 14-04 — wires the chip + map)*

- [x] 14-05-PLAN.md — 8th featured homicide chip in FiltersRow + MapIsland crimeIsHomicide branch (chip effect + year effect) [HOM-01]

**Wave 5** *(blocked on 14-05 — panel + human-verify)*

- [x] 14-06-PLAN.md — ResultPanel homicide figure (rate+count+CEAD year, non-alarmist zero-state) + chained build+validate + browser human-verify [HOM-02]

### Phase 15: Crime-Type SEO Ranking Pages

**Goal**: Programmatic bilingual "las N comunas con más {delito}" ranking pages (homicide first) capture long-tail SEO, correctly linked and indexable.
**Depends on**: Phase 14 (homicide data) + Phase 13 (SEO schema patterns).
**Requirements**: CSEO-01, CSEO-02
**Success Criteria** (what must be TRUE):

  1. Programmatic ranking pages exist for the priority crime types (homicide first) in both locales ("las N comunas con más {delito}" / "communes with the most {crime}"), with correct internal linking to comuna/region pages, reciprocal hreflang, and sitemap entries.
  2. Each page is static/indexable with a single keyword-focused H1, unique title/meta/canonical, and `ItemList` JSON-LD for the ranking; sober tone preserved (reported-incidence framing, sources cited).

**Plans**: 2 plans
Plans:
**Wave 1** *(foundation: seo.mjs SAMPLES + familyDefs methodology — built before the pages they assert/feed)*

- [x] 15-01-PLAN.md — Extend seo.mjs SAMPLES with crime-ranking first-subdir heuristic + add bilingual RANKING_METHODOLOGY_EN/ES (8 crime types, CEAD-cited, reported-incidence) [CSEO-01, CSEO-02]

**Wave 2** *(blocked on 15-01 — pages consume the methodology + are sampled by seo.mjs)*

- [x] 15-02-PLAN.md — EN /crime-ranking/[crime] + ES /es/ranking-delito/[crime] (8 crimes; homicide via featured_rates, families via by_family) + ItemList/Breadcrumb JSON-LD + reciprocal comuna homicide spoke + chained build/validate gate [CSEO-01, CSEO-02]

### Phase 16: News Activation + Geolocation Redesign + Model A/B

**Goal**: The built-but-dark news pipeline goes live with accurate comuna geolocation, the best-performing LLM provider chosen on evidence, and incidents surfaced and linked across the site.
**Depends on**: Phase 11 (comuna pages exist to link incidents to). Touches `pipeline/news/`, `data/incidents/`, the map incident layer, comuna pages.
**Requirements**: NEWS-01, NEWS-02, NEWS-03, NEWS-04
**Success Criteria** (what must be TRUE):

  1. Geolocation is redesigned so the LLM emits the comuna NAME (and region hint), resolved by a deterministic name→CUT lookup (mirroring the geometry re-key) instead of a raw-CUT guess; accuracy is measured against a labelled golden set and beats the current approach (the smoke test showed both DeepSeek and MiniMax pick the wrong CUT ~60–70% of the time when given bare codes).
  2. A labelled golden set (30–50 real incidents with ground-truth comuna + family) and a scoring script exist; the LLM provider is env-configurable; DeepSeek vs MiniMax are A/B-compared on comuna accuracy, family accuracy, latency, cost, and output reliability, and the winner is documented and wired as default.
  3. The pipeline runs for real (gated by the human go-live `DEEPSEEK_API_KEY`/`MINIMAX_API_KEY` step) producing `data/incidents/current.json`; the map incident layer and the comuna-page "recent incidents" section render real, correctly-geolocated incidents with no console errors.
  4. Each incident links to its source article ↗ AND back to its comuna page; a dedicated news/incidents page exists (bilingual); a data-freshness indicator ("updated …") is shown; all incidents cite and link the press source per editorial policy.

### Phase 17: Data Quality, Source Traceability & Methodology

**Goal**: Every quantitative figure on the site is verifiably correct and traceable to its *authoritative* source, and the methodology explicitly names and **links** each source — without re-architecting the metric. FOCUSED scope (re-scoped with user 2026-06-18); the composite index / schema migration is deferred to proposed Phase 18.
**Depends on**: Phase 11 (comuna pages). Wave 0 research COMPLETE (`17-WAVE0-RESEARCH-A.md`, `17-WAVE0-RESEARCH-B.md`, `17-CEAD-CATALOG.json`). Touches `site/src/pages/methodology.astro` + `es/metodologia.astro`, `pipeline/` (read-only verification + new fetch/normalize scripts), `data/` (new normalized source snapshots + `SOURCES.md`).
**Requirements**: DQ-01, DQ-02, DQ-03, DQ-04
**Success Criteria** (what must be TRUE):

  1. A `17-DATA-QUALITY.md` report verifies each surfaced metric/series against its authoritative source: the four anomalies (Providencia, Lo Barnechea, San Joaquín, Recoleta) are re-checked and explained (not silently carried); every surfaced figure that can be a partial/unconsolidated year is flagged; range/sanity checks pass; drug-scope (Ley 20.000 grupo 401) and casos-policiales (`tipoVal=1,2`) semantics are confirmed against the offline CEAD cache + Wave 0 facts. [DQ-01]
  2. A canonical source registry (`data/SOURCES.md`) lists, per data class, the authoritative source + exact endpoint/URL + vintage/coverage + licence + measure semantics: CEAD (host `cead.minsegpublica.gob.cl`, casos policiales), SPD homicide (VHC, comuna), SII exposure (`PUB_COMU.xlsb`), Fiscalía secuestro (regional). The wrong CEAD host (`cead.ministeriointerior.gob.cl`) is fixed everywhere it appears. [DQ-02]
  3. Methodology pages (EN `methodology.astro` + ES `es/metodologia.astro`) are rewritten with bilingual parity: correct CEAD host, casos-policiales/measure semantics, partial-year handling, low-count caveat, drug scope, and the floating-population denominator caveat; SPD/SII/Fiscalía are named as the authoritative sources for the figures they back; **every cited source has a working clickable link**; legal-safe tone preserved (forbidden-language validator #9 passes); verified in a real browser via BrowserOS (EN+ES). [DQ-03]
  4. Reproducible, attributed, normalized static snapshots of the new sources are committed under `data/` (homicides per comuna/year from SPD; empresas+trabajadores per comuna/year from SII; secuestro per región/year from Fiscalía), each with a fetch/normalize script in `pipeline/` and source attribution — reference-only, NOT wired to the displayed metric and NOT migrating the CEAD schema. Build + all validators pass (chained, OneDrive-safe). [DQ-04]

**Plans:** 3/5 plans executed

- [x] 17-01-PLAN.md — DQ-01 offline data-quality verification harness + `17-DATA-QUALITY.md` (wave 1)
- [x] 17-02-PLAN.md — DQ-04 reproducible SPD/SII/Fiscalía snapshot scripts + `data/snapshots/` (wave 1)
- [x] 17-03-PLAN.md — DQ-02 canonical `data/SOURCES.md` registry + terms-page host fix (wave 1)
- [ ] 17-04-PLAN.md — DQ-03 atomic bilingual methodology rewrite EN+ES, clickable sources (wave 2)
- [ ] 17-05-PLAN.md — verify gate: chained build+validate, dist host gate, BrowserOS, `17-VERIFICATION.md` (wave 3)

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Data Foundation | v1.0 | 4/4 | Complete | 2026-06-13 |
| 2. Astro Site + Programmatic Pages | v1.0 | 6/6 | Complete | 2026-06-13 |
| 3. Leaflet Map Island | v1.0 | 4/4 | Complete | 2026-06-13 |
| 4. Editorial Pages + AdSense | v1.0 | 7/7 | Complete | 2026-06-13 |
| 5. RSS News Pipeline | v1.0 | 4/4 | Complete | 2026-06-13 |
| 6. CI/CD + Cloudflare Deployment | v1.0 | 3/3 | Complete | 2026-06-13 |
| 7. E2E Review Pass | v1.1 | 5/5 | Complete    | 2026-06-14 |
| 8. Bug Fixes & Data Correctness | v1.1 | 5/5 | Complete    | 2026-06-15 |
| 9. UX / Readability / A11Y Polish | v1.1 | 5/5 | Complete   | 2026-06-15 |
| 10. High-Resolution Commune Geometry | v1.2 | 3/3 | Complete   | 2026-06-15 |
| 11. Publish All 346 Comunas + Comuna Finder | v1.2 | 4/4 | Complete   | 2026-06-15 |
| 12. Home / IA Redesign + Comuna Hub-and-Spoke | v1.2 | 6/6 | Complete    | 2026-06-16 |
| 13. Ranking SEO Hardening | v1.2 | 3/3 | Complete   | 2026-06-16 |
| 14. Homicide as a First-Class Category | v1.2 | 6/6 | Complete   | 2026-06-16 |
| 15. Crime-Type SEO Ranking Pages | v1.2 | 2/2 | Complete   | 2026-06-16 |
| 17. Data Quality, Source Traceability & Methodology | v1.2 | 3/5 | In Progress|  |
| 16. News Activation + Geolocation + Model A/B | v1.2 | 0/0 | Pending (runs 2nd) |  |

## Backlog

- **Phase 18 (proposed) — Composite Crime Index & Metric Redesign** (deferred from Phase 17 on 2026-06-18). The ambitious half of the original Phase 17: exposure-adjusted composite index using the SII denominator; switch the displayed homicide metric to SPD VHC (comuna-level); `featured_rates` → 7-metric schema migration (lesiones = CEAD grupos 103+104+105; add secuestro [region-level, Fiscalía]; drop the `vida` aggregate); multi-measure aggregation (denuncias/detenciones/aprehendidos, normalized per offence — D-AGG); index-driven choropleth + dual index+count display; re-validate the 4 anomalies post-redesign. **All sources already validated in Phase 17 Wave 0** (`phases/17-robust-crime-index/17-WAVE0-RESEARCH-A.md` + `17-WAVE0-RESEARCH-B.md`); snapshots committed in Phase 17 (DQ-04). Open research: S5b (comuna-level secuestro from the Fiscalía BED app). High-risk/large — do NOT run unattended; plan interactively.
- **999.1 — BUGFIX: Tarapacá comunas mis-assigned to Aysén/Los Ríos** (found 2026-06-15 during v1.1 close; pre-existing Phase-1 data issue). `region_id` stores an ambiguous 2-digit province code: Tarapacá (region 1) comunas carry `11`/`14`, which collide with the direct region numbers for Aysén (11) and Los Ríos (14). The region resolver (`region/[slug].astro` + `es/region/[slug].astro` `floor(n/10)` logic; `data.ts` `loadCommune`) therefore groups Iquique, Alto Hospicio (→ Aysén) and Pozo Almonte, Pica, Huara, Camiña, Colchane (→ Los Ríos) under the wrong region. Symptoms: 7 Tarapacá comuna pages show the wrong region (prose + breadcrumb + JSON-LD); Aysén & Los Ríos region pages list Tarapacá comunas; the Tarapacá region page resolves 0 comunas (empty). **Fix:** disambiguate region from the CUT itself (4-digit CUT `1xxx` ⇒ region 1; 5-digit `11xxx` ⇒ region 11) rather than from the stored `region_id`, then rebuild + re-validate region grouping, rankings, sitemap. Scope: data-layer; target v1.2.

## Open Human Go-Live Gates (launch checklist — not v1.1 scope)

- **INFRA-03** — live `ischilesafe.com` cutover via `DEPLOYMENT.md` (CF account + DNS + secrets). Unblocks everything below.
- **NEWS live audit** — run `pipeline/scrape_news.py` with real `DEEPSEEK_API_KEY` + 50-incident commune-hallucination audit.
- **EDIT/MON** — GSC submission of editorial pages; flip `ADSENSE_ENABLED` + wire AdSense Consent Mode after first indexing wave.
