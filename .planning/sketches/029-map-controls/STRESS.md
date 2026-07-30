# Phase 29 — FROZEN stress conditions

**Written 2026-07-30, before `iter-1/` existed.** Plan 29-01 Task 1b's gate asserts that directory was empty at the moment this file was written, so these conditions cannot have been reverse-engineered from a design.

**These are frozen. Do not amend them after seeing a score.** This is the F-02 precedent applied to a design loop: F-02 froze the rapidfuzz threshold before any precision number was observed, because tuning a measurement after seeing its result is the circularity the gate exists to prevent. The same reasoning applies here with more force, because in this phase the same agent authors both the design and the rubric.

## The problem these solve

Iteration 1's build instructions **are** the rubric criteria — "always-visible news toggle at z-index ≥ 800, outside the scrollable row" is simultaneously the design brief and the thing criterion 1 measures. So iteration 1 scores well by construction, iteration 2 inherits no failing target, and the only remaining evidence that a second *design* happened would be prose. Without an adversarial harness, a recolour of iteration 1 with the word "CrimeMapping" typed into its delta note satisfies every other gate in the phase.

These conditions exist so that a sketch can **lose**.

## Conditions

Each is scored separately; `stressCondition` in every JSON blob must be one of these ids, and `check-iteration.mjs` fails an iteration that skips any of them.

- id: desktop-1296
  Nominal desktop, 1296 px — matches the baseline capture width so the numbers are directly comparable to `29-BASELINE.md` §1.

- id: mobile-375
  375 px via the same-origin `mobile-frame.html` harness. Never `file://`.

- id: narrow-320
  320 px. iPhone SE and the Galaxy Fold cover screen still ship at this width; **375 is not the floor**, and a shell that only survives at 375 is untested at the size where it is most likely to break.

- id: breakpoint-481
  481 px — one pixel above `map.css`'s `max-width: 480px` band, where `.mode-toggle` stops being `position: static` and `.legend-mobile` stops being a `<details>`. Designs are routinely validated at "desktop" and "mobile" and never at the pixel where the rules actually switch.

- id: breakpoint-639
  639 px — one pixel below the `640px` band that governs `.zoom-ctl` visibility and `.result-panel`'s desktop-vs-bottom-sheet form. This is the band Phase 25's P0 tablet-overflow defect lived in, so it has already failed once in this codebase.

- id: content-growth
  At 1296 px, inject a 9th crime-family chip and a second year-select via `evaluate_script` before scoring. `29-RESEARCH.md`'s Pitfall 3 names content growth as the warning sign for exactly this failure and the rubric never implemented it. A shell that only fits today's eight families is one CEAD taxonomy change from regressing.

- id: longest-label
  At 375 px, replace every filter label with the longest string it can actually carry: ES `Robos con violencia o intimidación`, EN `Violent robbery and intimidation`. **Both locales ship.** A shell laid out against EN labels and validated only in EN is broken for half the audience, and ES is the longer language here.

- id: text-150pct
  At 375 px, set `document.documentElement.style.fontSize = '24px'` (WCAG 1.4.4 — 150 % text) before scoring. Reflow at enlarged text is an accessibility requirement, not a nicety.

## Pre-registered thresholds

Fixed now, before any score exists:

| Metric | Threshold | Gating? |
|---|---|---|
| `newsToggleDiscoverable` | must be `true` (in viewport **and** topmost at its own centre) | **yes** |
| `filterEntryDiscoverable` | must be `true` | **yes** |
| `filterOverflowsContainer` | must be `false` — no element anywhere in the document may hide > 8 px of horizontal content | **yes** |
| `touchTargetViolations` | `=== 0` at `mobile-375` and `narrow-320` | **yes** |
| `keyboardTrapFree` | must be `true` (0 negative tabindex, 0 key interceptors) | **yes** |
| `zIndexViolations.length` | `=== 0`; `z-index: auto` on a non-modal control counts as a violation | **yes** |
| `controlCoveragePct` | `<= 25 %` at 375 px with all panels closed (baseline is 24.7 %, so this forbids getting worse) | **yes** |
| `mapWidthRatio` | recorded every run | **NOT gating — F-43.** Full-bleed is out of scope: achieving it means editing `.map-stage`/`.map-canvas` in `map.css`, which MAPSH-05 confines Phase 30 away from. |
| `criterion5 === 'NOT_MEASURED_FAIL'` | forbidden — a sketch without a Leaflet pane stand-in is not a scored iteration | **yes** |

## Anti-theater rule

**A row with no `FAIL` anywhere in it, and no prior row to improve on, is evidence that the harness is too weak — not that the design is perfect.**

If iteration 1 passes all eight conditions on the first attempt, that fact is recorded explicitly in `iter-1/SCORE.md` and a **ninth, harder condition is appended here before iteration 2 is designed** — rather than declaring the loop converged. Adding a condition after iteration 1 is legitimate precisely because it raises the bar; loosening or removing one after seeing a score is not, and is banned.
