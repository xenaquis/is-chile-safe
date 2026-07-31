---
phase: 30-map-control-shell-rework
rereviewed: 2026-07-30
reviewer: Claude Opus (independent re-review, execution + mutation stance)
diff_base: 3b45ca4431fdce08b27cd10efd63595218a843d5
head: 46feccd
method: every verdict below is backed by a command that was run, a mutation that was applied and reverted, or an explicit "browser-only" caveat
original_findings: 13
verdicts: { closed: 8, partial: 4, open: 1 }
new_findings: { critical: 0, high: 0, medium: 3, low: 5 }
tree_state: clean (git status --porcelain empty; dist/ rebuilt from unmutated source after mutation testing)
---

# Phase 30 — Independent Re-Review (verification by execution)

## 0. Suite, run end-to-end from a clean tree

| Check | Command | Result | Expected | Verdict |
|---|---|---|---|---|
| build | `cd site && npm run build` | exit 0, 834 pages in 22.8 s | — | ✔ |
| vitest | `npm test` | **51 passed / 5 files** | 51 | ✔ |
| validators | `npm run validate` | **16/16 passed** | 16/16 | ✔ |
| astro check | `npx astro check` | **4 errors / 0 warnings / 44 hints**, all 4 at `ComparatorPairsLinks.astro:28` | 4 @ that location | ✔ |
| phase30 gate | `node scripts/phase30-gate.mjs` | **11/11 PASS, exit 0** | pass | ✔ |
| pytest | `python -m pytest -q` (repo root) | **344 passed, 1 skipped, 1 xfailed** | 344/1/1 | ✔ |

Every number the brief pre-registered was met exactly. No drift.

## 0b. Protected files (task 8) — verified independently of the gate

```
git diff --exit-code 3b45ca443… HEAD -- \
  site/src/components/map/ChoroplethLayer.ts \
  site/src/components/map/IncidentPinLayer.ts \
  site/src/components/map/LowZoomDotLayer.ts \
  .planning/sketches/029-map-controls/score.mjs
→ exit 0, no output
```
**Byte-identical. CONFIRMED.** `score.mjs` was not edited — F-49/F-58 hold.

---

## 1. The 13 original findings

### H-01 — `--map-topbar-h` hardcoded, badge lands inside the topbar → **CLOSED**

Verified in the **built** CSS (`dist/_astro/MapIsland.CfQlhWhx.css`, whitespace-stripped), not just source:
```
--map-topbar-h:143px            (base)
--map-topbar-h:117px            (@media min-width:1024px)
.partial-year-badge{…top:calc(var(--map-topbar-h,96px)+8px)…}
```
Band arithmetic against the built rules (`.map-topbar` pad 8/8 + gap 8 + border 1; `.map-topbar-row1{flex-wrap:wrap}`; `.entry-state-summary{flex-basis:100%}` → `auto` at ≥1024; `.entry-points-rail{display:none}` and row1 `flex-direction:column;gap:6px` at ≤480):

| Band | topbar | badge `top` | clearance |
|---|---|---|---|
| ≥1024 | 8+44+8+44+8+1 = **113** | 125 | +12 ✔ |
| 481–1023 | 8+(44+8+18)+8+44+8+1 = **139** | 151 | +12 ✔ |
| ≤480 | 8+(44+6+44)+8+1 = **111** | 151 | +40 ✔ |

The orchestrator's inversion (tall base, short override at `min-width:1024`) is the correct direction and removes the 1023 px hole the `max-width:1023px` form had. No band overlaps. Note the ≤480 badge now sits ~32 px lower than necessary (see N-8).

**Browser-only residue:** the 18 px summary row height and the 44 px control heights are computed-style assumptions. Assert in a real browser at 320/375/481/639/1024/1296: `badge.getBoundingClientRect().top >= topbar.getBoundingClientRect().bottom`.

### H-02 — radiogroup shipped without roving tabindex / arrow keys → **CLOSED**

Executed: rendered the shipped `FamilyField` / `ModeField` through `react-dom/server` in vitest (temp file, deleted; tree clean).

```
FAMILY null        ti=[0,-1,-1,-1,-1,-1,-1,-1,-1]  radios=9 radiogroup=true checked=1
FAMILY homicidios  ti=[-1,-1,-1,-1,-1,-1,-1,-1,0]  radios=9 radiogroup=true checked=1
FAMILY vif         ti=[-1,-1,-1,-1,-1,0,-1,-1,-1]  radios=9 radiogroup=true checked=1
MODE composite     ti=[0,-1]  aria-label=Modo  buttons="Índice|Por delito"
MODE family        ti=[-1,0]  aria-label=Modo  buttons="Índice|Por delito"
ARITH n=9  next(last)=0  prev(0)=8  Home=0  End=8
```

Answering each sub-question of the brief:

- **Does arrow navigation work, wrap, move focus, and select?** The handler (`FilterFields.tsx:55-77`, `:130-152`) computes the next index with `(i+1)%n` / `(i-1+n)%n` — wrap verified by execution above — then calls `onFamilyChange(next.key, next.familyIndex)` **key-first** (selection) and `btnRefs.current[nextIndex]?.focus()` (focus). Both. ✔
- **Does it `preventDefault` on anything but arrows/Home/End?** No. `FilterFields.tsx:69-71` and `:144-146` `return` **before** the single `e.preventDefault()` at `:73` / `:148` for every other key. Tab, Shift+Tab, Enter, Space are untouched. ✔
- **Can Tab still leave each radiogroup?** Yes — exactly one `tabIndex=0` per group in every reachable state (executed above), no Tab interception, and the rail's own `onKeyDown` (`EntryPointsRail.tsx:91-103`) handles only Escape with `stopPropagation()` and no `preventDefault`. ✔
- **Is the SAME implementation in both surfaces?** Yes, and it cannot drift: `EntryPointsRail.tsx:14` and `FilterSheet.tsx:28` both `import { YearField, FamilyField, ModeField } from './FilterFields'` — one component, two mount points. ✔

**F-49/F-55 side-check, executed:** `dist/es/mapa/index.html` ships 3 scripts, **all with inline text, `externalScriptCount` = 0**, and none of `keydown`/`keyup`/`preventDefault` appears in that inline text (the island lives in a dynamically-imported chunk). So the arrow handler does **not** add a `keyInterceptors` signal to c4. F-58's account is complete: `negativeTabindexCount: 9` is c4's only new signal, and it is the WAI-ARIA-mandated pattern. Accepting it (F-58) rather than reverting the a11y fix is the right call.

### M-01 — state summary disappears at ≤480 → **PARTIAL** (this is the fix cycle's central trade)

The summary is now extracted to `MapTopbar` row 1 and, at ≤480, made **visually hidden** (`map.css:79-89`; confirmed in built CSS: `position:absolute;width:1px;height:1px;…clip:rect(0 0 0 0)`), not `display:none`. So:

- The `aria-live="polite"` announcement contract of spec §6 **is** restored at ≤480. ✔
- Spec §2 item 4 — *"keeps the active selection legible without opening any panel"* — **is still not met for sighted users at 320/375**. They still cannot see the active year or crime family without opening the FAB sheet, which is the literal defect M-01 reported.

This is deliberate and documented (`map.css:71-78`, `30-CLOSE.md` §6b): the visible summary cost 21.7 → 27.4 % coverage at 375, breaching F-50's 22.7 % ceiling and STRESS.md's frozen ≤25 %. Given F-50's "if a ceiling is breached the disposition is a FIX, never reinterpretation", hiding the pixels is the only move that respects the frozen threshold. **Verdict PARTIAL, correctly traded and correctly recorded** — but it should be recorded as a *known spec deviation at ≤480*, not as M-01 being closed. Recommend a line in `30-CLOSE.md` §7 and an F-decision, since §6b currently frames it as a regression fix rather than a spec §2 deviation.

### M-02 — `aria-expanded` written both by JSX and imperatively → **CLOSED**

`FilterSheet.tsx:104-113`: the FAB's JSX carries `data-role`, `className`, `aria-label`, `aria-haspopup` and **no `aria-expanded`**. There is now exactly one writer (the three `setAttribute` sites at `:62,:77,:82`). The React-reconciler dependency the finding described is gone. The fix chose "remove the JSX writer" over the review's "lift to state"; both eliminate the defect, and the chosen one avoids a re-render of the dialog subtree on every open/close.

### M-03 — bottom sheet cannot be backdrop-dismissed, comment claims it can → **PARTIAL** (fixed, but introduced N-1)

Light dismiss added (`FilterSheet.tsx:119-127`) and the header comment corrected (`:12-13` now says native `<dialog>` does **not** do this without `closedby`). The dismissal defect is closed. The implementation, however, opened a new accidental-dismiss zone — see **N-1 (MEDIUM)**.

### M-04 — mode labels rewritten and contradicting the state summary → **CLOSED**

Executed render above: `ModeField` emits **`Índice` / `Por delito`** (base-SHA labels restored) and its `aria-label` is **`Modo`**, sourced from `strings.map_entry_mode` (`FilterFields.tsx:155`). Both `ModeField` and `EntryPointsRail.modeLabel()`/`StateSummary` read the single `MODE_LABELS` constant (`mapFilterDefs.ts:40-43`, consumed at `EntryPointsRail.tsx:13,42`). Drift is now structurally impossible.

### M-05 — gate assertion 6 could not fail → **CLOSED** (proven by mutation, both directions)

Mutated `map.css`, rebuilt, re-ran the gate:

| Mutation | Old gate | New gate |
|---|---|---|
| delete `z-index:800` from `.news-toggle` base rule | would PASS (`.map-topbar`/`.partial-year-badge` also emit `z-index:800`) | **FAIL** — `.news-toggle{ missing z-index:800` |
| add `z-index:5` to `.filter-sheet` | no such check | **FAIL** — `.filter-sheet{ contains a z-index declaration` |
| change `.legend` 750 → 700 | partially caught | **FAIL** on both the ladder check and `.legend z-index:700 absent` |

All reverted; clean rebuild returns 11/11 PASS. The value-per-selector rewrite works. Residual weakness: **N-7 (LOW)**.

### M-06 — gate assertions 5 and 7 weaker than the constraints → **CLOSED**

- **a5** kept as a substring smoke test and explicitly marked *necessary-not-sufficient* in the gate header (`phase30-gate.mjs:244-250`), with the real proof (`dialog.matches(':modal') === true`) pointed at `30-CLOSE.md` §3 where it was actually measured. This is precisely the disposition the review prescribed.
- **a7** widened to `site/src` with `.tsx/.ts/.jsx/.js`, plus a `package.json` dependency scan (`:395-449`). **Proven by mutation:** inserting `// <GeoJSON legacy` into `site/src/lib/regionParam.ts` — a file the old gate never read — produced `FAIL [react-leaflet declarative usage absent]: …/src/lib/regionParam.ts: <GeoJSON`. Reverted.

### M-07 — `?region=` exact-string match rejects padded forms → **PARTIAL** (resolver CLOSED, call site untested)

Ran the **real** `resolveRegionFocus` through vitest against a fixture index. Every input in the brief, plus extras:

| input | result | throws |
|---|---|---|
| `?region=05` | resolves (region 5 CUTs) | no |
| `?region=13 ` / `?region=%2013%20` / `?region=+13+` | resolves (region 13) | no |
| `?region=0` | `null` (correct — not a Chilean region) | no |
| `?region=` | `null` | no |
| `?region=abc` | `null` | no |
| `?region=00013` | resolves (region 13) | no |
| `?region=13.0` | `null` (correct — malformed) | no |
| `?region=13&region=5` | resolves 13 (first value; single-value semantics per F-48) | no |

Additionally asserted: for every valid id in `{1,5,13,16}`, all three of `N`, `0N`, `00N` resolve non-null. **No input throws; no valid Chilean region id is rejected.** Resolver half CLOSED.

**The call-site half is not covered** — see **N-2 (MEDIUM)**.

### L-01 — news toggle `aria-label` not the spec string → **CLOSED**

`i18n.ts:459` / `:692` define `map_news_toggle_aria` = `'Show recent press incidents on the map'` / `'Mostrar incidentes recientes de prensa en el mapa'` — the exact spec §6 string — and `NewsToggle.tsx:24` consumes it. WCAG 2.5.3 still satisfied: the visible short label `Noticias` is a substring of the accessible name.

### L-02 — focus return unguarded against a hidden FAB → **PARTIAL**

`focusFabIfVisible()` (`FilterSheet.tsx:69-73`) adds the `offsetParent` guard. But `.focus()` on a `display:none` element was **already** a silent no-op, so the guard changes no observable behaviour: on a widen-while-open, focus still ends up on `<body>`. The review's actual remedy — the `else` branch falling back to a rail `<summary>` — was not implemented. See **N-6 (LOW)**.

### L-03 — `AVAILABLE_YEARS` offers a year with no payload; Test 8 pins it → **OPEN**

Unchanged. `mapFilterDefs.ts:47-50` still derives from `new Date().getFullYear()` (= 2026); `ls site/public/data/cead/` stops at `map-payload-2025.json`. `mapFilterDefs.test.ts:47` still asserts `AVAILABLE_YEARS[0] === new Date().getFullYear()`, locking the defect in. The review classed the behaviour as out-of-scope **but asked that it be recorded** — it appears in neither `30-CLOSE.md` §7 nor `STATE.md` F-47..F-58.

**Fix:** add a line to `30-CLOSE.md` §7 and a Phase 31 backlog item; change Test 8 to assert `existsSync(map-payload-${AVAILABLE_YEARS[0]}.json)`, which would fail today and force the clamp.

### L-04 — gate assertion 1 ignores warnings, masked by same-location regressions → **OPEN**

The prescribed fix (also parse `- N errors` / `- N warnings` and assert `4 && 0`) was **not applied**; `phase30-gate.mjs:78-148` is unchanged in substance. Verified:

- **Falsifiable for a new location** ✔ — injecting `const __bad: number = 'not a number';` into `NewsToggle.tsx` produced `FAIL [astro-check baseline]: Unexpected error location(s) outside baseline set: NewsToggle.tsx:16`. Reverted.
- **Not falsifiable for warnings** — the gate never reads the summary lines. `npx astro check` currently reports `4 errors / 0 warnings / 44 hints`; a jump to N warnings would pass silently.
- **Not falsifiable for a new error at `ComparatorPairsLinks.astro:28`** — it is a `Set` of locations, structurally blind to multiplicity.

Not tautological, just still incomplete. Low risk, but the fix is three lines.

---

## 2. New findings introduced by the fix cycle

### N-1 (MEDIUM) — the M-03 backdrop handler also dismisses on the sheet's own 16 px padding ring

**File:** `site/src/components/map/FilterSheet.tsx:119-127`, with `site/src/components/map/map.css` `.filter-sheet{ padding:16px }` (confirmed in built CSS).

`if (e.target === dialogRef.current) close()` is the standard light-dismiss idiom, but it is only correct when the dialog has **no padding of its own**. `.filter-sheet` carries `padding:16px`, and `.filter-sheet-header`/`.filter-sheet-body` are block children inside the content box — so a 16 px ring **inside the visible sheet** (above the title, below the last field, and down both gutters for the sheet's full height) has `e.target === dialog` and closes it.

**Failure scenario:** at 375 px a user taps the left gutter beside a crime-type chip, or the strip just under the mode row — visually inside the sheet, nowhere near the dim backdrop — and the sheet closes, discarding the interaction. On a bottom sheet the bottom gutter is exactly where a thumb rests.

**Fix:** either move the padding off the dialog onto an inner wrapper —
```css
.filter-sheet { padding: 0; }
.filter-sheet > .filter-sheet-header { padding: 16px 16px 0; }
.filter-sheet > .filter-sheet-body   { padding: 0 16px 16px; }
```
— or hit-test the click against the content box instead of the target:
```tsx
onClick={(e) => {
  const d = dialogRef.current; if (!d) return;
  const r = d.getBoundingClientRect();
  const inside = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom;
  if (!inside) d.close();
}}
```
(The second form is also robust to future padding changes.)

### N-2 (MEDIUM) — `shouldApplyRegionFocus` is called but its call site has zero test coverage; deleting it keeps the suite green

**File:** `site/src/components/map/MapIsland.tsx:238`

The brief's task 5 has two halves. The first is satisfied: the helper **is** genuinely called (`MapIsland.tsx:238`, `if (shouldApplyRegionFocus(window.location.search) && idx) {`), not merely exported and unit-tested. The second is not.

**Proven by mutation:** replacing line 238 with `if (idx) {` — i.e. deleting the entire `?cut=` precedence rule — and running `npx vitest run` gives **51 passed / 51**, unchanged. Reverted.

So the M-07 fix made the *rule* testable but left the *wiring* untested, and `regionParam.test.ts:60-73` tests only the pure helper. A future refactor can silently delete the precedence guard — the exact contract `30-CLOSE.md` §4 verified in a browser (`?cut=13101&region=05` → Santiago wins) — with a fully green suite. This matters more than usual because §6b records that the earlier browser precedence test *could not have failed* (`region=05` resolved to nothing pre-fix), so the browser evidence for this rule is only one run old.

**Fix:** extract the region-focus block into a pure planner and test it:
```ts
// regionParam.ts
export function planRegionFocus(search: string, idx: CommuneIndexEntry[]): string[] | null {
  return shouldApplyRegionFocus(search) ? resolveRegionFocus(search, idx) : null;
}
```
call `planRegionFocus` from `MapIsland.tsx:238`, and add `expect(planRegionFocus('?cut=13101&region=05', idx)).toBe(null)` plus `expect(planRegionFocus('?region=05', idx)).not.toBe(null)`. Deleting the guard then fails a test.

### N-3 (MEDIUM) — dead band/summary machinery left behind in `EntryPointsRail` after the `StateSummary` extraction

**File:** `site/src/components/map/EntryPointsRail.tsx:66`, `:72-78`, `:105-116`

The orchestrator's correction moved the summary into the exported `StateSummary` component (`:212-228`), but the rail's original implementation was never removed. `band`/`setBand` (`:66`), the `resize` listener effect (`:72-78`), and `fLabelLong`/`fLabelShort`/`mLabel`/`stateSummary` (`:105-116`) are all computed and **never referenced by the returned JSX** (`:118-201`) — verified by grep: no occurrence of `stateSummary` after line 115.

**Failure scenario:** two components now register independent `resize` listeners and hold duplicate `band` state for the same breakpoints; the rail re-renders its whole `<details>` tree on every resize tick for a string it discards. More importantly, a maintainer editing `EntryPointsRail`'s per-band strings (`:110-116`) will change nothing on screen and conclude the band logic is broken — the same class of dead-surface confusion the original M-01 finding flagged in the *other* direction.

**Fix:** delete `EntryPointsRail.tsx:66`, `:72-78` and `:105-116`, and drop `Band`/`getBand` from the rail's own use (keep them for `StateSummary`). `familyLabel`/`modeLabel` stay — `StateSummary` uses them.

### N-4 (LOW) — `map.css:42-48` comment states the opposite of the rule 30 lines below it

The comment asserts *"at ≤480px … the state summary is NOT [hidden] (M-01 keeps it) … the topbar keeps its second row and measures 137px, not 111px"*. The shipped rule at `:79-89` visually-hides it, and `30-CLOSE.md` §6b records the topbar back at **111 px**. The comment documents the *reverted* intermediate state and directly contradicts the code it introduces.

**Fix:** rewrite `:42-48` to state what shipped — summary visually-hidden at ≤480, topbar 111 px, base 143 px covers the 481–1023 band and errs tall at ≤480 — and cite F-50/STRESS as the reason.

### N-5 (LOW) — an out-of-vocabulary `crimeFamily` makes the family radiogroup unreachable by Tab

**File:** `site/src/components/map/FilterFields.tsx:97`

`tabIndex={isActive ? 0 : -1}` assumes `crimeFamily` always matches a `CHIP_DEFS` key. Executed:
```
FAMILY NOT_A_KEY  ti=[-1,-1,-1,-1,-1,-1,-1,-1,-1]  radios=9 checked=0
```
All nine radios become `-1` → the group has **no tab stop at all** and no `aria-checked="true"`. Not reachable today (`MapIsland.tsx:98` initialises `crimeFamily` to `null`, which is `CHIP_DEFS[0].key`, and `onFamilyChange` only ever passes `CHIP_DEFS` keys), so this is latent, not live — but it is one `?family=` deep-link away, and `?region=`/`?cut=` show this codebase adds those.

**Fix:** mirror the handler's own fallback (`FilterFields.tsx:57-58` already does `if (currentIndex === -1) currentIndex = 0`):
```tsx
const activeIndex = Math.max(0, CHIP_DEFS.findIndex((c) => c.key === crimeFamily));
// …
tabIndex={i === activeIndex ? 0 : -1}
```

### N-6 (LOW) — L-02's `offsetParent` guard is behaviourally a no-op

**File:** `site/src/components/map/FilterSheet.tsx:69-73`

`fab.focus()` on a `display:none` element already did nothing; wrapping it in `if (fab.offsetParent !== null)` changes no outcome. The reported failure (widen-while-open → focus on `<body>`) still reproduces. The guard documents intent but does not deliver it.

**Fix:** add the fallback the review specified —
```tsx
if (fab!.offsetParent !== null) fab!.focus();
else document.querySelector<HTMLElement>('.entry-points-rail > details > summary')?.focus();
```

### N-7 (LOW) — gate a6 still passes when the pinned `z-index` exists only inside a media query, and half the forbidden check is vacuous

**File:** `site/scripts/phase30-gate.mjs:328-338`, `:301`, `:340-350`

`blockAfter` loops **all** occurrences of the selector token and sets `foundRequired` if *any* block carries the value. Spec §3 pins `z-index` "on the base rule, **not only inside the media query**" — the gate cannot tell the two apart. Measured: `.filter-fab{` occurs **3×** in the built CSS (base + two media blocks), so moving the declaration into a media block would still pass.

Separately, `rulesForbidden` includes `'#filter-sheet{'`, a token that **never appears** in `dist/_astro/*.css` (verified by scan) — that half of the check is unfalsifiable by absence. `.filter-sheet{` does occur (1×) and carries the check, so the assertion as a whole is sound.

**Fix:** capture the offset of the first `@media` in the stripped CSS and require the pinned selector's *base* occurrence (index < that offset, or not enclosed by an `@media` block) to carry the value; drop or comment the `#filter-sheet{` token.

### N-8 (LOW) — at ≤480 the partial-year badge sits ~32 px lower than the topbar requires

Base `--map-topbar-h: 143px` applies at ≤480 where the topbar measures **111 px**, so the badge renders 40 px below it instead of the ~12 px used at the other bands. This is the deliberate "err tall" direction (`map.css:26-31`) and is harmless correctness-wise, but on a 320 px phone 32 px of extra offset pushes the caveat further into the map. If it reads badly in the browser, add `@media (max-width:480px){ .map-stage{ --map-topbar-h:115px } }` — safe now that the summary is out of flow at that band, and the 1023 px hole the inversion was protecting against does not exist at this boundary.

---

## 3. Task-3 questions answered directly

- **Any band where the summary wraps to two lines (F-46 forbids it)?** **No.** `.entry-state-summary` carries `white-space:nowrap; overflow:hidden; text-overflow:ellipsis` in the built CSS at every band — the *text* can never wrap. What wraps at 481–1023 is `.map-topbar-row1` (the flex container), placing the summary on its own line; that is the intended F-52 layout, not an F-46 violation. **Browser-only:** confirm `el.scrollWidth - el.clientWidth <= 8` at 481/639/1024 so it is not silently ellipsising (which would feed `score.mjs` c2). Analytically it fits: widest ES wide-band string ≈ 230 px against ≈ 444 px available at 1024.
- **Any band where the topbar grew?** **No**, versus the pre-fix-cycle state: ≥1024 is back to 113 (the 139 px regression is fixed by row-1 placement), 481–1023 is 139 as before, ≤480 is back to 111 (the 137 px regression is fixed by visually-hiding the summary).
- **Any element now rendering as a sub-44 px target?** **No.** `.entry-state-summary` is an unhooked `<div>` and is **not** in `score.mjs:104-106`'s selector set (`a[href],button,input,select,textarea,summary,[role="button"],[data-role]`) at either its ~18 px or its 1×1 size. `.entry-points-rail` does carry `data-role`, but at ≥481 it now contains only the 44 px `<summary>` elements (so it measures ≥44 tall), and at ≤480 it is `display:none` → zero rect → filtered by the `w>0 && h>0` guard. The 296×18 rail violation §6b caught is genuinely gone.
- **Does `.entry-points-rail{display:none}` at ≤480 leave the FAB as the only rendered `[data-role="filter-entry"]`?** **Yes.** Built CSS: `@media(max-width:480px){….entry-points-rail{display:none}}` and `.filter-fab{…display:none}` with `@media(max-width:480px){.filter-fab{display:flex…}}`. The two are mutually exclusive at every width, so `score.mjs:66-73`'s "first *rendered* candidate" resolves unambiguously — FAB below 481, rail above.

## 4. What could not be settled without a browser

State these as the browser checks for 30-06, not as verdicts:

1. **H-01 badge clearance** — `badge.getBoundingClientRect().top >= topbar.getBoundingClientRect().bottom` at 320/375/481/639/1024/1296. My arithmetic says +12/+12/+40; the 18 px summary-row height is an assumption.
2. **N-1 accidental dismiss** — at 375, tap 8 px inside the sheet's left gutter and 8 px below the last field; the sheet must **not** close.
3. **H-02 live arrow behaviour** — focus a family radio, press `ArrowRight` ×9 and confirm it wraps to the first option with `aria-checked` following focus; press `Tab` and confirm focus exits the group to the next entry point.
4. **Summary ellipsis** — `scrollWidth - clientWidth <= 8` on `.entry-state-summary` at 481/639/1024/1296 for the widest family label (`Vida y convivencia`, mode `Por delito`).
5. **N-8** — visual judgement on the ≤480 badge offset.

---

## 5. Verdict

The fix cycle is materially sound: **8 of 13 findings are fully closed, 4 partial, 1 open**, and — unlike the pattern the brief warned about — the three orchestrator corrections did **not** re-break the layout. The topbar heights, the sub-44 px scan and the rail/FAB exclusivity all check out, and the coverage trade at ≤480 was made in the direction the frozen thresholds require.

The residue is concentrated in two places. **N-1** is the only finding with a live user-facing failure and should be fixed before close. **N-2** is the only finding that leaves a verified behaviour unprotected by any test, and is cheap to fix. **N-3** and **L-03/L-04** are hygiene; **N-4..N-8** are documentation and defensive hardening.

_Tree left clean: `git status --porcelain` empty; all mutations reverted with `git checkout -- site/src`; `dist/` rebuilt from unmutated source and the gate re-run to 11/11 PASS._
