# Roadmap — Chile Safety Map (ischilesafe.com)

_Last updated: 2026-06-13 after v1.0 milestone_

## Milestones

- ✅ **v1.0 MVP** — Phases 1–6 (shipped 2026-06-13) — full detail: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)

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
Audit: **[milestones/v1.0-MILESTONE-AUDIT.md](milestones/v1.0-MILESTONE-AUDIT.md)** (code-complete; live go-live = human gates in `DEPLOYMENT.md` + each phase's `*-HUMAN-UAT.md`)

</details>

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Data Foundation | v1.0 | 4/4 | Complete | 2026-06-13 |
| 2. Astro Site + Programmatic Pages | v1.0 | 6/6 | Complete | 2026-06-13 |
| 3. Leaflet Map Island | v1.0 | 4/4 | Complete | 2026-06-13 |
| 4. Editorial Pages + AdSense | v1.0 | 7/7 | Complete | 2026-06-13 |
| 5. RSS News Pipeline | v1.0 | 4/4 | Complete | 2026-06-13 |
| 6. CI/CD + Cloudflare Deployment | v1.0 | 3/3 | Complete | 2026-06-13 |

## Open Human Go-Live Gates (launch checklist — not v1.1 scope)

- **INFRA-03** — live `ischilesafe.com` cutover via `DEPLOYMENT.md` (CF account + DNS + secrets). Unblocks everything below.
- **NEWS live audit** — run `pipeline/scrape_news.py` with real `DEEPSEEK_API_KEY` + 50-incident commune-hallucination audit.
- **EDIT/MON** — GSC submission of editorial pages; flip `ADSENSE_ENABLED` + wire AdSense Consent Mode after first indexing wave.
