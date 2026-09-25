# Requirements — Milestone v2.2 Data Integrity & News Recovery

**Opened:** 2026-09-22 · **Source of truth:** `.planning/research/v2.2-AUDIT-260922.md` (finding IDs V-xx)
**Hard deadline:** NREC-* live before **2026-10-05**. That is when `current.json` (newest incident 2026-09-04) ages out of its 30-day window and `/news/`, the map pins, the commune news sections and the home news block go empty.

## Owner decisions (2026-09-22)

- Scope: phases 34-38 confirmed.
- Replacement classifier: **decided by metrics** (A/B on the eval harness), with an **alarm system** and a **DeepSeek backup**.
- Live erroneous cards: **immediate hotfix** via `/gsd:quick` BEFORE Phase 34. This means the kinship errors about a named real person repeated across 7 cards, and the prison suicide shown as "Delitos contra la Vida". The hotfix is outside the roadmap; FID-07 re-verifies it.
- Headline policy: **verbatim source headline** from now on.

## v2.2 Requirements

### News classification recovery (NREC)

- [x] **NREC-01**: The replacement classifier model is chosen by an A/B run of ≥3 candidates on the golden set, using a model-parameterized eval runner. Candidates are deepseek-v4-flash, granite-4.2-8b, qwen3.5-9b and deepseek-v4.1-flash. The chosen model must meet commune accuracy ≥95.45%, parse-fail ≤2%, family accuracy ≥ the Phase 16 baseline, and have ≥2 live endpoints at switch time. Results are committed. (V-01, V-08)
- [x] **NREC-02**: The classifier and clustering model ids come from config/env. No literal `granite-4.1-8b` remains in `pipeline/`. (V-01, V-26)
- [x] **NREC-03**: A startup preflight checks the primary model's provider endpoints and treats 0 endpoints as a provider failure. A unit test uses the measured granite-4.1 0-endpoint response as its fixture. (V-01)
- [x] **NREC-04**: A **DeepSeek backup** (direct API with `DEEPSEEK_API_KEY`) automatically takes over when the preflight fails or the circuit breaker trips on the primary. Failover is logged and counted in the run summary, and a live smoke test confirms the DeepSeek account is funded and reachable. (owner decision)
- [x] **NREC-05**: `classify()` returns a typed outcome: OK, NOT_CRIME/LOW_CONF, PARSE_ERROR or API_ERROR. API errors never add the URL to `seen.json` and never record it as `classifier_none`; they go to a persisted retry queue. Genuine model rejections are still marked seen (CR-02 kept). (V-02)
- [x] **NREC-06**: 429 and 5xx responses are retried with exponential backoff; 401 and 404 are not retried. A circuit breaker stops primary calls after N consecutive API errors and hands over to the backup (NREC-04). (V-09)
- [x] **NREC-07**: **Alarm.** When classification health fails, the news workflow commits whatever data it has and then concludes as failure at a post-commit health gate. Classification health fails when classified==0 with candidates>0, the API-error rate goes above threshold, or the backup is exhausted. The `pipeline-failure-news` issue opens automatically. This is verified by a 100%-injected-error harness test or a branch dispatch. (V-03)
- [x] **NREC-08**: The heartbeat and `freshness.mjs` assert newest-incident age (or `last_new_incident_at`) ≤48h instead of `current.json.generated`. A fixture with generated=now and max(date)=now-3d fails both. (V-03)
- [~] **NREC-09**: A backfill re-classifies exactly the 2,073 outage items, meaning those with stage `classifier_none` and first_seen ≥2026-09-04T20:13:49Z, taken from `rejected/2026-09.json` without refetching. Accepted items merge with dedup; rejected rows get their real stage; R2 `rejected.jsonl` and corpus-state are regenerated; the accepted/rejected split is reported as measured numbers. (V-04)
- [~] **NREC-10**: Live recovery: 3 consecutive scheduled runs show classified > 0 and 0 HTTP 404 lines. Before 2026-10-05, prod `/news/` and `/es/noticias/` show incidents dated 2026-09-05..2026-09-22, and the newest card is ≤1 day old at check time.

### Honest freshness signals (FRESH)

- [x] **FRESH-01**: `/news/` and `/es/noticias/` show "Latest incident: <max date>" / "Último incidente: <fecha>" taken from the data, not the build time. A bilingual stale notice renders when the newest incident is >48h old, and a validator asserts it with the Sep-4-frozen fixture. (V-05)
- [x] **FRESH-02**: The news day histogram draws no bars for days outside `current.json`'s coverage window. (V-05)
- [x] **FRESH-03**: When a commune "Recent incidents in the news" section's newest item is >7 days old, it switches to a caveated heading, in both locales. (V-05)
- [ ] **FRESH-04**: A no-op pipeline run (0 new incidents) leaves `current.json` byte-identical and fires no deploy. Over 7 days, deploys ≤ runs that changed the incident set. (V-12)
- [x] **FRESH-05**: The methodology and commune pages show "CEAD data as of <last_updated>" and label the partial-year cutoff, in both locales, with a validator. (V-13)

### Fidelity & attribution (FID)

- [ ] **FID-01**: Every new incident stores `title_src` (the outlet's verbatim headline). ES cards show `title_src`; EN cards show a translation of it, labeled as machine translation. The LLM no longer rewrites headlines. (V-06)
- [ ] **FID-02**: The golden set gains ≥20 keyword-passing non-crime items (accidents, suicides, institutional news) and relabelled vida/vif/robos boundary items. Non-crime rejection is ≥80%, and a family confusion matrix is recorded. (V-07, V-08)
- [ ] **FID-03**: A 50-item hand audit of a fresh 2-week sample meets the owner-set family-agreement threshold, and `vida` is no longer a catch-all. The owner decides whether Granite-era incidents (2026-07-27..09-04) get re-classified. (V-07)
- [ ] **FID-04**: Incident `url` is the publisher URL and `via_url` keeps the Google News link; seen and dedup key on both. The share of news.google.com links among new incidents drops from the 53% baseline, and the decode success rate is recorded. (V-10)
- [ ] **FID-05**: Cross-run dedup: the deterministic 0.82 (cut, date) rule runs against existing incidents, so applying it over `current.json` yields 0 drops (baseline 73/807). A validator enforces it. No LLM clustering. (V-11)
- [ ] **FID-06**: Descriptions are HTML-unescaped before classification, and the BioBio `application/octet-stream` warning is handled or suppressed. (V-19)
- [ ] **FID-07**: A prod regression check confirms the hotfixed cards (kinship cluster, prison-suicide item) stay correct after the pipeline and backfill changes.

### Dependency & security hygiene (DEPS)

- [ ] **DEPS-01**: astro ≥7.2.8 on master (PR #39 merged), advisory GHSA-26w7-cxv4-gfx2 closed, and `npm audit --omit=dev` reports 0 critical. (V-14)
- [ ] **DEPS-02**: ≤3 open Dependabot PRs, none older than 14 days. Each is merged with CI green or closed with a written reason. (V-15)
- [ ] **DEPS-03**: openai 3.x (PR #37) is merged only after the NREC-01 eval reproduces identical metrics, or closed with a reason.
- [ ] **DEPS-04**: The Dependabot triage policy and the CodeQL decision are recorded in `DEPLOYMENT.md`. (V-15, V-28)

### Pipeline, public-data, SEO & docs hygiene (HYG)

- [ ] **HYG-01**: The owner decides whether `seen.json` and `rejected/*.json` stay publicly served. If not, they return 404 on prod and pages and validators are unaffected. (V-17)
- [ ] **HYG-02**: `/map/` vs `/chile-crime-map/` cannibalization is resolved per the owner's choice (canonical, noindex or differentiated titles), and a validator asserts it. (V-16)
- [ ] **HYG-03**: The seen-ledger is pruned by `first_seen` rather than publication date, and old-dated feed items stop being re-candidates on every run. (V-18)
- [ ] **HYG-04**: `cead-scraper.yml` has no `continue-on-error` on data-producing steps. (V-27)
- [ ] **HYG-05**: `CLAUDE.md`, `STATE.md`, `DEPLOYMENT.md` and `data/SOURCES.md` match the repo (classifier model, openai/astro versions, resolved blockers), and stale memory carry-overs are cleared. (V-25)
- [ ] **HYG-06**: The Oct-1 local CEAD scrape is executed and its outcome recorded. Either new data is committed and `deploy-manual` dispatched, or byte-identical output is documented and the quarterly-cadence assumption re-evaluated. (operator + agent)
- [ ] **HYG-07**: The GSC sitemap submission (carried over from 22-03) is done or formally retired. (operator)

## Future Requirements (deferred)

- AdSense + Consent Mode activation (`todos/pending/adsense-consent-mode-phase6.md`), a future monetization cycle.
- ENUSC refresh, which waits for a newer INE vintage.

## Out of Scope

- LLM event clustering / opaque merging: NO-GO locked in v2.1. Only the deterministic FID-05 dedup is allowed.
- Heat maps and severity/risk scores: banned anti-features.
- Adding `sexuales` to CEAD `FAMILY_KEYS`, which stays at 7.
- Changing the national_rank direction (#1 = most reported).
- Running the CEAD scraper from GitHub Actions: the runner IPs get 403, so it stays local only.
- A BioBio mojibake fix: REFUTED (V-20), the data is clean UTF-8.
- A CEAD freshness validator (V-22 REFUTED; the heartbeat covers it) and a data-only deploy path (V-23 REFUTED; `deploy-manual.yml` exists).
- ads.txt, whose 404 is expected until AdSense.
- A git-history purge for repo bloat: the pack is 29.93 MiB and not needed.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| NREC-01 | Phase 34 | Complete |
| NREC-02 | Phase 34 | Complete |
| NREC-03 | Phase 34 | Complete |
| NREC-04 | Phase 34 | Complete |
| NREC-05 | Phase 34 | Complete |
| NREC-06 | Phase 34 | Complete |
| NREC-07 | Phase 34 | Complete |
| NREC-08 | Phase 34 | Complete |
| NREC-09 | Phase 34 | Partial (0 not_attempted / 2,122 withheld / 2 api_error; G-18) |
| NREC-10 | Phase 34 | Partial (15 days uncovered: withheld; G-18) |
| FRESH-01 | Phase 35 | Complete (35-01/35-04; prod verified 35-07 T2) |
| FRESH-02 | Phase 35 | Complete (35-01/35-04; prod verified 35-07 T2) |
| FRESH-03 | Phase 35 | Complete (35-04; prod verified 35-07 T2) |
| FRESH-04 | Phase 35 | Interim PASS (N=4 scheduled runs: D=4, C=4, G=0; live no-op 36198632047); 7-day check due 2026-10-02 (issue #45) |
| FRESH-05 | Phase 35 | Complete (35-03/35-05; prod verified 35-07 T2) |
| FID-01 | Phase 36 | Pending |
| FID-02 | Phase 36 | Pending |
| FID-03 | Phase 36 | Pending |
| FID-04 | Phase 36 | Pending |
| FID-05 | Phase 36 | Pending |
| FID-06 | Phase 36 | Pending |
| FID-07 | Phase 36 | Pending |
| DEPS-01 | Phase 37 | Pending |
| DEPS-02 | Phase 37 | Pending |
| DEPS-03 | Phase 37 | Pending |
| DEPS-04 | Phase 37 | Pending |
| HYG-01 | Phase 38 | Pending |
| HYG-02 | Phase 38 | Pending |
| HYG-03 | Phase 38 | Pending |
| HYG-04 | Phase 38 | Pending |
| HYG-05 | Phase 38 | Pending |
| HYG-06 | Phase 38 | Pending |
| HYG-07 | Phase 38 | Pending |
