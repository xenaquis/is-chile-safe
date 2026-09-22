---
phase: 30-map-control-shell-rework
reviewed: 2026-07-30T19:20:00Z
depth: deep
diff_base: 3b45ca4431fdce08b27cd10efd63595218a843d5
files_reviewed: 15
files_reviewed_list:
  - site/scripts/phase30-gate.mjs
  - site/src/components/map/EntryPointsRail.tsx
  - site/src/components/map/FilterFields.tsx
  - site/src/components/map/FilterSheet.tsx
  - site/src/components/map/FiltersRow.tsx (deleted)
  - site/src/components/map/MapIsland.tsx
  - site/src/components/map/MapTopbar.tsx
  - site/src/components/map/NewsToggle.tsx
  - site/src/components/map/map.css
  - site/src/config/i18n.ts
  - site/src/layouts/BaseLayout.astro
  - site/src/lib/mapFilterDefs.test.ts
  - site/src/lib/mapFilterDefs.ts
  - site/src/lib/regionParam.test.ts
  - site/src/lib/regionParam.ts
findings:
  critical: 0
  high: 2
  medium: 7
  low: 4
  total: 13
status: issues_found
---

# Phase 30: Adversarial Code Review

**Depth:** deep (full diff read, cross-file prop trace, gate executed, gate mutation-analysed)
**Scope:** `git diff 3b45ca443… -- site/`
**Tree state at review end:** clean (`git status --porcelain` empty; `dist/` is gitignored)

## What was verified by execution, not by claim

| Check | Method | Result |
|---|---|---|
| MAPSH-05 layer confinement | `git diff --exit-code 3b45ca443… -- ChoroplethLayer.ts IncidentPinLayer.ts LowZoomDotLayer.ts` run independently of the gate | **exit 0 — byte-identical** |
| No declarative react-leaflet | grep for `<GeoJSON`, `<Marker`, `from 'react-leaflet'` across `site/src` | none present |
| `?cut=` block unchanged | diff hunk shows `MapIsland.tsx:227-233` as pure context lines | **byte-identical** |
| vitest | `npx vitest run` | **45 passed / 5 files** (37 baseline + 8 new) |
| `astro check` | executed | **4 errors / 0 warnings**, all at `ComparatorPairsLinks.astro:28` — baseline held |
| `phase30-gate.mjs` | `npm run build && node scripts/phase30-gate.mjs` | 9/9 PASS, exit 0 |
| Prop chain, all 4 hops | read every prop through `MapIsland → MapTopbar → {EntryPointsRail, FilterSheet} → FilterFields` | **no prop dropped on either surface** — `year/onYearChange/crimeFamily/onFamilyChange/mode/onModeChange` are all forwarded to *both* the rail (`MapTopbar.tsx:52-60`) and the sheet (`MapTopbar.tsx:61-69`), and both pass them straight through to `FilterFields`. No `() => {}` stubs anywhere. |
| Homicide layer end-to-end | `mapFilterDefs.ts:31` (`key:'homicidios'`, `familyIndex:null`) → `FilterFields.tsx:58` `onFamilyChange(key, familyIndex)` **key-first** → `MapIsland.tsx:448` `setCrimeIsHomicide(key === 'homicidios')` → `MapIsland.tsx:330/465` `buildStyleMapFromHomicide` | **intact**; pinned by `mapFilterDefs.test.ts` Tests 5–7 |
| Mode recolor, branch-by-branch vs base SHA | composite → `buildStyleMapFromCompositeIndex`; family+homicide → `…FromHomicide`; family+index → `…FromFamily`; family+null → `…FromLevel`; then `applyStyleMap` | **all four branches present, same order, same guards** (`MapIsland.tsx:459-473`). Nothing dropped or reordered. |
| `?region=` semantics | `regionParam.ts` + `MapIsland.tsx:235-251` | own parser (not `parseFilterParams`) ✓ · single-value ✓ · yields to a valid `?cut=` ✓ · 100 ms defer ✓ · reads the **local `idx`**, not `communeIndex` state ✓ · never calls `setSelected` ✓ · `bounds.isValid()` guard, no fetch, no console error on unknown ✓ |
| No `document` keyboard listener (F-49 / c4) | grep of `EntryPointsRail.tsx` + built chunk | Escape is a container-scoped React `onKeyDown` (`EntryPointsRail.tsx:89-101`); the only `document` listener is `mousedown`, `offsetParent`-guarded and cleaned up (`:78-87`). **No `keydown` string in the island's own source.** |
| `openId` drives ARIA declaratively | `EntryPointsRail.tsx:63,125,138` | `open` and `aria-expanded` both render from `openId`; **no `setAttribute` anywhere in the rail** ✓ |
| `showModal()` never `open` | `FilterSheet.tsx:53`, and the `<dialog>` JSX carries no `open` attr | ✓ |
| `.filters-row` / `.mode-toggle` removal | grep `site/src` + built `dist/_astro/*` | fully removed, **zero orphaned references**; `.ev-dot-mini`, `.chip`, `.chip.select` retained ✓ |
| z-index ladder | built CSS | legend **750**, news-toggle **800**, FAB **800**, open panel **801**, dialog **no z-index** ✓ |

Two known-accepted items (legend bands not varied per family; residual sub-44px header/footer/skip-link/Leaflet-attribution targets) are **not** re-reported below.

---

## HIGH

### H-01 — `--map-topbar-h: 108px` is a single hardcoded value; the partial-year badge lands *inside* the topbar at 481–1023 px

**File:** `site/src/components/map/map.css:22` (definition), consumed at `map.css:1019`

Premortem §11 asked for "a real **per-band** value". What shipped is one constant, and the arithmetic only works at ≥1024 px.

`.entry-points-rail` is `flex-wrap: wrap` (`map.css:30-35`) and `.entry-state-summary` carries `flex-basis: 100%` (`map.css:93`), which **forces the summary onto its own row**. That `flex-basis` is only overridden at `@media (min-width: 1024px)` (`map.css:98-103`). So:

| Band | `.map-topbar` height (8 pad + row1 + 8 gap + rail + 8 pad + 1 border) | badge `top` = 108+8 | Result |
|---|---|---|---|
| ≥1024 | 8+44+8+**44**+8+1 = **113** | 116 | 3 px clearance |
| **481–1023** | 8+44+8+**(44+8+~14)** +8+1 = **~135** | 116 | **badge starts ~19 px above the topbar's bottom edge → overlap** |
| ≤480 | rail is `display:none` (`map.css:41-45`); row1 is column (`map.css:355-360`): 8+44+6+44+8+1 = **111** | 116 | 5 px clearance |

The badge is `z-index: 800` and later in DOM than `.map-topbar` (also 800), so it paints **over** the topbar, on top of `.entry-state-summary`. It renders whenever `payload.partial_year === true` (`MapIsland.tsx:476-482`) — i.e. by default on the newest partial year. 481 and 639 are two of the five bands the phase measures, and `score.mjs` has no criterion for this, so the gate set stays green.

The 108 px value is consistent with having been tuned at 1296 px only — the one width where the summary does not wrap.

**Fix:** make the variable per-band instead of global:
```css
.map-stage { --map-topbar-h: 140px; }              /* rail + wrapped summary */
@media (min-width: 1024px) { .map-stage { --map-topbar-h: 116px; } }
@media (max-width: 480px)  { .map-stage { --map-topbar-h: 114px; } }
```
Better still, drop the magic number: put `.partial-year-badge` in normal flow under `.map-topbar` (or set the variable from `MapTopbar` via a `ResizeObserver` on the topbar element) so it cannot desynchronise again. Add a browser assertion to 30-06: `badge.getBoundingClientRect().top >= topbar.getBoundingClientRect().bottom` at all five widths.

### H-02 — `role="radiogroup"` / `role="radio"` shipped with no roving tabindex and no arrow-key navigation

**File:** `site/src/components/map/FilterFields.tsx:44-73` (FamilyField), `:83-107` (ModeField)

Spec §5 mandated `radiogroup`/`radio` and the phase shipped the roles — but not the interaction contract they promise. All nine family radios are plain `<button role="radio">` with default `tabIndex=0`, so:

- a screen reader announces "radio button, 1 of 9" and **arrow keys do nothing** (WAI-ARIA APG requires ←/→/↑/↓ to move and select within a radiogroup);
- every radio is its own tab stop, so a keyboard user must press Tab nine times to traverse one dimension — the opposite of the single-stop-per-group contract `radiogroup` advertises.

This is squarely inside MAPSH-03 ("keyboard-trap-free by construction" was evidenced; *operable per the announced pattern* was not). `score.mjs` c4 counts focusables and negative tabindexes only, so it is blind to this by design.

There is a real tension with F-49 here: implementing arrow keys means a `keydown` handler, which the baseline correction warns could redden c4 if the string reaches scannable script. That tension must be resolved deliberately, not by shipping the roles without the behaviour.

**Fix (either, but pick one and record it):**
1. Implement the pattern: roving tabindex (`tabIndex={isActive ? 0 : -1}`) plus a **container-scoped React `onKeyDown`** on the radiogroup `<div>` handling `ArrowLeft/Right/Up/Down` + `Home/End` — same construction as the rail's Escape handler, so no `document` listener is added. Note `negativeTabindexCount` in `score.mjs` filters out non-rendered elements only, so roving `-1` on *visible* radios **will** raise it — verify against c4 before committing.
2. Or drop the radio roles and ship `<button aria-pressed>` inside a `role="group"` (which is valid for `aria-pressed` buttons — spec §5's prohibition is specifically on `group` as a parent of `role="radio"`), and record the deviation from spec §5 with its reason.

---

## MEDIUM

### M-01 — The persistent state summary disappears entirely at ≤480 px

**File:** `site/src/components/map/map.css:41-45` + `EntryPointsRail.tsx:198-200`

Spec §2 item 4 makes the state summary one of the four accepted design elements: *"A persistent state summary keeps the active selection legible **without opening any panel**."* It lives inside `.entry-points-rail`, and the rail is `display: none` below 481 px. `EntryPointsRail.tsx:43-51,112-113` even computes a dedicated `narrow` band string (`"Todos · 2025"`) that **can never render** — dead code proving the surface was intended and then lost when the rail was hidden wholesale.

`FilterSheet` renders no summary. So at 320/375 px the user cannot see the active year or crime type without opening the modal — the exact "state is invisible" failure the summary exists to prevent, at the band where it matters most.

**Fix:** render the summary outside the rail, or render a second copy in the FAB row:
```tsx
// FilterSheet.tsx, alongside the FAB
<span className="entry-state-summary entry-state-summary-mobile" aria-live="polite">
  {`${fLabelShort} · ${year}`}
</span>
```
Verify at 320/375 that `el.scrollWidth - el.clientWidth <= 8` (premortem §2 — a truncating ellipsis trips `score.mjs`'s overflow scan and fails c2).

### M-02 — `aria-expanded` is set imperatively on an element whose `aria-expanded` is also rendered from JSX

**File:** `site/src/components/map/FilterSheet.tsx:91` (JSX `aria-expanded="false"`) vs `:54,59,64` (`fab.setAttribute('aria-expanded', …)`)

This is premortem §7's banned pattern, avoided in `EntryPointsRail` and then re-introduced on the FAB. It happens to work today only because the JSX value is a **constant literal** — React's DOM reconciler skips props whose value is unchanged between renders, so it never overwrites the imperative value. That is an implementation detail, not a contract. The instant anyone makes that attribute dynamic, conditional, or moves the FAB behind a `key` change / remount, the sheet will report `aria-expanded="false"` to screen readers while open.

The header comment (`FilterSheet.tsx:11-15`) documents the three-site imperative approach as deliberate, which makes it likely to survive future review unexamined.

**Fix:** lift it to state, matching the rail:
```tsx
const [open, setOpen] = useState(false);
// …
<button ref={fabRef} aria-expanded={open} … />
// handlers: setOpen(true) / setOpen(false) instead of setAttribute
```

### M-03 — The bottom sheet cannot be dismissed by tapping the backdrop, and the source comment claims it can

**File:** `site/src/components/map/FilterSheet.tsx:12-14`, `:95-100`

The comment states the `close` event *"also fires on Escape **and backdrop dismissal**"*. A native `<dialog>` opened with `showModal()` does **not** close on backdrop click unless it carries `closedby="any"` (or a manual light-dismiss handler). No such attribute is set and no backdrop handler exists.

Consequence on the ≤480 px surface — the only surface this component serves — the sole dismissal affordance is the 44×44 `×` button, since phones have no Escape key. Tapping the dimmed backdrop, which is the near-universal mobile bottom-sheet gesture, does nothing.

**Fix:** add light dismiss and correct the comment:
```tsx
<dialog … onClick={(e) => { if (e.target === dialogRef.current) dialogRef.current.close(); }}>
```
(the `close` event handler already restores focus and clears `aria-expanded`, so no other wiring changes). `closedby="any"` is the declarative alternative where support permits.

### M-04 — Mode option labels were silently rewritten, and now contradict the state summary that describes them

**File:** `site/src/components/map/FilterFields.tsx:95,104` vs `EntryPointsRail.tsx:38-41`

The base-SHA mode toggle rendered `Índice` / `Por delito` (ES) and `Index` / `By crime` (EN) (`MapIsland.tsx:443-467` at the base SHA). `ModeField` ships `Índice compuesto` / `Por familia` and `Composite index` / `By family` — a user-facing copy change that no spec line, plan or gate requested, in a phase whose brief was to move markup, not to redecide labels.

Worse, `EntryPointsRail.modeLabel()` still emits the **old** strings, so the state summary reads `Índice · …` while the selected option reads `Índice compuesto`, and `Por delito · …` while the option reads `Por familia`. Two different names for the same state, on screen simultaneously at ≥640 px.

Also note `ModeField`'s `aria-label` is `'Modo' / 'Map mode'` while `i18n.ts` now defines `map_entry_mode` for exactly this string — the constant is bypassed and the ES/EN pair is hardcoded.

**Fix:** restore the base-SHA labels in `ModeField`, or update `modeLabel()` to match — and source both from a single exported constant so they cannot drift:
```ts
export const MODE_LABELS = {
  es: { composite: 'Índice', family: 'Por delito' },
  en: { composite: 'Index',  family: 'By crime'  },
} as const;
```
Use `strings.map_entry_mode` for `ModeField`'s `aria-label`.

### M-05 — Gate assertion 6 cannot fail for any of the controls spec §3 actually pins

**File:** `site/scripts/phase30-gate.mjs:279-318`

The assertion asks only whether the *strings* `z-index:750`, `z-index:800`, `z-index:801` appear **somewhere** in the bundled CSS. It binds no value to a selector. Proof it cannot fail on a broken tree: `z-index:800` is emitted by the pre-existing `.map-topbar` rule (`map.css:120`) **and** by the pre-existing `.partial-year-badge` rule (`map.css:1022`). Delete `z-index: 800` from `.news-toggle` *and* from `.filter-fab` — the two controls spec §3 pins as "explicit number, never `auto`" and "set on the base rule, not only inside the media query" — and **assertion 6 still passes**. The same holds for the dialog: nothing asserts `.filter-sheet` has *no* z-index, which spec §3 calls a defect.

Only the `.legend{…z-index:700` sub-check is genuinely falsifiable, and it is additionally fragile: it matches the literal minified token `.legend{`, so any future selector grouping (`.legend,.legend-x{`) makes it silently unfalsifiable too.

**Fix:** assert value-per-selector on the whitespace-stripped CSS:
```js
const rules = [
  ['.news-toggle{',  'z-index:800'],
  ['.filter-fab{',   'z-index:800'],
  ['.legend{',       'z-index:750'],
];
// and: block for '.filter-sheet{' must NOT contain 'z-index:'
```
Prove each direction by temporarily breaking the rule before the plan is signed off.

### M-06 — Gate assertions 5 and 7 are weaker than the constraints they claim to enforce

**File:** `site/scripts/phase30-gate.mjs:245-263` (a5), `:330-366` (a7)

- **a5** passes if the substring `showModal(` appears in any `dist/_astro/*.js`. It cannot distinguish `showModal()` from `<dialog open>` *coexisting*, and it would pass on a string literal or dead code. Spec §5 says this explicitly: *"`grep -c "showModal"` cannot distinguish the two — verify with `dialog.matches(':modal') === true`."* The gate shipped the exact check the spec named as insufficient.
- **a7** scans only `site/src/components/map/**`. F-47 says *"No declarative react-leaflet layer component may be introduced **anywhere**."* A `<GeoJSON>` in `src/components/`, `src/pages/` or `src/lib/` passes the gate. It also omits `.jsx`/`.js`.

**Fix:** a5 → keep the substring check as a cheap smoke test but mark it necessary-not-sufficient in the header comment, and move the real proof into 30-06's browser pass (`dialog.matches(':modal')`), which is already the only place it can be observed. a7 → change `MAP_SRC_DIR` to `path.join(SITE_ROOT,'src')` and add `.jsx`, `.js` to the extension list; additionally scan `package.json` for a `react-leaflet` dependency.

### M-07 — `?region=` matches `region_id` by exact string, so common padded forms silently no-op

**File:** `site/src/lib/regionParam.ts:26-28`

`region_id` in `data/cead/meta/index.json` is unpadded (`"1"…"16"`, verified). The resolver does `c.region_id === focusRegion`, so `?region=05`, `?region=013` or `?region=13 ` return `null` and the deep link degrades to "no focus". F-48's silent-degradation rule was written for *unknown* values; a **valid region expressed in the padded form used elsewhere in Chilean CUT data** is not an unknown value, and the failure is indistinguishable from the feature never having worked (premortem §12's exact concern). Note the premortem's own worked example uses `?region=05`.

Relatedly, the precedence rule ("a valid `?cut=` wins") lives in `MapIsland.tsx:237` and has **no test** — `regionParam.test.ts` Test 4 asserts the resolver *ignores* `cut`, which is the opposite side of the contract and would still pass if the `MapIsland` guard were deleted.

**Fix:**
```ts
const raw = new URLSearchParams(search).get('region');
if (!raw) return null;
const norm = raw.trim().replace(/^0+(?=\d)/, '');
const cuts = idx.filter((c) => c.region_id === norm).map((c) => c.cut);
```
Add a vitest case for `?region=05` → the Valparaíso CUTs, and extract the precedence guard into a tiny pure helper (`shouldApplyRegionFocus(search)`) so it can be tested directly.

---

## LOW

### L-01 — News toggle `aria-label` is not the string spec §6 prescribes

**File:** `site/src/components/map/NewsToggle.tsx:24`

Spec §6: *"News toggle: `aria-pressed` + `aria-label` (`Mostrar incidentes recientes de prensa en el mapa`)."* The implementation sets `aria-label={strings.map_news_toggle_long}` — "Noticias recientes" — which merely duplicates the visible text and drops the descriptive purpose the spec pinned. (WCAG 2.5.3 is still satisfied at ≤640 px because the short visible label "Noticias" is a substring of the accessible name.)

**Fix:** add `map_news_toggle_aria` to `i18n.ts` (`Mostrar incidentes recientes de prensa en el mapa` / `Show recent press incidents on the map`) and use it for `aria-label`.

### L-02 — Focus return after dialog close is unguarded against a hidden FAB

**File:** `site/src/components/map/FilterSheet.tsx:60,68`

`fab.focus()` is called unconditionally. `.filter-fab` is `display: none` above 480 px (`map.css:1088,1105-1111`), so a viewport widening or orientation change while the sheet is open leaves the close path calling `.focus()` on a non-rendered element — focus falls to `<body>`. This is the same failure mode the rail's `offsetParent` guard (`EntryPointsRail.tsx:80`) was added to prevent; the sheet did not receive the equivalent treatment.

**Fix:** `if (fab.offsetParent !== null) fab.focus(); else document.querySelector<HTMLElement>('.entry-points-rail summary')?.focus();`

### L-03 — `AVAILABLE_YEARS` offers a year with no payload, and Test 8 now pins that

**File:** `site/src/lib/mapFilterDefs.ts:38-41`, `site/src/lib/mapFilterDefs.test.ts:46-49`

`AVAILABLE_YEARS[0] === new Date().getFullYear()` = 2026, but `site/public/data/cead/` stops at `map-payload-2025.json`. Selecting the dropdown's first option produces a failed fetch and the "Datos no disponibles para este año." toast (`MapIsland.tsx:278`). The behaviour is **pre-existing** (ported verbatim from `FiltersRow.tsx`), but Test 8 now asserts it as correct, so the defect is locked in rather than merely inherited.

**Fix (out of this phase's scope, but record it):** derive the year list from the payload manifest, or clamp to the newest year with a shipped payload; change Test 8 to assert `AVAILABLE_YEARS[0]` has a corresponding file on disk.

### L-04 — Gate assertion 1 ignores warnings and is masked by a same-location regression

**File:** `site/scripts/phase30-gate.mjs:78-148`

It compares the **set** of error locations against `{ComparatorPairsLinks.astro:28}` — a genuine improvement over counting — but: (a) a *new* error introduced at `ComparatorPairsLinks.astro:28` is invisible; (b) the phase-close bar is "4 errors / **0 warnings**" and the warning count is never parsed, so new warnings pass silently; (c) locations are only extracted from `.astro`/`.ts`/`.tsx` tokens on lines containing the word "error". Executed against the current tree it correctly reports `ComparatorPairsLinks.astro:28`, and it does fail closed when nothing parses (`:138-142`), so it is not tautological — just incomplete.

**Fix:** also parse the `- N errors` / `- N warnings` summary lines and assert `errors === 4 && warnings === 0` **in addition to** the location-set check.

---

## Not defects (checked and cleared)

- **Prop chain across all four hops** — traced individually for both the rail and the sheet. No forwarded-to-one-surface-only prop exists. `FilterFields` receives real callbacks on both paths.
- **`onToggle` mutual exclusion** — the `openId === id ? null : openId` guard (`EntryPointsRail.tsx:126-134`) correctly ignores the React-driven close of the *previous* panel when a new one opens; traced through the full open→open transition.
- **`mousedown` listener** — registered with `[openId]` deps, removed in cleanup, `offsetParent`-guarded so it is inert while the rail is `display:none`.
- **Escape handler** — container-scoped, `stopPropagation()` only (no `preventDefault`), no Tab handling, cannot fire while focus is in the dialog or the Leaflet map. F-49's "no document-scoped keyboard listener at all" claim holds.
- **`.filters-row` / `.ev-chip` / `.mode-toggle`** — absent from source and from built `dist/`; `.ev-dot-mini`, `.chip`, `.chip.select` retained and consumed. No specificity collision found in the 970→1179-line file.
- **`score.mjs` dual `filter-entry` handling** — the rail and the FAB are mutually exclusive by media query (`map.css:41-45` vs `:1088,1105-1111`), so `score.mjs:66-73`'s "first rendered candidate" selection resolves unambiguously at every band.
- **FAB × result-panel collision (spec §4a)** — `map.css:1113-1119` raises the FAB to `calc(40vh + 16px)` via the already-shipped `.map-stage.has-panel` hook; the FAB's `z-index:800` inside `.map-topbar`'s stacking context clears `.result-panel`'s 700.
- **`BaseLayout.astro:125-126`** — the F-40 fix correctly preserves the current origin (`pathname + search + hash`); it is a one-line, correctly-scoped change.

---

_Reviewed: 2026-07-30_
_Reviewer: Claude (gsd-code-reviewer), adversarial/FORCE stance_
_Depth: deep — 15 files, diff-anchored to 3b45ca443, gate + tests + astro check executed_
