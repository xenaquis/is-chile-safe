---
phase: 35-honest-freshness-signals
plan: 05
subsystem: validate
tags: [validator, cead, freshness, vintage, node]

# Dependency graph
requires:
  - phase: 35-03
    provides: ".cead-vintage markup contract (data-cead-last-updated, data-partial-year, data-latest-complete-year) on methodology, commune and region pages EN/ES"
  - phase: 35-04
    provides: "shared freshness-signal conventions; plan executed alone (wave 4) after 35-04 per G-21(1)"
provides:
  - "cead-vintage.lib.mjs pure checkCeadVintagePage/expectedFromJson/formatDate/findBannedPartialLabels"
  - "cead-vintage.mjs dist scanner registered as validator #17"
  - "CEAD_VINTAGE_DIST env injection point for 35-07's prod-fetched-HTML reuse"
affects: [35-06, 35-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure lib + dist-scanner split (figure-registry.lib.mjs precedent): the validator never imports the production code it checks (site/src/lib/ceadVintage.ts), re-deriving expected values from raw data/cead JSON instead (facets.mjs precedent)"
    - "toLabel() posix-relative path normalization for validator error messages, so grep-based mutation proofs work identically on Windows and POSIX (figure-registry.mjs:356 precedent)"
    - "CEAD_VINTAGE_DIST subset-mode injection: missing region/commune pages are skipped (not FAILed) only when the env override is set, so 35-07 can point this validator at a partial prod-HTML fetch"

key-files:
  created:
    - site/scripts/validate/cead-vintage.lib.mjs
    - site/scripts/validate/cead-vintage.test.ts
    - site/scripts/validate/cead-vintage.mjs
  modified:
    - site/scripts/validate/all.mjs

key-decisions:
  - "Gate condition 2 (F35-R1-02) applied literally: M assigned via `cygpath -m \"$TEMP\"` (no backslashes inside double quotes), every rm -rf guarded by `[ -n \"${M%/ics-cv-mut}\" ]`, and the banned-label mutation targets news/index.html (a page the .cead-vintage node-parser never touches), proving the 3b whole-dist scan independently of the per-page checker."
  - "Error-message paths are normalized to posix-relative labels via toLabel() (figure-registry.mjs precedent) — without this, Windows path.join backslashes would silently break the plan's `grep -q \"news/index.html\"` mutation-proof assertion."
  - "PASS prints the 3b-scanned HTML file count (836 in the ROLLOUT_ALL=true build) and FAILs on 0, satisfying the R2/F35-R1-02 vacuous-pass guard."

requirements-completed: [FRESH-05]

# Metrics
duration: 55min
completed: 2026-09-24
---

# Phase 35 Plan 05: FRESH-05 CEAD vintage validator Summary

**Validator #17 (cead-vintage.mjs) mechanically checks the CEAD "as of" date and partial-year label on every methodology, region and commune page in both locales, and scans the whole dist tree for the invented Jan-Jun/partial-data phrasing this milestone removed — proven to fail on two independent mutations.**

## Performance

- **Duration:** ~55 min
- **Started:** 2026-09-24T20:47Z
- **Completed:** 2026-09-24T20:52Z
- **Tasks:** 2/2
- **Files modified:** 4 (3 created, 1 modified)

## Accomplishments
- `cead-vintage.lib.mjs` re-derives the expected `{lastUpdated, partialYear, latestCompleteYear}` triple from raw CEAD JSON independently of `site/src/lib/ceadVintage.ts`, per the facets.mjs precedent (validators never import the code they check).
- `checkCeadVintagePage(html, expected, locale, {methodology})` asserts exactly one `.cead-vintage` node, its three `data-*` attributes, the locale-correct visible "CEAD data as of .../Datos CEAD al ..." prefix, the partial-year + latest-complete-year labels (or their absence when not partial), the methodology-only "(currently N)"/"(actualmente N)" narrative sentence, and the R-05 ban on "or trends"/"ni las tendencias".
- `findBannedPartialLabels()` flags the removed invented month-cutoff phrasing (`Jan–Jun`, `ene–jun`, `(partial data)`, `(datos parciales)`).
- 22 vitest cases cover every behavior in the plan, all green.
- `cead-vintage.mjs` scans dist/methodology + dist/es/metodologia (methodology mode), all 16 region pages per locale (R-02), all 346 commune pages per locale, and every `dist/**/*.html` plus `ResultPanel.tsx` for banned phrasing. Registered as validator #17 in `all.mjs` (header count 16 → 17).
- Full build + validator run: `PASS cead-vintage: 2 methodology + 16/16 region + 346/346 commune pages (EN/ES), 0 banned partial labels in 836 html files, CEAD as of 2026-06-16`. `npm run validate` → 17/17 PASS.
- Mutation proof 1: rewriting "CEAD data as of" → "CEAD data at" in a Temp-dir copy of `dist/commune/santiago/index.html` (via `CEAD_VINTAGE_DIST`) makes the validator exit 1, naming the mismatch.
- Mutation proof 2 (gate condition 2 / F35-R1-02): injecting `<p>(partial data)</p>` before `</body>` of a Temp-dir copy's `news/index.html` — a page whose `.cead-vintage` node the per-page checker never parses — makes the validator exit 1, and the error message names `news/index.html` (only the 3b whole-dist scan can catch it). `site/dist` itself was never touched; both mutations ran on `cygpath -m "$TEMP"/ics-cv-mut` copies guarded by `[ -n "${M%/ics-cv-mut}" ]` before every `rm -rf`.

## Task Commits

1. **Task 1: cead-vintage.lib.mjs pure checker + vitest** - `77ccb33` (feat)
2. **Task 2: cead-vintage.mjs dist scanner + register as validator #17** - `6536cde` (feat)

## Files Created/Modified
- `site/scripts/validate/cead-vintage.lib.mjs` - Pure `expectedFromJson`, `formatDate`, `checkCeadVintagePage`, `findBannedPartialLabels`
- `site/scripts/validate/cead-vintage.test.ts` - 22 vitest cases (good/bad EN+ES fixtures, mismatch, missing/duplicate node, partial-year present/absent, wrong-locale format, methodology narrative, R-05 ban, banned-label regex)
- `site/scripts/validate/cead-vintage.mjs` - Dist scanner: methodology (2) + region (16/16) + commune (346/346) pages, plus the 3b whole-dist banned-phrasing scan; `CEAD_VINTAGE_DIST` env override for subset/prod-fetch mode
- `site/scripts/validate/all.mjs` - Appends `cead-vintage.mjs` to `VALIDATORS` after `facets.mjs`; header comment updated to list 17 validators

## Decisions Made
- Applied gate condition 2 (F35-R1-02) verbatim: `M="$(cygpath -m "$TEMP")/ics-cv-mut"` with no backslashes inside double quotes, `[ -n "${M%/ics-cv-mut}" ]` guarding every `rm -rf`, and the banned mutation targeting `news/index.html` rather than a commune page, so the proof is specific to the 3b scan rather than the per-page node checker.
- Discovered during verification (Rule 1 — bug) that error messages built from Windows `path.join()` paths contain backslashes, which silently broke the plan's `grep -q "news/index.html"` assertion (grep matched 0 because the log read `...\news\index.html`). Fixed by adding a `toLabel()` helper (posix-relative path, `path.sep` split/joined to `/`) mirroring the existing `figure-registry.mjs:356` precedent, and applying it to every error-message path in the validator. Re-ran both mutation proofs after the fix; both now pass their grep/exit-code assertions.
- Followed the facets.mjs precedent and did not import `site/src/lib/ceadVintage.ts` from the validator or its lib module — `expectedFromJson` is a from-scratch reimplementation over raw JSON, satisfying the "validators do not import the code they check" must-have.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Windows backslash paths broke the plan's forward-slash grep assertion in error messages**
- **Found during:** Task 2 verify (banned-mutation grep check)
- **Issue:** `path.join(DIST_DIR, ...)` on Windows produces `\`-separated paths; error messages built directly from these paths (e.g. `${enPath}: ${e}`) could never satisfy a `grep -q "news/index.html"` check, since the on-disk log would contain `news\index.html` instead.
- **Fix:** Added `toLabel(p)` — `path.relative(SITE_ROOT, p).split(path.sep).join('/')` — and applied it to every error-message path in `cead-vintage.mjs` (methodology, region EN/ES, commune EN/ES, and the 3b banned-scan file list), mirroring the existing `figure-registry.mjs:356` normalization used elsewhere in this validator suite.
- **Files modified:** `site/scripts/validate/cead-vintage.mjs`
- **Commit:** `6536cde` (folded into Task 2's single commit; the fix was applied before the commit, not as a separate patch)

Otherwise: plan executed exactly as written, including all Revision R1/R2 gate-condition text (M assignment via `cygpath -m`, the `rm -rf` guard, and the `news/index.html` banned-mutation target).

## Issues Encountered

None beyond the backslash-path fix documented above; no auth gates, no architectural questions.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Validator count is now 17 (`structure` … `facets`, `cead-vintage`); `npm run validate` prints `17/17 validators passed`.
- `CEAD_VINTAGE_DIST` is the injection point 35-06/35-07 can reuse to run this validator against a subset dist tree or prod-fetched HTML, per the plan's design intent.
- No blockers for 35-06 or 35-07.

---
*Phase: 35-honest-freshness-signals*
*Completed: 2026-09-24*

## Self-Check: PASSED

- FOUND: site/scripts/validate/cead-vintage.lib.mjs
- FOUND: site/scripts/validate/cead-vintage.test.ts
- FOUND: site/scripts/validate/cead-vintage.mjs
- FOUND: .planning/phases/35-honest-freshness-signals/35-05-SUMMARY.md
- FOUND commit: 77ccb33
- FOUND commit: 6536cde
