# Roadmap — Chile Safety Map (ischilesafe.com)

_Last updated: 2026-08-07 — v2.1 shipped and archived (Phases 26–33). No milestone is currently open._

## Milestones

- ✅ **v1.0 MVP** — Phases 1–6 (shipped 2026-06-13) — full detail: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Polish & QA** — Phases 7–9 (shipped 2026-06-15) — full detail: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Map Fidelity, Findability & News** — Phases 10–17 (shipped 2026-06-18) — full detail: [milestones/v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)
- ✅ **v1.3 Data Quality Hardening & Methodology** — Phases 19–20 (shipped 2026-06-19) — _(Phase 18 deliberately reserved for Composite Crime Index)_
- ✅ **v2.0 Composite Index, Comparators & Launch** — Phases 18, 21, 22, 23, 24, 25 (shipped 2026-07; production live) — full detail: [milestones/v2.0-ROADMAP.md](milestones/v2.0-ROADMAP.md)
- ✅ **v2.1 News Intelligence, Map UX & Ops Hardening** — Phases 26–33 (shipped 2026-08-05; run unattended per `v2.1-AUTONOMOUS-DIRECTIVE.md`) — full detail: [milestones/v2.1-ROADMAP.md](milestones/v2.1-ROADMAP.md)

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

## Phase Details

_Empty — every shipped phase's detail now lives in its milestone archive under `milestones/`.
The next milestone repopulates this section._

## Progress Table

_All phases below are archived. See the per-milestone files in `milestones/` for detail._

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
