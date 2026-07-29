# Project Research Summary

**Project:** Chile Safety Map (ischilesafe.com) — v2.1 "News Intelligence, Map UX & Ops Hardening"
**Domain:** Static-site (Astro/Cloudflare Pages) news faceting + LLM event clustering + Leaflet map control-shell UX + GitHub Actions cron/security hardening, layered on a live $0-budget bilingual crime-safety site
**Researched:** 2026-07-29
**Confidence:** HIGH overall (all four researchers read repo source directly; the one genuinely open unknown — the Phase 26 precision threshold — is a decision, not a knowledge gap)

## Executive Summary

v2.1 is not new-product work — it's disciplined extension of a stack that's already live and already has 14 validators + ~179 pytest guarding regressions. All four researchers converged, independently, on a "do almost nothing new" posture: no client-side faceting library, no new indexable facet URLs, no declarative react-leaflet, no popover/positioning JS library, no embeddings API, no new cron files. The single new runtime dependency across the entire milestone is `rapidfuzz` (a tiny pure-C pre-filter for event clustering), plus `zizmor` as a CI-only (non-shipping) security linter. This is a strong, convergent signal: the roadmap should treat "build-time computation, query-param client state, native HTML controls, imperative Leaflet" as settled architecture, not open design questions.

The riskiest work by far is Phase 26's LLM event-clustering spike: grouping multiple press articles that describe the same real-world crime. Every researcher flagged **false merges** (two distinct crimes collapsed into one displayed incident) as the top failure mode, for a site whose entire premise is accurate, attributed, per-incident reporting. Phase 26 is explicitly a gate — Phases 27/28 depend on its GO/NO-GO outcome, but critically, Phase 27 (faceting) is *not* blocked by Phase 26, since facets are a pure derivation over existing schema fields with zero new data or LLM dependency. The recommended approach is precision-biased evaluation (golden-set pairwise precision/recall, deterministic non-LLM-derived cluster IDs, connected-components with a max-cluster-size cap, structured fact-based LLM verdicts, RSS text treated as untrusted data never instructions) — but the actual numeric precision bar for GO is explicitly undefined by the researchers and must be set by the roadmapper or the Phase 26 planner, not assumed.

Secondary risks cluster around two already-scarred areas of this codebase: (1) SEO/SSG discipline — facet URLs must not explode into thousands of thin/duplicate pages against the Cloudflare 20K-file budget, and must not reintroduce the exact "render-only-in-client" bug class that already broke the EN news page once; and (2) cron/ops fragility — this project has already suffered a week-long silent billing outage and has a documented "empty-string secret" gotcha; Phase 32/33 must close these systematically rather than patch individually. Both are well-understood, low-ambiguity execution work once scoped correctly.

## Key Findings

### Recommended Stack

The headline finding is an *absence* of new frontend dependencies: news faceting is Astro-frontmatter + vanilla progressive-enhancement `<script>` (no `fuse.js`/`list.js`/Alpine/React island), and the map control-shell rework uses native `<details>`/`<dialog>` + CSS (no Radix/Floating UI/Popper — Leaflet's own `L.Control` positioning API already handles map-anchored placement correctly). The only two additions are backend/CI-side: `rapidfuzz==3.14.5` (pipeline, Phase 26 clustering pre-filter) and `zizmor` (CI-only Actions security static analyzer, Phase 33, invoked via `pipx`/`uvx`, never added to `requirements.txt`).

**Core technologies:**
- `rapidfuzz` 3.14.5 — cheap C++-backed fuzzy string pre-filter that narrows LLM clustering candidates to same-day/same-comuna pairs, bounding the O(n²) LLM cost problem — chosen over TF-IDF/scikit-learn (too heavy at this volume) and over embeddings (a second billed API surface with unproven marginal recall gain over lexical + LLM adjudication)
- Existing OpenRouter/DeepSeek client (Granite 4.1 8B default, DeepSeek v4-flash fallback) — reused as-is for clustering adjudication; per-task model selection is already this project's pattern and should extend the same way if Granite underperforms on clustering specifically
- `zizmor` — Actions-specific static analyzer (script-injection, unpinned actions, excessive `permissions:`) complementary to the already-present `actionlint` (syntax-only linter)
- Native `<details>`/`<dialog>`/Popover API — zero-JS-cost disclosure/modal semantics for the map control shell, matching the existing checkbox-based mobile-nav (WR-03) precedent

### Expected Features

**Must have (table stakes, from crime-map/local-news category norms — police.uk, CityProtect, SpotCrime):**
- Time-range presets (Today/7d/30d) + monthly archive access — never a calendar-range slider
- Region drill-down (16 regions) as primary geography facet + typeahead comuna search — never a flat 346-item `<select>`
- Category (crime-family) chips with multi-select, not single-select dropdown
- Facet counts shown per option, computed at build time ("Robo (14)")
- Graceful empty-state messaging for zero-result facet combinations
- URL-shareable filter state via query params, without making that the *only* path to content
- A visibly-labeled, always-visible map layer toggle for the news pin layer (today it's buried in a generic "mode" control)
- Mobile: bottom-sheet or FAB-triggered filter panel, not a hamburger-nested control

**Should have (differentiators):**
- Same-event clustering across outlets ("N sources report this") — gated on Phase 26 GO
- "Primary article + N related sources" card layout that keeps every constituent source individually visible
- Facet-count-aware SEO surfaces (e.g. a hand-picked `/news/robos/`-style page) — explicitly deferred, not in Phase 27/28 scope
- Sparse-day rollup framing ("3 incidents this week") rather than per-day sparklines that read as broken or as an implicit danger signal

**Defer / explicit anti-features:**
- Heat-map/density visualization of comuna-level incidents — conflicts with the "never seguro/peligroso" constraint, the single highest-risk anti-feature named in this milestone
- Severity/risk scoring — no supporting schema field, would functionally become an absolute danger label
- Real-time/"breaking" badges — pipeline runs on a cron, not sub-hourly
- User-submitted/crowd-sourced incident reports — already out of scope per PROJECT.md
- Auto-merging events with no visible constituent article list — violates the hard source-attribution constraint

### Architecture Approach

Facets are computed in Astro frontmatter at build time (a new shared `site/src/lib/newsFacets.ts`, imported by both `news.astro` and `es/noticias.astro`, following the existing `process.cwd()`-based data-resolution pattern) from the same `current.json` + `archive/*.json` the pipeline already writes — never a second committed derived-JSON artifact and never a client-only React island. Facet *state* lives in query params handled by progressive-enhancement JS over a fully pre-rendered superset page; no new indexable facet URLs are generated in Phase 27/28.

Event clustering is a new pipeline stage (`pipeline/news/clustering.py`) inserted *after* the existing cheap syntactic `dedup.py` step and *before* `merge_and_write()`, operating only on the deduped set to bound LLM cost. Cluster membership is persisted as two new optional-with-default fields directly on `IncidentRecord` (`cluster_id: str | None`, `is_primary: bool`) — additive, back-compatible, invisible to every existing consumer until they're explicitly updated.

The map control-shell rework is scoped to `MapTopbar.tsx` and sibling components only; `MapIsland.tsx`'s imperative Leaflet-layer effects (`ChoroplethLayer`, `IncidentPinLayer`, `LowZoomDotLayer`) are explicitly protected/unchanged. News facets and map filters share vocabulary (`familyDefs.ts`, `loadIndex()`/`data.ts`) as a common data source, never as a direct code dependency between the two pages.

**Major components:**
1. `newsFacets.ts` (NEW) — build-time facet index (byFamily/byRegion/byMonth/windows) shared by both locale news pages
2. `pipeline/news/clustering.py` (NEW, Phase 26 spike → Phase 28 wired) — LLM-assisted event grouping stage, deterministic `cluster_id` derived from sorted member-id hashes
3. Map control-shell components under `site/src/components/map/` (MODIFIED) — new/redesigned filter panel + news-toggle UI, driving existing React state setters
4. `.github/workflows/*.yml` (MODIFIED, Phase 32/33) — secret-emptiness guards, freshness/heartbeat checks, retry-count and issue-label reconciliation, SHA-pinning audit

### Critical Pitfalls

1. **False merges in LLM event clustering** — two distinct same-day/same-comuna crimes collapsed into one displayed incident. Mitigate with a structured fact-based verdict schema, a precision-biased threshold defaulting to no-merge on ambiguity, and a golden-set pairwise-precision gate before any GO decision.
2. **Facet/URL explosion causing thin content** — crossing time × 16 regions × 8 families as new indexable URLs would produce hundreds of near-empty pages against a shared 20K Cloudflare file budget. Mitigate by keeping facets as query-param client state over existing pages.
3. **Non-deterministic cluster IDs triggering needless rebuilds** — an LLM-derived cluster ID that isn't bit-stable run-to-run would fire the `git diff → deploy` cron trigger for zero real content change, burning the 500-builds/month free-tier budget. Mitigate by deriving cluster IDs from a hash of sorted member incident IDs.
4. **Reintroducing the react-leaflet `<GeoJSON>` re-render-on-hover bug** during the control-shell refactor. Mitigate with an explicit code-review acceptance criterion banning `<GeoJSON>`/`<Marker>`-as-JSX-child patterns.
5. **Cron billing-lapse / empty-string-secret silent failures recurring** — both have already happened once. Mitigate with explicit non-empty-secret assertion steps and a freshness/heartbeat guard covering all three data crons.

## Implications for Roadmap

Critical path: **26 → (27 in parallel) → 28 → 29 → 30**, with 31/32/33 as closing phases sequenced after 26–30's shape is known.

### Phase 26: Event clustering spike
**Rationale:** Gates 27/28's clustered-event scope; independent of Phase 27's faceting work.
**Delivers:** GO/NO-GO decision backed by golden-set pairwise-precision/recall; if GO, a defined `cluster_id`/`is_primary` contract and chosen model/prompt.
**Addresses:** "Same-event clustering across outlets" differentiator.
**Avoids:** False merges, transitive cluster drift, non-deterministic cluster IDs, O(n²) cost blowup, prompt injection, 8B-model weakness on Chilean short-text/place-name disambiguation.

### Phase 27: News faceting data model
**Rationale:** Pure derivation over existing schema fields — no dependency on Phase 26; should land before 28.
**Delivers:** `site/src/lib/newsFacets.ts`, wired into both locale news pages; verification that `region_id` exists on `data/cead/meta/index.json` entries.
**Addresses:** Time/region/family faceting table stakes.
**Avoids:** Facet URL explosion, canonical/hreflang errors, rebuild-loop reintroduction via a stray artifact under `site/**`.

### Phase 28: News visualizer UI
**Rationale:** Consumes Phase 27's facet lib; consumes Phase 26's `cluster_id` only if GO, degrading gracefully otherwise.
**Delivers:** Filter/grouping UI, SSG-safe; clustered-event cards with "N sources" badges if GO, always exposing every constituent outlet/URL.
**Addresses:** Facet-count UI, empty-state handling, cluster-card differentiator.
**Avoids:** Client-JS-only invisible content, CLS/hydration regression, unescaped LLM rationale text.

### Phase 29: Map UX audit (BrowserOS design loop)
**Rationale:** Gates Phase 30; independent of 26/27/28.
**Delivers:** Accepted control-shell design spec, iterated via repeated screenshot/redesign cycles at desktop + 375px.
**Addresses:** Map layer/filter discoverability table stakes.
**Avoids:** Mobile touch-target/gesture-conflict pitfalls, keyboard/screen-reader traps.

### Phase 30: Map control-shell rework
**Rationale:** Implements Phase 29's design; soft dependency on Phase 27 for shared vocabulary consistency.
**Delivers:** Redesigned filter panel + news toggle in `MapTopbar.tsx` and siblings; Leaflet logic untouched; closes `?region=` gap if design requires.
**Uses:** Native `<details>`/`<dialog>`, imperative `L.Control`/`L.geoJSON()`.
**Implements:** Desktop persistent toolbar + mobile bottom-sheet/FAB pattern.
**Avoids:** `<GeoJSON>` re-render jank, losing `?cut=`/`?region=` deep links, z-index/pane conflicts.

### Phase 31: Docs & methodology refresh
**Rationale:** Lands after 26–30's scope is finalized.
**Delivers:** Updated methodology/source-registry/attribution pages, EN+ES parity; closes `[verify edition]` ENUSC debt.
**Avoids:** Prose/computation drift, `figure-registry.mjs` false-green on stub sections, broken anchors, EN/ES parity gaps.

### Phase 32: Cron consistency
**Rationale:** Independent of feature work, but audits the pipeline shape *after* Phase 28's clustering wiring.
**Delivers:** Reconciled retry counts, per-workflow issue labels, freshness/heartbeat guard on all three data crons, `fetch+rebase`-before-push.
**Avoids:** Recurrence of the billing-outage failure class, concurrent-cron `git push` races, cron-drift false alarms.

### Phase 33: Security posture
**Rationale:** Parallel with or immediately after 32.
**Delivers:** Non-empty-secret assertion guards, read-only-default `GITHUB_TOKEN` confirmation, SHA-pinning decision for third-party actions, secret-scan CI step, confirmation clustering hasn't increased RSS fetch volume.
**Uses:** `zizmor`.
**Avoids:** Unset-secret silent no-ops, over-broad token permissions, unpinned supply-chain risk, API-key leakage.

### Phase Ordering Rationale
- Phase 26 is isolated (spike against existing archived data) so it can run first without blocking anything except clustering-specific portions of 27/28.
- Phase 27 has zero dependency on 26's outcome — the roadmap should make this explicit so it isn't accidentally sequenced as blocked.
- 29 gates 30 by design (human/BrowserOS acceptance gate), mirroring 26 gating 27/28.
- 31/32/33 are closing phases by nature and should not be front-loaded.

### Research Flags

Needs deeper research during planning:
- **Phase 26:** numeric precision/false-merge-rate GO threshold undefined — a required planner decision, plus the LLM call pattern (batched vs. pairwise).
- **Phase 27:** must verify `region_id` presence on `data/cead/meta/index.json` at kickoff.
- **Phase 30:** whether Phase 28's clustered-event UI needs a new grouped-marker map-pin treatment; needs a follow-up read of `IncidentPinLayer.ts` internals.

Standard patterns (research-phase optional):
- **Phase 28:** SSG faceting pattern already proven in this codebase (`news.astro`'s `monthGroups`).
- **Phase 31:** documentation refresh against known source files, no new architecture.
- **Phase 32/33:** standard GitHub Actions hardening, well-precedented in this repo's own history.

## The Phase 26 GO/NO-GO Gate — Consolidated Specification

- **Golden set:** hand-labeled, 60–100 article pairs/small clusters from `data/incidents/archive/`, including adversarial near-misses (same comuna+date/different crime; same crime/different comuna via typo/homophone; genuine same-event-from-2-3-outlets).
- **Primary metric: pairwise precision and recall**, not cluster-level V-measure/ARI alone (cluster metrics can mask a single catastrophic false merge).
- **Precision-biased, not balanced:** gate requires precision "above a strict bar (near-100% on the golden set) even at the cost of recall." **The exact numeric threshold is NOT defined by any researcher and must be set by the roadmapper or Phase 26 planner before the spike runs** — flagged explicitly, not invented here.
- **Deterministic cluster IDs:** `sha256` of the sorted set of member incident IDs, never from LLM output. Temperature 0.0 for all clustering calls.
- **Cost control:** bound LLM comparisons to existing `dedup.py` `(cut, date)` buckets (optionally ±1 day); incremental clustering only, never a full re-scan of the 30-day+archive store. Report actual per-run LLM cost in the spike findings doc.
- **Anti-transitivity guard:** connected-components with a high edge threshold + max-cluster-size sanity cap (flag any cluster >4 for manual review); log full pairwise decision matrices per cluster.
- **Structured, fact-based LLM verdict schema:** require concrete corroborating facts (location/entity/time-window + rationale), not a bare similarity score; reject unparseable verdicts rather than defaulting permissively. Treat RSS text strictly as data, never instructions.
- **Additive-only guarantee:** clustering never deletes/hides/overwrites `outlet`/`url`/`date`; every article's source stays independently visible even inside a merged card.
- **Regression-proof:** encode the precision-biased check as a pytest regression (`pipeline/tests/test_clustering.py`), not a one-off spike check, so future model swaps can't silently regress quality.

## Open Questions Carried Forward

- **[Phase 26]** Exact numeric pairwise-precision threshold for GO — must be set before the spike executes.
- **[Phase 26]** Single batched prompt vs. pairwise/iterative comparison — determines whether a new cost-control env var is needed.
- **[Phase 26]** Clustering candidate window size (same-day only vs. ±1 day) — a spike parameter.
- **[Phase 27]** Does `data/cead/meta/index.json` carry `region_id` per commune? Must verify at kickoff.
- **[Phase 27]** Add a new `facets.mjs` build-time validator to the existing 14-validator suite? Optional, roadmapper/planner decision.
- **[Phase 28]** Tie-break rule for a cluster's "primary" article (earliest date? highest confidence?) — not decided by research.
- **[Phase 30]** Does clustering require a new grouped-marker map-pin treatment? Deferred to the 29/30 design loop.
- **[Phase 30]** Close the `?region=` deep-link gap as part of this rework, or defer again? Needs an explicit decision either way.
- **[Phase 32]** Exact retry/backoff values and issue-label taxonomy — implementation choices, not prescribed.
- **[Phase 33]** SHA-pin vs. major-version-tag for third-party actions (`rhysd/actionlint`) — flagged as needing an explicit, documented decision.

## Watch Out For (Ranked)

1. **False merges in LLM event clustering** (Phase 26) — the single highest-risk failure mode; two real, distinct crimes silently shown as one is both a factual and credibility failure on a safety-information site.
2. **Heat-map/severity-scoring anti-features creeping in** — direct conflict with the "never seguro/peligroso" constraint; must be actively rejected in design review, not just avoided by omission.
3. **Facet/URL explosion breaking SEO or the Cloudflare 20K-file budget** (Phase 27/28) — the site already shares a tight page budget across comuna/region/crime-type pages.
4. **Reintroducing the react-leaflet `<GeoJSON>` re-render-on-hover bug** (Phase 30) — a previously-solved problem a "cleaner" declarative refactor could silently reintroduce.
5. **Cron billing-lapse / empty-string-secret failures recurring** (Phase 32/33) — this project has already lost a full week of pipeline freshness silently once.
6. **Non-deterministic cluster IDs burning the free-tier build budget** (Phase 26/32) — LLM non-determinism leaking into cluster-ID assignment would trigger spurious deploys against the 500-builds/month ceiling.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH (mechanics) / MEDIUM (OpenRouter pricing, embeddings catalog) | Astro/Leaflet/GH Actions claims verified against repo files directly; OpenRouter claims WebSearch-sourced, no Context7 entry |
| Features | MEDIUM overall (HIGH on data-mapping, MEDIUM on clustering-UX) | Data-shape claims verified against `schema.py`/live `current.json`; competitor patterns from training knowledge, not live-reverified |
| Architecture | HIGH | All claims verified by reading the actual cited repo files |
| Pitfalls | HIGH (repo-specific) / MEDIUM-LOW (general clustering-eval methodology) | Repo-specific pitfalls read from source/memory; general entity-resolution practice is standard knowledge, not live-verified |

**Overall confidence:** HIGH — repo-specific architecture/pitfall findings (load-bearing for phase sequencing) are source-verified; softer areas are corroborating context only.

### Gaps to Address
- Phase 26 precision threshold is an undecided parameter, not a research gap — flag to the Phase 26 planner as a required decision.
- `region_id` presence on `data/cead/meta/index.json` needs a one-line verification at Phase 27 kickoff.
- Competitor UX claims (police.uk, CityProtect) should get a lightweight live click-through during Phase 29's BrowserOS loop.

## Sources

### Primary (HIGH confidence)
- Direct repo reads: `site/package.json`, `pipeline/requirements.txt`, `.github/workflows/{ci,news-pipeline,cead-scraper,r2-archive,deploy-on-code}.yml`, `pipeline/news/{dedup.py,schema.py}`, `pipeline/scrape_news.py`, `site/src/pages/news.astro`, `site/src/components/map/MapIsland.tsx`, `data/incidents/current.json`, `.planning/PROJECT.md`, `CLAUDE.md`
- Project memory: `news-cron-billing-outage.md`, `r2-research-archive.md`, `granite-default-classifier.md`, `news-geolocation-ab-finding.md`, `map-focus-unknown-cut-polish.md`, `browseros-review-gotchas.md`

### Secondary (MEDIUM confidence)
- zizmor PyPI + Trail of Bits blog — active-release confirmation
- OpenRouter Granite 4.1 8B pricing + embedding models collection — WebSearch-sourced
- Competitor crime-map product patterns (police.uk, CityProtect, SpotCrime, Citizen, GDELT) — training-knowledge, converge across products
- General clustering-evaluation methodology — standard ML/NLP practice, not live-verified this pass

### Tertiary (LOW confidence)
- DeepSeek v4-flash pricing figures — aggregator-sourced
- Exact Leaflet pane z-index numbers — training-data knowledge

---
*Research completed: 2026-07-29*
*Ready for roadmap: yes*
