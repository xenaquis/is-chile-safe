---
phase: 30-map-control-shell-rework
plan: 04
subsystem: map-control-shell
tags: [mobile, dialog, fab, filter-sheet]
dependency-graph:
  requires: [FilterFields.tsx (30-02), .map-stage.has-panel (MapIsland.tsx:413, pre-existing)]
  provides: [FilterSheet.tsx (unwired — Plan 30-05 wires it into MapTopbar)]
  affects: [site/src/components/map/map.css]
tech-stack:
  added: []
  patterns: ["native <dialog> + showModal() for mobile modal sheets", "aria-expanded set via setAttribute at 3 independent sites (click, close-click, dialog 'close' event)"]
key-files:
  created:
    - site/src/components/map/FilterSheet.tsx
  modified:
    - site/src/components/map/map.css
decisions: []
metrics:
  duration: "~15 min"
  completed: 2026-07-30
---

# Phase 30 Plan 04: Mobile Filter FAB + Native Dialog Sheet Summary

Built the mobile (<=480px) filter entry point as a FAB that opens a native `<dialog>` bottom sheet via `showModal()`, containing the three FilterFields dimensions (Year/Family/Mode) flat, with the FAB-vs-result-panel collision resolved CSS-only via the pre-existing `.map-stage.has-panel` hook.

## What Was Built

- **`FilterSheet.tsx`** (new): Exports `FilterSheet(props)` with the same filter prop shape as `EntryPointsRail`. Renders a `<button data-role="filter-entry" className="filter-fab">` and a `<dialog id="filter-sheet">` containing a header (title + close button) and the three `FilterFields` components (`YearField`, `FamilyField`, `ModeField`) rendered flat, no `<details>` wrapper.
  - FAB click → `dialogRef.current.showModal()` (never the `open` attribute) + `fabRef.current.setAttribute('aria-expanded', 'true')`.
  - Close-button click → `dialog.close()` + `setAttribute('aria-expanded', 'false')` + `fab.focus()`.
  - Dialog native `'close'` event (fires on Escape/backdrop too) → `setAttribute('aria-expanded', 'false')`, wired independently of the close-button handler.
  - All three listeners attached/cleaned up in a single mount-time `useEffect`.
- **`map.css`** additions (appended at end of file, after the Phase 18-04 composite-index block):
  - `.filter-fab` base rule with `z-index: 800` set outside any media query; `display: none` by default, shown via `@media (max-width: 480px)` (min 44x44 target, MAPSH-03).
  - `@media (max-width: 640px) { .map-stage.has-panel .filter-fab { bottom: calc(40vh + 16px); } }` — CSS-only collision fix against the pre-existing `.map-stage.has-panel` class (`MapIsland.tsx:413`), zero new JS/state/props.
  - `.filter-sheet` (the `<dialog>` itself) styling with no `z-index` rule — relies on the browser top layer from `showModal()`.
  - Supporting `.filter-sheet-header`, `.filter-sheet-close`, `.filter-sheet-body`, `.filter-sheet-field-label` rules.

Not yet wired into `MapTopbar.tsx` — deferred to Plan 30-05 per plan's success criteria. This plan's diff is additive-only.

## Verification

**`<automated>` gate** (run exactly as written in the plan): **PASSED, exit code 0.**
```
PASS FilterSheet contract + CSS present
EXIT CODE: 0
```
All 9 assertions passed: `showModal(` present, no `open` attribute on `<dialog>`, `'close'` event listener present, `aria-expanded` set via `setAttribute` at 3 distinct sites, `.focus()` present in close handler, `data-role="filter-entry"` on FAB, `.filter-fab` base z-index 800, `.has-panel .filter-fab` collision rule present, no z-index rule on `#filter-sheet`.

**`cd site && npm run build && npm test`** (chained in one command per OneDrive constraint): **PASSED, exit code 0.**
- Build: 834 pages built in 27.30s, no errors.
- Vitest: 5 test files passed, **45 tests passed** (matches the plan's expected baseline — `FilterSheet` is not yet imported anywhere, so no new test files were expected or added by this plan).

## Deviations from Plan

None — plan executed exactly as written. `FilterSheet.tsx` was created and `map.css` extended per the task's `<action>` block; no files outside `files_modified` were touched; no commit was made per instructions.

## Known Stubs

None. `FilterSheet.tsx` is fully functional in isolation (FAB, dialog mechanics, focus return, collision CSS) but is intentionally unwired into `MapTopbar.tsx` — this is the plan's own documented scope boundary (Plan 30-05), not a stub.

## Threat Flags

None. No new network endpoints, auth paths, or trust-boundary changes — client-side UI state only, matching the plan's threat model (T-30-04, accepted disposition).

## Self-Check: PASSED

- `site/src/components/map/FilterSheet.tsx` — FOUND
- `site/src/components/map/map.css` — FOUND, contains `.filter-fab`, `.has-panel .filter-fab`, `.filter-sheet` additions
- Automated gate — re-run, exit code 0
- `npm run build && npm test` — re-run, exit code 0, 45/45 tests passed
