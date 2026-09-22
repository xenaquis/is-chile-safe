# Roadmap — Chile Safety Map (ischilesafe.com)

_Last updated: 2026-09-22 — v2.2 Data Integrity & News Recovery roadmap created (Phases 34-38)._

## Milestones

- ✅ **v1.0 MVP** — Phases 1–6 (shipped 2026-06-13) — full detail: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Polish & QA** — Phases 7–9 (shipped 2026-06-15) — full detail: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Map Fidelity, Findability & News** — Phases 10–17 (shipped 2026-06-18) — full detail: [milestones/v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)
- ✅ **v1.3 Data Quality Hardening & Methodology** — Phases 19–20 (shipped 2026-06-19) — _(Phase 18 deliberately reserved for Composite Crime Index)_
- ✅ **v2.0 Composite Index, Comparators & Launch** — Phases 18, 21, 22, 23, 24, 25 (shipped 2026-07; production live) — full detail: [milestones/v2.0-ROADMAP.md](milestones/v2.0-ROADMAP.md)
- ✅ **v2.1 News Intelligence, Map UX & Ops Hardening** — Phases 26–33 (shipped 2026-08-05; run unattended per `v2.1-AUTONOMOUS-DIRECTIVE.md`) — full detail: [milestones/v2.1-ROADMAP.md](milestones/v2.1-ROADMAP.md)
- 🔵 **v2.2 Data Integrity & News Recovery** — Phases 34–38 (OPEN, started 2026-09-22) — see below

> **Phase numbering note:** Phase 18 is the RESERVED slot for the Composite Crime Index (intentional gap in v1.3 which used 19 + 20). v2.0 used phases 18, 21, 22, 23, 24, 25 (there is no Phase 19/20 in v2.0 — those are archived v1.3 phases). v2.1 continued sequentially from v2.0's last phase and started at Phase 26. **v2.2 continues sequentially from v2.1's last phase and starts at Phase 34.**

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

Full phase details: **[milestones/v2.0-ROADMAP.md](milestones/v2.0-ROADMAP.md)**
Requirements: **[milestones/v2.0-REQUIREMENTS.md](milestones/v2.0-REQUIREMENTS.md)**
Audit: **[milestones/v2.0-MILESTONE-AUDIT.md](milestones/v2.0-MILESTONE-AUDIT.md)**

</details>

<details>
<summary>✅ v2.1 News Intelligence, Map UX & Ops Hardening (Phases 26–33) — SHIPPED 2026-08-05</summary>

- [x] Phase 26: Event Clustering Spike (4/4 plans) — verdict **NO-GO**, documented; no clustering shipped
- [x] Phase 27: News Facet Data Model (2/2 plans)
- [x] Phase 28: News Visualizer UI (3/3 plans)
- [x] Phase 29: Map UX Design Loop (2/2 plans) — a design contract, no code
- [x] Phase 30: Map Control-Shell Rework (6/6 plans)
- [x] Phase 31: Docs & Methodology Refresh (4/4 plans)
- [x] Phase 32: Cron Consistency (3/3 plans)
- [x] Phase 33: Security Posture (3/3 plans)

Executed as an unattended autonomous run under `v2.1-AUTONOMOUS-DIRECTIVE.md`.

Full phase details: **[milestones/v2.1-ROADMAP.md](milestones/v2.1-ROADMAP.md)**
Requirements: **[milestones/v2.1-REQUIREMENTS.md](milestones/v2.1-REQUIREMENTS.md)**
Audit: **[milestones/v2.1-MILESTONE-AUDIT.md](milestones/v2.1-MILESTONE-AUDIT.md)**

</details>

### 🔵 v2.2 Data Integrity & News Recovery (Phases 34–38) — OPEN

**Source of truth:** `.planning/research/v2.2-AUDIT-260922.md` (arbitrated multi-lens audit, 29 findings, 10 refuted). Requirements: `.planning/REQUIREMENTS.md` (NREC/FRESH/FID/DEPS/HYG, 33 requirements).

**⚠️ HARD DEADLINE: Phase 34 must be live before 2026-10-05.** `current.json`'s 30-day rolling window empties on that date (newest incident is currently frozen at 2026-09-04), which would blank `/news/`, `/es/noticias/`, the map incident pins, every commune "Recent Incidents" section, and the home news block.

**Pre-roadmap step (not a phase):** A `/gsd:quick` hotfix of the live erroneous cards (the Rosamel Fierro kinship-error cluster across 7 cards, and the prison-suicide item mislabeled "Delitos contra la Vida") runs **before** Phase 34 begins. FID-07 re-verifies this hotfix survives the pipeline and backfill changes.

**Protocol for every phase in this milestone (corrida-autonoma roles):** research (fresh Sonnet) → plan (Opus) → premortem + adversarial gate (fresh Opus arbiter) → implementation (Sonnet) → validation against served routes (Opus).

- [ ] **Phase 34: News Classification Restore, Fail-Loud Alarm & Outage Backfill** — replacement model chosen by metrics (A/B eval, DeepSeek direct as backup provider), preflight + circuit breaker + typed error outcomes, alarm on classification failure, honest heartbeat, backfill of the 2,073 lost outage items. **DEADLINE: before 2026-10-05.**
- [ ] **Phase 35: Honest Freshness Signals** — depends on Phase 34. Data-derived "Latest incident" stamps, stale notices, no false-zero histogram bars, byte-identical no-op runs, disclosed CEAD vintage.
- [ ] **Phase 36: Classification Fidelity & Attribution** — depends on Phase 34. Verbatim source headlines, family accuracy (vida stops being a catch-all), publisher URLs over Google News redirects, deterministic cross-run dedup.
- [ ] **Phase 37: Dependency & Security Hygiene** — depends on Phase 34 (DEPS-03 additionally needs the NREC-01 eval result). Astro advisory merge, Dependabot backlog triage, standing policy.
- [ ] **Phase 38: Pipeline, Public-Data, SEO & Docs Hygiene** — depends on Phase 34 and Phase 35. Public ledger exposure, `/map/` vs `/chile-crime-map/` cannibalization, seen-ledger pruning by `first_seen`, CEAD workflow `continue-on-error` removal, the Oct-1 local CEAD scrape (must run on/after 2026-10-01, operator step on the local machine), and docs/memory drift cleanup.

## Phase Details

_Every shipped phase's detail lives in its milestone archive under `milestones/`. v2.2 (open) is detailed below._

### Phase 34: News Classification Restore, Fail-Loud Alarm & Outage Backfill

**Goal**: Restore classification on a validated replacement model, make every class of API or provider failure loud and non-destructive, and reclassify the 2,073 lost outage items, before `current.json`'s 30-day window empties.
**Depends on**: Nothing (first phase of v2.2). **Note:** a `/gsd:quick` hotfix of the live erroneous cards runs before this phase starts (out of roadmap scope); the replacement model is chosen by metrics (A/B eval) with DeepSeek direct as the backup provider.
**Requirements**: NREC-01, NREC-02, NREC-03, NREC-04, NREC-05, NREC-06, NREC-07, NREC-08, NREC-09, NREC-10
**Deadline**: before 2026-10-05 (current.json's 30-day rolling window empties on that date)
**Success Criteria** (what must be TRUE):
  1. The eval runner (`pipeline/experiments/eval_classifier.py --model`) scores the owner-chosen replacement on the golden set at commune accuracy ≥95.45%, parse-fail ≤2%, family accuracy ≥65.91% baseline, and the model has ≥2 live OpenRouter endpoints at switch time; results are committed.
  2. `classifier.py` and `clustering.py` read the model id from config/env with zero literal `granite-4.1-8b` left in `pipeline/`; a startup preflight against the provider's `/endpoints` fails the run loudly on 0 endpoints (unit test uses the measured granite-4.1 0-endpoint fixture); a DeepSeek direct backup automatically takes over on preflight failure or circuit-breaker trip, with failover logged and counted.
  3. `classify()` returns a typed outcome (OK/NOT_CRIME/PARSE_ERROR/API_ERROR); API errors never mark a URL seen and never record `classifier_none` — they persist to a retry queue instead; genuine model rejections still mark seen (CR-02 kept); 429/5xx retry with backoff, 401/404 do not retry, and a circuit breaker stops primary calls after N consecutive errors.
  4. With 100% injected API errors, the news workflow still commits data and then fails at a post-commit health gate, opening the `pipeline-failure-news` issue automatically; the heartbeat and `freshness.mjs` assert newest-incident age (or `last_new_incident_at`) ≤48h instead of `generated` (a fixture with `generated=now`/`max(date)=now-3d` fails both).
  5. The backfill reclassifies exactly the 2,073 outage items (stage `classifier_none`, `first_seen` ≥2026-09-04T20:13:49Z) without refetching; accepted items merge with dedup, rejected rows carry their real stage, `seen.json` is untouched, R2 `rejected.jsonl`/corpus-state are regenerated, and the accepted/rejected split is reported as measured numbers.
  6. 3 consecutive scheduled runs show classified > 0 and 0 HTTP 404 lines; before 2026-10-05, prod `/news/` and `/es/noticias/` show incidents dated 2026-09-05..2026-09-22 with the newest card ≤1 day old at check time.
**Plans**: TBD

### Phase 35: Honest Freshness Signals

**Goal**: Make every date and recency signal a visitor or Google sees derive from the data, not from build or write time, and disclose the CEAD vintage.
**Depends on**: Phase 34
**Requirements**: FRESH-01, FRESH-02, FRESH-03, FRESH-04, FRESH-05
**Success Criteria** (what must be TRUE):
  1. `/news/` and `/es/noticias/` show "Latest incident: <max date>" / "Último incidente: <fecha>" derived from the data, with a bilingual stale notice rendering when the newest incident is >48h old (validator-enforced against a Sep-4-frozen fixture).
  2. The news day histogram draws no bars for days outside `current.json`'s coverage window.
  3. A commune's "Recent incidents in the news" section switches to a caveated heading (both locales) when its newest item is >7 days old.
  4. A no-op pipeline run (0 new incidents) leaves `current.json` byte-identical and fires no deploy; over 7 days, deploys stay ≤ the number of runs that changed the incident set.
  5. The methodology and commune pages show "CEAD data as of <last_updated>" and label the partial-year cutoff, in both locales, with a validator asserting it.
**Plans**: TBD

### Phase 36: Classification Fidelity & Attribution

**Goal**: Make each published incident faithful to its source — verbatim headline, correct family or a non-crime rejection, the publisher link, and no duplicate cards — using deterministic methods only, no LLM event merging.
**Depends on**: Phase 34
**Requirements**: FID-01, FID-02, FID-03, FID-04, FID-05, FID-06, FID-07
**Success Criteria** (what must be TRUE):
  1. Every new incident stores `title_src` (verbatim outlet headline); ES cards show `title_src`, EN cards show a labeled machine translation of it; the LLM no longer rewrites headlines.
  2. The golden set gains ≥20 keyword-passing non-crime items plus relabelled vida/vif/robos boundary items; non-crime rejection is ≥80% with a recorded family confusion matrix; a 50-item hand audit of a fresh 2-week sample meets the owner-set family-agreement threshold and `vida` is no longer a catch-all.
  3. Incident `url` is the publisher URL (with `via_url` retaining the Google News link); seen/dedup key on both; the share of news.google.com links among new incidents drops from the 53% baseline with the decode success rate recorded.
  4. The deterministic 0.82 (cut, date) cross-run dedup rule runs against existing incidents; applying it over `current.json` yields 0 drops (baseline 73/807), validator-enforced; no LLM clustering is introduced.
  5. Descriptions are HTML-unescaped before classification and the BioBio `application/octet-stream` warning is handled or suppressed.
  6. A prod regression check confirms the hotfixed cards (kinship cluster, prison-suicide item) stay correct after the pipeline and backfill changes.
**Plans**: TBD

### Phase 37: Dependency & Security Hygiene

**Goal**: Clear the security-alert and Dependabot backlog without destabilizing the restored pipeline, and set a standing triage policy.
**Depends on**: Phase 34 (DEPS-03 additionally requires the NREC-01 eval result)
**Requirements**: DEPS-01, DEPS-02, DEPS-03, DEPS-04
**Success Criteria** (what must be TRUE):
  1. astro ≥7.2.8 is on master (PR #39 merged, advisory GHSA-26w7-cxv4-gfx2 closed) and `npm audit --omit=dev` reports 0 critical.
  2. ≤3 open Dependabot PRs remain, none older than 14 days; each is merged with CI green or closed with a written reason.
  3. openai 3.x (PR #37) is merged only after the NREC-01 eval reproduces identical metrics, or is closed with a reason.
  4. The Dependabot triage policy and the CodeQL decision are recorded in `DEPLOYMENT.md`.
**Plans**: TBD

### Phase 38: Pipeline, Public-Data, SEO & Docs Hygiene

**Goal**: Close the remaining lower-severity issues — public data surface, SEO cannibalization, seen-ledger pruning, CEAD workflow gaps, and stale docs and memory.
**Depends on**: Phase 34, Phase 35
**Requirements**: HYG-01, HYG-02, HYG-03, HYG-04, HYG-05, HYG-06, HYG-07
**Success Criteria** (what must be TRUE):
  1. `seen.json` and `rejected/*.json` are either intentionally kept public or return 404 on prod per the owner's decision, with pages and validators unaffected.
  2. `/map/` vs `/chile-crime-map/` cannibalization is resolved per the owner's choice (canonical, noindex or differentiated titles), validator-enforced.
  3. The seen-ledger is pruned by `first_seen` rather than publication date, and old-dated feed items stop being re-candidates on every run.
  4. `cead-scraper.yml` has no `continue-on-error` on data-producing steps.
  5. `CLAUDE.md`, `STATE.md`, `DEPLOYMENT.md` and `data/SOURCES.md` match the repo (classifier model, openai/astro versions, resolved blockers), with stale memory carry-overs cleared.
  6. The Oct-1 local CEAD scrape is executed on/after 2026-10-01 (operator step, local machine) and its outcome recorded — either new data committed with `deploy-manual` dispatched, or byte-identical output documented and the quarterly-cadence assumption re-evaluated.
  7. The GSC sitemap submission (carried over from 22-03) is done or formally retired.
**Plans**: TBD

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 18. Composite Crime Index | 8/8 | Complete    | 2026-06-19 |
| 21. Commune Comparator + A-vs-B SEO | 4/4 | Complete   | 2026-06-20 |
| 23. ENUSC Communal Victimization Layer | 4/4 | Complete   | 2026-06-19 |
| 22. Go-Live / Launch Ops | 2/3 | Complete (22-03 reclassified as an operator task, F-133) | 2026-06-19 |
| 24. Rankings UX (sortable tables + polish) | 3/3 | Complete | 2026-06-20 |
| 25. UI/UX 360 remediation (prod diagnostic 260702) | 9/9 | Complete    | 2026-07-03 |
| 26. Event Clustering Spike | 4/4 | Complete   | 2026-07-29 |
| 27. News Facet Data Model | 2/2 | Complete   | 2026-07-30 |
| 28. News Visualizer UI | 3/3 | Complete   | 2026-07-30 |
| 29. Map UX Design Loop | 2/2 | Complete   | 2026-07-30 |
| 30. Map Control-Shell Rework | 6/6 | Complete   | 2026-07-31 |
| 31. Docs & Methodology Refresh | 4/4 | Complete   | 2026-08-03 |
| 32. Cron Consistency | 3/3 | Complete   | 2026-08-05 |
| 33. Security Posture | 3/3 | Complete   | 2026-08-05 |
| 34. News Classification Restore, Fail-Loud Alarm & Outage Backfill | 0/TBD | Not started (deadline before 2026-10-05) | - |
| 35. Honest Freshness Signals | 0/TBD | Not started | - |
| 36. Classification Fidelity & Attribution | 0/TBD | Not started | - |
| 37. Dependency & Security Hygiene | 0/TBD | Not started | - |
| 38. Pipeline, Public-Data, SEO & Docs Hygiene | 0/TBD | Not started | - |
