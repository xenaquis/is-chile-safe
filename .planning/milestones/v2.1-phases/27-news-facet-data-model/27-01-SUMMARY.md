---
phase: 27-news-facet-data-model
plan: 01
subsystem: news-facets
tags: [astro, build-time, facets, validator, vitest]
requires: []
provides:
  - site/src/lib/newsFacets.ts (computeNewsFacets)
  - site/scripts/validate/facets.mjs (validator #16)
affects:
  - site/src/pages/news.astro (Plan 27-02 will wire it in)
  - site/src/pages/es/noticias.astro (Plan 27-02 will wire it in)
tech-stack:
  added: []
  patterns:
    - "UTC/string-only date arithmetic anchored to newest incident date (never build wall-clock)"
    - "facet vocabulary derived from observed data, never from label-map keys"
    - "validator independently re-derives assertions rather than importing the module under test"
key-files:
  created:
    - site/src/lib/newsFacets.ts
    - site/src/lib/newsFacets.test.ts
    - site/scripts/validate/facets.mjs
  modified:
    - site/scripts/validate/all.mjs
    - site/package.json
decisions:
  - "Assertion 3 (live FAMILY_KEYS parse) necessarily also catches the homicidios-leak fixture before assertion 4 gets a chance — both are real, overlapping guards; documented as a deviation below, not a defect"
metrics:
  duration: "~45m"
  completed: "2026-07-30"
---

# Phase 27 Plan 01: News Facet Data Model Task 1
# News Facet Data Model — Task 1 (newsFacets.ts) + Task 2 (facets.mjs) Summary

One-liner: Build-time `computeNewsFacets()` module with UTC-anchored window arithmetic plus an independent 10-assertion `facets.mjs` validator (#16) that cross-checks it against raw JSON without importing it.

## What shipped

**Task 1 — `site/src/lib/newsFacets.ts` + `site/src/lib/newsFacets.test.ts` + `site/package.json`:**
- `computeNewsFacets(incidents, index, archiveDir?)` returning `{ byFamily, byRegion, byWindow, byMonth, facetKeys }`.
- `byFamily` derived from `new Set(incidents.map(i => i.family))` — never `familyDefs.ts` label-map keys (excludes phantom `homicidios`).
- `byRegion` resolves `region_id` via `data/cead/meta/index.json` (no CUT-length re-derivation in TS), `String(cut)` coercion at every lookup, sorted ascending by `Number(regionId)`.
- `byWindow`/`facetKeys` use UTC/string-only arithmetic anchored to the newest incident's date (`Date.parse(newestDate + 'T00:00:00Z')`, `lower(days)` helper) — no local-time `Date` construction, no locale formatting.
- `byMonth` is the union of archive months (`readdirSync` + per-file `existsSync`/try-catch) and months observed in `incidents`, tagged `source: 'archive'|'current'|'both'`.
- Module Published Contract (F-20) comment block written verbatim at the top of the file.
- `newsFacets.test.ts` implements all 8 behavior cases (7 numbered + 4b) as real vitest assertions, including the TZ-determinism test (Test 8, in-process `process.env.TZ` toggle — works because the implementation only uses TZ-independent primitives).
- `"test": "vitest run"` added to `site/package.json` scripts.

**Task 2 — `site/scripts/validate/facets.mjs` + `site/scripts/validate/all.mjs`:**
- 10 independent assertions against raw JSON (never imports `newsFacets.ts`): family-count sum integrity, CUT→region_id resolution + range check, live-parsed `FAMILY_KEYS` from `pipeline/shared/schema.py` (hard-fails if not exactly 7), `homicidios`-absence, `sexuales`-presence, 346-commune CUT-length cross-check against `region_id` (asserts exactly 16 distinct values), `byMonth` completeness (current.json months ⊆ archive∪current union), window monotonic-containment sanity, TZ=UTC vs TZ=America/Santiago determinism via two `spawnSync` child processes, and a recursive stray-`facet`-artifact walk under `site/public/`.
- Accepts `process.argv[2] || process.env.FACETS_CURRENT_JSON` override so the negative-path demo never touches `data/`.
- Registered in `all.mjs`'s `VALIDATORS` array as entry 16; header doc-comment corrected from "12" to "16" with a full entry-16 description line.

## Per-task verification output (pasted verbatim)

### Task 1

Export/type-import grep (acceptance criteria):
```
$ grep -E "^export (function|interface) " site/src/lib/newsFacets.ts
export interface IncidentLike {
export interface FacetBucket {
export interface WindowFacet {
export interface MonthBucket {
export interface FacetKeyEntry {
export interface NewsFacetIndex {
export function computeNewsFacets(
$ grep -Ec "^export (function|interface) " site/src/lib/newsFacets.ts
7
$ grep -c "import type { CommuneMeta" site/src/lib/newsFacets.ts
1
```

`npm test`:
```
 Test Files  2 passed (2)
      Tests  16 passed (16)
   Start at  02:22:49
   Duration  529ms
```
(7 tests from pre-existing `formatNumber.test.ts` + 9 from `newsFacets.test.ts` [8 numbered cases + 4b] = 16.)

`npx astro check` delta:
```
Result (128 files):
- 4 errors
- 0 warnings
- 36 hints
```
All 4 errors confirmed to be the pre-existing `ts(7031)` in `src/components/ComparatorPairsLinks.astro:28`:
```
$ grep "ComparatorPairsLinks" checkout.txt
src/components/ComparatorPairsLinks.astro:28:38 - error ts(7031): Binding element 'nameB' implicitly has an 'any' type.
src/components/ComparatorPairsLinks.astro:28:31 - error ts(7031): Binding element 'nameA' implicitly has an 'any' type.
src/components/ComparatorPairsLinks.astro:28:25 - error ts(7031): Binding element 'cutB' implicitly has an 'any' type.
src/components/ComparatorPairsLinks.astro:28:19 - error ts(7031): Binding element 'cutA' implicitly has an 'any' type.
```
Zero hits for `newsFacets` in the check output (`grep -i "newsFacets" checkout.txt` → `NO_NEWSFACETS_HITS`).

### Task 2

```
$ node site/scripts/validate/facets.mjs && echo GREEN
PASS facets: 1215 incidents, 8 families observed, 346 communes cross-checked, 3 months in byMonth union, window(today=11,7d=297,30d=1215), TZ-determinism verified
GREEN
```

Registration checks:
```
$ grep -c "'facets.mjs'" site/scripts/validate/all.mjs
1
$ grep -c "12 validation scripts" site/scripts/validate/all.mjs
0
$ grep -n "16 validation scripts\|16\.  facets" site/scripts/validate/all.mjs
2: * all.mjs — Aggregate validator: run all 16 validation scripts in sequence.
20: *  16.  facets.mjs            — news facet count integrity (...)
```

`npx astro check` re-run after adding `facets.mjs` (tsconfig includes `scripts/**/*.mjs`):
```
Result (128 files):
- 4 errors
- 0 warnings
- 36 hints
```
Zero hits for `facets.mjs` in the check output.

Negative-path demonstration (built entirely in `os.tmpdir()`, never under `data/` or the repo):
```
$ node site/scripts/validate/facets.mjs "<tmpdir>/bad-cut.json"
FAIL facets: assertion 2 — incident cut "99999" does not resolve to a region_id in index.json
EXIT_BADCUT:1

$ node site/scripts/validate/facets.mjs "<tmpdir>/bad-family.json"
FAIL facets: assertion 3 — observed family "homicidios" is not a member of VALID_FAMILIES (vida, robos_violentos, vif, drogas, armas, propiedad, incivilidades, sexuales)
EXIT_BADFAMILY:1
```
Both fixtures and the temp directory were deleted immediately after the run (`rm -rf <tmpdir>`).

`git status --porcelain data/` after the negative-path demo:
```
$ git status --porcelain data/
(empty output)
DATA_CLEAN_CHECK_DONE
```
Confirmed `data/` untouched.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `newsFacets.ts` doc comment false-positived assertion 9's TZ-sensitivity grep**
- **Found during:** Task 2, first run of `facets.mjs` against real data.
- **Issue:** The Module Published Contract prose in `newsFacets.ts` literally contained the string `toLocaleDateString` (as part of a sentence describing what NOT to use), which is exactly the pattern `facets.mjs` assertion 9 scans `newsFacets.ts` for. The validator correctly flagged the literal string match, exiting 1 even though no TZ-sensitive *code* exists in the file.
- **Fix:** Reworded the comment to describe the constraint without using the literal banned identifier strings (`toLocaleDateString`, `getMonth(`) — e.g. "never locale-formatted date strings" instead of naming the method.
- **Files modified:** `site/src/lib/newsFacets.ts` (comment only, no behavior change).
- **Commit:** `6a8fb25` (bundled with Task 2's commit since it was required for facets.mjs to pass; `npm test` re-run afterward confirmed all 16 tests still pass).

**2. [Documented, not a bug] Assertion 3 pre-empts assertion 4 for the `homicidios` negative-path fixture**
- **Found during:** Task 2 negative-path demonstration.
- **Observation:** The plan's negative-path demo expects to "prove assertion 2 and assertion 4 both actually fire." In practice, assertion 3 (live `VALID_FAMILIES` containment check, which by construction excludes `homicidios`) fires first and exits before assertion 4 (the dedicated `homicidios`-absence check) is ever reached, because both assertions test overlapping conditions for this exact fixture.
- **Why not fixed:** Reordering assertions or weakening assertion 3 to skip `homicidios` specifically would violate the "never weaken a validator" hard rule and the stated purpose of assertion 3 (catching any family value outside the live 8-value set, `homicidios` included by design). The demonstration still proves the validator is not a no-op — it correctly rejects the injected phantom-family incident with a clear `FAIL facets:` message — which is the load-bearing claim H1 was written to protect against.
- **No files modified for this item** — informational only.

**No other deviations.** Plan executed as written for all other tasks/assertions.

## Known Stubs

None — this plan ships a data module and a validator, no UI, no rendering.

## Threat Flags

None — no new network endpoints, auth paths, or trust-boundary changes introduced. `facets.mjs` remains read-only against `data/` (no `writeFileSync` call anywhere in the file) and its negative-path demo writes only to `os.tmpdir()`.

## Self-Check

```
$ [ -f "site/src/lib/newsFacets.ts" ] && echo FOUND || echo MISSING
FOUND
$ [ -f "site/src/lib/newsFacets.test.ts" ] && echo FOUND || echo MISSING
FOUND
$ [ -f "site/scripts/validate/facets.mjs" ] && echo FOUND || echo MISSING
FOUND
$ git log --oneline --all | grep -q "4fb0adb" && echo FOUND || echo MISSING
FOUND
$ git log --oneline --all | grep -q "6a8fb25" && echo FOUND || echo MISSING
FOUND
```

## Self-Check: PASSED
