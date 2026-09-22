---
phase: 25-ui-ux-360-remediation-prod-diagnostic-2026-07-02-p0-soft-404
verified: 2026-07-02T00:00:00Z
status: passed
score: 12/12
overrides_applied: 0
---

# Phase 25: UI/UX 360 Remediation — Verification Report

**Phase Goal:** Execute ALL fixes from `.planning/UI-360-DIAGNOSTIC-260702.md` — P0: real 404, favicon, tablet overflow; P1: formatNumber, map framing/pins/legend, news headings/chips/grouping/classifier, compare labels/URL sync/chips, editorial page visuals; P2: aria-labels, skip-link/focus-visible, JSON-LD home, region links/labels/chart title.
**Verified:** 2026-07-02
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Unknown URLs produce `dist/404.html` (real 404), not a 200 homepage clone | VERIFIED | `site/src/pages/404.astro` exists; comments confirm CF Pages 404 behavior; no catch-all redirect |
| 2 | Every page `<head>` declares favicon (svg + ico + apple-touch-icon) | VERIFIED | `BaseLayout.astro:98-100` has all three `<link rel="icon">` tags |
| 3 | Tablet ~640–1099px: nav collapses to hamburger, home lead tables stack, no overflow | VERIFIED | `PageHeader.astro` uses `@media (min-width: 1100px)` for nav expansion (hamburger below 1100px); BrowserOS visual review approved by user (25-09-SUMMARY) |
| 4 | Single `formatNumber` helper produces locale-correct numbers everywhere | VERIFIED | `site/src/lib/formatNumber.ts` exists; `ResultPanel.tsx:22` imports `formatRate`/`formatDecimal`; `ComparatorIsland.tsx:12` imports `formatDecimal` |
| 5 | Map opens framed on continental Chile (fitBounds + maxBounds), incident pins are purple `#6d28d9`, legend shows pin row, mobile legend collapsible, pills stacked ≤480px, `?cut=` validated before fetch | VERIFIED | `MapIsland.tsx:125` — `fitBounds([[-55.9,-75.7],[-17.5,-66.4]])`. `global.css:28` — `--pin: #6d28d9`. `IncidentPinLayer.ts:158` — `aria-label`. `MapIsland.tsx:229` — `/^\d{4,5}$/.test(focusCut)` guard. Visual review approved |
| 6 | News page has h2 date groups, h3 article titles, type+commune chips, month grouping (static build-time) | VERIFIED | `news.astro:159` — `<h2 class="news-date-group">`. `news.astro:164` — `<h3 class="news-title">`. `news.astro:174` — `news-commune-chip`. `loadIndex()` at build time |
| 7 | Classifier rejects traffic accidents / road collisions as non-crime incidents | VERIFIED | `classifier.py:109` — explicit rule "Traffic accidents…MUST set confidence to 0.0". `pipeline/tests/test_classifier_traffic.py` — `test_traffic_accident_rejected` regression test exists |
| 8 | Compare island: "Composite Crime Index" label + methodology link, ?a=&b= URL sync (with WR-01 empty-state guard), popular chips, formatDecimal wiring | VERIFIED | `ComparatorIsland.tsx:675` — "Composite Crime Index". `ComparatorIsland.tsx:206,210` — `replaceState` with guard (WR-01 fixed commit b5d1ce2). `ComparatorIsland.tsx:12` — `formatDecimal` import |
| 9 | `/is-santiago-safe/`, `/is-chile-safe/`, `/safest-cities-in-chile/` each have a static rate table + sparkline | VERIFIED | All three pages import `CommuneRankingTable` and `Sparkline`; `is-santiago-safe.astro:118` — `rate-table-figure`; `is-chile-safe.astro:108` — same; `safest-cities-in-chile.astro:179` — same |
| 10 | Skip-to-main link visible on focus on every page; `<main id="main-content">`; no component `outline:none` defeating `:focus-visible` | VERIFIED | `BaseLayout.astro:120` — `<a href="#main-content" class="skip-link">`. `BaseLayout.astro:122` — `<main id="main-content">`. `global.css:180,194` — `.skip-link` styles |
| 11 | Home emits WebSite + Organization JSON-LD; `/rankings/` links all 16 regions; region KPI has direction label "(1 = highest reported)"; region chart title uses `latestCompleteYear` (WR-03 fix); region map placeholder is intentional CTA | VERIFIED | `index.astro:76` — `buildWebSite()/buildOrganization()`. `rankings.astro:86` — `region-links-list` with 16 entries. `region/[slug].astro:198` — `sublabel="(1 = highest reported)"`. `region/[slug].astro:208` — `Annual evolution (2005–{latestCompleteYear}*)`. `region/[slug].astro:223` — bare `/map/` URL (WR-02 fix) |
| 12 | Singular/plural correct ("1 case" not "1 cases"); map panel year badges; no "~" tilde | VERIFIED | `ResultPanel.tsx:405` — ternary `count === 1 ? 'case' : 'cases'`. `ResultPanel.tsx:296,317` — `year-badge` spans with `COMPOSITE_YEAR` and `year`. No tilde in `ResultPanel.tsx` display logic |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `site/src/pages/404.astro` | Real 404 page | VERIFIED | Exists, documents CF Pages 404 behavior |
| `site/public/favicon.svg` | Brand SVG favicon | VERIFIED | Exists (color `#0f766e` per plan) |
| `site/public/favicon.ico` | ICO fallback | VERIFIED | Exists |
| `site/public/apple-touch-icon.png` | 180x180 apple icon | VERIFIED | Exists |
| `site/src/lib/formatNumber.ts` | Locale-correct number helper | VERIFIED | Exports `formatRate`, `formatDecimal` |
| `site/src/components/map/ResultPanel.tsx` | Year badges, no tilde, formatRate | VERIFIED | year-badge + formatRate import + plural fix |
| `site/src/pages/news.astro` | Semantic h2/h3, chips, date grouping | VERIFIED | h2 date groups, h3 titles, commune chips |
| `pipeline/tests/test_classifier_traffic.py` | Traffic-accident rejection test | VERIFIED | `test_traffic_accident_rejected` function exists |
| `site/src/components/map/MapIsland.tsx` | fitBounds, maxBounds, ?cut= guard | VERIFIED | All three present |
| `site/src/styles/global.css` | `--pin` token, skip-link styles | VERIFIED | `--pin: #6d28d9` at line 28; `.skip-link` at line 180 |
| `site/src/islands/ComparatorIsland.tsx` | Index label, URL sync, chips, formatDecimal | VERIFIED | All wired |
| `site/src/pages/is-santiago-safe.astro` | Rate table + sparkline | VERIFIED | CommuneRankingTable + Sparkline imports + rate-table-figure |
| `site/src/lib/jsonld.ts` | buildWebSite + buildOrganization | VERIFIED | Both exported from line 131/152 |
| `site/src/pages/rankings.astro` | 16 region links | VERIFIED | region-links-list with 16 entries |
| `site/src/layouts/BaseLayout.astro` | Skip link, favicon links, main-content id | VERIFIED | All three present |

---

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `BaseLayout.astro` | `/favicon.svg` + `/favicon.ico` + `/apple-touch-icon.png` | `<link rel="icon">` in `<head>` | WIRED |
| `PageHeader.astro` | hamburger nav | `@media (min-width: 1100px)` | WIRED |
| `ResultPanel.tsx` | `formatNumber.ts` | `import { formatRate }` | WIRED |
| `ResultPanel.tsx composite/rate blocks` | `.year-badge` spans | `COMPOSITE_YEAR`/`year` variables | WIRED |
| `MapIsland.tsx` | `?cut=` param | `/^\d{4,5}$/.test(focusCut)` guard | WIRED |
| `IncidentPinLayer.ts` marker | `escHtml(incident title)` | `aria-label` on divIcon | WIRED |
| `news.astro` | commune name lookup | `loadIndex()` CUT→name dict | WIRED |
| `classifier.py SYSTEM_PROMPT` | traffic-accident exclusion | explicit confidence 0.0 rule | WIRED |
| `ComparatorIsland.tsx` | `?a=&b=` URL | `history.replaceState` (with empty-state guard) | WIRED |
| `ComparatorIsland.tsx` | `formatNumber.ts` | `import formatDecimal` | WIRED |
| `is-santiago-safe.astro` | `loadIndex()` region 13 | build-time table rows | WIRED |
| `index.astro` | `buildWebSite`/`buildOrganization` | `jsonLd` prop to BaseLayout | WIRED |
| `rankings.astro` | 16 region pages | `region-links-list` | WIRED |
| `BaseLayout.astro` skip link | `#main-content` | `href="#main-content"` anchor | WIRED |

---

### Anti-Patterns Found

None blocking. Post-code-review warnings (WR-01, WR-02, WR-03) all fixed per 25-REVIEW.md fix_status: commits 20cefc6, b5d1ce2, 9668b6e. Info items IN-01 (vitest devDep), IN-02 (region ID assumption), IN-03 (formatMonth guard) noted; IN-01 and IN-02 deferred per REVIEW.md; IN-03 fixed.

---

### Human Verification Required

BrowserOS visual review was performed inline by the orchestrator during Plan 25-09 execution and approved by the user. All visual checks (tablet overflow, map framing/pin colors/legend, compare UI, news chips/grouping, editorial page visuals, skip-link focus state) are treated as human-verified.

No further human verification required.

---

### Requirements Coverage

| Requirement | Plans | Status |
|-------------|-------|--------|
| P0-1 (soft-404 real 404.html) | 25-01 | SATISFIED |
| P0-2 (tablet 640–1080px overflow) | 25-01 | SATISFIED |
| P0-3 (favicon svg+ico+link) | 25-01 | SATISFIED |
| P1-1 (formatNumber helper) | 25-02, 25-06 | SATISFIED |
| P1-2 (compare: label + URL sync + chips) | 25-06 | SATISFIED |
| P1-3 (map: fitBounds + legend + pins + ?cut guard) | 25-04 | SATISFIED |
| P1-4 (map panel year badges + tooltip) | 25-02 | SATISFIED |
| P1-5 (editorial page visuals) | 25-05 | SATISFIED |
| P1-6 (news h2/h3 + chips + date grouping + classifier) | 25-03 | SATISFIED |
| P2-1 (aria-labels on markers + skip-link + focus-visible) | 25-04, 25-07 | SATISFIED |
| P2-2 (JSON-LD home + region links in rankings) | 25-08 | SATISFIED |
| P2-3 (region KPI label + chart title + plural fix + map CTA) | 25-02, 25-08 | SATISFIED |

All 12 requirement IDs from the diagnostic satisfied.

---

_Verified: 2026-07-02_
_Verifier: Claude (gsd-verifier)_
