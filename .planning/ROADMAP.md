# Roadmap — Chile Safety Map (ischilesafe.com)

_Last updated: 2026-06-13 after v1.1 milestone roadmap_

## Milestones

- ✅ **v1.0 MVP** — Phases 1–6 (shipped 2026-06-13) — full detail: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
- 🔄 **v1.1 Polish & QA** — Phases 7–9 (in progress)

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

### v1.1 Polish & QA

- [x] **Phase 7: E2E Review Pass** — Walk every page in the inventory (ES/EN) with BrowserOS MCP, sample programmatic pages, exercise map interactions, check mobile, produce REVIEW-E2E-FINDINGS.md (completed 2026-06-14)
- [ ] **Phase 8: Bug Fixes & Data Correctness** — Resolve all Critical findings + fix console errors, broken links, data calculation bugs, and AdSlot CLS issues
- [ ] **Phase 9: UX / Readability / Accessibility Polish** — Apply UX, readability, editorial-tone, and a11y corrections surfaced by the review

## Phase Details

### Phase 7: E2E Review Pass

**Goal**: Every page category in the site has been seen in a real browser (ES and EN), representative programmatic pages sampled, map interactions exercised, mobile viewport checked, and all findings are recorded in a single prioritised document.
**Depends on**: Nothing (first v1.1 phase); dev server running (`cd site && npm run dev`); BrowserOS MCP connected (port 9200).
**Requirements**: REVIEW-01, REVIEW-02, REVIEW-03, REVIEW-04, REVIEW-05
**Success Criteria** (what must be TRUE):

  1. All 12 EN editorial pages, 12 ES editorial pages, /map/ + /es/mapa/, and the legal pages (4 URLs: terms + privacy, each locale — verified count) have been navigated, screenshotted, and console-checked. (07-RESEARCH.md verified 12+12 editorial and 4 legal URLs, not the 10+10/8 anticipated in REQUIREMENTS.md; the missing-legal-pages gap is logged as a Polish finding, not a blocker.)
  2. A declared sample of programmatic pages (≥3 communes at high/mid/low population, ≥2 regions, ≥2 crime types, both locales) has been reviewed against the page template.
  3. Map dynamic interactions verified in browser: year filter, crime-type filter, commune panel (rate/trend/ranking/sparkline/families), search, geolocation, and incident layer in empty state — all without unhandled errors.
  4. Mobile viewport (~375px) checked on money pages and map: no horizontal overflow, map usable, touch targets visually adequate.
  5. `.planning/REVIEW-E2E-FINDINGS.md` exists with every finding tagged Critical / Warning / Polish, the affected page identified, a screenshot reference, and a concrete recommendation.

**Plans**: 5 plans
Plans:
**Wave 1**

- [x] 07-01-PLAN.md — Pre-flight (dev server port + BrowserOS tools) + editorial/map/legal inventory walk [REVIEW-01]

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 07-02-PLAN.md — Programmatic page sampling vs template (communes/regions/crime, both locales) [REVIEW-02]

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 07-03-PLAN.md — Map dynamic interactions on /map/ (filters/panel/search/geo/incident empty state) [REVIEW-03]

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 07-04-PLAN.md — Mobile viewport (375×812) money pages + map, overflow + usability check [REVIEW-04]

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 07-05-PLAN.md — Consolidate REVIEW-E2E-FINDINGS.md (severity/page/screenshot/recommendation) [REVIEW-05]

### Phase 8: Bug Fixes & Data Correctness

**Goal**: All Critical findings from the review are corrected and re-verified; console is clean on money pages; data calculations are accurate; AdSlot does not cause layout shift.
**Depends on**: Phase 7 (REVIEW-E2E-FINDINGS.md must exist)
**Requirements**: BUGFIX-01, BUGFIX-02, BUGFIX-03, BUGFIX-04, BUGFIX-05
**Success Criteria** (what must be TRUE):

  1. Zero browser console errors on all money pages (10 EN editorial + /map/) after fixes; any remaining warnings are triaged with written justification.
  2. All internal links (header, footer, cross-links, language switcher) resolve without 404; hreflang reciprocal pairs are correct (canonical self-references intentional and documented).
  3. Rates on commune/region/country pages use `loadNationalAverage` (not a summation); ranking is by rate per 100k; spot-checked figures match `data/cead/` source JSON.
  4. AdSlot containers reserve explicit height so no CLS occurs; with `ADSENSE_ENABLED=false`, no `adsbygoogle` element is visible in the DOM.
  5. Every finding marked Critical in REVIEW-E2E-FINDINGS.md is either resolved (with re-verification note) or explicitly escalated with justification; Warning findings are resolved or carry a written deferral reason.

**Plans**: 5 plans
Plans:
**Wave 1** *(disjoint files — run in parallel)*

- [x] 08-01-PLAN.md — F-005 rollout-row gating across the 4 ranking templates (region EN/ES, crime EN/ES) [BUGFIX-02]
- [x] 08-02-PLAN.md — i18n + a11y string fixes: F-001 ES H1 "Comuna" + F-007 ResultPanel close aria-label locale-aware [BUGFIX-05]
- [x] 08-03-PLAN.md — F-009 zero-JS mobile hamburger nav in PageHeader (+ nav_menu_open i18n string) [BUGFIX-05]
- [x] 08-04-PLAN.md — BUGFIX-04 AdSlot blank reserved-height placeholder (remove dashed border, keep gate + zero adsbygoogle) [BUGFIX-04]

**Wave 2** *(blocked on Wave 1 — verifies its output)*

- [ ] 08-05-PLAN.md — Verification + closeout: console re-check, rate spot-check vs data/cead/, BUGFIX-05 finding ledger [BUGFIX-01, BUGFIX-03, BUGFIX-05]

### Phase 9: UX / Readability / Accessibility Polish

**Goal**: Money pages are easy to scan and pleasant to read in both languages; editorial tone is sober throughout; key a11y and SEO meta signals are present in sampled pages.
**Depends on**: Phase 7 (findings available); can run in parallel with Phase 8 for non-overlapping files.
**Requirements**: UX-01, UX-02, READ-01, READ-02, READ-03, A11Y-01, A11Y-02
**Success Criteria** (what must be TRUE):

  1. Every money page has exactly one H1; H2/H3 hierarchy is scannable; a new reader can understand the page purpose within ~5 seconds (verified by re-reading in browser after changes).
  2. DataCallout/StatCard components each communicate one clear idea with its source (CEAD + year cited); callout-to-prose redundancy identified in the review has been removed or consolidated.
  3. Editorial prose columns respect ~720px max width with paragraph rhythm; no wall-of-text sections remain on editorial pages.
  4. Each EN editorial page has a Spanish counterpart with equivalent content, structure, and tone; no sections are missing in either locale; absolute "peligroso/seguro" phrasing is absent site-wide.
  5. In sampled pages: colour contrast meets WCAG AA for the teal `#0f766e` palette, focus states are visible, images/icons have alt text, map controls have aria labels, `<title>` / meta-description / canonical / hreflang / JSON-LD (FAQPage where applicable) are present and valid.

**Plans**: TBD
**UI hint**: yes

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Data Foundation | v1.0 | 4/4 | Complete | 2026-06-13 |
| 2. Astro Site + Programmatic Pages | v1.0 | 6/6 | Complete | 2026-06-13 |
| 3. Leaflet Map Island | v1.0 | 4/4 | Complete | 2026-06-13 |
| 4. Editorial Pages + AdSense | v1.0 | 7/7 | Complete | 2026-06-13 |
| 5. RSS News Pipeline | v1.0 | 4/4 | Complete | 2026-06-13 |
| 6. CI/CD + Cloudflare Deployment | v1.0 | 3/3 | Complete | 2026-06-13 |
| 7. E2E Review Pass | v1.1 | 5/5 | Complete    | 2026-06-14 |
| 8. Bug Fixes & Data Correctness | v1.1 | 4/5 | In Progress|  |
| 9. UX / Readability / A11Y Polish | v1.1 | 0/TBD | Not started | - |

## Open Human Go-Live Gates (launch checklist — not v1.1 scope)

- **INFRA-03** — live `ischilesafe.com` cutover via `DEPLOYMENT.md` (CF account + DNS + secrets). Unblocks everything below.
- **NEWS live audit** — run `pipeline/scrape_news.py` with real `DEEPSEEK_API_KEY` + 50-incident commune-hallucination audit.
- **EDIT/MON** — GSC submission of editorial pages; flip `ADSENSE_ENABLED` + wire AdSense Consent Mode after first indexing wave.
