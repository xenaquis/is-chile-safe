# Phase 30 — Adversarial PREMORTEM

**Written**: 2026-07-30, before any Phase 30 code lands. **Stance**: it is one week later and Phase 30 failed.
**Inputs read**: `30-01..30-06-PLAN.md`, `30-FABLE-CONSTRAINTS.md` (F-47..F-50), `30-RESEARCH.md`,
`29-DESIGN-SPEC.md`, `STATE.md`, `ROADMAP.md` §Phase 30, `score.mjs`, and the real code:
`MapIsland.tsx`, `MapTopbar.tsx`, `FiltersRow.tsx`, `SearchBox.tsx`, `map.css` (970 lines),
`BaseLayout.astro:112-131`, `site/src/pages/map.astro`, `site/scripts/validate/map.mjs`.

This document changes no plan. Every amendment below is proposed text for the orchestrator to apply.
All six plans still carry `Fable review: PENDING` on line 1 — they are amendable without a re-plan cycle.

---

## Ranked failure modes

| # | Failure | P | Damage | P×D |
|---|---|---|---|---|
| 1 | `c3 touchTargetViolations === 0` is unachievable; the plan asserts "c3 stays PASS" against a baseline that says FAIL | ~0.95 | phase cannot close honestly, or the bar gets quietly redefined | **highest** |
| 2 | The mandated ellipsis state summary makes `criterion2` FAIL by construction | ~0.8 | c2 — the phase's headline fix — reports FAIL at the narrow bands | **highest** |
| 3 | Nobody deletes the `.filters-row` CSS rules → `phase30-gate.mjs` assertion 4 fails at close | ~0.85 | close blocked, or assertion weakened to HTML-only (instrument rebinds to legacy) | high |
| 4 | F-50 coverage ceilings are not like-for-like with the real DOM (double/triple counting + a topbar that carries search+locate) | ~0.7 | a real ceiling breach, or a meaningless "within ceiling" claim | high |
| 5 | Homicide layer silently lost: `familyIndex: null` is the same tuple as "Todos" | ~0.4 | user-visible data feature dies behind fully green gates | high |
| 6 | React 19 re-render overwrites the imperatively-set `aria-expanded` (and `open`) on `<details>` | ~0.7 | ARIA lies to screen readers; panels close mid-interaction | high |
| 7 | `verdict()`'s `c4` can never be `true`; "all gates green" is unreachable and invites instrument drift | ~0.9 | ambiguity at close; F-49 pressure | med-high |
| 8 | Escape handler focuses a `<summary>` inside a `display:none` rail; collides with the open `<dialog>` | ~0.5 | real focus-loss defect, in the exact criterion the phase evidences as trap-free | med-high |
| 9 | Green gates over a broken island: no gate binds any control to its effect | ~0.5 | Phase 28 repeat — defects found after close | med-high |
| 10 | `.mode-toggle` CSS deleted in Wave 2 while `MapIsland` still renders it until Wave 4 | ~0.5 | live-site window with an unstyled/mispositioned control | med |
| 11 | `--map-topbar-h` is a phantom var; the partial-year badge is positioned against a topbar height that changes | ~0.5 | visible overlap, no gate, no checklist item | med |
| 12 | `?region=` timing/precedence unspecified (`getBounds` validity, `?cut=` collision) | ~0.4 | new feature silently no-ops; manual check can't tell | med |
| 13 | Iframe height unpinned → baseline and close captures are not comparable | ~0.5 | every "no regression" number is uninterpretable | med |
| 14 | Gate brittleness: minified-CSS assumption, astro-check count parsing, `\|\| true` tautology, vitest piped to grep | ~0.5 | spurious red → pressure to loosen; or spurious green | med |
| 15 | `dist/` gate can be fully green over a page that throws at hydration | ~0.25 | worst-case: close with a blank map | med |
| 16 | The locate button (32px) is mandated to 44px by the spec and no plan touches it | ~0.7 | MAPSH-03 unmet, and it is also failure #1's cheapest fix | med |

---

## 1. `c3` cannot be PASS, and 30-06 asserts it will be

**Mechanism.** `score.mjs:104-114` selects `a[href],button,input,select,textarea,summary,[role="button"],[data-role]`
across the **whole document** — header nav, skip link, Leaflet's attribution links, everything — and counts any
rendered element under 44px in either dimension. The recorded baseline is `c3 FAIL (touchTargetViolations 20)`
(`29-DESIGN-SPEC.md:29`). Known offenders that Phase 30 does not touch:

- `.locate-btn-visible` — **32×32** (`map.css:344-357`, rendered `SearchBox.tsx:76-90`).
- `.zoom-ctl button` — **36×36** (`map.css:277-280`).
- Leaflet's attribution anchors inside `.leaflet-control-attribution` (added `MapIsland.tsx:122-139`), a few px tall.
- `PageHeader`/`PageFooter` links and the skip link (`BaseLayout.astro:141-146`) — outside MAPSH-05 scope entirely.

Yet `30-06-PLAN.md:15` states as a must-have truth: *"c1/c2/c5 improve to PASS, **c3 stays PASS**"*. c3 is not
PASS today. Nothing in plans 30-02..30-05 enlarges a single one of the offending targets, and
`29-DESIGN-SPEC.md:134` (MAPSH-03) explicitly requires *"All targets ≥ 44 px (incl. the locate button, raised
from 32 px)"* — an instruction that fell out of the plan set entirely.

One week later this resolves one of two ways, both bad: the phase closes with c3 recorded FAIL and "accepted"
(silently dropping a pinned MAPSH-03 requirement), or someone rescopes the criterion mid-close, which is exactly
the instrument-editing F-49 exists to forbid.

**Amendment (plan edit).**

(a) In `30-03-PLAN.md`, add to Task 1's `<action>`:

> Also raise the two undersized map controls the design spec's MAPSH-03 row pins (`29-DESIGN-SPEC.md:134`):
> `.locate-btn-visible` (`map.css:344-357`) from `32px` to `44px` width/height, and `.zoom-ctl button`
> (`map.css:277-280`) from `36px` to `44px`. Keep the SVG glyph sizes unchanged (18px / 20px font) — only the
> hit area grows. `.zoom-ctl`'s `border-radius: 8px; overflow:hidden` still clips correctly at 44px.

and to its `<verify>` check array:

> `[/\.locate-btn-visible\s*\{[^}]*width:\s*44px/.test(css),'locate button not raised to 44px'],`
> `[/\.zoom-ctl button\s*\{[^}]*width:\s*44px/.test(css),'zoom buttons not raised to 44px']`

(b) In `30-06-PLAN.md`, replace must-have truth 1's `c3 stays PASS` with:

> `c3`: `touchTargetViolations` may not include **any element inside `.map-topbar`, `.legend`, `.zoom-ctl`, or
> carrying a `data-role` attribute**. The `touchTargetDetail` array is recorded verbatim, pre and post, and the
> post-change list must be a strict subset of the baseline list. Residual violations from `PageHeader`/`PageFooter`
> and `.leaflet-control-attribution` are **accepted and recorded** with the reason: they are outside MAPSH-05's
> confinement (`ROADMAP.md:394`) and fixing them would be the scope creep this phase's risk annotation forbids.

This is a measurement-scope statement, not a threshold loosening — it never changes what value passes `score.mjs`,
it states which of its outputs this phase owns. Record it as the phase's own decision, not as an edit to `score.mjs`.

---

## 2. The ellipsis state summary makes `criterion2` FAIL by construction

**Mechanism.** `score.mjs:84-97` scans **every element in the document** and flags any with
`scrollWidth - clientWidth > 8` whose computed `overflow-x` is `auto|scroll|hidden`. `filterOverflowsContainer`
is then `hiddenOverflowElements.length > 0`, and `criterion2 = filterEntryDiscoverable && !filterOverflowsContainer`
(`score.mjs:100-101`); `verdict()` repeats it (`score.mjs:246`).

`30-03-PLAN.md:113` mandates:

> `.entry-state-summary` rule: `white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: <fixed>`

An element that is *actually truncating* has `scrollWidth` far greater than `clientWidth` — that is what makes the
ellipsis appear. `"Índice · Todos los delitos · 2025"` truncated at 320/375px overflows by well over 8px. So the
F-46-mandated UX mitigation **directly trips the instrument's own overflow scan** and reports the phase's headline
criterion (c2 — "the filters are findable and nothing is hidden by overflow") as FAIL, at exactly the narrow bands
where the phase most needs a PASS. Worse: the failure will read as "the filter row still overflows", which is the
old defect's signature, and could be mis-triaged for a whole cycle.

Second-order instances of the same trap already in the tree: `.family-bar-label` (`map.css:538-548`,
`nowrap+hidden+ellipsis`) whenever `ResultPanel` is open — so **never score with a commune selected**, which
collides with spec §4a's requirement to verify the FAB collision *with a commune selected* (score that state with
`isTopmost` only, not with `verdict()`).

**Amendment (plan edit).** Replace the `.entry-state-summary` sentence in `30-03-PLAN.md:113` with:

> Add a `.entry-state-summary` rule: `white-space: nowrap; overflow: hidden; text-overflow: ellipsis;` — and,
> because `score.mjs:84-97` flags **any** element overflowing its own box by >8px (which is precisely what a
> truncating ellipsis is), the summary **must be composed so it does not truncate at any of the five tested widths**.
> Implement band-aware composition in the component, not truncation in CSS:
> `≥640px`: `"Índice · Todos los delitos · 2025"`. `481-639px`: drop the mode word — `"Todos los delitos · 2025"`.
> `≤480px`: `"Todos · 2025"`. The ellipsis rule stays as a last-resort safety net (F-46 mitigation 1 — never wraps),
> but the component must be verified at 320/375/481/639/1296 to render a string that fits, i.e.
> `el.scrollWidth - el.clientWidth <= 8` at every width. Add that exact assertion to Plan 30-06's browser pass.

And add to `30-06-PLAN.md`'s ORCHESTRATOR-INLINE step 7:

> Before running `verdict()`, dump `hiddenOverflowElements` verbatim. If it is non-empty, name every entry and its
> `cls` — a non-empty list at close is a real defect, not a rounding issue, and must be fixed rather than narrated.
> Score c1/c2 with `ResultPanel` **closed** (spec §10) — `.family-bar-label` truncates by design and would
> otherwise poison the scan.

---

## 3. The `.filters-row` CSS survives, and the close gate is written to catch exactly that

**Mechanism.** `phase30-gate.mjs` assertion 4 (`30-06-PLAN.md:72`) scans *"every file under `dist/_astro/`"* for
the literal substrings `filters-row` and `ev-chip`. `map.css:47-59` defines `.filters-row` and
`.filters-row::-webkit-scrollbar`; `map.css` is imported by `MapIsland.tsx:20`, so those selectors are compiled
into `dist/_astro/*.css` verbatim. Deleting `FiltersRow.tsx` (Plan 30-05) removes the *consumer*, not the *rules*.
Searching the tree: `filters-row` appears at `FiltersRow.tsx:74`, `map.css:47`, `map.css:57`; `ev-chip` at
`FiltersRow.tsx:113`. **No plan task deletes `map.css:47-59`.** Plan 30-03 deletes only `.mode-toggle`
(`30-03-PLAN.md:113`); Plan 30-05 only *adds* band visibility rules (`30-05-PLAN.md:94`).

So the phase-close gate fails on its last assertion after all the work is done — at which point the cheap
"fix" is to narrow assertion 4 to the HTML files, which reintroduces exactly the risk F-47/§9a wrote it for.

Note `.ev-dot-mini` (`map.css:113-121`) must be **kept** (Plan 30-03 reuses it) and does not contain the string
`ev-chip` — no conflict.

**Amendment (plan edit).** In `30-05-PLAN.md` Task 1's `<action>`, append:

> Delete the now-dead `.filters-row` and `.filters-row::-webkit-scrollbar` rule blocks from `map.css`
> (`map.css:47-59`). Keep `.ev-dot-mini` (`map.css:113-121`) — `NewsToggle` uses it. Keep `.chip` and
> `.chip.select` — the new fields reuse them.

and to that task's verify array:

> `[!/\.filters-row/.test(fs.readFileSync('src/components/map/map.css','utf8')),'.filters-row CSS rules still present in map.css']`

---

## 4. The F-50 coverage ceilings are not comparable to what the real DOM will measure

**Mechanism.** `score.mjs:164-171` builds `controls` from
`.map-topbar, .legend, .mode-toggle, [data-role="filter-entry"], [data-role="news-toggle"], [data-role="entry-point"]`
and `score.mjs:223-228` sums **each element's rectangle independently** — there is no union. In the shipped
implementation the news toggle, the rail (`data-role="filter-entry"`) and the three entry points
(`data-role="entry-point"`) are all **descendants of `.map-topbar`** (`30-05-PLAN.md:94`). So the same pixels are
counted 2–3 times, and `controlCoveragePct` becomes a function of *how deeply the hooks are nested*, not of how
much map is covered. Whatever nesting the Phase 29 sketch had, the real page's is different — and the real topbar
additionally carries a search box (`.search-box`, max-width 360px, 44px tall) and a locate button that the ceilings
were never measured against.

Compounding it: `@media (max-width:480px) .map-topbar-row1 { flex-direction: column }` (`map.css:240-245`) already
stacks row 1, so adding the news toggle there makes the topbar *taller* at 320/375 — exactly the two bands with the
lowest ceilings (32.2% / 22.7%), and 22.7% is additionally hard-gated by `verdict()`'s `<= 25` at ≤375
(`score.mjs:249-251`).

Outcome one week later: either the number lands above the ceiling and F-50 (which says "may not exceed") blocks the
close with no designed remedy, or it lands below by accident and is reported as a verified mitigation when it is an
artifact of nesting depth.

**Amendment (plan edit).** Add to `30-01-PLAN.md`'s ORCHESTRATOR-INLINE step 3, as a new sub-item:

> For each width, also record, alongside `controlCoveragePct`: the `controlZIndexes` list (which names every element
> entering the coverage sum), the rect of `.map-topbar`, and the computed **union** coverage
> (`covered_union`, computed inline in the same `evaluate_script` — a separate, additional number that does not
> modify `score.mjs`). The union figure is the one that answers "how much map is hidden"; the raw
> `controlCoveragePct` is the one F-50 governs. Record both, both pre and post, and never substitute one for the other.

Add to `30-03-PLAN.md` Task 2's `<action>`:

> Coverage budget (F-50 is a hard ceiling): the rail must sit **on the same row as the search box at ≥481px**, not
> add a third topbar row, and at ≤480px only the FAB is rendered visible, so the topbar's height at 320/375 must not
> exceed its current height by more than the news toggle's own row. Measure `.map-topbar`'s `getBoundingClientRect().height`
> at 320/375 before and after; a growth of more than ~48px at those widths will breach the 22.7%/32.2% ceilings.

Add to `30-06-PLAN.md` step 4:

> If `controlCoveragePct` exceeds a ceiling at any band, the disposition is a **fix** (reduce topbar padding/height,
> or drop a hook off a nested wrapper so the same pixels are not counted twice — the latter only if it does not
> remove a `data-role` the spec §8 mandates). It is **not** admissible to average widths, to switch to the union
> number, or to reinterpret F-50 — F-50 says "may not exceed", and STRESS.md's freeze forbids loosening the ≤25%@375.

---

## 5. Everything `FiltersRow`/`modeToggle` own today, and what happens to each

Full inventory of the deleted surface, with the fate of each item under the plans as written:

| Owned today | Where | Fate under plans as written | Risk |
|---|---|---|---|
| `year` `<select>` + `aria-label` "Filtrar por año"/"Filter by year" | `FiltersRow.tsx:76-85` | → `YearField` (30-02) | label changes to `map_entry_year` ("Año") and is duplicated by the `<summary>` — ambiguous accessible name |
| `AVAILABLE_YEARS` derived from `new Date().getFullYear()` down to 2005 | `FiltersRow.tsx:45-52` | → `mapFilterDefs.ts` verbatim (30-02) | derived-at-import; a year rollover changes the list and no test pins it. **No test** today |
| `CHIP_DEFS` 8 entries incl. homicide `familyIndex:null` | `FiltersRow.tsx:30-43` | → `mapFilterDefs.ts` verbatim | see §6 — highest-risk item |
| chip → `onFamilyChange(key, familyIndex)` with **deselect-on-active** | `FiltersRow.tsx:95` | → `FamilyField` radiogroup | radios cannot deselect; if ported literally, all-`aria-checked=false` is an invalid radiogroup state |
| `aria-pressed={isActive}` per chip | `FiltersRow.tsx:96` | → `aria-checked` on `role="radio"` (spec §5) | correct change, but nothing gates it |
| `title={def}` from `familyDefs` (READ-02/D-02 gap closure) | `FiltersRow.tsx:90,97` | "port verbatim" (30-02) | **no gate asserts the 8 titles**; also unreachable by hover inside the ≤480 dialog |
| accent dot on `featured && !isActive` | `FiltersRow.tsx:99-105` | "port verbatim" | inline-styled; easy to drop in a rewrite, **no gate** |
| news toggle `.ev-chip` + `aria-pressed` + `.ev-dot-mini` | `FiltersRow.tsx:112-119` | → `NewsToggle` (30-03) | gated on `data-role`/`aria-pressed` presence only, **not on `showEvents` still reaching the pin layer** |
| `.mode-toggle` div, `role="group"`, `aria-label` "Modo de mapa" | `MapIsland.tsx:440` | → `ModeField` radiogroup (30-02/05) | ok |
| per-button recolor side effects (`buildStyleMapFromCompositeIndex` / `...Homicide` / `...Family` / `...Level` + `applyStyleMap`) | `MapIsland.tsx:443-467` | unified `onModeChange` (30-05) | logic is *already redundant* with the effect at `MapIsland.tsx:302-320` (deps `[crimeFamilyIndex, crimeIsHomicide, mode]`) — relocation is safe, but if the executor "simplifies" by deleting it, nothing breaks visibly, so nothing catches an incorrect merge either |
| `modeToggle?: React.ReactNode` prop | `MapTopbar.tsx:19-20,47` | removed (30-05) | gated |
| `.map-topbar-row1` layout dependency of the mode toggle at ≤480 | `map.css:240-251` | `.mode-toggle` rules deleted in Wave 2 | see §10 |

**Untested currently-working behavior that would break silently** (no vitest, no validator, no `score.mjs` coverage):
`?cut=` deep link (`MapIsland.tsx:226-232`), geolocation (`onLocate` → `locate()`, `MapIsland.tsx:434-438`),
incident pins (`showEvents` effect, `MapIsland.tsx:359-383`), the derived year list, `ResultPanel` open/close and
its `resetStyle` on close (`MapIsland.tsx:525-531`), the featured accent dot, and the chip `title=` definitions.
Each is one line on a manual checklist (`30-06-PLAN.md:101`) and nothing else. `score.mjs` measures geometry, never
function — spec §10 says so outright ("Criterion 1 tests presence and stacking, not legibility").

---

## 6. The homicide layer is one refactor away from silently becoming "Todos"

**Mechanism.** `CHIP_DEFS` (`FiltersRow.tsx:30-43`) has two entries whose `familyIndex` is `null`:
`{key: null, familyIndex: null}` ("Todos") and `{key: 'homicidios', familyIndex: null}` (the homicide layer,
D-04/HOM-01). The **only** thing that distinguishes them downstream is the `key` string:
`MapIsland.tsx:424-430` sets `setCrimeIsHomicide(key === 'homicidios')`, and `crimeIsHomicide` is what selects
`buildStyleMapFromHomicide` (`MapIsland.tsx:282-288`, `312-317`).

A radiogroup rewrite naturally keys options by a single value. If `FamilyField` models its radios on
`familyIndex` (the numeric, "obvious" identity) or emits `onFamilyChange(null, familyIndex)` for the homicide
option, homicide becomes indistinguishable from "All types", `crimeIsHomicide` stays `false` forever, and
`buildStyleMapFromHomicide` is dead code. The map still recolors (it falls to `buildStyleMapFromLevel`), so a
human ticking "choropleth recolors correctly switching crime family — PASS" sees nothing wrong. Every gate in the
phase stays green. This is a user-visible loss of a first-class data feature.

**Amendment (plan edit).** Add a third task to `30-02-PLAN.md` (or extend Task 2's `<behavior>`), TDD:

> `mapFilterDefs.test.ts` (vitest, pure):
> 1. `CHIP_DEFS.length === 9` entries? No — assert **exactly 9 rendered options**: the 8 in `FiltersRow.tsx:30-43`
>    plus none added. Assert the array literally equals the pinned list of `{key, familyIndex}` pairs:
>    `[null,null], ['vida',0], ['propiedad',5], ['robos_violentos',1], ['incivilidades',6], ['vif',2],
>    ['drogas',3], ['armas',4], ['homicidios',null]`.
> 2. Assert `CHIP_DEFS.filter(c => c.familyIndex === null).map(c => c.key)` is exactly `[null, 'homicidios']` —
>    pinning that the two null-index entries are distinguished **only** by `key`.
> 3. Assert every non-null `familyIndex` matches `family_keys` order in `data/cead/catalog.json`
>    (`0=vida,1=robos_violentos,2=vif,3=drogas,4=armas,5=propiedad,6=incivilidades`) — read from the real data file,
>    so a taxonomy drift breaks the test rather than mis-coloring the map.
> 4. Assert `AVAILABLE_YEARS[0] === new Date().getFullYear()` and `AVAILABLE_YEARS.at(-1) === 2005`.

and add to `30-02-PLAN.md` Task 2's `<action>` for `FamilyField`:

> `FamilyField`'s `onFamilyChange` must be called as `onFamilyChange(def.key, def.familyIndex)` — the **key first**,
> for all 9 options including `homicidios`. Never key the radios on `familyIndex`: `null` is the value for both
> "Todos" and "Homicidios", and `MapIsland.tsx:429` distinguishes them solely by `key === 'homicidios'`.
> "Todos" (`key: null`) is the only clearing option — do **not** port `FiltersRow.tsx:95`'s deselect-on-active
> behaviour into `role="radio"`, which has no "none selected" state; selecting "Todos" is the deselect.

---

## 7. `<details>` + React 19: the plan's own instruction creates the bug

**Mechanism.** `30-03-PLAN.md:105` says: *"Wire three behaviors via a single `useEffect` on mount holding refs to
the three `<details>` elements … **do not lift to controlled `open` state**"*, and `:106` says the toggle listener
*"updates `aria-expanded` on each `<summary>`"* — i.e. imperatively, via `setAttribute`. But `30-03-PLAN.md:103`
renders `<summary aria-expanded aria-controls={panelId}>` **from JSX**.

React owns any attribute it renders. On the next re-render, React reconciles `aria-expanded` back to its JSX value
and blows away the imperative one. And re-renders are guaranteed on *every* interaction: `EntryPointsRail`'s props
(`year`, `crimeFamily`, `mode`) change on every selection, and the `aria-live` state summary re-renders with them.
So the sequence "open Año → pick 2024" leaves the panel visually open with `aria-expanded="false"` (or vice versa) —
a screen reader is told the opposite of the truth, in the phase whose entire purpose is discoverability.

If anyone additionally puts `open` in the JSX to "fix" it without lifting state, React 19 will reset the native
`open` attribute on each render and panels will snap shut mid-interaction.

Leaflet itself is not the collision point: the panels are DOM siblings of `.map-canvas` under `.map-stage`
(`MapIsland.tsx:413-415`), outside `.leaflet-container`, so map drag/click never receives panel events and closing
a panel does not disturb the map's focus. The collision is purely React-vs-imperative-DOM.

**Amendment (plan edit).** Replace `30-03-PLAN.md:105`'s parenthetical with:

> Hold a single `const [openId, setOpenId] = useState<string|null>(null)` in `EntryPointsRail` and render
> `<details data-role="entry-point" open={openId === id} onToggle={(e) => setOpenId(e.currentTarget.open ? id : (openId === id ? null : openId))}>`
> with `<summary aria-expanded={openId === id} aria-controls={panelId}>`. Mutual exclusion is then a property of the
> state (only one id can be open), not a DOM mutation loop. **Never `setAttribute('aria-expanded', …)` on an element
> whose `aria-expanded` is also rendered from JSX** — React reconciles it away on the next render, and this component
> re-renders on every filter change because the `aria-live` summary is its sibling. The `document`-scoped Escape and
> `mousedown` listeners call `setOpenId(null)` (plus `summaryRef.current?.focus()` for Escape), never `el.open = false`.

---

## 8. The Escape listener, `score.mjs` c4, F-49 — and a strictly better construction

**Mechanism.** Native `<details>` does not close on Escape, so spec §6 forces new JS
(`30-RESEARCH.md` Q2). The plan puts one `keydown` on `document` (`30-03-PLAN.md:107`). Two concrete defects
follow from the plan as written:

1. **Both surfaces are always in the DOM.** `30-05-PLAN.md:94` renders `EntryPointsRail` *and* `FilterSheet`
   unconditionally, with CSS deciding visibility. A `<details>` opened at 640px and then narrowed to 400px (or an
   orientation change) stays `open` inside a `display:none` rail. Escape then closes it and calls `.focus()` on a
   `<summary>` that cannot receive focus → focus falls to `<body>`. That is a genuine keyboard defect, in the exact
   criterion the phase is spending three separate evidences to declare clean.
2. **Escape while the modal sheet is open.** The `<dialog>` closes natively *and* the rail's document listener runs,
   potentially moving focus to a hidden `<summary>` instead of back to the FAB — undoing 30-04's carefully-specified
   focus-return.

**On `score.mjs` c4 and F-49.** `score.mjs:145-151` sets `criterion4 = 'NOT_MEASURED_FAIL'` and
`keyboardTrapFree = null` **as soon as `externalScripts.length > 0`**, before any `keyInterceptors` reasoning.
Astro ships the island as `<script type="module" src=…>`, so this branch is taken unconditionally on the real page —
both pre and post. And `verdict()` (`score.mjs:248`) requires `keyboardTrapFree === true`, so
**`c4_keyboardTrapFree` is `false` in every verdict table this phase will ever produce**, before and after.
`29-DESIGN-SPEC.md:29`'s "c4 PASS" is therefore almost certainly a capture against a sketch page, not the real app
(30-RESEARCH.md Q5 flags the same tension). Wave 0 will discover this; the danger is that "c4 went from PASS to FAIL"
gets read as a regression *caused by this phase*.

Is there a strictly better construction than a `document` `keydown`? Yes, partially: put the listener on the **rail
container** (`onKeyDown` on the `<div data-role="filter-entry">`), not on `document`. Focus is always inside the rail
when a panel is open (that is what "Escape closes the open panel" means), so a container-scoped React `onKeyDown`
covers every real case, needs no `document` listener, no add/removeEventListener lifecycle, and cannot fire while
focus is in the dialog or the map. It also narrows the honest claim in the F-49 evidence chain from "our global
listener is well-behaved" to "there is no global listener at all", which is a much stronger thing to evidence.
The click-outside listener still needs `document` `mousedown` — matching the already-shipped precedent at
`SearchBox.tsx:50-58`.

**Amendment (plan edit).** Replace the Escape bullet in `30-03-PLAN.md:107` with:

> - **Escape-closes**: a React `onKeyDown` handler **on the `<div data-role="filter-entry">` rail container**, not on
>   `document`. When `e.key === 'Escape'` and `openId !== null`: `setOpenId(null)`, focus the closing panel's
>   `<summary>` via its ref, and `e.stopPropagation()` — never `preventDefault()`, and never any handling of Tab or
>   Shift+Tab. A container-scoped handler cannot fire while focus is in the `<dialog>` or in the Leaflet map, which
>   removes both the dialog-collision and the hidden-summary focus-loss failure modes, and lets Plan 30-06's F-49
>   evidence chain make the stronger claim: *the map island registers **no** document-scoped keyboard listener at all*
>   (grep the built chunk for `addEventListener('keydown'` / `addEventListener("keydown"` and expect **zero** hits in
>   the island's own code).
> - Guard the click-outside `mousedown` handler with `if (!railRef.current || railRef.current.offsetParent === null) return;`
>   so it is inert while the rail is `display:none` at ≤480px.

and in `30-06-PLAN.md` step 5, add a pre-registered expectation so the baseline diff is not misread:

> `criterion4` is expected to be `NOT_MEASURED_FAIL` **both pre and post** — `score.mjs:145-151` takes that branch
> unconditionally on any Astro page (external module script, empty `textContent`), and `verdict()`'s
> `c4_keyboardTrapFree` is consequently `false` in every table this phase produces. This is a property of the
> instrument on a bundled page, **not** a regression introduced by Phase 30, and it is not grounds for editing
> `score.mjs` (F-49). Record `29-DESIGN-SPEC.md:29`'s conflicting "c4 PASS" as superseded by Wave 0's measurement.
> The Tab walk must be shown falsifiable: run it once with a panel deliberately open and once with the sheet open,
> and record that focus order differs — a walk that returns the same answer in every state is measuring nothing.

---

## 9. How Phase 30 closes fully green with a broken UI (the Phase 28 pattern)

`STATE.md` records the precedent verbatim: *"Ten real defects were found AFTER the implementation passed every
automated gate green — including NEWSUI-02 having no gate at all"*. Phase 30's gate set has the same shape:

- Plans 30-02..30-05 verify with `node -e` **string/regex presence scans over source files**. Every one of them
  passes against a component that renders correctly but is wired to nothing.
- `phase30-gate.mjs` verifies `dist/` **substrings** and `git diff`. All green over a bundle whose island throws
  at hydration.
- `score.mjs` verifies **geometry** — rectangles, stacking, z-index. Spec §10 states outright that c1 "tests
  presence and stacking, not legibility"; nothing in it tests that any control *does* anything.
- vitest adds 4 tests, all for `resolveRegionFocus` — a function that is not even on the critical path of the
  rework.

**The named invariant with no gate**: *every control still drives the state it drove before.*
Concretely, five bindings, none of which any gate touches:
`YearField → onYearChange → setYear` (`MapIsland.tsx:421-422`);
`FamilyField → onFamilyChange → setCrimeFamily/setCrimeFamilyIndex/setCrimeIsHomicide` (`MapIsland.tsx:423-430`);
`ModeField → onModeChange → setMode` + recolor;
`NewsToggle → onEventsToggle → setShowEvents` → `fetchAndMountIncidents` (`MapIsland.tsx:359-383`);
`SearchBox → onSelect → selectCommune` (`MapIsland.tsx:388-407`).
A prop dropped anywhere in the four-hop chain `MapIsland → MapTopbar → EntryPointsRail/FilterSheet → FilterFields`
(a chain that does not exist today — today it is two hops) produces a control that looks perfect and does nothing.
TypeScript catches a *missing* required prop; it does not catch `onYearChange={() => {}}` or a prop forwarded to
the rail but not to the sheet — and the sheet is the ≤480px surface no desktop reviewer will open.

**Amendment (plan edit).** Add to `30-06-PLAN.md`'s ORCHESTRATOR-INLINE step 6, replacing the eyeball items with
scripted assertions (all runnable in one `evaluate_script` each):

> 6a. **Effect assertions, not appearance checks** — run each at 1296 **and** at 375 (the FAB/dialog surface):
> - News toggle: click it, wait 1500ms, assert `document.querySelectorAll('.ev-dot').length > 0`; click again,
>   assert it returns to 0. (Proves `showEvents` still reaches `IncidentPinLayer`.)
> - Crime type: select `Homicidios`, then read back the fill of a known polygon (e.g. via
>   `document.querySelectorAll('canvas')` is not introspectable — instead assert the `Legend` title/band text
>   changes and that selecting `Homicidios` yields a **different** legend band set than `Todos` at the same year and
>   mode). A wrong `familyIndex` mapping is invisible to the eye; a differing band set per family is not.
> - Year: switch 2025 → 2019 and assert the legend breaks change (or a `Datos no disponibles` toast appears) —
>   proving `onYearChange` still reaches `setYear`'s fetch effect (`MapIsland.tsx:246-297`).
> - Mode: `Índice` ↔ `Por delito` and assert `Legend`'s title toggles between the composite title and the banded
>   legend (`MapIsland.tsx:505-512`).
> - Search: type a commune, pick it, assert `ResultPanel` appears; close it and assert it disappears.
> - Run **all six at ≤480 through the `<dialog>`**, not only through the rail. The two surfaces receive props
>   independently (`30-05-PLAN.md:94`) and a prop forwarded to only one of them is the single most likely defect
>   in this phase.
> 6b. Assert `console` error count is 0 across the whole pass (BrowserOS `get_console_logs`), recorded verbatim.

---

## 10. `.mode-toggle` deleted in Wave 2, still rendered until Wave 4

**Mechanism.** `30-03-PLAN.md:113` deletes `.mode-toggle` (`map.css:104-111`) *and* its `@media (max-width:480px)`
reset (`map.css:247-250`) in Wave 2, and its gate asserts `!/\.mode-toggle\s*\{/.test(css)`. But `MapIsland.tsx:440`
still renders `<div className="mode-toggle">` until Plan 30-05 (Wave 4). Between those waves the mode toggle loses
`position:absolute; top:8px; right:16px; z-index:801` and falls into `.map-topbar-row1`'s flex flow — it will
overlap or displace the search box. Production is live (`30-FABLE-CONSTRAINTS.md:106`); an interruption, a partial
push, or a decision to ship after Wave 3 ships that state to real users. It also corrupts any mid-phase
`score.mjs` reading, since `.mode-toggle` is in the instrument's `controls` selector (`score.mjs:165`).

**Amendment (plan edit).** Move the deletion. In `30-03-PLAN.md:113`, delete the sentence beginning *"Remove the
now-superseded `.mode-toggle` rule block…"* and remove `[!/\.mode-toggle\s*\{/.test(css), …]` from its verify array.
Add to `30-05-PLAN.md` Task 1's `<action>`:

> In the same commit that removes the `modeToggle` JSX from `MapIsland.tsx`, delete the now-dead `.mode-toggle` rule
> block (`map.css:104-111`) and its `@media (max-width:480px)` reset (`map.css:247-250`) — keeping the
> `.map-topbar-row1 { flex-direction: column }` rule in that media block, which is still live. CSS deletion and the
> removal of its last consumer must land together so no intermediate wave ships an unstyled control to a live site.

and move the corresponding assertion into 30-05 Task 1's verify array.

---

## 11. `--map-topbar-h` is a phantom variable and the topbar height is about to change

**Mechanism.** `.partial-year-badge` positions itself at `top: calc(var(--map-topbar-h, 96px) + 8px)`
(`map.css:900-903`). `--map-topbar-h` is defined **nowhere in the repo** (verified: one occurrence, the consumer),
so the fallback 96px is always used. The badge renders whenever `payload.partial_year === true`
(`MapIsland.tsx:476-482`) — i.e. on the current year, i.e. by default. Phase 30 changes the topbar's height at every
band (news toggle added to row 1; rail added below it; `.mode-toggle` removed from the absolute layer). At 320/375,
`map.css:240-245`'s column stacking makes the topbar noticeably taller than 96px and the badge will render **inside**
the topbar. No gate, no `score.mjs` criterion, and no line on the manual checklist covers it.

**Amendment (plan edit).** Add to `30-03-PLAN.md` Task 2's `<action>`:

> Set the variable the badge already reads: add `--map-topbar-h` to the `.map-topbar` rule with a real per-band value
> (or, better, keep the badge in normal flow relative to the topbar). `map.css:902` consumes
> `var(--map-topbar-h, 96px)` and nothing in the repo defines it — the fallback is always used, and this phase changes
> the real height.

and to `30-06-PLAN.md` step 6's checklist:

> `partial-year-badge` renders fully clear of the topbar at all five widths (it is on by default whenever the current
> year's payload carries `partial_year`).

---

## 12. `?region=` timing and precedence are unspecified

**Mechanism.** `30-05-PLAN.md:74-82` computes region bounds from `polyIdxRef.current` **synchronously**, immediately
after `mountChoroplethLayer` returns. The adjacent `?cut=` path deliberately does **not** do that: `MapIsland.tsx:230`
carries the comment *"Small timeout to allow Leaflet to finish rendering polygons before getBounds is valid"* and
wraps `selectCommune` in `setTimeout(…, 100)`. If that concern is real for one polygon, it is real for 30+.
The failure is silent by design (`bounds.isValid()` guard) — the map simply loads at Chile's default extent, which is
exactly what a "silent degradation on unknown value" success looks like. A manual checker cannot distinguish
"correctly ignored an unknown region" from "the feature never worked".

Second: `?cut=13101&region=13` fires `fitBounds` (region, t=0) and then `flyToBounds` (cut, t=100ms) — the cut wins by
accident of ordering, which is probably right, but is undocumented and untested.

**Amendment (plan edit).** Replace `30-05-PLAN.md`'s `<interfaces>` `?region=` snippet with:

```ts
// Only when no valid ?cut= was requested — a commune deep link is more specific and wins.
if (!(focusCut && /^\d{4,5}$/.test(focusCut))) {
  const regionCuts = resolveRegionFocus(window.location.search, idx);
  if (regionCuts) {
    setTimeout(() => {
      const m = mapRef.current;
      if (!m) return;
      const bounds = L.latLngBounds([]);
      regionCuts.forEach((cut) => {
        const ly = polyIdxRef.current.get(cut);
        if (ly && 'getBounds' in ly) bounds.extend((ly as L.Polygon).getBounds());
      });
      if (bounds.isValid()) m.fitBounds(bounds, { padding: [40, 40] });
    }, 100); // same reason as ?cut=: getBounds is not valid until Leaflet has rendered (MapIsland.tsx:230)
  }
}
```

and add to `30-06-PLAN.md` step 6:

> `?region=13` must be verified **positively**: record the map's `getBounds()` (or centre+zoom) before and after, and
> assert it changed and is inside Región Metropolitana. A "the map looks about right" tick cannot distinguish a
> working region focus from a silently no-op'd one — and the unknown-value case is *specified* to look identical.
> Also test `?cut=13101&region=05`: the commune deep link must win and `ResultPanel` must open.

---

## 13. The iframe height is unpinned, so the baseline is not comparable to the close

**Mechanism.** Both browser passes emulate widths with a same-origin iframe (`30-01-PLAN.md:100`,
`30-06-PLAN.md:99`) and neither specifies a **height**. But `score.mjs` uses `window.innerHeight` in
`inViewport` (`score.mjs:28-31`) and derives `controlCoveragePct` from the map pane's *area*
(`score.mjs:220-231`). A 700px-tall iframe and an 850px-tall iframe give materially different coverage percentages
for identical markup, and `inViewport` can flip `newsToggleInViewport`/`filterEntryDiscoverable` (c1/c2) purely on
height — the legend sits at `bottom:32px` (`map.css:129`) and `.map-stage` is `calc(100vh - 64px)` (`map.css:14`),
both height-sensitive. One week later, "coverage went from 22.7% to 28%" may be entirely an iframe-height artifact,
and nobody can tell, because the baseline document does not record the height it used.

**Amendment (plan edit).** Add to both `30-01-PLAN.md` (ORCHESTRATOR-INLINE step 3) and `30-06-PLAN.md` (step 4):

> Pin the iframe geometry: `width = <band>`, **`height = 800`**, at every band, in both the baseline and the close
> capture. Record `viewportWidthPx`/`viewportHeightPx` from the returned JSON and refuse to compare any two captures
> whose heights differ — `controlCoveragePct`, `inViewport` (c1/c2) and `mapWidthRatio` are all functions of viewport
> height, and an unpinned height makes the pre/post diff uninterpretable.

---

## 14. Gate brittleness that will produce a spurious red (and then pressure to loosen)

Concrete items in `30-06-PLAN.md` Task 1 and elsewhere:

- **Assertion 6** requires the whitespace-free literals `z-index:750`, `z-index:800`, `z-index:801` in
  `dist/_astro/*.css`. That assumes CSS minification is on. If Astro/Vite emits unminified CSS in this project's
  build config, all three are absent and the gate fails on a perfectly correct implementation.
  → **Amendment**: accept either form: strip all whitespace from the CSS text before scanning
  (`css.replace(/\s+/g,'')`), then look for `z-index:750` etc. Also assert **absence** of `z-index:700` on `.legend`
  specifically, since a leftover unscoped rule elsewhere in the 970-line file could still win the cascade
  (Research Pitfall 3's warning sign).
- **Assertion 1** parses `npx astro check` output for exactly `4 errors / 0 warnings`. Five new `.tsx`/`.ts` files
  land in this phase; a single new error makes the number 5 and the gate red, with the "fix" being to bump the
  baseline — which then hides a real regression.
  → **Amendment**: assert on the *set* of `file:line` error locations (the pre-existing baseline is
  `ComparatorPairsLinks.astro:28`), not the count. New locations = fail; same locations = pass regardless of count.
- **`30-03-PLAN.md:116`** contains, inside its check array, the literal
  `[tsx.includes("role='radiogroup'")||tsx.includes('role="radiogroup"')||true, …]`. The trailing `|| true` makes
  that check unfalsifiable — the exact class of gate defect `30-FABLE-CONSTRAINTS.md:98` says has appeared eight times
  in phases 27–29.
  → **Amendment**: delete that array element entirely (the assertion belongs in 30-02's gate, on `FilterFields.tsx`);
  add there: `[/role=["']radiogroup["']/.test(ff) && !/role=["']group["']/.test(ff), 'FilterFields must use radiogroup, never group']`.
- **`30-02-PLAN.md:118`** runs vitest twice and pipes the second run through `grep -E "4 passed|[4-9][0-9]* passed"`.
  The exit status becomes grep's, and the pattern matches the whole-suite line as readily as the file's own — a
  failing sibling test would not be caught.
  → **Amendment**: `npx vitest run src/lib/regionParam.test.ts` alone (its own non-zero exit is the gate); assert the
  count in the plan's `<done>` prose, not through a pipe.

---

## 15. `dist/` can be fully green over a page that never renders

**Mechanism.** `30-06-PLAN.md:38` correctly records *why* the gate is dist-only-partial (`client:only="react"`,
no hooks in static HTML) — that reasoning is right and honest. But the consequence deserves to be a gate, not a
footnote: `phase30-gate.mjs` returns 0 when (a) three files are unchanged, (b) no packages were added, (c) two
strings are absent from `dist/`, (d) two strings are present. All four hold for a bundle that throws on mount.
`site/scripts/validate/map.mjs` does not help: its map-page assertions check the `astro-island` marker and the
locate `aria-label`, and the latter is satisfied by a **static span in `map.astro:32-36`**, not by the island —
so `16/16 validators` stays green over an island that renders nothing at all.

**Amendment (plan edit).** Add to `30-06-PLAN.md`'s success criteria:

> `phase30-gate.mjs` exiting 0 is **necessary and not sufficient** and may never be cited as the phase gate on its
> own. Phase 30 does not close without `30-CLOSE.md` containing five verbatim post-change `score.mjs` captures,
> because nothing in `dist/` can distinguish a working island from one that throws at hydration
> (`client:only="react"`; `validate/map.mjs`'s locate-label check is satisfied by the static span at
> `map.astro:32-36`, not by the island). If the browser pass cannot be run, the phase is **paused**, not closed.

---

## 16. Accepted-and-recorded (no amendment proposed)

- **`c4` will read `NOT_MEASURED_FAIL` forever on this codebase.** Accept: it is a correct fail-closed design
  (`score.mjs:140-151`) for a bundled page, and F-49 already prescribes the substitute evidence. Record the expected
  value in advance (see §8) so it is not mistaken for a Phase 30 regression.
- **`mapWidthRatio` 0.627 (full-bleed map) stays unfixed.** Accept: F-43/spec §10 put it out of scope, and fixing it
  means editing `.map-stage`/`.map-canvas`, which breaches MAPSH-05.
- **Header/footer/Leaflet-attribution touch targets stay under 44px.** Accept: outside MAPSH-05's confinement
  (`ROADMAP.md:394`). Record them by name in `30-CLOSE.md` so the residue is auditable rather than inferred.
- **The recolor logic in `onModeChange` is redundant with the effect at `MapIsland.tsx:302-320`.** Accept: preserving
  it (as `30-05-PLAN.md:106` requires) is the lower-risk move; note in the summary that it is belt-and-braces so a
  future reader does not "clean it up" and discover it was load-bearing after all.
- **F-40's regression proof depends on spoofing `navigator.languages`, which BrowserOS cannot do directly.** Accept:
  the textual gate at `30-01-PLAN.md:75` is the real proof of the fix; record the browser step as
  "not independently reproduced" rather than fabricating a PASS. The `/es/mapa/` driving rule makes the redirect
  irrelevant to every subsequent measurement anyway (the script only runs on `lang === 'en'` pages,
  `BaseLayout.astro:116`).

---

## Summary of proposed plan edits

| Plan | Edit | Premortem § |
|---|---|---|
| 30-01 | Pin iframe height 800 in the baseline capture; record `controlZIndexes` + union coverage alongside `controlCoveragePct` | 4, 13 |
| 30-02 | `mapFilterDefs.test.ts` (CHIP_DEFS/homicide/family_keys/AVAILABLE_YEARS); `onFamilyChange(key, index)` key-first rule; no deselect-on-active in a radiogroup; radiogroup gate moved here | 5, 6, 14 |
| 30-03 | Raise locate button + zoom buttons to 44px; band-composed state summary (no >8px truncation); lift `openId` to React state; container-scoped Escape; `offsetParent` guard on click-outside; topbar height budget; define `--map-topbar-h`; drop the `\|\| true` check; **do not** delete `.mode-toggle` here | 1, 2, 4, 7, 8, 11, 14 |
| 30-04 | (no structural change; verify FAB collision with `isTopmost` only, never with `verdict()`, because `ResultPanel` open poisons the overflow scan) | 2 |
| 30-05 | Delete `.filters-row` rules from `map.css`; delete `.mode-toggle` rules in this wave; `?region=` gets the same 100ms timeout as `?cut=` and yields to a valid `?cut=` | 3, 10, 12 |
| 30-06 | c3 truth rewritten to a scoped/subset assertion; c4 expectation pre-registered; effect-assertions replacing eyeball regression items (run at 375 through the dialog too); dump `hiddenOverflowElements`; positive `?region=` proof; iframe height pinned; whitespace-insensitive z-index scan; astro-check by error *location* not count; gate declared necessary-not-sufficient | 1, 2, 8, 9, 12, 13, 14, 15 |
