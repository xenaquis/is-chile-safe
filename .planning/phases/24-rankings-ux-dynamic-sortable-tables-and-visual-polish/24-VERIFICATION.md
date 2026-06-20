---
phase: 24-rankings-ux-dynamic-sortable-tables-and-visual-polish
verified: 2026-06-20T00:00:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Navigate to /safest-cities-in-chile/ and /es/comunas-mas-seguras-chile/ in a real browser at desktop (1280px) and mobile (375px). Confirm the teal (rgb(15,118,110)) ascending arrow ▲ is visible on the rate column header within 500ms of page load, the year <select> appears above the table, and clicking the rate header re-sorts rows descending and back."
    expected: "▲ teal arrow visible on load; year selector present; click toggles to ▼ and back; rows reorder correctly (lowest rate first on load, highest first after first click)."
    why_human: "BrowserOS review ran DOM-based assertions on the localhost preview. The screenshots are ephemeral tmp files not committed to the repo. A second human confirmation in a real browser (or CI screenshot baseline) closes this evidence gap."
  - test: "On a mobile device or devtools 375px emulation, verify the safest-cities ranking table scrolls horizontally without breaking page layout."
    expected: "Table body scrolls left-right inside the wrapper; no horizontal page overflow; sort arrow still visible after scroll."
    why_human: "Mobile check in 24-02 was structural (overflow-x CSS confirmed via DOM query) — no actual scroll interaction was performed."
---

# Phase 24: Rankings UX — Dynamic Sortable Tables and Visual Polish — Verification Report

**Phase Goal:** Make the ranking pages feel like first-class, sortable data tables. Wire the existing `RankingTableEnhancer` island into safest-cities surfaces (EN+ES per the UI-SPEC), default sort descending with a per-page ascending override, make sortability visually obvious (teal #0f766e affordance on load), apply polish with existing brand tokens. Close with a BrowserOS in-detail E2E visual review (EN+ES, desktop + mobile).

**Verified:** 2026-06-20
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

The phase goal decomposes into five observable truths. All five are verified by codebase evidence.

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | On home and crime-family ranking pages the rate column header shows ▼ (descending) on page load without user interaction. | VERIFIED | `RankingTableEnhancer.astro` line 106: `sortKey = 'rate'`; line 107: `sortDir = defaultSortDir`; lines 263-264: `updateAriaSort()` + `renderSort()` called at end of per-table init outside any event handler. The `defaultSortDir` fallback is `'desc'` when the attribute is absent (line 78). All existing home/crime-family tables have no `data-default-sort-dir` so they continue to load descending. |
| 2 | On `/safest-cities-in-chile/` and `/es/comunas-mas-seguras-chile/`, a ▲ (ascending) sort arrow is visible on the rate column header on page load, preserving the editorial lowest-first intent. | VERIFIED | `safest-cities-in-chile.astro` line 130: `data-default-sort-dir="asc"` on the `<table>`. `comunas-mas-seguras-chile.astro` line 124: same attribute. The enhancer reads `table.dataset.defaultSortDir` at init and wires `sortDir = 'asc'` for these two tables. DOM-asserted in BrowserOS review (24-02-SUMMARY): ascending default confirmed on both surfaces. |
| 3 | Clicking any ranking table's rate or commune-name header re-sorts rows and updates the visible arrow and `aria-sort`. | VERIFIED | `RankingTableEnhancer.astro` click handler at line 163 calls `updateAriaSort()` + `renderSort()`. BrowserOS review confirmed: safest-cities EN rate header toggled ascending (3,223/3,512/3,984) → descending (9,748/9,359/9,309). EN number-locale (comma) and ES locale (period) both correct per review record. |
| 4 | A year `<select>` appears above each safest-cities ranking table and re-renders rates for the chosen year. | VERIFIED | Both safest-cities pages have `data-rates={JSON.stringify(c.ratesByYear)}` per row (`safest-cities-in-chile.astro` line 148) populated from `data.series.filter(s => !s.partial)` using `s.rate_per_100k` (total rate, not by_family). The enhancer builds the controls strip from these rows' data. BrowserOS review: year `<select>` confirmed present and functional on both surfaces. |
| 5 | Home EN/ES preview tables are clean static teasers with no implied-but-absent sort affordance (GAP-24A closed). Region pages and crime-family pages keep their sortable behavior unchanged. | VERIFIED | `CommuneRankingTable.astro` lines 30+33: `sortable?: boolean` prop defaults to `true`. Lines 53, 67, 93: when `sortable=false`, `data-ranking-table`, per-row `data-rates`, and `<RankingTableEnhancer>` are all omitted. `index.astro` lines 105+111: `sortable={false}` on both `lowestRows` and `highestRows` tables. `es/index.astro` lines 105+111: same. 24-03-SUMMARY confirms `dist/index.html` has 0 occurrences of `data-ranking-table`; region pages still have 1. |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact | Provides | Status | Details |
|----------|----------|--------|---------|
| `site/src/components/RankingTableEnhancer.astro` | Auto-initialized sort on load honoring `data-default-sort-dir` | VERIFIED | `defaultSortDir` read at line 78 (declaration) and used at line 107 (sortDir init). `sortKey` initialized to `'rate'` at line 106 (was `null`). `updateAriaSort()` + `renderSort()` called at lines 263-264 (outside event handlers). `hasRatesData` guard at line 88 preserved. |
| `site/src/pages/safest-cities-in-chile.astro` | Wired sortable ranking table (data-ranking-table, per-row data-rates, enhancer mounted, asc override) | VERIFIED | Import at line 13; `data-ranking-table` at line 125; `data-default-sort-dir="asc"` at line 130; `data-rates={JSON.stringify(c.ratesByYear)}` at line 148; `<RankingTableEnhancer locale="en" />` at line 161; `-webkit-overflow-scrolling: touch` at line 281. |
| `site/src/pages/es/comunas-mas-seguras-chile.astro` | ES wired sortable ranking table (mirror of EN, data-locale=es) | VERIFIED | Import at line 13; `data-ranking-table` at line 119; `data-default-sort-dir="asc"` at line 124; `<RankingTableEnhancer locale="es" />` at line 155. |
| `site/src/components/CommuneRankingTable.astro` | `sortable` prop gating data-ranking-table + enhancer mount | VERIFIED | Props interface at line 30 (`sortable?: boolean`); destructured with default `true` at line 33; conditional spread at line 53 gates table-level attrs; line 67 gates per-row `data-rates`; line 93 gates enhancer mount. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `safest-cities-in-chile.astro` | `RankingTableEnhancer.astro` | `import` + `<RankingTableEnhancer locale="en" />` after table wrapper | WIRED | Import confirmed line 13; component rendered line 161 |
| `safest-cities-in-chile.astro <tr>` | `RankingTableEnhancer renderSort()` | `data-rates` JSON from `data.series.filter(!partial)` using `rate_per_100k` | WIRED | Line 148 confirmed; `ratesByYear` built per-commune in frontmatter |
| `RankingTableEnhancer init` | `<table data-default-sort-dir>` | `table.dataset.defaultSortDir` read drives initial `sortDir`; absent => `'desc'` | WIRED | Lines 78 and 107 confirmed; fallback `'desc'` correct |
| `index.astro` / `es/index.astro` home teasers | `CommuneRankingTable sortable=false` | `sortable={false}` prop omits `data-ranking-table` and enhancer | WIRED | Lines 105+111 in both home pages confirmed |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `safest-cities-in-chile.astro` | `c.ratesByYear` (per-row `data-rates`) | `data.series.filter(s => !s.partial)` — build-time CEAD JSON via `loadCommune()` | Yes — CEAD static JSON, not hardcoded | FLOWING |
| `RankingTableEnhancer.astro` | `yearRate` / `dataset.numericRate` | Parsed from each row's `data-rates` attribute seeded above | Yes — real rates per year per commune | FLOWING |

---

### Behavioral Spot-Checks

Step 7b spot-checks cannot run without a live server (`astro preview`). The BrowserOS inline review in 24-02 performed the equivalent DOM-assertion checks on the served preview. Results from that review:

| Behavior | Method | Result | Status |
|----------|--------|--------|--------|
| safest-cities EN: ▲ on load, year select present, click re-sorts | DOM assertion via `evaluate_script` | Arrow confirmed teal rgb(15,118,110), asc default, click toggles to desc | PASS |
| safest-cities ES: ▲ on load, year select, click re-sorts | DOM assertion | PASS (ES locale, period number format) | PASS |
| crime-ranking EN: ▼ on load, year select | DOM assertion, 346 rows | PASS | PASS |
| crime-ranking ES: ▼ on load | DOM assertion | PASS | PASS |
| Home EN/ES: no sort affordance emitted | DOM assertion — 0 `data-ranking-table` in built HTML | PASS | PASS |
| Focus ring (keyboard Tab on sort button) | DOM computed-style check | 2px solid teal, offset 2px confirmed | PASS |
| Mobile 375px horizontal overflow | CSS computed-value check (`overflow-x: auto`) | PASS (structural; no live scroll interaction) | PASS (structural) |

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| None found | — | — | — |

No `TBD`, `FIXME`, `XXX`, placeholder returns, or hardcoded empty data found in the three modified source files. The `sortable=false` branch intentionally omits `data-rates` — this is not a stub; it is the correct static-teaser rendering path.

---

### Requirements Coverage

Phase 24 has no formal requirement IDs (ROADMAP: "TBD", `requirements: []` intentional). Coverage verified against the phase goal and 24-UI-SPEC.md.

| UI-SPEC Requirement | Status | Evidence |
|--------------------|--------|----------|
| Wire safest-cities EN+ES into RankingTableEnhancer | SATISFIED | Both pages wired with all required data-attrs, per-row data-rates, enhancer mount |
| Ascending default on safest-cities (editorial lowest-first) | SATISFIED | `data-default-sort-dir="asc"` + enhancer reads attribute |
| Descending default on home/crime-family (no regression) | SATISFIED | Absent attribute falls back to `'desc'`; BrowserOS review confirmed no regression |
| Sort arrow visible on load without user interaction | SATISFIED | `sortKey='rate'` init + `updateAriaSort()` + `renderSort()` at end of table init block |
| Teal #0f766e sort arrow color | SATISFIED | Pre-existing `.rte-sort-btn` active styles use `--primary` (#0f766e); DOM review confirmed `rgb(15,118,110)` |
| Year select appears above table | SATISFIED | Enhancer builds controls strip on init; confirmed by BrowserOS review |
| Click-to-sort re-orders rows and updates arrow | SATISFIED | Header click handler wired; confirmed by rate toggle 3,223→9,748 in BrowserOS review |
| No new npm dependencies | SATISFIED | 24-01-SUMMARY: package.json unchanged; validators pass |
| i18n.ts untouched | SATISFIED | 24-01-SUMMARY confirms; required strings already present |
| Home teasers: remove vestigial data-ranking-table (GAP-24A) | SATISFIED | `sortable` prop + `sortable={false}` on home tables; built HTML confirmed 0 occurrences |
| Mobile overflow-x: auto on safest-cities wrapper | SATISFIED | `-webkit-overflow-scrolling: touch` added; `overflow-x: auto` already present |
| No new component library or shadcn | SATISFIED | All changes are vanilla JS + existing CSS tokens |

---

### Human Verification Required

#### 1. Visual confirmation of sort arrow + year select on safest-cities pages (browser)

**Test:** Open https://ischilesafe.com/safest-cities-in-chile/ (or localhost preview) in a real browser. Without clicking anything, observe the rate column header.
**Expected:** A teal (visually green/teal) upward-pointing arrow ▲ is visible on the rate header immediately after page load. A "Year:" label and `<select>` appear above the table. Clicking the rate header reverses the sort to descending (▼) and the row with the highest rate moves to the top.
**Why human:** The BrowserOS review used DOM-assertion style `evaluate_script` checks rather than pixel-level screenshot comparison. The screenshots saved to `C:/tmp/p24-review/` are ephemeral and not committed. A real-browser confirmation closes the evidence gap on visual correctness.

#### 2. Mobile scroll behavior on safest-cities table (375px)

**Test:** Open `/safest-cities-in-chile/` in Chrome devtools with iPhone SE (375px) emulation or a real mobile device. Scroll the table row of data left and right.
**Expected:** The table body scrolls horizontally within its wrapper; no horizontal page overflow bar appears at the document level; the sort arrow remains visible after scrolling.
**Why human:** The 24-02 mobile check confirmed `overflow-x: auto` via CSS computed value. Actual touch-scroll behavior was not exercised — a cross-origin iframe blocked introspection in BrowserOS.

---

### Gaps Summary

No code gaps. All five observable truths are verified in the codebase by direct code inspection. The two human verification items above are confirmation items, not implementation gaps — the code and CSS are in place; they need a real-browser visual spot-check to close the evidence trail started by the BrowserOS review.

GAP-24A (home previews not sortable) was raised in 24-02, triaged as a scope/design question, and resolved in 24-03 via the `sortable` prop approach (user decision: static teasers, not sortable). The gap is closed at the code level; the 24-03 build verification confirmed 0 `data-ranking-table` occurrences in both home pages.

---

_Verified: 2026-06-20_
_Verifier: Claude (gsd-verifier)_
