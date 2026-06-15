---
phase: 08-bug-fixes-data-correctness
fixed_at: 2026-06-15T09:24:31Z
review_path: .planning/phases/08-bug-fixes-data-correctness/08-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 5
skipped: 1
tests_passed: true
test_command: cd site && npm run build
status: all_fixed
---

# Phase 8: Code Review Fix Report

**Fixed at:** 2026-06-15T09:24:31Z
**Source review:** .planning/phases/08-bug-fixes-data-correctness/08-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6 (CR-01, WR-01, WR-02, WR-03, WR-04, WR-05)
- Fixed: 5 (CR-01, WR-01, WR-02, WR-04, WR-05)
- Skipped: 1 (WR-03 — out of scope per task instructions)
- Test gate: PASSED (`cd site && npm run build` — 100 pages, 0 errors)

## Test Gate

- PASSED — `cd site && npm run build` exited 0 after all fixes. 100 pages built in 27.6s, 0 errors.

## Fixed Issues

### CR-01: Rank number reflects filtered display list, not the true national ranking

**Files modified:** `site/src/pages/crime/[family].astro`, `site/src/pages/es/delito/[family].astro`
**Commit:** 1754afe
**Applied fix:** Added `nationalRank: number | null` field to `RankRow` type. Assigned stable national rank via an incrementing counter over `eligibleRows` (the full eligible list, before rollout filtering), and `null` for low-population rows. After filtering to `displayedRows`, the table renders `row.nationalRank` instead of the filtered loop index `i+1`. A commune at national position #87 now correctly shows `#87` instead of `#1`.

### WR-01: Low-population footnote rendered against `rankingRows` while table shows `displayedRows`

**Files modified:** `site/src/pages/crime/[family].astro`, `site/src/pages/es/delito/[family].astro`
**Commit:** 1754afe
**Applied fix:** Changed `rankingRows.some((r) => r.low_population)` to `displayedRows.some((r) => r.low_population)` on both EN and ES crime pages. The footnote now only appears when a `*` marker is actually visible in the table.

### WR-02: Hamburger checkbox marked `aria-hidden="true"` while remaining keyboard-focusable

**Files modified:** `site/src/components/PageHeader.astro`
**Commit:** 17b654f
**Applied fix:** Added `tabindex="-1"` to the `<input type="checkbox" id="nav-toggle">` element. The checkbox is now removed from the tab order, resolving the axe `aria-hidden-focus` violation. The zero-JS `:checked` CSS toggle and desktop layout are unaffected.

### WR-04: Rollout filter does O(n) `index.find` per row and silently drops unmatched rows

**Files modified:** `site/src/pages/crime/[family].astro`, `site/src/pages/es/delito/[family].astro`
**Commit:** 1754afe
**Applied fix:** Added `cut: string` field to `RankRow` type and populated it from `meta.cut` during the `allRows` build loop. The rollout filter now reads `rolloutCuts.has(row.cut)` directly, eliminating the lossy `index.find((c) => c.slug === row.slug)` lookup that would silently drop rows with no slug match.

### WR-05: `hiddenCount`/`rankingRows.length` disclosure inconsistent with hero commune count

**Files modified:** `site/src/pages/crime/[family].astro`, `site/src/pages/es/delito/[family].astro`
**Commit:** 1754afe
**Applied fix:** Changed the rollout-note denominator from `rankingRows.length` (which includes low-population rows) to `eligibleRows.length` (the count already shown in the hero as "{N} communes ranked"). The two counts on the page now agree. Region pages were verified to be consistent already (`communeCount === rankingRows.length` in that context) and were not changed.

## Skipped Issues

### WR-03: Hamburger dropdown not dismissible by keyboard / no focus management

**File:** `site/src/components/PageHeader.astro:42-53, 193-205`
**Reason:** Out of scope per task instructions — only CR-01, WR-01, WR-02, WR-04, WR-05 were in scope for this fix pass. WR-03 requires either a JS solution (violating D-09 zero-JS constraint) or a documented known limitation, which is a design decision beyond a mechanical fix.
**Original issue:** CSS-only hamburger has no Escape-to-close, no aria-expanded/aria-controls linkage, and no focus management on mobile.

---

_Fixed: 2026-06-15T09:24:31Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
