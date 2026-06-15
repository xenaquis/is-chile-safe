# Roadmap — Chile Safety Map (ischilesafe.com)

_Last updated: 2026-06-13 after v1.1 milestone roadmap_

## Milestones

- ✅ **v1.0 MVP** — Phases 1–6 (shipped 2026-06-13) — full detail: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Polish & QA** — Phases 7–9 (completed 2026-06-15)
- 🔄 **v1.2 Map Fidelity, Findability & News** — Phases 10–16 (Phase 10 shipped 2026-06-15; re-scoped 2026-06-15 from live audit + IA spike)

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

### v1.1 Polish & QA

- [x] **Phase 7: E2E Review Pass** — Walk every page in the inventory (ES/EN) with BrowserOS MCP, sample programmatic pages, exercise map interactions, check mobile, produce REVIEW-E2E-FINDINGS.md (completed 2026-06-14)
- [x] **Phase 8: Bug Fixes & Data Correctness** — Resolve all Critical findings + fix console errors, broken links, data calculation bugs, and AdSlot CLS issues (completed 2026-06-15)
- [x] **Phase 9: UX / Readability / Accessibility Polish** — Apply UX, readability, editorial-tone, and a11y corrections surfaced by the review (completed 2026-06-15; review-feedback gap-closure for term clarity + internal links, larger items routed to v1.2)

### v1.2 Map Fidelity, Findability & News

_Surfaced by the Phase-9 live review and re-scoped 2026-06-15 after a live BrowserOS audit + IA spike (spikes 001–003) + a DeepSeek/MiniMax news smoke test. Sequenced: geometry (10, done) → findability/comuna publishing (11) → home/IA + ranking SEO (12, 13) → homicide + crime-type SEO (14, 15) → news activation (16). The audit's core finding: the site has rich material but it is "lost" — only 12/346 comunas reachable, rankings don't link comunas, the news layer is built but dark._

- [x] **Phase 10: High-Resolution Commune Geometry** — Replace the 88KB heavily-simplified `communes.topo.json` with real commune boundaries so polygons read as actual comuna shapes for visual comparison; balance fidelity vs file size/Leaflet-canvas performance. (completed 2026-06-15; chilemapas GPL-3 source, 345KB raw / 85.6KB gzip, 346/0/0/0 join) [GEO-01, GEO-02]
- [ ] **Phase 11: Publish All 346 Comunas + Comuna Finder** — Flip the rollout gate (12→346) so every comuna with CEAD data has a reachable page; build a searchable comuna directory (A–Z + by-region, accent-insensitive); wire region/crime ranking tables to link every comuna; sitemap covers all. Kills the "material perdido" orphan-page problem. [COMU-01, COMU-02, COMU-03]
- [ ] **Phase 12: Home / IA Redesign + Comuna Page Hub-and-Spoke** — Redesign the home around the approved Hybrid C+B framing (editorial/SEO-led + "busca tu comuna" search hero + map as first-class CTA); make each comuna page a hub that cross-links map ↔ regional ranking ↔ similar comunas ↔ crime-type rankings ↔ its news. Depends on Phase 11. [IA-01, IA-02, IA-03]
- [ ] **Phase 13: Ranking SEO Hardening** — Add OpenGraph + Twitter cards site-wide, `ItemList` JSON-LD on ranking tables and `BreadcrumbList` JSON-LD where breadcrumbs render, and tighten internal linking between rankings and comuna/region pages. Depends on Phase 11. [RSEO-01, RSEO-02]
- [ ] **Phase 14: Homicide as a First-Class Category** — Expose the existing per-commune `homicidios` data as its own map filter/layer + commune-panel breakdown (currently folded inside "vida"/Life crimes). (was Phase 11) [HOM-01, HOM-02]
- [ ] **Phase 15: Crime-Type SEO Ranking Pages** — Programmatic bilingual "las N comunas con más {delito}" ranking pages (homicide first), with correct internal linking, hreflang, sitemap, single H1, and `ItemList` JSON-LD. Depends on Phases 14 + 13. (was Phase 12) [CSEO-01, CSEO-02]
- [ ] **Phase 16: News Activation + Geolocation Redesign + Model A/B** — Redesign news geolocation (LLM emits the comuna NAME → deterministic name→CUT lookup, not a raw CUT guess), build a labelled golden set + scoring to A/B DeepSeek vs MiniMax (env-configurable provider), run the pipeline for real, link incidents to source ↗ AND to their comuna page, and add a dedicated news page. Depends on Phase 11. [NEWS-01, NEWS-02, NEWS-03, NEWS-04]

## Phase Details

### Phase 7: E2E Review Pass

**Goal**: Every page category in the site has been seen in a real browser (ES and EN), representative programmatic pages sampled, map interactions exercised, mobile viewport checked, and all findings are recorded in a single prioritised document.
**Depends on**: Nothing (first v1.1 phase); dev server running (`cd site && npm run dev`); BrowserOS MCP connected (port 9200).
**Requirements**: REVIEW-01, REVIEW-02, REVIEW-03, REVIEW-04, REVIEW-05
**Success Criteria** (what must be TRUE):

  1. All 12 EN editorial pages, 12 ES editorial pages, /map/ + /es/mapa/, and the legal pages (4 URLs: terms + privacy, each locale — verified count) have been navigated, screenshotted, and console-checked. (07-RESEARCH.md verified 12+12 editorial and 4 legal URLs, not the 10+10/8 anticipated in REQUIREMENTS.md; the missing-legal-pages gap is logged as a Polish finding, not a blocker.)
  2. A declared sample of programmatic pages (≥3 communes at high/mid/low population, ≥2 regions, ≥2 crime types, both locales) has been reviewed against the page template.
  3. Map dynamic interactions verified in browser: year filter, crime-type filter, commune panel (rate/trend/ranking/sparkline/families), search, geolocation, and incident layer in empty state — all without unhandled errors.
  4. Mobile viewport (~375px) checked on money pages and map: no horizontal overflow, map usable, touch targets visually adequate.
  5. `.planning/REVIEW-E2E-FINDINGS.md` exists with every finding tagged Critical / Warning / Polish, the affected page identified, a screenshot reference, and a concrete recommendation.

**Plans**: 5 plans
Plans:
**Wave 1**

- [x] 07-01-PLAN.md — Pre-flight (dev server port + BrowserOS tools) + editorial/map/legal inventory walk [REVIEW-01]

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 07-02-PLAN.md — Programmatic page sampling vs template (communes/regions/crime, both locales) [REVIEW-02]

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 07-03-PLAN.md — Map dynamic interactions on /map/ (filters/panel/search/geo/incident empty state) [REVIEW-03]

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 07-04-PLAN.md — Mobile viewport (375×812) money pages + map, overflow + usability check [REVIEW-04]

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 07-05-PLAN.md — Consolidate REVIEW-E2E-FINDINGS.md (severity/page/screenshot/recommendation) [REVIEW-05]

### Phase 8: Bug Fixes & Data Correctness

**Goal**: All Critical findings from the review are corrected and re-verified; console is clean on money pages; data calculations are accurate; AdSlot does not cause layout shift.
**Depends on**: Phase 7 (REVIEW-E2E-FINDINGS.md must exist)
**Requirements**: BUGFIX-01, BUGFIX-02, BUGFIX-03, BUGFIX-04, BUGFIX-05
**Success Criteria** (what must be TRUE):

  1. Zero browser console errors on all money pages (10 EN editorial + /map/) after fixes; any remaining warnings are triaged with written justification.
  2. All internal links (header, footer, cross-links, language switcher) resolve without 404; hreflang reciprocal pairs are correct (canonical self-references intentional and documented).
  3. Rates on commune/region/country pages use `loadNationalAverage` (not a summation); ranking is by rate per 100k; spot-checked figures match `data/cead/` source JSON.
  4. AdSlot containers reserve explicit height so no CLS occurs; with `ADSENSE_ENABLED=false`, no `adsbygoogle` element is visible in the DOM.
  5. Every finding marked Critical in REVIEW-E2E-FINDINGS.md is either resolved (with re-verification note) or explicitly escalated with justification; Warning findings are resolved or carry a written deferral reason.

**Plans**: 5 plans
Plans:
**Wave 1** *(disjoint files — run in parallel)*

- [x] 08-01-PLAN.md — F-005 rollout-row gating across the 4 ranking templates (region EN/ES, crime EN/ES) [BUGFIX-02]
- [x] 08-02-PLAN.md — i18n + a11y string fixes: F-001 ES H1 "Comuna" + F-007 ResultPanel close aria-label locale-aware [BUGFIX-05]
- [x] 08-03-PLAN.md — F-009 zero-JS mobile hamburger nav in PageHeader (+ nav_menu_open i18n string) [BUGFIX-05]
- [x] 08-04-PLAN.md — BUGFIX-04 AdSlot blank reserved-height placeholder (remove dashed border, keep gate + zero adsbygoogle) [BUGFIX-04]

**Wave 2** *(blocked on Wave 1 — verifies its output)*

- [x] 08-05-PLAN.md — Verification + closeout: console re-check, rate spot-check vs data/cead/, BUGFIX-05 finding ledger [BUGFIX-01, BUGFIX-03, BUGFIX-05]

### Phase 9: UX / Readability / Accessibility Polish

**Goal**: Money pages are easy to scan and pleasant to read in both languages; editorial tone is sober throughout; key a11y and SEO meta signals are present in sampled pages.
**Depends on**: Phase 7 (findings available); can run in parallel with Phase 8 for non-overlapping files.
**Requirements**: UX-01, UX-02, READ-01, READ-02, READ-03, A11Y-01, A11Y-02
**Success Criteria** (what must be TRUE):

  1. Every money page has exactly one H1; H2/H3 hierarchy is scannable; a new reader can understand the page purpose within ~5 seconds (verified by re-reading in browser after changes).
  2. DataCallout/StatCard components each communicate one clear idea with its source (CEAD + year cited); callout-to-prose redundancy identified in the review has been removed or consolidated.
  3. Editorial prose columns respect ~720px max width with paragraph rhythm; no wall-of-text sections remain on editorial pages.
  4. Each EN editorial page has a Spanish counterpart with equivalent content, structure, and tone; no sections are missing in either locale; absolute "peligroso/seguro" phrasing is absent site-wide.
  5. In sampled pages: colour contrast meets WCAG AA for the teal `#0f766e` palette, focus states are visible, images/icons have alt text, map controls have aria labels, `<title>` / meta-description / canonical / hreflang / JSON-LD (FAQPage where applicable) are present and valid.

**Plans**: 5 plans
Plans:
**Wave 1**

- [x] 09-01-PLAN.md — Foundation: hoist familyDefs, i18n strings, dual-surface RateTooltip, focus + prose CSS [UX-02, A11Y-01, READ-01]

**Wave 2** *(disjoint files — run in parallel)*

- [x] 09-02-PLAN.md — Map comprehension: legend numeric bands (D-03), panel rate tooltip (D-01) + multiplier/bar (D-04), family glossary affordance (D-02) [UX-02, A11Y-01]
- [x] 09-03-PLAN.md — Bilingual glossary pages (/glossary/, /es/glosario/) + ranking-table tooltip & cross-links [READ-03, A11Y-02, UX-02]
- [x] 09-04-PLAN.md — Editorial readability: ES methodology parity + heading/callout/tone audit on top editorial pages [READ-02, READ-03, UX-01, UX-02, READ-01]

**Wave 3** *(blocked on Wave 2 — verifies its output)*

- [x] 09-05-PLAN.md — Verification + closeout: build, route emission, tone/meta grep, human a11y/browser checkpoint [A11Y-01, A11Y-02, READ-03, UX-01]

**UI hint**: yes

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

- [ ] 11-02-PLAN.md — Rollout flip: ROLLOUT_ALL=true committed build default via cross-env + un-gate the 4 ranking tables (region EN/ES, crime EN/ES) [COMU-01, COMU-03]

**Wave 2** *(blocked on Wave 1 — comuna pages must exist to link)*

- [ ] 11-03-PLAN.md — Comuna directory (EN /communes/ + ES /es/comunas/): SSR full 346-link list (A–Z + by-region) + vanilla filter/toggle + nav + home links + i18n strings [COMU-02]

**Wave 3** *(blocked on Waves 0–2 — verifies the full phase)*

- [ ] 11-04-PLAN.md — Register coverage.mjs in suite + full ROLLOUT_ALL build & validators (346×2 + directory + sitemap + zero orphans, <20 min) + human reachability checkpoint [COMU-01, COMU-02, COMU-03]

### Phase 12: Home / IA Redesign + Comuna Page Hub-and-Spoke

**Goal**: The site stops feeling scattered — the home presents the Hybrid C+B framing (validated in spike 001) and every comuna page is a hub that connects coherently to the rest of the site (spike 003).
**Depends on**: Phase 11 (comuna pages + finder must exist to link to). Reuses spike artifacts `.planning/spikes/001-home-hub-framing/` and `003-comuna-page-spokes/`.
**Requirements**: IA-01, IA-02, IA-03
**Success Criteria** (what must be TRUE):

  1. The home (EN `/` + ES `/es/`) is rebuilt on the Hybrid C+B framing: editorial/SEO-led above the fold (headline + lead "safest / highest incidence" rankings + guide cards), a prominent "busca tu comuna" search hero, and the national map as a first-class CTA; single H1, fully static/indexable, bilingual parity.
  2. Each comuna page is a hub cross-linking to: the map (centered on it), its regional ranking, similar/neighboring comunas, the per-crime-type rankings, and its geolocated news; with a breadcrumb Inicio › Comunas › Región › Comuna in both locales.
  3. A coherent navigation spine connects map ↔ comuna ↔ ranking ↔ region ↔ news in both locales; the primary nav includes "Comunas" (the directory); internal links are reciprocal and 404-free.

### Phase 13: Ranking SEO Hardening

**Goal**: The ranking/editorial pages gain the SEO signals the audit found missing, without changing their content — richer SERP/social presentation and machine-readable rankings.
**Depends on**: Phase 11 (so internal links target real comuna pages). Touches `BaseLayout.astro` + ranking templates.
**Requirements**: RSEO-01, RSEO-02
**Success Criteria** (what must be TRUE):

  1. OpenGraph (og:title/description/image/url/type) and Twitter Card meta are injected site-wide via the base layout; validated present on sampled ranking, editorial, comuna, and region pages, with locale-correct values.
  2. `ItemList` JSON-LD wraps the ranking tables (rank position + comuna link + rate) and `BreadcrumbList` JSON-LD is emitted wherever a visual breadcrumb renders (region, crime-type, comuna pages); both validate against schema.org and a build check asserts their presence on sampled templates.

### Phase 14: Homicide as a First-Class Category

**Goal**: Homicide is exposed as its own map filter/layer and commune-panel breakdown, rather than being folded inside the "vida"/Life-crimes family.
**Depends on**: Phase 10. Touches the map filters, choropleth payload, commune panel (`FiltersRow.tsx`, `ResultPanel.tsx`, map-payload build).
**Requirements**: HOM-01, HOM-02
**Success Criteria** (what must be TRUE):

  1. `homicidios` (featured subgroup 101) is selectable as its own map filter/layer with its own choropleth, distinct from "vida"; the data pipeline emits the homicide rate per comuna into the map payload.
  2. The commune detail panel shows a separate homicide figure/breakdown (not only the aggregated "vida" family), with the CEAD source + year cited; no regression to existing family rendering.

### Phase 15: Crime-Type SEO Ranking Pages

**Goal**: Programmatic bilingual "las N comunas con más {delito}" ranking pages (homicide first) capture long-tail SEO, correctly linked and indexable.
**Depends on**: Phase 14 (homicide data) + Phase 13 (SEO schema patterns).
**Requirements**: CSEO-01, CSEO-02
**Success Criteria** (what must be TRUE):

  1. Programmatic ranking pages exist for the priority crime types (homicide first) in both locales ("las N comunas con más {delito}" / "communes with the most {crime}"), with correct internal linking to comuna/region pages, reciprocal hreflang, and sitemap entries.
  2. Each page is static/indexable with a single keyword-focused H1, unique title/meta/canonical, and `ItemList` JSON-LD for the ranking; sober tone preserved (reported-incidence framing, sources cited).

### Phase 16: News Activation + Geolocation Redesign + Model A/B

**Goal**: The built-but-dark news pipeline goes live with accurate comuna geolocation, the best-performing LLM provider chosen on evidence, and incidents surfaced and linked across the site.
**Depends on**: Phase 11 (comuna pages exist to link incidents to). Touches `pipeline/news/`, `data/incidents/`, the map incident layer, comuna pages.
**Requirements**: NEWS-01, NEWS-02, NEWS-03, NEWS-04
**Success Criteria** (what must be TRUE):

  1. Geolocation is redesigned so the LLM emits the comuna NAME (and region hint), resolved by a deterministic name→CUT lookup (mirroring the geometry re-key) instead of a raw-CUT guess; accuracy is measured against a labelled golden set and beats the current approach (the smoke test showed both DeepSeek and MiniMax pick the wrong CUT ~60–70% of the time when given bare codes).
  2. A labelled golden set (30–50 real incidents with ground-truth comuna + family) and a scoring script exist; the LLM provider is env-configurable; DeepSeek vs MiniMax are A/B-compared on comuna accuracy, family accuracy, latency, cost, and output reliability, and the winner is documented and wired as default.
  3. The pipeline runs for real (gated by the human go-live `DEEPSEEK_API_KEY`/`MINIMAX_API_KEY` step) producing `data/incidents/current.json`; the map incident layer and the comuna-page "recent incidents" section render real, correctly-geolocated incidents with no console errors.
  4. Each incident links to its source article ↗ AND back to its comuna page; a dedicated news/incidents page exists (bilingual); a data-freshness indicator ("updated …") is shown; all incidents cite and link the press source per editorial policy.

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
| 11. Publish All 346 Comunas + Comuna Finder | v1.2 | 1/4 | In Progress|  |
| 12. Home / IA Redesign + Comuna Hub-and-Spoke | v1.2 | 0/0 | Pending    |  |
| 13. Ranking SEO Hardening | v1.2 | 0/0 | Pending    |  |
| 14. Homicide as a First-Class Category | v1.2 | 0/0 | Pending    |  |
| 15. Crime-Type SEO Ranking Pages | v1.2 | 0/0 | Pending    |  |
| 16. News Activation + Geolocation + Model A/B | v1.2 | 0/0 | Pending    |  |

## Open Human Go-Live Gates (launch checklist — not v1.1 scope)

- **INFRA-03** — live `ischilesafe.com` cutover via `DEPLOYMENT.md` (CF account + DNS + secrets). Unblocks everything below.
- **NEWS live audit** — run `pipeline/scrape_news.py` with real `DEEPSEEK_API_KEY` + 50-incident commune-hallucination audit.
- **EDIT/MON** — GSC submission of editorial pages; flip `ADSENSE_ENABLED` + wire AdSense Consent Mode after first indexing wave.
