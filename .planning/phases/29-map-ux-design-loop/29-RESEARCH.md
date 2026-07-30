# Phase 29: Map UX Design Loop - Research

**Researched:** 2026-07-30
**Domain:** Map control-shell UX (discoverability of a layer toggle + filter panel), native-HTML disclosure patterns (`<details>`/`<dialog>`), Leaflet pane/control z-index, WCAG keyboard/focus rules, BrowserOS-driven design-loop methodology
**Confidence:** MEDIUM-HIGH (codebase claims HIGH — read from source; Leaflet z-index HIGH — read from the installed package; competitor-pattern claims MEDIUM, explicitly deferred to the live click-through this phase performs; WCAG claims HIGH — official spec)

## Summary

Phase 29 does not write shipped map code. Its deliverable is a design spec plus an evidence pack (screenshots, per-iteration scoring, competitor findings) that Phase 30 implements against. The `no map control-shell code changes` constraint means every "apply" step in the design loop must produce and screenshot a **throwaway static HTML mockup**, not an edit to `site/src/components/map/*`. This repo already has an established throwaway-artifact convention for exactly this purpose: `/gsd:sketch` writes numbered variant directories under `.planning/sketches/NNN-name/` (`$HOME/.claude/get-shit-done/workflows/sketch.md:1-4`), each containing standalone HTML files opened directly in a browser — no Astro build, no dev server required for the mockup itself. No `.planning/sketches/` directory exists yet in this repo (confirmed empty), so Phase 29 is the first user of this convention here. Recommendation: reuse this exact structure — `.planning/sketches/029-map-controls/` with iteration subfolders (`iter-1/`, `iter-2/`) each holding a self-contained `desktop.html` and `mobile-375.html` that literally reproduce the current topbar/filter markup and CSS (copy-pasted, not imported, so editing them can never touch shipped code), screenshotted via BrowserOS `file://` navigation. This keeps the loop's "apply" step fast (no Astro rebuild between iterations) while still measuring against the real, current CSS as the iteration-0 baseline.

The measured baseline (already captured, not re-derived here) is unambiguous: `.filters-row` in `site/src/components/map/map.css:47-59` sets `overflow-x: auto` with `scrollbar-width: none` and a hidden `::-webkit-scrollbar` — the row is scrollable but gives the user zero visual affordance that more content exists off-screen. That single 13-line CSS block is the root cause of both the 507px desktop overflow and the 991px mobile overflow measured against the served build. The news-layer toggle chip is last in DOM order inside that same overflowing row (`FiltersRow.tsx:112-119`), which is why it is the specific control that goes missing.

The locked architectural constraint (STATE.md Key Decisions, 2026-07-29) rules out virtually every off-the-shelf popover/menu library: native `<details>`/`<dialog>` + CSS + Leaflet's own `L.Control` only. This is well-trodden ground — the repo already ships one working instance of exactly this pattern (`Legend.tsx:107-114`, collapsible `<details class="legend-mobile">`) and a second, different native-disclosure pattern for the nav hamburger (`PageHeader.astro:58-59`, a checkbox-driven zero-JS toggle, not `<details>`). Phase 29's spec should pick one discriminated pattern per surface (a `<dialog>` for a mobile bottom-sheet filter panel, `<details>` for a lower-stakes always-in-DOM disclosure) rather than inventing a third mechanism.

**Primary recommendation:** Design a control shell with two independently-discoverable, always-visible affordances — a persistent (non-buried) news-layer toggle chip and a dedicated filter entry point (FAB button on mobile opening a `<dialog>` bottom sheet; inline `<details>` panel or already-visible chip row on desktop) — validated per iteration against the five-point rubric in this document via `evaluate_script` in BrowserOS, with the police.uk/CityProtect click-through run between iteration 1 and iteration 2 to firm up at least one pattern claim before the design locks.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| News-layer toggle visibility | Browser / Client (CSS + markup) | — | Pure client-rendered control inside the React map island; no server logic involved |
| Filter panel disclosure | Browser / Client (native `<details>`/`<dialog>`) | — | Locked decision explicitly forbids a JS positioning library; must be resolvable with CSS + native elements only |
| Leaflet layer rendering (choropleth, pins, low-zoom dots) | Browser / Client (Leaflet panes) | — | Protected/untouched in Phase 30; Phase 29 must design *around* these panes, never inside them |
| Filter/facet vocabulary | Browser / Client (`familyDefs.ts`, `data.ts`) | — | MAPSH-07 requires the map and `/news/` facets share vocabulary via data, not a code dependency — Phase 29's spec should reference the same source, not redefine chip labels |
| Design-spec artifact itself | N/A (documentation) | — | Phase 29 produces a spec + sketches, not runtime code in any tier |

## Standard Stack

### Core (no new dependencies — locked decision)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Leaflet | 1.9.4 [VERIFIED: site/package.json:22, node_modules/leaflet/dist/leaflet.css] | Base map, `L.Control` API for any new control | Already the project's only map library; `L.Control` is the sanctioned extension point per the locked decision |
| Native `<details>`/`<dialog>` | HTML living standard | Filter panel disclosure, mobile bottom sheet / FAB expansion | Explicitly locked — "no popover/positioning library, no declarative react-leaflet layer components" (STATE.md Key Decisions, 2026-07-29) |
| CSS only (no JS positioning) | — | All layout/animation for the control shell | Same locked decision; zero new shipped JS dependencies (MAPSH-02) |

### Supporting (design-loop tooling only, not shipped)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| BrowserOS MCP | n/a (local tool, reachable per STATE.md:354) | Screenshot capture, `evaluate_script` measurement, live click-through of police.uk/CityProtect | Every iteration of the design loop; also the MAPUX-03 scoring instrument |
| `npx astro preview --port 4321 --host` | Astro 6.4.x preview server | Serves the **real** built site for the baseline screenshot and any spec verification against current markup | Iteration 0 (baseline) only — later iterations work against throwaway static HTML in `.planning/sketches/`, not the live build, per the "no code changes" constraint |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `.planning/sketches/` throwaway HTML | Editing `site/src/components/map/*` directly and reverting each iteration with git | Directly violates the roadmap's explicit ban ("No map control-shell code changes happen before the human acceptance gate") — rejected outright, not a real option |
| Native `<dialog>` bottom sheet | A CSS-only `<details>` positioned via `position: fixed` | `<dialog>` gets built-in modal semantics (backdrop, ESC-to-close, native focus containment per the HTML spec) for free; a `<details>` styled as a bottom sheet must hand-roll focus trapping and backdrop-click-to-close, which is more code for a worse accessibility baseline. Recommend `<dialog>` for the mobile filter sheet specifically. |
| `L.control()` custom control for the news toggle | Keep it as a React-rendered chip inside `FiltersRow` | Both are permitted by the locked decision. An `L.control()` places the toggle in Leaflet's own control container (verified z-index 800/1000, see below) which auto-avoids attribution/zoom-control collision; a React chip in the existing topbar needs no new abstraction and is more consistent with the current codebase. Recommend keeping it a React-rendered element in the topbar/FAB (matches MAPSH-05's "changes confined to `MapTopbar.tsx` and sibling control components") — flag as Claude's-discretion open point in the spec for Phase 30 to finalize during implementation planning. |

**Installation:** none — no new packages for this phase (design-only). Phase 30 also ships zero new frontend dependencies per the locked decision.

## Package Legitimacy Audit

Not applicable — this phase installs no packages. No `npm install` step exists in scope.

## Architecture Patterns

### System Architecture Diagram

```
[BrowserOS: baseline pass]
   npx astro preview --port 4321 --host
        │
        ▼
   real /map/ + /es/mapa/ pages (dist build)
        │  screenshot desktop (1296px) + 375px iframe
        ▼
[Baseline evidence: MAPUX-01]
        │
        ▼
[Iteration loop, ≥2 times — MAPUX-02]
   screenshot(prev) → Fable-agent redesign → apply (write throwaway
   .planning/sketches/029-map-controls/iter-N/{desktop,mobile-375}.html)
   → open file:// in BrowserOS → re-screenshot → score (MAPUX-03 rubric)
        │
        ├──► [Competitor click-through: MAPUX-04]
        │     police.uk + CityProtect, live BrowserOS pass,
        │     findings feed into iteration ≥2's redesign step
        │
        ▼
[Design spec + evidence pack written to phase dir — MAPUX-05]
        │
        ▼
[Fable-proxy acceptance gate — human review deferred, recorded pending]
        │
        ▼
   Phase 30 (implements spec against real MapTopbar.tsx / FiltersRow.tsx)
```

### Recommended Project Structure

```
.planning/
├── sketches/
│   └── 029-map-controls/
│       ├── MANIFEST.md              # design direction, iteration table, winner
│       ├── baseline/
│       │   ├── desktop-1296.png     # BrowserOS screenshot of the real build
│       │   └── mobile-375.png
│       ├── iter-1/
│       │   ├── desktop.html         # throwaway, self-contained (inline <style>)
│       │   ├── mobile-375.html
│       │   ├── desktop.png
│       │   ├── mobile-375.png
│       │   └── SCORE.md             # MAPUX-03 rubric results
│       ├── iter-2/
│       │   └── ...  (same shape; informed by MAPUX-04 competitor findings)
│       └── competitor-clickthrough/
│           ├── police-uk-notes.md
│           ├── cityprotect-notes.md
│           └── *.png
└── phases/29-map-ux-design-loop/
    └── 29-DESIGN-SPEC.md            # the accepted deliverable Phase 30 consumes
```

### Pattern 1: Native `<dialog>` as mobile filter bottom sheet

**What:** A `<dialog>` element styled with `position: fixed; bottom: 0` and `::backdrop`, opened via `showModal()` from a FAB button, closed via the native ESC key or a close button that calls `close()`.
**When to use:** Mobile filter panel (MAPSH-02's "bottom-sheet or FAB pattern" requirement) — needs modal focus containment, which `<dialog showModal()>` provides natively per the HTML Standard (the browser automatically restricts Tab-cycling to elements inside the dialog and returns focus to the invoker on close).
**Example:**
```html
<!-- Source: HTML Living Standard, dialog element section (https://html.spec.whatwg.org/multipage/interactive-elements.html#the-dialog-element) -->
<button id="filter-fab" aria-haspopup="dialog" aria-controls="filter-sheet">Filters</button>
<dialog id="filter-sheet" aria-label="Filter map by year and crime type">
  <form method="dialog">
    <!-- filter controls -->
    <button type="submit">Apply</button>
  </form>
</dialog>
<script>
  document.getElementById('filter-fab').addEventListener('click', () => {
    document.getElementById('filter-sheet').showModal();
  });
</script>
```
```css
#filter-sheet {
  position: fixed; inset: auto 0 0 0; margin: 0; width: 100%;
  border-radius: 16px 16px 0 0; max-height: 80vh;
}
#filter-sheet::backdrop { background: rgb(0 0 0 / 0.4); }
```

### Pattern 2: Always-visible news-layer toggle (never inside a disclosure)

**What:** A single labeled toggle button rendered directly in the topbar (or as a distinct `L.control()`), never nested inside a `<details>`, hamburger, or the filter `<dialog>`.
**When to use:** MAPSH-01 explicitly requires this control be "always visible" — the current bug (`FiltersRow.tsx:112-119`, last chip in an overflowing scroll row) is precisely a disclosure-by-accident failure, so the fix must NOT be "put it in the new filter panel," which would just relocate the same bug.
**Example:** Codebase precedent already exists for a persistent, non-scrolling overlay control — `.mode-toggle` in `map.css:104-111` is `position: absolute; z-index: 801` fixed to the top-right corner regardless of `.filters-row` scroll state. The spec should place the news toggle in the same positioning class of element (fixed-position, non-scrolling), not inside the scrollable chip row.

### Anti-Patterns to Avoid

- **Hiding the news toggle inside the new filter `<dialog>`:** MAPSH-01's whole point is that it must NOT be buried in a generic control. A filter sheet is a generic control from the user's perspective the first time they see it.
- **Re-implementing focus trapping by hand for a custom `<details>`-based "modal":** `<details>` has no native modal/focus-trap semantics — using it for anything that needs backdrop-modal behavior forces a hand-rolled `keydown` trap, which is exactly the kind of bespoke JS the locked decision (`no popover/positioning library`) is trying to avoid the *maintenance burden* of, even if it avoids the *dependency*. Use `<dialog>` for anything modal.
- **`<GeoJSON>` / `<Marker>`-as-JSX-child from react-leaflet:** explicitly banned for Phase 30 (STATE.md pitfall list) — Phase 29's spec must not describe or sketch a control that implies this pattern (e.g., a "layer control" drawn as a declarative React child of the map).
- **Positioning any new control at raw z-index values below 700 without checking pane occupancy:** see z-index table below — anything under `z-index: 700` risks being drawn under Leaflet's own popup pane.

## Leaflet Pane / Control Z-Index Constraints

Read directly from the installed package (`site/node_modules/leaflet/dist/leaflet.css`) — HIGH confidence, not training-data recall:

| Selector | z-index | Source |
|----------|---------|--------|
| `.leaflet-tile-pane` | 200 | `leaflet.css:109` |
| `.leaflet-pane` (default) | 400 | `leaflet.css:107` |
| `.leaflet-overlay-pane` | 400 | `leaflet.css:110` |
| `.leaflet-shadow-pane` | 500 | `leaflet.css:111` |
| `.leaflet-marker-pane` | 600 | `leaflet.css:112` |
| `.leaflet-tooltip-pane` | 650 | `leaflet.css:113` |
| `.leaflet-popup-pane` | 700 | `leaflet.css:114` |
| `.leaflet-zoom-box` | 800 | `leaflet.css:100` |
| `.leaflet-control` | 800 | `leaflet.css:134` |
| `.leaflet-top` / `.leaflet-bottom` (control container) | 1000 | `leaflet.css:141` |

**Codebase cross-check:** the existing control-shell classes already sit in this band — `.map-topbar { z-index: 800 }` (`map.css:32`), `.mode-toggle { z-index: 801 }` (`map.css:110`), `.legend { z-index: 700 }` (`map.css:131`). A new filter FAB/dialog or news toggle must land at **≥ 800** to sit above every Leaflet pane including popups (700), and should stay **below or clear of 1000** (Leaflet's own control container) unless it is deliberately meant to render above native zoom/attribution controls — which for a modal `<dialog>` opened via `showModal()` is moot, since the browser's top-layer rendering for `<dialog>` ignores document z-index entirely (it paints above everything, including `z-index: 2147483647` elements, per the HTML spec's "top layer" concept) [CITED: HTML Living Standard, dialog element — top layer]. This means a `<dialog>`-based bottom sheet is immune to Leaflet pane conflicts by construction — one more reason to prefer it over a `position: fixed` `<details>` for the modal filter panel.

**Practical rule for the spec:** any non-modal always-visible control (news toggle, FAB button) must be styled with `z-index: 800` or higher and positioned outside `.leaflet-top`/`.leaflet-bottom` containers to avoid competing with Leaflet's own zoom/attribution controls for the same corner.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Modal focus trap for the mobile filter sheet | A custom `keydown` Tab-cycle interceptor | `<dialog>` + `showModal()` | Native focus containment and ESC-to-close are implemented by the browser per spec; a hand-rolled trap is exactly the class of bug (missed Tab-order edge case) that produces the WCAG 2.1.2 violations MAPSH-03 tests for |
| Detecting whether a control is off-screen / undiscoverable | Eyeballing screenshots only | `element.getBoundingClientRect()` vs `element.closest('.scroll-container').clientWidth` via `evaluate_script` | Screenshots alone cannot prove "590px past the visible edge" — that number in this document's own baseline came from `scrollWidth`/`clientWidth` measurement, and the scoring rubric below formalizes the same technique for every iteration |
| Backdrop click-to-close on the filter sheet | Manual `click` listener computing whether the click target was outside the panel | `<dialog>`'s `::backdrop` pseudo-element + a `click` listener on `dialog` itself checking `event.target === dialog` | Standard, well-documented pattern; avoids reimplementing hit-testing that the browser already does via the backdrop layer |

**Key insight:** every "don't hand-roll" item in this phase is really the same insight restated: the locked decision bans a *library*, not native browser affordances — `<dialog>`'s built-in modal/focus/backdrop behavior is not a library, it's the platform, and using it fully (rather than reimplementing pieces of it in JS) is both more compliant with the locked decision's spirit (zero new shipped JS) and structurally safer for the WCAG gate.

## Common Pitfalls

### Pitfall 1: Scoring by opinion instead of the falsifiable rubric
**What goes wrong:** MAPUX-03 requires per-iteration scoring against concrete criteria; without a script, "iteration 2 feels better" gets recorded, which is not falsifiable and won't survive an Opus/Fable review.
**Why it happens:** Screenshots are visually persuasive even when the underlying DOM still overflows or still traps focus.
**How to avoid:** Run the `evaluate_script` rubric (below) on every iteration and paste the raw JSON result into that iteration's `SCORE.md` — never approximate from a screenshot.
**Warning signs:** A `SCORE.md` with no numbers, only prose adjectives.

### Pitfall 2: The `<dialog>` fails to render as modal because `showModal()` was never called
**What goes wrong:** A `<dialog open>` attribute (declarative) renders the dialog as a non-modal block-in-flow element — no backdrop, no focus containment, no top-layer promotion. A sketch that hardcodes `open` to make the screenshot look right will silently misrepresent the accessibility properties the spec is supposed to lock in.
**Why it happens:** `open` and `showModal()` look visually identical in a static screenshot; the difference only shows up in behavior (Tab key, backdrop click, ESC).
**How to avoid:** Any interactive sketch used for MAPUX-03's keyboard/focus scoring must call `showModal()` via a real click, not just ship the attribute; if a sketch is screenshot-only (non-interactive), label it explicitly as "visual only, not behavior-verified" in `SCORE.md` so it is never mistaken for a passing keyboard-trap check.
**Warning signs:** A sketch HTML file with `<dialog open>` in the markup and no accompanying `showModal()` call anywhere in its inline `<script>`.

### Pitfall 3: `scrollbar-width: none` hides the very affordance that would have signaled overflow
**What goes wrong:** This is the *actual, already-measured* root cause in the current code (`map.css:57-59`, `::-webkit-scrollbar { display: none }` + `scrollbar-width: none` on line 54). Any redesign that keeps a horizontally-scrolling chip row without adding a replacement affordance (fade-edge gradient, visible partial-chip peek, or arrow buttons) reproduces the exact same bug under a new visual skin.
**Why it happens:** Hiding scrollbars is a common polish choice (looks cleaner) that is usually paired with implicit affordances (partial next-item visible) which this layout does not have — the row currently clips content flush to the container edge.
**How to avoid:** If any iteration keeps a scrollable filter/chip row, the sketch must include a visible "there's more" signal (CSS `mask-image` fade, a chevron icon, or simply constraining the row's max-width so at least one chip is always partially cut off) and the rubric's "can they find the filters" criterion must specifically test for this rather than assuming an X-axis scroll container is self-evidently discoverable.
**Warning signs:** A redesign that removes the current `.filters-row` overflow but doesn't verify (via `scrollWidth > clientWidth` at 375px) that overflow can't recur with more chips added later (e.g. if a 9th family chip is added).

## Code Examples

### MAPUX-03 rubric — falsifiable, `evaluate_script`-executable

Each criterion below is designed to run inside BrowserOS's `evaluate_script` tool against a live page (the built `/map/` for the baseline, or the sketch's `file://` HTML for later iterations) and return a number or boolean — never a subjective read.

```javascript
// Source: derived from the baseline measurement methodology already used to capture
// the 507px/991px overflow numbers in this document's Summary — same technique,
// formalized into a reusable, falsifiable rubric. Run once per iteration, once at
// desktop width and once inside the 375px iframe.

function scoreControlShell() {
  const results = {};

  // 1. Can a first-time user find and activate the news layer?
  //    Falsifiable proxy: is the news toggle within the visible viewport bounds
  //    WITHOUT scrolling any ancestor, and is it clickable (not covered by
  //    another element at its own coordinates)?
  const newsToggle = document.querySelector('[data-role="news-toggle"], .ev-chip');
  if (newsToggle) {
    const r = newsToggle.getBoundingClientRect();
    const withinViewport = r.left >= 0 && r.right <= window.innerWidth && r.top >= 0 && r.bottom <= window.innerHeight;
    const topEl = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    const isTopmost = topEl === newsToggle || newsToggle.contains(topEl);
    results.newsToggleDiscoverable = withinViewport && isTopmost;
    results.newsToggleRect = r;
  } else {
    results.newsToggleDiscoverable = false;
    results.newsToggleMissing = true;
  }

  // 2. Can they find the filters? Falsifiable proxy: a filter entry point
  //    (button, FAB, or the filter row itself) is within viewport bounds
  //    without horizontal scroll of any ancestor.
  const filterEntry = document.querySelector('[data-role="filter-entry"], .filters-row, #filter-fab');
  if (filterEntry) {
    const scrollParent = filterEntry.closest('[style*="overflow"], .filters-row') || filterEntry;
    results.filterOverflowsContainer = scrollParent.scrollWidth > scrollParent.clientWidth;
    results.filterOverflowPx = scrollParent.scrollWidth - scrollParent.clientWidth;
  }

  // 3. Touch targets >= 44px at 375px (WCAG 2.5.5 / iOS HIG convention this repo
  //    already follows — .chip is height:44px per map.css:68).
  const targets = [...document.querySelectorAll('button, .chip, [role="button"], a')];
  results.touchTargetViolations = targets
    .map(el => el.getBoundingClientRect())
    .filter(r => r.width > 0 && r.height > 0 && (r.width < 44 || r.height < 44))
    .length;
  results.touchTargetsChecked = targets.length;

  // 4. No keyboard/focus trap: Tab from the first focusable element N+2 times
  //    (N = count of focusable elements) must eventually return to (or cycle
  //    through) every focusable element — never lock onto one element after
  //    the first repeat. Run as a separate synchronous sequence (see Pitfall 2
  //    for the dialog-specific caveat: inside an open <dialog>, cycling should
  //    stay WITHIN the dialog — that is correct trap behavior, not a bug).
  const focusables = [...document.querySelectorAll(
    'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"]), select, input, dialog[open] *'
  )];
  results.focusableCount = focusables.length;
  // (Actual Tab-sequence walk is performed by BrowserOS's own keyboard-press
  // tool driving real Tab keydown events — evaluate_script alone cannot
  // synthesize trusted Tab events. This function reports the candidate set;
  // the loop tool performs N presses and asserts document.activeElement
  // visits every candidate before repeating, OR stays confined to a single
  // open <dialog>'s candidates if one is open.)

  // 5. No map occlusion / Leaflet pane conflict.
  const mapPane = document.querySelector('.leaflet-map-pane, .leaflet-container');
  if (mapPane) {
    const mapRect = mapPane.getBoundingClientRect();
    const controls = [...document.querySelectorAll('.map-topbar, .legend, .mode-toggle, [data-role="filter-entry"], [data-role="news-toggle"]')];
    results.mapVisibleWidthPx = mapRect.width; // compare against viewport width per iteration
    results.controlZIndexes = controls.map(el => ({
      cls: el.className,
      zIndex: Number(getComputedStyle(el).zIndex) || 0,
    }));
    // Flag: any control z-index between 400-699 sits inside/below Leaflet's
    // overlay/shadow/marker panes and risks visual conflict; verified band is
    // documented in this file's "Leaflet Pane / Control Z-Index Constraints"
    // section (leaflet.css:107-114, 134, 141).
    results.zIndexViolations = results.controlZIndexes.filter(c => c.zIndex > 0 && c.zIndex < 700);
  }

  return results;
}

scoreControlShell();
```

**Sampling procedure per iteration:**
1. Run `scoreControlShell()` via `evaluate_script` at desktop width (viewport per the already-captured 1296px baseline).
2. Repeat inside the 375px iframe (per the directive's mandated mobile-emulation method — no native viewport resize in BrowserOS).
3. Drive a real Tab-key sequence via BrowserOS's keyboard tool for criterion 4, asserting `document.activeElement` against the `focusables` set returned above.
4. Record all four JSON blobs (desktop + mobile, before Tab-walk + after) verbatim in that iteration's `SCORE.md` — no paraphrasing.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| jQuery UI / custom-JS popover positioning libraries for filter panels | Native `<dialog>` with `showModal()` + CSS anchor/inset positioning | `<dialog>` reached full modern-browser baseline support years before this project started (broad support since ~2022 across evergreen browsers) | Directly enables the locked decision's "no popover/positioning library" constraint without sacrificing modal UX — this was not true a few years ago when `<dialog>` support was patchy |
| Custom `role="dialog"` + manual `aria-modal` + hand-rolled focus trap | Native `<dialog>` (browser-provided top-layer rendering + focus containment) | Same timeframe | Removes an entire class of accessibility bugs (missed focus-trap edge cases) that used to require a JS library (e.g. focus-trap) to get right |

**Deprecated/outdated:** Nothing library-specific to deprecate here since the stack has no UI-component library to begin with; the relevant "old approach" is a pattern (hand-rolled JS popovers), not a specific package.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | police.uk and CityProtect use a persistent layer-toggle + a modal/off-canvas filter panel on mobile (general pattern claim, not sourced from a fresh crawl in this research session) | Prior Art section below | MEDIUM — if their actual pattern differs materially, the "at least one design iteration informed by the click-through" requirement (MAPUX-04) could end up citing a stale or wrong pattern; mitigated because MAPUX-04 explicitly requires a **live** click-through in BrowserOS this same phase, which will supersede this assumption with direct observation |
| A2 | `<dialog>`'s browser "top-layer" rendering is immune to any z-index set by page CSS, including Leaflet's 400-1000 pane range | Leaflet Pane / Control Z-Index Constraints | LOW — this is a documented HTML spec behavior (top-layer promotion on `showModal()`), but was not independently verified against this repo's specific Leaflet version's canvas/SVG renderer interaction; if wrong, a modal dialog could theoretically still be occluded by a Leaflet canvas layer using `will-change` or `transform` stacking contexts, which should be spot-checked in the first sketch iteration |
| A3 | The recommended sketch location `.planning/sketches/029-map-controls/` will not collide with the numbering scheme `/gsd:sketch` itself would assign (next available `NNN`) | Recommended Project Structure | LOW — no existing sketches exist in this repo (confirmed via glob), so `029` (matching the phase number) is available; if a future `/gsd:sketch` invocation for an unrelated purpose runs first and claims `029` by its own auto-increment before this phase does, a rename is a one-line fix, not a design risk |

## Open Questions

1. **Should the news-layer toggle be an `L.control()` (Leaflet-native) or a React-rendered element inside `MapTopbar.tsx`?**
   - What we know: both are permitted by the locked decision; the codebase currently does the latter, and MAPSH-05 constrains Phase 30's changes to `MapTopbar.tsx` and sibling components (implying the React approach is the path of least resistance).
   - What's unclear: whether an `L.control()` would more robustly avoid the discoverability failure by being drawn in Leaflet's own control layer (auto-positioned relative to zoom/attribution) versus needing careful manual CSS to stay outside `.filters-row`'s scroll container.
   - Recommendation: default to the React-rendered approach (consistent with MAPSH-05 and the existing `.mode-toggle` precedent at `map.css:104-111`) and record this as a locked decision in the design spec; only reconsider if the first sketch iteration reveals a positioning conflict the CSS-only approach can't solve cleanly.

2. **Exact FAB icon/label and bottom-sheet trigger placement on mobile — not yet decided.**
   - What we know: MAPSH-02 requires a bottom-sheet or FAB pattern, not nested in the hamburger nav.
   - What's unclear: FAB corner (bottom-right is the near-universal Material convention, but this repo has no prior FAB precedent to match against).
   - Recommendation: default to bottom-right FAB (industry-standard corner, keeps it clear of the existing top-left search box and top-right `.mode-toggle`), verify no collision with `.legend` (`bottom: 32px; left: 16px` per `map.css:128-130`, opposite corner already) during the first sketch iteration.

3. **Should `?region=` deep-link support be designed for in Phase 29's spec, or left entirely to Phase 30?**
   - What we know: MAPSH-04 (Phase 30's requirement) needs `?region=` to behave like the working `?cut=`; STATE.md's Research Flag for Phase 30 calls this "an open decision."
   - What's unclear: whether the filter panel's redesign needs to reserve UI space for a "focused region" state indicator.
   - Recommendation: out of scope for Phase 29's control-shell spec — MAPUX's five requirements are entirely about discoverability/accessibility of the toggle and filter panel, not deep-link behavior. Flag explicitly in the design spec as "not addressed here; Phase 30 planner decides `?region=` UI treatment independently," so Phase 30 doesn't assume Phase 29 settled it.

## Prior Art — What to Look For in the police.uk / CityProtect Click-Through (MAPUX-04)

This section is deliberately a checklist, not a claim — MAPUX-04 requires the live pass to firm up these patterns, not for this research to assert them as fact.

**On police.uk (crime map, UK Home Office):**
- [ ] Screenshot the desktop layer/filter control area — is a "crime type" filter always visible, or does it require a click to reveal?
- [ ] Screenshot at 375px (iframe-emulated) — does the filter collapse into a bottom sheet, a full-screen overlay, or stay inline?
- [ ] Note whether there's a distinct, separately-labeled toggle for "show markers" vs. the underlying choropleth/heat layer (structurally similar to this project's news-pin vs. choropleth split).
- [ ] Check touch target sizes on any mobile filter chips (use `evaluate_script`'s `getBoundingClientRect()` — same technique as this repo's rubric).
- [ ] Tab through the filter control with a keyboard — does focus visibly move, and does it ever get stuck?

**On CityProtect (community crime-mapping product, used by many US police departments):**
- [ ] Screenshot the "layers" control — is it a distinct button from the "filter by date/type" control, or merged into one menu?
- [ ] At 375px, is there a FAB, a bottom sheet, or a hamburger-nested filter? (This is the exact pattern MAPSH-02 explicitly wants Phase 30 to AVOID if it's hamburger-nested — a negative finding here, if CityProtect does bury it in a hamburger, is itself a useful "don't repeat this" data point.)
- [ ] Note any z-index/occlusion issues observed live (a control drawn under the map, or a popup hidden behind a legend) — direct evidence for this project's own z-index rubric criterion 5.

**How findings feed the loop:** record findings as `.planning/sketches/029-map-controls/competitor-clickthrough/{police-uk,cityprotect}-notes.md` with screenshots, then explicitly cite at least one finding in iteration 2's redesign rationale — this satisfies MAPUX-04's "informs at least one design iteration" wording literally, not just in spirit.

## How to Prove an Iteration Actually Happened (MAPUX-02)

Per-iteration artifact checklist — a directory that has all of these is proof; a directory missing any of them is not a completed iteration:

1. **`desktop.html` + `mobile-375.html`** — the throwaway sketch markup for that iteration (self-contained, inline `<style>`, no build step).
2. **`desktop.png` + `mobile-375.png`** — BrowserOS screenshots of those files opened via `file://`, taken AFTER the sketch was applied (not the baseline).
3. **`SCORE.md`** — raw JSON output of `scoreControlShell()` (see Code Examples) for both viewports, plus the Tab-walk keyboard-trap result, dated and iteration-numbered.
4. **A one-paragraph delta note**: what changed from the previous iteration and why (should cite either a rubric failure from the prior `SCORE.md` or a competitor-click-through finding — never "just felt better").
5. **`MANIFEST.md` row**: each iteration gets one row in the sketch directory's manifest recording pass/fail per rubric criterion, so the final design spec can cite "iteration 2 fixed criteria 1 and 3, which iteration 1 failed" with a traceable source.

The **baseline** (iteration 0, already captured against the real served build) counts as the "before" state, not as one of the required ≥2 iterations — MAPUX-02's two iterations must both be genuine screenshot→redesign→apply→re-screenshot cycles against the sketches, distinct from the baseline capture.

## Accessibility

**`<details>` keyboard/focus requirements** [CITED: WHATWG HTML Living Standard, `details`/`summary` elements]:
- The `<summary>` element is natively focusable and activatable via Enter/Space without any `tabindex` or JS — this is why `Legend.tsx:108-114`'s existing `<details class="legend-mobile">` needs no additional keyboard wiring.
- Screen readers announce `<summary>` with an implicit `button`-like role and expose expanded/collapsed state via the `open` attribute — no manual `aria-expanded` needed, though adding it defensively is harmless.
- **No native focus trap** — `<details>` content becomes part of normal tab order when open; this is CORRECT non-modal behavior (a WCAG pass, not a failure) for a disclosure that doesn't need to block interaction with the rest of the page, but it is WRONG behavior to rely on if the design spec calls the filter panel "modal" — a modal filter panel must use `<dialog>` instead (see Pattern 1).

**`<dialog>` keyboard/focus requirements** [CITED: WHATWG HTML Living Standard, `dialog` element, "The dialog element" / "Focusing steps"]:
- `showModal()` (not the declarative `open` attribute) is required to get: (a) top-layer rendering above all other content regardless of z-index, (b) a `::backdrop` pseudo-element, (c) automatic initial focus on the dialog's first focusable descendant (or the dialog itself if none), (d) Tab/Shift+Tab cycling confined to the dialog's focusable descendants while open, (e) ESC key closes the dialog and fires a `cancel` event, and (f) focus returns to the invoking element on close.
- These are all **native browser behaviors** — none require custom JS, which is exactly why `<dialog>` satisfies the locked "no popover/positioning library" constraint while still being fully WCAG-compliant for a modal use case.

**Testable definition of "no keyboard trap" (WCAG 2.1.2, Success Criterion, Level A)** [CITED: W3C WCAG 2.1, SC 2.1.2 "No Keyboard Trap"]:
> "If keyboard focus can be moved to a component of the page using a keyboard interface, then focus can be moved away from that component using only a keyboard interface... "

Testable procedure for this project (matches the rubric's criterion 4):
1. Enumerate all focusable elements in DOM order (the `focusables` query in `scoreControlShell()`).
2. Simulate `focusables.length + 2` real Tab keypresses (via BrowserOS's keyboard tool, which dispatches trusted events — `evaluate_script` alone cannot synthesize a trusted `Tab` keydown that triggers native browser focus-advance behavior).
3. Assert: every element in the `focusables` set receives focus at least once, AND focus does not remain fixed on a single element for 2+ consecutive Tab presses (the actual signature of a trap) — UNLESS that element is inside a currently-open `<dialog>`, in which case confinement to the dialog's own focusable set is the CORRECT, spec-defined behavior and must be scored as a pass, not a trap.
4. Additionally: press Shift+Tab from the first element and assert focus moves backward (proves the trap isn't one-directional only).

This distinguishes intentional, spec-compliant `<dialog>` focus confinement from an actual accessibility bug — a naive "does focus ever repeat" check would incorrectly flag every correctly-implemented modal dialog as a keyboard trap.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| BrowserOS MCP (`http://127.0.0.1:9200/mcp`) | Entire design loop (screenshots, evaluate_script, click-through) | Yes — confirmed reachable, `list_pages` returned 38 open tabs (STATE.md:354, checked 2026-07-30 at Phase 28 close) | n/a | Directive's own fallback: retry once, else mark Phase 29 BLOCKED and skip 30 (STATE.md:367) — not needed, already confirmed reachable |
| `npx astro preview --port 4321 --host` | Baseline screenshot capture (MAPUX-01) | Yes — Astro 6.4.x already the project's build tool | 6.4.x [CITED: CLAUDE.md Technology Stack] | none needed |
| Node.js 20/22 LTS | Astro build/preview | Yes | v22.21.1 [VERIFIED: `node --version` this session] | none needed |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none — all required tooling confirmed present.

## Validation Architecture

**Skip reasoning:** `workflow.nyquist_validation` is `true` in `.planning/config.json` (present, not `false`), so this section is normally required. However, Phase 29 ships **zero application code and zero automated test files** — its entire deliverable is a design spec and a sketches directory. There is no `pytest`/`vitest` surface for this phase to add to, and no shipped behavior for a unit test to pin. The "test framework" for this phase's five requirements IS the BrowserOS `evaluate_script` rubric documented above (Code Examples section) — that rubric is this phase's test suite, executed manually per iteration rather than via `npm test`.

### Phase Requirements → Verification Map

| Req ID | Behavior | Verification Type | Executable Procedure | Artifact Exists? |
|--------|----------|-------------------|----------------------|-------------------|
| MAPUX-01 | Baseline captured against real build, desktop + 375px | BrowserOS screenshot + manual overflow measurement | `evaluate_script` reading `scrollWidth`/`clientWidth` (already run once to produce this doc's Summary numbers) | Already done — see Summary |
| MAPUX-02 | ≥2 full iterations, each a real screenshot→redesign→apply→re-screenshot cycle | Artifact-count check | Verify `.planning/sketches/029-map-controls/iter-{1,2}/` both contain all 5 items from "How to Prove an Iteration Actually Happened" | Wave 0 gap — directory doesn't exist yet |
| MAPUX-03 | Per-iteration scoring against 5 concrete criteria | `evaluate_script` rubric | `scoreControlShell()` (Code Examples) + BrowserOS keyboard Tab-walk | Wave 0 gap — script must be run live per iteration, not pre-computed |
| MAPUX-04 | Live competitor click-through informs ≥1 iteration | Artifact + citation check | Verify `competitor-clickthrough/*.md` exists AND iteration 2's delta note cites a specific finding from it | Wave 0 gap |
| MAPUX-05 | Design spec + acceptance gate recorded | Document existence + STATE.md entry | Verify `29-DESIGN-SPEC.md` exists in the phase dir and a Fable-proxy acceptance line is added to STATE.md (per the directive's gate amendment 1, since human review is deferred in this unattended run) | Wave 0 gap |

### Sampling Rate
- **Per iteration:** run the full `scoreControlShell()` rubric (desktop + 375px + Tab-walk) — this IS the "quick run" for this phase, no faster proxy exists since the criteria are inherently browser-behavioral.
- **Phase gate:** all 5 requirements' artifacts present and cross-referenced before the design spec is marked accepted.

### Wave 0 Gaps
- [ ] `.planning/sketches/029-map-controls/` directory structure (MANIFEST.md, baseline/, iter-1/, iter-2/, competitor-clickthrough/) — none of it exists yet.
- [ ] The rubric script itself needs to be saved as a real `.mjs` file (e.g. `.planning/sketches/029-map-controls/score.mjs` exporting the `scoreControlShell` function as a string to inject via `evaluate_script`) rather than inlined ad hoc each time — this also satisfies the ban on embedding fragile shell-escaped logic (F-36 precedent: keep logic in a real file, not a shell-quoted inline script).
- [ ] No Wave 0 test-framework install needed — there is no `npm test`/`pytest` surface for this phase.

## Security Domain

**Skip reasoning:** `security_enforcement: true` in `.planning/config.json`, but Phase 29 introduces no new endpoints, no new data handling, no new user input processing, and no shipped code at all (design spec + throwaway static HTML mockups that are never deployed or served in production). None of the ASVS categories below apply to a documentation-only deliverable; recorded explicitly rather than silently omitted, per this document's own honesty requirement.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | No auth surface touched |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A |
| V5 Input Validation | No | The filter controls sketched here handle no new untrusted input beyond what Phase 27/28's `newsFilterLogic.ts` already validates; Phase 29 doesn't touch that code |
| V6 Cryptography | No | N/A |

**Known Threat Patterns for this stack:** None applicable to a static-HTML-sketch-only phase. Phase 30 (which DOES ship code) should re-run this section at its own research step, particularly checking that any new `<dialog>`-embedded form doesn't introduce a new client-side XSS sink analogous to the `set:html` pattern Phase 27/28 already had to guard (F-24/F-38 precedent in STATE.md) — flagged here as a forward note for Phase 30's research, not a Phase 29 requirement.

## Project Constraints (from CLAUDE.md)

- Astro 6.4.x + React islands, pre-rendered static HTML — any sketch that later graduates into Phase 30's real implementation must remain fully static-HTML-indexable (not applicable to the throwaway sketches themselves, which are never deployed).
- `client:only="react"` on the map island (per CLAUDE.md "What NOT to Use" — never `client:load` on the map island) — the design spec should explicitly reaffirm this for Phase 30's benefit, since a redesigned control shell is exactly the kind of change that could accidentally regress the client directive if a control gets hoisted outside the island.
- No new shipped JS dependencies — reaffirmed by both CLAUDE.md's existing stack table and the v2.1-specific locked decision; this research recommends zero new packages, consistent with both.
- Editorial/legal constraint (never label territories safe/dangerous) — not implicated by a control-shell UX redesign, noted only for completeness.

## Sources

### Primary (HIGH confidence)
- `site/node_modules/leaflet/dist/leaflet.css` (installed package, read directly) — all Leaflet pane/control z-index values
- `site/src/components/map/map.css`, `MapTopbar.tsx`, `FiltersRow.tsx`, `Legend.tsx` (read directly this session) — all codebase claims, baseline root-cause analysis
- `.planning/ROADMAP.md:359-393` (Phase 29 + Phase 30 sections) — requirements, gates, risk annotations
- `.planning/REQUIREMENTS.md:72-86` (MAPUX-01..05, MAPSH-01..07 full text)
- `.planning/STATE.md` §§ Key Decisions, Phase 28 Outcome, Phase 29 readiness, Fable Decisions F-01..F-38
- `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md` (BrowserOS constraints, model routing, gate amendments)
- `$HOME/.claude/get-shit-done/workflows/sketch.md` — throwaway-sketch convention (`.planning/sketches/NNN-name/`)
- W3C WCAG 2.1, Success Criterion 2.1.2 "No Keyboard Trap" — official spec text quoted verbatim
- WHATWG HTML Living Standard — `dialog` and `details`/`summary` element behavior (top-layer rendering, `showModal()` focus semantics, native `<summary>` focusability)

### Secondary (MEDIUM confidence)
- General claims about police.uk/CityProtect UX patterns in the "Prior Art" section are explicitly NOT sourced from a fresh crawl this session — they are framed as a checklist for the live MAPUX-04 click-through to confirm or refute, not asserted as verified fact.

### Tertiary (LOW confidence)
- None — every claim in this document is either read directly from the codebase/installed package, cited to an official spec, or explicitly flagged in the Assumptions Log / Prior Art section as needing the phase's own live verification.

## Metadata

**Confidence breakdown:**
- Standard stack / locked constraints: HIGH — read verbatim from STATE.md Key Decisions and the installed `package.json`
- Architecture (z-index, disclosure patterns): HIGH — Leaflet values read from the installed package; `<dialog>`/`<details>` behavior cited to the HTML spec
- Pitfalls: HIGH — Pitfall 3 (scrollbar hiding) is a direct file:line finding (`map.css:47-59`), not inference
- Competitor UX patterns: MEDIUM, by design — deliberately deferred to the phase's own live click-through (MAPUX-04) rather than asserted here

**Research date:** 2026-07-30
**Valid until:** 30 days (stable domain — native HTML APIs and an already-installed Leaflet version do not shift quickly); the competitor-pattern checklist has no expiry since it's explicitly a "go verify live" instruction, not a claim with a shelf life.
