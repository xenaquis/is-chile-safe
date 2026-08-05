# REQUIREMENTS — Milestone v2.1 News Intelligence, Map UX & Ops Hardening

**Defined:** 2026-07-29
**Source:** v2.1 milestone research (`.planning/research/SUMMARY.md` + STACK/FEATURES/ARCHITECTURE/PITFALLS) plus user scoping decisions taken at milestone kickoff.
**Goal:** Make the news layer explorable (facet by time / geography / crime family, and group reports of the same real-world event), make the map genuinely usable (news toggle and filters discoverable on desktop and 375px mobile), and close the outstanding documentation, cron-consistency and security-posture debt.

**Previous milestone:** v2.0 requirements archived at `milestones/v2.0-REQUIREMENTS.md`. One item remains open there and is **carried forward as a deferred, human-only task**: GL-04 / Phase 22-03 — Google Search Console sitemap submission. It is not a v2.1 requirement and no v2.1 phase depends on it.

---

## Locked decisions (taken at kickoff — treat as settled, not open design questions)

These came out of research convergence plus explicit user choices. A phase plan that reopens one of them is wrong unless it presents new evidence.

| Decision | Value | Why |
|---|---|---|
| **Clustering GO gate** | **100% pairwise precision — zero false merges** on the golden set. Recall is unconstrained. | Under-grouping is invisible and harmless; over-grouping publishes a false factual claim on a safety site. A single false merge in the golden set is a NO-GO. |
| **Facet URL strategy** | **Query params only** (`?family=&region=&window=`) on the existing `/news/` and `/es/noticias/`. No new indexable facet URLs. | Avoids thin/duplicate content, canonical/hreflang burden, and pressure on the shared Cloudflare 20K-file budget. All four researchers converged here. |
| **Facet computation** | **Astro build time**, in a shared `site/src/lib/newsFacets.ts`, reading data via `process.cwd()`. | Keeps everything pre-rendered and indexable. `import.meta.url` already broke the EN news page once. |
| **New dependencies** | `rapidfuzz` (pipeline only) + `zizmor` (CI only). Nothing else, and **zero new shipped frontend JS**. | Research verdict: no facet library, no new React island, no popover/positioning library, no embeddings API. |
| **Map controls** | Native `<details>`/`<dialog>` + CSS. Leaflet's own `L.Control` owns in-map placement. | Matches the existing zero-JS nav pattern; no framework added. |
| **Leaflet layer code** | `ChoroplethLayer.ts`, `IncidentPinLayer.ts`, `LowZoomDotLayer.ts` are **protected** — imperative `L.geoJSON()` stays. Declarative react-leaflet layer components are banned. | Reintroducing `<GeoJSON>` would restore the documented re-render-on-hover jank this repo deliberately avoided. |
| **Anti-features — actively rejected** | No heat-map / density visualization. No severity or risk score. No "breaking" badges. No opaque event merging without visible constituent sources. | A density surface or a single severity number functions as an absolute "dangerous zone" label regardless of disclaimer text — direct conflict with the hard editorial constraint. |

## Per-phase protocol (mandatory, every phase)

Every phase in this milestone runs: **research → plan → premortem → plan review by a Fable agent → implementation by Sonnet → code review by Opus → GSD validation.** Phases are deliberately granular so each cycle fits in one context.

## Gates

- **Phase 26 gates the clustering portions of 27/28 only.** Phase 27's faceting work has **no dependency** on the spike outcome and must not be sequenced as blocked.
- **Phase 29 gates Phase 30.** No map code is rewritten until a BrowserOS-verified design is accepted by a human.

---

## v2.1 Requirements

### Event Clustering Spike (→ Phase 26)

- [x] **CLUS-01**: A hand-labeled golden set of 60–100 article pairs / small clusters is built from `data/incidents/archive/`, including adversarial near-misses (same comuna + same date but genuinely different crimes; same crime reported with a misspelled or homophonous comuna; and true same-event coverage from 2–3 outlets).
- [x] **CLUS-02**: A `rapidfuzz`-based lexical pre-filter narrows LLM candidate pairs to the existing `(cut, date)` buckets (optionally ±1 day), so LLM comparison cost is bounded and never O(n²) over the whole store.
- [x] **CLUS-03**: The LLM adjudicator returns a structured, fact-based verdict (corroborating location / entity / time-window facts plus rationale) at temperature 0.0 — never a bare similarity score — and an unparseable verdict is rejected as no-merge rather than defaulting permissively.
- [x] **CLUS-04**: RSS-derived article text is treated strictly as untrusted data and never as instructions, with the prompt structured so injected content cannot alter the adjudication task.
- [x] **CLUS-05**: Cluster IDs are derived deterministically as a `sha256` of the sorted set of member incident IDs — never from LLM output — so re-runs are bit-stable and cannot churn `data/` or fire spurious Cloudflare rebuilds.
- [x] **CLUS-06**: Cluster assembly uses connected components with a high edge threshold plus a max-cluster-size sanity cap (any cluster larger than 4 members is flagged for manual review, not published silently), and the full pairwise decision matrix per cluster is logged.
- [x] **CLUS-07**: The spike reports measured pairwise precision and recall against the golden set, plus actual per-run LLM cost, and issues an explicit **GO / NO-GO** verdict against the locked gate: **100% precision, zero false merges**.
- [x] **CLUS-08**: The precision check is encoded as a pytest regression (`pipeline/tests/test_clustering.py`), not a one-off spike script, so a future model swap cannot silently regress clustering quality.
- [x] **CLUS-09**: On GO, `cluster_id: str | None` and `is_primary: bool` are added to `IncidentRecord` as optional-with-default fields, verified backward-compatible against existing `current.json` and archive consumers; on NO-GO, the finding is documented and no schema change ships. **Satisfied via NO-GO branch (2026-07-29): fp=11, no schema change shipped — see `.planning/phases/26-event-clustering-spike/26-SPIKE-REPORT.md`.**

### News Facet Data Model (→ Phase 27)

- [x] **FACET-01**: A shared `site/src/lib/newsFacets.ts` computes facet indexes at build time from `data/incidents/current.json` plus the monthly archive, reading data via `process.cwd()`, and is consumed by both `/news/` and `/es/noticias/` so the two locales cannot drift.
- [x] **FACET-02**: Time facets expose day-granularity presets (today / 7d / 30d) plus monthly-archive access — no calendar-range slider, and sparse days are rolled up rather than rendered as empty per-day slots.
- [x] **FACET-03**: Geography facets resolve each incident's `cut` to its region via the established CUT-length derivation, giving a 16-region drill-down. ✅ *Open question CLOSED 2026-07-29: `data/cead/meta/index.json` entries carry `region_id` per commune (verified) — use it as the authoritative cross-check for the derivation.*
- [x] **FACET-04**: Crime-family facets cover all 8 news families including the news-only `sexuales`, without extending CEAD's `FAMILY_KEYS` (which stays at 7).
- [x] **FACET-05**: Per-option facet counts are computed at build time and available to the UI (e.g. "Robo (14)").
- [x] **FACET-06**: No facet artifact is written under `site/**` and no new derived JSON is committed — facets are computed in-build, so the existing data-change-gated deploy hook cannot be triggered by facet computation.
- [x] **FACET-07**: The existing validator suite and page-count budget stay green: `@astrojs/check` clean on new code, all validators pass, and no new indexable URLs are introduced.

### News Visualizer UI (→ Phase 28)

- [x] **NEWSUI-01**: A user can filter the news list by time window, region, and crime family, with per-option counts visible, on both `/news/` and `/es/noticias/`.
- [x] **NEWSUI-02**: The unfiltered superset of incidents is fully pre-rendered in static HTML; filtering is progressive enhancement only, so no incident content is invisible to Google or to a JS-disabled reader.
- [x] **NEWSUI-03**: A user can search comunas by typeahead (accent-insensitive, reusing the established directory-finder pattern) instead of scanning a 346-item select.
- [x] **NEWSUI-04**: Filter state is reflected in shareable query params and restored on load, and a zero-result combination renders a clear bilingual empty state that is never itself indexed as a thin page.
- [x] **NEWSUI-05**: On Phase 26 GO, clustered events render as a primary-article card with an "N fuentes / N sources" badge that always exposes every constituent outlet and URL — no source is ever hidden or overwritten by grouping. On NO-GO the page ships faceting only, degrading gracefully.
- [x] **NEWSUI-06**: Any LLM-produced text surfaced in the UI (rationale, grouped-event summary) is escaped, and the page adds no measurable CLS or hydration regression versus the current zero-JS news page.
- [x] **NEWSUI-07**: EN/ES parity holds for every new string, with i18n keys in `i18n.ts` as the single source of truth (not per-locale inline literals), and ES localized slugs hardcoded where `getRelativeLocaleUrl()` cannot translate them.

### Map UX Design Loop (→ Phase 29)

- [ ] **MAPUX-01**: The current map is driven in BrowserOS against a real served build (`npx astro preview --port 4321 --host`), and the baseline discoverability problem is captured with screenshots at desktop and at 375px (emulated via a 375px iframe — BrowserOS has no viewport resize).
- [ ] **MAPUX-02**: The control-shell design is **iterated in a loop** — screenshot → redesign with a Fable agent → apply → re-screenshot — repeating until the design is excellent. A single audit pass does not satisfy this requirement; the loop and its iterations are the deliverable.
- [ ] **MAPUX-03**: Each iteration is evaluated against concrete criteria, not taste alone: can a first-time user find and activate the news layer; can they find the filters; are touch targets ≥44px at 375px; is there any keyboard or focus trap; do controls avoid occluding the map or conflicting with Leaflet panes.
- [ ] **MAPUX-04**: A lightweight live click-through of comparable products (police.uk, CityProtect) firms up the medium-confidence UX pattern claims before the design is locked.
- [ ] **MAPUX-05**: The loop terminates in an accepted design spec plus a human acceptance gate; Phase 30 does not start until that gate passes.

### Map Control-Shell Rework (→ Phase 30)

- [ ] **MAPSH-01**: The news layer has an always-visible, explicitly labeled toggle — it is no longer buried inside a generic "mode" control. This is the specific complaint that motivated the milestone.
- [ ] **MAPSH-02**: The filter panel is redesigned per the Phase 29 spec using native `<details>`/`<dialog>` and CSS, with a bottom-sheet or FAB pattern on mobile rather than filters nested inside the hamburger nav, and zero new shipped JS dependencies.
- [ ] **MAPSH-03**: All map controls are keyboard-operable and screen-reader-labeled, with no focus traps, touch targets ≥44px at 375px, and no z-index conflict with Leaflet panes.
- [ ] **MAPSH-04**: The `?region=` deep link is implemented to match the existing working `?cut=` behavior, including graceful degradation on an unknown value (no 404 or console error).
- [ ] **MAPSH-05**: Changes are confined to `MapTopbar.tsx` and sibling control components; `ChoroplethLayer.ts`, `IncidentPinLayer.ts`, and `LowZoomDotLayer.ts` are untouched, and the Opus code review explicitly verifies that no declarative react-leaflet layer component (`<GeoJSON>`, `<Marker>`-as-JSX-child) was introduced.
- [ ] **MAPSH-06**: Existing map behavior is regression-verified after the refactor: `?cut=` deep link, choropleth year/family filters, commune panel, geolocation, and incident pins all still work.
- [ ] **MAPSH-07**: Map filters and news facets share vocabulary through common data (`familyDefs.ts`, `data.ts`) without creating a code dependency between the map island and the news pages.

### Docs & Methodology Refresh (→ Phase 31)

- [x] **DOCS-01**: The EN + ES methodology pages are brought current with what the code actually computes today — composite index, ENUSC victimization layer, the news-only `sexuales` family, and the directional meaning of `national_rank` (rank #1 = most reported crime, not safest) — closing all prose-vs-computation drift.
- [x] **DOCS-02**: Editorial and legal disclaimers are reaffirmed across the affected pages: "reported incidence" framing, under-reporting caveats, and no absolute safe/dangerous verdict.
- [x] **DOCS-03**: `data/SOURCES.md` is current and canonical, the outstanding ENUSC `[verify edition]` year is resolved, and CEAD plus every press outlet is correctly attributed.
- [x] **DOCS-04**: The clustering behavior and the facet semantics are documented for readers — how same-event grouping works, what each facet means, and the measured limits and error rate — required if Phase 26 returned GO.
- [x] **DOCS-05**: `site/scripts/validate/figure-registry.mjs` <!-- path corrected 2026-08-03: this requirement and the ROADMAP both said `scripts/validators/`, which has never existed in this repo; the real directory is `scripts/validate/` --> is hardened so substring matching can no longer report green against a stub section, and the full validator suite plus pytest stay green.
- [x] **DOCS-06**: EN/ES parity holds and no existing anchor that other pages link to is broken by the rewrite.

### Cron Consistency (→ Phase 32)

- [x] **CRON-01**: Every workflow asserts that each secret it consumes is non-empty before doing work, and fails loudly otherwise — closing the documented gotcha where an unset GitHub secret arrives as an empty string and produces a green run that did nothing.
- [ ] **CRON-02**: A freshness/heartbeat guard covers all three data crons (news daily, R2 research archive, CEAD quarterly reminder) with cron-drift-tolerant thresholds, so a silent stall is detected rather than discovered weeks later — this project already lost a full week of news freshness to an Actions billing lapse with no alert.
- [x] **CRON-03**: Deploy-hook retry and backoff behavior is reconciled to one consistent policy across all workflows that call it (currently three different retry counts).
- [x] **CRON-04**: Issue labels are made specific per pipeline instead of shared generic labels across unrelated workflows, so an alert identifies its own source.
- [x] **CRON-05**: The CEAD cron's expected-to-fail status is documented in the workflow itself (Actions runner IPs are 403'd; the scraper runs locally and the cron serves only as a reminder), so it cannot be misread as a real failure or silently "fixed".
- [x] **CRON-06**: Every workflow that writes `data/` fetches and rebases before pushing, eliminating the race between concurrent crons touching the same files.
- [ ] **CRON-07**: The whole schedule surface is documented as one coherent table (schedule, trigger, secrets consumed, permissions, what it writes) and audited after Phase 28 wires clustering into the news pipeline, so cost and latency changes are accounted for.

### Security Posture (→ Phase 33)

- [ ] **SEC-01**: `GITHUB_TOKEN` defaults to read-only at the repository level, and every job declares a minimal explicit `permissions:` block.
- [ ] **SEC-02**: Third-party actions are pinned by full commit SHA with a version comment, with an explicit documented decision recorded for each (SHA-pin versus major-version tag).
- [ ] **SEC-03**: A `.github/dependabot.yml` is added (none exists today) covering the `github-actions`, `pip`, and `npm` ecosystems.
- [ ] **SEC-04**: `zizmor` runs in CI as an Actions-specific static analyzer (invoked via `pipx`/`uvx`, never added to `pipeline/requirements.txt`), alongside the existing `actionlint`, and its findings are triaged.
- [ ] **SEC-05**: No API key can leak into logs or committed artifacts; GitHub secret scanning and push protection status is verified manually on the repository settings (research could not check this via API).
- [ ] **SEC-06**: Scraping courtesy is verified — delays toward CEAD (a government server) and toward press RSS feeds are present and adequate, and clustering is confirmed not to have increased fetch volume against any upstream.

---

## Future Requirements (deferred, not this milestone)

- Facet-count-aware SEO surfaces (e.g. a hand-picked `/news/robos/` page) — deliberately out of Phase 27/28 scope to avoid thin content; revisit once real facet traffic exists.
- New grouped-marker visual treatment for clustered events on the map — a Phase 29/30 design question that may surface, explicitly deferred unless the design loop demands it.
- AdSense Consent Mode wiring + flipping `ADSENSE_ENABLED` — monetization, a future cycle.
- Embeddings-based clustering as a recall improvement — only if the lexical pre-filter plus LLM adjudication proves insufficient, and only after re-verifying OpenRouter embedding pricing.

## Out of Scope (explicit exclusions with reasoning)

- **Heat-map / density visualization of incidents** — functions as an implicit "dangerous zone" label regardless of disclaimer; direct conflict with the hard editorial constraint. Must be actively rejected in design review, not merely omitted.
- **Severity or risk scoring per incident** — no supporting schema field exists, and it would become an absolute danger label.
- **Real-time / "breaking" badges** — the pipeline is cron-driven, not sub-hourly; the badge would be false.
- **User-submitted incident reports / social layer** — already out of scope project-wide; needs a backend and moderation.
- **Client-side re-filtering library or a new React island for news** — volume (tens to low hundreds of records) never justifies the shipped JS, and it would put content behind hydration.
- **Pre-rendered facet URLs (region × family × time)** — thin content plus canonical/hreflang burden against a shared 20K-file budget.
- **Declarative react-leaflet layer components** — reintroduces the documented re-render-on-hover jank.
- **GSC sitemap submission (v2.0 GL-04 / 22-03)** — carried forward as a human/manual task; not a v2.1 requirement.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLUS-01 | Phase 26 | Complete |
| CLUS-02 | Phase 26 | Complete |
| CLUS-03 | Phase 26 | Complete |
| CLUS-04 | Phase 26 | Complete |
| CLUS-05 | Phase 26 | Complete |
| CLUS-06 | Phase 26 | Complete |
| CLUS-07 | Phase 26 | Complete |
| CLUS-08 | Phase 26 | Complete |
| CLUS-09 | Phase 26 | Complete (NO-GO branch) |
| FACET-01 | Phase 27 | Complete |
| FACET-02 | Phase 27 | Complete |
| FACET-03 | Phase 27 | Complete |
| FACET-04 | Phase 27 | Complete |
| FACET-05 | Phase 27 | Complete |
| FACET-06 | Phase 27 | Complete |
| FACET-07 | Phase 27 | Complete |
| NEWSUI-01 | Phase 28 | Complete |
| NEWSUI-02 | Phase 28 | Complete |
| NEWSUI-03 | Phase 28 | Complete |
| NEWSUI-04 | Phase 28 | Complete |
| NEWSUI-05 | Phase 28 | Complete |
| NEWSUI-06 | Phase 28 | Complete |
| NEWSUI-07 | Phase 28 | Complete |
| MAPUX-01 | Phase 29 | Pending |
| MAPUX-02 | Phase 29 | Pending |
| MAPUX-03 | Phase 29 | Pending |
| MAPUX-04 | Phase 29 | Pending |
| MAPUX-05 | Phase 29 | Pending |
| MAPSH-01 | Phase 30 | Pending |
| MAPSH-02 | Phase 30 | Pending |
| MAPSH-03 | Phase 30 | Pending |
| MAPSH-04 | Phase 30 | Pending |
| MAPSH-05 | Phase 30 | Pending |
| MAPSH-06 | Phase 30 | Pending |
| MAPSH-07 | Phase 30 | Pending |
| DOCS-01 | Phase 31 | Complete |
| DOCS-02 | Phase 31 | Complete |
| DOCS-03 | Phase 31 | Complete |
| DOCS-04 | Phase 31 | Complete |
| DOCS-05 | Phase 31 | Complete |
| DOCS-06 | Phase 31 | Complete |
| CRON-01 | Phase 32 | Complete |
| CRON-02 | Phase 32 | Pending |
| CRON-03 | Phase 32 | Complete |
| CRON-04 | Phase 32 | Complete |
| CRON-05 | Phase 32 | Complete |
| CRON-06 | Phase 32 | Complete |
| CRON-07 | Phase 32 | Pending |
| SEC-01 | Phase 33 | Pending |
| SEC-02 | Phase 33 | Pending |
| SEC-03 | Phase 33 | Pending |
| SEC-04 | Phase 33 | Pending |
| SEC-05 | Phase 33 | Pending |
| SEC-06 | Phase 33 | Pending |

**Coverage: 54/54 v2.1 requirements mapped to exactly one phase (Phases 26–33). No orphans, no duplicates.**
(9 CLUS + 7 FACET + 7 NEWSUI + 5 MAPUX + 7 MAPSH + 6 DOCS + 7 CRON + 6 SEC = 54)

Deferred (not a v2.1 requirement, tracked separately): v2.0 GL-04 / Phase 22-03 — GSC sitemap submission (human/manual).

---
*Requirements defined 2026-07-29 for milestone v2.1. Phase numbering continues from v2.0 — v2.1 starts at Phase 26.*
*Traceability filled by the roadmapper 2026-07-29 — 8 phases (26–33), 54/54 requirements mapped, 100% coverage.*
