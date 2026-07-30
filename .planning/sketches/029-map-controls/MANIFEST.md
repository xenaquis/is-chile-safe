# Phase 29 — Map Control-Shell Design Loop: iteration manifest

Throwaway sketches. **Nothing here is ever deployed, imported, or referenced from a served route.** Phase 29 ships no map code; Phase 30 implements `29-DESIGN-SPEC.md` against the real components.

## Design direction

The baseline failure is not chip styling. It is that **one flat, horizontally-scrolling row is carrying five dimensions** — map mode, year, crime family, homicide layer and news layer — plus a search box and a locate button. `site/src/components/map/map.css:47-59` gives `.filters-row` `overflow-x: auto` and then suppresses its only affordance twice over (`scrollbar-width: none` plus a hidden `::-webkit-scrollbar`), so the row scrolls but nothing signals that it does. The news-layer toggle is the **last** chip in that row (`FiltersRow.tsx:112-119`), which puts it 590 px past the visible edge on a 1296 px desktop and ~855 px past it at 375 px. Half the product's value proposition — the qualitative news layer — is therefore unreachable unless the user guesses that an unmarked row scrolls sideways. See `29-BASELINE.md` §1–2.

The direction comes from `29-BASELINE.md` §3: every comparable product gives **each dimension its own persistent, labeled entry point** and keeps current filter state legible without opening anything. CrimeMapping's left rail (`SUMMARY / WHAT / WHERE / WHEN`) is the clearest instance — nothing is ever offscreen.

## How to read this table

Scores come from `score.mjs`, executed in a real browser via BrowserOS `evaluate_script`, once per frozen condition in `STRESS.md`. `check-iteration.mjs` gates the raw JSON: every blob must parse, carry its provenance fields, cover every declared condition, and — from iteration 2 on — prove structural distinctness from its predecessor. **Do not read a row of PASSes as quality**; read `STRESS.md`'s anti-theater rule first.

`mapWidthRatio` is recorded but **not gating** (F-43): full-bleed is out of scope, because achieving it means editing `map.css` layout rules that MAPSH-05 confines Phase 30 away from.

## Iteration matrix

| Iteration | c1 news toggle | c2 filters | c3 touch targets | c4 keyboard | c5 z-index / occlusion | Notes |
|---|---|---|---|---|---|---|
| **Baseline (iteration 0)** — the real `/map/`, measured 2026-07-30 | **FAIL** — `.ev-chip` at x=1370 on a 1296 px viewport; **not in viewport** at either width | **FAIL** — `.filters-row` overflows **507 px** desktop / **991 px** at 375 px, with `scrollbar-width:none` suppressing the only affordance | **PASS** — all chips 44 px; 0 violations | **PASS** by construction — 0 negative tabindex, 0 key interceptors in the map component tree (only `tabIndex={-1}` is a `display:none` aria sentinel, `MapIsland.tsx:500`) | **FAIL** — `.legend` at z **700**, tying `.leaflet-popup-pane` at 700 (order decided by DOM position); control coverage **24.7 %** of the map area (topbar 18.4 % + legend 6.3 %); `mapWidthRatio` **0.63** (812/1296) | The instrument returns FAIL against a real input — which is what proves it is not merely rubber-stamping prototypes built to pass |
| **iter-1** — news toggle lifted out of the scroll row (z 800); overflow affordance restored | **FAIL at 481px** — toggle rect x=404 w=183 on a 481 px viewport, i.e. **offscreen again** in the 480–639 band; PASS at 1296/639/375/320 | **FAIL** at `content-growth` (52 px), `breakpoint-639` (479 px) and `breakpoint-481` (**637 px — worse than the 507 px baseline**); PASS at 1296/375/320 | **FAIL** at every desktop-family width — the locate button `◎` is **32 × 32 px**; PASS at 375/320 | **PASS** everywhere — 0 negative tabindex, 0 key interceptors (F-41 by-construction standard) | **PASS** everywhere — `zIndexViolations: []`; coverage 13.4 % at 375 px (ceiling 25 %), 35.2 % desktop | `showModal()` proven real (`:modal` true, focus contained). Defect: `aria-expanded` never reset on close. Two conditions near-vacuous (sheet closed) |
| iter-2 | | | | | | |

Baseline figures are transcribed from `29-BASELINE.md` §1–2 and from the z-index/occlusion measurement taken in the same session. They are **not** marked "not measured": they were measured, and they are the only row in this table produced by an artifact that nobody designed to satisfy the rubric.

## Artifacts

- `STRESS.md` — the frozen adversarial conditions (written before iteration 1 existed)
- `score.mjs` — the rubric; also Phase 30's regression instrument, via the `data-role` hooks
- `check-iteration.mjs` · `check-astro.mjs` · `check-spec.mjs` — the gates
- `mobile-frame.html` — the narrow-viewport harness (HTTP only; `file://` is an opaque origin)
- `iter-N/` — `desktop.html`, `mobile-375.html`, both PNGs, `SCORE.md`
