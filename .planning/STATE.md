---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Data Quality Hardening & Methodology
status: planning
last_updated: "2026-06-19T06:01:27.195Z"
last_activity: 2026-06-19 — ROADMAP.md written; v1.3 phases 19 + 20 defined
progress:
  total_phases: 10
  completed_phases: 1
  total_plans: 10
  completed_plans: 9
  percent: 10
---

# STATE — Chile Safety Map (ischilesafe.com)

_Last updated: 2026-06-19 — v1.3 roadmap written (P19 Tech-Debt Sweep + P20 Methodology & Sources Hardening); Phase 18 Composite Index reserved for after v1.3_

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-19)

**Core value**: Un mapa nacional interactivo con datos delictivos oficiales reales por comuna, servido en páginas estáticas bilingües que Google indexa — si el mapa con datos CEAD reales y las páginas SEO funcionan, el resto puede esperar.

**Current focus**: v1.3 Data Quality Hardening & Methodology. Roadmap written; next = plan Phase 19.

## Current Position

Phase: 19 — Tech-Debt Sweep (not started — awaiting plan)
Plan: —
Status: Roadmap written; ready to plan Phase 19
Last activity: 2026-06-19 — ROADMAP.md written; v1.3 phases 19 + 20 defined

## Deferred Items

Items acknowledged and deferred at milestone close on 2026-06-13 (human/external go-live work — not code defects):

| Category | Item | Status |
|----------|------|--------|
| uat | Phase 04 HUMAN-UAT — editorial prose spot-check, GSC submission, footer render, FAQ tone | partial (4 pending) |
| uat | Phase 05 HUMAN-UAT — live pipeline run + 50-incident commune-hallucination audit (needs DEEPSEEK_API_KEY) | partial (2 pending) |
| uat | Phase 06 HUMAN-UAT — live ischilesafe.com cutover (CF + DNS + secrets) + no-rebuild-loop verification | partial (2 pending) |
| todo | adsense-consent-mode-phase6 — wire AdSense Consent Mode when flipping ADSENSE_ENABLED | pending (high) |

All gated on one root action: execute `DEPLOYMENT.md` (CF account + DNS + `DEEPSEEK_API_KEY`/`CF_DEPLOY_HOOK_URL` secrets). See each phase's `*-HUMAN-UAT.md` and `.planning/milestones/v1.0-MILESTONE-AUDIT.md`.

## Performance Metrics

| Metric | Value |
|--------|-------|
| v1.3 Phases defined | 2 (19 + 20) |
| v1.3 Phases complete | 0/2 |
| v1.3 Requirements mapped | 24/24 |
| v1.3 Plans created | 0 |
| v1.3 Plans complete | 0 |
| v1.1 Phases complete | 3/3 |
| v1.2 Phases complete | 8/8 |
| Phase 01-data-foundation P04 | 45m \| 3 tasks \| 7 files |
| Phase 02-astro-site-programmatic-pages P01 | 35m \| 3 tasks \| 17 files |
| Phase 02-astro-site-programmatic-pages P03 | 45min \| 3 tasks \| 5 files |
| Phase 03-leaflet-map-island P01 | 25 \| 3 tasks \| 9 files |
| Phase 03-leaflet-map-island P02 | 45 \| 3 tasks \| 11 files |
| Phase 03-leaflet-map-island P03 | 25 \| 2 auto tasks + 1 UAT checkpoint (OPEN) \| 3 files |
| Phase 04-editorial-pages-adsense P02 | 18m \| 3 tasks \| 5 files |
| Phase 04-editorial-pages-adsense P03 | 22m \| 3 tasks \| 5 files |
| Phase 04 P06 | 25m \| 3 tasks \| 10 files |
| Phase 04-editorial-pages-adsense P07 | 12m \| 3 tasks \| 8 files |
| Phase 05-rss-news-pipeline P01 | 35 \| 3 tasks \| 18 files |
| Phase 05-rss-news-pipeline P03 | 12m \| 2 tasks \| 2 files |
| Phase 08-bug-fixes-data-correctness P01 | 8m | 2 tasks | 4 files |
| Phase 08-bug-fixes-data-correctness P03 | 12m | 2 tasks | 2 files |
| Phase 08 P05 | 15m | 3 tasks | 1 files |
| Phase 09 P04 | 12m | 2 tasks | 2 files |
| Phase 10-high-resolution-commune-geometry P01 | 18m | 2 tasks | 2 files |
| Phase 10-high-resolution-commune-geometry P02 | 25 | 3 tasks | 4 files |
| Phase 10-high-resolution-commune-geometry P03 | 10m | 2 tasks + 1 human-verify checkpoint | 3 files |
| Phase 11-publish-346-comunas-finder P02 | 15m | 3 tasks | 5 files |
| Phase 12-home-ia-redesign-comuna-page-hub-and-spoke P04 | 18m | 3 tasks | 2 files |
| Phase 13-ranking-seo-hardening P01 | 25 | 3 tasks | 11 files |
| Phase 13-ranking-seo-hardening P02 | 12m | 3 tasks | 13 files |
| Phase 14 P01 | 25m | 3 tasks | 4 files |
| Phase 14-homicide-as-a-first-class-category P05 | 8m | 2 tasks | 2 files |
| Phase 15 P02 | 25 | 3 tasks | 4 files |

## Accumulated Context

### Key Decisions

- Pydantic v2 syntax exclusively across pipeline — no v1 @validator or parse_obj
- PLAUSIBILITY_MAX_RATE raised to 100000 after real CEAD data confirmed micro-communes reach 43369 per-100k (Sierra Gorda, Juan Fernandez)
- Astro 6.4.x + React islands for pre-rendered static HTML (SEO indexability mandatory)
- JSON in repo as data store — no backend/DB; GitHub Actions cron commits trigger Cloudflare Pages via Deploy Hook only (never Git auto-build)
- DeepSeek v4-flash for RSS classification; `deepseek-chat` deprecated 2026-07-24 — never commit that model ID
- Commune canonical list (346 items) must be fixed in prompt at temperature 0.0 to prevent LLM geolocation hallucination
- Rate per 100,000 inhabitants is the single canonical metric; raw counts must never appear in rankings
- Programmatic pages deploy in batches of 10–20 first; GSC indexing confirmed before generating all 346
- CUT codes stored as raw string digits without zero-padding (matches CEAD catalog)
- is_low_population defaults to True for unknown CUT codes (safe exclusion from rankings)
- INE 2024 population values spot-checked against official INE projections — Assumption A6 closed
- parse_cead_float maps all CEAD missing-value markers ('', '-', 'S/I', 'N/A') to None — uniform handling
- CEAD live endpoint confirmed HTTP 200 on 2026-06-12 with 3 RM communes; inter-batch sleep belongs to orchestrator not client
- Open Question 3 (homicides subgroup ID=101, kidnappings subgroup ID unknown) deferred to Plan 04 — do not hard-code featured-flag subgroup IDs until Plan 04 confirms them via live call
- CHIP_DEFS carries display order + catalog by_family index — chip order != array index (0=vida, 1=robos_violentos, 2=vif, 3=drogas, 4=armas, 5=propiedad, 6=incivilidades)
- ResultPanel converts series.by_family RECORD to catalog-indexed ARRAY for PanelFamilyBars (commune JSON uses record; map-payload uses array — never confuse them)
- [Phase 17 Wave 0, 2026-06-18] CEAD host is `cead.minsegpublica.gob.cl` (methodology wrongly says `ministeriointerior` — fix in DQ). CEAD grupo/subgrupo catalog enumerated via `ajax_2.php seleccion=9`; familia = first digit of grupo id; full catalog in `phases/17-robust-crime-index/17-CEAD-CATALOG.json`.
- [Phase 17 Wave 0] CEAD `tipoVal` is additive: 1=denuncias, 2=detenciones, 3=aprehendidos; casos policiales (what the site shows) = `1,2`. Never naive-sum across measures (double-counts per offence).
- [Phase 17 Wave 0] lesiones = CEAD grupos 103+104+105 (graves/gravísimas, menos graves, leves); secuestro is ABSENT from CEAD entirely (Fiscalía/Ministerio Público, regional only, 868/2024).
- [Phase 17 Wave 0] Homicide truth = SPD VHC xlsx (`prevenciondehomicidios.cl`, comuna-level, 2018–2025; count = row count per comuna/year). Exposure proxy = SII `PUB_COMU.xlsb` (empresas + trabajadores dependientes per comuna, 2005–2024; needs `pyxlsb`; comuna = firm domicile/HQ caveat).
- [Phase 16] News geolocation bottleneck = design not vendor: both LLMs pick wrong CUT ~60-70% from bare codes. Fix = LLM emits comuna NAME → deterministic name→CUT. MiniMax that works: `MiniMax-Text-01` @ `https://api.minimaxi.chat/v1` (no json_object response_format). Keep centroid-from-CUT for coords.
- [v1.3 Decisions] Phase 18 number is RESERVED for Composite Crime Index; v1.3 uses phases 19 + 20 (intentional gap at 18). COMU-03 `/crime/homicide/` = redirect (not a scope note). SII/Fiscalía/SPD-VHC snapshots stay stubs in v1.3 — promoted to first-class at Phase 18 when wired to displayed figures.

### Critical Pitfalls to Avoid

- Thin programmatic content → Google deindexing (recovery 4–8 weeks)
- GitHub Actions → Cloudflare Pages infinite rebuild loop (burns 500 free builds/month)
- LLM assigning incidents to wrong communes (use closed-list classification)
- Frequency vs. rate ranking error (bake `rate_per_100k` into schema from day 1)
- CEAD endpoint silently returning wrong data (validate 346-commune count + key presence after every scrape)
- OneDrive build desync: repo lives inside OneDrive; always chain build+validate in ONE command (`cd site && npm run build && npm run validate`) — never separate processes
- Methodology text drift: never say "population-weighted" for the national aggregate (code is unweighted; that claim was the MC-01/MC-07 bug P19 must fix)
- Forbidden language: never an unqualified absolute "safe/dangerous/seguro/peligroso" verdict about any territory — CI validator enforces this after P20

### Research Flags for Planning

- Phase 7: BrowserOS MCP must be connected before review starts (port 9200; verify with tool search for `mcp__*browseros*__*` navigate/screenshot/console/resize tools)
- Phase 7: dev server `cd site && npm run dev` must be running (predev runs sync-data.mjs; incidents layer will show empty state — expected)
- Phase 19: COMU-03 canonical redirect target must be determined during plan (exact URL — likely the crime-ranking homicide page `/crime-ranking/homicide/` / `/es/ranking-delito/homicidios/`)
- Phase 20: ENUSC official URL requires verification before publishing (`[verify URL]` note in METHODOLOGY-SPEC); confirm canonical between ine.gob.cl/enusc and seguridadpublica.gov.cl

### Todos

- (none yet — populated during planning)

### Blockers

- (none)

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260616-huj | Clarify crime-ranking rate labels (denuncias per 100k residents, 1 decimal, bilingual explainer — presentational only, no data change) | 2026-06-16 | 4be9045 | [260616-huj-clarify-rate-labels](./quick/260616-huj-clarify-rate-labels/) |
| 260616-klv | Audit drug rates (verified 9688/9688 vs CEAD cache — data faithful); clarify CEAD drug-family scope (Ley 20.000 vs consumption); fix national/region aggregation to population-weighted mean | 2026-06-16 | 5b997e4 | [260616-klv-auditar-tasas-drogas-100k-anomalas-modo-](./quick/260616-klv-auditar-tasas-drogas-100k-anomalas-modo-/) |
| 260616-ldi | Fix region_id grouping (backlog 999.1): derive region from CUT length, ending Tarapacá 11/14 collision; migrate 217 commune files + recompute regional_rank; all 16 regions now populate; simplify frontend. Verified (build 790pp, 12/12 validators) | 2026-06-16 | cad6a20 | [260616-ldi-fix-region-id-grouping-backlog-999-1-der](./quick/260616-ldi-fix-region-id-grouping-backlog-999-1-der/) |
| 260616-lu4 | Make ranking tables dynamic via progressive enhancement: shared vanilla-JS RankingTableEnhancer adds clickable asc/desc sort headers (rate + name) and a complete-years-only year selector to both region commune tables and national crime-ranking tables (EN+ES). national_rank stays fixed canonical; low-pop stays grouped at bottom; JS-off static HTML byte-identical (SEO intact); zero new deps. Build green, all 48 ranking pages carry data-* hooks | 2026-06-16 | 2a550bd | [260616-lu4-hacer-dinamicas-las-tablas-rankings-de-c](./quick/260616-lu4-hacer-dinamicas-las-tablas-rankings-de-c/) |
| 260618-x95 | Fix prod-deploy gap: CF Pages auto-build is disabled (anti rebuild-loop), so code pushes never redeployed prod (stale build = user saw no news/data). New `.github/workflows/deploy-on-code.yml` curls the CF Deploy Hook on push to master touching `site/**` (not `data/**` — no loop); empty-secret → exit 0 (dry-run safe). Requires CF_DEPLOY_HOOK_URL secret + user push to take effect | 2026-06-19 | 18b558b | [260618-x95-deploy-on-code](./quick/260618-x95-deploy-on-code/) |

## Session Continuity

**Last session**: 2026-06-19 — v1.3 milestone started. ROADMAP.md written with Phases 19 (Tech-Debt Sweep) and 20 (Methodology & Sources Hardening). Phase 18 number reserved for Composite Crime Index (post-v1.3). All 24 v1.3 requirements mapped (TD-01..07 → P19, BIL-01..04 → P19, SEO-01..03 → P19, MTH-01..04 → P20, SRC-01..05 → P20). Next: `/gsd:plan-phase 19`.
**Prior session (2026-06-18, v1.2 close)**: v1.2 shipped — Phase 17 (data quality) then Phase 16 (news) completed via /gsd-autonomous; tech_debt audit 0 blockers, 22/22 reqs; all 16 regions populate after BUGFIX-999.1 (quick-260616-ldi).
**Known env issue (not code)**: project is inside OneDrive — `dist/` artifacts desync between separate processes; ALWAYS chain build + validate in one command: `cd site && npm run build && npm run validate`.

## Decisions

- [Phase 02-06]: Region pages fall back to national latestCompleteYear when region series is empty
- [Phase 02-06]: Crime page spatialCoverage Country is valid — only top-level Place/@type is prohibited
- [Phase 02-06]: Sitemap filter CUT-to-slug join via index.json at astro config time
- [Phase ?]: corrected path traversal depth
- [Phase ?]: CEAD region_id mapping required for loadCommune regionName
- [Phase ?]: component library
- [Phase ?]: L.canvas renderer scoped to L.geoJSON layer only (Pitfall 6 compliance)
- [Phase ?]: Static aria-label in Astro shell satisfies map validator without SSR
- [Phase ?]: CUT list from comunas filenames; Node TopoJSON decode; 4 hardcoded centroid fallbacks for null-geometry communes
- [Phase ?]: Four-way CUT integrity assertion (missing/orphan/dup/Santiago vs index.json) in Step-5 and Step-8 of build-topojson.mjs
- [Phase ?]: Dual budget gate: raw le 420 KB (430080 B) AND gzip le 140 KB (143360 B); single mapshaper 10%/q=10000 config replaces three-config retry loop
- [Phase ?]: chilemapas GPL-3 boundary source adopted; srcCodeToCut normalizes zero-padded codigo_comuna to CEAD CUT
- [Phase 10-03]: chilemapas attribution added to EN/ES methodology pages (GPL-3, INE/SUBDERE/BCN); geometry vs CEAD stats distinction explicit
- [Phase ?]: pageType defaults to default in BaseLayout — safe fallback for pages not in enum
- [Phase ?]: EditorialLayout defaults pageType=editorial; explicit prop overrides enabling rankings override
- [Phase ?]: jsonLd Props type widened to object|object[]|null in all three layouts; emission unchanged until Plan 03
- [Phase ?]: CONFIRMED CEAD param for homicide subgroup 101 is grupo[]=101 (NOT subgrupo[] — silently ignored, returns all-zero rows)
- [Phase ?]: Rate (medida=2) and count (medida=1) for homicide require two separate CEAD POST requests per year
- [Phase ?]: CEAD zero-marker is '0,0000000000' (full-decimal) — parse_cead_float returns 0.0 not None
- [Phase ?]: crimeIsHomicide set in onFamilyChange handler; exclusive with family via familyIndex null

## Operator Next Steps

- Run `/gsd:plan-phase 19` to plan the Tech-Debt Sweep phase
