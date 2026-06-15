---
phase: 08-bug-fixes-data-correctness
reviewed: 2026-06-15T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - site/src/components/AdSlot.astro
  - site/src/components/PageHeader.astro
  - site/src/components/map/ResultPanel.tsx
  - site/src/config/i18n.ts
  - site/src/pages/crime/[family].astro
  - site/src/pages/es/delito/[family].astro
  - site/src/pages/es/delitos-por-comuna.astro
  - site/src/pages/es/region/[slug].astro
  - site/src/pages/region/[slug].astro
findings:
  critical: 1
  warning: 5
  info: 3
  total: 9
status: fixed
---

# Phase 8: Code Review Report

**Reviewed:** 2026-06-15
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Phase 08 introduced rollout-gating (F-005) to four ranking pages, a zero-JS hamburger
menu in `PageHeader.astro`, localized close-button labels in `ResultPanel.tsx`, and
text corrections in the ES editorial page. The bilingual close-label fix, the i18n
string additions, and the "commune→comuna" Spanish corrections are correct and complete.

However, the rollout-gating change introduced a **data-correctness regression** that is
exactly the class of bug this phase was meant to eliminate: on the two crime-family pages,
the displayed rank number (`#1`, `#2`, …) is now computed from the *filtered* display list
rather than the *full national* ranking. With rollout active, a commune that is genuinely
ranked #87 nationally will be presented to users as `#1`, mislabeling its standing. This
is a correctness defect on pages whose entire purpose is national ranking. Several
secondary inconsistencies (footnote shown without any matching markers, duplicated
filter loops doing O(n) `find` lookups) accompany it.

## Critical Issues

### CR-01: Rank number reflects filtered display list, not the true national ranking

**File:** `site/src/pages/crime/[family].astro:230-234` and `site/src/pages/es/delito/[family].astro:220-224`
**Issue:**
`rankingRows` is the full national ranking (all eligible communes sorted by rate desc, low-pop appended). Phase 08 added a `displayedRows` filter that keeps only rollout CUTs, then the table iterates `displayedRows` and prints the rank as `#${i + 1}` using the index into the *filtered* array:

```jsx
{displayedRows.map((row, i) => (
  ...
  <td class="col-num col-rank">
    {row.low_population ? '—' : `#${i + 1}`}
  </td>
```

Because the filter is applied *before* the index is read, the first rollout commune always shows `#1` even if it sits at national position #50. The page heading literally says "Communes ranked by … rate per 100,000 inhabitants" and emits Dataset JSON-LD describing a national ranking — so the displayed rank is factually wrong, not merely cosmetic. With only a handful of rollout CUTs enabled (the F-005 scenario), nearly every printed rank is incorrect.

Note this differs from the region pages, which delegate to `CommuneRankingTable` and print `row.national_rank` (a precomputed absolute rank) — so the region pages are correct and the crime pages are inconsistent with them.

**Fix:** Compute the true rank from position in `rankingRows` (eligible portion) before filtering, and carry it onto the row, e.g.:

```js
// assign absolute national rank to eligible rows during ranking build
let rankCounter = 0;
const rankedRows = rankingRows.map((row) => ({
  ...row,
  nationalRank: row.low_population ? null : ++rankCounter,
}));
const displayedRows = rankedRows.filter((row) => {
  const meta = index.find((c) => c.slug === row.slug);
  return meta ? rolloutCuts.has(meta.cut) : false;
});
```

```jsx
{displayedRows.map((row) => (
  ...
  <td class="col-num col-rank">
    {row.low_population ? '—' : `#${row.nationalRank}`}
  </td>
```

Apply identically to both EN and ES crime-family pages.

## Warnings

### WR-01: Low-population footnote rendered against `rankingRows` while table shows `displayedRows`

**File:** `site/src/pages/crime/[family].astro:251` and `site/src/pages/es/delito/[family].astro:241`
**Issue:**
The footnote that explains the `*` low-population marker is gated on the *unfiltered* list:

```jsx
{rankingRows.some((r) => r.low_population) && (
  <p class="low-pop-footnote">* This commune has a small resident population…</p>
)}
```

But the table only renders `displayedRows`. If no rollout-enabled commune is low-population (entirely possible during a small rollout), the footnote appears with no `*` marker anywhere in the visible table — a dangling explanatory note with no referent. Conversely the logic is internally inconsistent with the table's data source.

**Fix:** Gate the footnote on the displayed data: `{displayedRows.some((r) => r.low_population) && (...)}`. (The region pages already do this correctly inside `CommuneRankingTable`, which keys its footnote off the `rows` it actually renders.)

### WR-02: Hamburger checkbox marked `aria-hidden="true"` while remaining keyboard-focusable

**File:** `site/src/components/PageHeader.astro:42`
**Issue:**
```astro
<input type="checkbox" id="nav-toggle" class="nav-toggle-input" aria-hidden="true" />
```
`aria-hidden="true"` on a still-focusable interactive element is an accessibility anti-pattern: screen-reader users can tab into a control that AT is told to ignore, producing a focusable-but-unannounced element (axe rule `aria-hidden-focus`). The visual control is the `<label>` (which has the `aria-label`), so the checkbox should be removed from the tab order, not just hidden.

**Fix:** Add `tabindex="-1"` to the checkbox (it is `display:none` via CSS but `aria-hidden` + focusable is the flagged combination; the safest fix is to make it non-focusable):
```astro
<input type="checkbox" id="nav-toggle" class="nav-toggle-input" tabindex="-1" aria-hidden="true" />
```
Better still, expose state with `aria-expanded` on the label, but at minimum remove the focusable-yet-hidden contradiction.

### WR-03: Hamburger dropdown not dismissible by keyboard / no focus management

**File:** `site/src/components/PageHeader.astro:42-53, 193-205`
**Issue:**
The CSS-only menu toggles via a `<label>` pointer/Enter activation, but because the control is the hidden checkbox + label pattern, there is no `Escape`-to-close, the open menu is not announced (no `aria-expanded`/`aria-controls` linkage), and the `<label>` is the only operable element. On mobile this is the sole navigation affordance. This is a degraded-but-shippable interaction rather than a hard break, hence Warning.

**Fix:** Wire `aria-expanded` (requires a tiny bit of state or accept the CSS-only limitation and document it), add `aria-controls="…"` pointing at the `<nav>`, and consider that pure-CSL toggles cannot trap/return focus. If the D-09 "zero JS" constraint forbids scripting, document the known a11y limitation explicitly in the component header.

### WR-04: Rollout filter does O(n) `index.find` per row — and silently drops rows with no index match

**File:** `site/src/pages/crime/[family].astro:114-117`, `site/src/pages/es/delito/[family].astro:106-109`, `site/src/pages/region/[slug].astro:91-95`, `site/src/pages/es/region/[slug].astro:85-88`
**Issue:**
```js
const displayedRows = rankingRows.filter((row) => {
  const meta = index.find((c) => c.slug === row.slug);
  return meta ? rolloutCuts.has(meta.cut) : false;
});
```
The `false` branch silently discards any row whose `slug` is not found in `index`. Since `rankingRows` was itself built *from* `index`, a miss indicates a slug collision or data inconsistency that would now vanish without trace instead of surfacing. The slug→cut round-trip is also unnecessary: the rows already derive from index entries that have a `cut`. (Performance is out of scope, but the correctness concern — silent drop masking data bugs — is in scope.)

**Fix:** Carry `cut` onto each row when building `rankingRows`/`allRows` (the crime pages already iterate `meta.cut`), then filter directly: `rankingRows.filter((row) => rolloutCuts.has(row.cut))`. This removes the lossy lookup and the possibility of a slug mismatch silently hiding a commune.

### WR-05: `hiddenCount`/`rankingRows.length` disclosure can leak the full commune total during rollout

**File:** `site/src/pages/region/[slug].astro:214-215`, `site/src/pages/es/region/[slug].astro:202-203`, `site/src/pages/crime/[family].astro:256-257`, `site/src/pages/es/delito/[family].astro:246-247`
**Issue:**
```jsx
<p class="rollout-note">Showing {displayedRows.length} of {rankingRows.length} communes — more coming soon.</p>
```
This is likely intentional, but verify it is desired: the note publishes the exact full count (`rankingRows.length`) on every gated page even though only `displayedRows` are shown. If the rollout is meant to keep the eventual scope private, this exposes it. More concretely, on crime pages `rankingRows.length` includes low-pop rows while the hero says "{eligibleRows.length} communes ranked" — two different totals appear on the same page, which reads as inconsistent.

**Fix:** Confirm intent. If the "of N" should match the hero, use `eligibleRows.length`; if the disclosure of the full planned set is undesired, drop the denominator and say "more coming soon." Make the denominator consistent with the count cited elsewhere on the page.

## Info

### IN-01: `ResultPanel` level derivation is a per-commune self-normalization, not a real incidence level

**File:** `site/src/components/map/ResultPanel.tsx:184-190`
**Issue:**
`level` is derived from `rate / max(of this commune's own series)`. A commune always normalizes against itself, so its latest year frequently lands in level 4–5 regardless of how it compares nationally. The inline comment acknowledges this is "approximate." It is pre-existing (not changed in phase 08) but worth flagging since this phase targets data correctness: the colored "Nivel N" chip can misrepresent relative safety.
**Fix:** Derive `level` from the same national quintile thresholds used by the choropleth/map-payload rather than intra-series position, or relabel the chip to make clear it is a within-commune trend indicator.

### IN-02: `REGION_NAMES` duplicate-region pattern is fragile and partially redundant

**File:** `site/src/components/map/ResultPanel.tsx:78-96`
**Issue:**
`'56'` is hand-mapped to Valparaíso duplicating `'5'`, but the canonical mapping already exists in `regionFileId()` in `lib/data.ts` (which divides codes ≥17 by 10). This second, manually-maintained copy will drift if other sub-regional codes appear. Pre-existing, not phase-08.
**Fix:** Reuse `regionFileId()` to normalize `data.region_id` before lookup so only the 16 canonical entries are needed.

### IN-03: ES editorial page still mixes "comuna"/"commune" terminology in code identifiers vs prose

**File:** `site/src/pages/es/delitos-por-comuna.astro` (prose now corrected)
**Issue:**
Phase 08 correctly fixed the visible Spanish prose ("commune" → "comuna"). No further visible defects remain. Flagging only to confirm the fix was the intended scope and that no remaining user-facing "commune" strings exist in the ES tree (grep confirms the reviewed file is clean).
**Fix:** None required; recorded for traceability.

---

_Reviewed: 2026-06-15_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
