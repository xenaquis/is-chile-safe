---
gsd_state_version: 1.0
milestone: v2.1
milestone_name: News Intelligence, Map UX & Ops Hardening
status: executing
last_updated: "2026-07-29T23:41:05.551Z"
last_activity: 2026-07-29
progress:
  total_phases: 14
  completed_phases: 5
  total_plans: 35
  completed_plans: 32
  percent: 36
---

# STATE — Chile Safety Map (ischilesafe.com)

_Last updated: 2026-07-29 — **v2.1 AUTONOMOUS RUN in progress** (see `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md`). Phase 26 (Event Clustering Spike) is PLANNED: 4 plans, 4 waves, Fable review APPROVED after two revision cycles (Opus plan-check 5 blockers + Opus premortem 4 HIGH/28 amendments + Opus re-check 2 regression blockers, all closed). 10 binding orchestrator decisions recorded as F-01..F-10. Next action: `/gsd:execute-phase 26`._

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-29)

**Core value**: Un mapa nacional interactivo con datos delictivos oficiales reales por comuna, servido en páginas estáticas bilingües que Google indexa — si el mapa con datos CEAD reales y las páginas SEO funcionan, el resto puede esperar.

**Current focus**: v2.1 News Intelligence, Map UX & Ops Hardening — unattended autonomous run per `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md` (Sonnet codes, Opus validates, Fable decides; NO `git push`, `data/` read-only). Phase 26 planned and approved; executing next.

## Current Position

Phase: 26 (event-clustering-spike) — EXECUTING
Plan: 3 of 4
Status: Ready to execute
Last activity: 2026-07-29

## Progress Bar

```
Phase 18 [████████████████████] 100% complete
Phase 23 [████████████████████] 100% complete
Phase 24 [████████████████████] 100% complete
Phase 22 [█████████████░░░░░░░]  67% in progress (2/3, 22-03 deferred human task)
Phase 21 [████████████████████] 100% complete (4/4)
Phase 25 [████████████████████] 100% complete (9/9)
Phase 26 [░░░░░░░░░░░░░░░░░░░░]   0% PLANNED (4 plans, Fable APPROVED — Event Clustering Spike, high risk)
Phase 27 [░░░░░░░░░░░░░░░░░░░░]   0% not started (News Facet Data Model — no dep on 26)
Phase 28 [░░░░░░░░░░░░░░░░░░░░]   0% not started (News Visualizer UI)
Phase 29 [░░░░░░░░░░░░░░░░░░░░]   0% not started (Map UX Design Loop — gates 30)
Phase 30 [░░░░░░░░░░░░░░░░░░░░]   0% not started (Map Control-Shell Rework — regression risk)
Phase 31 [░░░░░░░░░░░░░░░░░░░░]   0% not started (Docs & Methodology Refresh)
Phase 32 [░░░░░░░░░░░░░░░░░░░░]   0% not started (Cron Consistency)
Phase 33 [░░░░░░░░░░░░░░░░░░░░]   0% not started (Security Posture)
```

## Deferred Items

Items acknowledged and deferred at v1.x/v2.0 milestone closes:

| Category | Item | Status |
|----------|------|--------|
| uat | Phase 04 HUMAN-UAT — editorial prose spot-check, GSC submission, footer render, FAQ tone | partial (4 pending) — resolved at Phase 22 |
| uat | Phase 05 HUMAN-UAT — live pipeline run + 50-incident commune-hallucination audit | partial (2 pending) — resolved at GL-03 |
| uat | Phase 06 HUMAN-UAT — live ischilesafe.com cutover + no-rebuild-loop verification | partial (2 pending) — resolved at GL-01/GL-02 |
| todo | adsense-consent-mode — wire AdSense Consent Mode + flip ADSENSE_ENABLED | DEFERRED out of v2.0; monetization is a future cycle |
| todo | GL-04 / Phase 22-03 — Google Search Console sitemap submission | DEFERRED human/manual; carried into v2.1 but NOT a v2.1 requirement or phase |

## Performance Metrics

| Metric | Value |
|--------|-------|
| v2.1 Phases defined | 8 (26–33) |
| v2.1 Phases complete | 0/8 |
| v2.1 Requirements mapped | 54/54 |
| v2.1 Plans created | 4 (Phase 26) |
| v2.1 Plans complete | 0 |
| v2.0 Phases complete | 6/6 (18, 21, 22*, 23, 24, 25 — *22-03 deferred human task) |
| v1.3 Phases complete | 2/2 (shipped 2026-06-19) |
| v1.2 Phases complete | 8/8 (shipped 2026-06-18) |
| v1.1 Phases complete | 3/3 (shipped 2026-06-15) |
| v1.0 Phases complete | 6/6 (shipped 2026-06-13) |
| Build pages (v1.3 close) | 791 pages |
| Validators passing | 14/14 frontend + **301** pytest (301 collected 2026-07-29 — the old 179 figure was stale) |
| Phase 23 P01 | 20m | 3 tasks | 5 files |
| Phase 23 P04 | 8m | 3 tasks | 4 files |
| Phase 24 P01 | 12m | 2 tasks | 3 files |
| Phase 24 P03 | 8m | 2 tasks | 3 files |
| Phase 21 P03 | 35m | 3 tasks | 7 files |
| Phase 26 P01 | 35m | 2 tasks | 3 files |
| Phase 26 P02 | 35m | 1 tasks | 6 files |

## Accumulated Context

### Roadmap Evolution

- **v2.1 roadmap created 2026-07-29**: 8 phases (26–33), continuing sequential numbering from v2.0's last phase (25). Phase 26 (Event Clustering Spike, high-risk) is independent and gates only the clustering portions of 27/28 — Phase 27 (News Facet Data Model) has zero dependency on Phase 26 and runs in parallel. Phase 28 (News Visualizer UI) depends on 27 and conditionally on 26. Phase 29 (Map UX Design Loop, iterative BrowserOS + Fable) hard-gates Phase 30 (Map Control-Shell Rework, regression-risk — protected Leaflet layer files) via a human acceptance gate. Phases 31 (Docs & Methodology Refresh), 32 (Cron Consistency), 33 (Security Posture) are closing phases sequenced after 26–30's shape is known; 32 audits the pipeline after 28 wires clustering in; 33 runs parallel with or after 32. Mandatory per-phase protocol for all 8 phases: research → plan → premortem → plan review by a Fable agent → implementation by Sonnet → code review by Opus → GSD validation. Carried-over deferred item NOT mapped to any v2.1 phase: v2.0 GL-04 / Phase 22-03 GSC sitemap submission (human/manual).
- Phase 25 added 2026-07-02: **UI/UX 360 remediation** — executes all fixes from `.planning/UI-360-DIAGNOSTIC-260702.md` (prod audit, evidence in `C:\Users\Carlo\bos-shots\`). P0: real 404.html (kill catch-all soft-404), favicon ico+svg+link, tablet 640–1080px overflow (hamburger ≤1100px, stack home lead-table-col ≤900px, "Glossary" nav copy). P1: single `formatNumber(value, locale)` via Intl.NumberFormat (MapIsland/Compare/ES tables), map fitBounds+maxBounds + collapsible mobile legend + pills 2 rows ≤480px + distinctive incident-pin color/shape + legend entry + ?cut= pre-fetch guard, static visuals (top/bottom tables + sparklines from public/data JSON) on /is-santiago-safe/ /is-chile-safe/ /safest-cities-in-chile/, news h2/h3 + comuna/crime chips + date grouping + classifier filter excluding traffic accidents (Python pipeline), compare "Composite Crime Index" label + methodology link + ?a=&b= URL sync (history.replaceState) + popular-comparison chips + verify trend data, map panel year badges + tooltip + drop "~". P2: aria-label on incident markers, global :focus-visible + skip-link, JSON-LD WebSite+Organization on home, 16 region links in /rankings/, directional "#13 of 16 (1 = highest reported)", "(1 cases)" plural, region evolution title 2005–2026. Constraints: never label territories safe/dangerous; rank #1 = MOST reported crime; rates already per-100k; hardcode ES slugs; OneDrive — chain build+validate in one command; verify via astro preview + BrowserOS inline.
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
- [v2.1 Roadmap, 2026-07-29] Clustering GO gate is locked at 100% pairwise precision / zero false merges on the golden set — recall is unconstrained. A single false merge in the golden set is a NO-GO; exact call pattern (batched vs pairwise) is a Phase 26 planner decision.
- [v2.1 Roadmap, 2026-07-29] Facet URL strategy is locked to query params only (`?family=&region=&window=`) on existing `/news/` + `/es/noticias/` — no new indexable facet URLs, ever.
- [v2.1 Roadmap, 2026-07-29] New dependencies for the whole milestone: `rapidfuzz` (pipeline, Phase 26) + `zizmor` (CI-only, Phase 33). Zero new shipped frontend JS.
- [v2.1 Roadmap, 2026-07-29] Map controls locked to native `<details>`/`<dialog>` + CSS + Leaflet's own `L.Control` — no popover/positioning library, no declarative react-leaflet layer components.

### Critical Pitfalls to Avoid

- **[Phase 18] Normalization without winsorization collapses the choropleth** — Sierra Gorda 43,369 per-100k pushes 95% of communes to the bottom of a raw min-max scale. Use scipy.stats.mstats.winsorize(limits=[0.01,0.01]) then min-max, OR percentile-rank. Add pytest distribution assertion.
- **[Phase 18] Composite index implies absolute safety verdict through IA alone** — a red-to-green choropleth or "A is safer than B" in a comparator communicates a verdict without forbidden words. Extend CI validator to catch "safest / mas segura / most dangerous / mas peligrosa" without "reported" qualifier.
- **[Phase 18] Schema migration breaks 5+ consumers of featured_rates** — commune panel, choropleth, Astro template, figure-registry validator, pytest all read featured_rates. Enumerate all consumers, add TypeScript types, run @astrojs/check, keep old fields present until all consumers verified.
- **[Phase 21] A-vs-B page count explosion blows 20K Cloudflare free-tier limit** — 59,685 pairs × 2 locales = 119,370 pages. Use curated priority-pair allowlist (~3,400 pairs). Assert total_pages < 18,000 at build time.
- **[Phase 21] Thin A-vs-B content triggers Google SpamBrain deindexing** — 95% identical symmetric pages = deindex risk. Minimum 5 uniqueness blocks + 300 non-swappable words per pair; acceptance-check ≥ 10 random pairs before deploy.
- **[Phase 22] CF_DEPLOY_HOOK_URL unset keeps production stale** — set the secret FIRST before any v2.0 code merge depends on a live deploy.
- **OneDrive build desync** — repo is inside OneDrive; always chain build+validate in ONE command (`cd site && npm run build && npm run validate`).
- **Forbidden language** — never an unqualified absolute "safe/dangerous/seguro/peligroso" verdict about any territory; CI validator enforces this.
- **[Phase 26] False merges in LLM event clustering** — two distinct same-day/same-comuna crimes collapsed into one displayed incident is the milestone's single highest-risk failure mode. Mitigate with structured fact-based verdict schema, precision-biased threshold defaulting to no-merge on ambiguity, golden-set pairwise-precision gate before GO.
- **[Phase 26/32] Non-deterministic cluster IDs burning the free-tier build budget** — LLM non-determinism leaking into cluster-ID assignment would trigger spurious deploys against the 500-builds/month ceiling. Cluster IDs must be sha256 of sorted member-ID set, never LLM output.
- **[Phase 27/28] Facet/URL explosion causing thin content** — crossing time × 16 regions × 8 families as new indexable URLs would produce hundreds of near-empty pages against the shared 20K Cloudflare file budget. Keep facets as query-param client state over existing pages only.
- **[Phase 30] Reintroducing the react-leaflet `<GeoJSON>` re-render-on-hover bug** during the control-shell refactor. Explicit Opus code-review acceptance criterion bans `<GeoJSON>`/`<Marker>`-as-JSX-child patterns.
- **[Phase 32/33] Cron billing-lapse / empty-string-secret silent failures recurring** — both have already happened once (a full week of news freshness lost silently). Mitigate with explicit non-empty-secret assertion steps and a freshness/heartbeat guard covering all three data crons.

### Research Flags for Planning

- **Phase 18 — plan interactively (NOT autonomous):** Normalization method final decision; SII cap threshold (recommended: sii_workers / ine_population > 5.0 → INE fallback); schema migration consumer enumeration; SPD VHC reference year confirmation (cap at 2024 until SPD confirms 2025 as final); composite_config.py metric weights (homicide 0.30 recommended, then violent families, then property, then incivilidades).
- **Phase 21 — scope prose engine before committing:** buildComparisonProse() must generate substantively different text per pair from real trend data; priority-pair allowlist exact count must be computed from actual commune data before getStaticPaths is written. Scope these two sub-problems in planning before committing to page count.
- **Phase 22 — standard patterns, no research needed:** All steps are documented human actions; see DEPLOYMENT.md and memory `prod-deploy-hook-secret-gap`.
- **Phase 26 — plan interactively (high-risk):** numeric pairwise-precision GO threshold is locked at 100%/zero-false-merges but the LLM call pattern (batched vs. pairwise/iterative) and candidate window size (same-day vs. ±1 day) are Phase 26 planner decisions.
- **Phase 27 — verify at kickoff:** does `data/cead/meta/index.json` carry `region_id` per commune? Must confirm before finalizing the CUT→region derivation. Consider (optional) adding a `facets.mjs` build-time validator to the 14-validator suite.
- **Phase 28 — standard pattern:** SSG faceting is already proven in this codebase (`news.astro`'s `monthGroups`); decide the cluster "primary article" tie-break rule (earliest date? highest confidence?) during planning if Phase 26 was GO.
- **Phase 30 — needs a follow-up read of `IncidentPinLayer.ts`:** whether Phase 28's clustered-event UI needs a new grouped-marker map-pin treatment; explicit decision needed on whether to close the `?region=` gap as part of this rework.
- **Phase 33 — explicit per-action decision needed:** SHA-pin vs. major-version-tag for each third-party action (e.g. `rhysd/actionlint`) — not a blanket rule.

### Todos

- (populated during planning)

### Blockers

- (none)

### Fable Decisions — v2.1 Autonomous Run

Decisions taken inline by the Fable orchestrator during the unattended run. Each is binding; do not reopen in phase plans.

| # | Date | Phase | Decision | Rationale |
|---|------|-------|----------|-----------|
| F-01 | 2026-07-29 | 26 | Proceed to planning with **no CONTEXT.md**; the autonomous directive is the decision source of record (`skip_discuss: true`, `mode: yolo`). | Directive authorizes unattended decision-making; its "planner decisions already taken" section supplies the locked context CONTEXT.md would have held. |
| F-02 | 2026-07-29 | 26 | rapidfuzz pre-filter threshold **frozen at 45.0** (`token_set_ratio`) for the whole phase — may NOT be tuned after any precision number is observed. | Tuning post-measurement is exactly the circularity the 100%-precision gate exists to prevent. Premortem measured min score 48.7 on both mandatory buckets → 45.0 is a lexical floor, not a cost control. |
| F-03 | 2026-07-29 | 26 | Mergeable state = `same_event is True AND confidence == "high"`. `confidence: "low"` merges are **never** accepted. | Precision-biased per the locked zero-false-merge gate. |
| F-04 | 2026-07-29 | 26 | **No ±1-day bucket widening** in Phase 26 — same-day `(cut, date)` buckets only. Revisit in Phase 28 only if a real cross-day miss is observed. | Both mandatory hard buckets are same-day; widening inflates the pair universe and LLM cost without adding adversarial value. |
| F-05 | 2026-07-29 | 26 | The pre-declared "reporting noise" label on the Tongoy 4102 bucket is **REVOKED**. `6eed24180c36dbec` ("19 años / homicidio") is presumed a DISTINCT event from the other seven ("8 años y medio / homicidio frustrado") unless source articles affirmatively prove one case. Same standard applied to 2101 Event C for `16439f8dc78173a6` and `b01de8947aa555f6`. | A mislabel in the `merge` direction is the ONLY direction that inflates precision — and the pre-declared label did exactly that. A 10.5-year sentence delta plus consummated-vs-frustrated is the signature of a different case. |
| F-06 | 2026-07-29 | 26 | Blind second pass on every `merge`-labeled pair is **mandatory**: a separate subagent sees only titles/outlets/URLs — never the first pass's label or the `cached_verdict`. Disagreement → `no_merge`, or `excluded: "label_disputed"` (out of the precision denominator, reported separately). | Golden-set labels are the oracle; an unchecked label makes the 100% gate measure nothing. |
| F-07 | 2026-07-29 | 26 | A GO requires `fp == 0` **AND** `tp > 0` **AND** `n_failsafe == 0`. `precision = None` when `tp + fp == 0` — a zero-denominator run is a STATE.md blocker, never a GO. An import/collection/runtime error is likewise a blocker, never a NO-GO verdict. | Without this, a run where every LLM call failed (e.g. missing `OPENROUTER_API_KEY`, which surfaces as an empty string in this project) would read as precision 1.0 → a GO on zero evidence. |
| F-08 | 2026-07-29 | 26 | On NO-GO the gate test is quarantined with `@pytest.mark.xfail(strict=True)` — never by weakening its assertion — so the suite exits 0 for phases 27–33 while the verdict stays encoded and re-arms if a future model passes. | The directive requires every phase to leave the suite green; the original plan made GO and NO-GO mutually exclusive with that rule. |
| F-09 | 2026-07-29 | 26 | Added a hand-constructed **cross-bucket typo/homophone `no_merge` sub-set** (~8–12 pairs, different `cut` values with lexically confusable comuna names) that bypasses `(cut, date)` bucketing by construction. | CLUS-01's third adversarial class was otherwise unreachable: exact-`(cut,date)` grouping can never emit a cross-comuna pair. ~12 extra calls. |
| F-13 | 2026-07-29 | 26 | Blind second pass executed: 4 independent Opus reviewers over interleaved batches, shown only `pair_id`/titles/outlets. Raw result: 33 `same`, 0 `different`, 5 `unsure` over the 38 `merge` labels. **Excluded 8 pairs, not the 5 flagged** — every merge pair involving article `9b1e83` is excluded as `label_disputed`, because reviewers contradicted *each other* about that same article depending on which partner it was paired with (3 `unsure`, 3 `same`). | The inconsistency localizes the ambiguity to the article ("8 años" vs "8 años y medio"), not to particular pairs — the same defect class the premortem found in `6eed24180c36dbec`. Excluding only the flagged pairs would have left the ambiguous article scoring TPs elsewhere. Golden set retains 86 non-excluded pairs (inside the 60–100 bound) and 30 independently-confirmed merges. |
| F-11 | 2026-07-29 | 26 | Phase 26's Wave 2 is dispatched in three orchestrator-managed steps rather than one executor run: (a) executor produces the draft + first-pass labels, (b) **the Fable orchestrator itself runs the blind second pass** by spawning independent reviewer agents, (c) executor performs the live verdict fill. | `gsd-executor` has no Agent tool (its registry grants Read/Write/Edit/Bash/Grep/Glob only), so it structurally cannot spawn the independent reviewers F-06 mandates. Leaving the instruction in the plan would have produced a silently-skipped gate or a self-review by the same agent that wrote the labels — the exact circularity F-06 exists to prevent. |
| F-12 | 2026-07-29 | 26 | Fixed a pre-existing 1-line `sys.path` bug in `pipeline/tests/test_build_enusc_enrichment.py` (Phase 23-02) out of band, rather than deferring it. | All 5 tests in that file had been failing with `ModuleNotFoundError` since they were written (confirmed at `f094142`, before Phase 26). The directive requires every phase to leave the suite green; carrying 5 known-red tests would have made that gate meaningless for phases 27–33. Suite: 307 passed/5 failed -> 312 passed. |
| F-10 | 2026-07-29 | 26 | Accepted the cumulative append-only `26-CALL-LOG.md` ledger with a refuse-to-start guard **in place of** a bare `_MAX_LLM_CALLS` constant, seeded with the 3 spike-ping calls. | Stronger than the constant: it survives resumed runs and counts cumulatively across the phase, which a per-process constant cannot. |

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260616-huj | Clarify crime-ranking rate labels (denuncias per 100k residents, 1 decimal, bilingual explainer) | 2026-06-16 | 4be9045 | [260616-huj-clarify-rate-labels](./quick/260616-huj-clarify-rate-labels/) |
| 260616-klv | Audit drug rates; fix national/region aggregation to population-weighted mean | 2026-06-16 | 5b997e4 | [260616-klv-auditar-tasas-drogas-100k-anomalas-modo-](./quick/260616-klv-auditar-tasas-drogas-100k-anomalas-modo-/) |
| 260616-ldi | Fix region_id grouping (BUGFIX-999.1): derive region from CUT length; all 16 regions now populate | 2026-06-16 | cad6a20 | [260616-ldi-fix-region-id-grouping-backlog-999-1-der](./quick/260616-ldi-fix-region-id-grouping-backlog-999-1-der/) |
| 260616-lu4 | Make ranking tables dynamic via progressive enhancement | 2026-06-16 | 2a550bd | [260616-lu4-hacer-dinamicas-las-tablas-rankings-de-c](./quick/260616-lu4-hacer-dinamicas-las-tablas-rankings-de-c/) |
| 260618-x95 | Fix prod-deploy gap: new deploy-on-code.yml curls CF Deploy Hook on push to master touching site/** | 2026-06-19 | 18b558b | [260618-x95-deploy-on-code](./quick/260618-x95-deploy-on-code/) |
| 260702-wjr | News-cron fixes: pre-public secret audit (clean), Fase 25 sync+deploy, GH Issue alerting on pipeline failure, freshness validator #15, --retry-all-errors deploy hook, CEAD PYTHONPATH fix | 2026-07-03 | b12067b | [260702-wjr-news-cron-fix-sequence-pre-public-secret](./quick/260702-wjr-news-cron-fix-sequence-pre-public-secret/) |
| 260703-cvd | Clarify commune percentile card copy: "Más delitos reportados que el {pct}%" / "More reported crime than {pct}%" (EN+ES), drop parenthetical from national label | 2026-07-03 | aafffa4 | [260703-cvd-clarify-commune-page-percentile-copy-rep](./quick/260703-cvd-clarify-commune-page-percentile-copy-rep/) |
| 260620-hrh | Per-comuna year selector (whole-page, vanilla JS, default year static for SEO) + static SVG longitudinal charts (7 families + homicide/year), EN+ES | 2026-06-20 | ff57ba9 | [260620-hrh-anio-selector-graficos-longitudinales-po](./quick/260620-hrh-anio-selector-graficos-longitudinales-po/) |
| 260620-cps | Align ranking/methodology copy to "casos policiales" (denuncias + detenciones flagrantes); fix stray "denuncias" mislabels that contradicted the documented measure, EN+ES | 2026-06-20 | 2feb81a | [260620-cps-alinear-copy-casos-policiales](./quick/260620-cps-alinear-copy-casos-policiales/) |
| 260703-e83 | Fix P0 ranking-table bugs: stale rank column on year change, comparator links 404 (only enabled pairs), similar-communes table silently static (missing ratesByYear) | 2026-07-03 | 52d82e3 | [260703-e83-fix-p0-ranking-table-bugs-stale-rank-col](./quick/260703-e83-fix-p0-ranking-table-bugs-stale-rank-col/) |
| 260703-fjh | Expand news sources: Google News RSS (1 national + 4 regional queries, source-tag attribution) + La Cuarta Arc feed; cross-outlet dedup verified by test | 2026-07-03 | 835e636 | [260703-fjh-expand-news-sources-add-google-news-rss-](./quick/260703-fjh-expand-news-sources-add-google-news-rss-/) |
| 260726-dqf | Adopt Granite 4.1 8B (OpenRouter) as default news classifier per spike 008 (commune 100% vs 95.45%, ~6-11x cheaper, 2.6x faster); family-whitespace guard; DeepSeek/MiniMax stay selectable via NEWS_PROVIDER | 2026-07-26 | 0dc42f7 | [260726-dqf-adopt-granite-4-1-8b-openrouter-as-defau](./quick/260726-dqf-adopt-granite-4-1-8b-openrouter-as-defau/) |
| 260726-ep0 | R2 research archive: daily cron uploads consolidated incidents (JSONL/CSV + APA citations), full article text via trafilatura (append-only, SHA-256, 100/run cap), url-ledger + corpus-state to bucket ischilesafe; live-verified 1264 incidents | 2026-07-26 | 820aac1 | [260726-ep0-archive-all-news-incidents-to-r2-with-ap](./quick/260726-ep0-archive-all-news-incidents-to-r2-with-ap/) |
| 260726-gf7 | Google News URL decoder (batchexecute, live-verified) + archive rejected candidates (data/incidents/rejected/, corpus schema v2, kind-aware ledger) + security hardening (SSRF redirect+DNS guards, CSV injection, robustness); code review 2 CRITICAL+5 warnings all fixed; 288 tests | 2026-07-26 | 3f9648a | [260726-gf7-google-news-url-decoder-archive-rejected](./quick/260726-gf7-google-news-url-decoder-archive-rejected/) |
| 260726-jya | Bump all GitHub Actions pins to v7 (Node-24 era): checkout v4→v7, setup-python v5→v7, setup-node v4→v7 across 4 workflows; clears Node-20 deprecation annotations | 2026-07-26 | 787a239 | [260726-jya-bump-github-actions-to-node-24-versions-](./quick/260726-jya-bump-github-actions-to-node-24-versions-/) |
| 260726-k23 | Full system health verification (no code): both crons live-dispatched green + Node-20 annotation gone (v7 validated), Granite + rejected-capture (16 items) working, R2 corpus v2 with 248 full-text articles + gnews decoder recovering URLs (133 fetched), 288 tests, 0 secret leaks | 2026-07-26 | verify | [260726-k23-verify-full-system-health-v7-workflow-bu](./quick/260726-k23-verify-full-system-health-v7-workflow-bu/) |
| 260727-j6z | News-only "sexuales" family (classifier prompt + news schema + EN/ES labels; CEAD 7-family contract untouched), deterministic repair of mis-classified incidents (25 flipped vida→sexuales across current.json + archive, R2 incidents.csv/corpus-state rebuilt and verified), browser-language redirect on EN pages (hreflang-based, lang-pref persisted) | 2026-07-27 | 3ffc6d8 | [260727-j6z-fix-granite-classifier-sexual-crimes-mis](./quick/260727-j6z-fix-granite-classifier-sexual-crimes-mis/) |

## Session Continuity

**Last session**: 2026-07-29 — v2.1 roadmap created: `.planning/ROADMAP.md` appended with Phase Details for 26–33, dependency graph (26 gates only clustering-in-27/28; 27 independent; 29 hard-gates 30), risk annotations (26 high-risk, 30 regression-risk), and mandatory per-phase protocol. `.planning/REQUIREMENTS.md` traceability filled: 54/54 requirements mapped to Phases 26–33, 100% coverage, no orphans. `.planning/STATE.md` updated: total_phases=8, Current Position points at Phase 26 as next to plan (Phase 27 can run in parallel — no dependency on 26). Next: `/gsd:plan-phase 26` (and/or `/gsd:plan-phase 27` in parallel).
**Prior session**: 2026-06-20 — Phase 21 Plan 04 complete: avs-b-budget.mjs registered as validator #14 in all.mjs; 14/14 validators green; 1258 dist files (margin 16742 vs 18000 limit); 10/10 prose sample PASS programmatically. Phase 21 COMPLETE (4/4). Pending human: visual prose acceptance + GSC URL Inspection before expanding batch beyond 20 pairs.
**Prior session (2026-06-19, v2.0 roadmap)**: v2.0 milestone roadmap written. 21/21 requirements mapped: CI-01..CI-10 → Phase 18, CMP-01..CMP-07 → Phase 21, GL-01..GL-04 → Phase 22. Phase 18 is the reserved number (intentional gap from v1.3). Hard dependency: Phase 21 depends on Phase 18. Phase 22 parallel with Phase 21. AdSense/Consent Mode deferred.
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
- [Phase ?]: 26-01: rapidfuzz pre-filter threshold 45.0 kept frozen per F-02
- [Phase ?]: Phase 26-02: adjudicate_pair recovers leading JSON via raw_decode when the model appends trailing prose after valid JSON (deterministic bug found during live fill).

## Operator Next Steps

- **Plan Phase 26 (Event Clustering Spike): `/gsd:plan-phase 26`** — highest-risk phase this milestone; must lock the LLM call pattern (batched vs pairwise) and candidate window size during planning; the numeric GO gate (100% precision, zero false merges) is already locked in REQUIREMENTS.md.
- **Plan Phase 27 (News Facet Data Model) in parallel: `/gsd:plan-phase 27`** — has zero dependency on Phase 26; first task should verify `region_id` presence on `data/cead/meta/index.json`.
- Phase 29 (Map UX Design Loop) can also start independently — remember the BrowserOS constraints (run inline, no viewport resize, `npx astro preview --port 4321 --host`, chain build+validate in one command).
- Phase 22-03 (GSC sitemap submission) remains an outstanding deferred human/manual task, carried forward but not part of v2.1.
