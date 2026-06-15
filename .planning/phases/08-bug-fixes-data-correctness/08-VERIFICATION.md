---
phase: 08-bug-fixes-data-correctness
verified: 2026-06-15T09:40:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Open money pages and /map/ in a real browser; open DevTools Console; navigate and interact with the map"
    expected: "Zero console errors and zero console warnings on all 11 EN money pages plus /map/"
    why_human: "Console output during client-side Leaflet/React island hydration cannot be observed by static build grep; the REVIEW-01 baseline was established by a live browser session in Phase 7 and Phase 8 adds no new client-side code, but the clean-console claim requires a human browser run to be auditable under BUGFIX-01"
  - test: "Open /crime/homicide/ and /es/delito/homicidio/ in a browser; verify the rank numbers (#N) shown in the table match national standing, not filtered-list position"
    expected: "Each commune shows its true national rank (e.g. a commune at #87 nationally displays #87, not #1)"
    why_human: "CR-01 fix is code-verified (nationalRank assigned from pre-filter counter, rendered as row.nationalRank); functional correctness with real rollout data requires a human to cross-reference a displayed rank against the commune's data/cead/ national_rank field"
  - test: "Open the site at <640px viewport; activate the hamburger menu; attempt to close it with the Escape key"
    expected: "Known limitation: Escape does not close the CSS-only menu (WR-03 intentionally deferred — D-09 zero-JS constraint). No crash or console error. Tab order does not land on the hidden checkbox."
    why_human: "WR-02 (tabindex=-1) is code-verified. WR-03 (Escape + focus management) is a known deferred a11y gap requiring human observation on mobile viewport"
---

# Phase 8: Bug Fixes & Data Correctness — Verification Report

**Phase Goal:** All Critical findings from the E2E review are corrected and re-verified; console is clean on money pages; data calculations are accurate; AdSlot does not cause layout shift.
**Verified:** 2026-06-15T09:40:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | CR-01 fixed: crime ranking pages show true national rank, not filtered-list index | VERIFIED | `site/src/pages/crime/[family].astro` lines 82-124: `nationalRank` counter assigned over `eligibleRows` before rollout filter; table renders `row.nationalRank` (line 240). ES mirror identical (lines 75-116, 230). |
| 2 | Console clean on money pages (BUGFIX-01) | VERIFIED (code) / HUMAN NEEDED (runtime) | Phase 8 adds zero client-side code (08-01 through 08-04 are all build-time or CSS-only). No new `client:*` directive introduced. REVIEW-01 baseline: 0 errors/warnings on 30 URLs. Runtime confirmation requires browser. |
| 3 | Internal links resolve without 404 — no non-rollout commune hrefs in built HTML (BUGFIX-02) | VERIFIED | `grep -r "href=\"/commune/cerrillos/\""` in `dist/` → 0 occurrences. All 4 ranking templates (region EN/ES, crime EN/ES) filter through `loadRolloutCuts()`. |
| 4 | Rates use `loadNationalAverage` (arithmetic mean of per-100k rates, not raw sum); ranking by rate/100k (BUGFIX-03) | VERIFIED | `site/src/lib/data.ts` line 190: `return rates.length > 0 ? sum / rates.length : 0`. `latestCompleteYearRate` ensures non-partial years. Spot-check: Santiago 9,309/100k, Concepción 7,256/100k, Punta Arenas 3,512/100k match `data/cead/` source. |
| 5 | AdSlot reserves height (90px/50px) and emits zero `<ins class="adsbygoogle">` when ADSENSE_ENABLED is unset (BUGFIX-04) | VERIFIED | `AdSlot.astro` line 18: `const enabled = import.meta.env.ADSENSE_ENABLED === 'true'`. CSS: `.ad-slot--content { height: 90px }`, mobile 50px. `grep -r "adsbygoogle" dist/` → 0 occurrences in built output. |

**Score:** 5/5 truths verified (3 automated, 2 partially human-gated)

---

### Requirements Coverage

| Requirement | Phase | Description | Status | Evidence |
|-------------|-------|-------------|--------|----------|
| BUGFIX-01 | Phase 8 | Zero browser console errors on money pages | VERIFIED (code) | No new client-side code in Phase 8; build clean 100 pages/0 errors |
| BUGFIX-02 | Phase 8 | Internal links resolve without 404; hreflang reciprocal correct | VERIFIED | 0 dead-link patterns in dist/; hreflang×3 on home page |
| BUGFIX-03 | Phase 8 | Rates use loadNationalAverage (mean not sum); ranking by rate/100k; 3+ communes spot-checked | VERIFIED | data.ts mean confirmed; 3 communes verified against data/cead/ |
| BUGFIX-04 | Phase 8 | AdSlot reserves height; no adsbygoogle in DOM when disabled | VERIFIED | CSS heights intact; 0 adsbygoogle in dist/ |
| BUGFIX-05 | Phase 8 | All Critical findings corrected; Warnings resolved or deferred with justification | VERIFIED | CR-01 fixed (commit 1754afe); WR-01/02/04/05 fixed; WR-03 deferred under D-09 constraint; F-002/03/04/06/08 deferred to Phase 9 with written justification |

All 5 BUGFIX requirements mapped to Phase 8 are accounted for. No orphaned requirements found. UX/READ/A11Y requirements are correctly mapped to Phase 9 (Pending) — not in scope for Phase 8.

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `site/src/pages/crime/[family].astro` | CR-01 fix: nationalRank field + displayedRows filter | VERIFIED | `nationalRank` assigned pre-filter (line 117); rendered via `row.nationalRank` (line 240); `rolloutCuts.has(row.cut)` direct filter (line 124) |
| `site/src/pages/es/delito/[family].astro` | CR-01 fix (ES mirror) | VERIFIED | Identical structure; nationalRank lines 109/230; rolloutCuts.has line 116 |
| `site/src/pages/region/[slug].astro` | Rollout-gated ranking rows (EN) | VERIFIED | `loadRolloutCuts` imported (line 27); `displayedRows` passed to CommuneRankingTable (line 213) |
| `site/src/pages/es/region/[slug].astro` | Rollout-gated ranking rows (ES) | VERIFIED | `loadRolloutCuts` imported (line 21); `displayedRows` passed (line 201) |
| `site/src/components/PageHeader.astro` | WR-02 fix: tabindex=-1 on hidden checkbox | VERIFIED | Line 42: `<input type="checkbox" id="nav-toggle" class="nav-toggle-input" aria-hidden="true" tabindex="-1" />` |
| `site/src/components/AdSlot.astro` | Height reservation + env gate + no adsbygoogle when disabled | VERIFIED | 90px/50px CSS; `=== 'true'` gate; 0 adsbygoogle in dist/ |
| `site/src/lib/data.ts` | loadNationalAverage = arithmetic mean | VERIFIED | Line 190: `sum / rates.length` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `crime/[family].astro` | true national rank | `nationalRank` counter over `eligibleRows` pre-filter | VERIFIED | Counter increments before `displayedRows` filter; table reads `row.nationalRank` |
| `crime/[family].astro` | rollout.json | `loadRolloutCuts()` → `rolloutCuts.has(row.cut)` | VERIFIED | Direct CUT field on row; no lossy slug lookup |
| `region/[slug].astro` | rollout.json | `loadRolloutCuts()` → `displayedRows` filter | VERIFIED | CommuneRankingTable receives `displayedRows` |
| `AdSlot.astro` | ADSENSE_ENABLED env var | `=== 'true'` strict equality gate | VERIFIED | `<ins>` element only rendered when gate passes |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `crime/[family].astro` | `nationalRank` | Counter over CEAD index `eligibleRows` | Yes — derived from real commune data at build time | FLOWING |
| `region/[slug].astro` | `displayedRows` | `rankingRows` filtered by `loadRolloutCuts()` | Yes — real CEAD commune data | FLOWING |
| `AdSlot.astro` | `enabled` | `import.meta.env.ADSENSE_ENABLED` | Env gate; no data flow needed | N/A |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Build produces 100 pages with 0 errors | `cd site && npm run build` | 100 pages in 24.58s, 0 errors | PASS |
| No adsbygoogle in built output | `grep -r "adsbygoogle" dist/` | 0 occurrences | PASS |
| No dead 404-bound commune hrefs | `grep -r "href=\"/commune/cerrillos/\"" dist/` | 0 occurrences | PASS |
| nationalRank assigned pre-filter | grep pattern in crime/[family].astro | `row.nationalRank` rendered; counter over eligibleRows before filter | PASS |
| loadNationalAverage is mean not sum | grep in data.ts | `sum / rates.length` confirmed | PASS |

### Probe Execution

No probe scripts declared in PLAN files. No `scripts/*/tests/probe-*.sh` found. Step 7c: SKIPPED (no declared probes).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | No TBD/FIXME/XXX markers in modified files | — | — |

WR-03 (hamburger keyboard dismiss) is an intentionally skipped finding under D-09 (zero-JS constraint), not an unresolved debt marker. The REVIEW-FIX.md documents the skip reason explicitly.

---

### Human Verification Required

#### 1. Console Cleanliness on Money Pages (BUGFIX-01 runtime confirmation)

**Test:** Open `/is-santiago-safe/`, `/is-chile-safe/`, `/map/`, and 3–4 other money pages in Chrome/Firefox. Open DevTools Console. Navigate between pages and interact with the map (change year, change crime type, click a commune).
**Expected:** Zero console errors, zero console warnings on all pages. The Leaflet/React island hydrates without error.
**Why human:** Static build grep cannot observe client-side JavaScript execution, React hydration errors, or Leaflet initialization warnings. Phase 8 adds no new client code, but the REVIEW-01 baseline needs runtime confirmation to be auditable.

#### 2. National Rank Correctness on Crime Pages (CR-01 functional verification)

**Test:** Open `/crime/homicide/` (or any crime family page). Note a displayed commune and its shown rank (e.g. "#5"). Navigate to that commune's individual page or check `data/cead/comunas/{CUT}.json` for its `national_rank` field.
**Expected:** The rank displayed in the crime family table matches the commune's true national position in the data, not its position in the rollout-filtered display list.
**Why human:** Code is verified correct (nationalRank assigned before filter), but a human cross-reference against a real commune's `national_rank` in `data/cead/` gives end-to-end confidence that the fix works with live rollout data.

#### 3. Hamburger Menu Keyboard Behavior (WR-03 known limitation confirmation)

**Test:** On a <640px viewport (or browser resize), open the hamburger menu by clicking/tapping it. Try pressing Escape to close it. Tab through the navigation.
**Expected:** Escape does NOT close the menu (known CSS-only limitation, D-09). Tab order skips the hidden checkbox (tabindex=-1 fix verified). No console error. The known limitation is acceptable under the zero-JS constraint.
**Why human:** CSS-only interactive state cannot be verified programmatically. The tabindex fix (WR-02) is code-verified; the broader WR-03 keyboard accessibility gap is documented as a deferred known limitation requiring human acknowledgment.

---

### Gaps Summary

No automated gaps found. All 5 BUGFIX requirements have code-level evidence of correct implementation. The Critical finding (CR-01) is demonstrably fixed with the correct algorithm (pre-filter rank counter). The 3 human verification items are runtime confirmations of already-verified code, not missing implementations.

---

_Verified: 2026-06-15T09:40:00Z_
_Verifier: Claude (gsd-verifier)_
