---
phase: 27-news-facet-data-model
plan: 02
subsystem: news-pages
tags: [astro, build-time, facets, wiring, validators]
requires:
  - site/src/lib/newsFacets.ts (27-01)
provides:
  - site/src/pages/news.astro (computeNewsFacets consumer + #news-facets node)
  - site/src/pages/es/noticias.astro (computeNewsFacets consumer + #news-facets node)
affects:
  - Phase 28 (News Visualizer UI) — will read #news-facets projection shape as a reference contract
tech-stack:
  added: []
  patterns:
    - "inert <script type=\"application/json\" id=\"...\"> node with set:html for build-provable, non-rendering data consumption (mirrors year-i18n/year-data pattern already in commune/[slug].astro)"
key-files:
  created: []
  modified:
    - site/src/pages/news.astro
    - site/src/pages/es/noticias.astro
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - .planning/v2.1-AUTONOMOUS-DIRECTIVE.md
decisions:
  - "Cast incidents to IncidentLike[] at the computeNewsFacets() call site (Rule 1 auto-fix) — incidents' cut field is optional/undefined in the page's local type but IncidentLike requires string|number; computeNewsFacets already guards every lookup with String(inc.cut), which safely no-ops on undefined, so the cast changes zero runtime behavior"
metrics:
  duration: "~40m"
  completed: "2026-07-30"
---

# Phase 27 Plan 02: News Facet Data Model — Page Wiring + Phase Close Summary

One-liner: Wired `/news/` and `/es/noticias/` to the shared `computeNewsFacets()` module via an inert, build-provable `#news-facets` JSON node, then closed the phase on a clean 16/16 validator gate (freshness passed outright — the pre-declared F-19 environmental exclusion was not needed).

## What shipped

**Task 1 — `site/src/pages/news.astro` + `site/src/pages/es/noticias.astro`:**
- Added `import { computeNewsFacets } from '../lib/newsFacets'` (ES: `'../../lib/newsFacets'`), alongside the existing imports.
- Added `archiveDir` const (`path.resolve(process.cwd(), 'public/data/incidents/archive')`) and a `computeNewsFacets(incidents, loadIndex(), archiveDir)` call, immediately before each page's existing `jsonLd` object.
- Added a counts-only `facetsProjection` object: `{ byFamily, byRegion, byMonth, byWindow: { today, sevenDay, thirtyDay } }` — `byWindow`'s three `IncidentLike[]` arrays are reduced to `.length`s only; `facetKeys` is excluded entirely per Planning Decision 11/FM-9.
- Added one inert node per page, placed immediately before `</EditorialLayout>`: `<script type="application/json" id="news-facets" set:html={JSON.stringify(facetsProjection)}></script>` — written with an explicit open/close pair (never self-closing), per the plan's RE-REVIEW W2 constraint.
- Existing `existsSync`/try-catch current.json parsing, `monthGroups` construction, and ALL card-rendering markup (news-card/news-title/news-meta/safeUrl/JSON-LD) are byte-identical to before — confirmed by grep guards below and by the deep-equality dist check.
- **Deviation (Rule 1 — auto-fixed bug, not in original plan):** `computeNewsFacets`'s `incidents` param requires `IncidentLike[]` (`cut: string | number`), but both pages' local `incidents` array type has `cut?: string | number` (optional/possibly-undefined). This produced two new `astro check` `ts(2345)` errors after wiring — a genuine type-checker regression the plan did not anticipate. Fixed with a minimal cast at each call site: `incidents as unknown as import('../lib/newsFacets').IncidentLike[]` (ES: `'../../lib/newsFacets'`), documented inline with a comment explaining why it's runtime-safe (`computeNewsFacets`/`facets.mjs` already guard every `cut` lookup with `String(inc.cut)`, which safely no-ops on `undefined` — zero behavior change, type-checker-only fix). Verified: `astro check` returned to the 4-error `ComparatorPairsLinks.astro` baseline afterward; 16/16 validators and the EN/ES dist deep-equality check both re-confirmed green after the fix.

## Per-task verification output (pasted verbatim)

### Task 1 — acceptance criteria grep

```
$ grep -c "computeNewsFacets" site/src/pages/news.astro
2
$ grep -c "computeNewsFacets" site/src/pages/es/noticias.astro
2
$ grep -n "existsSync(dataPath)" site/src/pages/news.astro
38:if (existsSync(dataPath)) {
$ grep -c "monthGroups" site/src/pages/news.astro
4
$ grep -c 'id="news-facets"' site/src/pages/news.astro
1
$ grep -c 'id="news-facets"' site/src/pages/es/noticias.astro
1
```

### Task 1 — pre-edit baseline (Step 0, M3)

```
$ grep -o 'class="news-card"' dist/news/index.html | wc -l
1215
$ grep -o 'class="news-card"' dist/es/noticias/index.html | wc -l
1215
```

### Task 1 — falsifiable chained verify (post-wiring, after the type-cast fix)

```
$ cd site && npm run build && node -e "...card-count floor + empty-state-paragraph guard + EN/ES #news-facets deep-equality..."
...
[build] 834 page(s) built in 23.96s
[build] Complete!
OK: facets present, non-empty, EN/ES identical. byFamily keys: vida,robos_violentos,propiedad,drogas,incivilidades,armas,sexuales,vif
```
Card counts in the post-wiring `dist/` output: both EN and ES passed the >= 1000 floor (measured 1215/1215, unchanged from the pre-edit baseline — zero card-count regression).

### Task 2 — chained build+validate gate

```
$ cd site && npm run build && npm run validate
...
────────────────────────────────────────────────────────────
▶ freshness
────────────────────────────────────────────────────────────
PASS freshness: data/incidents/current.json is 2.7 days old (generated: 2026-07-27T14:25:05.303451Z)

✓ freshness: PASSED

────────────────────────────────────────────────────────────
▶ facets
────────────────────────────────────────────────────────────
PASS facets: 1215 incidents, 8 families observed, 346 communes cross-checked, 3 months in byMonth union, window(today=11,7d=297,30d=1215), TZ-determinism verified

✓ facets: PASSED


════════════════════════════════════════════════════════════
VALIDATION SUITE SUMMARY
════════════════════════════════════════════════════════════
  PASS  structure
  PASS  commune
  PASS  rollout
  PASS  region
  PASS  crime
  PASS  hreflang
  PASS  schema
  PASS  map
  PASS  forbidden-language
  PASS  coverage
  PASS  spine
  PASS  seo
  PASS  figure-registry
  PASS  avs-b-budget
  PASS  freshness
  PASS  facets
────────────────────────────────────────────────────────────
  16/16 validators passed

All validators passed.
```

**F-19 branch NOT taken.** `freshness` passed outright at execution time (`current.json` was 2.7 days old, under `MAX_AGE_DAYS=3`). The phase closes on a **plain 16/16**, not the F-19-qualified 15/16. Per the plan's own Step 2 instruction ("If freshness passes outright... ignore this entire branch"), no new blocker entry was needed — the pre-existing STATE.md Blockers entry (from before this gate ran) was updated to reflect that freshness passed this time, while keeping the standing note that it may flip red again in a later phase purely from elapsed time (F-19 governs if/when that happens).

### Task 2 — astro check (before the type-cast fix — 6 errors, 2 NEW)

```
src/pages/news.astro:122:34 - error ts(2345): Argument of type '{ ... cut?: string | number | undefined ... }[]' is not assignable to parameter of type 'IncidentLike[]'.
src/pages/es/noticias.astro:121:34 - error ts(2345): [same error]

Result (128 files):
- 6 errors
- 0 warnings
- 38 hints
```

### Task 2 — astro check (after the type-cast fix — back to 4-error baseline)

```
$ grep -n "ComparatorPairsLinks" checkout3.txt
src/components/ComparatorPairsLinks.astro:28:38 - error ts(7031): Binding element 'nameB' implicitly has an 'any' type.
src/components/ComparatorPairsLinks.astro:28:31 - error ts(7031): Binding element 'nameA' implicitly has an 'any' type.
src/components/ComparatorPairsLinks.astro:28:25 - error ts(7031): Binding element 'cutB' implicitly has an 'any' type.
src/components/ComparatorPairsLinks.astro:28:19 - error ts(7031): Binding element 'cutA' implicitly has an 'any' type.

Result (128 files):
- 4 errors
- 0 warnings
- 38 hints
```
Zero `news.astro`/`noticias.astro` errors remain. All 4 errors are the pre-existing `ts(7031)` baseline.

### Task 2 — pytest reconfirmation

```
$ cd pipeline && python -m pytest
=========== 344 passed, 1 skipped, 1 xfailed, 67 warnings in 44.39s ===========
```
Matches the untouched baseline exactly (this phase touched zero Python files).

### Task 2 — stale validator-count grep (scoped node check)

```
$ node -e "...scoped grep for 15/15 | 15 validadores | 15 validators in STATE.md and the directive, excluding the F-21 row..."
OK: no stale validator counts in STATE.md or the directive
```

### Task 2 — ROADMAP.md scope check

```
$ git diff .planning/ROADMAP.md
--- a/.planning/ROADMAP.md
+++ b/.planning/ROADMAP.md
@@ -324,7 +324,7 @@ Plans:
-- [ ] 27-02-PLAN.md — Wire news.astro + es/noticias.astro to computeNewsFacets(); chained build+validate+check+pytest phase-close gate
+- [x] 27-02-PLAN.md — Wire news.astro + es/noticias.astro to computeNewsFacets(); chained build+validate+check+pytest phase-close gate
@@ -437,7 +437,7 @@ Plans:
-| 27. News Facet Data Model | 1/2 | In Progress|  |
+| 27. News Facet Data Model | 2/2 | Complete   | 2026-07-30 |
```
Only Phase 27's checkbox and Progress Table row were touched — `### Phase 28` and its `**Plans**: TBD` line are untouched (confirmed by reading the full diff — no hunk near line ~329 where Phase 28's section starts).

### Task 2 — git status scope check

```
$ git status --porcelain .planning/
 M .planning/ROADMAP.md
 M .planning/STATE.md
 M .planning/v2.1-AUTONOMOUS-DIRECTIVE.md
```
No historical file (26-*-SUMMARY.md, 26-SPIKE-REPORT.md, quick/*-SUMMARY.md, research/ARCHITECTURE.md) was modified.

### Task 2 — freshness.mjs byte-unchanged check

```
$ git diff --stat site/scripts/validate/freshness.mjs
(empty output)
```
Confirmed unchanged, regardless of which F-19 branch fired (in this run, neither branch's remediation list was ever invoked, since freshness passed outright).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `computeNewsFacets()` call introduced two new `astro check` ts(2345) errors on optional `incident.cut`**
- **Found during:** Task 2, first `astro check` re-run after Task 1's wiring.
- **Issue:** Both pages' local `incidents` array type declares `cut?: string | number` (optional). `newsFacets.ts`'s `IncidentLike` interface requires `cut: string | number` (non-optional). TypeScript correctly flagged the mismatch as `ts(2345)` at both `computeNewsFacets(incidents, ...)` call sites — a real type-checker regression this plan's interfaces section did not anticipate (it showed the call as `computeNewsFacets(incidents, loadIndex(), archiveDir)` verbatim, without accounting for the type gap).
- **Fix:** Added `as unknown as import('../lib/newsFacets').IncidentLike[]` (ES: `'../../lib/newsFacets'`) at each call site, with an inline comment explaining the cast is behavior-neutral: `computeNewsFacets`/`facets.mjs` both resolve every `cut` via `String(inc.cut)`, which safely stringifies `undefined` to `"undefined"` and simply fails the region lookup (returns `undefined`/no match) rather than throwing — the exact same runtime behavior as before the cast, just now type-checker-clean.
- **Files modified:** `site/src/pages/news.astro`, `site/src/pages/es/noticias.astro` (both: one-line cast + comment, no other changes).
- **Commit:** `99b1435`.
- **Verified:** `astro check` re-run confirmed exactly 4 errors (the pre-existing `ComparatorPairsLinks.astro:28` `ts(7031)` baseline) with zero `news.astro`/`noticias.astro` hits; `npm run build && npm run validate` re-confirmed 16/16; the Task 1 EN/ES `#news-facets` deep-equality check was re-run and still passed.

**No other deviations.** Plan executed as written for all other steps.

## Known Stubs

None — this plan only adds a build-time data call and an inert JSON script node; no new UI, no placeholder data paths.

## Threat Flags

None. The `#news-facets` node serializes only counts and category keys derived from the closed 8-value family set and 16-value region set (per `newsFacets.ts`'s own design, unchanged in this plan) — no free-text incident titles/URLs/outlet names reach the JSON node. No new network endpoints, auth paths, or trust-boundary changes were introduced. STATE.md/ROADMAP.md/directive edits were additive Edit-tool operations, scope-verified by `git diff`.

## Self-Check

```
$ [ -f "site/src/pages/news.astro" ] && echo FOUND || echo MISSING
FOUND
$ [ -f "site/src/pages/es/noticias.astro" ] && echo FOUND || echo MISSING
FOUND
$ git log --oneline --all | grep -q "d37c816" && echo FOUND || echo MISSING
FOUND
$ git log --oneline --all | grep -q "99b1435" && echo FOUND || echo MISSING
FOUND
$ git log --oneline --all | grep -q "9a03e5c" && echo FOUND || echo MISSING
FOUND
```

## Self-Check: PASSED

## Notes for Phase 28 / the Opus reviewer

- **F-19's freshness branch was NOT exercised this run** — `freshness` passed outright (2.7 days < 3-day threshold) at the time this gate ran. The directive's Hard safety rules now carry a standing F-19 bullet so this doesn't need rediscovery if/when freshness flips red again in a later phase.
- The `#news-facets` projection shape shipped is exactly Decision 11's spec: `{ byFamily, byRegion, byMonth, byWindow: { today, sevenDay, thirtyDay } }` (counts/lengths only — no `IncidentLike[]` arrays, no `facetKeys`). Phase 28 should treat this as the load-bearing contract when building filter UI — cross-filtered counts are explicitly Phase 28's own client-side computation per F-20's Module Published Contract, not something this plan's static projection can serve.
- The `as unknown as IncidentLike[]` cast at both call sites is worth a second look in Phase 28 if `incidents`' local page type is ever tightened to make `cut` non-optional — at that point the cast becomes removable dead code, not a correctness requirement.
