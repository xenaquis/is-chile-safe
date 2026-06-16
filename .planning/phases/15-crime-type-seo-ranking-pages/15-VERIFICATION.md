---
phase: 15-crime-type-seo-ranking-pages
verified: 2026-06-16T14:00:00Z
status: human_needed
score: 9/9 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 9/9
  gaps_closed:
    - "CR-01: Duplicate homicide spoke link removed — vida key filtered from byFamily loop in both commune/[slug].astro and es/comuna/[slug].astro (commit 30c7b7d)"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Open /crime-ranking/homicide/ in browser, click locale switcher"
    expected: "Navigates to /es/ranking-delito/homicidios/ (hreflang cross-locale resolves)"
    why_human: "hreflang attribute presence is verified programmatically; actual browser navigation behavior (locale switcher component wiring) cannot be verified without a browser"
  - test: "Read the methodology paragraph on /crime-ranking/homicide/ and /crime-ranking/property/"
    expected: "Methodology cites CEAD, states 'denuncias' (not convictions), names included CEAD sub-types. Propiedad note explicitly says it includes hurtos and robos (full aggregate, not sub-type only)."
    why_human: "Editorial accuracy of methodology copy requires human judgment; automated checks only confirmed CEAD is cited and forbidden terms are absent"
---

# Phase 15: Crime-Type SEO Ranking Pages Verification Report

**Phase Goal:** Programmatic bilingual "las N comunas con más {delito}" ranking pages (homicide first) capture long-tail SEO, correctly linked and indexable — correct internal linking, hreflang, sitemap, single H1, and ItemList JSON-LD.
**Verified:** 2026-06-16T14:00:00Z
**Status:** human_needed
**Re-verification:** Yes — after CR-01 gap closure (commit 30c7b7d)

## Re-verification Summary

| Item | Previous | Now | Change |
|------|----------|-----|--------|
| CR-01: Duplicate homicide spoke | OPEN (human decision required) | CLOSED — fix confirmed in source and built HTML | Gap closed |
| Locale switcher cross-navigation | Human needed | Human needed | No change — still requires browser |
| Editorial accuracy of methodology | Human needed | Human needed | No change — still requires human judgment |

**CR-01 fix verification:**
- `site/src/pages/commune/[slug].astro` line 243: `Object.entries(byFamily).filter(([key]) => key !== 'vida').map(...)` — confirmed
- `site/src/pages/es/comuna/[slug].astro` line 246: identical filter — confirmed
- Built HTML `dist/commune/algarrobo/index.html`: exactly 1 occurrence of `crime-ranking/homicide`, 0 occurrences of `crime/homicide` — confirmed
- Built HTML `dist/es/comuna/algarrobo/index.html`: exactly 1 occurrence of `ranking-delito/homicidios`, 0 occurrences of `es/delito/homicidios` — confirmed

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | seo.mjs samples the new /crime-ranking/ and /es/ranking-delito/ pages so OG + ItemList assertions fire on them | VERIFIED | `enCrimeRankingDir`, `esCrimeRankingDir`, `firstCrimeRankingEn`, `firstCrimeRankingEs` all present in seo.mjs lines 171-181; guarded spread entries in SAMPLES lines 193-194 |
| 2 | Each of the 8 crime types has a bilingual methodology note citing CEAD, denuncias framing, and included delitos | VERIFIED | `RANKING_METHODOLOGY_EN` and `RANKING_METHODOLOGY_ES` in familyDefs.ts lines 66-92; all 8 keys present (homicidios, robos_violentos, drogas, propiedad, vif, armas, incivilidades, vida); each cites "CEAD — Ministry of Interior and Public Security" |
| 3 | A reader can open /crime-ranking/homicide/ and /es/ranking-delito/homicidios/ and see Chilean communes ranked by reported homicide rate | VERIFIED | Built pages exist at `dist/crime-ranking/homicide/index.html` and `dist/es/ranking-delito/homicidios/index.html`; table tbody shows Saavedra #1 at rate 24 (non-zero, non-uniform) |
| 4 | Each of the 8 crime types has an EN page and an ES page generated at build time | VERIFIED | 8 pages in `dist/crime-ranking/*/` and 8 in `dist/es/ranking-delito/*/` confirmed via glob |
| 5 | Every ranking page has a single keyword-focused H1, unique title/canonical, reciprocal hreflang (en/es/x-default), ItemList JSON-LD, and appears in the sitemap | VERIFIED | Homicide page: H1 count=1, hreflang en/es/x-default present, `ItemList` and `BreadcrumbList` in built HTML, canonical=`https://ischilesafe.com/crime-ranking/homicide/`, sitemap-0.xml contains 8 crime-ranking + 8 ranking-delito entries |
| 6 | The homicide page ranks by featured_rates.homicidios (non-zero, non-uniform rates) — NOT by_family | VERIFIED | `dataSource === 'featured_rates'` branch in `[crime].astro` line 88-90 reads `commune.featured_rates?.homicidios?.[commune.latestCompleteYear]`; built table row #1 shows Saavedra with rate 24 |
| 7 | Comuna pages link to the homicide ranking page (reciprocal IA link) — exactly one link per locale, no duplicate | VERIFIED | EN built HTML (algarrobo): 1 occurrence of `crime-ranking/homicide`, 0 of `crime/homicide`. ES built HTML (algarrobo): 1 occurrence of `ranking-delito/homicidios`, 0 of `es/delito/homicidios`. CR-01 closed. |
| 8 | Sober tone preserved: no forbidden-language term; ItemList name passes assertSafeName | VERIFIED | Build succeeded with no assertSafeName throw; full validator suite including forbidden-language.mjs passed (12/12 validators, 790 pages) |
| 9 | CSEO-01 and CSEO-02 satisfied per requirements definition | VERIFIED | CSEO-01: bilingual pages exist for 8 crime types, internal-linked to commune pages via 346 commune links per page, reciprocal hreflang, 16 sitemap entries. CSEO-02: single H1, unique canonical, ItemList JSON-LD, sober framing, static/indexable |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `site/scripts/validate/seo.mjs` | First-subdir sample entries for crime-ranking (EN) + ranking-delito (ES) | VERIFIED | Lines 171-181 and 193-194 add guarded spread entries |
| `site/src/lib/familyDefs.ts` | RANKING_METHODOLOGY_EN + RANKING_METHODOLOGY_ES keyed by family key | VERIFIED | Both records exported with all 8 keys |
| `site/src/pages/crime-ranking/[crime].astro` | EN crime-type ranking pages, featured_rates branch, 200+ lines | VERIFIED | File exists; contains `featured_rates`; 480+ lines |
| `site/src/pages/es/ranking-delito/[crime].astro` | ES crime-type ranking pages, featured_rates branch, 200+ lines | VERIFIED | File exists; contains `featured_rates`; 480+ lines |
| `site/src/pages/commune/[slug].astro` | Homicide-ranking reciprocal spoke link, no vida duplicate | VERIFIED | Single `/crime-ranking/homicide/` href; `vida` filtered at line 243 |
| `site/src/pages/es/comuna/[slug].astro` | ES homicide-ranking reciprocal spoke link, no vida duplicate | VERIFIED | Single `/es/ranking-delito/homicidios/` href; `vida` filtered at line 246 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `[crime].astro` | `commune.featured_rates.homicidios[latestCompleteYear]` | `dataSource==='featured_rates'` branch | VERIFIED | Line 90: `commune.featured_rates?.homicidios?.[commune.latestCompleteYear] ?? 0` |
| `[crime].astro` | `/commune/{slug}/` | ranking table row anchor | VERIFIED | 346 commune links found in built homicide page |
| `[crime].astro (ES)` | `/es/comuna/{slug}/` | ranking table row anchor | VERIFIED | ES page contains `/es/comuna/` links |
| `[crime].astro` | `buildItemList / buildBreadcrumb` | jsonLd array passed to BaseLayout | VERIFIED | `ItemList` and `BreadcrumbList` present in built HTML |
| `seo.mjs` | `dist/crime-ranking/* + dist/es/ranking-delito/*` | firstSubdir heuristic in SAMPLES | VERIFIED | Lines 193-194 append guarded entries; actual built pages exist |
| `commune/[slug].astro` | `/crime-ranking/homicide/` only (no /crime/homicide/ duplicate) | `byFamily` loop with `filter(key !== 'vida')` | VERIFIED | Built algarrobo page: 1 hit for crime-ranking/homicide, 0 for crime/homicide |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `dist/crime-ranking/homicide/index.html` | Ranking table rows | `commune.featured_rates.homicidios` via `loadCommune()` | Yes — Saavedra #1 at 24 per 100k, non-uniform rates | VERIFIED |
| `dist/crime-ranking/property/index.html` | Ranking table rows | `commune.series[].by_family.propiedad` via `loadCommune()` | Confirmed by build passing (346 commune links in output) | VERIFIED |
| `sitemap-0.xml` | 16 new ranking URLs | Astro `@astrojs/sitemap` from getStaticPaths | 8 EN + 8 ES URLs present | VERIFIED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| CSEO-01 | 15-01, 15-02 | Páginas programáticas bilingües con internal linking, hreflang recíproco y sitemap | SATISFIED | 16 pages built; 346 commune links per page; hreflang en/es/x-default; 16 sitemap entries |
| CSEO-02 | 15-01, 15-02 | Cada página estática/indexable con un solo H1 keyword, title/canonical únicos, ItemList JSON-LD, tono sobrio | SATISFIED | Single H1 verified; canonical unique per slug; ItemList + BreadcrumbList present; forbidden-language validator green |

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `site/src/pages/crime-ranking/[crime].astro:81` | `latestYear = new Date().getFullYear() - 1` seed from wall clock | Warning | If dataset's latest complete year lags behind wall clock, table heading advertises a year no commune reports (WR-05) |
| `site/src/pages/es/ranking-delito/[crime].astro:23-33` | Duplicate `ES_CRIME_SLUGS` module-scope record (dead) | Info | Dead code; three copies of slug map across two files — drift risk (WR-03) |
| `site/src/pages/crime-ranking/[crime].astro:90,95` | Per-commune `latestCompleteYear` in rank loop vs global `latestYear` in heading (CR-02) | Warning | Ranking can mix years under single heading; inherited from `/crime/[family].astro` but now on new public pages |

CR-01 (vida duplicate spoke) — CLOSED (commit 30c7b7d). No longer an active finding.

No TBD, FIXME, or XXX debt markers found in modified files (debt-marker gate: PASS).

### Behavioral Spot-Checks

| Behavior | Result | Status |
|----------|--------|--------|
| `dist/crime-ranking/homicide/index.html` exists | File present | PASS |
| 8 EN ranking pages built | All 8 slugs under `dist/crime-ranking/` | PASS |
| 8 ES ranking pages built | All 8 slugs under `dist/es/ranking-delito/` | PASS |
| Homicide table non-zero rates | Saavedra #1 at rate 24 per 100k | PASS |
| Single H1 on homicide EN page | H1 count = 1 | PASS |
| hreflang en/es/x-default present | All 3 tags found | PASS |
| ES hreflang points to `/es/ranking-delito/homicidios/` | Confirmed | PASS |
| ItemList and BreadcrumbList JSON-LD | Both present in built HTML | PASS |
| 346 commune links in homicide ranking page | 346 `/commune/` hrefs | PASS |
| 16 new URLs in sitemap | 8 crime-ranking + 8 ranking-delito in sitemap-0.xml | PASS |
| Reciprocal homicide spoke in EN commune page (algarrobo) | Exactly 1 `/crime-ranking/homicide/` href, 0 `/crime/homicide/` hrefs | PASS |
| Reciprocal homicide spoke in ES commune page (algarrobo) | Exactly 1 `/es/ranking-delito/homicidios/` href, 0 `/es/delito/homicidios/` hrefs | PASS |

### Human Verification Required

#### 1. Locale Switcher Cross-Navigation

**Test:** Open `/crime-ranking/homicide/` in browser; click the locale switcher.

**Expected:** Browser navigates to `/es/ranking-delito/homicidios/`.

**Why human:** hreflang attribute presence is verified programmatically; actual navigation behavior (locale switcher component wiring) cannot be verified without a browser.

#### 2. Editorial Accuracy of Methodology Notes

**Test:** Read the methodology paragraph on `/crime-ranking/homicide/` and `/crime-ranking/property/`.

**Expected:** Notes are factually accurate: homicidio note references CEAD subgroup 101; propiedad note explicitly says it covers the full aggregate including hurtos and robos; both cite CEAD and use "denuncias" framing (not convictions).

**Why human:** Editorial accuracy of methodology copy requires human judgment; automated checks only confirmed CEAD is cited and forbidden terms are absent.

### Code Review Advisory Findings

**CR-01 — CLOSED (commit 30c7b7d):** `vida` key filtered from byFamily loop in both `commune/[slug].astro` (line 243) and `es/comuna/[slug].astro` (line 246). Built HTML confirms single homicide link per commune page in both locales.

**CR-02 (ADVISORY — not blocking):** National ranking table mixes per-commune `latestCompleteYear` values under a single `latestYear` heading. Propagated from existing `/crime/[family].astro`; not solely introduced by Phase 15. Does not break SEO indexability or structural correctness of the pages. Logged as tech debt.

**WR-01 through WR-06:** Lower-severity warnings documented in 15-REVIEW.md — rate??0 buries missing-data communes; Tarapacá region collision in region breakdown; duplicate ES_CRIME_SLUGS dead code; seo.mjs only samples first subdir; latestYear wall-clock seed; maxRegionRate floor at 1. None block goal achievement.

---

_Verified: 2026-06-16T14:00:00Z_
_Verifier: Claude (gsd-verifier)_
