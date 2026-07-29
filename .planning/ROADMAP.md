# Roadmap — Chile Safety Map (ischilesafe.com)

_Last updated: 2026-07-29 — v2.1 News Intelligence, Map UX & Ops Hardening roadmap created (Phases 26–33, continuing from v2.0's last phase 25)_

## Milestones

- ✅ **v1.0 MVP** — Phases 1–6 (shipped 2026-06-13) — full detail: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Polish & QA** — Phases 7–9 (shipped 2026-06-15) — full detail: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Map Fidelity, Findability & News** — Phases 10–17 (shipped 2026-06-18) — full detail: [milestones/v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)
- ✅ **v1.3 Data Quality Hardening & Methodology** — Phases 19–20 (shipped 2026-06-19) — _(Phase 18 deliberately reserved for Composite Crime Index)_
- ✅ **v2.0 Composite Index, Comparators & Launch** — Phases 18, 21, 22, 23, 24, 25 (production live; Phase 22-03 GSC sitemap submission carried forward as a deferred human/manual task)
- 🔄 **v2.1 News Intelligence, Map UX & Ops Hardening** — Phases 26–33 (roadmap created 2026-07-29; not started)

> **Phase numbering note:** Phase 18 is the RESERVED slot for the Composite Crime Index (intentional gap in v1.3 which used 19 + 20). v2.0 used phases 18, 21, 22, 23, 24, 25 (there is no Phase 19/20 in v2.0 — those are archived v1.3 phases). **v2.1 continues sequentially from v2.0's last phase and starts at Phase 26.**

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
Audit: **[milestones/v1.0-MILESTONE-AUDIT.md](milestones/v1.0-MILESTONE-AUDIT.md)**

</details>

<details>
<summary>✅ v1.1 Polish & QA (Phases 7–9) — SHIPPED 2026-06-15</summary>

- [x] Phase 7: E2E Review Pass (5/5 plans)
- [x] Phase 8: Bug Fixes & Data Correctness (5/5 plans)
- [x] Phase 9: UX / Readability / Accessibility Polish (5/5 plans)

Full phase details: **[milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)**
Audit: **[milestones/v1.1-MILESTONE-AUDIT.md](milestones/v1.1-MILESTONE-AUDIT.md)**

</details>

<details>
<summary>✅ v1.2 Map Fidelity, Findability & News (Phases 10–17) — SHIPPED 2026-06-18</summary>

- [x] Phase 10: High-Resolution Commune Geometry
- [x] Phase 11: Publish All 346 Comunas + Findability
- [x] Phase 12: Home / IA Redesign + Hub-and-Spoke Cross-linking
- [x] Phase 13: Ranking SEO Hardening
- [x] Phase 14: Homicide as a First-Class Category
- [x] Phase 15: Crime-Type SEO Ranking Pages
- [x] Phase 16: News Activation
- [x] Phase 17: Data Quality + Source Traceability + Methodology

Full phase details: **[milestones/v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)**
Audit: **[milestones/v1.2-MILESTONE-AUDIT.md](milestones/v1.2-MILESTONE-AUDIT.md)**

</details>

<details>
<summary>✅ v1.3 Data Quality Hardening & Methodology (Phases 19–20) — SHIPPED 2026-06-19</summary>

- [x] Phase 19: Tech-Debt Sweep
- [x] Phase 20: Methodology & Sources Hardening

Audit: **[milestones/v1.3-MILESTONE-AUDIT.md](milestones/v1.3-MILESTONE-AUDIT.md)**

</details>

<details>
<summary>✅ v2.0 Composite Index, Comparators & Launch (Phases 18, 21, 22, 23, 24, 25) — production live</summary>

- [x] Phase 18: Composite Crime Index (8/8 plans, completed 2026-06-19)
- [x] Phase 21: Commune Comparator + A-vs-B SEO (4/4 plans, completed 2026-06-20)
- [x] Phase 23: ENUSC Communal Victimization Layer (4/4 plans, completed 2026-06-19)
- [x] Phase 22: Go-Live / Launch Ops (2/3 plans; production live; 22-03 GSC sitemap submission carried forward as a deferred human/manual task, not a v2.1 requirement)
- [x] Phase 24: Rankings UX — dynamic sortable tables + visual polish (3/3 plans, completed 2026-06-20)
- [x] Phase 25: UI/UX 360 remediation (9/9 plans, completed 2026-07-03)

Full phase details for 18/21/22/23/24/25 remain below in this file's Phase Details section (not yet archived to a separate milestone file).

</details>

### v2.1 News Intelligence, Map UX & Ops Hardening

**Per-phase execution protocol (mandatory, every phase 26–33):** research → plan → premortem → plan review by a **Fable** agent → implementation by **Sonnet** → code review by **Opus** → GSD validation. Phases are deliberately granular so each cycle stays inside one context.

**⚙️ AUTONOMOUS MODE (authorized 2026-07-29):** the milestone runs unattended under `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md` — model routing, gate amendments (MAPUX-05 human acceptance → Fable-proxy with deferred human review; CRON-01 live dry run → local simulation; SEC-01/05 settings items → deferred-live), hard safety rules (no `git push`, no `data/` mutation, no GitHub settings changes, Phase-26 LLM call budget), and the deferred-live list for the user's return. That directive supersedes any conflicting phrasing here while the run is unattended.

**Dependency graph:**

- Phase 26 (Event Clustering Spike) gates **only the clustering portions** of Phases 27 and 28. It does **not** block Phase 27's faceting work — Phase 27 has zero dependency on the Phase 26 outcome and must not be sequenced as blocked.
- Phase 27 (News Facet Data Model) has no dependency on Phase 26. It can start immediately, in parallel with Phase 26.
- Phase 28 (News Visualizer UI) depends on Phase 27 (consumes `newsFacets.ts`) and conditionally on Phase 26 (consumes `cluster_id`/`is_primary` only on GO; degrades gracefully to faceting-only on NO-GO per NEWSUI-05).
- Phase 29 (Map UX Design Loop) is independent of 26/27/28 and can run in parallel with them.
- Phase 29 **hard-gates** Phase 30 via a human acceptance gate — no map control-shell code changes happen before that gate passes.
- Phase 31 (Docs & Methodology Refresh) lands after Phases 26–30 so the methodology reflects the actual clustering GO/NO-GO outcome and the shipped map redesign.
- Phase 32 (Cron Consistency) audits the schedule surface after Phase 28 has wired clustering into the news pipeline (cost/latency changed), so it is sequenced late.
- Phase 33 (Security Posture) runs parallel with or immediately after Phase 32.

**Risk annotations:**

- **Phase 26 is the milestone's high-risk phase.** A false merge (two distinct crimes displayed as one incident) is a published factual error on a safety-information site — not merely a bug.
- **Phase 30 is a regression-risk phase.** `ChoroplethLayer.ts`, `IncidentPinLayer.ts`, and `LowZoomDotLayer.ts` are protected/untouched; the `?cut=` deep link must survive the rework unchanged, and no declarative react-leaflet layer component may be introduced.

**Carried-over deferred item (not mapped to any v2.1 phase):** v2.0 GL-04 / Phase 22-03 — Google Search Console sitemap submission. Human/manual, still outstanding, tracked but out of v2.1 scope.

- [x] **Phase 26: Event Clustering Spike** — GO/NO-GO on grouping multi-outlet coverage of the same real-world incident (completed 2026-07-29)
- [ ] **Phase 27: News Facet Data Model** — time/region/family facet indexes computed at build time, no dependency on Phase 26
- [ ] **Phase 28: News Visualizer UI** — filter/grouping UI on `/news/` + `/es/noticias/`, SSG-safe, clustered-event cards on GO
- [ ] **Phase 29: Map UX Design Loop** — iterative BrowserOS + Fable redesign of the map control shell, human acceptance gate
- [ ] **Phase 30: Map Control-Shell Rework** — implement the accepted design; Leaflet layer code untouched
- [ ] **Phase 31: Docs & Methodology Refresh** — methodology/sources/attribution brought current with everything shipped since v1.3 plus this milestone
- [ ] **Phase 32: Cron Consistency** — reconcile the whole schedule surface (secrets, retries, labels, freshness, race conditions)
- [ ] **Phase 33: Security Posture** — secrets hygiene, Actions permissions, SHA-pinning, dependabot, scraping courtesy

---

## Phase Details

### Phase 18: Composite Crime Index

**Goal**: Users can see each commune's overall crime exposure as a single 0–100 index score in the map, commune pages, and popup — computed from 7 hardened metrics with exposure adjustment — while every page maintains the editorial constraint that no absolute safety verdict is issued.
**Depends on**: Phase 17 / v1.3 (SPD VHC, SII, and CEAD snapshots hardened; SOURCES.md canonical; figure-registry zero-orphan passing)
**Requirements**: CI-01, CI-02, CI-03, CI-04, CI-05, CI-06, CI-07, CI-08, CI-09, CI-10
**Research flag**: Needs deeper research during planning — normalization method decision (winsorized min-max vs percentile rank), SII cap logic, schema migration consumer enumeration, year-alignment assertion design are all high-risk. NOT suitable for autonomous execution; plan interactively.
**Success Criteria** (what must be TRUE):

  1. A visitor to any commune page sees an integer 0–100 composite index score with its 5-band label ("Very Low" / "Low" / "Moderate" / "High" / "Very High") and the commune's national and regional rank on that index — accompanied by a mandatory bilingual caveat block disclosing the composite-of-reported-crime framing, data vintage, and SII firm-domicile limitation.
  2. The map choropleth offers a toggle between composite-index mode and the existing per-family rate mode; in index mode each commune polygon is colored by its 0–100 score using the 5-level palette, and clicking a commune shows the exact integer score in the popup.
  3. The pipeline's `build_composite_index.py` step runs in isolation after the CEAD scraper and writes `data/cead/comparator_table.json` without breaking the existing CEAD scraper if it fails; a pytest distribution assertion confirms the index spread (25th percentile > 10% of max score) proving winsorization or percentile-rank normalization was applied.
  4. The CI forbidden-language validator (extended in this phase) flags "safest / most dangerous / más segura / más peligrosa" without a qualifying "reported / reportado" qualifier, and `npm run validate` exits 0 on the full build — confirming no absolute verdict is emitted anywhere.
  5. `@astrojs/check` passes on all TypeScript types; every consumer of `featured_rates` (commune panel, choropleth, Astro templates, figure-registry validator, pytest) is verified non-breaking after the additive schema migration; EN + ES methodology pages document the formula, normalization method, SPD VHC switch, and SII exposure caveat with every new figure registered (figure-registry zero-orphan passes).

**Plans**: 5 plans + 3 gap-closure plans (18-06..18-08, post-verification)

  - [x] 18-01-PLAN.md — Composite index compute core: scipy + config + normalize/SII-cap/year-align + build_composite_index.py + comparator_table.json + tests
  - [x] 18-02-PLAN.md — Extract build_map_payload.py (ci field, 30 KB assertion); strip scrape_cead.py; three-step GitHub Actions order
  - [x] 18-03-PLAN.md — Choropleth index-mode toggle (default): ci on CommunaPayload + buildStyleMapFromCompositeIndex + MapIsland toggle + legend
  - [x] 18-04-PLAN.md — Index display surfaces: ResultPanel + EN/ES commune pages, integer score + bands + national/regional rank + always-visible caveat
  - [x] 18-05-PLAN.md — Editorial + docs gate: forbidden-language extension, F13/F14 figure-registry, SOURCES.md + methodology pages, full non-breaking validator suite
  - [x] 18-06-PLAN.md — Gap 1 (CI-05): key ResultPanel composite block on COMPOSITE_YEAR=2024 so the score/band/rank/caveat render in the default map view
  - [x] 18-07-PLAN.md — Gap 2 (CI-04/CI-08): correct SII cap docs (SOURCES.md + EN/ES methodology) to INE-fallback semantics matching D-03 and the code
  - [x] 18-08-PLAN.md — Gap 3 (CI-02): mask NaN before winsorizing in normalize_metric + NaN+outlier clip-point test

**UI hint**: yes

### Phase 21: Commune Comparator + A-vs-B SEO

**Goal**: Users can compare 2–3 communes side by side in an interactive island and find bilingual A-vs-B programmatic pages ("Santiago o Providencia?") that deliver substantively differentiated content built on the composite index — without exceeding Cloudflare's file limit or producing thin-content pages Google would deindex.
**Depends on**: Phase 18 (requires `comparator_table.json` and `composite_index` field in commune JSON; the comparator headline number and A-vs-B opening prose are direct consumers of Phase 18 outputs)
**Requirements**: CMP-01, CMP-02, CMP-03, CMP-04, CMP-05, CMP-06, CMP-07
**Success Criteria** (what must be TRUE):

  1. A user on the comparator landing page (`/compare/` / `/es/comparar/`) can type commune names with accent-insensitive autocomplete across all 346 communes and see a side-by-side panel showing composite index headline, per-family breakdown, trend indicator, and a "compare to national/regional average" column — all on a pre-rendered static HTML shell that is indexable by Google.
  2. A-vs-B programmatic pages (e.g. `/compare/13110-vs-13119/`) are generated from the curated priority-pair allowlist, use CUT-code slugs in alphabetical order (one canonical page per pair, no A-vs-B / B-vs-A duplication), carry reciprocal EN/ES hreflang, and include at least 5 uniqueness blocks (index difference statement, per-family rate table, trend narrative, national rank, regional context) totaling ≥ 300 words of non-swappable prose — verified by a build-time thin-content assertion.
  3. The full build (existing ~792 pages + A-vs-B additions) stays under 18,000 files as asserted at build time — safely within the Cloudflare Pages free-tier 20,000-file limit.
  4. Every commune page links to 3–5 relevant A-vs-B pairs involving that commune, and the hreflang reciprocity validator is extended to cover A-vs-B pages — all validators exit 0.
  5. A random sample of ≥ 10 A-vs-B pairs is acceptance-checked for prose quality before any pages are deployed; the first batch of ~20 pairs is published and GSC URL Inspection is verified before expanding to subsequent batches.

**Plans**: 4 plans
**UI hint**: yes

Plans:

**Wave 1**

- [x] 21-01-PLAN.md — Wave 0: same-region pair allowlist (5,031) + comparisonProse engine (≥300 non-swappable words) + avs-b-budget validator (<18,000 files) + 15 i18n keys
- [x] 21-02-PLAN.md — Comparator island (autocomplete + side-by-side + homicide row) + EN/ES static landing shells + Compare nav link
- [x] 21-03-PLAN.md — A-vs-B programmatic pages (EN/ES, thin-content gate) + commune-page cross-links + hreflang/spine validator extensions

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 21-04-PLAN.md — Register budget validator + full 14/14 suite green + ≥10-pair prose acceptance + staged batch GSC verification

### Phase 22: Go-Live / Launch Ops

**Goal**: The production site at ischilesafe.com reflects v2.0 content, automated deploys fire on code pushes, the live news pipeline is running with a verified commune-assignment audit, and the URL is submitted to Google Search Console — all without activating AdSense (deferred).
**Depends on**: Nothing (no code dependency; can run in parallel with Phase 21 — start once CF_DEPLOY_HOOK_URL secret is set)
**Requirements**: GL-01, GL-02, GL-03, GL-04
**Note**: AdSense activation + Consent Mode v2 are explicitly deferred out of v2.0 scope. Do not include them in success criteria or planning.
**Success Criteria** (what must be TRUE):

  1. `CF_DEPLOY_HOOK_URL` is set as a GitHub Actions secret and verified — a test push to `master` triggers a build visible in the Cloudflare dashboard, confirming automated deploys are live.
  2. The production site at ischilesafe.com serves the v2.0 build from `master`, and the rebuild-loop guard is confirmed intact — a data-only commit (touching `data/**` only) does NOT increment the Cloudflare build count.
  3. A live news pipeline run executes via `scrape-news.yml` (using `DEEPSEEK_API_KEY` repo secret) and a 50-incident commune-assignment hallucination audit confirms the name→CUT resolver is performing at acceptable accuracy in production.
  4. An updated sitemap is submitted to Google Search Console immediately after the first v2.0 deploy, with URL Inspection run on 5–10 representative commune pages and A-vs-B pages confirming they are indexable.

**Plans**: 3 plans

- [x] 22-01-PLAN.md — Set CF_DEPLOY_HOOK_URL secret; verify code-push deploy fires + production serves v2.0; confirm rebuild-loop guard (GL-01, GL-02)
- [x] 22-02-PLAN.md — Scored 50-incident commune-assignment audit + live News Pipeline run (GL-03)
- [ ] 22-03-PLAN.md — Confirm v2.0 sitemap live; submit to GSC + URL Inspection on representative pages (GL-04) — **carried forward as a deferred human/manual task, not a v2.1 requirement**

### Phase 23: ENUSC Communal Victimization Layer

**Sequence note**: Runs **BEFORE Phase 22 (Go-Live)** — the SEED-002 motivation is to not launch infra-representing reported crime. Numbered 23 (sequential), sequenced ahead of 22.
**Goal**: Each of the 136 ENUSC-covered comuna pages additionally displays INE's ENUSC 2024 communal household violent-crime victimization (VHDV) figure as a clearly-labeled experimental / SAE-modeled estimate shown **alongside (never merged into)** the CEAD composite index, while the 210 uncovered comunas degrade gracefully to an explicit "no estimate" caveat — robustifying the site against reported-crime infra-representation **without altering any Phase-18 locked decision**.
**Depends on**: Phase 18 (composite index, F-series figure registry zero-orphan, SOURCES.md discipline) and Phase 17 (name→CUT resolver)
**Origin**: SEED-002 feasibility study (Design A) — `.planning/research/SEED-002-FINDINGS.md`, spikes 004–007
**Requirements**: VL-01, VL-02, VL-03, VL-04, VL-05
**Key constraints**: additive/versioned only (composite + all Phase-18 outputs byte-unchanged); comuna unit = 346; CEAD rates already per-100k (do not rescale); ~$0 infra; EN/ES parity; SEO-static; never an absolute seguro/peligroso verdict; every figure attributed + caveated.
**Ingestion decision** (user-approved): **manual/assisted annual versioned snapshot** of the ENUSC SAE VHDV Excel checked into the repo with provenance (source URL, retrieval date, INE experimental disclaimer, checksum) — **not** a brittle recurring cron scraper.
**Success Criteria** (what must be TRUE):

  1. A new isolated pipeline step ingests the ENUSC 2024 SAE VHDV Excel from a versioned in-repo snapshot into a data artifact with provenance (source URL, retrieval date, INE experimental disclaimer, checksum); it runs after the CEAD scraper and fails gracefully without breaking the CEAD pipeline if absent/malformed.
  2. The 136 covered comunas map to valid CUT codes (reusing the existing name→CUT resolver); a build-time assertion confirms every ingested row resolves to a valid CUT and the coverage count equals the published N (~136); unresolved rows fail the build loudly.
  3. Each covered comuna page (EN + ES) shows the VHDV victimization figure with value + reference year (2024) + a mandatory bilingual caveat labeling it an INE experimental, SAE-modeled estimate distinct from CEAD reported-crime — never an absolute verdict; the forbidden-language validator exits 0.
  4. The 210 non-covered comunas render an explicit bilingual "no ENUSC victimization estimate for this comuna (coverage: 136 comunas)" note with no broken layout and no implied value.
  5. Every new figure is registered in the F-series figure registry (zero-orphan passes) and documented in SOURCES.md + EN/ES methodology pages (source, SAE method, experimental status, coverage limitation, victimization ≠ reported-crime distinction); a verification confirms the composite index and all Phase-18 outputs are byte-unchanged (additive-only).

**Plans**: 4 plans

- [x] 23-01-PLAN.md — ENUSC VHDV fetcher (sha256-guarded ingest) + committed snapshot + ATTRIBUTION (VL-01, VL-02)
- [x] 23-02-PLAN.md — Additive enrichment of comuna JSONs + byte-unchanged guard + GitHub Actions wiring (VL-01, VL-02, VL-05)
- [x] 23-03-PLAN.md — EN/ES commune-page VHDV module + no-estimate fallback + i18n + type + commune validator (VL-03, VL-04)
- [x] 23-04-PLAN.md — F16 registry + SOURCES.md + EN/ES methodology + full-suite byte-unchanged gate (VL-05)

**UI hint**: yes

### Phase 24: Rankings UX: dynamic sortable tables and visual polish

**Goal:** Make the ranking pages — the project's most important SEO products — feel like first-class, sortable data tables. Wire dynamic high→low sorting (the existing `RankingTableEnhancer` island) into every ranking surface that currently lacks it (landing/home `index.astro` EN+ES, `/crime/[family]/` family pages EN+ES, `/communes/` directory, `/safest-cities-in-chile/` + ES), default sort to descending, make sortability visually obvious, and apply visual/UX polish using existing brand tokens (teal #0f766e, 5-level incidence scale). Includes a BrowserOS in-detail E2E visual review (EN+ES, desktop + mobile).
**Depends on:** Phase 18 (composite-index data, already shipped). Independent of Phase 22 launch ops.
**UI hint**: yes
**Plans:** 4/4 plans complete

Plans:

- [x] 24-01-PLAN.md - Fix enhancer to show sort affordance on load (data-default-sort-dir) + wire safest-cities EN+ES tables
- [x] 24-02-PLAN.md - BrowserOS E2E visual review (EN+ES, desktop 1280px + mobile 375px)

### Phase 25: UI/UX 360 remediation (prod diagnostic 2026-07-02): P0 soft-404/favicon/tablet-overflow, P1 number-locale/map-UX/editorial-visuals/news-semantics/compare-labeling/map-panel-years, P2 a11y+SEO polish

**Goal:** Execute ALL fixes from `.planning/UI-360-DIAGNOSTIC-260702.md` (2026-07-02 prod audit of ischilesafe.com; evidence `C:\Users\Carlo\bos-shots\`) following the report's "Orden sugerido": (1) P0-1 real 404 — check `public/_redirects`/Pages config, remove `/* /index.html 200` catch-all, add real `404.html`; (2) P0-3 favicon ico+svg + `<link rel=icon>` in base layout; (3) P0-2 tablet overflow 640–1080px — collapse nav to hamburger ≤1100px, stack home `.lead-table-col` ≤900px, shorten nav item to "Glossary"/"Glosario"; (4) P1-1 single `formatNumber(value, locale)` helper (Intl.NumberFormat) — fix MapIsland "~4.984" in EN, EN-formatted numbers in ES tables, Compare missing thousands separator + inconsistent decimals; (5) P1-3 map — fitBounds to Chile bbox + maxBounds, collapsible/compact mobile legend, Index/By-crime pills in 2 rows ≤480px, distinctive incident-pin color/shape + legend entry, pre-fetch guard for unknown ?cut=; (6) P1-5 static visuals on /is-santiago-safe/, /is-chile-safe/, /safest-cities-in-chile/ — top/bottom comuna tables + sparklines generated statically from public/data JSON (must be in HTML, nothing client-only); (7) P1-6 news — h2/h3 titles, comuna + crime-type chips per card, date grouping or pagination; harden Python classifier filter (exclude traffic accidents); (8) P1-2 compare — "Composite Crime Index" label + methodology link on big number, ?a=&b= URL sync via history.replaceState, popular-comparison chips in empty state, verify trend data (all show "→"); (9) P1-4 map panel — group blocks by year with badge + tooltip explaining differing years, drop the "~"; (10) P2 sweep — aria-label on incident markers, global :focus-visible + skip-link, JSON-LD WebSite+Organization on home, list of 16 linked regions in /rankings/, "#13 of 16" with "1 = highest reported", "(1 cases)" pluralization, region evolution title 2005–2026. P0 items are independent atomic commits, first.
**Requirements**: Editorial: never label territories safe/dangerous in absolute terms; rank #1 = MOST reported crime; rates already per-100k (never rescale); getRelativeLocaleUrl doesn't translate ES slugs (hardcode /es/...); OneDrive repo: chain build+validate in one command; verify with `npx astro build` + `npx astro preview --port 4321 --host` and BrowserOS inline (no subagents; screenshots to no-spaces path; mobile via 375px iframe).
**Depends on:** Phase 24
**Plans:** 9/9 plans complete

Plans:

**Wave 1**

- [x] 25-01-PLAN.md — P0 critical trio (real 404, favicon svg+ico, tablet breakpoints ≤1100/≤900 + Glossary) — 3 atomic commits (P0-1, P0-2, P0-3)

**Wave 2**

- [x] 25-02-PLAN.md — formatNumber helper + all number call sites + map-panel year badges/tooltip, drop "~", plural (P1-1, P1-4)
- [x] 25-03-PLAN.md — News semantic headings + type/comuna chips + date grouping; classifier traffic-accident exclusion + regression test (P1-6)

**Wave 3**

- [x] 25-04-PLAN.md — Map fitBounds/maxBounds framing, purple incident pins + aria-label + legend row, collapsible mobile legend, pill stacking ≤480px, ?cut= guard (P1-3, P2-1 markers)
- [x] 25-05-PLAN.md — Static rate tables + sparklines on is-santiago-safe / is-chile-safe / safest-cities (P1-5)
- [x] 25-06-PLAN.md — Compare: Composite Crime Index label + methodology link, ?a=&b= URL sync, popular chips, formatDecimal, trend cleanup (P1-2, P1-1)

**Wave 4**

- [x] 25-07-PLAN.md — Skip-to-main link + focus-visible sweep (P2-1)
- [x] 25-08-PLAN.md — Home WebSite+Organization JSON-LD, 16 region links in /rankings/, region KPI direction + chart footnote + placeholder CTA (P2-2, P2-3)

**Wave 5**

- [x] 25-09-PLAN.md — Full build+validate+check+pytest + BrowserOS inline visual review checkpoint (all P0/P1/P2)

### Phase 26: Event Clustering Spike

**Goal**: The team knows, with measured evidence rather than assumption, whether the LLMs this project already pays for (Granite 4.1 8B via OpenRouter default, DeepSeek fallback) can group multiple press articles covering the same real-world incident with zero false merges — and either a defined, back-compatible `cluster_id`/`is_primary` contract ships (GO) or a documented NO-GO closes the question so Phase 27/28 aren't left guessing.
**Depends on**: Nothing (spike runs against existing archived data in `data/incidents/archive/`); independent of Phases 27–30.
**Requirements**: CLUS-01, CLUS-02, CLUS-03, CLUS-04, CLUS-05, CLUS-06, CLUS-07, CLUS-08, CLUS-09
**Risk**: **Milestone's highest-risk phase.** A false merge (two distinct crimes displayed as one incident) is a published factual error on a safety-information site, not merely a bug. Precision-biased evaluation is non-negotiable; recall is unconstrained.
**Research flag**: ✅ Partially resolved 2026-07-29 by pre-phase feasibility ping (`26-00-SPIKE-PING.md`): Granite 4.1 8B at temp 0.0 passed 3/3 (positive + clean negative + adversarial same-day/same-comuna negative) with clean structured JSON. Validated verdict schema and pairwise-within-`(cut,date)`-bucket call pattern recorded there. Remaining planner work: build the full golden set (must include the comuna-2101 nine-article/3-event bucket and the Tongoy 4102 noisy-positive bucket) and run the full evaluation against the locked 100%-precision gate.
**Success Criteria** (what must be TRUE):

  1. A hand-labeled golden set of 60–100 article pairs/small clusters exists, built from `data/incidents/archive/`, including adversarial near-misses (same comuna+date/different crime; same crime/different comuna via typo or homophone; genuine same-event coverage from 2–3 outlets).
  2. Running the clustering pipeline against the golden set produces a measured pairwise precision and recall plus actual per-run LLM cost, and these numbers are compared against the locked gate (100% precision, zero false merges) to produce an explicit, documented GO or NO-GO verdict.
  3. A re-run of the pipeline over unchanged input data produces byte-identical `cluster_id` values every time (sha256 of the sorted member-ID set, never LLM output) — verified by a pytest regression, not a one-off script — so re-runs cannot silently churn `data/` or fire spurious Cloudflare rebuilds.
  4. No cluster in the golden-set run exceeds 4 members without being explicitly flagged for manual review, and the full pairwise decision matrix per cluster is present in the spike's logged output for audit.
  5. On GO, `IncidentRecord` gains optional-with-default `cluster_id: str | None` and `is_primary: bool` fields, verified backward-compatible against existing `current.json` and archive consumers (existing tests still pass unmodified); on NO-GO, the finding is documented in the spike report and no schema change ships.

**Plans**: 4 plans, sequential waves 1-4 (each wave gated on the prior wave's output)

Plans:

**Wave 1**

- [x] 26-01-PLAN.md — Core clustering module: rapidfuzz prefilter, cluster_id (sha256), union-find assembly + oversized flag, LLM verdict schema + prompt-injection hardening, fully-mocked offline unit tests (CLUS-02, CLUS-03, CLUS-04, CLUS-05, CLUS-06)

**Wave 2**

- [x] 26-02-PLAN.md — Golden-set construction: 60-100 hand-labeled pairs from real current.json data (mandatory comuna 2101/4102 hard buckets + sampled supplemental buckets), live-called cached verdicts, call budget logged (CLUS-01)

**Wave 3**

- [x] 26-03-PLAN.md — Pair-level precision/recall/cost evidence: run_clustering_spike.py + full pairwise decision matrix + offline pytest regression against the golden set (CLUS-07, CLUS-08)

**Wave 4**

- [x] 26-04-PLAN.md — GO/NO-GO close-out: apply the measured verdict to IncidentRecord.cluster_id/is_primary (GO) or document NO-GO with zero schema change, finalize spike report, full pytest + 14/14 frontend validators green (CLUS-09)

### Phase 27: News Facet Data Model

**Goal**: Every incident already in `data/incidents/current.json` and the monthly archive is discoverable by time window, region, and crime family through a single build-time-computed, shared facet index — with zero new dependency on Phase 26's outcome, zero new indexable URLs, and zero risk to the shared Cloudflare 20,000-file budget.
**Depends on**: Nothing from Phase 26 (explicitly independent — faceting is a pure derivation over existing schema fields). Runs in parallel with Phase 26.
**Requirements**: FACET-01, FACET-02, FACET-03, FACET-04, FACET-05, FACET-06, FACET-07
**Research flag**: ✅ RESOLVED 2026-07-29 — `region_id` IS present per commune on `data/cead/meta/index.json` (verified: `{"cut":"10101","region_id":"10",...}`). Use it as the authoritative cross-check for the CUT-length derivation.
**Success Criteria** (what must be TRUE):

  1. A shared `site/src/lib/newsFacets.ts` computes facet indexes (byFamily/byRegion/byMonth/time-window) at build time from `current.json` + the monthly archive, reading data via `process.cwd()`, and both `/news/` and `/es/noticias/` consume the exact same module (no per-locale drift).
  2. Time facets expose day-granularity presets (today / 7d / 30d) plus monthly-archive access, with sparse days rolled up rather than rendered as empty per-day slots.
  3. Geography facets resolve every incident's `cut` to one of the 16 regions via the established CUT-length derivation, and this derivation is verified correct against `data/cead/meta/index.json` at phase kickoff.
  4. All 8 news crime-family facets (including the news-only `sexuales`) are present with correct per-option counts (e.g. "Robo (14)"), and CEAD's `FAMILY_KEYS` remains unmodified at 7.
  5. No facet artifact is written under `site/**`, no new derived JSON is committed, `@astrojs/check` is clean on the new code, and the full validator suite plus page-count budget stay green with no new indexable URLs introduced.

**Plans**: TBD

### Phase 28: News Visualizer UI

**Goal**: A user on `/news/` or `/es/noticias/` can filter incidents by time window, region, and crime family with visible per-option counts, search comunas by typeahead instead of scanning a 346-item list, and — if Phase 26 was GO — see multi-source coverage of the same event grouped into one card that still names every constituent outlet; the whole experience stays fully indexable and zero-JS-required for content visibility.
**Depends on**: Phase 27 (consumes `newsFacets.ts`). Conditionally depends on Phase 26 for clustered-event cards only (NEWSUI-05 degrades gracefully to faceting-only UI on NO-GO — this is not a hard block).
**Requirements**: NEWSUI-01, NEWSUI-02, NEWSUI-03, NEWSUI-04, NEWSUI-05, NEWSUI-06, NEWSUI-07
**Research flag**: The tie-break rule for a cluster's "primary" article (earliest date? highest confidence?) is not decided by research and must be set during planning if Phase 26 was GO.
**Success Criteria** (what must be TRUE):

  1. A user can filter the news list by time window, region, and crime family with per-option counts visible, on both `/news/` and `/es/noticias/`.
  2. The unfiltered superset of incidents is fully present in the static pre-rendered HTML (viewable with JS disabled); filtering is progressive enhancement only.
  3. A user can find a comuna via accent-insensitive typeahead search reusing the established directory-finder pattern, instead of scanning a flat 346-item control.
  4. Filter state round-trips through shareable query params (survives reload/share), and a zero-result filter combination renders a clear bilingual empty state that is never itself indexed as a thin page.
  5. On Phase 26 GO, a clustered event renders as one primary-article card with an "N fuentes / N sources" badge that always exposes every constituent outlet and URL (no source hidden); on NO-GO, the page ships faceting only. Either way, any LLM-produced text shown in the UI is escaped, and the page adds no measurable CLS or hydration regression versus the current zero-JS news page. EN/ES parity holds via `i18n.ts`-sourced keys.

**Plans**: TBD

### Phase 29: Map UX Design Loop

**Goal**: The map's discoverability problem (the news toggle and filters are hard to find on desktop and effectively unusable at 375px mobile) is solved through an *iterative* BrowserOS-driven design loop — not a one-pass audit — that terminates in a concrete, human-accepted design spec before any map code is touched.
**Depends on**: Nothing (independent of Phases 26–28; can run in parallel with them).
**Requirements**: MAPUX-01, MAPUX-02, MAPUX-03, MAPUX-04, MAPUX-05
**Gates**: Phase 29 **hard-gates Phase 30**. No map control-shell code changes happen before the human acceptance gate in MAPUX-05 passes.
**BrowserOS constraints (must be followed exactly)**: run browser phases inline — `gsd-executor` has no BrowserOS tools; `save_screenshot` needs a path with no spaces; there is no viewport-resize, so emulate 375px mobile via a 375px iframe; serve the build with `npx astro preview --port 4321 --host` (there is no `npm run preview` script); chain build+validate in one command because the repo lives in OneDrive and `dist/` desyncs between processes.
**Success Criteria** (what must be TRUE):

  1. The current map is driven in BrowserOS against a real served build, and the baseline discoverability problem is captured with screenshots at desktop and at 375px (iframe-emulated).
  2. The design goes through **at least two full iterations** of screenshot → Fable-agent redesign → apply → re-screenshot before being considered for acceptance — a single audit-and-fix pass does not satisfy this criterion.
  3. Each iteration is scored against concrete criteria (not taste alone): can a first-time user find and activate the news layer; can they find the filters; are touch targets ≥44px at 375px; is there any keyboard or focus trap; do controls avoid occluding the map or conflicting with Leaflet panes — and the scoring is recorded per iteration.
  4. A lightweight live click-through of at least one comparable product (police.uk or CityProtect) is performed in BrowserOS and its findings inform at least one design iteration.
  5. The loop terminates in a written, accepted design spec, and a human explicitly signs off (the acceptance gate) before Phase 30 is allowed to start — recorded in STATE.md / the phase's plan artifacts.

**Plans**: TBD
**UI hint**: yes

### Phase 30: Map Control-Shell Rework

**Goal**: A first-time user, on desktop or at 375px mobile, can immediately find and use the news-layer toggle and the filter panel — implementing the Phase 29-accepted design — while every existing map behavior (choropleth, `?cut=` deep link, geolocation, incident pins) keeps working exactly as before.
**Depends on**: Phase 29 (hard gate — implements its accepted design spec). Soft dependency on Phase 27 for shared filter vocabulary consistency.
**Requirements**: MAPSH-01, MAPSH-02, MAPSH-03, MAPSH-04, MAPSH-05, MAPSH-06, MAPSH-07
**Risk**: **Regression-risk phase.** `ChoroplethLayer.ts`, `IncidentPinLayer.ts`, and `LowZoomDotLayer.ts` are protected and must remain untouched; the `?cut=` deep link is a previously-fixed feature that must survive; no declarative react-leaflet layer component (`<GeoJSON>`, `<Marker>`-as-JSX-child) may be introduced — this would reintroduce a previously-solved re-render-on-hover bug.
**Research flag**: Whether Phase 28's clustered-event UI needs a new grouped-marker map-pin treatment is an open question deferred to this design loop; and whether to close the `?region=` deep-link gap as part of this rework needs an explicit decision.
**Success Criteria** (what must be TRUE):

  1. The news-layer toggle is always visible and explicitly labeled — no longer buried inside a generic "mode" control — matching the specific complaint that motivated this milestone.
  2. The filter panel matches the Phase 29 spec, uses native `<details>`/`<dialog>` + CSS with zero new shipped JS dependencies, and follows a bottom-sheet or FAB pattern on mobile rather than being nested inside the hamburger nav.
  3. All map controls are keyboard-operable and screen-reader-labeled with no focus traps, touch targets ≥44px at 375px, and no z-index conflict with Leaflet panes.
  4. `?region=` behaves like the existing working `?cut=` (including graceful degradation on an unknown value — no 404, no console error), and a full regression pass confirms `?cut=` deep link, choropleth year/family filters, commune panel, geolocation, and incident pins all still work unchanged.
  5. Changes are confined to `MapTopbar.tsx` and sibling control components; the Opus code review explicitly verifies `ChoroplethLayer.ts`/`IncidentPinLayer.ts`/`LowZoomDotLayer.ts` are untouched and no declarative react-leaflet layer component was introduced; map filters and news facets share vocabulary via common data (`familyDefs.ts`, `data.ts`) without a code dependency between the map island and the news pages.

**Plans**: TBD
**UI hint**: yes

### Phase 31: Docs & Methodology Refresh

**Goal**: Every EN/ES methodology, source-registry, and disclaimer page accurately reflects what the shipped code actually computes today — including everything landed in this milestone — so no reader-facing claim is stale or contradicted by the running system.
**Depends on**: Phases 26–30 (documents the actual GO/NO-GO clustering outcome and the shipped map redesign; must land after their scope is finalized).
**Requirements**: DOCS-01, DOCS-02, DOCS-03, DOCS-04, DOCS-05, DOCS-06
**Success Criteria** (what must be TRUE):

  1. The EN + ES methodology pages describe the composite index, ENUSC victimization layer, the news-only `sexuales` family, and the directional meaning of `national_rank` (rank #1 = most reported crime, not safest) with zero prose-vs-computation drift.
  2. Editorial and legal disclaimers ("reported incidence" framing, under-reporting caveats, no absolute safe/dangerous verdict) are present and correct on every affected page.
  3. `data/SOURCES.md` is current and canonical, the outstanding ENUSC `[verify edition]` year is resolved to a real value, and every press outlet plus CEAD is correctly attributed.
  4. If Phase 26 returned GO, the clustering behavior (how same-event grouping works, its measured precision/recall, its limits) and every facet's semantics are documented for readers in plain bilingual language; if NO-GO, the documentation states that clearly instead.
  5. `site/scripts/validators/figure-registry.mjs` is hardened so substring matching can no longer report green against a stub section; the full validator suite plus pytest stay green; EN/ES parity holds and no existing inbound anchor is broken by the rewrite.

**Plans**: TBD

### Phase 32: Cron Consistency

**Goal**: The entire GitHub Actions schedule surface (news daily, R2 research archive, CEAD quarterly reminder, freshness guard) behaves as one coherent, self-diagnosing system — a silent stall or an empty-secret no-op is caught automatically, not discovered weeks later the way the past billing-lapse outage was.
**Depends on**: Phase 28 (audits the pipeline's cron shape *after* clustering is wired into the news pipeline, since that changes cost/latency). Runs late in the milestone by design.
**Requirements**: CRON-01, CRON-02, CRON-03, CRON-04, CRON-05, CRON-06, CRON-07
**Success Criteria** (what must be TRUE):

  1. Every workflow explicitly asserts each secret it consumes is non-empty before doing real work, and fails loudly (not a silent green no-op) when a secret is unset — verified by a deliberately-blanked-secret dry run.
  2. A freshness/heartbeat guard covers all three data crons (news daily, R2 archive, CEAD quarterly reminder) with cron-drift-tolerant thresholds, and a simulated stall on any one of them is detected and surfaced rather than passing silently.
  3. Deploy-hook retry/backoff behavior is identical across every workflow that calls it (previously three different retry counts), and issue labels are specific per pipeline so an alert is traceable to its source at a glance.
  4. The CEAD cron's expected-403-from-Actions-IPs status is documented directly in the workflow file, so a red run there cannot be misread as a real regression or "fixed" by someone unfamiliar with the history.
  5. Every workflow that writes to `data/` fetches and rebases before pushing (verified by a concurrent-write simulation with no lost update), and one documented table (schedule, trigger, secrets consumed, permissions, what it writes) covers the whole schedule surface.

**Plans**: TBD

### Phase 33: Security Posture

**Goal**: The project's GitHub Actions surface follows least-privilege defaults, every third-party action is pinned with a documented decision, dependency updates are automated, and a static Actions-specific security scanner runs in CI — closing supply-chain and secret-leakage risk without adding any shipped frontend footprint.
**Depends on**: Runs parallel with or immediately after Phase 32.
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, SEC-06
**Research flag**: SHA-pin vs. major-version-tag for each third-party action (e.g. `rhysd/actionlint`) needs an explicit, documented per-action decision, not a blanket rule.
**Success Criteria** (what must be TRUE):

  1. `GITHUB_TOKEN` defaults to read-only at the repository level, and every job across every workflow declares its own minimal explicit `permissions:` block (no job relies on the repo default alone).
  2. Every third-party action reference is pinned by full commit SHA with a version comment, and a documented decision (SHA-pin vs. major-version tag, with rationale) exists for each one.
  3. `.github/dependabot.yml` exists and covers the `github-actions`, `pip`, and `npm` ecosystems, and a dependabot PR can be observed being opened against at least one of them.
  4. `zizmor` runs in CI (invoked via `pipx`/`uvx`, never added to `pipeline/requirements.txt`) alongside the existing `actionlint`, and every finding it raises is triaged (fixed or explicitly accepted with a documented reason).
  5. A manual verification confirms GitHub secret scanning and push protection are enabled on the repository, no API key is discoverable in logs or committed artifacts, courtesy delays toward CEAD and press RSS feeds are present and adequate, and clustering (Phase 26/28) is confirmed not to have increased fetch volume against any upstream.

**Plans**: TBD

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 18. Composite Crime Index | 8/8 | Complete    | 2026-06-19 |
| 21. Commune Comparator + A-vs-B SEO | 4/4 | Complete   | 2026-06-20 |
| 23. ENUSC Communal Victimization Layer | 4/4 | Complete   | 2026-06-19 |
| 22. Go-Live / Launch Ops | 2/3 | In Progress (22-03 deferred human task) |  |
| 24. Rankings UX (sortable tables + polish) | 3/3 | Complete | 2026-06-20 |
| 25. UI/UX 360 remediation (prod diagnostic 260702) | 9/9 | Complete    | 2026-07-03 |
| 26. Event Clustering Spike | 4/4 | Complete   | 2026-07-29 |
| 27. News Facet Data Model | 0/? | Not started | - |
| 28. News Visualizer UI | 0/? | Not started | - |
| 29. Map UX Design Loop | 0/? | Not started | - |
| 30. Map Control-Shell Rework | 0/? | Not started | - |
| 31. Docs & Methodology Refresh | 0/? | Not started | - |
| 32. Cron Consistency | 0/? | Not started | - |
| 33. Security Posture | 0/? | Not started | - |
