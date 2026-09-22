# Phase 29 — Independent UI Review

**Reviewer**: independent pass, spawned specifically to break the self-review circularity (F-06 / F-11 / F-23).
**Read**: `29-BASELINE.md`, `29-DESIGN-SPEC.md`, `STRESS.md`, `MANIFEST.md`, `score.mjs`, `iter-1/` + `iter-2/` (SCORE.md, both HTML, all four PNGs), `REQUIREMENTS.md` (MAPUX/MAPSH text), and — for Q3 only — the real `site/src/components/map/map.css` and `MapTopbar.tsx` (plus `FiltersRow.tsx`, needed to check a spec claim about where `.ev-chip` lives).
**Deliberately not read**: `29-01-PLAN.md`, `29-02-PLAN.md`, any `*-SUMMARY.md`, the premortem, STATE.md's decision log.
**Files modified**: this one only. No `site/` file was touched.

---

## Verdicts

| Q | Subject | Verdict |
|---|---|---|
| 1 | Iteration 2 genuinely distinct? | **PASS** (with one scope caveat) |
| 2 | Which criteria are falsifiable? | **FLAG** — c1/c2/c3 are real; **c4 and c5 are decoration** |
| 3 | Spec implementable without re-designing? | **BLOCK** — 4 missing decisions, 3 factually wrong citations |
| 4 | Decisions unsupported by evidence? | **FLAG** — 3 unsupported, 1 arithmetic error repeated 3x |

**Phase 29 is NOT accepted as it stands.** The BLOCK is on Q3 and is repairable by editing `29-DESIGN-SPEC.md` alone — no re-running of the loop is required. The loop itself (Q1) is sound and its evidence is unusually honest.

---

## Q1 — Is iteration 2 a distinct design or a restyle? **PASS**

Judged from the HTML and the PNGs, not the prose.

**The structural difference is real and is a topology change, not a restyle:**

| | iter-1 | iter-2 |
|---|---|---|
| Filter mechanism | one `.filters-row` flex container, `overflow-x:auto`, 10 sibling `.chip` buttons in a single undifferentiated list (`iter-1/desktop.html:118-130`) | three `<details class="entry">` disclosure widgets, each with its own `<summary>` label and an absolutely-positioned `.entry-panel` (`iter-2/desktop.html:158-198`). **No element in the document has `overflow-x:auto`.** |
| Dimensions | flattened — year, family and mode all as peer chips | separated and labeled — `Año` / `Tipo de delito` / `Modo` |
| Files | two viewport-specific documents, **zero media queries** in either | one document with real media queries; `desktop.html` and `mobile-375.html` are byte-identical (verified: both md5 `5cc1ae10…`) |
| New surface | — | persistent `.state-summary` (`Índice · Todos los delitos · 2025`) |
| Affordance strategy | *patch* the scroll container (mask fade + visible scrollbar + `›` hint) | *delete* the scroll container |

The screenshots confirm it independently: `iter-1/desktop.png` shows the ten-chip row bleeding under a mask fade at the right edge with a `›` affordance; `iter-2/desktop.png` shows three labeled pills plus a grey state line and **no chip row at all**. The `.mode-toggle` (Índice / Por delito, top-right in iter-1) is gone from the iter-2 shot, folded into the `Modo` entry point. `entryPointCount` 0→3 is a consequence of the restructure, not a token.

This is a different answer to the same problem, derived from a named source (CrimeMapping finding 1). It is not a recolour.

**Caveat, non-blocking**: the redesign is **desktop- and mid-width-only**. iter-1's `mobile-375.html` already had the news toggle lifted into the topbar, the FAB, and the `showModal()` bottom sheet. Compare `iter-1/mobile-375.html:105-134` with iter-2's 480px band — the mobile shell is materially the same design in both iterations. The claim "two full iterations" survives, but "two iterations of the *mobile* shell" would not, and the spec should not be read as having iterated mobile twice.

---

## Q2 — Which criteria are falsifiable, and which are true by construction? **FLAG**

Checked against `score.mjs` itself, not the prose.

### Genuinely falsifiable — these earn their place

- **c1 `newsToggleDiscoverable`** — `inViewport && isTopmost`. Returned **FAIL** on a real input (baseline, `.ev-chip` at x=1370) and on a designed input (`iter-1` `breakpoint-481`, `newsToggleInViewport:false`). The `elementFromPoint` topmost half is also non-vacuous: both sketches deliberately place a `.popup-dummy` inside the `.leaflet-popup-pane` at z 700 overlapping the toggle, so a toggle without an explicit z-index would lose. Real.
- **c2 `filtersDiscoverable` + `filterOverflowsContainer`** — the whole-document overflow scan (`score.mjs:84-98`) cannot be defeated by renaming a class, and it caught 52 / 479 / 637 px on iteration 1. The 637 px figure is the strongest evidence in the phase that the harness bites: it is **worse than the 507 px baseline** it was built to fix. Real.
- **c3 `touchTargetViolations`** — caught the 32 x 32 locate button the designer carried over from the real `.locate-btn-visible`. Real. (Minor: the selector includes `[data-role]`, so non-interactive wrapper divs like `.entry-points` get size-scored. Harmless here, but a small decorative `data-role` container would produce a false FAIL in Phase 30.)

### True by construction — decoration

- **c4 `keyboardTrapFree` — cannot FAIL, and will be structurally incapable of failing in Phase 30.**
  It is `negativeTabindexCount === 0 && keyInterceptors.length === 0`, where `keyInterceptors` is a substring scan of **inline `<script>` textContent** (`score.mjs:124-130`). It returned PASS at every one of the 16 scored rows *and* at the baseline. `iter-1/SCORE.md:40` says so outright ("by construction").
  The serious part is forward-looking: `29-DESIGN-SPEC.md` §8 and §12 require this same file to run **unchanged against the real `/map/`** as Phase 30's acceptance instrument. On the real build, Astro/React ship as `<script type="module" src=…>` — `textContent` is empty — so `keyInterceptors` is **always `[]` there regardless of what the bundle does**. c4 will report PASS on a real focus trap. A criterion that is guaranteed-PASS on the artifact it is meant to gate is worse than no criterion, because it renders as coverage.
- **c5 `zIndexAndOcclusion` — never returned FAIL, and cannot detect the one real z-index defect this phase found.**
  `criterion5` is `zIndexViolations.length === 0`, and a violation is `(auto && !governed) || (z > 0 && z < 700)` (`score.mjs:180-182`). Every control in both sketches is explicitly >= 700, so the predicate is unreachable. It was PASS in all 16 rows.
  Worse: the defect the phase actually discovered — **`.legend` at z-index 700 tying `.leaflet-popup-pane` at 700** (verified: `map.css:131` is `z-index: 700`) — is *exactly the value the predicate excludes*, since `700 < 700` is false. `MANIFEST.md`'s baseline row prints **"c5 — FAIL"**, but `score.mjs` run against that baseline would return `criterion5: PASS`. That FAIL is a prose judgment by the author, presented in an instrument column. It is the only FAIL c5 has ever shown, and the instrument did not produce it.
  The coverage half is also mis-plumbed: `controlCoveragePct` gates only inside `verdict()` and only at `<= 375`, while the SCORE.md tables print `criterion5`, which ignores coverage entirely. That is why `iter-2` `narrow-320` prints "c5 PASS" at **32.2 %** coverage when `verdict().c5_zIndexAndOcclusion` is **false** at that row.

**Blunt summary**: MAPUX-03 names five criteria. Three of them do work. Two are ceremony, and one of those two is the criterion the design spec leans on hardest (§3's entire pinned z-index ladder rests on a check that cannot fail). This does not invalidate iteration 2 — it invalidates reading its c4/c5 columns as evidence.

---

## Q3 — Does the spec let Phase 30 implement without re-designing? **BLOCK**

Every citation checked against the real files.

### Citations that are correct (recorded so the fix list is trusted)

- The z-index ladder in §3 is accurate: `.map-topbar` 800 (`map.css:32`), `.mode-toggle` 801 (`:110`), `.legend` 700 (`:131`), `.zoom-ctl` 700 (`:262`), `.search-dropdown` 900 (`:369`), `.map-error-overlay` 900 (`:410`), `.result-panel` 700 (`:456`), `.toast` 1000 (`:808`), `.partial-year-badge` 800 (`:905`). All nine verified.
- `.legend` **does** tie `.leaflet-popup-pane` at 700. Real defect, correctly reported.
- `.filters-row` **does** suppress its affordance twice (`scrollbar-width:none` at `map.css:53` plus `::-webkit-scrollbar{display:none}` at `:56-58`). Correct in substance; the cited range `47-59` is off by one (the rules are `46-58`).
- The five `@media` blocks are at exactly `192 / 210 / 240 / 271 / 463`. Line numbers correct.
- EN label `Recent incidents` matches `FiltersRow.tsx:119`. `.ev-chip` is indeed the last child of the row (`FiltersRow.tsx:112-121`).

### Factually wrong citations — must be corrected

1. **§4's breakpoint bands are off by one pixel, in the phase whose entire subject is pixel bands.** The real rules are `@media (max-width: 480px)` (`map.css:210`, `:240`) and `@media (max-width: 640px)` (`:192`, `:463`) / `@media (min-width: 640px)` (`:271`). The real bands are therefore **<=480 / 481-639 / 640+**. The spec's table says **"< 480"** and **"480 - 639"**, which puts 480 px in the wrong band and contradicts `STRESS.md`'s own `breakpoint-481` rationale ("one pixel above `map.css`'s `max-width: 480px` band"). Phase 30 implementing §4 literally will write `max-width:479px` and produce a one-pixel dead zone.
2. **The sketch's own breakpoints do not match `map.css`, and both the sketch header and §4 claim they do.** `iter-2/desktop.html:112` is `@media (max-width:639px)`; the real rule is `max-width:640px`. The sketch comment (`iter-2/desktop.html:16`) asserts "real bands at 480 and 640 (map.css:192/210/240/271)" — it does not have a 640 band. At exactly 640 px the sketch and the app diverge, and 640 is a real device width. Small in effect, but the spec inherits the claim as verified fact.
3. **§4 claims `<480: .result-panel is a 40vh bottom sheet`. The sketch that was scored does the opposite**: `iter-2/desktop.html:128` sets `.result-panel{display:none}` at `<=480` with the comment *"not shown at rest; would otherwise cover the FAB"*. The spec pins a behaviour the evidence deliberately did not test, and pins it to the exact configuration the sketch avoided because it broke. See missing decision (a).

### Missing decisions — Phase 30 must re-design to fill these

a. **The FAB x `.result-panel` collision is unresolved and absent from the spec.** `iter-1/mobile-375.html:54-57` raised it in a comment ("It would be covered by `.result-panel`'s 40vh bottom sheet when a commune is selected — recorded in SCORE.md as an interaction to resolve"). It was never resolved; iteration 2 sidestepped it by hiding `.result-panel`. The spec then asserts both a bottom-right FAB (§2.3) and a 40vh bottom sheet (§4) in the same band, with no rule for what happens when a commune is selected. **This is the single most concrete re-design Phase 30 is forced into**, and it is the one the loop knowingly deferred twice.

b. **The fate of `FiltersRow.tsx` and of the `.filters-row` / `.chip` / `.ev-chip` CSS is never stated.** Today the year select, all family chips and the news toggle live inside `FiltersRow.tsx` (`:112-121`), rendered by `MapTopbar.tsx:52`. §2.1 says "the flat scrolling filter row is deleted" but never says whether `FiltersRow.tsx` is deleted, gutted or renamed, nor whether the `.filters-row` rules leave `map.css`. Not pedantry: `score.mjs:39` and `:67` fall back to **`.ev-chip`** and **`.filters-row`** as selectors. If any stale node with those classes survives the refactor, Phase 30's own regression instrument silently measures the wrong element — the exact class of bug the rubric already hit twice ("`querySelector` picked the hidden filter entry").

c. **Folding `Modo` into an entry point breaks MAPSH-05's stated file confinement, and the spec does not acknowledge it.** `MapTopbar.tsx:19` receives the mode toggle as a `modeToggle?: React.ReactNode` **prop from its parent** and renders it in row 1 (`:51`). Making `Modo` one of the three `<details>` entry points requires editing the parent (`MapIsland.tsx`) to stop passing it — a file §9/MAPSH-05 does not list as in scope ("`MapTopbar.tsx` + sibling control components"). Either the prop stays and `Modo` is not an entry point, or `MapIsland.tsx` joins the allowed set. The spec must pick one.
   Related internal inconsistency: §3's ladder keeps `.mode-toggle` at 801 and §4 discusses its `position:static` reset, while §2.1 dissolves the mode toggle into an entry point. Both cannot be true.

d. **No dismissal behaviour is specified for the `<details>` entry points.** Native `<details>` does **not** close on outside click or on ESC. On a map, where the next click is usually a commune polygon, an entry panel that stays open over the map is a defect. §5 pins only "one panel open at a time". This needs a decision — and it needs new JS, which bears on how §9/MAPSH-02's "zero new JS dependencies" is being read (no *dependency*, but non-trivial new *code*).

e. **Minor but pinned-wrong ARIA.** §5 pins `<button role="radio" aria-checked>`; the sketch puts those buttons inside `role="group"` (`iter-2/desktop.html:163`, `:174`, `:191`). `role="radio"` must be owned by a `radiogroup`, not a `group`. Phase 30 will ship an invalid ARIA tree straight from the spec.

f. **`.legend-mobile` is claimed but was never in iteration 2.** §4 says "`.legend-mobile` stays a `<details>`" below 480. True of the real app (`map.css:210-238`), but **iteration 2's sketch has no `legend-mobile` at all** — it renders the full desktop `.legend` at every width (`iter-2/desktop.html:220-228`; visible as a full-size legend panel in `iter-2/mobile-375.png`). So every narrow-width `controlCoveragePct` figure — 22.7 % @375, **32.2 % @320** — was measured against a legend larger than the one the spec describes. Conservative rather than flattering, so not dishonest; but §12's `coverage <= 22.7 % at 375 px` bar is not reproducible against a shell built to §4.

**Verdict: BLOCK.** Items (a), (b) and (c) each force a design decision during implementation, which is exactly what §7's opening promise ("this spec pins values so Phase 30 implements rather than decides") rules out for a declared regression-risk phase. Fixing them is a spec edit, not another loop.

---

## Q4 — Decisions the evidence does not support **FLAG**

1. **"Nine criterion x condition cells moved FAIL->PASS" is arithmetically wrong — it is eight.** Counting `iter-1/SCORE.md`'s table: desktop-1296 c3 (1); content-growth c2, c3 (3); breakpoint-639 c2, c3 (5); breakpoint-481 c1, c2, c3 (8). Eight FAILs existed; eight became PASS. `iter-2/SCORE.md`'s own table carries exactly **eight `↑` marks**. The figure "nine" is stated three times — `MANIFEST.md`, `iter-2/SCORE.md`, and `29-DESIGN-SPEC.md` §1 — and propagated into the accepted spec unchecked. The substantive claim (iteration 2 fixed everything iteration 1 broke) is true; the headline number is not.
2. **"None regressed" is true only after excluding four cells.** c1 and c2 at `longest-label` and `text-150pct` went PASS (iter-1) -> **FAIL** (iter-2). `iter-2/SCORE.md` is honest that this is modal-backdrop occlusion and that iter-1's PASSes were vacuous — that is the right reading — but the correct phrasing is "four cells became unscoreable", not "none regressed".
3. **The 25 % coverage ceiling's own justification is mis-anchored, so the threshold is softer than it reads.** `STRESS.md` writes: `controlCoveragePct <= 25 %` **at 375 px** `(baseline is 24.7 %, so this forbids getting worse)`. But **24.7 % is the desktop-1296 baseline figure** — `29-DESIGN-SPEC.md` §0's own table puts it in the "Desktop 1296" column, and no 375 px baseline coverage number exists anywhere in `29-BASELINE.md` §2. The ceiling that gates mobile was set from a desktop measurement. Nothing was tampered with after the fact, but "this forbids getting worse" is not something the evidence establishes at 375 px.
4. **On the coverage overrun: honest in disclosure, but it resolves its own ambiguity in its own favour.** `iter-2/SCORE.md` finding 2 states the mismatch plainly and refuses to loosen the threshold — that is exactly right, and it is the single best piece of self-criticism in the phase. However, `STRESS.md`'s prose scopes the ceiling to 375 px while `score.mjs:215,223` applies it to **every width <= 375**, which makes 320 px (32.2 %) a genuine `verdict()` failure. The spec (§10, §12) adopts the *prose* reading and re-states the bar as "coverage <= 22.7 % at 375 px", dropping the 320 px breach from the acceptance bar. It is disclosed, not hidden, and carried as a Phase 30 constraint; but a pre-registered threshold that turns out to have two readings should be resolved to the **stricter** one, not the one the design passes. **FLAG, not BLOCK** — because it is fully surfaced, and because 43.1 % @481 is recorded rather than buried.

### On the three items I was specifically asked to check

- **"Two complete iterations" — supported.** Two distinct designs, both scored under the same eight pre-frozen conditions, with iteration 1 genuinely failing three ways. The one honest qualification is Q1's caveat: the mobile shell was only designed once. `check-iteration.mjs` exists on disk, as claimed.
- **Rubric corrections during the loop — none loosened a threshold.** All three (`auto` z-index governed by an ancestor; `querySelector` picking the `display:none` entry; `display:none` controls scored for z-index) change **which element is measured**, not **what value passes**. Each is a correction I would have made myself, and the `governedByAncestor` fix was demonstrated falsifiable in both directions before being accepted (`iter-1/SCORE.md:48`). `STRESS.md`'s freeze rule is intact. **No violation found here.** The one thing the corrections *did* do is progressively narrow c5's already-unreachable failure predicate — a Q2 problem, not a freeze problem.
- **`iter-2/mobile-375.png` — the explanation is honest and the image corroborates it.** I read it: the news toggle is a bare teal circle containing an orange dot, with **no text label**, exactly as `iter-2/SCORE.md` finding 1 describes; the FAB is genuinely outside the captured region. Retaining a pre-fix screenshot as the evidence for a defect the rubric missed, rather than re-shooting a flattering one, is the correct call and is labelled clearly at `iter-2/SCORE.md:94`. **No issue.** This defect — caught by looking, not by measuring — is also the best argument in the phase for why Q2's c4/c5 matter.
- **Control-coverage overrun — handled honestly**, see item 4. Disclosed in three places (`MANIFEST.md` warn-marks, `iter-2/SCORE.md` finding 2, spec §10). FLAG only for choosing the looser of two readings.

### One requirement observation, outside the four questions

`REQUIREMENTS.md:76` (MAPUX-05) reads: *"The loop terminates in an accepted design spec **plus a human acceptance gate**; Phase 30 does not start until that gate passes."* The spec's status line reads *"accepted by Fable-proxy… Human review **deferred, not waived**."* On the requirement's own text, MAPUX-05 is **not yet satisfied**, and a deferred gate is not a passed gate. Whether the Fable-proxy convention substitutes for the human is a governance call for the returning human, not for me — but MAPUX-05 should not be marked Complete in the traceability table on this evidence.

---

## What would clear the BLOCK

Spec edits only — no new iteration required:

1. Correct §4's bands to **<=480 / 481-639 / 640-1023 / >=1024**, and note that the sketch used 639 where `map.css` uses 640.
2. Decide the FAB x `.result-panel` interaction below 480, or state it as an explicit Phase 30 decision with the constraint that the FAB must stay reachable while a commune is selected.
3. State the disposition of `FiltersRow.tsx` and of the `.filters-row` / `.ev-chip` CSS, and require Phase 30 to verify `score.mjs` binds to the new `data-role` nodes and not to surviving legacy classes.
4. Resolve `Modo`: either add `MapIsland.tsx` to MAPSH-05's in-scope set, or keep the mode toggle as a prop and drop it as an entry point. Then reconcile §3's `.mode-toggle` 801 entry with §2.1.
5. Specify dismissal for the `<details>` panels (outside-click / ESC).
6. Change §5's option container from `role="group"` to `role="radiogroup"`.
7. Fix "nine cells" -> "eight cells" in §1 (and in `MANIFEST.md` / `iter-2/SCORE.md`).

## Recommendations regardless of the BLOCK

- **Do not let `score.mjs` serve as Phase 30's acceptance instrument for c4 and c5 without repair.** c4's inline-`<script>` scan is inert against a bundled Astro/React build and will report PASS unconditionally. c5 cannot flag the 700-vs-700 legend/popup tie it is credited with finding. Phase 30 needs c4 replaced with a real focus-order walk, and c5's predicate widened to `z <= 700` for controls that must clear `.leaflet-popup-pane`.
- **Gate coverage at the stricter reading** (<=25 % at every width <=375) so the 320 px figure is a tracked failure rather than an out-of-scope note.
- The F-40 `BaseLayout.astro` cross-origin redirect warning (spec §11) was **outside my permitted read set** and is therefore unverified by this review. It should be confirmed by whoever fixes it.

---

**Bottom line.** The loop is real, the frozen conditions did their job, iteration 2 is a genuine second design, and the phase's self-reporting is more candid than most — the pre-fix screenshot, the vacuous-PASS admission and the coverage overrun were all volunteered, not extracted. The failure is downstream: the *spec* is not yet a build order. Three implementation decisions are missing, three citations are wrong, and two of the five acceptance criteria cannot fail. Fix the spec; keep the loop.

---

# Fable response — fix cycle 1 (2026-07-30)

Every finding was accepted. Nothing was argued down. The BLOCK on Q3 is resolved; the FLAGs on Q2 and Q4 are resolved by correcting the instrument and the arithmetic.

## Q2 — the two decorative criteria are fixed, and the fix is verified against the real app

**c4 (keyboard) — was structurally unable to fail on the real target.** It scanned `document.querySelectorAll('script')` **textContent**, which is empty for the `<script type="module" src=…>` bundles the real `/map/` ships — so it would have reported `keyInterceptors: []` and PASS on a page with a genuine focus trap, while §8 and §12 make this file Phase 30's regression instrument for exactly that page. It now **fails closed**: `criterion4: 'NOT_MEASURED_FAIL'` whenever external scripts with no inline text are present, with a note naming how to settle it (grep the built chunk, plus a real Tab walk).

Running it against the real `/map/` then exposed the **opposite** defect in the same criterion: `negativeTabindexCount` counted a deliberate `display:none` aria sentinel (`MapIsland.tsx:500`), reporting a keyboard trap on a page that has none. An element that cannot receive focus cannot trap it, so only rendered elements are counted now.

**c5 (z-index) — the predicate excluded the one value it existed to catch.** `z > 0 && z < 700` skips *exactly* 700, which is `.leaflet-popup-pane`'s own z-index and therefore the precise defect this phase found on the live map (`.legend` at 700, `map.css:131`). You were right that `MANIFEST.md` printed "baseline c5 FAIL" while the instrument would have returned PASS. Corrected to `<= 700` and re-measured:

| Target | c5 before | c5 after |
|---|---|---|
| Real `/map/` | (would have been) PASS | **FAIL** — `zIndexViolations: ["legend=700"]` |
| iter-1 | PASS | **FAIL** — it inherited `.legend { z-index: 700 }` unchanged |
| iter-2 | PASS | **PASS** — `.legend` raised to **750**, clear of the popup pane |

`iter-1/SCORE.md`'s c5 column is corrected to FAIL at every condition; its raw JSON blocks are left **byte-unchanged** as the honest record of what was measured under the old predicate, with that stated in place.

**The decisive check**: `score.mjs` now run unchanged against the real `/map/` returns **c1 FAIL, c2 FAIL, c3 FAIL, c4 PASS, c5 FAIL** — reproducing the entire hand-measured baseline (toggle at x=1370, 507 px overflow with `scrollbarSuppressed: true`, `legend=700`, ratio 0.627). Four of five criteria fail against a real input and the fifth correctly passes. Added to the spec as §0.

## Q3 — BLOCK resolved

| Finding | Resolution |
|---|---|
| Bands off by one (`max-width` is inclusive) | §4 now reads **≤ 480 / 481–639 / 640–1023 / ≥ 1024**, and says so explicitly against the real rules |
| FAB × `.result-panel` collision — flagged in iter-1, never resolved, absent from the spec | New **§4a**, a required decision: the FAB anchors to `calc(40vh + 16px)` above the open panel. Also states plainly that the sketch's `display:none` sidestep is a sketch convenience and not acceptable real behaviour, and that "commune selected" is a state the sketches never modelled |
| `FiltersRow.tsx`'s fate unstated; `score.mjs` falls back to `.ev-chip`/`.filters-row` | New **§9a**: `FiltersRow.tsx` is **deleted, not refactored**, and Phase 30 must assert those classes are gone from `dist/` — otherwise Phase 30's own instrument silently binds to the old markup. This was the sharpest finding in the review |
| `MapTopbar.tsx:19` takes `modeToggle` as a prop from `MapIsland.tsx`, which MAPSH-05 excludes | **§9a** gives two admissible resolutions and requires Phase 30 to pick one *and record it*: (a) preferred — authorize a narrowly-scoped `MapIsland.tsx` prop-wiring edit, since MAPSH-05's intent is protecting the Leaflet **layer** files; (b) fallback — leave the mode toggle ungrouped, fully within MAPSH-05 as written |
| No dismissal behaviour for `<details>` panels | §6 now pins it: Escape closes and returns focus to `<summary>`; outside click/focus closes; opening one closes the others; non-modal panels must **not** trap focus |
| `role="radio"` inside `role="group"` is invalid ARIA | §5 now requires **`role="radiogroup"`**, and flags that the sketch got it wrong |

## Q4 — corrected

**"Nine cells FAIL→PASS" was eight.** Corrected in `29-DESIGN-SPEC.md` §1, `MANIFEST.md` and `iter-2/SCORE.md`, each noting the miscount rather than quietly editing the number. (The c5 correction above does add a further genuine improvement, but the conservative count of eight is kept, matching iteration 1's recorded FAILs.)

**The ≤ 25 % coverage ceiling was anchored to a desktop figure and applied as a 375 px gate, and the spec resolved the STRESS-vs-code ambiguity in its own favour.** Accurate. The spec's §10 now states the breach without resolving it favourably: the design measures 22.7 % at 375 px, **32.2 % at 320 px and 43.1 % at 481 px**, the frozen threshold may not be loosened after the fact, and the narrower bands are carried into Phase 30 as a known weakness rather than a passed test.

## On your caveat to Q1

Accepted and worth recording: iteration 1's mobile file already carried the FAB and `showModal()` sheet, so **the mobile shell was designed once, not twice**. The two full iterations are unambiguous on the desktop/tablet shell (flat scroll row → grouped disclosure), and the mobile FAB pattern survived from iteration 1 unchanged. `check-iteration.mjs` certifies distinctness on entry-point count and FAIL→PASS transitions, neither of which is mobile-specific.
