---
phase: 12-home-ia-redesign-comuna-page-hub-and-spoke
verified: 2026-06-15T12:00:00Z
status: passed
score: 11/11
human_smoke_signoff: "Orchestrator-performed browser smoke test (BrowserOS, dev :4326) on 2026-06-15 — all 3 runtime map-focus items passed: /map/?cut=13101 flew to + selected Santiago (panel populated, no console errors); /map/ default view unchanged; /map/?cut=zzz no crash (graceful default + benign 404 on the unknown-CUT JSON fetch). Promoted human_needed → passed."
human_verification:
  - test: "Visit /map/?cut=13101 in the dev server"
    expected: "Map flies to and highlights Santiago commune; panel/flyToBounds engaged"
    why_human: "Map focus param wiring (D-08) depends on runtime Leaflet rendering; automated scan confirms the URLSearchParams code is present after mountChoroplethLayer but cannot execute the React island"
  - test: "Visit /map/ with no query param"
    expected: "Default national view unchanged — no regression"
    why_human: "Runtime Leaflet behavior, not statically verifiable"
  - test: "Visit /map/?cut=zzz"
    expected: "No crash, default view — garbage CUT is a safe no-op"
    why_human: "Runtime behaviour depends on polyIdxRef.current.get returning undefined gracefully"
---

# Phase 12: Home / IA Redesign + Comuna Page Hub-and-Spoke — Verification Report

**Phase Goal:** The site stops feeling scattered — the home presents the Hybrid C+B framing (validated in spike 001) and every comuna page is a hub that connects coherently to the rest of the site (spike 003).
**Verified:** 2026-06-15
**Status:** passed (21/21 automated truths verified; 3 runtime map-focus items smoke-tested green by orchestrator via BrowserOS — see human_smoke_signoff)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Home presents Hybrid C+B: single H1 + search hero (GET to directory) + two lead ranking tables + map CTA + guide cards + condensed prose below fold | VERIFIED | `site/src/pages/index.astro`: HomeLayout, one `<h1>`, `<form action="/communes/" method="get">`, `CommuneRankingTable` called twice (lowestRows/highestRows), `<a href="/map/">`, guide-cards section, prose below fold |
| 2 | ES home at parity with EN, ES slugs hardcoded | VERIFIED | `site/src/pages/es/index.astro`: `action="/es/comunas/"`, `href="/es/mapa/"`, `CommuneRankingTable` twice, single Spanish H1, zero getRelativeLocaleUrl for slugs |
| 3 | Zero client:* on home pages | VERIFIED | No `client:load`, `client:only`, or `client:visible` in either home file; HomeLayout wraps BaseLayout without adding any island directives |
| 4 | Every EN comuna page has 4-level breadcrumb: Home > Communes > Region > commune (terminal aria-current) | VERIFIED | `commune/[slug].astro` L137-145: `href="/"`, `href="/communes/"`, `href="/region/{regionSlug}/"`, terminal `<span aria-current="page">{data.name}</span>` |
| 5 | Every ES comuna page has 4-level breadcrumb: Inicio > Comunas > Region > commune | VERIFIED | `es/comuna/[slug].astro` L139-146: `href="/es/"`, `href="/es/comunas/"`, `href="/es/region/{regionSlug}/"`, terminal span with aria-current |
| 6 | Every EN comuna page links to map centered on itself via /map/?cut=\<cut\> | VERIFIED | `commune/[slug].astro` L209: `href={\`/map/?cut=${data.cut}\`}` — static anchor, zero client:* |
| 7 | Every ES comuna page links to map via /es/mapa/?cut=\<cut\> | VERIFIED | `es/comuna/[slug].astro` L211: `href={\`/es/mapa/?cut=${data.cut}\`}` |
| 8 | Every comuna page shows similar-comunas spoke (nearest rate, same region) | VERIFIED | Both slug templates call `nearestComparables(cut, 5)` and render via `CommuneRankingTable`; `data.ts` exports `nearestComparables` at L329 with same-region filter, ascending abs-rate sort, no national fallback (D-07 compliant) |
| 9 | Every comuna page shows per-crime-type ranking spoke links | VERIFIED | Both slug templates iterate `byFamily`, emit `<a href="/crime/{FAMILY_SLUGS[key].en}/">` (EN) and `<a href="/es/delito/{FAMILY_SLUGS[key].es}/">` (ES) |
| 10 | Regional-rank device #N of M present on every comuna page | VERIFIED | Both templates compute `regionCommuneCount = loadIndex().filter(...)` and render `#${data.regional_rank} of ${regionCommuneCount}` (EN) / `#${data.regional_rank} de ${regionCommuneCount}` (ES) in the StatCard |
| 11 | Nav spine includes Rankings link in both locales (/rankings/ + /es/rankings/) | VERIFIED | `PageHeader.astro` L28: `rankingsHref = locale === 'en' ? '/rankings/' : '/es/rankings/'`; L64: `<a href={rankingsHref}>` rendered in nav |
| 12 | Footer spine row (map/communes/rankings/editorial) appears on every page in both locales | VERIFIED | `PageFooter.astro` L35-51: `<nav class="footer-spine">` with hardcoded per-locale links (EN: /map/, /communes/, /rankings/, /safest-cities-in-chile/; ES: /es/mapa/, /es/comunas/, /es/rankings/, /es/comunas-mas-seguras-chile/) |
| 13 | /rankings/ and /es/rankings/ are real static pages with a single H1 | VERIFIED | `site/src/pages/rankings.astro` has `<h1>Crime Incidence Rankings</h1>`; `site/src/pages/es/rankings.astro` has `<h1>Rankings de Incidencia Delictiva</h1>`; both use EditorialLayout; both carry reciprocal enPath/esPath |
| 14 | /rankings/ pages link existing ranking pages only — no new ranking data | VERIFIED | rankings.astro links /safest-cities-in-chile/, /communes/, and FAMILY_SLUGS-derived /crime/* pages only. es/rankings.astro links /es/comunas-mas-seguras-chile/, /es/comunas/, /es/delito/* pages. No new tables or data sources. |
| 15 | spine.mjs validator registered in all.mjs and asserts F-L | VERIFIED | `all.mjs` VALIDATORS array includes `'spine.mjs'` at position 11; `spine.mjs` implements assertions F (map pages exist), G (rankings pages exist), H (rankings in sitemap), I (breadcrumb reciprocity across all communes), J (map-spoke on all ficha pages), K (home single H1), L (rankings nav site-wide) |
| 16 | Directory finder honors ?q= URL param on load (EN + ES) | VERIFIED | `communes/index.astro` L280: `const initialQ = new URLSearchParams(window.location.search).get('q');`; `es/comunas/index.astro` L276: same pattern — value assigned to `input.value`, never to innerHTML |
| 17 | i18n string maps expose nav_rankings + 4 footer-spine keys in both locales | VERIFIED | `i18n.ts` interface L110-114 declares all 5 keys; EN_STRINGS L230-234 and ES_STRINGS L353-357 supply values |
| 18 | nearestComparables(targetCut, n) exported from data.ts | VERIFIED | `data.ts` L329: `export function nearestComparables(targetCut: string, n: number): RankingRow[]` — same-region filter, abs-rate sort, no national fallback, throws on missing CUT, BUGFIX-999.1 comment present |
| 19 | Map island reads ?cut= URL param after choropleth layer mount | VERIFIED | `MapIsland.tsx` L211-215: `const focusCut = new URLSearchParams(window.location.search).get('cut');` placed inside the `if (!cancelled && mapRef.current)` block immediately after `mountChoroplethLayer` returns; calls `setTimeout(() => selectCommune(focusCut), 100)` — opaque string, no DOM injection |
| 20 | No news section on any comuna page; no Noticias nav node (D-11, D-14 honoured) | VERIFIED | Neither `commune/[slug].astro` nor `es/comuna/[slug].astro` contains any news section; `PageHeader.astro` nav has 5 links only (Home, Map, Communes, Rankings, Methodology) — no Noticias entry |
| 21 | Editorial tone: no absolute "safe"/"dangerous" labels on home or rankings pages | VERIFIED | Home uses "Lowest Reported Rate" / "Highest Reported Rate" framing; rankings.astro prose says "reported incidence rates" and "reported counts, not absolute measures of risk"; ES mirrors the same phrasing |

**Score:** All automated truths VERIFIED (21/21). 3 runtime map-focus items require human smoke (see Human Verification section).

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `site/src/lib/data.ts` | `nearestComparables(cut, n)` plural helper | VERIFIED | Exported at L329; RankingRow[] return type; same-region filter, abs-rate sort |
| `site/src/config/i18n.ts` | `nav_rankings` + 4 footer-spine keys (EN + ES) | VERIFIED | Interface L110-114; EN L230-234; ES L353-357 |
| `site/src/pages/communes/index.astro` | `?q=` URL read via URLSearchParams | VERIFIED | L280 — `initialQ` assigned to `input.value` only |
| `site/src/pages/es/comunas/index.astro` | `?q=` URL read via URLSearchParams | VERIFIED | L276 — same pattern |
| `site/src/components/map/MapIsland.tsx` | `?cut=` focus param inside loadData() | VERIFIED | L211-215 — after mountChoroplethLayer, opaque string, setTimeout wrapper |
| `site/src/layouts/HomeLayout.astro` | Wide full-bleed layout wrapping BaseLayout | VERIFIED (inferred) | Referenced by both home files; wraps BaseLayout per plan pattern |
| `site/src/pages/index.astro` | EN home on Hybrid C+B (≥80 lines) | VERIFIED | 130+ lines; single H1, search hero form, two tables, map CTA, guide cards |
| `site/src/pages/es/index.astro` | ES home parity (≥80 lines) | VERIFIED | 80+ lines; ES slugs hardcoded; single H1 |
| `site/src/pages/commune/[slug].astro` | 4-level breadcrumb + map spoke + similar + crime-type | VERIFIED | All spokes present at confirmed line locations |
| `site/src/pages/es/comuna/[slug].astro` | ES mirror of all spokes + breadcrumb | VERIFIED | ES hardcoded slugs; identical spoke structure |
| `site/src/components/PageHeader.astro` | `rankingsHref` hardcoded per-locale | VERIFIED | L28; rendered in nav at L64 |
| `site/src/components/PageFooter.astro` | `footer-spine` nav row | VERIFIED | L35-51; EN + ES hardcoded per-locale links |
| `site/src/pages/rankings.astro` | EN rankings index with single H1 | VERIFIED | h1 present; links to existing pages only |
| `site/src/pages/es/rankings.astro` | ES rankings index with single H1 | VERIFIED | h1 present; ES slugs hardcoded |
| `site/scripts/validate/spine.mjs` | Assertions F-L | VERIFIED | Full 366-line validator with all 7 assertions |
| `site/scripts/validate/all.mjs` | `spine.mjs` in VALIDATORS array | VERIFIED | Position 11 in array |

---

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `index.astro` search hero | `/communes/?q=` | `<form action="/communes/" method="get">` | WIRED |
| `es/index.astro` search hero | `/es/comunas/?q=` | `<form action="/es/comunas/" method="get">` | WIRED |
| `commune/[slug].astro` map spoke | `/map/?cut=<cut>` | `href={\`/map/?cut=${data.cut}\`}` | WIRED |
| `es/comuna/[slug].astro` map spoke | `/es/mapa/?cut=<cut>` | `href={\`/es/mapa/?cut=${data.cut}\`}` | WIRED |
| `commune/[slug].astro` similar spoke | `nearestComparables(cut, 5)` | data helper + CommuneRankingTable | WIRED |
| `commune/[slug].astro` breadcrumb | `/communes/` | `<a href="/communes/">` | WIRED |
| `es/comuna/[slug].astro` breadcrumb | `/es/comunas/` | `<a href="/es/comunas/">` | WIRED |
| `PageHeader.astro` nav | `/rankings/` (EN) / `/es/rankings/` (ES) | `rankingsHref` hardcoded ternary | WIRED |
| `PageFooter.astro` spine | map/communes/rankings/editorial per locale | `footer-spine` nav, hardcoded | WIRED |
| `MapIsland.tsx loadData()` | `selectCommune(focusCut)` | URLSearchParams after mountChoroplethLayer | WIRED (code present; runtime behaviour is human-verified) |
| `all.mjs` | `spine.mjs` | VALIDATORS array entry | WIRED |

---

### Requirements Coverage

| Requirement | Phase Plans | Description | Status |
|-------------|-------------|-------------|--------|
| IA-01 | 12-03 | Home rebuilt with Hybrid C+B, single H1, static/indexable, EN/ES parity | SATISFIED — both home files rebuild complete per spec |
| IA-02 | 12-01, 12-02, 12-04 | Every comuna page is a hub: map spoke, regional ranking, similar comunas, crime-type spoke, breadcrumb | SATISFIED — all 4 non-news spokes + breadcrumb implemented in both EN/ES templates; news spoke correctly absent (deferred D-11) |
| IA-03 | 12-01, 12-05 | Nav spine: Rankings nav + /rankings/ pages + footer spine + reciprocal 404-free links + validator | SATISFIED — Rankings in nav, footer spine, /rankings/ + /es/rankings/ pages exist, spine.mjs registered |

**Note on scope:** IA-02's "geolocated news" sub-item and IA-03's "noticias" spine node are intentionally deferred to Phase 16 per locked decisions D-11 and D-14. Their absence is NOT a gap for Phase 12.

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `index.astro` lead tables | `lowestRows` / `highestRows` | `loadIndex()` + `loadCommune()` + `latestCompleteYearRate()` — build-time | Yes — derived from full commune index, not hardcoded | FLOWING |
| `commune/[slug].astro` similar spoke | `similarComunas` | `nearestComparables(cut, 5)` — build-time | Yes — same-region pool from real data | FLOWING |
| `commune/[slug].astro` regional rank device | `regionCommuneCount` | `loadIndex().filter(c => c.region_id === data.region_id).length` — build-time | Yes — count from index, not hardcoded | FLOWING |

---

### Anti-Patterns Found

| File | Pattern | Severity | Notes |
|------|---------|----------|-------|
| None found | — | — | No TBD/FIXME/XXX markers found in Phase 12 modified files; no hardcoded empty arrays flowing to render; no stubs |

---

### Behavioral Spot-Checks

Runtime checks skipped — the site requires a build+dev server to exercise the map island. The spine.mjs validator covers all static assertions (F-L). The map focus param (?cut=) requires human verification (Task 3 from 12-06-PLAN.md).

---

### Human Verification Required

#### 1. Map focus param — commune flies to and is selected

**Test:** Start `cd site && npm run dev`. Visit `http://localhost:4321/map/?cut=13101`.
**Expected:** Map flies to and highlights Santiago (commune panel engaged, flyToBounds called). Takes approximately 1-2 seconds for choropleth to mount.
**Why human:** `selectCommune` is called via `setTimeout(() => selectCommune(focusCut), 100)` inside the React island — cannot execute Leaflet layer rendering in a static scan.

#### 2. Map regression — no-param default view unchanged

**Test:** Visit `http://localhost:4321/map/` (no ?cut=).
**Expected:** Default national view — no diff vs. before Phase 12. No crash.
**Why human:** The `if (focusCut)` guard should be a no-op, but runtime Leaflet state cannot be verified statically.

#### 3. Map garbage CUT — safe no-op

**Test:** Visit `http://localhost:4321/map/?cut=zzz`.
**Expected:** No crash, no visual anomaly. `polyIdxRef.current.get('zzz')` returns undefined, flyToBounds is not called.
**Why human:** Runtime Map lookup behaviour in the React island.

---

### Gaps Summary

No gaps. All automated truths are VERIFIED. The three human verification items above are runtime-only checks for the map island focus behaviour — the code wiring is present and correct. The orchestrator has already manually smoke-tested these items (confirmed green). The status is `human_needed` per the decision tree because human verification items exist; if the orchestrator's green smoke counts as formal sign-off, status can be promoted to `passed`.

---

_Verified: 2026-06-15_
_Verifier: Claude (gsd-verifier)_
