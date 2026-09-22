# Phase 30 — Wave 0 baseline (pre-implementation)

Captured 2026-07-30 by the orchestrator (Fable) INLINE in BrowserOS, against a **real served build**
of the unmodified map control shell. This is the document Plan 30-06 diffs the close capture against.

**PHASE30_BASE_SHA: 3b45ca4431fdce08b27cd10efd63595218a843d5**

That is the commit immediately BEFORE any Phase 30 code landed (the planning commit). Plan 30-06's
protected-file gate anchors its `git diff` to this SHA rather than to `HEAD`, because this run makes
atomic commits mid-phase — a working-tree-vs-HEAD diff would be empty after any mid-phase commit and
therefore could never fail (Opus plan-check blocker 3).

## Method (reproduce exactly at close)

1. `cd site && npm run build && npm run validate` (chained — OneDrive `dist/` desync rule), then
   `npm test`. Result at capture time: build OK, **16/16 validators**, **vitest 37 passed**.
2. `npx astro preview --port 4321 --host`.
3. `cp .planning/sketches/029-map-controls/score.mjs site/dist/_score.mjs` — the instrument is served
   **byte-unchanged** from the build output so the page can `import()` it. `dist/` is gitignored, so
   this does not dirty the tree and does not modify `score.mjs` (F-49; the file is inside Plan 30-06's
   SHA-anchored byte-identical gate).
4. Open `http://127.0.0.1:4321/es/mapa/` — **never `/map/`**. Inject a same-origin `<iframe>` whose
   `src` is `/es/mapa/`, pinned to `width = <band>`, **`height = 800`** at every band (F-44: a
   `file://` iframe has an opaque origin and `contentDocument` returns null; premortem §13: coverage,
   `inViewport` and `mapWidthRatio` are all functions of viewport height, so an unpinned height makes
   the pre/post diff uninterpretable). Wait 3.5 s after `load` for Leaflet to settle.
5. Inside the iframe context: `const m = await import('/_score.mjs'); m.scoreControlShell({...})`,
   then `m.verdict(r)`.

**F-40 regression note.** The redirect fix landed before this capture (`BaseLayout.astro`, one line:
the target is now built from `new URL(esLink.href).pathname + search + hash`, keeping the current
origin). The browser-side proof would require spoofing `navigator.languages`, which BrowserOS cannot
do directly — so it is recorded as **not independently reproduced in-browser**; the source-level gate
is the real proof, and it exits 0. This is a deliberate acceptance, not a silent skip: the script only
runs on `lang === 'en'` pages, and every measurement in this phase drives `/es/mapa/`, where it never
fires.

## Results — five widths, height pinned to 800

| Width | c1 news toggle | c2 filters / hidden overflow | c3 targets | c4 keyboard | c5 z-index | coverage % | mapWidthRatio |
|---|---|---|---|---|---|---|---|
| **1296** | **FAIL** — rect x = **1370**, offscreen | **FAIL** — **507 px** hidden, `scrollbarSuppressed: true` | FAIL — 20 | **PASS** | **FAIL** — `legend=700` | **21.9** | 0.627 |
| **639** | FAIL — x = 1151 | FAIL — **727 px** | FAIL — 19 | PASS | FAIL — `legend=700` | **24.3** | 0.926 |
| **481** | FAIL — x = 1151 | FAIL — **885 px** | FAIL — 19 | PASS | FAIL — `legend=700` | **27.6** | 0.901 |
| **375** | FAIL — x = 1151 | FAIL — **991 px** | FAIL — 20 | PASS | FAIL — `legend=700` | **27.5** | 0.875 |
| **320** | FAIL — x = 1151 | FAIL — **1046 px** | FAIL — 20 | PASS | FAIL — `legend=700` | **28.6** | 0.853 |

`verdict()` at every width: `c1 false, c2 false, c3 false, c4 true, c5 false`.
Constant across all five: `entryPointCount: 0`, `filterEntryCandidates: 1` (the legacy `.filters-row`),
`negativeTabindexCount: 0`, `keyInterceptors: []`, `focusableCount: 45`,
`controlZIndexes: [map-topbar=800, mode-toggle=801, legend=700]`, and `hiddenOverflowElements` = the
Leaflet canvas (benign, tile pane) plus **`.filters-row` with the scrollbar suppressed** — the exact
baseline defect, reproduced.

This reproduces `29-DESIGN-SPEC.md` §0's headline figures independently: toggle at x=1370, 507 px of
hidden overflow at desktop, 991 px at 375, `legend=700`, ratio 0.627.

### Verbatim capture — 1296 px (full JSON, unabridged)

```json
{"capturedAt":"2026-07-30T20:33:02.479Z","pageUrl":"http://127.0.0.1:4321/es/mapa/","viewportWidthPx":1296,"viewportHeightPx":800,"stressCondition":"baseline-1296","newsToggleMissing":false,"newsToggleRect":{"x":1370,"y":124,"w":167,"h":44},"newsToggleInViewport":false,"newsToggleTopmost":false,"newsToggleDiscoverable":false,"criterion1":"FAIL","filterEntryCandidates":1,"filterEntryMissing":false,"filterEntryDiscoverable":true,"hiddenOverflowElements":[{"cls":"map-canvas leaflet-container leaflet-touch leaflet-retina leaflet-fade-anim leaflet-grab leaflet-touch-drag leaflet-touch-zoom","overflowPx":428,"scrollbarSuppressed":false},{"cls":"filters-row","overflowPx":507,"scrollbarSuppressed":true}],"filterOverflowsContainer":true,"filterOverflowPx":507,"entryPointCount":0,"criterion2":"FAIL","touchTargetViolations":20,"criterion3":"FAIL","focusableCount":45,"negativeTabindexCount":0,"keyInterceptors":[],"externalScriptCount":0,"keyboardTrapFree":true,"criterion4":"PASS","controlZIndexes":[{"cls":"map-topbar","zIndexRaw":"800","zIndex":800,"governedByAncestor":false},{"cls":"mode-toggle","zIndexRaw":"801","zIndex":801,"governedByAncestor":false},{"cls":"legend","zIndexRaw":"700","zIndex":700,"governedByAncestor":false}],"zIndexViolations":[{"cls":"legend","zIndexRaw":"700","zIndex":700,"governedByAncestor":false}],"mapVisibleWidthPx":812,"mapWidthRatio":0.627,"controlCoveragePct":21.9,"criterion5":"FAIL"}
```

**Recorded deviation (ratified, not silent):** for the other four widths this document stores the full
field projection above rather than the raw JSON blob — every field any close-comparison rule consumes
(`verdict`, all five criteria, rects, overflow list, target detail at 320/375/1296, z-index list,
coverage, ratio, viewport w/h) is present. The harness is deterministic and documented above, so any
capture is re-runnable byte-for-byte.

### c3 baseline detail — the 20 violations (identical set at 320, 375, 1296)

**Map-owned (this phase MUST fix these — F-51):**

| Element | Size | Where |
|---|---|---|
| locate button (`BUTTON`) | **32 × 32** | `map.css:344-357` — the one `29-DESIGN-SPEC.md:134` names explicitly |
| zoom `+` / `−` | **36 × 36** each | `map.css:277-280` (absent at 320/375 — `.zoom-ctl` appears only ≥640) |
| search `INPUT` | 268 × **17** (1296), 174 × 17 (375), 156 × 17 (320) | inside `.map-topbar`; the input itself is 17 px tall inside a taller wrapper |
| mode toggle (`Índice delictivo ▸Índice…`) | 97 × **18** | at ≤480 only; disappears with the toggle's fold into the rail |
| hidden `INPUT` 1 × 1 | 1 × 1 | at ≤480; a hidden control — re-check at close whether it is rendered |

**Outside MAPSH-05's confinement — accepted and recorded by name (F-51):** the skip link
(`Ir al contenido principal` 185×29), the site title (184×30), the `EN` locale links (39×29 and 19×21),
the Leaflet attribution anchors (`OpenStreetMap` 85×14, `CARTO` 42×14), and the eight header/footer
nav links (`Mapa`, `Comunas`, `Rankings`, `Noticias`, `Glosario`, `¿Es seguro Chile?`,
`Política de Privacidad`, `Términos de Uso`, `Acerca de`, `Contacto` — all 21 px tall). Fixing these
would touch `PageHeader`/`PageFooter`/`BaseLayout`, i.e. every page on a live production site, which is
the scope creep this phase's regression-risk annotation forbids.

---

## Two corrections this capture forces on decisions taken before it

### 1. c4 is measurable on the real page, and it PASSES — F-53(a) was wrong

`externalScriptCount` is **0** at all five widths, so `score.mjs`'s fail-closed branch
(`score.mjs:145-151`) is **never taken** on the real `/es/mapa/`; `criterion4` returns a real
**PASS**, with `keyInterceptors: []` and `negativeTabindexCount: 0`. Both the premortem's §8 claim
("`c4` can never be `true` on any Astro page") and my own F-53(a) pre-registration were **falsified by
measurement**. `29-DESIGN-SPEC.md` §0's "c4 PASS" was correct all along.

**Consequence, and it inverts the close rule:** c4 must **STAY PASS**. A flip to `FAIL` or
`NOT_MEASURED_FAIL` at close is a **real regression introduced by this phase**, not an instrument
artifact, and must be diagnosed — not narrated. Concretely, the scan CAN see this page's script text,
so a `keydown`/`keyup`/`preventDefault` string landing in scannable script would redden it. That is
another independent reason the rail's Escape handling is a **container-scoped React `onKeyDown`** and
not a `document` listener. F-49's three-part evidence chain still gets recorded at close, but now as
corroboration of a PASS rather than as a substitute for an unmeasurable criterion.

This is exactly why Wave 0 measures instead of inheriting: two documents and one of my own decisions
agreed on a number that the instrument, run once, contradicts.

### 2. The F-50 coverage ceilings are sketch figures, and at three bands the real app is already better

| Band | F-46/F-50 sketch ceiling | **Real pre-change** | Binding ceiling at close (F-54) |
|---|---|---|---|
| 1296 | 33.2 % | **21.9 %** | **21.9 %** |
| 639 | (none) | **24.3 %** | **24.3 %** |
| 481 | 43.1 % | **27.6 %** | **27.6 %** |
| 375 | 22.7 % | **27.5 %** | **22.7 %** — must IMPROVE |
| 320 | 32.2 % | **28.6 %** | **28.6 %** |

Allowing the sketch's 33.2 % at 1296 would let the rework hand an extra 11 points of the map to chrome
and still call it "within ceiling". The binding rule is therefore **`min(sketch ceiling, measured
pre-change)` at every band** — no band may regress, and the sketch ceilings still cap. At 375 that
cuts the other way: today's 27.5 % already breaches both F-50's 22.7 % and `verdict()`'s hard ≤25 %
rule, so the phase must genuinely reduce chrome there. That is a demanding but coherent target — the
scrolling filter row is replaced by a single FAB below 480 px, which is where the reduction comes from.

Recorded as **F-54** in STATE.md. This tightens the bar and loosens nothing, so it does not touch
`STRESS.md`'s freeze.
