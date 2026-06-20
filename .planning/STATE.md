---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Composite Index, Comparators & Launch
status: verifying
last_updated: "2026-06-20T15:58:46.907Z"
last_activity: 2026-06-20
progress:
  total_phases: 5
  completed_phases: 4
  total_plans: 22
  completed_plans: 21
  percent: 80
---

# STATE — Chile Safety Map (ischilesafe.com)

_Last updated: 2026-06-20 — Phase 21 (Commune Comparator + A-vs-B SEO) complete: 4/4 plans done. avs-b-budget registered as validator #14 (14/14 green, 1258 dist files, 10/10 prose sample PASS). Pending human: visual prose acceptance + GSC URL Inspection before batch expansion. Phase 22-03 (GSC sitemap submission) also remaining._

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-19)

**Core value**: Un mapa nacional interactivo con datos delictivos oficiales reales por comuna, servido en páginas estáticas bilingües que Google indexa — si el mapa con datos CEAD reales y las páginas SEO funcionan, el resto puede esperar.

**Current focus**: v2.0 Composite Index, Comparators & Launch. Remaining: Phase 21 (comparator, not started) + Phase 22-03 (GSC sitemap submission, manual).

## Current Position

Phase: 21 (Commune Comparator + A-vs-B SEO) — EXECUTING
Plan: 4 of 4 (Plan 03 complete — A-vs-B pages, cross-links, validators)
Status: Phase complete — ready for verification
Last activity: 2026-06-20

## Progress Bar

```
Phase 18 [████████████████████] 100% complete
Phase 23 [████████████████████] 100% complete
Phase 24 [████████████████████] 100% complete
Phase 22 [█████████████░░░░░░░]  67% in progress (2/3)
Phase 21 [████████████████████] 100% complete (4/4)
```

## Deferred Items

Items acknowledged and deferred at v1.x milestone closes:

| Category | Item | Status |
|----------|------|--------|
| uat | Phase 04 HUMAN-UAT — editorial prose spot-check, GSC submission, footer render, FAQ tone | partial (4 pending) — resolved at Phase 22 |
| uat | Phase 05 HUMAN-UAT — live pipeline run + 50-incident commune-hallucination audit | partial (2 pending) — resolved at GL-03 |
| uat | Phase 06 HUMAN-UAT — live ischilesafe.com cutover + no-rebuild-loop verification | partial (2 pending) — resolved at GL-01/GL-02 |
| todo | adsense-consent-mode — wire AdSense Consent Mode + flip ADSENSE_ENABLED | DEFERRED out of v2.0; monetization is a future cycle |

## Performance Metrics

| Metric | Value |
|--------|-------|
| v2.0 Phases defined | 3 (18, 21, 22) |
| v2.0 Phases complete | 0/3 |
| v2.0 Requirements mapped | 21/21 |
| v2.0 Plans created | 0 |
| v2.0 Plans complete | 0 |
| v1.3 Phases complete | 2/2 (shipped 2026-06-19) |
| v1.2 Phases complete | 8/8 (shipped 2026-06-18) |
| v1.1 Phases complete | 3/3 (shipped 2026-06-15) |
| v1.0 Phases complete | 6/6 (shipped 2026-06-13) |
| Build pages (v1.3 close) | 791 pages |
| Validators passing | 13/13 frontend + 179/179 pytest |
| Phase 23 P01 | 20m | 3 tasks | 5 files |
| Phase 23 P04 | 8m | 3 tasks | 4 files |
| Phase 24 P01 | 12m | 2 tasks | 3 files |
| Phase 24 P03 | 8m | 2 tasks | 3 files |
| Phase 21 P03 | 35m | 3 tasks | 7 files |

## Accumulated Context

### Roadmap Evolution

- Phase 23 added 2026-06-19: **ENUSC Communal Victimization Layer** (Track 4, VL-01..VL-05) — from SEED-002 feasibility study. Additive INE ENUSC 2024 SAE household-victimization (VHDV) figure on the ~136 covered comuna pages, graceful "no estimate" on the other ~210. **Sequenced BEFORE Phase 22 (Go-Live)** — motivation is to not launch infra-representing reported crime. Depends on Phase 18 + 17. Ingestion = manual/assisted versioned snapshot (no stable URL; behind INE JS widget). Findings: `.planning/research/SEED-002-FINDINGS.md`; spikes 004–007.

### Key Decisions

- Pydantic v2 syntax exclusively across pipeline — no v1 @validator or parse_obj
- PLAUSIBILITY_MAX_RATE raised to 100000 after real CEAD data confirmed micro-communes reach 43369 per-100k (Sierra Gorda, Juan Fernandez)
- Astro 6.4.x + React islands for pre-rendered static HTML (SEO indexability mandatory)
- JSON in repo as data store — no backend/DB; GitHub Actions cron commits trigger Cloudflare Pages via Deploy Hook only (never Git auto-build)
- DeepSeek v4-flash for RSS classification; `deepseek-chat` deprecated 2026-07-24 — never commit that model ID
- Commune canonical list (346 items) must be fixed in prompt at temperature 0.0 to prevent LLM geolocation hallucination
- Rate per 100,000 inhabitants is the single canonical metric; raw counts must never appear in rankings
- CUT codes stored as raw string digits without zero-padding (matches CEAD catalog)
- is_low_population defaults to True for unknown CUT codes (safe exclusion from rankings)
- [Phase 17 Wave 0, 2026-06-18] CEAD host is `cead.minsegpublica.gob.cl`. CEAD `tipoVal` is additive: 1=denuncias, 2=detenciones, 3=aprehendidos; casos policiales = `1,2`. Never naive-sum across measures.
- [Phase 17 Wave 0] Homicide truth = SPD VHC xlsx (`prevenciondehomicidios.cl`, 2018–2025; 2025 is partial/unconsolidated — reference year capped at 2024). Exposure proxy = SII `PUB_COMU.xlsb` (firms + dependent workers per commune; firma domicile/HQ caveat applies).
- [Phase 16] LLM emits commune NAME → deterministic name→CUT resolver (95.45% accuracy). Keep centroid-from-CUT for coords.
- [v1.3 Decisions] Phase 18 number is RESERVED for Composite Crime Index; v1.3 uses phases 19 + 20. COMU-03 `/crime/homicide/` = redirect (not scope note).
- [v2.0 Roadmap, 2026-06-19] Normalization method (winsorized min-max vs percentile rank) is the highest-risk planning decision for Phase 18 — must be locked before any index-driven template is written. Run distribution check on actual featured_rates data first.
- [v2.0 Roadmap, 2026-06-19] A-vs-B priority-pair allowlist exact count must be computed from actual commune data before getStaticPaths is written in Phase 21. Estimate ~3,400 pairs × 2 locales = ~6,800 pages; assert < 18,000 total files.
- [v2.0 Roadmap, 2026-06-19] AdSense activation + Consent Mode v2 DEFERRED out of v2.0 — monetization is a future cycle.
- [v2.0 Roadmap, 2026-06-19] Phase 22 (Go-Live) has no code dependency on Phase 21 — can run in parallel; starts once CF_DEPLOY_HOOK_URL secret is set.
- [Phase 18-01, 2026-06-19] scipy winsorized min-max (D-01) implemented; SII cap=5.0 confirmed; Providencia CUT 13123 (ratio 5.186) is only capped commune; 141 SPD-absent communes get 0.0; SII-absent available_metrics decremented by 1.

### Critical Pitfalls to Avoid

- **[Phase 18] Normalization without winsorization collapses the choropleth** — Sierra Gorda 43,369 per-100k pushes 95% of communes to the bottom of a raw min-max scale. Use scipy.stats.mstats.winsorize(limits=[0.01,0.01]) then min-max, OR percentile-rank. Add pytest distribution assertion.
- **[Phase 18] Composite index implies absolute safety verdict through IA alone** — a red-to-green choropleth or "A is safer than B" in a comparator communicates a verdict without forbidden words. Extend CI validator to catch "safest / mas segura / most dangerous / mas peligrosa" without "reported" qualifier.
- **[Phase 18] Schema migration breaks 5+ consumers of featured_rates** — commune panel, choropleth, Astro template, figure-registry validator, pytest all read featured_rates. Enumerate all consumers, add TypeScript types, run @astrojs/check, keep old fields present until all consumers verified.
- **[Phase 21] A-vs-B page count explosion blows 20K Cloudflare free-tier limit** — 59,685 pairs × 2 locales = 119,370 pages. Use curated priority-pair allowlist (~3,400 pairs). Assert total_pages < 18,000 at build time.
- **[Phase 21] Thin A-vs-B content triggers Google SpamBrain deindexing** — 95% identical symmetric pages = deindex risk. Minimum 5 uniqueness blocks + 300 non-swappable words per pair; acceptance-check ≥ 10 random pairs before deploy.
- **[Phase 22] CF_DEPLOY_HOOK_URL unset keeps production stale** — set the secret FIRST before any v2.0 code merge depends on a live deploy.
- **OneDrive build desync** — repo is inside OneDrive; always chain build+validate in ONE command (`cd site && npm run build && npm run validate`).
- **Forbidden language** — never an unqualified absolute "safe/dangerous/seguro/peligroso" verdict about any territory; CI validator enforces this.

### Research Flags for Planning

- **Phase 18 — plan interactively (NOT autonomous):** Normalization method final decision; SII cap threshold (recommended: sii_workers / ine_population > 5.0 → INE fallback); schema migration consumer enumeration; SPD VHC reference year confirmation (cap at 2024 until SPD confirms 2025 as final); composite_config.py metric weights (homicide 0.30 recommended, then violent families, then property, then incivilidades).
- **Phase 21 — scope prose engine before committing:** buildComparisonProse() must generate substantively different text per pair from real trend data; priority-pair allowlist exact count must be computed from actual commune data before getStaticPaths is written. Scope these two sub-problems in planning before committing to page count.
- **Phase 22 — standard patterns, no research needed:** All steps are documented human actions; see DEPLOYMENT.md and memory `prod-deploy-hook-secret-gap`.

### Todos

- (populated during planning)

### Blockers

- (none)

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260616-huj | Clarify crime-ranking rate labels (denuncias per 100k residents, 1 decimal, bilingual explainer) | 2026-06-16 | 4be9045 | [260616-huj-clarify-rate-labels](./quick/260616-huj-clarify-rate-labels/) |
| 260616-klv | Audit drug rates; fix national/region aggregation to population-weighted mean | 2026-06-16 | 5b997e4 | [260616-klv-auditar-tasas-drogas-100k-anomalas-modo-](./quick/260616-klv-auditar-tasas-drogas-100k-anomalas-modo-/) |
| 260616-ldi | Fix region_id grouping (BUGFIX-999.1): derive region from CUT length; all 16 regions now populate | 2026-06-16 | cad6a20 | [260616-ldi-fix-region-id-grouping-backlog-999-1-der](./quick/260616-ldi-fix-region-id-grouping-backlog-999-1-der/) |
| 260616-lu4 | Make ranking tables dynamic via progressive enhancement | 2026-06-16 | 2a550bd | [260616-lu4-hacer-dinamicas-las-tablas-rankings-de-c](./quick/260616-lu4-hacer-dinamicas-las-tablas-rankings-de-c/) |
| 260618-x95 | Fix prod-deploy gap: new deploy-on-code.yml curls CF Deploy Hook on push to master touching site/** | 2026-06-19 | 18b558b | [260618-x95-deploy-on-code](./quick/260618-x95-deploy-on-code/) |

## Session Continuity

**Last session**: 2026-06-20 — Phase 21 Plan 04 complete: avs-b-budget.mjs registered as validator #14 in all.mjs; 14/14 validators green; 1258 dist files (margin 16742 vs 18000 limit); 10/10 prose sample PASS programmatically. Phase 21 COMPLETE (4/4). Pending human: visual prose acceptance + GSC URL Inspection before expanding batch beyond 20 pairs.
**Prior session**: 2026-06-19 — v2.0 milestone roadmap written. 21/21 requirements mapped: CI-01..CI-10 → Phase 18, CMP-01..CMP-07 → Phase 21, GL-01..GL-04 → Phase 22. Phase 18 is the reserved number (intentional gap from v1.3). Hard dependency: Phase 21 depends on Phase 18. Phase 22 parallel with Phase 21. AdSense/Consent Mode deferred. Next: `/gsd:plan-phase 18` — interactively (high risk, not autonomous).
**Prior session (2026-06-19, v1.3 close)**: v1.3 shipped — Phases 19 (Tech-Debt Sweep) + 20 (Methodology & Sources Hardening). 13/13 validators, 179 pytest green. Milestone archived.
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
- [Phase ?]: Dual budget gate: raw le 420 KB AND gzip le 140 KB; single mapshaper 10%/q=10000 config
- [Phase ?]: chilemapas GPL-3 boundary source adopted; srcCodeToCut normalizes zero-padded codigo_comuna to CEAD CUT
- [Phase 10-03]: chilemapas attribution added to EN/ES methodology pages (GPL-3, INE/SUBDERE/BCN)
- [Phase ?]: pageType defaults to default in BaseLayout — safe fallback
- [Phase ?]: EditorialLayout defaults pageType=editorial; explicit prop overrides enabling rankings override
- [Phase ?]: jsonLd Props type widened to object|object[]|null in all three layouts
- [Phase ?]: CONFIRMED CEAD param for homicide subgroup 101 is grupo[]=101
- [Phase ?]: Rate (medida=2) and count (medida=1) for homicide require two separate CEAD POST requests per year
- [Phase ?]: CEAD zero-marker is '0,0000000000' — parse_cead_float returns 0.0 not None
- [Phase ?]: crimeIsHomicide set in onFamilyChange handler; exclusive with family via familyIndex null
- [Phase ?]: Column header matching in fetch_enusc_vhdv.py uses accent-normalized NFD comparison — real XLSX omits accents on 'victimas'/'logaritmico'
- [Phase 21-03]: Low-population fallback for comparator pair links — when commune has no non-low-pop same-region neighbors (Arica, region 15), fall back to all same-region communes to guarantee all 346 pages have /compare/ href
- [Phase 21-04]: avs-b-budget.mjs registered as validator #14 in all.mjs; full suite 14/14 green; GSC URL Inspection deferred to human operator before batch expansion beyond 20 enabled pairs

## Operator Next Steps

- **Plan Phase 23 (ENUSC Victimization Layer): `/gsd:plan-phase 23`** — runs before go-live. First plan task must drill INE's "Cuadros Estadísticos" widget once to download the VHDV Excel and verify its real schema (CUT mapping, value/unit, CV/precision columns, exact 136-comuna list) before designing the ingest. browseros must run INLINE (gsd-executor subagents lack it).
- Phase 22 (Go-Live) is gated AFTER Phase 23; can still pre-stage: set CF_DEPLOY_HOOK_URL secret in GitHub repo settings.
- Phase 18 gap-closure plans 18-06..18-08 are marked done in ROADMAP; confirm before relying on composite outputs.
