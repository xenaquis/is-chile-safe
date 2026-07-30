# Phase 30 — Binding Fable constraints (read BEFORE researching or planning)

These are orchestrator decisions taken **before** research, so the phase implements rather than
re-decides. They are mirrored into `.planning/STATE.md` § Fable Decisions as F-47..F-50 and are
binding on every plan, task and gate in this phase. Do not re-litigate them.

The design contract itself is `.planning/phases/29-map-ux-design-loop/29-DESIGN-SPEC.md` — **fully
accepted (F-42, F-46)**. It pins values; the phase implements them. It is NOT open for redesign.

---

## F-47 — Spec §9a resolution: option (a), the narrowly-scoped `MapIsland.tsx` edit

`Modo` is folded into a grouped entry point. That requires moving the mode-toggle markup out of
`MapIsland.tsx` (which today builds the `modeToggle` React node and passes it as a prop, see
`MapTopbar.tsx:19-20,47`) into `MapTopbar.tsx`, with `mode` / `onModeChange` passed as plain props.

**MAPSH-05's in-scope list is therefore read as**: `MapTopbar.tsx`, sibling control components,
`map.css`'s control rules, **and the mode-toggle prop wiring in `MapIsland.tsx`**. Nothing else in
`MapIsland.tsx` may be restructured beyond what that prop change and the `?region=` work (F-48)
require.

**Hard invariant, gated in code review AND in an automated gate:** `ChoroplethLayer.ts`,
`IncidentPinLayer.ts` and `LowZoomDotLayer.ts` must be **byte-identical** at phase close
(`git diff --exit-code -- <the three files>` must exit 0). No declarative react-leaflet layer
component (`<GeoJSON>`, `<Marker>`-as-JSX-child) may be introduced anywhere.

## F-48 — MAPSH-04: `?region=` IS implemented in this phase, single-value, own parser

Roadmap success criterion 4 requires it and the spec declares it out of scope for the *design*
(§9 MAPSH-04), i.e. it is Phase 30's own decision. Decision: **implement it.**

- Semantics: **single-value region focus**, mirroring the existing `?cut=` behaviour — never the
  `/news/` CSV multi-value semantics. **`parseFilterParams` must NOT be reused** (Phase 28 Outcome
  N1 / F-35 N1). Every filter dimension this phase introduces is single-select.
- Unknown / malformed value: degrade **silently** — no fetch of a non-existent file, no 404 in the
  network log, no console error, no toast. Guard before any fetch (the same polish the `?cut=`
  path needed; see memory `map-focus-unknown-cut-polish`).
- `region_id` values are **strings** (F-20), matching `data/cead/meta/index.json` verbatim.
- The existing `?cut=` deep link must keep working **unchanged** — it is a previously-fixed feature.

## F-49 — Criterion 4 (keyboard) may not be made green by editing the instrument

`score.mjs` fails **closed** on c4 when the page ships external module scripts with no inline text
(`criterion4 = 'NOT_MEASURED_FAIL'`) — deliberate, because a static scan cannot see a bundled
handler. Whatever it returns against the real `/es/mapa/`:

- **`score.mjs` may not be edited to turn c4 green.** Measurement-correctness fixes are admissible
  only under F-45's rule (change *which element is measured*, never *what value passes*), must be
  proven falsifiable in both directions, and must be recorded.
- If c4 comes back `NOT_MEASURED_FAIL`, it is settled with the supplementary evidence the file
  itself prescribes: `negativeTabindexCount === 0`, **grep the built `dist/` chunks** for
  `keydown` / `keyup` / `preventDefault` in the map island's own code, **and a real Tab walk** in
  BrowserOS through the full documented focus order (spec §6). All three, recorded.
- Wave 0 must **measure** the current c4 result against the real page rather than assume it, and
  record the baseline verbatim. Phase 29 reported `c4 PASS`; the code path suggests
  `NOT_MEASURED_FAIL` is also possible. Whichever it is, the number is captured before any code
  changes, so the close comparison is against a real baseline.

## F-50 — F-46's coverage figures are CEILINGS, and the three UX mitigations are mandatory

`controlCoveragePct` measured by the accepted design: **33.2 % @1296 · 43.1 % @481 · 32.2 % @320 ·
22.7 % @375**. The real implementation **may not exceed any of them** at its band. The ≤ 25 % @375
threshold from `STRESS.md` also still gates, and may not be loosened.

Mandatory UX mitigations from F-46, each verified:
1. The state summary may truncate with an ellipsis but **never wraps to a second line**.
2. The topbar keeps its **translucent gradient**, so covered map area stays partially legible.
3. Coverage stays at or below the ceilings above.

---

## Non-negotiable environment / process facts for this phase

- **Drive `http://127.0.0.1:4321/es/mapa/`, never `/map/`**, until the Wave-0 fix of F-40 lands
  (`BaseLayout.astro:116-131` redirects an es-locale browser on an EN page to an absolute
  **production** URL, silently substituting production for the build under test). Fixing that one
  line — keep the current origin, take `new URL(esLink.href).pathname + search + hash` — is a
  **Wave 0 task of this phase**. Even after the fix, prefer `/es/mapa/` for continuity with the
  Phase 29 baseline.
- **`FiltersRow.tsx` is DELETED, not refactored**, and `dist/` must be asserted free of
  `.filters-row` and `.ev-chip`. `score.mjs` falls back to those classes, so survivors would bind
  this phase's own instrument to the legacy markup and report on the wrong elements.
- **`score.mjs` is the regression instrument.** Ship the `data-role` hooks (`news-toggle`,
  `filter-entry` on both the grouped rail and the FAB, `entry-point` on each dimension) into the
  real DOM. Bar to reproduce: spec §12, at **320 / 375 / 481 / 639 / 1296**.
- BrowserOS work runs **inline in the orchestrator session** — `gsd-executor` has no BrowserOS
  tools (operating lesson 1). Do not put a BrowserOS step inside an executor task; it will be
  silently skipped. Serve with `npx astro preview --port 4321 --host`; there is no `npm run
  preview`. No viewport-resize tool — emulate narrow widths with an iframe served from the **same
  HTTP origin** (`file://` gives an opaque origin and `contentDocument` returns null — F-44).
  `save_screenshot` cannot write to a path containing spaces.
- **OneDrive**: chain `npm run build && npm run validate` (and any `dist/` consumer) in ONE command.
  `npm run validate` does NOT run vitest — chain `npm test` explicitly.
- **`data/` is read-only.** Zero Python changes expected.
- **Gate hygiene (this has appeared 8 times in phases 27–29):** a verify block's exit status must
  never pass through `| tail`, `| head`, `; echo`, `|| echo`, `|| true`, or a `;` that terminates
  an `&&` chain. Every `<automated>` gate must be **run against the real tree before the plan is
  approved**, and must be able to exit non-zero on a broken tree and zero on a correct one.
- Phase-close bar: **pytest 344 passed / 1 skipped / 1 xfailed** (the xfail is Phase 26's
  deliberate quarantine — never "fix" it), **vitest 37**, **16/16 validators**, `astro check`
  4 errors / 0 warnings (pre-existing baseline, `ComparatorPairsLinks.astro:28`).
  If `freshness` goes red purely from local staleness, F-19's branch governs and its listed
  remediations are BANNED.
- **Production is live.** A regression on push reaches real users.
