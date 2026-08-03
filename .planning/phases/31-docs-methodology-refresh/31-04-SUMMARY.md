---
phase: 31-docs-methodology-refresh
plan: 04
subsystem: testing
tags: [vitest, build-time-validators, figure-registry, coverage, facets, mutation-testing, i18n]

requires:
  - phase: 31-01
    provides: national_rank direction fix (highest reported rate) on methodology.astro / metodologia.astro / safest-cities-in-chile.astro
  - phase: 31-02
    provides: data/SOURCES.md News section rewrite (news.google.com, Granite, R2, data/incidents/current.json)
  - phase: 31-03
    provides: bilingual facet-semantics note (id="news-facet-semantics") on /news/ and /es/noticias/
provides:
  - Hardened figure-registry.mjs F16 check (section-bounded, heading-stripped, length-guarded) that can no longer report PASS against a stub INE ENUSC SAE section
  - Real vitest mutation test (figure-registry.test.ts, 4 cases) proving the hardening is falsifiable
  - DOCS-01 build-time regression guard: inverted-phrase absence + corrected-phrase presence across all three national_rank pages, whitespace-normalized
  - DOCS-03 build-time regression guard: data/SOURCES.md must still carry Google News / Granite / R2 tokens
  - DOCS-06 anchor-presence assertion in coverage.mjs (six methodology anchors, both locales)
  - DOCS-04 facet-semantics-note assertion (23) plus EN/ES VALUE-parity assertion (23b) in facets.mjs
  - STATE.md backlog entries for the two map defects and the DOCS-04 clustering N/A disposition
affects: [phase-31-close, future-map-code-phase]

tech-stack:
  added: []
  patterns:
    - "Side-effect-free .lib.mjs sibling module pattern for making a CLI validator's logic unit-testable without a fragile process.argv[1] === fileURLToPath(import.meta.url) guard"
    - "Whitespace-normalized prose assertions (norm = s => s.replace(/\\s+/g,' ')) to avoid coupling a content guard to incidental line-wrap"
    - "i18n VALUE-parity assertion (not just KEY parity) for locale-pair prose nodes"

key-files:
  created:
    - site/scripts/validate/figure-registry.lib.mjs
    - site/scripts/validate/figure-registry.test.ts
  modified:
    - site/scripts/validate/figure-registry.mjs
    - site/scripts/validate/coverage.mjs
    - site/scripts/validate/facets.mjs
    - .planning/STATE.md

key-decisions:
  - "No CLI-execution guard on figure-registry.mjs (F-67) — checkF16/extractSection live in a separate side-effect-free figure-registry.lib.mjs instead, because all.mjs judges validators purely on exit status and a mis-comparing guard would silently disable F16 plus the new content checks"
  - "checkF16 strips the heading line before evaluating body length/tokens — the real heading already contains both of token group 1's members, so without stripping, a heading+filler stub would still pass at 200+ chars"
  - "extractSection anchors the heading match to line-start (regex with 'm' flag), not content.indexOf — SOURCES.md contains an inline backtick cross-reference to the same heading text earlier in the file, which a naive indexOf would match instead of the real '## ' heading"
  - "All six DOCS-01 prose checks run against whitespace-normalized content, never raw file bytes (F-68)"
  - "facets.mjs assertion 23b gates EN/ES note VALUE parity, closing a gap where assertion 13 only gated i18n KEY parity"

patterns-established:
  - "Pure logic extracted to sibling .lib.mjs modules when a CLI validator's core check needs a real vitest mutation test"

requirements-completed: [DOCS-05, DOCS-01, DOCS-03, DOCS-04, DOCS-06]

duration: 55min
completed: 2026-08-02
---

# Phase 31 Plan 04: Durable Regression Guards for the Phase 31 Prose Fixes Summary

**Hardened figure-registry's exploitable F16 stub-passes hole with a section-bounded, heading-stripped, length-guarded check plus a real 4-case vitest mutation test, and added four new build-time regression guards (DOCS-01/03/04/06) so Plans 31-01/31-02/31-03's prose fixes cannot silently regress.**

## Performance

- **Duration:** ~55 min
- **Tasks:** 3
- **Files modified:** 6 (2 created, 4 modified)

## Accomplishments

- Closed the F16 "green against a stub" hole: `checkF16` now extracts the `## INE ENUSC SAE` section, strips the heading line, and requires a body > 200 chars before applying the token check — proven by a real vitest spec that fails RED when reverted to the pre-hardening whole-file `.includes()` check.
- Added DOCS-01 (national_rank direction) and DOCS-03 (SOURCES.md News-section content) guards directly into `figure-registry.mjs`'s CLI run, whitespace-normalized per F-68.
- Added DOCS-06 anchor-presence assertion F to `coverage.mjs` — all six actively-linked methodology anchors (including the previously-ungated ES `#trend-formula`) are asserted present in `dist/`.
- Added DOCS-04 assertions 23/23b to `facets.mjs` — facet-semantics-note presence in both built news pages, plus an EN/ES VALUE-parity check that an untranslated copy-paste would trip. Final summary now reads "24 assertions passed".
- Appended STATE.md backlog entries for the two out-of-scope map defects and the DOCS-04 clustering N/A disposition.
- Ran and reported the full chained phase-close gate.

## Task Commits

1. **Task 1: Harden figure-registry.mjs's F16 check + encode the mutation test** - `291ed7d` (test)
2. **Task 2: Add durable regression guards for DOCS-01, DOCS-03, DOCS-04, DOCS-06** - `b98acd3` (feat)
3. **Task 3: STATE.md backlog notes + full chained phase-close gate** - `5d0d1ff` (docs)

## Files Created/Modified

- `site/scripts/validate/figure-registry.lib.mjs` - New side-effect-free module exporting `extractSection`/`checkF16` (F-67, no CLI-execution guard)
- `site/scripts/validate/figure-registry.test.ts` - Real vitest spec, 4 test cases against hardcoded fixtures (never data/SOURCES.md)
- `site/scripts/validate/figure-registry.mjs` - Imports `checkF16` for the F16 loop entry; appends DOCS-01/DOCS-03 content checks after the figure loop
- `site/scripts/validate/coverage.mjs` - New assertion F (six methodology anchors, both locales)
- `site/scripts/validate/facets.mjs` - New assertions 23 (note presence) and 23b (EN/ES value parity); summary text updated to "24 assertions passed"
- `.planning/STATE.md` - Two backlog entries (map legend bands, AVAILABLE_YEARS) + DOCS-04 N/A internal note

## Decisions Made

- **No CLI guard (F-67):** `figure-registry.mjs` keeps its existing top-level CLI shape unchanged; `checkF16`/`extractSection` live in a separate `figure-registry.lib.mjs` with zero side effects, imported by both the CLI script and the vitest spec. Avoids the catastrophic-and-silent failure mode where a mis-comparing `import.meta.url` guard makes the script run nothing, exit 0, and print PASS.
- **Heading-strip is mandatory:** confirmed empirically — the real `## INE ENUSC SAE` heading line already contains both `## INE ENUSC SAE` and `VHDV` (token group 1), so evaluating length against `heading + body` rather than `body` alone would let a padded 201-char stub pass. `checkF16` evaluates length against the body only, then re-joins `heading + body` only for the token check.
- **Line-anchored heading match, not `indexOf`:** discovered during Task 1 fixture-building that `data/SOURCES.md` line 313 contains an inline backtick cross-reference to the same heading text (`the dated SAE VHDV snapshot in the section below (\`## INE ENUSC SAE — communal VHDV...\`)`), which appears *before* the real heading in file order. A plain `content.indexOf(heading)` matched that inline reference and extracted a 372-char span instead of the real ~1,562-char section. `extractSection` now uses a `^`-anchored, `m`-flag regex so it only matches a genuine line-start `## ` heading.
- **All six DOCS-01 prose checks whitespace-normalized (F-68).**
- **facets.mjs assertion 23b (VALUE parity):** assertion 13 already gates that `news_*` i18n keys exist in both locales; 23b closes the gap where the *values* could be copy-pasted untranslated and still ship green.

## Deviations from Plan

None — plan executed exactly as written, including all five Fable-review amendments (no CLI guard, heading-strip, four vitest tests, whitespace normalization + six anchors, assertion 23b with "24 assertions passed").

One implementation detail not explicitly anticipated by the plan body (not a deviation from the amendments, but worth recording): `extractSection` needed line-start anchoring rather than a bare substring search, because of the inline backtick cross-reference to the real heading elsewhere in `data/SOURCES.md`. This was discovered and fixed during Task 1 before any commit, verified against the real file, and does not change any of the five amendments' required behavior.

## Falsifiability Evidence (RED then GREEN for every new assertion)

**checkF16 (Task 1):** Reverted `checkF16` in `figure-registry.lib.mjs` to the pre-hardening whole-file `.includes()` check:
```
FAIL  scripts/validate/figure-registry.test.ts > Test 1: heading-only stub ... expected true to be false
FAIL  scripts/validate/figure-registry.test.ts > Test 4: the padded-stub case ... expected true to be false
Test Files  1 failed (1)  Tests  2 failed | 2 passed (4)
```
Restored → `Test Files 1 passed (1)  Tests 4 passed (4)`.

**DOCS-01 inverted-phrase / positive-phrase checks (Task 2):** Temporarily changed `methodology.astro`'s "highest reported rate in Chile" to "lowest reported rate in Chile":
```
FAIL [DOCS-01] methodology.astro contains the inverted phrase "lowest reported rate in Chile" (national_rank direction regression)
FAIL [DOCS-01] methodology.astro is missing the corrected phrase "highest reported rate in Chile"
figure-registry: FAILED — 2 DOCS-01/DOCS-03 content check(s) failed
```
`node scripts/validate/figure-registry.mjs` exit code: RED=1. Restored from backup → exit code 0.

**DOCS-06 anchor-presence assertion F (Task 2):** Mutated `dist/methodology/index.html`'s `id="trend-formula"` to `id="trend-formula-removed"`:
```
node scripts/validate/coverage.mjs exit code: RED=1
```
Restored from backup → exit code 0.

**facets.mjs assertion 23 (Task 2):** Mutated `dist/news/index.html`'s `id="news-facet-semantics"` to `id="news-facet-semantics-removed"`:
```
FAIL facets: assertion 23 — EN built news page is missing the facet-semantics note (id="news-facet-semantics" with non-empty text content, Plan 31-03)
node scripts/validate/facets.mjs exit code: RED=1
```
Restored from backup → exit code 0.

**facets.mjs assertion 23b (Task 2):** Copied the EN note's inner text into `dist/es/noticias/index.html`'s ES note (byte-for-byte, same `id="news-facet-semantics"` element):
```
FAIL facets: assertion 23b — EN and ES facet-semantics notes are byte-identical after whitespace normalization (untranslated ES string, i18n VALUE-parity regression)
node scripts/validate/facets.mjs exit code: RED=1
```
Restored from backup → exit code 0.

All mutations were performed against scratch/dist/backup copies outside the repo (or restored from a Bash `cp` snapshot before commit); `data/SOURCES.md` itself was never written.

## Issues Encountered

None beyond the `extractSection` line-anchoring fix documented above, which was caught and resolved during Task 1's own fixture-building before any test ran green falsely.

## Full Chained Phase-Close Gate (Task 3)

Run from repo root, exactly as specified (build+validate chained in one command, OneDrive requirement):

```
cd site && npm run build && npm run validate
```

**Result: 15/16 validators passed, `freshness` the sole failure.**
```
FAIL freshness: data/incidents/current.json is 3.3 days old (generated: 2026-07-30T19:20:47.950917Z)
```
Both F-19 preconditions confirmed:
- (a) The failure output is exactly the age assertion (not missing-file, not unparseable `generated`).
- (b) `git log -1 --format=%ci origin/master -- data/incidents/current.json` → `2026-08-02 19:04:27 +0000`, within 3 days of the gate run.

Nothing was remediated: no `MAX_AGE_DAYS` change, no editing/skipping/deleting/unregistering the validator, no `data/` mutation, no `git pull`/`rebase`/`push`.

`cd site && npm test`:
```
Test Files  6 passed (6)
Tests  55 passed (55)
```
(51 pre-existing + 4 new figure-registry.test.ts cases = 55, as required.)

`npx astro check` (from `site/`):
```
Result (139 files):
- 4 errors
- 0 warnings
- 43 hints
```
Matches the pre-existing `ComparatorPairsLinks.astro` baseline exactly — zero new errors.

`python -m pytest pipeline/tests -q` (from repo root):
```
344 passed, 1 skipped, 1 xfailed, 67 warnings in 46.60s
```
Unchanged from the pre-phase baseline, as expected (this plan touches no Python).

**Close bar, stated explicitly per F-34 (never encoded into a gate command):** 16/16, or 15/16 with `freshness` excluded per the pre-authorized F-19 branch. This run closes at **15/16 with freshness excluded per F-19**.

## Next Phase Readiness

Phase 31's DOCS-05/01/03/04/06 requirements are now durably guarded by falsifiable build-time assertions. The two map defects and the DOCS-04 clustering N/A status are recorded in STATE.md as internal backlog, not reader-facing prose, ready for a future map-code phase to pick up. No blockers for Phase 31 close.

## Self-Check: PASSED

All created files verified present on disk; all three task commit hashes (291ed7d, b98acd3, 5d0d1ff) verified present in `git log --oneline --all`.

---
*Phase: 31-docs-methodology-refresh*
*Completed: 2026-08-02*
