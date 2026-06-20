---
phase: 21
plan: "02"
subsystem: frontend/island
tags: [comparator, react-island, seo-shell, i18n, autocomplete, homicide]
dependency_graph:
  requires: ["21-01"]
  provides: [CMP-01, CMP-02, comparator-island, compare-nav-link]
  affects: [PageHeader.astro, /compare/, /es/comparar/]
tech_stack:
  added: []
  patterns: [client:only="react", safeFetch, accent-insensitive autocomplete, HOM-02 !== undefined]
key_files:
  created:
    - site/src/islands/ComparatorIsland.tsx
    - site/src/pages/compare/index.astro
    - site/src/pages/es/comparar/index.astro
  modified:
    - site/src/components/PageHeader.astro
decisions:
  - strings prop pattern for client:only island (no EN/ES_STRINGS import at island module level)
  - hardcoded esPath=/es/comparar/ (i18n-localized-slug-pitfall)
  - Compare nav link placed after Map in nav order per UI-SPEC
metrics:
  duration: "~20m"
  completed: "2026-06-20"
  tasks: 2
  files: 4
---

# Phase 21 Plan 02: ComparatorIsland + EN/ES Shells + Compare Nav — Summary

**One-liner:** React island for 2–3-commune side-by-side comparison with accent-insensitive autocomplete, composite index, per-family breakdown, homicide sub-row (HOM-02), and Chile-avg column — mounted on pre-rendered indexable shells at /compare/ and /es/comparar/.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | ComparatorIsland.tsx — autocomplete + columns + homicide row | 818ead6 | site/src/islands/ComparatorIsland.tsx |
| 2 | EN + ES landing shells + Compare nav link | 818ead6 | compare/index.astro, es/comparar/index.astro, PageHeader.astro |

## What Was Built

### Task 1: ComparatorIsland.tsx
- Props: `{ lang: 'en'|'es'; communes: ComparatorEntry[]; strings: Record<string,string> }`
- Accent-insensitive autocomplete: `normalize('NFD').replace(/\p{Diacritic}/gu,'').toLowerCase()` — "nunoa" finds "Ñuñoa"
- Search index built from `communes` prop at init (no extra fetch); max 20 results shown
- Max 3 commune selection; keyboard nav (Arrow/Enter/Escape); aria-expanded/aria-disabled
- safeFetch copies verbatim from MapIsland.tsx; fetches `/data/cead/comunas/{cut}.json` per selection
- Fetches `/data/cead/national.json` once (memoized) and `/data/cead/regions/{id}.json` for avg column
- `latestCompleteYear` computed via `Math.max(...series.filter(s=>!s.partial).map(s=>s.year))`
- **HOM-02 homicide sub-row**: `homRate !== undefined && homCount !== undefined` (0 is valid, not "no data")
- Composite index: score at `--text-display`, band label, national rank
- Per-family table: 7 families + homicide sub-row; trend arrows ↑↓→ with `--trend-up/down/stable`
- Chile avg column: tinted `--bg` background + `--primary` border to distinguish
- All 8 interaction states: empty, 1-commune, 2–3, autocomplete open, no-match, loading skeleton, data error, max reached
- No import of EN_STRINGS/ES_STRINGS (client:only safety — strings passed as prop)
- No Leaflet dependency
- Mobile responsive: `flex-direction: column` at max-width 640px via scoped `<style>`

### Task 2: Landing shells + nav link
- `/compare/index.astro`: BaseLayout lang="en", esPath="/es/comparar/" (hardcoded), h1+lead+MethodologyCaveat+noscript+#comparator-root
- `/es/comparar/index.astro`: ES mirror with `../../../` import depth, ES_STRINGS, ES noscript text
- `PageHeader.astro`: `compareHref = locale === 'en' ? '/compare/' : '/es/comparar/'`; Compare link inserted after Map in nav

## Acceptance Criteria

- [x] File exports default React component with Props `{ lang; communes; strings }`
- [x] Homicide sub-row uses `!== undefined` (grep `homicidios_count` line 524)
- [x] normalizeForSearch uses NFD + `\p{Diacritic}` strip (line 82–83)
- [x] `npm run build` succeeds (833 pages, 19.33s)
- [x] `dist/compare/index.html` and `dist/es/comparar/index.html` exist
- [x] Each shell contains `<h1>`, lead, MethodologyCaveat, noscript, `#comparator-root`
- [x] EN shell links to `/es/comparar/` (hreflang reciprocity verified)
- [x] PageHeader contains Compare nav link for both locales (grep "comparar" passes)
- [x] No top-level import of EN_STRINGS/ES_STRINGS in island

## Human-Verify Checkpoint (Task 3 — pending)

**Type:** checkpoint:human-verify  
**Status:** awaiting human verification

### Automated checks (completed):
- Build: 833 pages, green, 19.33s
- dist/compare/index.html: comparator-root + h1 + /es/comparar/ hreflang — OK
- dist/es/comparar/index.html: comparator-root + h1 + /es/comparar/ — OK
- PageHeader nav comparar link: OK
- Source assertions (homicidios_count, NFD/Diacritic, no EN_STRINGS import): OK

### Manual steps for verifier:
1. Run: `cd site && npx astro preview --port 4321 --host`
2. Visit http://localhost:4321/compare/ — confirm h1 + lead + methodology caveat render before JS (view-source)
3. Type "nunoa" (no tilde) — confirm "Ñuñoa" appears in autocomplete dropdown
4. Select 2–3 communes — confirm side-by-side columns: composite score, per-family rates with arrows, homicide row, Chile avg column
5. Confirm a commune with 0 homicides shows 0.00 (not "no data")
6. Visit http://localhost:4321/es/comparar/ — confirm ES copy: "Comparar Comunas…" / "Prom. Chile" / "Homicidios"
7. Open at 375px — columns stack vertically, no horizontal scroll
8. Confirm no absolute "safe/dangerous/seguro/peligroso" verdict anywhere
9. Type "approved" or describe issues to resume

## Deviations from Plan

None — plan executed as written. Tasks 1 and 2 committed together (single atomic unit — island + shell + nav are tightly coupled; build verification requires all three).

## Threat Surface Scan

| Flag | File | Description |
|------|------|-------------|
| (none) | — | No new network endpoints, auth paths, or schema changes introduced. Island fetches same-origin static JSON already public (T-21-05 accepted). No dangerouslySetInnerHTML anywhere (T-21-04 mitigated by React auto-escape). |

## Known Stubs

None. The island renders real data from `/data/cead/comunas/{cut}.json` (same source as commune pages). National/regional averages from `/data/cead/national.json` and `/data/cead/regions/{id}.json`. All data is live CEAD pipeline output.

## Self-Check: PASSED

- [x] `site/src/islands/ComparatorIsland.tsx` exists
- [x] `site/src/pages/compare/index.astro` exists
- [x] `site/src/pages/es/comparar/index.astro` exists
- [x] `site/src/components/PageHeader.astro` modified (compareHref + nav link)
- [x] Commit 818ead6 exists in git log
- [x] `dist/compare/index.html` and `dist/es/comparar/index.html` exist with correct content
