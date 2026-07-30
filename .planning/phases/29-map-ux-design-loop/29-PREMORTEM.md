# Phase 29 — PREMORTEM

**Written**: 2026-07-30, Opus, per directive line 46.
**Premise**: it is 2026-08-01. Phase 29 is closed. `29-DESIGN-SPEC.md` exists, `MANIFEST.md` has three rows, the phase-close gate went green, an F-NN row says ACCEPTED. **And the phase failed.** Below is why, in descending order of how badly it failed, each with an exact amendment or a reasoned acceptance.

Verdict up front: **as written, both plans can execute to completion, produce every listed artifact, pass every `<automated>` verify block, and satisfy none of MAPUX-02, MAPUX-03 or MAPUX-05 in substance.** Seven of the findings below are the exact defect class the directive's operating lessons 9, 14 and 15 name. Two are hard execution blockers that will fire in the first ten minutes of Wave 1.

---

## Severity index

| # | Failure | Class | Disposition |
|---|---|---|---|
| F1 | Rubric criterion 5 (Leaflet z-index) **cannot run at all** in a Leaflet-less sketch — it silently vanishes from the JSON | cannot-fail | AMEND (blocking) |
| F2 | `save_screenshot` cannot write to the declared PNG paths — they contain spaces | execution blocker | AMEND (blocking) |
| F3 | The 375px iframe scoring is unreachable over `file://` — opaque origins block `contentDocument` | execution blocker | AMEND (blocking) |
| F4 | Nothing detects iteration theater; iter-1 can score 5/5 by construction, leaving iter-2 no falsifiable target | theater | AMEND (blocking) |
| F5 | MAPUX-05 acceptance is pure self-review; F-39's own mandated Opus `gsd-ui-checker` pass **is in no plan** | circularity | AMEND (blocking) |
| F6 | Criteria 1, 2 and 5 are true-by-construction; only 3 and (partly) 4 are falsifiable | operating-lesson 9 | AMEND |
| F7 | The prototype has no contact with the real stacking context — `.zoom-ctl`, `.result-panel`, `.toast`, `.mode-toggle`'s ≤480 reset | prototype invalidity | AMEND |
| F8 | Design spec under-specifies: no breakpoints, no ARIA, no focus order, no z-index assignments, no i18n strings, no data-* hooks | Phase 30 re-designs | AMEND |
| F9 | BrowserOS mid-iteration drop = lost iteration; no resume protocol, no write-as-you-go | flakiness | AMEND |
| F10 | Fable-decision numbering is stale by three (plan says F-39; F-39/40/41 already exist) | correctness | AMEND (one-line) |
| F11 | Phase-close gate laundering `astro check`, and `cd site`/`cd ..` leaves cwd poisoned on failure | operating-lesson 8/16 | AMEND |
| F12 | Nothing enforces the no-map-code hard gate; the plan only asserts it in prose | scope leak | AMEND (one-line) |
| F13 | "Controls avoid occluding the map" has a measurement but no threshold | not falsifiable | AMEND |
| F14 | Full-bleed map (competitor finding 2) conflicts with MAPSH-05's confinement | scope collision | AMEND (spec must decide) |
| F15 | Tab-walk method contradicts F-41's adopted by-construction standard and is the flakiest step in the phase | cost/flakiness | AMEND |
| F16 | Iteration 1 has no "before" screenshot of itself | roadmap wording | ACCEPT (reasoned) |
| F17 | `grep -c "showModal"` / `grep -c "newsToggleDiscoverable"` cannot distinguish real output from a typed word | weak gate | AMEND |

---

## F1 — The rubric's most important criterion cannot fire. (BLOCKING)

`29-RESEARCH.md:283-299` guards all of criterion 5 behind:

```js
const mapPane = document.querySelector('.leaflet-map-pane, .leaflet-container');
if (mapPane) { … results.zIndexViolations = … }
```

The sketches contain **no Leaflet**. `mapPane` is `null`. `results.mapVisibleWidthPx`, `results.controlZIndexes` and `results.zIndexViolations` are therefore **absent from every JSON blob this phase will ever produce** — not `false`, not `[]`, absent. `SCORE.md` will be pasted verbatim (as required), `MANIFEST.md`'s `zIndexViolations` column will read blank or `—` for every row, and nobody will notice because the baseline row is already legitimately marked "not measured at baseline" (`29-01-PLAN.md:103`), which normalizes the empty cell.

Meanwhile `29-01-PLAN.md:22` asserts as a must-have truth: *"Iteration 1's news-layer toggle is **provably** … outside the Leaflet pane z-index conflict band."* Nothing in the plan proves it. This is operating lesson 14 exactly: pick the phase's headline invariant, ask what goes red if it breaks — answer: nothing.

Second defect in the same criterion: `Number(getComputedStyle(el).zIndex) || 0` maps `auto` → `0`, and the filter is `c.zIndex > 0 && c.zIndex < 700`. **A control with no `z-index` at all is scored as compliant.** In a hand-written sketch, that is most of them.

**Amendment A1** — replace `29-RESEARCH.md`'s criterion-5 block, and the copy extracted into `score.mjs` (Plan 29-01 Task 1), with:

```js
  // 5. No map occlusion / Leaflet pane conflict.
  const mapPane = document.querySelector('.leaflet-map-pane, .leaflet-container');
  const controls = [...document.querySelectorAll(
    '.map-topbar, .legend, .mode-toggle, [data-role="filter-entry"], [data-role="news-toggle"]'
  )];
  results.controlZIndexes = controls.map(el => {
    const raw = getComputedStyle(el).zIndex;           // may be the string "auto"
    return { cls: el.className, zIndexRaw: raw, zIndex: raw === 'auto' ? null : Number(raw) };
  });
  // An always-visible non-modal control with z-index:auto is a VIOLATION: its paint
  // order is DOM-order-dependent and will not survive contact with map.css.
  results.zIndexViolations = results.controlZIndexes.filter(
    c => c.zIndex === null || (c.zIndex > 0 && c.zIndex < 700)
  );
  if (!mapPane) {
    // Criterion 5 is UNMEASURABLE without a Leaflet stand-in. Fail closed, loudly.
    results.criterion5 = 'NOT_MEASURED_FAIL';
    results.mapVisibleWidthPx = null;
  } else {
    results.criterion5 = results.zIndexViolations.length === 0 ? 'PASS' : 'FAIL';
    results.mapVisibleWidthPx = mapPane.getBoundingClientRect().width;
    results.viewportWidthPx = window.innerWidth;
    results.mapWidthRatio = results.mapVisibleWidthPx / window.innerWidth;
  }
```

**Amendment A2** — `29-01-PLAN.md` Task 2 `<action>`, append:

> Both sketches MUST include a Leaflet **stacking stand-in**: a `div.leaflet-container` sized to the sketch's map area, containing the real pane divs with the real z-index values copied verbatim from `site/node_modules/leaflet/dist/leaflet.css` — `.leaflet-tile-pane` 200, `.leaflet-overlay-pane` 400, `.leaflet-shadow-pane` 500, `.leaflet-marker-pane` 600, `.leaflet-tooltip-pane` 650, `.leaflet-popup-pane` 700, `.leaflet-control` 800, `.leaflet-top/.leaflet-bottom` 1000 — plus one absolutely-positioned dummy element inside `.leaflet-popup-pane` positioned to overlap the news toggle's coordinates. Criterion 1's `elementFromPoint` topmost check then becomes a real test of the toggle's stacking, not a formality. A sketch whose `SCORE.md` reports `criterion5: "NOT_MEASURED_FAIL"` is **not a scored iteration** and may not be entered in `MANIFEST.md`.

**Amendment A3** — `29-01-PLAN.md:22` truth, replace with:

> "Iteration 1's news-layer toggle is proven topmost at its own centre point (`elementFromPoint`) against a Leaflet pane stand-in carrying the real leaflet.css z-index values, and carries an explicit numeric `z-index` ≥ 800 (never `auto`)."

---

## F2 — The screenshots cannot be written where the plan says. (BLOCKING)

Both plans list PNG paths under `.planning/sketches/029-map-controls/iter-N/` (`29-01-PLAN.md:12-13`, `29-02-PLAN.md:10-11`). The repo root is `C:\Users\Carlo\OneDrive - pjud.cl\Documentos\GitHub\Is Chile Safe\` — **two spaces in the absolute path**. `save_screenshot` requires a no-spaces path; this is a recorded memory (`browseros-review-gotchas`), it is restated in `ROADMAP.md:365`, and `29-BASELINE.md:5` records that the baseline session already worked around it by writing to `C:\Users\Carlo\bos-shots\p29\`. The plans then forgot it. Wave 1 Task 2 stalls on the first screenshot call.

**Amendment A4** — insert into `29-01-PLAN.md` Task 2 and `29-02-PLAN.md` Task 1, immediately before the screenshot instruction:

> `save_screenshot` cannot write into the repo (the absolute path contains spaces — the same constraint that forced `29-BASELINE.md`'s shots to `C:\Users\Carlo\bos-shots\p29\`). Screenshot to `C:\Users\Carlo\bos-shots\p29\iter-N-desktop.png` / `iter-N-mobile375.png`, then copy into the repo with Bash: `cp /c/Users/Carlo/bos-shots/p29/iter-N-desktop.png ".planning/sketches/029-map-controls/iter-N/desktop.png"`. The `test -f` verifies below check the **repo** copy, so a forgotten `cp` fails the gate rather than passing silently.

---

## F3 — The 375px mobile score is unreachable over `file://`. (BLOCKING)

The mandated mobile method is a 375px iframe (`ROADMAP.md:365`). Scoring requires `evaluate_script` to reach *inside* that iframe. `29-BASELINE.md:32-34` did this successfully — over `http://127.0.0.1:4321`, where parent and child are same-origin. Both Phase 29 plans instead open the sketches over `file://` (`29-01-PLAN.md:119`, `29-02-PLAN.md:97`). Chrome treats `file://` documents as **opaque origins**; `iframe.contentDocument` returns `null` and `contentWindow.document` throws `SecurityError`. Every mobile JSON blob in this phase is empty, or the step is quietly "adapted" mid-execution into scoring the mobile sketch at desktop width — which is the same undetectable degradation as F1.

Note this also silently voids criterion 3, which is the *only* criterion whose threshold is defined at 375px (WCAG 2.5.5 touch targets).

**Amendment A5** — replace the "Open … via `file://`" sentence in `29-01-PLAN.md:119` and `29-02-PLAN.md:97` with:

> Serve the sketch directory over HTTP so that the 375px iframe is same-origin and `evaluate_script` can reach into it (a `file://` parent is an opaque origin — `iframe.contentDocument` is `null` and every mobile measurement would come back empty). From the repo root, in the background: `python -m http.server 4399 --directory .planning/sketches/029-map-controls`. Open `http://127.0.0.1:4399/iter-N/desktop.html` for desktop, and for mobile open a wrapper page on the **same** origin containing `<iframe src="/iter-N/mobile-375.html" width="375" height="720">`. Before scoring, assert same-origin access succeeded: `evaluate_script` returning `document.querySelector('iframe').contentDocument !== null` must be `true`; if it is `false` or throws, the mobile score is **NOT_MEASURED_FAIL**, never omitted. Port 4399 is chosen to avoid 4321 (astro preview). This server is unrelated to the F-40 `BaseLayout` redirect hazard — the sketches contain no `hreflang` link — but do not reuse the astro preview server, whose EN pages will bounce an es-locale browser to production.

Also add a Task-1 wrapper artifact: `.planning/sketches/029-map-controls/mobile-frame.html` (the 375px iframe wrapper, `?src=` parameterized or one per iteration), so the mobile harness is a committed artifact rather than an ad-hoc DOM injection that dies with the session (see F9).

---

## F4 — Nothing in the plan can detect iteration theater. (BLOCKING)

Angle 1 of the brief, and the answer is bluntly: **nothing**. Trace it:

- Iteration 1 is authored by the orchestrator *to satisfy the rubric* (`29-01-PLAN.md:117` literally instructs "always-visible news toggle … `z-index: 801` … never inside the scrollable chip row" — i.e. the criteria are the build instructions).
- Therefore iter-1 scores 5/5.
- `29-02-PLAN.md:93` then says "any rubric criterion iteration 1 failed … is a mandatory target for iteration 2." There will be none.
- Iteration 2 is left with one non-falsifiable instruction: restructure into grouped entry points and cite CrimeMapping finding 1.
- Its score is 5/5, identical to iter-1. `MANIFEST.md` shows two identical rows. The only evidence that a second *design* happened is prose in `SCORE.md` — and the only gate is `grep -ci "crimemapping"` (`29-02-PLAN.md:102`), which passes on the word appearing anywhere.

A cosmetic recolour of iter-1 with "CrimeMapping" typed into the delta note passes every gate in this phase. MAPUX-02 says the loop *is* the deliverable; the loop as planned cannot be distinguished from a single pass plus a copy.

The fix is not "try harder" — it is to **pre-register, before iteration 1 is built, a set of adversarial stress conditions the rubric is re-run under**, so that (a) iteration 1 has a real chance of failing something, and (b) iteration 2 has a falsifiable target that is not the orchestrator's own opinion.

**Amendment A6** — new task in `29-01-PLAN.md`, inserted as Task 1b (before any sketch is built, so the conditions cannot be reverse-engineered from the design — the F-02 "freeze before you measure" precedent):

> **Task 1b: Pre-register the stress conditions (do this BEFORE building iteration 1).**
> Files: `.planning/sketches/029-map-controls/STRESS.md`.
> Write, and do not amend afterwards, the five conditions under which every iteration's rubric is re-run. These are frozen at this point in the phase exactly as F-02 froze the rapidfuzz threshold: tuning them after seeing a score is the circularity this phase's acceptance gate exists to prevent.
> 1. **Content growth**: a 9th crime-family chip and a 2nd year-select are injected via `evaluate_script` before scoring (`29-RESEARCH.md` Pitfall 3's own stated warning sign, which the rubric never implemented).
> 2. **Longest real label**: every filter label is replaced by the longest string it can actually carry in ES — `Robos con violencia o intimidación` — and in EN. Both locales ship; a shell that only fits EN is broken.
> 3. **Narrow viewport**: 320px iframe in addition to 375px (iPhone SE / Galaxy Fold cover screen; 375 is not the floor).
> 4. **Enlarged text**: `document.documentElement.style.fontSize = '24px'` (WCAG 1.4.4, 150%) before scoring at 375px.
> 5. **Real breakpoint boundaries**: also score at **481px and 639px** — the two bands `map.css:192`, `map.css:210`, `map.css:240` and `map.css:271` actually switch on, and the band Phase 25's P0 tablet-overflow defect lived in. A design validated only at "desktop" and 375px has never been tested at either boundary it will meet in production.
>
> `MANIFEST.md`'s iteration table gains a column per condition. **A row with no `FAIL` anywhere in it and no prior row to improve on is evidence the harness is too weak, not that the design is perfect** — if iteration 1 passes all five conditions on the first try, record that fact explicitly in `iter-1/SCORE.md` and add a sixth, harder condition before iteration 2, rather than declaring the loop converged.

**Amendment A7** — `29-02-PLAN.md` Task 1 `<verify>`, replace the whole `<automated>` block with:

```
test -f ".planning/sketches/029-map-controls/iter-2/SCORE.md" && test -f ".planning/sketches/029-map-controls/iter-2/desktop.png" && test -f ".planning/sketches/029-map-controls/iter-2/mobile-375.png" && node .planning/sketches/029-map-controls/check-iteration.mjs 2
```

with a new committed `check-iteration.mjs` (written in Task 1 of Plan 29-01, per F-36 — real `.mjs` file, no regex inside a quoted `node -e`) that exits non-zero unless **all** hold for iteration N:

1. Every JSON blob in `iter-N/SCORE.md` `JSON.parse`s, and each carries `newsToggleDiscoverable`, `filterOverflowsContainer`, `touchTargetViolations`, `criterion5`, `capturedAt` (ISO), `pageUrl`, `viewportWidthPx`.
2. No blob has `criterion5 === 'NOT_MEASURED_FAIL'` and none is missing a stress condition from `STRESS.md`.
3. For N ≥ 2: the count of **top-level labelled control entry points** in `iter-N/desktop.html` (elements carrying `data-role="entry-point"`) differs from `iter-(N-1)/desktop.html`, **or** at least one criterion×condition cell moved from FAIL to PASS. Structural identity plus identical scores = theater, and exits 1 with the message `ITERATION N IS NOT A DISTINCT ITERATION`.
4. `iter-N/SCORE.md` contains at least one literal numeric value that also appears in `iter-(N-1)/SCORE.md`'s JSON (proving the delta note compared, not paraphrased).

Prove the check is falsifiable before approving: copy `iter-1/` to a scratch `iter-2/`, run `check-iteration.mjs 2`, confirm exit 1 (operating lesson 9 — construct the counterexample).

---

## F5 — MAPUX-05 is self-review, and F-39's own remedy is missing from the plans. (BLOCKING)

`29-02-PLAN.md:125` states it plainly: *"Executed inline by the orchestrator — this IS the acceptance act."* The same agent writes the rubric, builds both iterations, runs the scoring, writes the design spec, and accepts it. That is the precise circularity F-06 (blind second pass mandatory), F-11 (split the dispatch so the reviewer is not the author) and F-23 (never let the producing model review itself, escalate instead of downgrade) exist to prevent. The gate amendment at directive line 66 replaces *human* acceptance with Fable acceptance; it does not license *unreviewed* acceptance.

Worse: **F-39 already binds this phase to an independent check, and neither plan contains it.** F-39 reads: "the phase's own `29-DESIGN-SPEC.md` IS the design contract, and it is checked by an Opus `gsd-ui-checker` pass at the end instead of by a researcher-written UI-SPEC at the start." No task in `29-01-PLAN.md` or `29-02-PLAN.md` spawns `gsd-ui-checker`. A binding Fable decision is silently dropped by the plans written after it. If the phase closes this way, the acceptance record is false on its face.

The independent check is cheap and available: an Opus subagent is a subagent-tool call, and everything it needs is on disk (screenshots, JSON, spec, baseline). It does not need BrowserOS.

**Amendment A8** — insert into `29-02-PLAN.md` as **Task 2b**, between "Write the accepted design spec" and "Record the acceptance gate" — acceptance must not precede the review:

> **Task 2b: Independent Opus review of the design spec and the evidence pack (blind to the orchestrator's rationale).**
> Files: `.planning/phases/29-map-ux-design-loop/29-UI-CHECK.md`.
> Executed inline by the orchestrator **spawning** an Opus `gsd-ui-checker` (per F-39; `model="opus"` per F-18 routing). This step discharges F-39 and breaks the F-06/F-11/F-23 circularity: the acceptor is not the author.
> The agent is given ONLY: `29-BASELINE.md`, `STRESS.md`, `MANIFEST.md`, `iter-1/SCORE.md`, `iter-2/SCORE.md`, the four PNGs, `29-DESIGN-SPEC.md`, and the MAPUX-01..05 + MAPSH-01..07 requirement text. It is **not** given `29-01-SUMMARY.md`, the plans, or any orchestrator commentary — it must reconstruct the argument from the evidence, exactly as the returning human will.
> It must answer, in `29-UI-CHECK.md`, with a BLOCK/FLAG/PASS verdict per question:
> 1. Is iteration 2 a genuinely distinct design from iteration 1, judged from the two HTML files and the two screenshots — or a restyle? Name the structural difference or state that there is none.
> 2. Which rubric criteria are falsifiable against these sketches and which are true by construction? Name each explicitly.
> 3. Does `29-DESIGN-SPEC.md` contain everything Phase 30 needs to implement without re-designing (§F8's checklist), against the real `site/src/components/map/map.css` and `MapTopbar.tsx`? Name every missing decision.
> 4. Is there any decision in the spec that the evidence does not support?
> A **BLOCK** verdict on question 1 or 3 must be resolved (another iteration, or spec amendments) before Task 3 records acceptance. Max 2 cycles, then Fable decides inline and records the unresolved BLOCK verbatim in the F-NN row and in STATE.md `## Blockers` — never silently.
> If Opus is unavailable (`529`), apply F-23: do **not** downgrade to Sonnet; run the pass inline as Fable against the blind evidence set only, record that fact in the F-NN row, and add "independent Opus re-review of 29-UI-CHECK.md" to the deferred-live list.

**Amendment A9** — `29-02-PLAN.md` Task 3, add to the `<action>`: the F-NN row must cite `29-UI-CHECK.md`'s verdict and state that acceptance is *Fable-proxy on independently-reviewed evidence*, not Fable-only. Add to `<verify>`: `test -f ".planning/phases/29-map-ux-design-loop/29-UI-CHECK.md"`.

---

## F6 — Which criteria are actually falsifiable. Bluntly.

| MAPUX-03 criterion | Rubric implementation | Verdict |
|---|---|---|
| 1. Find/activate the news layer | `querySelector('[data-role="news-toggle"], .ev-chip')` + in-viewport + `elementFromPoint` | **Decoration as written.** The author writes the `data-role` attribute and positions the element; both halves are true by construction. `elementFromPoint` becomes real only once something can overlap it (A2's popup-pane stand-in) and only under the stress conditions (A6). |
| 2. Find the filters | `filterEntry.closest(…).scrollWidth > clientWidth` | **Decoration as written.** With a FAB, `scrollParent` falls back to the FAB element itself; a button's `scrollWidth === clientWidth` always, so `filterOverflowsContainer: false` is guaranteed regardless of whether any filter is reachable. Also `document.querySelector` takes the *first* of three selectors in DOM order, so which element is measured is accidental. |
| 3. Touch targets ≥44px at 375px | measures every button/chip/link rect | **Genuinely falsifiable.** The only criterion that can fail on a design the author believed was fine — and the baseline already passes it (`29-BASELINE.md:42,50`), so it will produce no delta. Keep it as a regression guard, do not count it as loop evidence. |
| 4. No keyboard/focus trap | candidate set only; the actual walk is a manual BrowserOS procedure | **Falsifiable in principle, unexecutable in practice** at 375px (F3) and contradicted by F-41's adopted standard (F15). |
| 5. Map occlusion / Leaflet panes | guarded by a `.leaflet-container` that does not exist in the sketch | **Cannot fire at all** (F1). |

So of five criteria, **one is falsifiable and produces no signal, one is fixable, and three are decoration**. The phase's own rubric is, today, a 1-of-5 instrument being reported as 5-of-5.

**Amendment A10** — replace criterion 2's body in `29-RESEARCH.md` and `score.mjs`:

```js
  // 2. Can they find the filters? Three independent falsifiable sub-checks.
  const entries = [...document.querySelectorAll('[data-role="entry-point"]')];
  results.entryPointCount = entries.length;
  results.entryPointLabels = entries.map(el => (el.getAttribute('aria-label') || el.textContent || '').trim());
  // 2a. every declared entry point is fully inside the viewport, unscrolled
  results.entryPointsOffscreen = entries.filter(el => {
    const r = el.getBoundingClientRect();
    return r.left < 0 || r.right > window.innerWidth || r.top < 0 || r.bottom > window.innerHeight;
  }).map(el => el.getAttribute('data-role-name') || el.className);
  // 2b. NO ancestor of any entry point silently clips it
  results.clippedEntryPoints = entries.filter(el => {
    let p = el.parentElement;
    while (p && p !== document.body) {
      const s = getComputedStyle(p);
      if ((s.overflowX === 'auto' || s.overflowX === 'hidden' || s.overflowX === 'scroll')
          && p.scrollWidth > p.clientWidth) return true;
      p = p.parentElement;
    }
    return false;
  }).length;
  // 2c. the page itself must not scroll horizontally at ANY tested width
  results.documentOverflowPx =
    document.documentElement.scrollWidth - document.documentElement.clientWidth;
  results.criterion2 = (results.entryPointsOffscreen.length === 0
    && results.clippedEntryPoints === 0
    && results.documentOverflowPx <= 0) ? 'PASS' : 'FAIL';
```

Every sub-check can fail on a design the author believed was correct, especially under A6's stress conditions. `entryPointCount`/`entryPointLabels` also give A7's structural-difference check something to compare.

**Amendment A11** — `29-RESEARCH.md`'s "Sampling procedure per iteration" and both plans: the rubric must be run **once per stress condition per viewport**, and `MANIFEST.md`'s row is a matrix cell set, not five booleans. A row is PASS only if every cell is PASS.

---

## F7 — The prototype proves nothing about the real app, and the plan's own interface notes are wrong about it.

`29-01-PLAN.md:78-88` reproduces five facts from `map.css`. It omits every fact that would actually break the design:

| Real code | Why it invalidates the sketch |
|---|---|
| `.mode-toggle { position: static }` at `max-width: 480px` (`map.css:240-251`) | The plan cites `.mode-toggle`'s `position:absolute; z-index:801` (`map.css:104-111`) as the **precedent for the always-visible news toggle** (`29-01-PLAN.md:80`, `:117`). That precedent **does not hold at mobile** — the real component drops out of the stacking context below 480px, and 375px is below 480px. A sketch that pins a fixed z-index-801 toggle at 375px is designing something the existing CSS actively contradicts. |
| `.zoom-ctl { position:absolute; right:16px; bottom:120px; z-index:700 }`, shown at ≥640px (`map.css:257-275`) | `29-RESEARCH.md` Open Question 2 recommends a **bottom-right FAB** and tells the sketch to "verify no collision with `.legend`" at bottom-**left**. It checks the wrong corner. The bottom-right corner is already occupied on desktop. |
| `.result-panel { position:fixed; right:0; width:380px; z-index:700 }` desktop, `left:0;right:0;height:40vh` bottom sheet at ≤640px (`map.css:450-480`) | On desktop the right 380px is a panel, not free canvas; at mobile the bottom 40vh is a sheet. A bottom-right FAB collides with both. Neither exists in the sketch, so this is invisible until Phase 30. |
| `.search-dropdown` z 900 (`map.css:364-369`), `.map-error-overlay` z 900 (`map.css:407-410`), `.toast` z 1000 (`map.css:803-808`), `.partial-year-badge` z 800 top-centre (`map.css:900-905`) | The real z-index ladder has five occupied tiers, not the two the plan lists. A new control at 800 ties with the topbar and the partial-year badge — resolved by DOM order, which the sketch does not model. |
| `.legend-mobile` `<details>` at ≤480 (`map.css:210-224`), already below the fold per `29-BASELINE.md:44` | A second `<details>`/`<dialog>` filter surface at 375px interacts with an existing one. Untested. |
| React island (`MapIsland.tsx`, 541 lines) with `client:only="react"` | Nothing about hydration order, the fact that the shell renders **nothing** server-side, or how a `<dialog>` inside a `client:only` island behaves on first paint is modelled. |

**Amendment A12** — replace `29-01-PLAN.md`'s `<interfaces>` block (lines 74-91) so it carries the **complete real inventory**, and add to Task 2's `<action>`:

> The sketch must reproduce, as inert positioned stand-ins with their real classes and z-index values, every element that competes for map-edge space in the real app: `.zoom-ctl` (bottom-right, `bottom:120px`, desktop-only ≥640 — `map.css:257-275`), `.result-panel` (fixed right 380px desktop / bottom 40vh ≤640 — `map.css:450-480`), `.legend` (bottom-left, `.legend-mobile` `<details>` ≤480 — `map.css:127-131`, `210-224`), `.partial-year-badge` (z 800, top-centre — `map.css:900-905`), `.search-dropdown` (z 900 — `map.css:364`), `.toast` (z 1000 — `map.css:803`), and `.mode-toggle` **including its `position:static` reset at ≤480** (`map.css:240-251`). A FAB or toggle placement that collides with any of these is a FAIL, and the rubric's `elementFromPoint` check must be run at each control's centre with all stand-ins present. If iteration 1's bottom-right FAB collides with `.zoom-ctl`, say so in `SCORE.md` and move it — that is exactly the kind of real failure this loop is supposed to surface, and `29-RESEARCH.md` Open Question 2 checked the wrong corner.

---

## F8 — What the design spec must pin, or Phase 30 re-designs it.

`29-02-PLAN.md:113` asks for six sections. None of them pins an implementable value. Phase 30 is a declared regression-risk phase against protected layer files; it must not be making UX decisions. The spec must contain, as a table Phase 30 implements literally:

1. **Exact z-index assignment for every new/changed control**, placed in the real ladder (700 legend/result-panel/zoom-ctl, 800 topbar/partial-year-badge, 801 mode-toggle, 900 search-dropdown/error-overlay, 1000 toast, Leaflet 400–1000) — with the rule that a modal `<dialog>` uses top-layer and needs **no** z-index, and non-modal controls need an explicit number, never `auto`.
2. **Breakpoints**, stated as the real ones: 480 and 640 (`map.css:192,210,240,271,463`), **not** "desktop and 375". What the shell looks like in each of the four bands (<480, 480–639, 640–1023, ≥1024) and what the `.mode-toggle` `position:static` reset becomes.
3. **Exact element semantics per control**: `<button aria-pressed>` vs `<input type="checkbox">` vs `<details>/<summary>` vs `<dialog>` — this determines React state shape and MAPSH-02 compliance, and cannot be inferred from a screenshot.
4. **Focus order**, as an explicit DOM-order list, and what happens on `<dialog>` close (focus returns to the invoking control).
5. **ARIA**: `aria-label`/`aria-pressed` on the news toggle; `aria-expanded` + `aria-controls` on each entry point; `aria-labelledby` on the dialog; whether a live region announces filter results (CrimeMapping findings 3 and 4 argue yes — `29-BASELINE.md:64-65` — and `/news/` already has the precedent, F-41 item 4).
6. **The exact label strings in EN and ES**, with their i18n keys, plus the longest-string layout consequence from A6 condition 2.
7. **The `data-role` hooks** (`data-role="news-toggle"`, `data-role="entry-point"`, `data-role="filter-entry"`) that Phase 30 must ship into the real DOM — **so this same `score.mjs` runs unchanged against the real `/map/` as Phase 30's MAPSH-06 regression gate.** Without this, the rubric dies with the sketch and Phase 30 has no acceptance instrument.
8. **Explicit non-decisions**: MAPSH-04 `?region=` (out of scope, `29-RESEARCH.md` OQ3) **and** the Phase 28 N1 trap — Phase 30 must not reuse `parseFilterParams`, because `/news/`'s `?region=` is CSV multi-value while the map's is single-value focus.
9. **The pass/fail matrix the accepted design achieved**, so Phase 30 knows the bar it must reproduce in real code, not just the shape it must build.

**Amendment A13** — replace `29-02-PLAN.md:113`'s item list with sections (1)–(9) above, and replace Task 2's `<automated>` verify with a `check-spec.mjs` asserting the presence of each of the nine sections by heading and that the z-index table has a numeric value per control (not prose). Prove it fails on a spec with the z-index column blank.

---

## F9 — A BrowserOS drop mid-iteration loses the iteration.

The MCP connection has already dropped once this run and screenshots have timed out intermittently. Directive line 59 handles only "unreachable **when 29 starts**". Neither plan says what happens at minute 40. As written, all measurement lives in the orchestrator's context until `SCORE.md` is written at the end of the task — a drop before that point loses every JSON blob, and the 375px iframe wrapper (injected ad hoc) dies with the tab.

The good news: the sketches are deterministic static files, so *reconstruction is cheap* — provided the harness is on disk and the results are flushed as they are produced.

**Amendment A14** — add to both plans, after the `<objective>`:

> **BrowserOS resume protocol (applies to every browser step in this phase).**
> 1. The harness is committed, not improvised: `score.mjs`, `mobile-frame.html`, and the `python -m http.server 4399` command are on disk before any measurement. Any measurement is re-runnable from a cold session by re-reading them.
> 2. **Flush as you go.** Every `evaluate_script` result is appended to `iter-N/SCORE.md` **immediately**, with its `capturedAt`, `pageUrl` and stress-condition name, before the next call is made. Never buffer a set of blobs to write at the end of a task.
> 3. On any MCP error or timeout: retry once; then re-check `http://127.0.0.1:9200/mcp`; then restart the browser tab and re-run **only** the missing cells (they are named in `SCORE.md` by their absence).
> 4. If BrowserOS is unrecoverable, the iteration closes as **PARTIAL**: `MANIFEST.md`'s cells for the missing measurements read `NOT_MEASURED_FAIL`, and `check-iteration.mjs` exits non-zero. A PARTIAL iteration does not count toward MAPUX-02's ≥2, and Phase 29 is marked BLOCKED per directive line 59 with 30 skipped — it is never closed on a partial evidence pack.
> 5. Screenshots go to `C:\Users\Carlo\bos-shots\p29\` first (F2); a dropped connection after the shot but before the `cp` costs one file copy, not one iteration.

---

## F10 — The Fable-decision number is wrong. (one line)

`29-02-PLAN.md:127` instructs: *"Append a new row `F-39` (next available number after F-38…)"*. **F-39, F-40 and F-41 already exist** in `STATE.md` — all three were written for Phase 29 itself (spec-gate routing, the `BaseLayout` cross-origin redirect, and the Phase 28 N3 closure). A literal execution creates a duplicate F-39 and overwrites the record of the phase's own setup decisions.

**Amendment A15** — replace with: *"Append a new row **`F-42`** (F-39/F-40/F-41 already exist for this phase; re-confirm the current max in `STATE.md` § Fable Decisions before writing, since rows are not stored in monotonic order)."*

---

## F11 — The phase-close gate launders `astro check` and poisons the shell cwd.

`29-02-PLAN.md:132`:

```
cd site && npx astro check; npm run build && npm test && npm run validate && cd .. && python -m pytest -q
```

Two defects, both in the class that appeared seven times across Phases 27–28 (operating lessons 8 and 16):

1. `npx astro check;` — the `;` discards astro-check's status entirely. This is *intended* (4 pre-existing errors, F-34/F-08) but the result is that astro check is **not a gate at all**: 4 errors and 400 errors are indistinguishable. The plan's `<done>` claims "4 expected astro-check errors" as if it were verified. It is not.
2. `cd site … && cd ..` — the Bash tool's cwd persists between calls. If `npm test` fails, `cd ..` never runs and the shell is left inside `site/`, so the next command's relative paths silently resolve wrong. Use a subshell.

**Amendment A16** — replace the `<automated>` block with:

```
(cd site && npx astro check > ../.planning/tmp-astro-check.txt 2>&1; node ../.planning/sketches/029-map-controls/check-astro.mjs ../.planning/tmp-astro-check.txt && npm run build && npm test && npm run validate) && python -m pytest -q
```

where `check-astro.mjs` reads the file, finds the summary line, and exits 0 **only if the error count is exactly 4** (string comparison, not regex — F-36), exits 1 with the delta otherwise. Run it once against the real tree at approval time (operating lesson 16) and confirm it exits 0; then mutate the expected count to 3 and confirm it exits 1 (operating lesson 9).

---

## F12 — Nothing enforces "no map code". (one line)

`ROADMAP.md:98` and `:364` make this the phase's hard gate. Both plans state it in prose (`29-01-PLAN.md:51`, `29-02-PLAN.md:48`) and neither checks it. The most likely drift points are precisely the two places the plan sends the executor into the real code: `29-01-PLAN.md:66-71` `@`-includes `map.css`, `MapTopbar.tsx`, `FiltersRow.tsx`, `Legend.tsx` into context, and A12 above deepens that. From "read `map.css` to copy the values" to "just try the fix in `FiltersRow.tsx` to see if it works" is one keystroke, and the phase-close gate runs a full `npm run build` that would happily build the modified tree green.

**Amendment A17** — add as the first line of both plans' `<verify>` sections:

```
test -z "$(git status --porcelain -- site/)"
```

and to the prose: *"If this fails, the phase has violated its own hard gate. Revert `site/` (`git checkout -- site/`), record the attempted change in `STATE.md` § Blockers, and re-run — do not carry it into Phase 30 as a fait accompli."*

---

## F13 — "Controls avoid occluding the map" has no threshold.

MAPUX-03's fifth clause is two things: pane conflict (F1) *and* occlusion. The rubric records `mapVisibleWidthPx` with the comment "compare against viewport width per iteration" — i.e. it defers the comparison to a human, forever. `29-BASELINE.md:30` gives the real number (812/1296 = 63%) and calls it a finding, but no iteration can pass or fail on it.

**Amendment A18** — add to `score.mjs` (already partly in A1) and to `STRESS.md`: `results.mapWidthRatio` and `results.controlCoveragePct` (union area of all `[data-role]` control bounding boxes intersecting the map rect, as a percentage of the map rect). Thresholds, pre-registered before iteration 1: `mapWidthRatio ≥ 0.90` at desktop and `≥ 0.98` at 375px; `controlCoveragePct ≤ 25%` at 375px with all panels closed. If iteration 1 or 2 cannot meet these, that is a legitimate FAIL to record and design against — which is what a loop is for.

---

## F14 — Full-bleed vs MAPSH-05: the spec must decide, not hint.

CrimeMapping finding 2 (`29-BASELINE.md:63`) is "the map is full-bleed"; `29-BASELINE.md:30` flags our 812/1296 boxed map as a secondary desktop finding; A18 above turns it into a threshold. But achieving it means changing `.map-stage`/`.map-canvas` layout in `map.css` — while MAPSH-05 confines Phase 30's changes to "`MapTopbar.tsx` and sibling control components". These are in direct tension, and the tension is invisible in both plans.

**Amendment A19** — `29-DESIGN-SPEC.md` must resolve it explicitly, one of two ways, and say which: **(a)** the map-width ratio is declared **out of scope** for Phase 30 (spec records the finding, thresholds apply to control coverage only, boxed map survives); or **(b)** it is in scope and the spec **names the exact `map.css` selectors and properties** Phase 30 is authorized to change, so the Opus code review's MAPSH-05 check reads "confined to `MapTopbar.tsx`, siblings, **and these named `map.css` rules**" rather than flagging a legitimate change as a violation. Recommendation: **(a)** — the phase's stated failure is discoverability, not framing, and (b) widens a declared regression-risk phase for a secondary finding.

---

## F15 — The Tab-walk is the flakiest step in the phase and contradicts the standard this run just adopted.

`29-01-PLAN.md:133` mandates `focusables.length + 2` real Tab keypresses on both pages. At the sketch's likely size that is 15–30 individual MCP round-trips per page per iteration per stress condition — the single largest source of drop exposure (F9) in the phase, for the criterion that is *least* likely to fail in native markup. And in the 375px iframe it does not work at all: focus enters the iframe and `document.activeElement` in the parent stays pinned to the `<iframe>` element.

Meanwhile **F-41 already adopted the opposite method as "the standard for this run"**: settle the keyboard-trap criterion *by construction* — count focusables, count negative tabindexes, and grep for `keydown`/`keyup`/`preventDefault` handlers; if no script intercepts key events, native tab order applies and a trap is impossible. `29-BASELINE.md:80` calls this "stronger evidence than sampling a few Tab presses," and it is right.

**Amendment A20** — replace `29-01-PLAN.md:133` and `29-02-PLAN.md:99`'s Tab-walk instruction with:

> Criterion 4 is settled **by construction, per F-41's adopted standard**: via `evaluate_script`, record (a) the focusable count, (b) the count of elements with `tabindex="-1"`, (c) the result of scanning the sketch's own inline `<script>` text for `keydown`, `keyup` and `preventDefault`. Zero interceptors + zero negative tabindexes = PASS, and the result is a single call instead of thirty. **Then** perform exactly one real interaction, on the desktop page only (where focus is not inside an iframe): click the filter entry point to fire `showModal()`, `evaluate_script` that `document.querySelector('dialog').matches(':modal')` is `true` (this is the check that actually distinguishes `showModal()` from a declarative `<dialog open>` — `29-RESEARCH.md` Pitfall 2, which `grep -c "showModal"` cannot detect), press `Escape`, and assert focus returned to the invoking element. Record all of it in `SCORE.md`.

---

## F16 — Iteration 1 has no "before" screenshot of itself. ACCEPTED.

`ROADMAP.md:371` defines an iteration as "screenshot → Fable-agent redesign → apply → re-screenshot". Read strictly, iteration 1 is only half a cycle: its "before" is the baseline, not a prior sketch. **This is acceptable and should be stated rather than papered over.** `29-BASELINE.md` is a genuine, measured, screenshotted prior state of the real artifact — a stronger "before" than a sketch of a sketch would be. The chain baseline → iter-1 → iter-2 contains two complete redesign→re-measure transitions, which is what MAPUX-02's "at least two full iterations" is protecting. Record this reading explicitly in `29-DESIGN-SPEC.md` § loop-history so the returning human is not left to wonder whether a cycle was skipped. **No plan change beyond that sentence.**

---

## F17 — Two verify blocks pass on a typed word.

`29-01-PLAN.md:138` (`grep -c "newsToggleDiscoverable" SCORE.md`) and `29-01-PLAN.md:122` (`grep -c "showModal" mobile-375.html`) both pass on the literal string appearing anywhere — in a comment, in prose, in a hand-typed approximation of JSON. The `<done>` text for both says the artifact must be *real* output; nothing checks it. Superseded in substance by A7 (`check-iteration.mjs` JSON-parses and checks types/timestamps) and A20 (`:modal` check replaces the `showModal` grep). **Amendment A21**: apply A7's `check-iteration.mjs 1` to Plan 29-01 Task 3's verify as well, and drop the `showModal` grep in favour of the `:modal` assertion result being present in `SCORE.md`.

---

## Three things the listed angles miss

**M1 — The plans are structurally unable to fail the phase.** Every `<automated>` block in both plans is `test -f` plus `grep -c`. Not one asserts a *value*. A phase whose entire gate surface is "the files exist" will close green on an empty design loop. A7, A13 and A16 are the minimum needed to make Phase 29's own close gate capable of turning red. This is operating lesson 14 restated at the phase level: pick MAPUX-02 (≥2 real iterations) and ask what would go red if it were violated — currently nothing.

**M2 — The design spec must survive Phase 28's `?region=` trap, and the plan half-knows it.** `29-02-PLAN.md:82` cites MAPSH-07 ("shared vocabulary via data, not a code dependency") but never mentions Phase 28 Outcome N1: `/news/`'s `?region=` is **CSV multi-value**, the map's is **single-value focus**, and Phase 30 must NOT reuse `parseFilterParams`. If the spec's grouped-entry-point design implies multi-select region filtering on the map (which "grouped by dimension, CrimeMapping-style" naturally suggests), it will pull Phase 30 straight into that trap. Folded into F8 item 8 — the spec must state the semantics of every filter dimension it introduces as single- or multi-select, and explicitly note the divergence from `/news/`.

**M3 — The F-40 redirect hazard is unfixed and Phase 30's whole method depends on it.** `29-BASELINE.md:91-99` records that `BaseLayout.astro:116-131` bounced a local `/map/` tab to production mid-session, and that the baseline had to be re-taken on an ES URL to avoid contamination. F-40 records it; nothing fixes it. Phase 29's sketches are immune (no `hreflang` link), but **Phase 30's entire verification method is driving the real `/map/` in a browser** — the same page that redirects. The next agent to open `http://127.0.0.1:4321/map/` will silently measure production. Either fix the one line now (out of Phase 29's scope, but it is one line and the phase already has the finding), or **`29-DESIGN-SPEC.md` must carry a prominent Phase-30 warning: always drive `http://127.0.0.1:4321/es/mapa/`, never `/map/`, until F-40 is fixed.** Recommendation: put the warning in the spec (respects the hard gate — the fix touches `site/`, and F12's `git status --porcelain -- site/` check would flag it) and add "fix F-40's cross-origin redirect" as an explicit Phase 30 Wave-0 task.

---

## Amendment checklist for the planner

Blocking (must land before Fable approval): **A1, A2, A3** (criterion 5 can fire) · **A4** (screenshot paths) · **A5** (HTTP-served sketches, same-origin iframe) · **A6, A7** (pre-registered stress conditions + `check-iteration.mjs`) · **A8, A9** (independent Opus review before acceptance — discharges F-39) · **A15** (F-42, not F-39) · **A16** (astro-check gate + subshell) · **A17** (`git status --porcelain -- site/`).

Strongly recommended: **A10, A11** (falsifiable criterion 2, matrix scoring) · **A12** (full stand-in inventory; the bottom-right corner is occupied) · **A13** (nine-section spec + `check-spec.mjs`) · **A14** (BrowserOS resume protocol) · **A18** (occlusion thresholds) · **A19** (full-bleed in or out) · **A20** (F-41 method for criterion 4; `:modal` assertion) · **A21**.

Accepted without change: **F16** (record the reading, no plan change).

Before approving the revised plans, run every `<automated>` block once against the real tree (operating lesson 16), and construct one counterexample per new assertion and prove it exits non-zero (operating lesson 9) — including copying `iter-1/` to a scratch `iter-2/` and confirming `check-iteration.mjs 2` exits 1.
