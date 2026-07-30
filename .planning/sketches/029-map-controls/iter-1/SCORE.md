# Iteration 1 — score

**Measured** 2026-07-30 in BrowserOS against sketches served over HTTP at `http://127.0.0.1:4399` (never `file://` — an opaque origin whose `contentDocument` is `null`, which would have made every narrow-viewport measurement come back empty). Narrow widths emulated through the committed `mobile-frame.html` same-origin iframe harness.

## What iteration 1 changed, and against which baseline defect

The baseline's news-layer toggle was the **last** chip in a row overflowing **507 px** on desktop and **991 px** at 375 px (`29-BASELINE.md` §1–2), so it sat ~590 px past the visible edge with no scroll affordance — `map.css:47-59` suppresses the scrollbar twice (`scrollbar-width:none` plus a hidden `::-webkit-scrollbar`).

Iteration 1 does two things and deliberately no more:
1. Lifts the news toggle **out of the scrolling row** into the topbar's first row, with an explicit `z-index: 800`.
2. Restores an overflow affordance on the chip row (trailing mask fade, visible thin scrollbar, `›` hint).

It **keeps the flat scrolling chip row**. That is the honest scope of this iteration, and it is why criterion 2 still fails below — giving iteration 2 a measured target rather than a matter of taste.

## Results — 8 frozen conditions (STRESS.md)

| Condition | vw | c1 news | c2 filters | c3 targets | c4 keyboard | c5 z/occlusion | overflow | coverage |
|---|---|---|---|---|---|---|---|---|
| desktop-1296 | 1296 | PASS | PASS | **FAIL** | PASS | PASS | 0 px | 35.2 % |
| content-growth | 1296 | PASS | **FAIL** | **FAIL** | PASS | PASS | **52 px** | 38.5 % |
| mobile-375 | 375 | PASS | PASS | PASS | PASS | PASS | 0 px | 13.4 % |
| narrow-320 | 320 | PASS | PASS | PASS | PASS | PASS | 0 px | 14.3 % |
| longest-label | 375 | PASS | PASS | PASS | PASS | PASS | 0 px | 13.4 % |
| text-150pct | 375 | PASS | PASS | PASS | PASS | PASS | 0 px | 13.4 % |
| breakpoint-639 | 639 | PASS | **FAIL** | **FAIL** | PASS | PASS | **479 px** | 35.7 % |
| breakpoint-481 | 481 | **FAIL** | **FAIL** | **FAIL** | PASS | PASS | **637 px** | 36.8 % |

**Iteration 1 did not sweep the board.** The pre-registered conditions broke it in three independent ways, which is the entire reason they were frozen before it was designed.

## The four defects iteration 2 must fix

1. **`breakpoint-481` reproduces the baseline bug exactly.** `newsToggleDiscoverable: false` — the toggle's rect is x=404 w=183 against a 481 px viewport, so the very control this iteration exists to rescue is **back offscreen** in the 480–639 px band. The fix moved the toggle out of the scroll row but did nothing about the topbar's own horizontal budget.
2. **The split-file design cannot answer breakpoint questions honestly.** `desktop.html` and `mobile-375.html` are two files with **no media queries**, so at 481 px and 639 px the desktop sketch simply overflows — 637 px and 479 px respectively, i.e. *worse than the 507 px baseline it was meant to fix*. The real app is one responsive page with real bands at 480 and 640 (`map.css:192/210/240/271`). **Iteration 2 must be a single responsive file** or its breakpoint scores are fiction.
3. **A 32 × 32 px touch target** — the locate button (`◎`), carried over from the real `.locate-btn-visible`. Fails WCAG 2.5.5 at every desktop-family width. It is a genuine finding that transfers to the real app, not a sketch artifact.
4. **`aria-expanded` is never reset when the filter sheet closes.** Verified by execution: `rest=false → open=true → afterCloseBtn=true` while `dialog.open` is correctly `false`. A freshly-attached `close` listener also recorded `closeEventsFired: 0`, so the handler wiring is wrong, not merely the attribute. A screen-reader user is told the sheet is still expanded after closing it.

## What genuinely passed

- **`showModal()` is real, and proven so.** `dialog.matches(':modal')` is `false` at rest and **`true`** when opened, with `dlg.contains(document.activeElement)` true — native top-layer modality, so focus containment, ESC and the backdrop come for free with **zero new JS dependencies** (MAPSH-02). This is the assertion that distinguishes a real `showModal()` from a declarative `<dialog open>`; `grep -c "showModal"` cannot.
- **Criterion 4 by construction (F-41 standard):** `negativeTabindexCount: 0` and `keyInterceptors: []` at every condition — no script intercepts `keydown`/`keyup`/`preventDefault`, so native tab order applies and a trap is impossible.
- **Criterion 5 clean** at every condition after the rubric correction below: `zIndexViolations: []`, with `map-topbar=800`, `news-toggle=800`, `mode-toggle=801`, `filter-fab=800`, `legend=700`.
- Mobile coverage **13.4 %**, comfortably inside the pre-registered ≤ 25 % ceiling (baseline was 24.7 %).

## A correction made to the rubric, recorded rather than buried

The first run flagged `.filters-row` as a `z-index` violation because its computed value is `auto`. That was a **false positive in the rubric, not a defect in the design**: `.filters-row` is nested inside `.map-topbar`, which carries `z-index: 800` and governs its stacking context. `score.mjs` now treats `auto` as a violation only when no control ancestor carries an explicit `z-index >= 700`.

This is a correction to a *measurement*, not a loosening of a *threshold*, which is why it is not barred by STRESS.md's freeze. It was proven falsifiable in both directions before being accepted: against the corrected sketch `zIndexViolations: []` / `criterion5: PASS`, and against an injected body-level control with no `z-index` at all, `criterion5: FAIL` with `governedByAncestor: false`.

## A measurement gap, stated so iteration 2 closes it

`longest-label` and `text-150pct` both scored straight PASSes at 375 px — but **only because the filter chips live inside a closed `<dialog>`**, so they were not laid out and could not overflow. Those two conditions are currently near-vacuous on mobile. Iteration 2 must score them **with the sheet open**, or they measure nothing.

## Raw measurements

Full `evaluate_script` output, unedited except that three verbose arrays are summarized into `overflowElements` / `zIndexSummary` / `smallestTarget` (counts and identities preserved).

```json
{"capturedAt":"2026-07-30T18:08:15.633Z","pageUrl":"http://127.0.0.1:4399/iter-1/desktop.html","viewportWidthPx":1296,"viewportHeightPx":678,"stressCondition":"desktop-1296","newsToggleMissing":false,"newsToggleRect":{"x":404,"y":76,"w":183,"h":44},"newsToggleInViewport":true,"newsToggleTopmost":true,"newsToggleDiscoverable":true,"criterion1":"PASS","filterEntryMissing":false,"filterEntryDiscoverable":true,"filterOverflowsContainer":false,"filterOverflowPx":0,"entryPointCount":0,"criterion2":"PASS","touchTargetViolations":1,"criterion3":"FAIL","focusableCount":18,"negativeTabindexCount":0,"keyInterceptors":[],"keyboardTrapFree":true,"criterion4":"PASS","zIndexViolations":[],"mapVisibleWidthPx":1296,"mapWidthRatio":1,"controlCoveragePct":35.2,"criterion5":"PASS","smallestTarget":{"t":"◎","w":32,"h":32},"overflowElements":[],"zIndexSummary":["map-topbar=800","news-toggle=800","mode-toggle=801","filters-row=auto","legend=700"]}
```

```json
{"capturedAt":"2026-07-30T18:08:15.634Z","pageUrl":"http://127.0.0.1:4399/iter-1/desktop.html","viewportWidthPx":1296,"viewportHeightPx":678,"stressCondition":"content-growth","newsToggleMissing":false,"newsToggleRect":{"x":404,"y":76,"w":183,"h":44},"newsToggleInViewport":true,"newsToggleTopmost":true,"newsToggleDiscoverable":true,"criterion1":"PASS","filterEntryMissing":false,"filterEntryDiscoverable":true,"filterOverflowsContainer":true,"filterOverflowPx":52,"entryPointCount":0,"criterion2":"FAIL","touchTargetViolations":1,"criterion3":"FAIL","focusableCount":20,"negativeTabindexCount":0,"keyInterceptors":[],"keyboardTrapFree":true,"criterion4":"PASS","zIndexViolations":[],"mapVisibleWidthPx":1296,"mapWidthRatio":1,"controlCoveragePct":38.5,"criterion5":"PASS","smallestTarget":{"t":"◎","w":32,"h":32},"overflowElements":["filters-row:52px"],"zIndexSummary":["map-topbar=800","news-toggle=800","mode-toggle=801","filters-row=auto","legend=700"]}
```

```json
{"capturedAt":"2026-07-30T18:09:51.230Z","pageUrl":"http://127.0.0.1:4399/iter-1/mobile-375.html","viewportWidthPx":375,"viewportHeightPx":812,"stressCondition":"mobile-375","newsToggleMissing":false,"newsToggleRect":{"x":268,"y":64,"w":99,"h":44},"newsToggleInViewport":true,"newsToggleTopmost":true,"newsToggleDiscoverable":true,"criterion1":"PASS","filterEntryMissing":false,"filterEntryDiscoverable":true,"filterOverflowsContainer":false,"filterOverflowPx":0,"entryPointCount":0,"criterion2":"PASS","touchTargetViolations":0,"criterion3":"PASS","focusableCount":15,"negativeTabindexCount":0,"keyInterceptors":[],"keyboardTrapFree":true,"criterion4":"PASS","zIndexViolations":[],"mapVisibleWidthPx":375,"mapWidthRatio":1.001,"controlCoveragePct":13.4,"criterion5":"PASS","smallestTarget":null,"overflowElements":[],"zIndexSummary":["map-topbar=800","news-toggle=800","filter-fab=800","legend=700"]}
```

```json
{"capturedAt":"2026-07-30T18:09:52.231Z","pageUrl":"http://127.0.0.1:4399/iter-1/mobile-375.html","viewportWidthPx":320,"viewportHeightPx":812,"stressCondition":"narrow-320","newsToggleMissing":false,"newsToggleRect":{"x":213,"y":64,"w":99,"h":44},"newsToggleInViewport":true,"newsToggleTopmost":true,"newsToggleDiscoverable":true,"criterion1":"PASS","filterEntryMissing":false,"filterEntryDiscoverable":true,"filterOverflowsContainer":false,"filterOverflowPx":0,"entryPointCount":0,"criterion2":"PASS","touchTargetViolations":0,"criterion3":"PASS","focusableCount":15,"negativeTabindexCount":0,"keyInterceptors":[],"keyboardTrapFree":true,"criterion4":"PASS","zIndexViolations":[],"mapVisibleWidthPx":320,"mapWidthRatio":1,"controlCoveragePct":14.3,"criterion5":"PASS","smallestTarget":null,"overflowElements":[],"zIndexSummary":["map-topbar=800","news-toggle=800","filter-fab=800","legend=700"]}
```

```json
{"capturedAt":"2026-07-30T18:09:54.245Z","pageUrl":"http://127.0.0.1:4399/iter-1/mobile-375.html","viewportWidthPx":375,"viewportHeightPx":812,"stressCondition":"longest-label","newsToggleMissing":false,"newsToggleRect":{"x":268,"y":64,"w":99,"h":44},"newsToggleInViewport":true,"newsToggleTopmost":true,"newsToggleDiscoverable":true,"criterion1":"PASS","filterEntryMissing":false,"filterEntryDiscoverable":true,"filterOverflowsContainer":false,"filterOverflowPx":0,"entryPointCount":0,"criterion2":"PASS","touchTargetViolations":0,"criterion3":"PASS","focusableCount":15,"negativeTabindexCount":0,"keyInterceptors":[],"keyboardTrapFree":true,"criterion4":"PASS","zIndexViolations":[],"mapVisibleWidthPx":375,"mapWidthRatio":1.001,"controlCoveragePct":13.4,"criterion5":"PASS","smallestTarget":null,"overflowElements":[],"zIndexSummary":["map-topbar=800","news-toggle=800","filter-fab=800","legend=700"]}
```

```json
{"capturedAt":"2026-07-30T18:09:55.244Z","pageUrl":"http://127.0.0.1:4399/iter-1/mobile-375.html","viewportWidthPx":375,"viewportHeightPx":812,"stressCondition":"text-150pct","newsToggleMissing":false,"newsToggleRect":{"x":268,"y":64,"w":99,"h":44},"newsToggleInViewport":true,"newsToggleTopmost":true,"newsToggleDiscoverable":true,"criterion1":"PASS","filterEntryMissing":false,"filterEntryDiscoverable":true,"filterOverflowsContainer":false,"filterOverflowPx":0,"entryPointCount":0,"criterion2":"PASS","touchTargetViolations":0,"criterion3":"PASS","focusableCount":15,"negativeTabindexCount":0,"keyInterceptors":[],"keyboardTrapFree":true,"criterion4":"PASS","zIndexViolations":[],"mapVisibleWidthPx":375,"mapWidthRatio":1.001,"controlCoveragePct":13.4,"criterion5":"PASS","smallestTarget":null,"overflowElements":[],"zIndexSummary":["map-topbar=800","news-toggle=800","filter-fab=800","legend=700"]}
```

```json
{"capturedAt":"2026-07-30T18:09:56.231Z","pageUrl":"http://127.0.0.1:4399/iter-1/desktop.html","viewportWidthPx":639,"viewportHeightPx":812,"stressCondition":"breakpoint-639","newsToggleMissing":false,"newsToggleRect":{"x":404,"y":76,"w":183,"h":44},"newsToggleInViewport":true,"newsToggleTopmost":true,"newsToggleDiscoverable":true,"criterion1":"PASS","filterEntryMissing":false,"filterEntryDiscoverable":true,"filterOverflowsContainer":true,"filterOverflowPx":479,"entryPointCount":0,"criterion2":"FAIL","touchTargetViolations":1,"criterion3":"FAIL","focusableCount":18,"negativeTabindexCount":0,"keyInterceptors":[],"keyboardTrapFree":true,"criterion4":"PASS","zIndexViolations":[],"mapVisibleWidthPx":624,"mapWidthRatio":0.977,"controlCoveragePct":35.7,"criterion5":"PASS","smallestTarget":{"t":"◎","w":32,"h":32},"overflowElements":["filters-row:479px"],"zIndexSummary":["map-topbar=800","news-toggle=800","mode-toggle=801","filters-row=auto","legend=700"]}
```

```json
{"capturedAt":"2026-07-30T18:09:57.243Z","pageUrl":"http://127.0.0.1:4399/iter-1/desktop.html","viewportWidthPx":481,"viewportHeightPx":812,"stressCondition":"breakpoint-481","newsToggleMissing":false,"newsToggleRect":{"x":404,"y":76,"w":183,"h":44},"newsToggleInViewport":false,"newsToggleTopmost":false,"newsToggleDiscoverable":false,"criterion1":"FAIL","filterEntryMissing":false,"filterEntryDiscoverable":true,"filterOverflowsContainer":true,"filterOverflowPx":637,"entryPointCount":0,"criterion2":"FAIL","touchTargetViolations":1,"criterion3":"FAIL","focusableCount":18,"negativeTabindexCount":0,"keyInterceptors":[],"keyboardTrapFree":true,"criterion4":"PASS","zIndexViolations":[],"mapVisibleWidthPx":466,"mapWidthRatio":0.968,"controlCoveragePct":36.8,"criterion5":"PASS","smallestTarget":{"t":"◎","w":32,"h":32},"overflowElements":["filters-row:637px"],"zIndexSummary":["map-topbar=800","news-toggle=800","mode-toggle=801","filters-row=auto","legend=700"]}
```

### Modal / focus interaction (desktop-equivalent, run on the mobile sheet where the dialog lives)

Fenced as `jsonc`, not `json`: this is an interaction trace, not a rubric score blob, and `check-iteration.mjs` validates every ```json block as a score blob (it correctly rejected this one when it was mislabelled).

```jsonc
{"invoker":"filter-fab","dialogOpenAtRest":false,"isModalAtRest":false,"onOpen":{"open":true,"isModal":true,"ariaExpanded":"true","focusInsideDialog":true},"onClose":{"open":false,"ariaExpanded":"true","focusReturnedToInvoker":true},"defect":"aria-expanded not reset on close; a freshly-attached close listener recorded closeEventsFired:0","keyboardTrapFree":true}
```

## Screenshots

`desktop.png` (1296 px) · `mobile-375.png` (375 px). Captured to `C:\Users\Carlo\bos-shots\p29\` first, because `save_screenshot` cannot write to a path containing spaces, then copied into this directory.
