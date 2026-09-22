---
phase: 30-map-control-shell-rework
verified: 2026-07-30T20:20:00Z
status: gaps_found
score: 4/5 success criteria fully verified (1 PARTIAL); 6/7 requirements PASS, 1 PARTIAL
overrides_applied: 0
gaps:
  - truth: "Success criterion 4 / MAPSH-06 — a full regression pass confirms ?cut=, choropleth year/family filters, commune panel, geolocation and incident pins all still work"
    status: partial
    reason: >
      Every item on the enumerated regression list is evidenced in 30-CLOSE.md §4 EXCEPT geolocation,
      which appears in no measurement table in any phase artifact. The locate control is reached through
      a prop chain that this phase rewrote (MapIsland.onLocate -> MapTopbar -> SearchBox), so
      "UserLocationMarker.ts is untouched" does not by itself establish that the control still fires.
      Static evidence is strong (see below) but the criterion asserts a regression *pass*, and none was run.
    artifacts:
      - path: ".planning/phases/30-map-control-shell-rework/30-CLOSE.md"
        issue: "§4 'Effect assertions — every control still drives the state it drove before' has 9 rows; none is the locate button. §6b/§6c re-measurements do not add one."
      - path: "site/src/components/map/MapTopbar.tsx"
        issue: "onLocate is a new pass-through prop (line 22/37/48) introduced by this phase; no test and no browser assertion exercises it."
    missing:
      - "One browser assertion: click .locate-btn-visible on a served build and confirm the user-dot renders / the commune is selected (or, with geolocation denied, that the documented Santiago fallback path in UserLocationMarker.ts:112 runs) with no console error."
human_verification:
  - test: "On `npx astro preview --port 4321 --host`, open /es/mapa/ in a FOREGROUND tab and click the locate button in the search bar."
    expected: "Geolocation prompt or the documented silent Santiago fallback; a user dot appears and the commune is highlighted/selected; no console error."
    why_human: "Requires a browser with a geolocation permission decision; the verifier has no browser. Closes the only unevidenced item on criterion 4's regression list."
  - test: "Tab from the news toggle through the entry-points rail at 1296px and at 481px."
    expected: "Focus order news-toggle -> Año -> Tipo de delito -> Modo -> zoom '+', skipping the nine tabindex=-1 radios inside closed <details>; no trap."
    why_human: "This is the substitute evidence F-58 uses to overturn the rubric's c4 FAIL at >=481px. It is recorded in 30-CLOSE.md but is not encoded in any automated gate, so nothing would redden if it regressed."
---

# Phase 30: Map Control-Shell Rework — Verification Report

**Phase Goal:** A first-time user, on desktop or at 375px mobile, can immediately find and use the news-layer toggle and the filter panel — implementing the Phase 29-accepted design — while every existing map behavior (choropleth, `?cut=` deep link, geolocation, incident pins) keeps working exactly as before.
**Verified:** 2026-07-30
**Status:** gaps_found (one PARTIAL; no blocker)
**Re-verification:** No — initial verification.

## What I re-ran myself, versus what rests on 30-CLOSE.md

This distinction is load-bearing for this phase, because three of the five success criteria are settled
by browser measurement and I have no browser.

**Re-run by me, in this session (independent of any summary):**

| Command | Expected | Actual | Match |
|---|---|---|---|
| `cd site && npm run build && npm test && npm run validate` | 834 pages, vitest 51, 16/16 | build OK 834 pages · **51/51 tests, 5 files** · **16/16 validators** · exit 0 | ✔ |
| `node site/scripts/phase30-gate.mjs` | all PASS | **12/12 PASS**, exit 0 | ✔ |
| `npx astro check` | 4 errors / 0 warnings at `ComparatorPairsLinks.astro:28` | **4 errors / 0 warnings**, all four at `ComparatorPairsLinks.astro:28` (cols 19/25/31/38, ts7031) | ✔ |
| `python -m pytest -q` (repo root) | 344 / 1 / 1 | **344 passed, 1 skipped, 1 xfailed** | ✔ |
| `git diff 3b45ca44 -- ChoroplethLayer.ts IncidentPinLayer.ts LowZoomDotLayer.ts score.mjs` | empty | **empty** (no output, exit 0) | ✔ |
| `ls site/src/components/map/FiltersRow.tsx` | absent | absent; deleted in `e14c41c` | ✔ |
| `grep -rl "filters-row\|ev-chip" site/dist/` | no hits | **no hits** | ✔ |
| Source reading: control shell, prop chains, import graph | — | see per-criterion evidence below | — |

**Rests on 30-CLOSE.md's browser measurements, which I cannot reproduce:** the toggle being on-screen
and labeled at each of the five widths (c1), `dialog.matches(':modal')` being true, the `aria-expanded`
and focus-return lifecycle, the real-Escape `close` event, the `?cut=`/`?region=` runtime behaviour and
zoom levels, the coverage percentages and topbar heights, the zero-map-owned-sub-44px result, and the
Tab-walk that overturns c4's FAIL. I treat those as evidence — they are specific, falsifiable, recorded
with their own self-corrections and two of them (§5) are recorded measurement artifacts that argue
against a rubber-stamping author — but every conclusion below that depends on them is marked as such.

## Success Criteria

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | News-layer toggle always visible and explicitly labeled, no longer buried in a generic "mode" control | **PASS** | Code (mine): `NewsToggle.tsx` is a standalone component rendered by `MapTopbar.tsx:8`, with `data-role="news-toggle"`, `aria-pressed`, `aria-label`, and two label spans (long/short) — the label shortens below 640px, it is never removed. `news-toggle` is present in the shipped `dist/_astro/MapIsland.*.js`. The old surface is gone: `FiltersRow.tsx` deleted, `.filters-row`/`.ev-chip` absent from `dist/` (gate assertion 5, and my own grep). Browser (CLOSE §1): c1 FAIL→PASS at all five widths, x-offset 1370→618 at 1296 and →132 at 375; `entryPointCount` 0→3. |
| 2 | Filter panel matches the Phase 29 spec, native `<details>`/`<dialog>` + CSS, zero new shipped JS deps, bottom-sheet/FAB on mobile rather than nested in the hamburger nav | **PASS, with one stated spec deviation** | Code (mine): `EntryPointsRail.tsx` uses three native `<details>`/`<summary>` (lines 105/130/155); `FilterSheet.tsx` uses a native `<dialog>` opened via `showModal()` (line 61) — never the `open` attribute — behind a FAB carrying `aria-haspopup="dialog"`. `map.css:1175` deliberately carries **no** z-index on `#filter-sheet` because `showModal()` uses the top layer. Zero new deps: gate assertion 4 verifies `package.json`/`package-lock.json` byte-unchanged vs base SHA (I re-ran it). `showModal(` present in the shipped chunk (gate assertion 6, proven falsifiable by mutation per REREVIEW M-05). Browser-only (CLOSE §3): `:modal` true, rail `display:none` / FAB `display:flex` at 375, focus returns to the FAB on all three dismissal paths. **Deviation:** at ≤480px the persistent state summary (spec §2 item 4) is visually-hidden and screen-reader-only — stated plainly in CLOSE §6c and traded against F-50's 22.7% and STRESS.md's frozen ≤25% ceiling. Recorded, not silent; I accept it as a governed trade rather than a miss. |
| 3 | All map controls keyboard-operable and SR-labeled, **no focus traps**, touch targets ≥44px at 375, no z-index conflict with Leaflet panes | **PASS (evidence-dependent) — see the adversarial note below** | Code (mine): roving tabindex is genuinely implemented in `FilterFields.tsx` (`role="radiogroup"`, `tabIndex={isActive ? 0 : -1}` at :97 and :165, Arrow/Home/End at :61-67 and :136-142) — the WAI-ARIA pattern, container-scoped `onKeyDown`, no document listener. `.locate-btn-visible` is 44×44 (`map.css:512`), zoom/summary/search all carry 44px rules. Gate (mine, re-run): z-index ladder bound per selector (`.news-toggle=800`, `.filter-fab=800`, `.legend=750`), `.legend z-index:700` absent, sheet carries no z-index. Browser (CLOSE §1/§6b/§7): `zIndexViolations: []` at every width; **zero map-owned sub-44px targets** at every width. |
| 4 | `?region=` behaves like `?cut=` incl. graceful degradation, **and a full regression pass confirms `?cut=`, choropleth year/family filters, commune panel, geolocation and incident pins all still work** | **PARTIAL** | `?region=` half: **PASS**. Code (mine): `regionParam.ts` is a pure resolver with padded-form normalisation (M-07) and a `shouldApplyRegionFocus` precedence guard; the `MapIsland.tsx` diff adds exactly three hunks and contains **no `-` lines touching the `?cut=` block** — the deep-link path is byte-identical, region is additive and guarded. `regionParam.test.ts` (74 lines) is in the green 51. Gate assertion 12 pins the precedence guard at source level (REREVIEW N-2 proved deleting it left vitest 51/51 green — a real hole, now closed). Browser (CLOSE §4): `?region=13` zoom 8 panel closed, `?region=99999` default extent + **zero console errors**, `?cut=13101&region=05` commune wins. Regression half: 4 of 5 items evidenced in CLOSE §4 (incident pins 0→1412→0; crime type incl. Homicidios; mode repaint + legend title; year 2025→2019 reaching the fetch; `?cut=` opening ResultPanel = commune panel). **Geolocation is evidenced nowhere.** See below. |
| 5 | Changes confined to `MapTopbar.tsx` + sibling controls; Opus review verifies the three Leaflet layer files untouched and no declarative react-leaflet component introduced; map filters and news facets share vocabulary via common data without a code dependency between the map island and the news pages | **PASS** | Protected files: my own `git diff` against `3b45ca44` returns **empty** for all three layer files and `score.mjs`; gate assertions 3 and 2 re-assert it SHA-anchored. No declarative react-leaflet: gate assertions 10/11 (`<GeoJSON`, `<Marker`, `react-leaflet` import absent from all of `site/src`; `react-leaflet` absent from dependencies) — I re-ran and confirmed. Confinement: the diff is 8 map files + 5 new `src/lib`/`src/config` files; `MapIsland.tsx` is touched in exactly **three hunks** (import, the `?region=` block at ~:231, the mode-toggle removal at ~:456), which is precisely the bounded edit **F-47 authorized in advance and in writing**, before research began — a scope decision recorded ahead of the work, not a rescope discovered at close. MAPSH-07: see the requirement row. |

**Score: 4/5 fully verified, 1 PARTIAL, 0 FAILED.**

## The three adversarial questions, answered directly

### (1) Is criterion 4's regression list actually evidenced — geolocation in particular? **No. Geolocation is not.**

Your suspicion is correct and I could not resolve it in the artifacts. `30-CLOSE.md` §4 is titled *"every
control still drives the state it drove before"* and contains nine rows: news toggle, crime type, mode,
year, mutual exclusion, and four deep-link rows. There is no locate row. §6b and §6c re-measure coverage,
c4, the summary and the sheet — they add no geolocation assertion either. `30-REREVIEW.md` does not raise
it. No vitest test touches it. **Nothing in this phase, at any stage, exercised the locate control.**

What I *can* establish statically, and did:

- `UserLocationMarker.ts` and `SearchBox.tsx` are **byte-identical** to `3b45ca44` (`git diff` empty).
- The chain is intact and I read every link: `MapIsland.tsx:37` imports `locate`; `:453-458` passes an
  `onLocate` closure calling `locate(map, featuresRef.current, userRef, selectCommune, setToast, lang)`;
  `MapTopbar.tsx:22/37/48` declares and forwards `onLocate`; `SearchBox.tsx:80` binds it to
  `.locate-btn-visible`'s `onClick`.
- The only phase change to that control is cosmetic: `.locate-btn-visible` 32px → **44×44** (`map.css:508-520`),
  which is the F-51-mandated fix, not a behavioural edit.

So the probability the feature is broken is low. But `MapTopbar.tsx` was **rewritten in this phase** and
`onLocate` is a *new* prop on it — this is exactly the class of pass-through that a refactor drops
silently, and it is exactly why the criterion names geolocation. "The implementation file is untouched"
is not the same claim as "the control still fires". Criterion 4 says a regression pass *confirms* it; no
such confirmation exists. **PARTIAL**, closable by one click in a foreground tab.

### (2) Is criterion 3 honestly met, given c4 FAILs at ≥481 under F-58 and sub-44px targets remain? **Yes — and unusually honestly, but the honesty is undergated.**

I pushed hard on this and came out on the phase's side, with one durability warning.

- **The residual sub-44px targets are genuinely out of scope, and the scoping was decided in advance.**
  F-51 was written *before* the close, enumerates the residue by name (skip link, site title, locale
  links, header/footer nav, Leaflet's attribution anchors), and sets a falsifiable bar: zero elements
  inside `.map-topbar`/`.legend`/`.zoom-ctl` or carrying `data-role`, and a strict subset of the baseline
  list. Both MAPSH-03 and criterion 3 say **"all map controls"** — the site header is not a map control.
  This is a pre-registered scope statement, not a close-time rescope, and the measured result meets it at
  every width. Chasing header/footer targets on a live production site would be scope creep on a phase
  already flagged regression-risk. I accept it.
- **c4's FAIL at ≥481 is credibly an instrument false positive, not a trap.** The chain holds: the review's
  H-02 found `role="radiogroup"` shipped without roving tabindex — an announced ARIA contract that wasn't
  honoured, i.e. a real defect. Fixing it correctly *necessarily* produces `tabindex="-1"` on unselected
  radios, and `score.mjs:131-137` reads any negative tabindex as a trap signal. The nine flagged elements
  are radios inside **closed** `<details>`, invisible and inert. The alternative — reverting a genuine
  accessibility fix to protect a metric — would be worse than either editing the instrument or recording
  the false positive. Crucially, **`score.mjs` was not edited** (I verified byte-identity myself, and the
  gate pins it), the re-review independently confirmed the arrow-key handler adds no `keyInterceptors`
  signal, and the substitute evidence is the concrete Tab walk F-49 had *already* prescribed in advance.
  The phase also corrected itself in the opposite direction earlier (F-55 overturned its own F-53(a) when
  measurement disagreed), which is the behaviour of an author who is measuring rather than narrating.
- **The warning.** The Tab walk is the entire load-bearing evidence for "no focus traps" at three of five
  widths, and it is encoded in **nothing**. `phase30-gate.mjs`'s 12 assertions do not cover focus order;
  vitest does not; `score.mjs` now reports FAIL there by design. A future change that genuinely breaks the
  focus order would redden no gate and would look identical to today's accepted state. That is the same
  hole N-2 identified for the `?cut=` precedence rule — and that one *was* closed with a source-level gate
  assertion. The precedent exists and was not applied here. Worth a Phase 31/32 item, not a blocker.

Verdict: criterion 3 **PASS**, with the caveat stated in the frontmatter that it rests on browser
measurement I cannot reproduce and on no durable gate.

### (3) Was MAPSH-07 delivered, or inherited? **Inherited and preserved — the negative requirement holds, and the phase did add a real consolidation.**

Checked directly, both directions:

- **No import edge exists.** `grep` for `news`/`facet` across every file in `site/src/components/map/`
  returns nothing but `./NewsToggle` (a map-local component) and `../../config/i18n`. In the other
  direction, the only `components/map` importers are the six map *page* templates importing `MapIsland`;
  `src/pages/news.astro` and `src/pages/es/noticias.astro` import no map component. The requirement's
  operative clause — *"without creating a code dependency between the map island and the news pages"* — is
  **true**, and I verified it rather than inferring it.
- **Shared vocabulary via `familyDefs.ts` is true, but it was already true.** `git show 3b45ca44:.../FiltersRow.tsx`
  line 18 already read `import { FAMILY_DEFS_EN, FAMILY_DEFS_ES } from '../../lib/familyDefs'` and used it
  at line 90. Today `mapFilterDefs.ts:12` imports and re-exports the same symbols and `FilterFields.tsx:87`
  consumes them at the identical call shape. So the property was **inherited from the pre-change tree, not
  created by this phase.**
- **What the phase did add is nonetheless real, not cosmetic:** `mapFilterDefs.ts` is a new single source of
  truth (`CHIP_DEFS`, `AVAILABLE_YEARS`, `MODE_LABELS`) that four new components import instead of
  re-deriving per component — and M-04 in the review was exactly the bug that arises without it (mode
  labels drifting from the state summary). `newsFacets.ts:150` independently derives families from observed
  data (*"never familyDefs.ts keys"*), which is why the facets validator reports 8 families against CEAD's 7
  — the news-only `sexuales` family. The two surfaces share vocabulary through data and diverge where the
  data legitimately diverges.

Verdict: **PASS**, correctly, but the requirement was satisfied by *not breaking* an existing property
during a rewrite that easily could have broken it. Framing it as new delivery would overstate it, and no
phase artifact does.

## Requirements Coverage

| Req | Verdict | Evidence |
|---|---|---|
| MAPSH-01 | **PASS** | `NewsToggle.tsx` standalone + labeled + `aria-pressed`, in the shipped bundle; old `.ev-chip` surface absent from `dist/` (my grep + gate 5). On-screen position at five widths rests on CLOSE §1. |
| MAPSH-02 | **PASS** (one recorded spec deviation at ≤480) | Native `<details>` ×3 + native `<dialog>`+`showModal()` + FAB; zero new deps verified by gate assertion 4 against the base SHA (package.json/lock byte-unchanged). `:modal` proof is browser-only. |
| MAPSH-03 | **PASS** (evidence-dependent, undergated) | Roving tabindex + arrow/Home/End read in `FilterFields.tsx`; 44px rules in `map.css`; z-index ladder verified by gate. No-focus-trap rests solely on the CLOSE Tab walk; residue outside the map scoped by F-51. |
| MAPSH-04 | **PASS** | `regionParam.ts` pure resolver + `shouldApplyRegionFocus`; 74 lines of vitest in the green 51; gate assertion 12 pins the precedence guard (proven falsifiable). Graceful degradation with zero console errors rests on CLOSE §4. |
| MAPSH-05 | **PASS** | Protected diff **empty** — re-run by me, not read. No declarative react-leaflet anywhere in `site/src`; `react-leaflet` not a dependency. `MapIsland.tsx` edit is 3 hunks within F-47's pre-authorized bound. |
| MAPSH-06 | **PARTIAL** | `?cut=`, year, family, mode, commune panel, incident pins all evidenced (CLOSE §4). **Geolocation unevidenced by any measurement**; static chain intact (see adversarial Q1). |
| MAPSH-07 | **PASS** (inherited + preserved) | No import edge either direction (verified by grep); `familyDefs.ts` shared through `mapFilterDefs.ts`; property pre-existed in the base `FiltersRow.tsx`. |

## Anti-patterns and residue

| Item | Severity | Note |
|---|---|---|
| L-03 — `AVAILABLE_YEARS` offers 2026 with no payload; selecting it shows the "no data" toast | ℹ️ Info | Pre-existing behaviour of the ported year list, now pinned by a test. Carried deliberately (fix cycles capped at 2). Flagged for Phase 31. |
| L-04 — gate assertion 1 compares astro-check error *locations*, so a same-location regression or a new warning would not redden it | ⚠️ Warning | Deliberate and reasoned (the count-based alternative invites baseline-bumping). I confirmed the 4 errors are all at `ComparatorPairsLinks.astro:28`, unchanged. |
| Legend numeric bands computed from overall commune rate, not the selected family | ℹ️ Info | Pre-existing (`MapIsland.tsx:201,290`), unchanged by this phase, correctly routed to Phase 31 rather than silently fixed. |
| No gate encodes the Tab-walk focus order (the sole evidence for criterion 3's no-trap clause at ≥481) | ⚠️ Warning | The N-2 precedent (source-level gate assertion for a browser-only rule) exists and was not applied here. |
| No debt markers (`TBD`/`FIXME`/`XXX`) found in the phase's changed files | — | Clean. |

## Gaps Summary

The phase substantially achieved its goal. The news toggle is a real standalone labeled control, the old
buried `.filters-row` surface is genuinely deleted from the shipped output, the filter panel is native
`<details>`/`<dialog>` with zero new dependencies, `?region=` is implemented with a tested pure resolver
and a gated precedence rule, and the three protected Leaflet layer files plus `score.mjs` are byte-identical
to the base SHA — which I verified by running the diff myself, not by reading a claim. Every suite figure
you specified reproduced exactly: vitest 51, 16/16 validators, gate 12/12, astro check 4 errors / 0 warnings
all at `ComparatorPairsLinks.astro:28`, pytest 344/1/1.

The phase's evidence discipline is above average for this repo: the instrument was not edited, coverage was
settled by rebuilding the pre-change tree and measuring both sides through the same harness, two
measurement artifacts were recorded as artifacts rather than laundered into passes, three fix-cycle
regressions were caught only because the whole rubric was re-run instead of the fixer being believed, one
prior decision (F-53a) was overturned by its own author on measurement, and the ≤480 spec deviation is
stated as a deviation.

**The one real gap is geolocation.** Criterion 4 and MAPSH-06 both name it explicitly in the regression
list, and it was never exercised — not in the browser pass, not in the re-review, not in a test. The
implementation file is untouched and I traced the full prop chain by hand, so this is very likely fine;
but the criterion asserts a confirmation that does not exist, and the pass-through it depends on is new
code in a file this phase rewrote. One foreground-tab click closes it.

Not a blocker. Phase 30 should not be reopened for this — it should be closed after that single click, or
the item carried explicitly into Phase 31's opening checks.

---

_Verified: 2026-07-30_
_Verifier: Claude (gsd-verifier)_

---

## Orchestrator addendum (Fable, 2026-07-30, after the verification run)

Two of this report's three findings are addressed; one is a timing artifact.

**1. Geolocation — the PARTIAL is stale, and the verifier was right that it was missing when it looked.**
I noticed the same gap while the verification was running and closed it in the browser before reading
this report; the evidence row landed in `30-CLOSE.md` §4 after this agent had already read that file.
Measured against the real build, in a foreground tab: the locate button is **44×44** with
`aria-label="Mostrar mi ubicación"`; clicking it calls `navigator.geolocation.getCurrentPosition`
**with a real error callback**; and a simulated `PERMISSION_DENIED` surfaces the toast
**"No se pudo obtener tu ubicación"** instead of failing silently or throwing. That is exactly the
"one click in a foreground tab" this report asked for, so criterion 4's regression list is now
complete. The underlying observation was correct and worth having: the `onLocate` prop is new on a
component this phase rewrote, which is the pass-through a refactor drops silently.

**2. Criterion 3's durability gap — accepted and CLOSED, applying the N-2 precedent as suggested.**
`phase30-gate.mjs` gains **assertion 9**: no map component may register a document-scoped keyboard
listener (the invariant that keeps `score.mjs`'s criterion 4 measurable at all, and the reason the
rail's Escape handling is a container-scoped React `onKeyDown`), and `FilterFields.tsx` must keep both
the roving tabindex and arrow/Home/End navigation. **Proven falsifiable in both directions**: adding a
`document.addEventListener('keydown', …)` and stripping `ArrowRight` makes the gate exit 1 naming both,
and the restored tree exits 0. The Tab walk is no longer the sole evidence — the property it observed
is now encoded.

**3. MAPSH-07 "inherited, not delivered" — agreed, and the report's framing is the correct one.**
The negative clause (no code edge in either direction) predates this phase and was preserved; the
phase's own contribution is `mapFilterDefs.ts` as a single source of truth, which is not cosmetic —
review finding M-04 was precisely the label-drift bug its absence had already caused.

**On criterion 5's confinement**: recording agreement rather than leaving it implicit — the
`MapIsland.tsx` edit and the new `src/lib`/`src/config` files are exactly the bound **F-47 authorized
in writing before research began**, for the reason the design spec §9a demanded a decision rather
than a mid-implementation discovery. It is a pre-registered scope decision, not a close-time rescope.

Final gate after this addendum: `phase30-gate.mjs` **14/14 PASS**, vitest **51**, **16/16 validators**,
pytest **344 / 1 / 1**, astro check **4 errors / 0 warnings** at the baseline location, protected
Leaflet files and `score.mjs` byte-identical.
