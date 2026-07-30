# Phase 29 — Accepted Map Control-Shell Design Spec

**Status**: accepted by Fable-proxy on independently-reviewed evidence (MAPUX-05). Human review **deferred, not waived**.
**Implements**: MAPUX-01..05. **Consumed by**: Phase 30 (Map Control-Shell Rework).
**Evidence**: `29-BASELINE.md`, `.planning/sketches/029-map-controls/` (`STRESS.md`, `MANIFEST.md`, `iter-1/`, `iter-2/`, `score.mjs`), `29-UI-CHECK.md`.

Phase 30 is a declared regression-risk phase working against protected Leaflet layer files. **This spec pins values so Phase 30 implements rather than decides.** Where it does not pin something, that is stated explicitly as an out-of-scope non-decision.

---

## 0. The problem, in numbers

The baseline failure is not chip styling: **one flat, horizontally-scrolling row carries five dimensions** (mode, year, crime family, homicide layer, news layer) plus search and locate. `map.css:47-59` gives `.filters-row` `overflow-x:auto` then suppresses its only affordance twice (`scrollbar-width:none` + hidden `::-webkit-scrollbar`).

| Measured on the real `/map/` | Desktop 1296 px | 375 px |
|---|---|---|
| `.filters-row` hidden overflow | **507 px** | **991 px** |
| News toggle (`.ev-chip`) position | x = 1370 — ~590 px offscreen | ~855 px offscreen |
| Control coverage of map area | **26.2 %** (instrument); 24.7 % by hand (topbar 18.4 + legend 6.3) | — |
| `.legend` z-index | **700 — ties `.leaflet-popup-pane`** | — |
| `mapWidthRatio` | **0.627** (812/1296) | — |

Half the product's value — the qualitative news layer — is unreachable unless the user guesses that an unmarked row scrolls sideways.

**Every figure above was reproduced by running `score.mjs` unchanged against the real `/map/`** (`http://127.0.0.1:4321/es/mapa/`), which returns:

```
c1 FAIL (newsToggleDiscoverable false, rect x=1370)   c2 FAIL (filterOverflowPx 507, scrollbarSuppressed true)
c3 FAIL (touchTargetViolations 20)                    c4 PASS (negativeTabindexCount 0, keyInterceptors [])
c5 FAIL (zIndexViolations ["legend=700"])             controlCoveragePct 26.2   mapWidthRatio 0.627
```

**Four of five criteria return FAIL against the real application, and the fifth correctly returns PASS.** That is the evidence that this rubric is a real instrument rather than a rubber stamp for prototypes built to satisfy it — and it is a live demonstration that §8's hooks let Phase 30 reuse it as-is.

## 1. Loop history (read this before judging the iteration count)

`ROADMAP.md:371` defines an iteration as screenshot → redesign → apply → re-screenshot. Iteration 1's "before" is **the measured baseline of the real artifact**, not a prior sketch — a stronger prior state than a sketch of a sketch. The chain **baseline → iter-1 → iter-2** therefore contains **two complete redesign→re-measure transitions**, which is what MAPUX-02's "at least two full iterations" protects. No cycle was skipped.

Iteration 1 was not a rubber stamp: the eight conditions frozen in `STRESS.md` *before it was designed* broke it three ways — the news toggle went offscreen again at 481 px, the row overflowed **637 px** there (worse than the 507 px baseline), and a 32 × 32 px locate button failed WCAG 2.5.5. Iteration 2 moved **8 criterion × condition cells FAIL→PASS with none regressing** (an earlier draft said 9 — miscounted). `check-iteration.mjs` was demonstrated to reject a copied iteration, so the claim "two real iterations happened" is gated, not narrated.

## 2. The accepted design

**Adopted: iteration 2 wholesale**, which already carries iteration 1's news-toggle placement and dialog mechanics. Rendered as React elements inside `MapTopbar.tsx` and sibling components — **not** a Leaflet `L.control()` (29-RESEARCH.md Open Question 1; keeps MAPSH-05's confinement meaningful).

1. **The flat scrolling filter row is deleted.** Filters become three separately-labeled, always-visible entry points — `Año`, `Tipo de delito`, `Modo` — each a native `<details>` with its own panel. No control is a scroll container. Source: **CrimeMapping finding 1** (`29-BASELINE.md` §3).
2. **The news-layer toggle is a standalone persistent control** in the topbar's first row, never inside a filter surface and never inside a scroll container. **It must never be hidden inside the filter dialog** — that would re-create the exact bug this phase exists to fix.
3. **Below 480 px** the three entry points collapse into a single bottom-sheet `<dialog>` opened with a real `showModal()`, reached from a FAB — **not** nested in the hamburger nav (MAPSH-02).
4. **A persistent state summary** (`Índice · Todos los delitos · 2025`) keeps the active selection legible without opening any panel. Source: **CrimeMapping finding 3**.

## 3. Pinned z-index assignments

Placed in the real ladder — 700 `legend`/`result-panel`/`zoom-ctl` · 800 `map-topbar`/`partial-year-badge` · 801 `mode-toggle` · 900 `search-dropdown`/`map-error-overlay` · 1000 `toast` · Leaflet panes 200–700, controls 800, corners 1000.

| Control | z-index | Note |
|---|---|---|
| `.map-topbar` | **800** | unchanged |
| news toggle (`[data-role="news-toggle"]`) | **800** | explicit number, **never `auto`** |
| entry points (`[data-role="entry-point"]`) | inherit `.map-topbar`'s context | `auto` is acceptable **only** because a control ancestor carries an explicit ≥ 700 |
| entry panel (open `<details>` popover) | **801** | must clear `.map-topbar` siblings |
| filter FAB (≤ 480 px) | **800** | set on the base rule, not only inside the media query — otherwise it computes to `auto` at wider widths |
| filter bottom sheet | **none** | modal `<dialog>` renders in the browser top layer; giving it a z-index is wrong |

**Rule**: a non-modal always-visible control needs an explicit numeric z-index ≥ 800. `z-index: auto` is a defect **unless** an ancestor control carries an explicit ≥ 700 — its paint order is otherwise DOM-order dependent and will not survive the real 970-line `map.css`.

**Also fix**: `.legend` currently sits at **700, tying `.leaflet-popup-pane`**, so a Leaflet popup and the legend are ordered only by DOM position. Phase 30 should raise `.legend` clear of the popup pane.

## 4. The four real breakpoint bands

Not "desktop and mobile" — the bands `map.css:192/210/240/271/463` actually switch on. **The real rules are `max-width:480px` and `max-width:640px`, which are inclusive**, so the bands are ≤ 480 / 481–639 / 640–1023 / ≥ 1024. An earlier draft wrote "< 480 / 480–639", which is off by one and contradicted `STRESS.md`'s own `breakpoint-481` condition. **One responsive implementation**, not viewport-specific variants: iteration 1's split-file approach was measured unable to answer breakpoint questions at all.

| Band | Shell |
|---|---|
| **≤ 480** | Topbar = search + news toggle (short label `Noticias`). Entry points hidden; filter FAB + `<dialog>` bottom sheet. **`.result-panel` and the FAB collide — see §4a, this is a required decision, not an omission.** `.legend-mobile` stays a `<details>`. |
| **481 – 639** | Grouped entry points visible inline. News toggle keeps the short label. `.zoom-ctl` still hidden (appears ≥ 640). |
| **640 – 1023** | Full labels (`Noticias recientes`). `.zoom-ctl` appears bottom-right. `.result-panel` becomes the right-hand 380 px panel. |
| **≥ 1024** | As above, with the state summary inline. |

`.mode-toggle`'s `position:static` reset at ≤ 480 (`map.css:240-251`) **is not a usable precedent for the news toggle** — the toggle carries its own explicit z-index at every band, because that reset drops the element out of the stacking context exactly where the toggle must stay pinned.

## 4a. The FAB × `.result-panel` collision (REQUIRED — do not leave to implementation)

At ≤ 640 px `.result-panel` becomes a bottom sheet occupying the lower **40vh** (`map.css:450-480`). The filter FAB sits at `right:16px; bottom:24px`. **They occupy the same space whenever a commune is selected.** Iteration 1 flagged this; the scored sketch sidestepped it by setting `.result-panel { display:none }` below 480 px, which is a sketch convenience and **not** acceptable behaviour in the real app, where selecting a commune is the primary interaction.

**Decision for Phase 30**: the FAB is anchored **above** the result panel rather than hidden by it — when `.result-panel` is open at ≤ 640 px, the FAB's `bottom` becomes `calc(40vh + 16px)`, animating with the sheet. The FAB must never be occluded and must never overlap the sheet's own controls. Verify with the rubric's `elementFromPoint` topmost check on `[data-role="filter-entry"]` **with a commune selected**, which is a state the Phase 29 sketches never modelled.

## 5. Element semantics (determines React state shape — cannot be inferred from a screenshot)

| Control | Element | State |
|---|---|---|
| News layer toggle | `<button aria-pressed>` | boolean `showEvents` |
| Entry point (each dimension) | `<details>` + `<summary>` | native `open`; **one panel open at a time**, enforced on the `toggle` event |
| Option inside a panel | `<button role="radio" aria-checked>` inside a container with **`role="radiogroup"`** | single-select per dimension. The sketch used `role="group"`, which is **invalid** as a parent for `role="radio"` — Phase 30 must ship `radiogroup` |
| Mobile filter sheet | `<dialog>` + **`showModal()`** | native top layer |
| Legend | `<details>` at ≤ 480 (existing) | unchanged |

**`showModal()` is mandatory, not `<dialog open>`.** Only `showModal()` gives native focus containment, ESC and a backdrop — satisfying MAPSH-02's zero-new-JS-dependency constraint and the WCAG keyboard requirement together. **Verify with `dialog.matches(':modal') === true`**; `grep -c "showModal"` cannot distinguish the two.

## 6. Focus order and ARIA

DOM order: skip-link → header nav → search input → locate button → **news toggle** → `Año` → `Tipo de delito` → `Modo` → state summary → map → legend → zoom.

- `<dialog>` close returns focus to the invoking control. **Set `aria-expanded="false"` where the close is *initiated* as well as on the `close` event** — iteration 1 relied on the `close` event alone and it never fired (`closeEventsFired: 0`), leaving screen-reader users told the sheet was still open.
- News toggle: `aria-pressed` + `aria-label` (`Mostrar incidentes recientes de prensa en el mapa`).
- Each entry point's `<summary>`: `aria-expanded` + `aria-controls`, driven by the native `toggle` event.
- Dialog: `aria-labelledby` pointing at its title.
- **Dismissal for the `<details>` entry panels** (unspecified in the sketch, required here): Escape closes the open panel and returns focus to its `<summary>`; a click or focus outside the open `<details>` closes it; opening one panel closes any other (enforced on the native `toggle` event). These are non-modal popovers, so they must NOT trap focus — that is the `<dialog>`'s job at ≤ 480 px.
- **State summary is an `aria-live="polite"` region.** `/news/` already ships this precedent (`#news-result-count`, verified in F-41), and CrimeMapping findings 3–4 argue for it.

## 7. Labels — EN and ES, with the longest-string consequence

| Key | ES | EN |
|---|---|---|
| `map_entry_year` | Año | Year |
| `map_entry_family` | Tipo de delito | Crime type |
| `map_entry_mode` | Modo | Map mode |
| `map_news_toggle_long` | Noticias recientes | Recent incidents |
| `map_news_toggle_short` | Noticias | News |
| `map_filters_fab` | Filtros | Filters |

**The news toggle's label must remain visible at every width** — shorten it, never remove it (MAPSH-01: an always-visible **labeled** toggle). The first build of iteration 2 hid it below 640 px, leaving a bare orange dot that the rubric scored PASS and no sighted first-time user could identify. Longest real ES label (`Robos con violencia o intimidación`) and 150 % root text were both verified to produce **0 px overflow**.

## 8. `data-role` hooks Phase 30 must ship into the real DOM

`data-role="news-toggle"` · `data-role="filter-entry"` (on **both** the grouped rail and the FAB) · `data-role="entry-point"` (each dimension).

**This is load-bearing, not cosmetic**: it lets `.planning/sketches/029-map-controls/score.mjs` run **unchanged** against the real `/map/` as Phase 30's MAPSH-06 regression instrument. Without these hooks the rubric dies with the sketch and Phase 30 has no acceptance instrument.

## 9. MAPSH decision table

| Req | Decision | Source |
|---|---|---|
| **MAPSH-01** | Standalone always-visible **labeled** news toggle, topbar row 1, z-index 800, label shortened not hidden below 640 px | iter-1 §2 + iter-2 finding 1 |
| **MAPSH-02** | Native `<details>` entry points + `<dialog>`/`showModal()` bottom sheet ≤ 480 px via FAB, never in the hamburger nav. Zero new JS dependencies | iter-2; MAPSH-02 |
| **MAPSH-03** | All targets ≥ 44 px (incl. the locate button, raised from 32 px); keyboard-trap-free by construction — no `keydown`/`keyup`/`preventDefault` interceptors, no negative tabindex; `zIndexViolations: []` | iter-2 scores |
| **MAPSH-04** | **OUT OF SCOPE for this spec** — `?region=` deep link is Phase 30's own decision (29-RESEARCH.md OQ3) | — |
| **MAPSH-05** | Changes confined to `MapTopbar.tsx` + sibling control components. `ChoroplethLayer.ts` / `IncidentPinLayer.ts` / `LowZoomDotLayer.ts` untouched. No declarative react-leaflet layer component | ROADMAP |
| **MAPSH-06** | **OUT OF SCOPE for this spec** — regression verification is Phase 30's job; it should use `score.mjs` via the §8 hooks | — |
| **MAPSH-07** | Shared vocabulary with news facets **via data, not a code dependency**. See the trap in §10 | Phase 28 Outcome N1 |

## 9a. Component scope — two things MAPSH-05 does not resolve on its own

**`FiltersRow.tsx` is DELETED, not refactored.** Its chip row is the defect. `MapTopbar.tsx` renders the grouped entry points directly. This matters beyond tidiness: `score.mjs` falls back to `.ev-chip` and `.filters-row` when no `data-role` hook is found, so if the legacy classes survive anywhere, **Phase 30's own instrument would silently bind to the old markup and report on the wrong elements**. Phase 30 must assert `.filters-row` and `.ev-chip` no longer exist in `dist/`.

**Folding `Modo` into an entry point requires editing `MapIsland.tsx`, which MAPSH-05's in-scope list does not name.** `MapTopbar.tsx:19-20` receives the mode toggle as a `modeToggle` **prop** constructed by its parent (`MapIsland.tsx:440-460`), so the grouping cannot be done inside `MapTopbar.tsx` alone. Two admissible resolutions — **Phase 30 must pick one and record it, not discover it mid-implementation**:

- **(a) Preferred.** Authorize a **narrowly-scoped** `MapIsland.tsx` edit: move the mode-toggle markup into `MapTopbar.tsx` and pass `mode` / `onModeChange` as plain props. MAPSH-05's intent is protecting the **Leaflet layer files** (`ChoroplethLayer.ts`, `IncidentPinLayer.ts`, `LowZoomDotLayer.ts`), not freezing the island's prop wiring. The code review's MAPSH-05 check should read "confined to `MapTopbar.tsx`, sibling control components, **and the mode-toggle prop wiring in `MapIsland.tsx`**".
- **(b) Fallback.** Leave the mode toggle exactly as it is (its own control, its own `modeToggle` prop) and ship only `Año` and `Tipo de delito` as entry points. This is strictly less good — `Modo` stays a separate ungrouped control — but it is fully within MAPSH-05 as written.

## 10. Explicit non-decisions and traps

- **`?region=` means different things on the two surfaces.** On `/news/` it is **CSV multi-value**; on the map it is **single-value focus**. **Phase 30 must NOT reuse `parseFilterParams`** (Phase 28 Outcome N1). Every filter dimension this spec introduces is **single-select**, matching the map's existing semantics and diverging deliberately from `/news/`.
- **Full-bleed map is OUT of scope (F-43).** `mapWidthRatio` 0.63 is recorded as a finding and measured every run, but is **not gating**. Achieving it means editing `.map-stage`/`.map-canvas` layout in `map.css`, which collides with MAPSH-05's confinement of Phase 30 to control components. The phase's failure is discoverability, not framing.
- **Control coverage carried, not resolved.** The accepted design measures **22.7 %** at 375 px, within the pre-registered ≤ 25 % ceiling — but **32.2 % at 320 px and 43.1 % at 481 px**. `STRESS.md` scoped the ceiling to 375 px and its freeze rule forbids loosening it after the fact, so this is recorded as a **Phase 30 constraint**: keep coverage at or below the 375 px figure and treat the narrower bands as a known weakness to improve, not a passed test.
- **Criterion 1 tests presence and stacking, not legibility.** A criterion-1 PASS is not proof the control is understandable — that gap is exactly what produced the unlabeled-dot defect. Phase 30 must not read it as such.
- **Criteria 1 and 2 are not meaningful while a modal is open** (`elementFromPoint` correctly returns the backdrop). Score them with the sheet closed.

## 11. ⚠ Phase 30 driving warning (F-40)

**Always drive `http://127.0.0.1:4321/es/mapa/`. Never `/map/`.**

`BaseLayout.astro:116-131` redirects es-locale browsers on EN pages to `esLink.href`, which is an **absolute production URL** (built from `BASE_URL`, lines 72-74). On localhost this bounces the tab to `https://ischilesafe.com` — it happened during this phase's setup, silently substituting production for the build under test. **The next agent to open `/map/` locally will measure production and not know it.**

**Phase 30 Wave 0 must fix it** (one line: take `new URL(esLink.href).pathname + search + hash` and keep the current origin). It is barred from Phase 29 because the fix touches `site/`, which this phase's hard gate forbids.

## 12. The bar Phase 30 must reproduce in real code

| Criterion | Required |
|---|---|
| c1 news toggle discoverable | PASS at 320 / 375 / 481 / 639 / 1296, with a **visible label** at each |
| c2 filters discoverable, no hidden overflow | PASS, `filterOverflowPx === 0`, including with a 9th family and a 4th dimension |
| c3 touch targets | `touchTargetViolations === 0` at 320 and 375 |
| c4 keyboard | `negativeTabindexCount === 0`, `keyInterceptors === []` |
| c5 z-index | `zIndexViolations === []`; coverage ≤ 22.7 % at 375 px |
| modal | `dialog.matches(':modal') === true`; focus returns to invoker; `aria-expanded` correct after close |

Reproduce these by running `score.mjs` unchanged against the real `/map/` — that is what §8's hooks are for.
