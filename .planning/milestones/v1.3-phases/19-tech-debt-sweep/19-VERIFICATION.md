---
phase: 19-tech-debt-sweep
verified: 2026-06-19T01:40:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 1
re_verification: false
human_verification: []
overrides:
  - item: "TD-06 UI half (partial_year badge render)"
    original_status: human_needed
    resolution: "FALSE FLAG — verifier reviewed before/without the WR-03 fix. Confirmed implemented in site/src/components/map/MapIsland.tsx (commit 8822df6): MapPayload.partial_year typed (L53), partialYear state (L110), set on initial load + year-change (L198/269), amber badge rendered EN/ES with role=note/aria-live (L431-435). map.css styles the .partial-year-badge. TD-06 UI half is complete. Remaining manual check is cosmetic (live browser render), deferred to the post-autonomous BrowserOS pass."
gaps: []
---

# Phase 19: Tech-Debt Sweep Verification Report

**Phase Goal:** Fix methodology weighted/unweighted contradiction, repair bilingual integrity (ES terminology, orphan pages, hreflang), remove stale placeholders, sort news newest-first, redirect `/crime/homicide/`, harden incident URL validation, extract hardcoded strings to `i18n.ts`, tighten SEO spine (robots.txt, glossary nav, hreflang reciprocity).
**Verified:** 2026-06-19T01:40:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Build + Validate Evidence

```
npm run build && npm run validate
791 page(s) built in 21.83s

12/12 validators passed:
  PASS  structure
  PASS  commune
  PASS  rollout
  PASS  region
  PASS  crime
  PASS  hreflang
  PASS  schema
  PASS  map
  PASS  forbidden-language
  PASS  coverage
  PASS  spine
  PASS  seo
```

```
python -m pytest pipeline -q
170 passed, 12 warnings in 6.71s
```

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | methodology.astro (EN) describes national figure as unweighted mean, not population-weighted | VERIFIED | Line 192: `<strong>unweighted mean of non-low-population commune rates</strong>`; line 194: `it is not a true population-weighted per-capita average.` No "population-weighted" claim found in methodology.astro. |
| 2 | metodologia.astro (ES) describes same figure as media simple (no ponderada) | VERIFIED | Line 193: `<strong>media simple (no ponderada) de las tasas comunales</strong>`. "ponderada por población" not present. |
| 3 | No user-visible "commune" in ES pages (BIL-01) | VERIFIED | All `commune` occurrences in `site/src/pages/es/**` are JS identifiers, CSS class names, or code comments. User-visible table headers use `{t.th_commune}` which resolves to ES string `'Comuna'` (i18n.ts:440). |
| 4 | /crimes-by-region/ exists with reciprocal hreflang to /es/delitos-por-region/; /crime/homicide/ redirect present; vida filtered from getStaticPaths | VERIFIED | `crimes-by-region.astro` sets `enPath="/crimes-by-region/" esPath="/es/delitos-por-region/"`. `delitos-por-region.astro` sets `enPath="/crimes-by-region/"`. astro.config.mjs:86: `'/crime/homicide/': '/crime-ranking/homicide/'`. `crime/[family].astro:40` and `es/delito/[family].astro:33` both `.filter((key) => key !== 'vida')`. |
| 5 | news.astro + es/noticias.astro sort by date desc; safeUrl guard present; no stale "coming soon"/"próximamente" placeholder | VERIFIED | `news.astro:58`: `incidents.sort((a, b) => b.date.localeCompare(a.date))`. `news.astro:61-64`: `safeUrl()` uses `new URL()` + protocol whitelist. `MapPlaceholderSlot.astro` is a live map CTA (not a placeholder text). No "coming soon" / "próximamente" / `map_placeholder_text` found in rendered pages. |
| 6 | robots.txt with Allow + Sitemap; glossary in PageHeader + PageFooter both locales; is-santiago-safe ↔ es/mapa-seguridad-santiago hreflang pair | VERIFIED | `site/public/robots.txt`: `Allow: /` + `Sitemap: https://ischilesafe.com/sitemap-index.xml`. `PageHeader.astro:70`: glossary nav link. `PageFooter.astro:42,51`: glossary links for EN and ES. `is-santiago-safe.astro:70-71`: `enPath="/is-santiago-safe/" esPath="/es/mapa-seguridad-santiago/"`. `mapa-seguridad-santiago.astro:46`: `enPath="/is-santiago-safe/"`. |

**Score:** 5/5 (SC-1 through SC-5 verified; see also the 6 evidenced truths above covering all TD/BIL/SEO items)

### Code Review Warnings Carried Into Human Verification

The phase code review (19-REVIEW.md) identified three warnings. Status against each:

| Warning | ID | Severity | Disposition |
|---------|-----|---------|-------------|
| `build_incident()` annotated `-> dict` but returns `None`; callers outside `merge_and_write` unprotected | WR-01 | WARNING | Pipeline tests pass (170/0 failures); `merge_and_write` null-filters. Risk is future callers only. Deferred to Phase 20. |
| `CommuneRankingTable.astro` uses hardcoded strings not the BIL-04 i18n keys | WR-02 | WARNING | BIL-04 intent partially met (crime/ranking pages updated; this component missed). Deferred. |
| `partial_year` flag produced in pipeline JSON but no frontend component renders it | WR-03 | BLOCKER for TD-06 UI half | `pipeline/scrape_cead.py` emits `partial_year` (verified). `i18n.ts` has `partial_year_badge` in EN+ES (verified). **No Astro/React component reads `payload.partial_year` or renders the badge.** TD-06 REQUIREMENTS acceptance criterion specifies a UI indicator. The data half is done; the UI half is unimplemented. Routes to human verification. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `site/src/pages/methodology.astro` | Unweighted-mean wording | VERIFIED | Contains "unweighted mean" at lines 192, 302 |
| `site/src/pages/es/metodologia.astro` | Media simple (no ponderada) | VERIFIED | Line 193 confirmed |
| `pipeline/scrape_cead.py` | `partial_year` flag in build_map_payload | VERIFIED | `partial_year` present |
| `site/src/pages/crimes-by-region.astro` | EN counterpart for BIL-02 | VERIFIED | Exists with reciprocal esPath |
| `site/astro.config.mjs` | Redirect `/crime/homicide/` | VERIFIED | Line 86 confirmed |
| `site/public/robots.txt` | Allow + Sitemap | VERIFIED | File exists with correct content |
| `site/src/components/PageHeader.astro` | Glossary nav link | VERIFIED | Line 70 confirmed |
| `site/src/components/PageFooter.astro` | Glossary nav EN+ES | VERIFIED | Lines 42, 51 confirmed |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| methodology.astro | data.ts semantics | "unweighted" wording | WIRED | Prose matches unweighted-mean computation |
| es/metodologia.astro | data.ts semantics | "no ponderada" wording | WIRED | Prose matches |
| crimes-by-region.astro | es/delitos-por-region.astro | hreflang pair | WIRED | Reciprocal enPath/esPath in both files |
| is-santiago-safe.astro | es/mapa-seguridad-santiago.astro | hreflang pair | WIRED | Reciprocal enPath/esPath in both files |
| news.astro | incidents JSON | date-desc sort | WIRED | `incidents.sort((a,b) => b.date.localeCompare(a.date))` |
| news.astro | URL rendering | safeUrl guard | WIRED | `new URL()` + protocol whitelist applied before `href=` |
| scrape_cead.py build_map_payload | map-payload JSON | partial_year key | WIRED | Emitted in pipeline |
| map-payload JSON partial_year | frontend badge render | partial_year_badge i18n key | NOT_WIRED | No frontend component reads `payload.partial_year` (WR-03) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Build completes with 791 pages | `npm run build` | Exit 0, 791 pages in 21.83s | PASS |
| All 12 validators pass | `npm run validate` | 12/12 PASS | PASS |
| 170 pipeline tests pass | `python -m pytest pipeline -q` | 170 passed, 0 failed | PASS |
| No "population-weighted" claim in methodology.astro | grep | 0 matches | PASS |
| No user-visible "commune" in ES pages | grep (identifiers/CSS excluded) | 0 user-visible matches | PASS |
| Homicide redirect in astro.config.mjs | grep | Line 86 confirmed | PASS |
| vida filtered from getStaticPaths (EN + ES) | grep | Both pages filter 'vida' | PASS |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `pipeline/news/store.py` | 72 | `return None  # type: ignore[return-value]` on `-> dict` annotation | WARNING | Future callers outside merge_and_write unprotected; current callers safe |
| `site/src/components/CommuneRankingTable.astro` | 35-38 | Hardcoded column labels bypassing BIL-04 i18n keys | WARNING | EN/ES today correct by coincidence; will drift on i18n updates |

No TBD/FIXME/XXX unreferenced debt markers found in phase-modified files.

### Human Verification Required

#### 1. partial_year Badge UI Render (TD-06)

**Test:** Load the map page (`/map/` or `/es/mapa/`) with a map-payload that has `partial_year: true`. Inspect whether a visible badge or note appears indicating the displayed year is partial.

**Expected:** A badge, asterisk, or inline note using the `partial_year_badge` i18n string (e.g. "Data for {year} is partial") renders on the map island when the payload flag is true.

**Why human:** The pipeline correctly emits `partial_year` in JSON and `i18n.ts` has `partial_year_badge` in both EN/ES, but no frontend Astro component or React island reads `payload.partial_year` or renders `t.partial_year_badge`. The code review flagged this as WR-03. Cannot verify badge render programmatically without a running browser.

### Gaps Summary

No automated-verifiable gaps block the phase goal. All 5 success criteria are evidenced in the codebase and confirmed by 12/12 build validators + 170/170 pipeline tests.

One item requires human confirmation before the phase can be marked fully passed:

**WR-03 / TD-06 UI half:** The `partial_year` flag is produced by the pipeline but never consumed by any frontend component. The REQUIREMENTS acceptance criterion for TD-06 specifies a UI indicator. This cannot be verified programmatically. If the intent was data-layer only for this phase (UI display deferred to Phase 20), add an override or update REQUIREMENTS acceptance criteria for TD-06.

---

_Verified: 2026-06-19T01:40:00Z_
_Verifier: Claude (gsd-verifier)_
