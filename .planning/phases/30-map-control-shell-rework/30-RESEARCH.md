# Phase 30: Map Control-Shell Rework — Research

**Researched:** 2026-07-30
**Domain:** React island DOM restructuring (native `<details>`/`<dialog>`) against a protected Leaflet map, zero new JS dependencies
**Confidence:** HIGH (the codebase itself is the primary source; every claim below is `file:line` verified against the real tree, not inferred)

## Summary

Phase 30 implements `29-DESIGN-SPEC.md` (BINDING, do not redesign) inside `site/src/components/map/`. The current shell is `MapTopbar.tsx` (`site/src/components/map/MapTopbar.tsx:1-60`) composing `SearchBox` + `FiltersRow`, with `MapIsland.tsx` constructing a `modeToggle` React node (`MapIsland.tsx:439-472`) and passing it as a prop consumed at `MapTopbar.tsx:19-20,47`. `FiltersRow.tsx` (`site/src/components/map/FiltersRow.tsx:1-123`) is the single flat `.filters-row` scroll container that must be **deleted**, not refactored, and has exactly one consumer (`MapTopbar.tsx:6,49-57` — confirmed via `grep -rn FiltersRow site/src`).

There is no `site/src/lib/i18n.ts`. The project's actual i18n string map lives at `site/src/config/i18n.ts` (`EN_STRINGS`/`ES_STRINGS`, interface `I18nStrings`), and both `Legend.tsx:11` and `ResultPanel.tsx:21` already import from `'../../config/i18n'`. **The six new label keys in spec §7 must be added to `site/src/config/i18n.ts`, not a nonexistent `lib/i18n.ts`.** `FiltersRow.tsx` and the current `MapTopbar`/`MapIsland` inline their ES/EN strings directly as ternaries rather than using the central i18n map, which is the existing local convention for map-island-only strings (not a defect to fix in this phase — MAPSH-05 confines scope).

No map-island-specific automated test exists today. The 37 vitest tests are all pure-logic (`site/src/lib/formatNumber.test.ts`, `newsFacets.test.ts`, `newsFilterLogic.test.ts`) — nothing DOM-heavy for `MapIsland.tsx`/`MapTopbar.tsx`. This phase's automated evidence is therefore `score.mjs` run in a real browser (BrowserOS, inline in the orchestrator) plus `dist/`-scanning `grep`/`node` checks the orchestrator can run directly — not new vitest specs, except a possible pure-function test for a `parseRegionParam`-style helper if it is extracted as its own module (parallel to `parseFilterParams`, which explicitly must **not** be reused per F-48/N1).

**Primary recommendation:** Implement F-47's option (a) exactly as pinned — fold the mode toggle's markup into `MapTopbar.tsx`, passing `mode`/`onModeChange` as plain props from `MapIsland.tsx`; ship the sketch's iter-2 markup (`.planning/sketches/029-map-controls/iter-2/desktop.html`) as the real React structure with `data-role` hooks intact; add a small `<details>` "one-open, Escape-closes, click-outside-closes" controller as sibling-component-local JS (not global `keydown` on `document` unconditionally — see Q2); implement `?region=` with its own guarded parser mirroring the existing `?cut=` pattern at `MapIsland.tsx:226-232`; and settle criterion 4 per F-49's three-part evidence chain rather than editing `score.mjs`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Filter entry points (Año/Tipo de delito/Modo) | Browser / Client (React island) | — | Client-only React component tree (`client:only="react"`, `map.astro:34`); no SSR involvement per D-06 |
| News-layer toggle | Browser / Client | — | Existing `showEvents` state lives in `MapIsland.tsx:106`; purely client-rendered |
| `?region=`/`?cut=` deep-link parsing | Browser / Client | — | Read from `window.location.search` inside a `useEffect`, same as the existing `?cut=` handling (`MapIsland.tsx:226-232`); no server involved (client:only page) |
| Mobile bottom-sheet dialog | Browser / Client | — | Native `<dialog>` + `showModal()`; zero new dependency (MAPSH-02) |
| Choropleth/pin/dot rendering | Browser / Client (protected) | — | `ChoroplethLayer.ts`/`IncidentPinLayer.ts`/`LowZoomDotLayer.ts` — byte-identical gate (F-47); Phase 30 must not touch |
| Shared filter vocabulary (family/region labels) | Static data / Build-time | Browser / Client | `familyDefs.ts`/`data.ts` are imported by both map island and news pages at build+runtime; MAPSH-07 forbids a *code* dependency between the two page trees, not shared imports of the same data module |
| Runtime map data (topojson, payload, index) | CDN / Static (public/data) | Browser / Client (fetch) | `safeFetch` hits hardcoded same-origin `/data/cead/*` paths (`MapIsland.tsx:66-74,170-173`) — this phase adds no new fetch surface |

## User Constraints

This phase has no `CONTEXT.md` (no `/gsd:discuss-phase` was run for Phase 30 as of this research). The binding constraints instead come from `30-FABLE-CONSTRAINTS.md` (F-47..F-50) and `29-DESIGN-SPEC.md`, both already fully read and folded into every section below. Treat every numbered item in `30-FABLE-CONSTRAINTS.md` as if it were a locked `## Decisions` entry — it is orchestrator-pre-decided and this research does not re-litigate it.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MAPSH-01 | Always-visible labeled news toggle, not buried in a mode control | §12 of spec is reproducible against real `/es/mapa/`; `MapIsland.tsx:106,431-432` already owns `showEvents` state — only the rendering (`MapTopbar`/sibling) changes |
| MAPSH-02 | `<details>`/`<dialog>` filter panel, bottom-sheet/FAB on mobile, zero new JS deps | iter-2 sketch (`iter-2/desktop.html:145-235`) is the real markup to port; dialog JS pattern at `iter-2/desktop.html:237-273` |
| MAPSH-03 | Keyboard/touch/z-index compliance | Spec §3 pins the z-index ladder; §5-6 pin ARIA; `score.mjs` (`.planning/sketches/029-map-controls/score.mjs`) is the instrument |
| MAPSH-04 | `?region=` deep link, single-value, own parser | `MapIsland.tsx:226-232` (`?cut=`) is the pattern to mirror; `region_id` is a string field already present in `CommuneIndexEntry` (`SearchBox.tsx:20-25`) and in `data/cead/meta/index.json` |
| MAPSH-05 | Changes confined to `MapTopbar.tsx` + siblings + narrowly-scoped `MapIsland.tsx` mode-toggle wiring | F-47 pins this; `MapIsland.tsx:439-472` is the exact block to move |
| MAPSH-06 | Regression-verify existing map behavior | `score.mjs` + a manual full-behavior pass (see Q5/Q6) |
| MAPSH-07 | Shared vocabulary via data, not code dependency | `familyDefs.ts` already the single source used by both `FiltersRow.tsx:18` and the news pages (verify no map-island import path reaches into `site/src/pages/news.astro` or vice versa) |

## Standard Stack

No new packages. MAPSH-02 explicitly forbids new shipped JS dependencies; native `<details>`/`<summary>`/`<dialog>` + `showModal()` are used, both already supported by the project's target browsers (this is a client-only React 19 + Leaflet 1.9 island — see project CLAUDE.md stack table, unchanged by this phase).

### Package Legitimacy Audit

Not applicable — this phase installs zero packages. `package.json`/`package-lock.json` remain untouched; the gate check for this phase is `git diff --exit-code -- site/package.json site/package-lock.json` (should be clean, or explicitly empty diff).

## Architecture Patterns

### System Architecture Diagram

```
window.location.search (?cut=, ?region=)
        │
        ▼
MapIsland.tsx useEffect (mapReady gate)
        │  parses ?cut= (existing, regex-guarded)      ─┐  BOTH must run before
        │  parses ?region= (NEW, own guard, F-48)       ─┘  any fetch — silent no-op on bad input
        │
        ├──> selectCommune(cut)  [existing, unchanged]
        └──> focusRegion(region_id) [NEW] ─> fitBounds over all polygons whose
                                             communeIndex entry has that region_id
        │
        ▼
React state (year, crimeFamily, crimeIsHomicide, mode, showEvents, selected)
        │
        ▼
MapTopbar.tsx (topbar row 1: search + news toggle)
        │
        ├─ SearchBox.tsx (unchanged)
        ├─ NewsToggle (NEW, replaces modeToggle's old position — persistent, labeled)
        └─ EntryPointsRail (NEW, replaces FiltersRow) ── one <details> per dimension
                 │        (Año / Tipo de delito / Modo)
                 │        + FilterFAB + <dialog> bottom sheet at ≤480px
                 ▼
        onYearChange / onFamilyChange / onModeChange callbacks bubble up
        to MapIsland's setState, which recolors via applyStyleMap (D-12,
        UNCHANGED — ChoroplethLayer.ts untouched)
        │
        ▼
Leaflet L.geoJSON canvas layer (ChoroplethLayer.ts, protected, byte-identical)
```

### Recommended Project Structure

No new files strictly required beyond what MAPSH-05 already names ("`MapTopbar.tsx` and sibling control components"). Concretely:

```
site/src/components/map/
├── MapTopbar.tsx        # rewritten: composes NewsToggle + EntryPointsRail/FAB, receives mode/onModeChange as plain props (F-47)
├── FiltersRow.tsx        # DELETED
├── NewsToggle.tsx        # NEW sibling — standalone labeled toggle (MAPSH-01)
├── EntryPointsRail.tsx    # NEW sibling — Año/Tipo de delito/Modo <details> group + state summary
├── FilterSheet.tsx        # NEW sibling — mobile <dialog>+showModal() bottom sheet, FAB trigger
├── SearchBox.tsx          # unchanged
├── Legend.tsx             # unchanged except z-index fix (spec §3: raise .legend off 700)
├── ZoomControl.tsx        # unchanged
├── ResultPanel.tsx        # unchanged except CSS-only FAB-collision coordination (§4a)
├── MapIsland.tsx          # mode-toggle prop wiring moved out (F-47); ?region= parsing added (F-48); ChoroplethLayer/IncidentPinLayer/LowZoomDotLayer calls UNCHANGED
└── map.css                # .filters-row/.ev-chip/.mode-toggle rules replaced; new entry-point/dialog/FAB rules; .legend z-index fixed; FAB-collision rule added
```

This is a **proposal**, not a pinned file list — the design spec pins *behavior and DOM contract* (§5, §8), not component filenames. Splitting into `NewsToggle.tsx`/`EntryPointsRail.tsx`/`FilterSheet.tsx` is one reasonable decomposition consistent with "sibling control components"; a single larger `MapTopbar.tsx` would equally satisfy MAPSH-05's *scope* constraint. The planner should pick one and record it (mirroring how F-47 required an explicit pick for §9a).

### Pattern 1: `<details>` grouped filter entry, one-open-at-a-time, non-modal

**What:** Each dimension (`Año`/`Tipo de delito`/`Modo`) is a `<details>` whose `<summary>` is the visible always-present control; opening one must close any other open one, driven by the native `toggle` event — exactly as demonstrated working in the sketch.
**When to use:** All three grouped entry points at ≥481px (spec §4 band table).
**Example (from the sketch, already React-portable 1:1):**
```html
<!-- Source: .planning/sketches/029-map-controls/iter-2/desktop.html:241-253 -->
<script>
var entries = document.querySelectorAll('details.entry');
for (var i = 0; i < entries.length; i++) {
  (function (d) {
    d.addEventListener('toggle', function () {
      d.querySelector('summary').setAttribute('aria-expanded', d.open ? 'true' : 'false');
      if (d.open) {
        for (var j = 0; j < entries.length; j++) {
          if (entries[j] !== d && entries[j].open) entries[j].open = false;
        }
      }
    });
  })(entries[i]);
}
</script>
```
In React this becomes a `useEffect` with `ref`s to the three `<details>` elements (or a small shared open-id state lifted to a parent `EntryPointsRail` component using controlled `open` props + `onToggle` handlers) — either approach avoids a new dependency. **The sketch does NOT implement Escape-closes or click-outside-closes** (spec §6 requires both, but iter-2's script only wires the `toggle` event for mutual exclusion) — this is new code Phase 30 must write; see Q2.

### Pattern 2: Mobile bottom sheet via native `<dialog>` + `showModal()`

**What:** Below 480px, `<dialog id="filter-sheet">` is opened with `.showModal()` (never the `open` attribute — spec §5 is explicit that this distinction is load-bearing for focus containment/Escape/backdrop) from a FAB (`data-role="filter-entry"`).
**Example (working reference, port as-is into a React ref+effect):**
```js
// Source: .planning/sketches/029-map-controls/iter-2/desktop.html:255-272
fab.addEventListener('click', function () {
  sheet.showModal();
  fab.setAttribute('aria-expanded', 'true');
});
closeBtn.addEventListener('click', function () {
  sheet.close();
  fab.setAttribute('aria-expanded', 'false');
  fab.focus();
});
sheet.addEventListener('close', function () {
  fab.setAttribute('aria-expanded', 'false');
});
```
Verify with `dialog.matches(':modal') === true` per spec §5 — `grep -c "showModal"` alone cannot distinguish `showModal()` from `<dialog open>`.

### Pattern 3: `?cut=`/`?region=` guarded URL-param parsing (existing pattern to mirror)

**What:** Read `window.location.search`, validate with a narrow regex/allowlist BEFORE any fetch or DOM mutation, degrade silently on mismatch.
**Existing code to mirror exactly (already correct, previously fixed per memory `map-focus-unknown-cut-polish`):**
```typescript
// Source: site/src/components/map/MapIsland.tsx:226-232
const focusCut = new URLSearchParams(window.location.search).get('cut');
if (focusCut && /^\d{4,5}$/.test(focusCut)) {
  setTimeout(() => selectCommune(focusCut), 100);
}
```
For `?region=`, the equivalent guard is a check against the known `region_id` set already resident client-side in `communeIndex` (`MapIsland.tsx:111,183` — `CommuneIndexEntry[]`, each with `.region_id: string`, sourced from `data/cead/meta/index.json`, confirmed values `"10"`, `"13"` etc. — strings, never numbers, matching F-20). Concretely:
```typescript
// Proposed pattern — NOT existing code, illustrative only
const focusRegion = new URLSearchParams(window.location.search).get('region');
if (focusRegion && communeIndex.some((c) => c.region_id === focusRegion)) {
  // fitBounds over every polygon in polyIdxRef whose CUT belongs to this region_id
}
```
This never triggers a fetch (the guard is a membership check against already-loaded `communeIndex`, not a file existence probe), satisfying F-48's "no fetch of a non-existent file" requirement. Note `communeIndex` is only populated *after* the initial `safeFetch` for `meta/index.json` resolves (`MapIsland.tsx:172,183`) — the `?region=` effect must depend on `communeIndex.length > 0` (or `mapReady` + a loaded flag), not fire in the same effect as `?cut=` at `MapIsland.tsx:226` which runs before `communeIndex` is guaranteed populated (`Promise.all` at line 169-173 resolves all three fetches together, so by the time the effect body at line 226 runs, `communeIndex` state itself has NOT yet been set via `setCommuneIndex` — it is only set at line 183, and React state updates from the same synchronous block are not visible until the next render). **This is a real ordering hazard, not a hypothetical** — the `?region=` guard must read `idx` (the local variable at line 172), not `communeIndex` (the state), since it executes in the same `loadData()` closure before the state update commits.

### Anti-Patterns to Avoid

- **Declarative react-leaflet layer components** (`<GeoJSON>`, `<Marker>` as JSX children) — hard-banned by F-47/MAPSH-05; the codebase already uses native `L.geoJSON()` inside `mountChoroplethLayer` for exactly this reason (documented re-render-on-hover bug, `MapIsland.tsx:9-11`).
- **A global unconditional `document.addEventListener('keydown', ...)`** registered once at mount and never removed/scoped — this is the exact shape `score.mjs`'s `keyInterceptors` scan is watching for (`score.mjs:138`), and more importantly is a real accessibility risk if it ever calls `preventDefault()` broadly. See Q2 for the narrower alternative.
- **Re-fetching or re-mounting the choropleth layer on filter change** — D-12 (documented in `MapIsland.tsx:13`) requires `setStyle` in place; this phase's new entry points must call the *existing* `onYearChange`/`onFamilyChange` callbacks, never re-mount `layerRef.current`.
- **Using `<GeoJSON>`-adjacent patterns for the dot layer/pin layer** — same as above; `LowZoomDotLayer.ts`/`IncidentPinLayer.ts` are protected and Phase 30 has no reason to touch them at all (the filter-shell rework does not change what layers exist, only how their controlling filters are exposed).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Focus containment + Escape + backdrop for the mobile sheet | A custom modal implementation with manual focus trap JS | Native `<dialog>` + `.showModal()` | Browser-native focus containment, Escape-to-close, and `::backdrop` are exactly what MAPSH-02's "zero new JS dependencies" clause exists to make you use instead of a modal library |
| Single-select radio-like option groups | A custom keyboard-nav widget | `role="radiogroup"` wrapping `role="radio"` buttons (spec §5 — NOT `role="group"`, which the original sketch used and the spec explicitly calls invalid) | ARIA authoring practices define this exact pattern; a `role="group"` parent for `role="radio"` children fails the ARIA 1.2 spec's required-owned-elements rule and screen readers will not announce the group as a radio group |
| Mutual-exclusion of open panels | A custom "close all others" event bus | The native `toggle` event on each `<details>`, iterated over a small NodeList (as in the sketch) | Already demonstrated working in `iter-2/desktop.html:241-253`; no state management library needed for 3 elements |

**Key insight:** every "don't hand-roll" item in this phase resolves to "the native HTML element already does this" — that is the entire point of MAPSH-02's dependency-zero constraint, and the sketch already proves each pattern works.

## Common Pitfalls

### Pitfall 1: `communeIndex` state-vs-closure-variable race for `?region=`
**What goes wrong:** Reading `communeIndex` (React state) inside the same `loadData()` closure that calls `setCommuneIndex(idx)` will read the stale (empty) array, because the state setter has not committed yet.
**Why it happens:** `MapIsland.tsx:183` sets state; `MapIsland.tsx:226` (same synchronous function body) is where `?cut=`'s guard runs today — but `?cut=` doesn't need `communeIndex` at all (it just validates a regex and calls `selectCommune`, which independently reads `polyIdxRef.current`, populated later at line 211-225). `?region=`'s guard, in contrast, DOES need the just-fetched index to validate `region_id` membership, so it must read the local `idx` variable (line 172), not the `communeIndex` state.
**How to avoid:** Place the `?region=` parse/guard/dispatch logic after `if (idx) setCommuneIndex(idx);` (line 183) but reference `idx` directly, not `communeIndex`.
**Warning signs:** `?region=` deep link works on second visit (state now populated from a previous mount) but not on first cold load — a classic "worked in dev, broken in prod" symptom if tested via hot-reload where state persists across edits.

### Pitfall 2: `.mode-toggle`'s `position:static` reset is explicitly NOT a template for the news toggle
**What goes wrong:** Reusing the existing `@media (max-width: 480px) { .mode-toggle { position: static; } }` rule (`map.css:240-251`) as a shortcut for laying out the news toggle at narrow widths would drop it out of its z-index-800 stacking context exactly where spec §4 requires it to stay pinned.
**Why it happens:** It looks like a ready-made "how do we stack controls at ≤480px" pattern already in the codebase.
**How to avoid:** Spec §4 states this explicitly: "This is not a usable precedent for the news toggle... the toggle carries its own explicit z-index at every band." Give the news toggle its own always-`relative`/`absolute` positioning with an explicit `z-index: 800` at every breakpoint, never falling back to `static`.
**Warning signs:** News toggle visually present but a Leaflet popup or another topbar element paints over it at ≤480px only.

### Pitfall 3: The `.legend` z-index fix and `zIndexViolations`'s `<=700` predicate
**What goes wrong:** Naively bumping `.legend`'s z-index from 700 to some arbitrary higher number (e.g. 750, matching the sketch) without checking `score.mjs`'s predicate (`score.mjs:208-210`: `c.zIndex > 0 && c.zIndex <= 700` is a violation) could still tie or undershoot if the chosen value isn't clearly outside every other "700-tier" control's exact number.
**Why it happens:** The real z-index ladder (spec §3) places `legend`/`result-panel`/`zoom-ctl` all nominally at "700" as a *tier label*, but the instrument treats exactly ≤700 as a violation — so `.legend` must move to a distinct value >700 that does not collide with `map-topbar` (800) or the mode-toggle band (801), e.g. matching the sketch's 750.
**How to avoid:** Set `.legend { z-index: 750; }` (as the sketch does at `iter-2/desktop.html:93`) and re-run `score.mjs`'s `controlZIndexes`/`zIndexViolations` check against the real built page before considering this closed.
**Warning signs:** `score.mjs` still reports `legend=700` after the "fix" — check that the CSS specificity/cascade actually applied (a leftover unscoped rule elsewhere in `map.css` could still be setting 700).

### Pitfall 4: `FiltersRow.tsx`'s crime-family chip data (`CHIP_DEFS`) must not be silently dropped
**What goes wrong:** Deleting `FiltersRow.tsx` wholesale without carrying over `CHIP_DEFS` (`FiltersRow.tsx:30-43`, including the homicide 8th "chip" with `familyIndex: null` and the `featured`/title-tooltip wiring from `familyDefs.ts`) would lose the homicide-layer selection and the hover-tooltip accessibility feature (D-02 gap-closure, cited at `FiltersRow.tsx:13-15`).
**Why it happens:** The file is being deleted, not refactored, and it's easy to treat "delete the flat row" as "delete the whole file's logic including the family taxonomy," when only the *rendering* (a scrollable row of chips) is the defect — the *data* (order, `familyIndex` mapping, homicide special-case, ES/EN labels) must migrate into the new `Tipo de delito` entry point's option list.
**How to avoid:** Port `CHIP_DEFS` verbatim (do not re-derive the family_keys index mapping) into the new `Tipo de delito` `<details>` panel's option list; each `role="radio"` option corresponds 1:1 to a former chip.
**Warning signs:** Homicide layer no longer selectable from the UI; missing hover-title tooltips users previously had on crime-type chips.

### Pitfall 5: Both `MapTopbar.tsx` map pages (EN `/map/`, ES `/es/mapa/`) must be exercised, and only the ES one is safe to drive live locally until F-40 lands
**What goes wrong:** Testing exclusively against `/map/` (EN) during Wave 0/1 before the redirect-origin fix lands would silently bounce the browser to `https://ischilesafe.com` (production) per F-40/§11 of the spec — every subsequent measurement in that session would be of production, not the local build.
**Why it happens:** `BaseLayout.astro:122-125` (verified: `nav.toLowerCase().startsWith('es')` → `window.location.replace(esLink.href)`, where `esLink.href` is an absolute URL built from `BASE_URL`) fires for any es-locale browser hitting an EN page.
**How to avoid:** Fix the one line first (Wave 0 task, per F-40/§11: take `new URL(esLink.href).pathname + search + hash`, keep current origin), then drive `http://127.0.0.1:4321/es/mapa/` for all subsequent measurement, per the phase's explicit driving rule.
**Warning signs:** A local BrowserOS tab unexpectedly shows the live production site mid-session.

## Code Examples

### Existing `?cut=` guarded deep-link parsing (pattern to mirror for `?region=`)
```typescript
// Source: site/src/components/map/MapIsland.tsx:226-232
const focusCut = new URLSearchParams(window.location.search).get('cut');
if (focusCut && /^\d{4,5}$/.test(focusCut)) {
  // Small timeout to allow Leaflet to finish rendering polygons before getBounds is valid
  setTimeout(() => selectCommune(focusCut), 100);
}
```

### Existing mode-toggle construction to be moved (F-47's exact edit target)
```typescript
// Source: site/src/components/map/MapIsland.tsx:439-472 (excerpt — full block must move)
modeToggle={
  <div className="mode-toggle" role="group" aria-label={lang === 'es' ? 'Modo de mapa' : 'Map mode'}>
    <button className={`chip${mode === 'composite' ? ' active' : ''}`} onClick={() => { setMode('composite'); /* ... */ }}>
      {lang === 'es' ? 'Índice' : 'Index'}
    </button>
    <button className={`chip${mode === 'family' ? ' active' : ''}`} onClick={() => { setMode('family'); /* ... */ }}>
      {lang === 'es' ? 'Por delito' : 'By crime'}
    </button>
  </div>
}
```
Per F-47, this JSX construction moves into `MapTopbar.tsx` (or a sibling `ModeEntryPoint` inside it), with `MapIsland.tsx` instead passing `mode={mode} onModeChange={(next) => { setMode(next); /* same recolor logic */ }}` as plain props. The recolor side-effect logic (calling `buildStyleMapFromCompositeIndex`/`buildStyleMapFromHomicide`/etc. and `applyStyleMap`) can stay in `MapIsland.tsx` inside the `onModeChange` callback exactly as it is today — only the JSX markup moves.

### `dialog.matches(':modal')` verification (spec §5's required check)
```js
// Proposed verification snippet for the orchestrator's manual/BrowserOS pass — not existing code
const sheet = document.getElementById('filter-sheet');
sheet.showModal();
console.log(sheet.matches(':modal')); // must be true
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Flat `.filters-row` horizontally-scrolling chip row (`FiltersRow.tsx`, `map.css:47-59`) | Grouped `<details>` entry points + persistent news toggle + mobile `<dialog>` FAB sheet | This phase (implementing `29-DESIGN-SPEC.md`) | News toggle and filters go from ~507-991px hidden overflow to zero hidden content at every measured width (spec §0, §12) |
| `mode` rendered as an ungrouped standalone control (`.mode-toggle`, absolutely positioned top-right) | `Modo` folded into the same grouped entry-point rail as `Año`/`Tipo de delito` | This phase (F-47) | Removes a fourth separately-positioned control, reducing visual clutter and unifying interaction pattern |
| `.legend` at z-index 700 (ties `.leaflet-popup-pane`) | `.legend` at an explicit value clear of 700 (e.g. 750, per sketch) | This phase (spec §3) | Removes the one real z-index defect the Phase 29 loop found on the live map |

**Deprecated/outdated:** `.ev-chip`/`.filters-row` CSS classes must not survive in `dist/` after this phase — `score.mjs` falls back to them when `data-role` hooks are absent, so any surviving reference (even dead CSS) risks the instrument silently re-binding to legacy markup if a stray element still carries the class.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Splitting `MapTopbar.tsx`'s new controls into `NewsToggle.tsx`/`EntryPointsRail.tsx`/`FilterSheet.tsx` as separate sibling files (vs. one larger `MapTopbar.tsx`) is a reasonable decomposition | Recommended Project Structure | None if the planner instead chooses a single-file decomposition — both satisfy MAPSH-05's *scope* constraint; this is a structural suggestion, not a pinned requirement, and is explicitly flagged as such in-line |
| A2 | A React `useEffect` with three `<details>` refs (rather than lifting to a single `openId` state) is a viable, dependency-free way to port the sketch's mutual-exclusion script | Pattern 1 | Low — either approach is native-JS-only; if refs prove awkward, controlled `open` + `onToggle` state is a drop-in alternative, still zero new dependencies |

**If this table is empty:** N/A — two low-risk structural suggestions are recorded above; nothing here overrides `29-DESIGN-SPEC.md`'s pinned behavior/DOM contract, and nothing here is a compliance, retention, or security claim.

## Open Questions — Answered

### Q1. What state does `MapIsland.tsx` hold today, and what props does each new control need?

**State currently in `MapIsland.tsx` (verified `MapIsland.tsx:96-114`):**
`year: number`, `crimeFamily: string | null`, `crimeFamilyIndex: number | null`, `crimeIsHomicide: boolean`, `mode: 'composite' | 'family'`, `showEvents: boolean`, `lowZoom: boolean`, `selected: string | null`, `loadError: boolean`, `toast: string | null`, `communeIndex: CommuneIndexEntry[]`, `mapReady: boolean`, `breaks: number[] | undefined`, `partialYear: boolean`.

**Props each new control needs (mapped from state MapIsland already owns):**
- `Año` entry point: `year: number`, `onYearChange: (year: number) => void` — identical to the existing `FiltersRow` props (`FiltersRow.tsx:56-57`), no new state needed.
- `Tipo de delito` entry point: `crimeFamily: string | null`, `onFamilyChange: (key, idx) => void` — identical to existing (`FiltersRow.tsx:58-59`); must additionally surface the homicide chip (`key: 'homicidios', familyIndex: null`) exactly as `CHIP_DEFS` does today (`FiltersRow.tsx:42`).
- `Modo` entry point (NEW location per F-47): `mode: 'composite' | 'family'`, `onModeChange: (m) => void` — **does not exist as a prop today**; must be added, replacing the current `modeToggle: React.ReactNode` prop (`MapTopbar.tsx:20`) which is a pre-built node, not state+callback.
- News toggle: `showEvents: boolean`, `onEventsToggle: (v) => void` — identical to existing (`FiltersRow.tsx:60-61`).
- State summary (`aria-live="polite"`, spec §2.4/§6): needs read-only derived values — `mode`, `crimeFamily` (or "Todos"), `year` — all already available as props above; no new state, purely a formatting function over existing props.
- `?region=`-driven "region focus": needs `communeIndex: CommuneIndexEntry[]` (already a MapIsland state, `MapIsland.tsx:111`) plus a way to iterate `polyIdxRef.current` (a ref, already present, `MapIsland.tsx:88`) to collect all polygons whose CUT's `region_id` matches — this can be implemented entirely inside `MapIsland.tsx`'s existing data-load effect, no new prop needed for the initial focus-on-load case, though a manual region-select UI (not required by MAPSH-04, which only asks for URL-driven focus) would need new plumbing if ever added later.

**Conclusion:** `MapIsland.tsx`'s existing state shape already covers every new control except the `mode`/`onModeChange` plain-prop pair, which is exactly the one narrowly-scoped edit F-47 authorizes.

### Q2. `<details>` one-panel-open + Escape-closes + click-outside-closes with zero dependencies, and the c4 tradeoff

**One-panel-open:** Solved natively, zero-dependency, exactly as the sketch demonstrates (`iter-2/desktop.html:241-253`) — a `toggle` event listener per `<details>` that closes siblings. No `keydown` needed for this part.

**Escape-closes:** Native `<details>` elements do **not** close on Escape by default (unlike `<dialog>`, which does). Achieving this requires either:
(a) A `keydown` listener scoped to `document`, checking `e.key === 'Escape'` and whether any tracked `<details>` is currently `.open`, then setting `.open = false` and returning focus to that `<summary>`; or
(b) No listener at all, accepting that Escape does nothing for the non-modal entry points (a spec violation — §6 requires it).

Since spec §6 explicitly mandates Escape-closes and click-outside-closes for the non-modal entry panels, some new JS is unavoidable — but it is a narrowly-scoped `document`-level `keydown` listener (checking a small closed set of tracked elements, calling `preventDefault()` only when a panel is actually open and Escape was pressed) rather than a broad interceptor. This is exactly the shape `score.mjs`'s static-scan `keyInterceptors` check is designed to flag when it CAN see the code (inline `<script>` text) — but against the real built app, React/Astro ship this handler inside an external module bundle with no inline text, so `score.mjs` will hit its `externalScripts.length > 0` branch (`score.mjs:145-151`) and return `criterion4 = 'NOT_MEASURED_FAIL'` regardless of whether the listener exists or is well-behaved.

**Explicit tradeoff:** A `document`-scoped `keydown` listener is required to satisfy spec §6's Escape-dismissal requirement, and it is unavoidable given the constraint of zero new dependencies (no existing native primitive gives `<details>` an Escape-to-close behavior). **This is not a defect to hide** — it must be evidenced per F-49's three-part chain, not disguised as passing c4 cleanly:
1. `negativeTabindexCount === 0` (from `score.mjs` itself, still measurable even with `NOT_MEASURED_FAIL` on the composite criterion4).
2. `grep` the built `dist/` JS chunks for `keydown`/`keyup`/`preventDefault` in the map island's own bundle — expect a **positive** match (this listener), and manually confirm by reading the matched context that it only acts when a panel is open and never blocks Tab/Shift+Tab.
3. A real Tab walk in BrowserOS through the documented focus order (spec §6: skip-link → header nav → search → locate → news toggle → Año → Tipo de delito → Modo → state summary → map → legend → zoom), confirming focus is never trapped and Escape only closes the currently-open panel without swallowing any other key.

**Click-outside-closes:** Achievable with a `document`-scoped `mousedown`/`click` listener checking `!detailsEl.contains(e.target)` — same category of listener as (a), can be combined into one shared `document` listener that handles both concerns. This is the same pattern `SearchBox.tsx:50-58` already uses for its own dropdown (`document.addEventListener('mousedown', handleClick)` scoped via a `containerRef.contains` check) — **an existing, already-shipped precedent in this exact codebase**, which strengthens the case that this pattern is acceptable practice here, not a novel risk.

### Q3. `?region=` parsing, "region focus" semantics, and unknown-value degradation

**Where it must be parsed:** In the same `useEffect`/`loadData()` closure as the existing `?cut=` parse (`MapIsland.tsx:160-241`), specifically after `idx` (the fetched `CommuneIndexEntry[]`) is available (see Pitfall 1 above for the exact ordering hazard — must read the local `idx` variable, not the `communeIndex` state).

**What "region focus" means concretely, given what `?cut=` already does:** `?cut=` calls `selectCommune(cut)` (`MapIsland.tsx:388-407`), which does two things: (1) sets `selected` state + calls `highlightSelected` on the choropleth layer, and (2) calls `map.flyToBounds()` on that single polygon's bounds (`ly.getBounds()`). For `?region=`, the equivalent is: compute the **union of bounds** across every polygon in `polyIdxRef.current` whose corresponding commune has that `region_id` (cross-referenced via `idx`/`communeIndex`, matching by CUT), then call `map.flyToBounds()` (or `fitBounds()`) on the combined `L.latLngBounds` — this is a "zoom to region extent" action, not a commune selection (it must NOT set `selected`, since no single commune was chosen, and must NOT open `ResultPanel`, which is gated on `selected !== null`, `MapIsland.tsx:518`).

**Guard before fetch, no 404/console error on unknown value:**
```typescript
// Proposed pattern, mirroring MapIsland.tsx:228-232 exactly — NOT existing code
const focusRegion = new URLSearchParams(window.location.search).get('region');
if (focusRegion && idx.some((c) => c.region_id === focusRegion)) {
  // safe: focusRegion is confirmed to match at least one already-loaded commune's region_id
  // — no fetch is ever attempted for an unknown region_id, since the check is a pure
  // in-memory array scan over data already fetched for the initial map load.
}
```
Because `region_id` membership is checked against data **already resident in memory** (the same `idx`/`meta/index.json` fetch that powers the search box), an unknown `?region=` value simply fails the `.some()` check and the `if` body never runs — no additional `fetch()` call exists in this code path at all, so there is structurally no way for a bad value to trigger a 404. This is stronger guard placement than `?cut=`'s regex check, because `?cut=`'s regex only validates *shape* (4-5 digits), not *existence* — an unknown-but-well-shaped CUT (e.g. `99999`) would pass the regex and calls `selectCommune('99999')`, which then does `polyIdxRef.current.get('99999')` returning `undefined`, silently no-oping the `flyToBounds` call (`MapIsland.tsx:397-406`, the `if (ly && ...)` guard) — so `?cut=`'s existing degradation is also silent, just via a different mechanism (map lookup miss rather than array membership). Both approaches converge on "no fetch, no console error, no toast" — consistent with F-48.

**`?cut=` must keep working unchanged:** Confirmed no proposed change touches `MapIsland.tsx:226-232`; the `?region=` logic is additive, placed in the same effect but as an independent `if` block.

### Q4. `.result-panel` × FAB collision fix — CSS-only feasibility

**Current DOM structure (verified, `MapIsland.tsx:412-533`):** `ResultPanel` and the (to-be-added) FAB are both direct children of `<div className="map-stage...">` (`MapIsland.tsx:413`), siblings under the same parent. `ResultPanel` renders conditionally (`{selected && <ResultPanel .../>}`, `MapIsland.tsx:518`), and `MapIsland.tsx:413` already computes `` `map-stage${selected ? ' has-panel' : ''}` `` — **a `has-panel` class is already added to the shared ancestor (`.map-stage`) whenever a commune is selected, today, for other styling purposes.** This is the exact mechanism spec §4a needs.

**CSS-only solution:** Because `.map-stage.has-panel` already exists as a hook, the FAB (a sibling of `.result-panel` under the same `.map-stage`) can use:
```css
/* Proposed — not existing code */
.filter-fab { bottom: 24px; /* default */ }
@media (max-width: 640px) {
  .map-stage.has-panel .filter-fab { bottom: calc(40vh + 16px); }
}
```
This requires **zero JavaScript** — the FAB "learns" the panel is open purely via the CSS descendant selector against the class already toggled by existing React logic (`MapIsland.tsx:413`), with no new state, no new prop drilling, and no `ResizeObserver`/`MutationObserver`. This is the cleanest possible answer to Q4: the ancestor-class hook the spec's §4a decision needs is **already shipped code**, one line away from being reused.

**Verify:** Spec §4a's stated verification (`elementFromPoint` topmost check on `[data-role="filter-entry"]` with a commune selected) is exactly what `score.mjs`'s existing `isTopmost` helper (`score.mjs:33-36`) already does generically for any control — running the rubric with a commune selected (a stress condition not in the original `STRESS.md` list, per spec §4a's own note) will validate this.

### Q5. Baseline `score.mjs` run — orchestrator's exact steps (I cannot run BrowserOS)

I have no BrowserOS tools in this research pass and must not fabricate a score. The orchestrator (inline, per environment rule) must run, in order:

```bash
# 1. Fix F-40's one-line redirect bug FIRST (Wave 0), or the ES-origin workaround below
#    substitutes for it until fixed. From site/:
cd "site" && npm run build && npm run validate
```
(single chained command per the OneDrive gate-hygiene rule — `dist/` must not desync between processes)

```bash
# 2. Serve the build (no npm run preview script exists)
npx astro preview --port 4321 --host
```

```
3. In BrowserOS (inline, orchestrator session, NOT gsd-executor):
   - navigate to http://127.0.0.1:4321/es/mapa/  (NEVER /map/, per F-40/§11)
   - for each width in [320, 375, 481, 639, 1296]:
       - emulate the width via a same-origin iframe (no native viewport-resize tool
         — per BrowserOS constraint list), served from the SAME http origin (not file://)
       - evaluate_script: `(${scoreControlShell.toString()})({stressCondition: '<id>'})`
         — the wrapper invocation is mandatory per score.mjs's own header comment
       - record the full JSON result verbatim, per width, BEFORE any code changes
   - run the `verdict()` function over each captured JSON to get PASS/FAIL per criterion
```

**Flag explicitly:** Per F-49, expect `criterion4` to likely return `NOT_MEASURED_FAIL` against the real page, NOT the `c4 PASS` that `29-DESIGN-SPEC.md §0` reports from the baseline capture — because Astro ships the map island as `<script type="module" src=...>` (external, no inline text), which trips `score.mjs`'s `externalScripts.length > 0` branch (`score.mjs:145-151`). The Phase 29 spec's own §0 table shows `c4 PASS` from an earlier capture, but STATE.md's Phase 29 Outcome item 1 and F-42's ledger entry state the corrected instrument, run against the real live `/map/`, returns `c1/c2/c3/c5 FAIL, c4 PASS` — meaning either the real page's module script textContent happened to be empty in a way that still yielded `keyInterceptors: []` legitimately (no interceptors currently exist, since there is no `<details>`/`<dialog>` code shipped yet pre-Phase-30), or the distinction is that TODAY's map ships no keydown-handling code at all so `externalScripts.length > 0` is true but happens not to matter for a PASS/FAIL semantic — re-read `score.mjs:145-151` carefully: `NOT_MEASURED_FAIL` is set as soon as `externalScripts.length > 0`, **overriding** any keyInterceptors computation. This means the STATE.md claim of "c4 PASS" against the real page is worth re-verifying at Wave 0 exactly as F-49 mandates ("Wave 0 must measure the current c4 result... rather than assume it") — **this research cannot resolve the apparent tension in the existing record and explicitly flags it as the first thing Wave 0 must settle by running the instrument, not by trusting either prior document.**

### Q6. What can an automated (non-browser) gate assert from `dist/` alone?

**Assertable purely from `dist/` via `grep`/`node`, no browser needed:**
1. `.filters-row` and `.ev-chip` class-name absence — `grep -rL` inverted, or `grep -c` returning 0, across `dist/es/mapa/index.html`, `dist/map/index.html`, and any built CSS/JS chunk referencing these class names.
2. Presence of the three `data-role` hooks in the shipped HTML — `grep -o 'data-role="[^"]*"' dist/es/mapa/index.html | sort -u` should include `news-toggle`, `filter-entry` (expect it to appear at least twice — once on the rail, once on the FAB, per spec §8), `entry-point` (expect at least 3 occurrences pre-hydration if server-rendered attributes are present, though note this is a `client:only="react"` island — see caveat below).
3. `showModal(` string presence in the shipped JS chunk that contains the map island's bundle — `grep -c "showModal(" dist/_astro/*.js` (or wherever Astro's chunk-hash naming places the map bundle) should be ≥1.
4. Explicit z-index numeric values in the built CSS — `grep -n "z-index" dist/_astro/*.css` (or wherever `map.css` compiles to) should show the pinned values (800, 801, 750 for legend, etc.) as literal numbers, never `auto`, for every non-modal always-visible control class.
5. `git diff --exit-code -- site/src/components/map/ChoroplethLayer.ts site/src/components/map/IncidentPinLayer.ts site/src/components/map/LowZoomDotLayer.ts` — byte-identical gate (F-47), runs against the source tree, not `dist/`.
6. `git diff --exit-code -- site/package.json site/package-lock.json` — zero new dependencies gate.

**Important caveat on #2:** `MapIsland` is mounted with `client:only="react"` (confirmed `map.astro:34`, `mapa.astro:39`) — Astro does **not** server-render this component's output into the static HTML at all (that is the whole point of `client:only`; it ships an empty placeholder + hydration script and the real DOM is built client-side after JS runs). This means **`grep`-ing `dist/es/mapa/index.html` for `data-role="entry-point"` will find NOTHING**, because the entry-point `<details>` elements do not exist in the static HTML — they are constructed by React in the browser. The only way to verify these hooks exist in the *rendered* DOM is a browser check (BrowserOS `evaluate_script` running `document.querySelectorAll(...)`, exactly what `score.mjs` already does). **This is the single most important finding of Q6: item #2 above is only partially automatable from `dist/` — the static HTML can prove the *island mounts* (existing `map.mjs` check #3, `astro-island` marker) but cannot prove the *hooks render*, because they render client-side.**

**Settled only in a browser (cannot be automated from `dist/` alone):**
- Whether `data-role="entry-point"`/`filter-entry`/`news-toggle` actually appear in the LIVE DOM after React hydrates (per the caveat above).
- All of `score.mjs`'s criteria (c1-c5) — every one of them calls `getBoundingClientRect()`/`getComputedStyle()`/`elementFromPoint()`, which require a real (or real-origin-emulated) rendered layout; none of this exists in static `dist/` HTML for a `client:only` island.
- `dialog.matches(':modal')` — requires a live DOM with the dialog actually open.
- Real Tab-walk focus order (spec §6) and the Escape/click-outside dismissal behavior (Q2) — inherently interactive, browser-only.
- The FAB × `.result-panel` collision fix (Q4) with a commune actually selected — requires triggering a real click and re-measuring layout.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Native `<details>`/`<summary>` | MAPSH-02 grouped entry points | ✓ (all evergreen browsers; project ships no IE11 support) | — | — |
| Native `<dialog>` + `showModal()` | MAPSH-02 mobile sheet | ✓ (all evergreen browsers) | — | — |
| `npx astro preview` | Local build serving for BrowserOS pass | ✓ (part of installed `astro` devDependency; no separate `npm run preview` script exists — confirmed via `package.json` scripts block) | matches project's Astro 6.x | — |
| BrowserOS MCP | Manual measurement pass (score.mjs, Tab walk, showModal check) | Available to the orchestrator per environment instructions; **NOT available to this research agent** — all Q5/Q6 browser steps are prescribed, not executed, here | — | None — this is a hard requirement of MAPSH-03/06 acceptance; no automated substitute exists for the interactive checks listed in Q6 |
| `slopcheck` / package registry checks | N/A — zero new packages this phase | N/A | N/A | N/A |

**Missing dependencies with no fallback:** BrowserOS execution itself — this research agent has no such tools and did not attempt to fabricate a score; every BrowserOS step above is a prescribed command for the orchestrator, not a completed measurement.

## Validation Architecture

`.planning/config.json`'s `workflow.nyquist_validation` was not found set to `false` in the read config — treat as enabled (absent = enabled per default rule).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | vitest (confirmed `site/package.json` `"test": "vitest run"`; 37 existing tests, all pure-logic under `site/src/lib/`) |
| Config file | No standalone `vitest.config.ts` found at `site/` root — vitest likely runs off Vite/Astro's own config or defaults; UNVERIFIED — the orchestrator should confirm with `npx vitest --version` and `npx vitest list` before Wave 0 if a new test file is planned |
| Quick run command | `cd site && npx vitest run <path-to-new-test>.test.ts` |
| Full suite command | `cd site && npm test` (37 tests today; any new pure-logic test for this phase adds to that count, which cascades into hardcoded counts per F-21 — flag any new test file to the planner explicitly) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MAPSH-04 | `?region=` guard degrades silently on unknown value, matches existing region_id set | unit (IF extracted as its own pure function, mirroring `parseFilterParams`'s own test file) | `npx vitest run src/components/map/regionParam.test.ts` (proposed name) | ❌ Wave 0 — only worth creating if the guard logic is factored into a standalone importable function; if it stays inline inside `MapIsland.tsx`'s effect, this cannot be unit-tested without a DOM harness and MUST fall to the browser/manual pass instead |
| MAPSH-01/02/03 | News toggle discoverable, filters discoverable, no overflow, touch targets, keyboard trap-free, z-index clean | browser (score.mjs) | BrowserOS `evaluate_script` per Q5's prescribed steps | N/A — not a vitest-shaped check at all |
| MAPSH-05 | Protected Leaflet files untouched | automated (non-browser) | `git diff --exit-code -- site/src/components/map/ChoroplethLayer.ts site/src/components/map/IncidentPinLayer.ts site/src/components/map/LowZoomDotLayer.ts` | N/A — pure git check |
| MAPSH-06 | `?cut=` deep link, choropleth filters, geolocation, incident pins unchanged | manual/browser regression pass | BrowserOS click-through of each existing behavior at `/es/mapa/` | N/A — no automated harness exists for the map island's full interactive behavior today |

### Sampling Rate
- **Per task commit:** `cd site && npm test` (fast — pure-logic suite, seconds)
- **Per wave merge:** `cd site && npm run build && npm run validate && npm test` (chained per OneDrive gate hygiene) + a BrowserOS `score.mjs` pass at the five widths
- **Phase gate:** Full suite green (pytest, vitest, 16/16 validators, astro check) + `score.mjs` bar reproduced per spec §12 + the three F-49 c4 evidences recorded, before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] Fix `BaseLayout.astro:122-125` redirect-origin bug (F-40) — one-line change, take `new URL(esLink.href).pathname + search + hash`, keep current origin
- [ ] Run `score.mjs` against the real, unmodified `/es/mapa/` at all five widths and record the verbatim baseline (F-49's mandatory pre-change measurement) — **do not trust `29-DESIGN-SPEC.md §0`'s or `STATE.md`'s prior figures as a substitute**; those were captured under different conditions/dates and F-49 explicitly requires re-measurement now
- [ ] Decide (and record, not discover mid-implementation, per spec §9a) which of options (a)/(b) is used for the mode-toggle fold — F-47 has already pre-decided (a), so this is really "confirm F-47 and proceed," not an open choice
- [ ] Decide the exact new-component file split (single `MapTopbar.tsx` vs. `NewsToggle.tsx`/`EntryPointsRail.tsx`/`FilterSheet.tsx` siblings) — proposed above (A1), not pinned

## Security Domain

`security_enforcement` was not found explicitly set to `false`; treat as enabled per default rule, though this phase's actual attack surface is minimal (no new user input surface beyond `?region=`, which is read-only/display-only and never reflected into the DOM or used in any fetch path — see Q3's guard analysis).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | No auth surface in this phase |
| V3 Session Management | No | No session state introduced |
| V4 Access Control | No | No access-control surface |
| V5 Input Validation | Yes | `?region=` value is validated by exact-match membership against an already-loaded string set (`communeIndex`/`idx`) before any use — never regex-only, never used to construct a fetch URL or DOM string. `?cut=`'s existing `/^\d{4,5}$/` regex remains the pattern for shape validation where membership-checking isn't available |
| V6 Cryptography | No | Not applicable |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| Reflected XSS via `?region=`/`?cut=` echoed into the DOM | Tampering | Neither value is ever rendered into HTML/`dangerouslySetInnerHTML`; both are used only as opaque lookup keys against pre-loaded, code-controlled data (`polyIdxRef`, `communeIndex`) — confirmed for `?cut=` at `MapIsland.tsx:226-232` (no DOM injection, per its own comment "opaque string — Map lookup only, no DOM injection"); the same discipline must extend to `?region=` |
| Open-redirect via a manipulated `hreflang` link exploited through the existing EN→ES auto-redirect script | Tampering/Spoofing | Out of this phase's direct scope but adjacent — F-40's fix (keep current origin, use only the pathname/search/hash from `esLink.href`) is itself a hardening of an existing redirect that currently trusts an absolute production URL; Wave 0 must land this fix regardless of security framing, since it is also a correctness bug |

## Sources

### Primary (HIGH confidence — direct file reads, this session)
- `.planning/phases/30-map-control-shell-rework/30-FABLE-CONSTRAINTS.md` — F-47..F-50, binding
- `.planning/phases/29-map-ux-design-loop/29-DESIGN-SPEC.md` — full spec, binding
- `.planning/STATE.md` — Phase 29 Outcome, F-39..F-46 ledger entries
- `.planning/ROADMAP.md` — Phase 30 goal/success criteria/MAPSH list
- `.planning/REQUIREMENTS.md` lines 80-86 — MAPSH-01..07 text
- `.planning/sketches/029-map-controls/score.mjs`, `STRESS.md`, `iter-2/desktop.html`, `iter-2/mobile-375.html` — the regression instrument and adopted markup
- `site/src/components/map/MapIsland.tsx` (full file), `MapTopbar.tsx`, `FiltersRow.tsx`, `SearchBox.tsx`, `Legend.tsx`, `ZoomControl.tsx`, `ResultPanel.tsx` (partial), `map.css` (full 970 lines)
- `site/src/pages/map.astro`, `site/src/pages/es/mapa.astro`, `site/src/layouts/BaseLayout.astro` (redirect lines)
- `site/scripts/validate/all.mjs`, `site/scripts/validate/map.mjs` (full)
- `site/src/lib/familyDefs.ts` (full), `site/src/lib/data.ts` (region_id grep)
- `data/cead/meta/index.json` (sample entries, confirmed `region_id` string format)
- `site/src/lib/newsFilterLogic.ts`/`.test.ts` (`parseFilterParams`, confirmed single consumer set: `news.astro`, `es/noticias.astro`)
- `site/package.json` (test script, no separate preview script)

### Secondary (MEDIUM confidence)
- None used — this research relied entirely on direct codebase reads (Primary) and reasoning from `29-DESIGN-SPEC.md`'s already-verified figures; no external web search was needed for a codebase-internal implementation phase

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new packages, native-only APIs, no external verification needed
- Architecture: HIGH — every claim is a direct `file:line` read from the real tree
- Pitfalls: HIGH — each pitfall is derived from an actual code-reading finding (state/closure race, existing CSS rule scope, existing chip data, existing redirect bug), not speculation
- The Q5 baseline number itself: **UNVERIFIED by this agent** — explicitly flagged; the orchestrator must run the prescribed BrowserOS steps and record a fresh number rather than trust either `29-DESIGN-SPEC.md §0` or `STATE.md`'s figures, which the research explicitly identifies as possibly stale/inconsistent with each other on the c4 question

**Research date:** 2026-07-30
**Valid until:** Effectively the life of this phase (implementation-only, no external ecosystem drift risk) — but the Q5 baseline must be re-measured at Wave 0 regardless of this document's age, per F-49
