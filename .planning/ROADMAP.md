# Roadmap — Chile Safety Map (ischilesafe.com)

_Last updated: 2026-06-19 — v2.0 Composite Index, Comparators & Launch (Phases 18, 21, 22); Phase 18 is the reserved number for Composite Crime Index_

## Milestones

- ✅ **v1.0 MVP** — Phases 1–6 (shipped 2026-06-13) — full detail: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Polish & QA** — Phases 7–9 (shipped 2026-06-15) — full detail: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Map Fidelity, Findability & News** — Phases 10–17 (shipped 2026-06-18) — full detail: [milestones/v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)
- ✅ **v1.3 Data Quality Hardening & Methodology** — Phases 19–20 (shipped 2026-06-19) — _(Phase 18 deliberately reserved for Composite Crime Index)_
- 🔄 **v2.0 Composite Index, Comparators & Launch** — Phases 18, 21, 23, 22 (in progress; Phase 23 ENUSC victimization layer added from SEED-002, runs before go-live)

> **Phase numbering note:** Phase 18 is the RESERVED slot for the Composite Crime Index (intentional gap in v1.3 which used 19 + 20). The comparator follows at Phase 21 and go-live at Phase 22. There is no Phase 19 or 20 in this milestone — those are archived v1.3 phases.

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

### v2.0 Composite Index, Comparators & Launch

- [~] **Phase 18: Composite Crime Index** — exposure-adjusted 0–100 index, SPD VHC homicide switch, schema migration, index-driven choropleth _(RESERVED number; highest-risk phase — plan interactively)_ (executed 2026-06-19; verified gaps_found — 3 gap-closure plans 18-06..18-08 pending execution)
- [x] **Phase 21: Commune Comparator + A-vs-B SEO** — interactive comparator island + ~6,800 bilingual A-vs-B programmatic pages built on Phase 18 outputs _(depends on Phase 18)_ (completed 2026-06-19)
- [x] **Phase 23: ENUSC Communal Victimization Layer** — additive INE ENUSC 2024 SAE household-victimization (VHDV) figure on the 136 covered comuna pages, graceful "no estimate" for the other 210; anti-infra-representation, additive-only vs Phase 18 _(depends on Phase 18 + 17; **runs BEFORE Phase 22**)_ — origin SEED-002 (completed 2026-06-19)
- [ ] **Phase 22: Go-Live / Launch Ops** — CF deploy hook, production deploy, live news audit, GSC submission _(parallel with Phase 21; no code dependency; **gated after Phase 23** per SEED-002)_

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

**Plans**: TBD
**UI hint**: yes

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

**Plans**: TBD

### Phase 23: ENUSC Communal Victimization Layer

**Sequence note**: Runs **BEFORE Phase 22 (Go-Live)** — the SEED-002 motivation is to not launch infra-representing reported crime. Numbered 23 (sequential), sequenced ahead of 22.
**Goal**: Each of the 136 ENUSC-covered comuna pages additionally displays INE's ENUSC 2024 communal household violent-crime victimization (VHDV) figure as a clearly-labeled experimental / SAE-modeled estimate shown **alongside (never merged into)** the CEAD composite index, while the 210 uncovered comunas degrade gracefully to an explicit "no estimate" caveat — robustifying the site against reported-crime infra-representation **without altering any Phase-18 locked decision**.
**Depends on**: Phase 18 (composite index, F-series figure registry zero-orphan, SOURCES.md discipline) and Phase 17 (name→CUT resolver)
**Origin**: SEED-002 feasibility study (Design A) — `.planning/research/SEED-002-FINDINGS.md`, spikes 004–007
**Requirements**: VL-01, VL-02, VL-03, VL-04, VL-05
**Key constraints**: additive/versioned only (composite + all Phase-18 outputs byte-unchanged); comuna unit = 346; CEAD rates already per-100k (do not rescale); ~$0 infra; EN/ES parity; SEO-static; never an absolute seguro/peligroso verdict; every figure attributed + caveated.
**Ingestion decision** (user-approved): **manual/assisted annual versioned snapshot** of the ENUSC SAE VHDV Excel checked into the repo with provenance (source URL, retrieval date, INE experimental disclaimer, checksum) — **not** a brittle recurring cron scraper. The Excel sits behind INE's JS "Cuadros Estadísticos" widget (`https://www.ine.gob.cl/estadisticas/estadisticas-experimentales/seguridad-ciudadana`) with **no stable static URL**. Metodología PDF: `http://www.ine.gob.cl/docs/default-source/estadisticas-experimentales-seguridad-ciudadana/publicaciones-y-anuarios/2024/presentación-metodología-sae--enusc-2024.pdf`. ArcGIS map: `https://experience.arcgis.com/experience/53d8caa5ab904894bb9b52ba6189c5cf`.
**Research flag**: First execution task is to drill the INE widget once, download the VHDV Excel, and verify its real schema (CUT mapping, value/unit, presence of CV/precision columns, exact 136-comuna list) — the plan must be grounded on the actual file, not assumptions.
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

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 18. Composite Crime Index | 8/8 | Complete    | 2026-06-19 |
| 21. Commune Comparator + A-vs-B SEO | 0/TBD | Not started | - |
| 23. ENUSC Communal Victimization Layer | 4/4 | Complete   | 2026-06-19 |
| 22. Go-Live / Launch Ops | 0/TBD | Not started (gated after 23) | - |
