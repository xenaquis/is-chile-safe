---
phase: 27-news-facet-data-model
verified: 2026-07-30T03:55:00Z
status: passed
score: 5/5 success criteria verified (FACET-01..07: 7/7 satisfied)
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
warnings:
  - id: W-1
    item: "facets.mjs assertion 1 is structurally unfalsifiable (tautology)"
    detail: "sumFamilyCounts is the sum of a histogram built in the same loop that increments incidentsWithFamily; the two quantities are the same number by construction. Fuzzed 20,000 random incident arrays — zero counterexamples. This is the same defect species review already caught twice (old assertion 7 tautology, assertion 8 dead branch); it is the fourth instance."
  - id: W-2
    item: "facets.mjs assertion 8 is also structurally unfalsifiable"
    detail: "today (date === max date) is necessarily a subset of 7d (date >= max-6) which is necessarily a subset of 30d (date >= max-29) which is necessarily <= incidents.length. All three comparisons are self-consistency checks on numbers the assertion computes itself from the same array; it never compares against newsFacets.ts output. Fuzzed 20,000 inputs — zero counterexamples. FACET-02 therefore has NO regression gate at the validator level (vitest Tests 4/4b/11 are the real gate and they ARE falsifiable)."
  - id: W-3
    item: "facets.mjs assertion 4 (phantom homicidios) is shadowed by assertion 3"
    detail: "Probed: a homicidios fixture fails at assertion 3, never reaching 4. Assertion 4 is only reachable if schema.py were edited to contain exactly 7 keys including homicidios. Redundant, not harmful."
  - id: W-4
    item: "newsFacets.ts:29-30 contract comment is still factually wrong (RR-2, accepted-not-fixed)"
    detail: "Comment claims currentCount reports the raw current.json row count 'unchanged'; it is now Set cardinality (distinct ids). Review accepted the behavior but the fix directive included 'correct the comment', which was not done. Phase 28 reads this comment as its contract."
  - id: W-5
    item: "assertion 5 hard-requires 'sexuales' to exist in live current.json"
    detail: "A legitimately sexuales-free news window (possible — 28/1215 today) would fail validator #16 and red the build on correct data. Data-shape coupling, not a correctness bug today."
  - id: W-6
    item: "FACET-07 checkbox still unchecked in REQUIREMENTS.md"
    detail: "Line 58 is '- [ ] FACET-07' and the Progress Table row reads 'Pending', while every FACET-07 condition is verified green here. Bookkeeping only."
deferred:
  - truth: "Window chips must be labelled relative to the data ('Últimos datos: 27 jul'), not as absolute 'Today'"
    addressed_in: "Phase 28"
    evidence: "27-REVIEW.md:101-102 records the caveat and assigns it to Phase 28's spec. Confirmed live: newest incident date is 2026-07-27 while wall-clock is 2026-07-30, so today=11 is already 3 days stale."
  - truth: "RR-2 / RR-3 / RR-4 byMonth id-fallback edge cases"
    addressed_in: "Phase 28 (recorded, accepted-not-fixed)"
    evidence: "27-REVIEW.md:311-313, 354. Verified unreachable on live data: 1215 incidents, 0 unresolved cuts, region sum == total == 1215."
  - truth: "F-20 forward contract (unfiltered marginal counts, string region ids, String(cut) coercion)"
    addressed_in: "Phase 28"
    evidence: "newsFacets.ts:5-11 module header; verified in dist — all 16 regionId values typeof string, facetKeys absent from the projection, byWindow counts-only."
---

# Phase 27: News Facet Data Model — Verification Report

**Phase Goal:** every existing incident discoverable by time window, region and crime family through a single build-time, shared facet index — zero Phase-26 dependency, zero new indexable URLs, zero risk to the 20,000-file budget.
**Verified:** 2026-07-30 (re-run from scratch, not read from SUMMARY)
**Status:** PASSED (5/5 criteria, 6 warnings, 0 blockers)
**Re-verification:** No — initial verification.

## What I actually executed

| Command | Result |
|---|---|
| `npm run build` then `npm run validate` (chained, same shell) | build exit 0; **16/16 validators PASS** including `facets` and `freshness` |
| `npm test` (vitest) | 2 files, **20 tests passed** |
| `npx astro check` | **4 errors, all `ComparatorPairsLinks.astro:28` ts(7031)** — the pre-existing baseline; 0 new errors on Phase 27 code |
| `python -m pytest` (pipeline) | **344 passed, 1 skipped, 1 xfailed** — the Phase 26 GO-gate xfail is intact |
| Independent recomputation of every facet from raw `data/incidents/*.json` + `data/cead/meta/index.json`, compared against the **rendered dist payload** | exact match on byFamily, byRegion, byMonth, byWindow (see below) |
| `node scripts/validate/facets.mjs <fixture>` × 3 negative fixtures | assertions 2, 3, 5 each fired with the right message |
| Temporary revert of the ES page's `escapeForInlineScript(...)` call → run facets.mjs → restore | RR-1 source guard **fired**; tree restored, `git status --porcelain` empty |
| 20,000-input fuzz of facets.mjs assertion 1 and assertion 8 logic | **0 counterexamples** for either — both unfalsifiable (W-1, W-2) |
| `node scripts/validate/avs-b-budget.mjs` | `1266 files in dist/ (limit 18000, margin 16734)`; 833 sitemap `<loc>`s; 0 facet routes |

Working tree left clean (`git status --porcelain` empty at start and end).

## Success Criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Shared `newsFacets.ts`, build-time, `process.cwd()`, both locales, no drift | ✓ VERIFIED | Module exists (253 lines, real logic). `news.astro:121` / `noticias.astro:120`: `path.resolve(process.cwd(), 'public/data/incidents/archive')`. Drift verified **empirically, not by eyeballing source**: the `#news-facets` node extracted from `dist/news/index.html` is **byte-identical** to `dist/es/noticias/index.html` (973 bytes each). Only diff in the two source blocks is the relative import depth and a translated comment. `facets.mjs` assertion 7 now opens BOTH dist pages (RR-1), so a future ES-only drift reds the build. |
| 2 | today/7d/30d presets + monthly archive, sparse days rolled up, no empty per-day slots | ✓ VERIFIED | Rendered `byWindow` = `{today:11, sevenDay:297, thirtyDay:1215}` — exactly my independent recomputation. `byMonth` = 3 buckets only (`2026-07:current:1198`, `2026-06:both:101 currentCount 17`, `2026-04:archive:1`) — months with no data emit no bucket, so sparse days/months are rolled up by construction. Regex scan of the rendered node for any `"YYYY-MM-DD":` per-day key → **no match**; no per-day structure exists anywhere in `newsFacets.ts` (only three preset arrays + a `window` tag). Caveat: `today` is anchored to the newest incident date (2026-07-27), not wall-clock — correct for a cron-rebuilt static site, and the UX labelling consequence is deferred to Phase 28 (see `deferred`). |
| 3 | Every `cut` resolves to one of 16 regions "via the established CUT-length derivation", derivation verified against `index.json` | ✓ VERIFIED — **and the wording tension resolves in the implementation's favour** | The module resolves region by **reading `region_id` from `index.json`** (`cutToRegion`), not by re-deriving in TS. I judge this to satisfy criterion 3, for three reasons I checked rather than assumed: (a) `facets.mjs` assertion 6 re-derives region from CUT length for **every** entry and compares to `region_id` — I independently re-ran that derivation: **346 entries, 0 mismatches, exactly 16 distinct region_ids** (`1..16`); (b) the derivation therefore *is* verified correct against `index.json`, which is literally what the criterion demands; (c) reading the authoritative field is strictly stronger than re-deriving it — it makes the 11/14 Tarapacá-style collision class (project memory) structurally impossible instead of merely tested. Resolution completeness: region counts sum to **1215 == total incidents, 0 unresolved cuts**, and assertion 2 hard-fails the build on any unresolvable cut (probed with a `99999` fixture → fired). Both string and numeric `cut` resolve to the same bucket (vitest Test 3). Caveat, stated plainly: assertion 6 hardcodes `index.json` and has no negative-path test (documented in the code as a known limitation) — the derivation is verified in the positive direction only, which is sufficient for the criterion as written. |
| 4 | All 8 news families with correct counts; CEAD `FAMILY_KEYS` still exactly 7 and unmodified; no phantom `homicidios` | ✓ VERIFIED | Counts checked against **raw data**, not merely present — rendered `byFamily` is byte-identical to my independent histogram: `vida 613, robos_violentos 283, propiedad 109, drogas 78, incivilidades 53, armas 32, sexuales 28, vif 19` (sums to 1215). 8 families incl. news-only `sexuales`. `homicidios` absent from rendered payload and from observed families; probed a `homicidios` fixture → validator fired. `pipeline/shared/schema.py` `FAMILY_KEYS` = 7 entries and `git diff 5457ea8..HEAD -- pipeline/` is **empty** — untouched. `facets.mjs` assertion 3 parses the list live from the Python source and hard-fails if it is not exactly 7. |
| 5 | No facet artifact under `site/**`, no new derived JSON, astro-check clean on new code, validators + page budget green, no new indexable URLs | ✓ VERIFIED | `find site -iname "*facet*"` (excl. node_modules) returns exactly three source files: `scripts/validate/facets.mjs`, `src/lib/newsFacets.ts`, `src/lib/newsFacets.test.ts` — no data artifact, and none under `site/public/` (assertion 10 walks that gitignored tree recursively). Phase diff adds **zero JSON**: only 3 new source files + 5 modified. astro check: 4 errors, all pre-existing `ComparatorPairsLinks.astro:28`. Budget checked explicitly: `avs-b-budget` → `1266 files in dist/ (limit 18000, margin 16734)` — nowhere near the Cloudflare 20,000 ceiling; the phase added **0 files to dist** (no new page modules; the facet index is an inline `<script type="application/json">` inside two already-existing pages). 833 sitemap `<loc>`s, 835 `index.html`s, no facet route in `dist/`, no query-param routes emitted → **no new indexable URLs**. |

**Score: 5/5.**

## Requirements Traceability

| Req | Artifact | Check that proves it | Status | Nominal? |
|---|---|---|---|---|
| FACET-01 | `newsFacets.ts` + both `.astro` pages | dist EN payload **byte-equal** to ES; `process.cwd()` archive path; assertion 7 opens both dist pages | ✓ SATISFIED | No — real |
| FACET-02 | `byWindow` + `byMonth` | rendered counts match independent recomputation; vitest Tests 4/4b/11 (7d spans exactly 7 dates, day-8 excluded); no per-day keys in output | ✓ SATISFIED | **Partly**: the validator-level gate (assertion 8) is a tautology (W-2). The real gate is vitest, which is falsifiable. |
| FACET-03 | `cutToRegion` + assertion 6 | 346/346 CUT-length derivations match `region_id`; 16 distinct ids; region sum 1215 == total; bad-cut fixture fires assertion 2 | ✓ SATISFIED | No — real, positive-direction only |
| FACET-04 | assertion 3 (live schema.py parse) + assertion 5 | 7 FAMILY_KEYS parsed live; 8th = `sexuales`; homicidios fixture fires; pipeline diff empty | ✓ SATISFIED | No — real (assertion 4 is redundant, W-3) |
| FACET-05 | `byFamily`/`byRegion`/`byMonth` counts in projection | every count matched against raw data independently | ✓ SATISFIED | **Partly**: assertion 1 cannot fail for any input (W-1). The real gates are assertion 7 (byMonth, proven falsifiable in review and structurally cross-checks the rendered page) and my own recomputation. Also `facetKeys` is computed but consumed by nothing today — deliberate F-20 groundwork for Phase 28, not a defect, but it is currently dead output. |
| FACET-06 | absence proof | `find` scan of all of `site/**`; assertion 10 walk of gitignored `site/public/`; phase diff adds no JSON | ✓ SATISFIED | No — real |
| FACET-07 | full gate | 16/16 validators, astro check 0 new errors, budget margin 16734, 0 new URLs, pytest baseline intact | ✓ SATISFIED (checkbox not updated — W-6) | No — real |

**Hunt for a fourth nominal defect: found two (W-1, W-2).** Both are the exact species review already caught twice: a validator assertion that recomputes a quantity from an input and then compares it to itself. Assertion 1 (`sum(histogram) === count of increments`) and all three comparisons in assertion 8 (`today ⊆ 7d ⊆ 30d ⊆ all`) are true by construction for every possible input — confirmed analytically and by 20,000-input fuzz. Neither reaches `newsFacets.ts`'s actual output, so neither would notice a regression in the module. They are not blockers: FACET-05's real coverage comes from assertion 7 (which does read the rendered page and was proven falsifiable) and FACET-02's from the vitest boundary tests, and I re-derived every count myself here. But the validator's advertised "10 assertions" is honestly 7 load-bearing ones.

## Nyquist (27-VALIDATION.md)

`nyquist_compliant: true` **holds**, with one accuracy correction owed:

- 27-01-01 row: claims "8 behavior cases" via `npm test`. Actual: `newsFacets.test.ts` has **13** `it()` blocks; `npm test` runs 20 tests over 2 files (the 7 pre-existing `formatNumber` tests now execute too — a genuine side-benefit of wiring `"test": "vitest run"`). Undercount, not overclaim. The spec is real, executed, and falsifiable (assertions on exact objects, not existence).
- 27-01-02 row: claims 10 assertions independently proving count-sum integrity. Two of those assertions cannot fail (W-1, W-2), so "independently proves count-sum integrity" is stronger than what ships. This is the one row I'd call not-quite-honest.
- 27-02-01/02 rows: accurate — I re-ran the exact commands and got the stated results, including the F-19 branch being unnecessary (`freshness` PASSED outright).
- Sampling continuity, no watch-mode flags, <90s latency: all confirmed (build+validate ~2 min on this OneDrive checkout; vitest 412 ms).
- The one weak test: Test 8 sets `process.env.TZ` in-process, which does not reliably re-seed V8's timezone cache — its pass is near-guaranteed. The real TZ proof is `facets.mjs` assertion 9's two `spawnSync` subprocesses, which I confirmed run and compare output.

## Premortem spot-checks

| Failure mode | Claimed mitigated | Verified |
|---|---|---|
| Local-time / TZ drift in window arithmetic | yes | ✓ assertion 9 greps `newsFacets.ts` for `toLocaleDateString`/`getMonth(`/`new Date(<digit>` (0 hits) **and** spawns two real subprocesses under `TZ=UTC` / `TZ=America/Santiago` with identical output |
| XSS breakout via `set:html` + `</script>` in LLM-derived family string | yes | ✓ **probed live**: reverting the ES page's `escapeForInlineScript` call makes assertion 7 fail. The honesty note in the validator is correct — the dist-level `<` check alone cannot catch the revert (today's payload has no `<`), which is why both guards exist |
| Per-locale drift | yes | ✓ byte-equal payloads + both dist pages gated |
| Stray artifact in gitignored `site/public/data/` | yes | ✓ assertion 10 recursive walk; independent `find` confirms nothing |
| CEAD `FAMILY_KEYS` extended to 8 | yes | ✓ live parse asserts exactly 7; pipeline diff empty |
| Cloudflare file budget | yes | ✓ 1266/18000, phase added 0 dist files |

## Anti-Patterns

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `site/scripts/validate/facets.mjs` | 78-92 | assertion 1 unfalsifiable | ⚠️ Warning | FACET-05 has no validator-level regression gate for family counts |
| `site/scripts/validate/facets.mjs` | 336-374 | assertion 8 unfalsifiable | ⚠️ Warning | FACET-02 has no validator-level regression gate (vitest covers it) |
| `site/scripts/validate/facets.mjs` | 142-144 | assertion 4 unreachable behind assertion 3 | ℹ️ Info | redundant |
| `site/scripts/validate/facets.mjs` | 149-151 | assertion 5 requires `sexuales` in live data | ⚠️ Warning | correct data with no sexual-offence news would red the build |
| `site/src/lib/newsFacets.ts` | 29-30 | doc comment contradicts code (RR-2) | ⚠️ Warning | Phase 28 treats this header as the contract |
| `site/src/lib/newsFacets.ts` | 63-77, 208-214 | `facetKeys` computed, never consumed | ℹ️ Info | intentional F-20 groundwork; dead until Phase 28 |
| both `.astro` pages | ~126 | `as unknown as IncidentLike[]` double cast | ℹ️ Info | already flagged in 27-02-SUMMARY.md for Phase 28 |

No `TBD`/`FIXME`/`XXX` markers in any file this phase modified (checked all 5 modified + 3 added source files).

## Human Verification Required

None. This phase ships no rendered UI — the deliverable is an inert `<script type="application/json">` node with no visual surface — and every criterion was verifiable by execution plus independent recomputation. The one judgment call (Phase 28's window labelling over stale data) is recorded as a deferred item, not a Phase 27 check.

## Gaps Summary

No blockers. All 5 ROADMAP success criteria and all 7 FACET requirements are satisfied in the codebase, verified by independent recomputation against the raw data rather than by reading SUMMARY claims: the rendered facet payload matches raw `current.json` + archive exactly on all four facet dimensions, in both locales, byte-for-byte identical between them.

The residue is validator quality, not product correctness: two of `facets.mjs`'s ten assertions (1 and 8) cannot fail for any input, making them the fourth and fifth instances of the tautology species review already fixed twice. Fixing them is small (compare against the rendered `#news-facets` payload the way assertion 7 already does, instead of against self-computed numbers) and belongs in Phase 28 or a `/gsd:quick`, not in a Phase 27 reopen. Also worth a one-line cleanup: `FACET-07`'s checkbox in `REQUIREMENTS.md` is still unchecked even though every one of its conditions is green here, and `newsFacets.ts`'s `currentCount` comment still states the pre-fix semantics.

---

_Verified: 2026-07-30_
_Verifier: Claude (gsd-verifier) — goal-backward, execution-based_
