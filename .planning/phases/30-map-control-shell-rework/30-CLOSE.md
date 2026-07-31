# Phase 30 — Close evidence (post-implementation browser pass)

Captured 2026-07-30 by the orchestrator (Fable) INLINE in BrowserOS against a real served build,
same harness and same pinned iframe geometry as `30-BASELINE.md` (`height = 800` at every band).
`score.mjs` ran **unchanged** and is inside the SHA-anchored byte-identical gate.

## 1. `score.mjs` — five widths, before vs after

| Width | c1 news toggle | c2 | c3 targets (map-owned) | c4 keyboard | c5 z-index | raw coverage | **union coverage** |
|---|---|---|---|---|---|---|---|
| 1296 | FAIL → **PASS** (x 1370 → 618) | FAIL → FAIL¹ | 20 → 16 (**0 map-owned**) | PASS → **PASS** | FAIL → **PASS** | 21.9 → 29.4 | **21.2 → 21.2** |
| 639 | FAIL → **PASS** (x 400) | FAIL → FAIL¹ | 19 → 17 (**0**) | PASS → **PASS** | FAIL → **PASS** | 24.3 → 38.6 | → 26.5 |
| 481 | FAIL → **PASS** (x 339) | FAIL → FAIL¹ | 19 → 17 (**0**) | PASS → **PASS** | FAIL → **PASS** | 27.6 → 42.4 | → 29.2 |
| 375 | FAIL → **PASS** (x 132) | FAIL → FAIL¹ | 20 → 17 (**0**) | PASS → **PASS** | FAIL → **PASS** | 27.5 → **21.7** | → **20.2** |
| 320 | FAIL → **PASS** (x 105) | FAIL → FAIL¹ | 20 → 17 (**0**) | PASS → **PASS** | FAIL → **PASS** | 28.6 → **23.0** | → **21.3** |

`zIndexViolations` is `[]` at every width (baseline: `legend=700` at every width). `entryPointCount`
0 → 3. The news toggle is on-screen and **labeled** at every band (long label ≥640, short below).
`filterOverflowPx` from `.filters-row`: **507 / 727 / 885 / 991 / 1046 → the element no longer exists.**

¹ **c2's residual FAIL is `.map-canvas`, Leaflet's own tile container, and it was in the baseline
too** (428 px at 1296, 912 px at 375). See §4 — this is a scope statement about the instrument, not
a defect this phase introduced and not a threshold change.

## 2. The coverage question, settled by measurement rather than by argument

The raw `controlCoveragePct` rises at the wide bands and falls at the narrow ones, which looks
alarming until you measure what it counts. `score.mjs:223-228` sums each control's rect **with no
union**, and the design spec §8 *requires* `data-role` hooks on the rail and on all three entry
points — every one of them a descendant of `.map-topbar`. The same pixels are therefore counted
three times after the rework and once before.

To settle it I **rebuilt the pre-change tree** (`git checkout <PHASE30_BASE_SHA> -- site/src`, full
build, measure, restore) and measured both figures on both builds through the identical harness:

| | pre-change | post-change |
|---|---|---|
| controls entering the sum @1296 | topbar, mode-toggle, legend | topbar, news-toggle, rail, 3× details, legend |
| raw `controlCoveragePct` | 21.9 % | 29.4 % |
| **union coverage (map area actually hidden)** | **21.2 %** | **21.2 %** |
| `.map-topbar` height | **113 px** | **113 px** |

**The map area actually hidden by chrome is unchanged to the tenth of a percent at 1296, and is
materially better at 320/375** (union 21.3 / 20.2 versus a pre-change raw of 28.6 / 27.5). At 375 the
phase clears both F-50's 22.7 % ceiling and `verdict()`'s hard ≤25 % rule, which the **pre-change app
did not** (27.5 %).

At **481–639 the design does cost map area**: union 29.2 % @481 and 26.5 % @639, against pre-change
raw figures of 27.6 % and 24.3 %. That is the tradeoff **F-46 decided explicitly**, at that exact
band, with the user's stated priority "prioriza UI y UX": permanently visible filter entry points
cost area at tablet widths, and discoverability wins. The measured raw 42.4 % @481 is inside F-46's
own accepted 43.1 %. Recorded as **F-56**, which supersedes F-54's raw-ceiling clause — F-54 was
written before either number existed and its raw ceiling cannot be met without deleting hooks the
spec mandates.

One real fix came out of this rather than a re-interpretation: at 481 the topbar was first measured
at **191 px** (union 36.3 %) because every `<summary>` repeated its current value
(`Tipo de delito: Todos los delitos` = 257 px wide), wrapping the rail onto two rows. The summaries
now carry the **dimension label only** — the persistent state summary already carries the values,
which is precisely its job in spec §2 — taking the topbar to **139 px** and union to 29.2 %.

## 3. MAPSH-02 modal proof (verified in a real browser, at 375 px with the FAB visible)

| Check | Result |
|---|---|
| `dialog.matches(':modal')` while open | **true** |
| `<dialog open>` without `:modal` (the thing `grep showModal` cannot distinguish) | false |
| FAB `aria-expanded` while open | **"true"** |
| Focus inside the dialog while open | **true** |
| Close via the sheet's close button → `aria-expanded` | **"false"**, focus returns to FAB |
| Close via `close` event → `aria-expanded` | **"false"**, `closeEventsFired: 1`, focus returns to FAB |
| Real **Escape** key (top-level tab) | dialog closes, `close` fires, `aria-expanded` → "false" |
| Rail vs FAB at 375 | rail `display:none`, FAB `display:flex` |

**One real defect found and fixed here.** After a native Escape dismissal, focus landed on `<body>`
rather than the FAB — the close-button path restored focus explicitly, the `close`-event path did
not. `handleDialogClose` now calls `fab.focus()`. Spec §6 requires focus to return to the invoking
control on *every* dismissal path.

## 4. Effect assertions — every control still drives the state it drove before

Run against the real page; these are the invariant the premortem named as having no gate at all.

| Control | Assertion | Result |
|---|---|---|
| News toggle | `.ev-dot` pin count | **0 → 1412 → 0**, `aria-pressed` tracks |
| Crime type | 9 options incl. `Homicidios`; selecting it sets `aria-checked` and the state summary | **"Índice · Homicidios · 2025"** |
| Mode | `Índice compuesto` ↔ `Por familia` repaints the choropleth and the legend title | legend switches to `Incidencia reportada` + numeric bands |
| Year | 2025 → 2019 reaches the fetch effect | state summary → **"Por delito · Todos los delitos · 2019"** |
| Mutual exclusion | opening `Año` closes `Tipo de delito` | `[true,false,false]`, and `aria-expanded` **matches** — the React-state model does not lie |
| `?cut=13101` | ResultPanel opens on Santiago, map flies (zoom 12) | **PASS** (deep link survives the rework) |
| `?region=13` | fits the map to Región Metropolitana **without** opening ResultPanel | **PASS** — tiles at zoom **8**, panel closed |
| `?region=99999` | silent degradation | **PASS** — default extent (zoom 4), panel closed, **zero console errors/warnings** |
| `?cut=13101&region=05` | the commune deep link WINS | **PASS** — panel on Santiago at zoom 12, no flight to Valparaíso |
| **Geolocation** (criterion 4, and the one item no other artifact evidenced) | the locate button still calls `navigator.geolocation` and degrades gracefully when denied | **PASS** — button measures **44×44** with `aria-label="Mostrar mi ubicación"`; clicking it calls `getCurrentPosition` with a real error callback, and a simulated `PERMISSION_DENIED` surfaces the toast **"No se pudo obtener tu ubicación"** rather than failing silently or throwing |
| **MAPSH-07** shared vocabulary via DATA, no code edge between the map island and the news pages | grep the import graph both directions | **PASS** — zero imports from `src/components/map/**` to any news module, and zero from the news pages/modules to any map component. `mapFilterDefs.ts` reaches the shared vocabulary through `./familyDefs`, the same data module the news side reads independently |

## 5. Two measurement artifacts that first looked like defects — recorded so they are not rediscovered

1. **A `<dialog>` does not respond to synthetic key events, and `press_key` does not cross into an
   iframe.** My first modal test dispatched a synthetic `KeyboardEvent('Escape')` and then read
   `closeEventsFired: 0` — the same signature Phase 29's iteration 1 recorded and treated as a code
   defect. It is an artifact: with a **real** key press on a top-level tab the `close` event fires
   exactly once. Phase 29's finding may well have been this same artifact.
2. **Leaflet does not run `fitBounds`/`flyTo` or fetch tiles in a background tab.** Measured in
   background tabs, `?region=13`, `?region=99999`, `?cut=13101` and a plain load ALL returned tiles
   at zoom 4 — which reads exactly like "the new feature is a silent no-op", the premortem's §12
   failure. Foregrounding the tab (`background: false`) resolved it: zoom **8** for `?region=13`,
   **12** for `?cut=`, **4** for the unknown region. **Any future map measurement must be taken in a
   visible tab**, and a "no effect" result from a background tab is worthless.

## 6. Suite state at close

`npm run build` OK · **vitest 45** (37 + 8 new) · **16/16 validators** · `astro check` **4 errors /
0 warnings**, all in `ComparatorPairsLinks.astro:28` (unchanged baseline) · `phase30-gate.mjs`
**exits 0 on all 9 assertions**, each proven falsifiable by mutation · protected Leaflet layer files
and `score.mjs` **byte-identical** to `PHASE30_BASE_SHA` · zero new dependencies.

## 6b. After the Opus code review and fix cycle 1 (final measured state)

The review returned 0 CRITICAL / 2 HIGH / 7 MEDIUM / 4 LOW. All 13 were addressed. Re-measured after
the fixes — and **the fix cycle itself introduced three regressions, caught only because the whole
rubric was re-run rather than the fixer's report believed**:

| Regression introduced by fix cycle 1 | Cause | Resolution |
|---|---|---|
| coverage @375 rose 21.7 → **27.4 %**, breaching F-50's 22.7 % ceiling AND STRESS.md's frozen ≤25 % | M-01 kept the state summary visible at ≤480, growing the topbar 111 → 137 px | summary is visually-hidden (not removed) at ≤480 — the `aria-live` announcement survives, the pixels return |
| c3 gained a map-owned violation: the rail itself at **296×18** | the rail stayed in flow at ≤480 to host the summary, and it carries `data-role` | `StateSummary` extracted out of the rail and rendered by `MapTopbar`; the rail is `display:none` again below 480 |
| topbar @1296 grew 113 → **139 px** (coverage 29.4 → 32.9) | the extracted summary became a direct child of the column-flex topbar, forming its own row at every band | summary moved into `.map-topbar-row1` with `flex-wrap` — one row at ≥1024, wraps at the narrow bands |

A fourth interaction was caught the same way: H-01's band-aware `--map-topbar-h` was tuned to the
*pre-fix* heights, and M-01 changed them — and at exactly 1023 px the `max-width: 1023px` form did not
match while the topbar was already 139 px. Inverted to a tall base with a `min-width: 1024px`
override, so the badge errs low rather than landing inside the topbar.

**Final measured state (post-fix-cycle):**

| Width | c1 | c3 map-owned | c4 | c5 | raw coverage | topbar | badge clears topbar | summary |
|---|---|---|---|---|---|---|---|---|
| 1296 | PASS | **0** | FAIL¹ | PASS | 29.4 | 113 | ✔ | fits, 1 line |
| 1024 | PASS | **0** | FAIL¹ | PASS | 29.4 | 113 | ✔ | fits, 1 line |
| 639 | PASS | **0** | FAIL¹ | PASS | 35.3 | 139 | ✔ | fits |
| 481 | PASS | **0** | FAIL¹ | PASS | 39.1 | 139 | ✔ | fits |
| 375 | PASS | **0** | **PASS** | PASS | **21.7** | 111 | ✔ | visually hidden, announced |
| 320 | PASS | **0** | **PASS** | PASS | **23.0** | 111 | ✔ | visually hidden, announced |

¹ **c4's FAIL at ≥481 is a documented instrument false positive (F-58), not a regression.** The
roving tabindex the review's H-02 required sets `negativeTabindexCount: 9`, and `score.mjs:131-137`
reads any rendered negative tabindex as a trap signal. The nine elements are radios inside **closed**
`<details>` panels. **The real Tab walk is the ground truth and it is clean**: from the news toggle,
focus moves `news-toggle → Año → Tipo de delito → Modo → zoom "+"` — precisely spec §6's documented
order — skipping all nine and exiting the rail. `score.mjs` was not edited.

`?region=05` (the padded form) now resolves: the map moves west to tile column x=3, because region 5
includes Isla de Pascua and Juan Fernández, so its combined bounds span the Pacific and the fit stays
at zoom 4. **This is also why my earlier `?cut=13101&region=05` precedence test could not have
failed** — `region=05` resolved to nothing before the M-07 fix. Re-tested with `?region=13`: zoom 8,
panel closed; with `?cut=13101&region=05`: panel on Santiago at zoom 12.

## 6c. Independent Opus re-review and fix cycle 2 (final)

The re-review verified the 13 findings **by execution and mutation** (it rendered `FilterFields`
through `react-dom/server` to check the roving tabindex in every reachable state, and mutated the
gate's own rules): **8 CLOSED, 4 PARTIAL, 1 OPEN**, plus **three new MEDIUM findings the fix cycle
introduced**. All three are now fixed and verified:

- **N-1 — the backdrop light-dismiss also covered the sheet's own visible gutter.** The `<dialog>`
  carried `padding: 16px`, and the handler closes when the click target *is* the dialog element — so
  the 16 px ring inside the visible sheet dismissed it, which on a bottom sheet is exactly where a
  thumb rests. Padding moved to a `.filter-sheet-inner` wrapper. **Verified in the browser:** the
  inner element now fills the dialog exactly (gutter 0 px), `elementFromPoint` at the sheet's top edge
  returns `.filter-sheet-inner`, not the dialog, so that click can no longer dismiss.
- **N-2 — the `?cut=` precedence rule was wired but ungated.** The re-review proved that replacing the
  guard with `if (idx)` — deleting the rule entirely — left the suite at **51/51 green**. The rule is
  only observable in a browser, so it is now guarded at source level (`phase30-gate.mjs` assertion 8,
  the F-24 precedent). **Proven falsifiable:** on the mutated tree the gate exits 1 naming the missing
  guard while vitest still reports 51/51 — which is precisely the hole it was written to close.
- **N-3 — dead code left by the `StateSummary` extraction** (`band` state, its resize listener and the
  unrendered `stateSummary` string in `EntryPointsRail`). Removed.

Also cleaned: a stale `map.css` comment block that still described the superseded M-01 approach and
contradicted the code beside it.

**Confirmed by the re-review, not just claimed:** the three orchestrator corrections in §6b broke
nothing — no band's summary can wrap, no topbar grew, no new sub-44 px target appeared, and the rail
and FAB are mutually exclusive at every width. It also independently confirmed F-58's account: the
arrow-key handler adds **no** `keyInterceptors` signal, so c4's FAIL is attributable solely to the
roving tabindex.

**Final suite:** build OK · **vitest 51** · **16/16 validators** · **pytest 344 passed / 1 skipped /
1 xfailed** · astro check **4 errors / 0 warnings** at the baseline location · `phase30-gate.mjs`
**12/12 PASS** · protected Leaflet files and `score.mjs` byte-identical.

**Final rubric, all five widths:** c1 **PASS**, c3 **zero map-owned violations**, c5 **PASS** with
`zIndexViolations: []`, badge clears the topbar everywhere, coverage **21.7 % @375** and **23.0 %
@320** (baseline 27.5 / 28.6), summary fits on one line at every band where it is visible.

**Carried, with the reason recorded rather than fixed** (fix cycles are capped at 2):
- **L-03** — `AVAILABLE_YEARS` offers 2026, which has no payload yet; selecting it shows the
  "no data" toast. Pre-existing behaviour of the ported year list, now pinned by a test. Worth a
  Phase 31 look.
- **L-04** — the gate compares astro-check error *locations*, so a same-location regression or a new
  *warning* would not redden it. Deliberate: the count-based alternative is the one that invites
  baseline-bumping.
- Two LOW items about an unreachable radiogroup state on an out-of-vocabulary `crimeFamily` and the
  `offsetParent` guard being a behavioural no-op today.

**One deviation stated plainly rather than framed as a fix:** at ≤480 px the state summary is
screen-reader-only, so **spec §2 item 4 is met for assistive tech but not for sighted users at that
band**. That is a deliberate trade against F-50's ceiling and STRESS.md's frozen ≤25 % rule — showing
it cost 26 px of topbar and pushed coverage to 27.4 %. At that width the sheet shows the live
selection when opened. Recorded as a spec deviation, not a silent one.

## 7. Accepted and recorded, not fixed

- **Residual sub-44 px targets** (16–17 per width) are the skip link, site title, locale links,
  header/footer nav and Leaflet's attribution anchors — all outside MAPSH-05's confinement (F-51).
  **Zero** map-owned violations remain at any width: the locate button (32→44), the zoom buttons
  (36→44), the search input (17→44 min-height) and the mobile legend `<summary>` (18→44) were all
  raised by this phase.
- **c2 cannot return PASS on a real Leaflet page.** `score.mjs`'s overflow scan is document-wide and
  `.leaflet-container` legitimately overflows its own box with tiles; it did so in the baseline too.
  The meaningful reading — *no control overflows* — holds: `hiddenOverflowElements` contains exactly
  one entry, `.map-canvas`, at every width, where the baseline contained `.filters-row` with a
  suppressed scrollbar as well. `score.mjs` was NOT edited (F-49). Recorded as **F-57**.
- **The legend's numeric bands are computed from the overall commune rate** (`MapIsland.tsx:201,290`
  — `computeQuantileBreaks(payload.comunas.map(c => c.rate))`) and therefore do not vary by selected
  family, including homicide. Pre-existing, unchanged by this phase, and worth a line in Phase 31's
  methodology pass.
- **`mapWidthRatio` stays 0.627** at 1296 — full-bleed is out of scope per F-43.
