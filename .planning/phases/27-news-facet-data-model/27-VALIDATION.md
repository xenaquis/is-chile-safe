---
phase: 27
slug: news-facet-data-model
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-30
revised: 2026-07-30
---

# Phase 27 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

## Amendments applied (revision cycle 1)

FM-5 (corrected the false "no Jest/Vitest configured" claim — `vitest ^4.1.9` is present in `site/devDependencies`, with no `test` script and one dead spec; 27-01-PLAN.md now wires a real `npm test`), FM-12 (downgraded the `git status --porcelain` manual entry to "tracked files only" and pointed to `facets.mjs`'s recursive stray-artifact walk under gitignored `site/public/data/`), F-19 (added the freshness environmental-exclusion branch to the "Before `/gsd:verify-work`" sampling rate, mirroring 27-02-PLAN.md's Task 2 wording so this document doesn't contradict it), F-21 (validator count corrected to 16 throughout, with the F-19-qualified "15/16" alternate phrasing noted). H2/FM-5 combined effect: the Per-Task Verification Map row for 27-01-01 is updated to point at the real `npm test` command instead of an unspecified "inline test script".

## Test Infrastructure

This is a frontend/Node build-time-derivation phase with **no Python changes**. Honest accounting of what each layer actually covers (corrected per FM-5 — the prior version of this document wrongly stated no test runner exists):

| Property | Value |
|----------|-------|
| **Framework** | `vitest ^4.1.9` **is** present in `site/devDependencies` (confirmed, not previously known). There was no `test` script and one pre-existing dead spec (`site/src/lib/formatNumber.test.ts`) that nothing in this repo executes. 27-01-PLAN.md Task 1 adds `"test": "vitest run"` to `site/package.json` and wires `newsFacets.test.ts` as a real, executed spec — this is now genuine test infrastructure, not a hollow file. Verification is additionally via (a) `@astrojs/check` for TypeScript type safety and (b) custom Node `.mjs` validator scripts (`site/scripts/validate/*.mjs`, run via `node scripts/validate/all.mjs`). `pytest` on the Python pipeline side is **unaffected by this phase**, run only to reconfirm the untouched baseline. |
| **Config file** | No `vitest.config.*`/`vite.config.*` exists under `site/` as of phase kickoff; Vitest's zero-config defaults are expected to discover `site/src/lib/newsFacets.test.ts`. If discovery fails, 27-01-PLAN.md Task 1 authorizes adding the minimal config needed, noted in the SUMMARY. Each `.mjs` validator remains standalone (no shared config); `all.mjs` is the aggregator/registry. `pytest` uses `pipeline/pytest.ini` (pre-existing, untouched). |
| **Quick run command** | `cd site && npm test` (vitest, ~5-15s) or `node site/scripts/validate/facets.mjs` (targeted, ~1s) or `cd site && npx astro check` (type-check only, ~10-20s) |
| **Full suite command** | `cd site && npm run build && npm run validate` (MUST be chained in ONE command — OneDrive `dist/` desync gotcha) |
| **Estimated runtime** | ~60-90s for full build+validate; ~10-20s for astro check alone; ~5-15s for `npm test`; ~30-60s for the pytest reconfirmation run (unaffected, run for baseline safety only) |

---

## Sampling Rate

- **After every task commit:** Run `cd site && npm test` (once wired, Plan 01 Task 1 onward), `node site/scripts/validate/facets.mjs` (once it exists, Plan 01 Task 2 onward), and `cd site && npx astro check` for fast type/logic signal.
- **After every plan wave:** Full `cd site && npm run build && npm run validate` (chained, OneDrive-safe).
- **Before `/gsd:verify-work`:** Full suite must be green — **16/16 validators**, or **15/16 with `freshness` environmentally excluded per F-19** (binding branch: admissible ONLY if the sole failure is `freshness`, the failure is exactly the age assertion, and `git log -1 --format=%ci origin/master -- data/incidents/current.json` shows a commit within 3 days; `MAX_AGE_DAYS`, `data/`, and `freshness.mjs`/`VALIDATORS` must stay byte-unchanged regardless). `@astrojs/check` delta = 0 new errors vs the 4-error `ComparatorPairsLinks.astro` baseline. Pytest reconfirmed at 344 passed / 1 skipped / 1 xfailed (untouched).
- **Max feedback latency:** ~90 seconds (full chained gate).

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 27-01-01 | 01 | 1 | FACET-01, FACET-02, FACET-03, FACET-04, FACET-05 | T-27-01, T-27-03 | `computeNewsFacets()` produces correct, deterministic, UTC-safe facet buckets (byFamily/byRegion/byWindow/byMonth/facetKeys) from data actually present; malformed archive months skipped, not fatal; byMonth is a real archive/current union | unit (real vitest spec) | `cd site && npm test` (8 behavior cases, real execution — corrected from the prior invalid "fold into facets.mjs" escape hatch) | ✅ (created by task) | ⬜ pending |
| 27-01-02 | 01 | 1 | FACET-01, FACET-03, FACET-04, FACET-05, FACET-06 | T-27-02, T-27-04, T-27-05 | `facets.mjs` independently proves count-sum integrity, region/CUT-length cross-check, family-set containment parsed live from Python source, byMonth completeness, TZ determinism, and stray-artifact absence (including gitignored `site/public/data/`); never writes to `data/`/`site/**` | validator (standalone Node script, 10 assertions) | `node site/scripts/validate/facets.mjs && echo GREEN` (corrected from the H1 no-op `; echo "EXIT:$?"` form) | ✅ (created by task) | ⬜ pending |
| 27-02-01 | 02 | 2 | FACET-01, FACET-06 | T-27-05, T-27-06 | Both news pages consume the identical `computeNewsFacets()` call via a real, build-provable `#news-facets` inert JSON node (not an unused local); existing graceful-degradation and ALL rendering markup byte-identical; no new artifact under `site/**` | build assertion (real build command) | `cd site && npm run build && node -e "<dist-parsing deep-equality check>"` (corrected from FM-3's forbidden `npx astro build`) | ✅ (modifies existing files) | ⬜ pending |
| 27-02-02 | 02 | 2 | FACET-07 | T-27-07, T-27-08 | Full chained build+validate is 16/16 green (or 15/16 with F-19's freshness exclusion correctly justified); astro check shows zero new errors; pytest baseline reconfirmed untouched; STATE.md/ROADMAP.md/directive corrected without cross-phase corruption | integration / full suite | `cd site && npm run build && npm run validate` + `npx astro check` + `cd pipeline && python -m pytest` + `grep -rn "15/15..." .planning/` | ✅ (existing scripts) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

`facets.mjs` (the new validator) and `newsFacets.test.ts` (the new vitest spec, wired to a newly-added `npm test` script) are both Wave 0-equivalent test infrastructure for this phase — both are created in Plan 01 before any page wiring happens in Plan 02, so Plan 02's Task 1 already has real automated checks available before its own verification step runs. No separate pytest scaffold is needed since this phase introduces zero Python changes.

- [x] `site/scripts/validate/facets.mjs` — created in Plan 01 Task 2, covers FACET-01/02/03/04/05/06 sanity assertions (10 total, not a stub) — this is the phase's only durable regression test for facet count integrity independent of the TS module itself
- [x] `site/src/lib/newsFacets.test.ts` + `site/package.json`'s new `"test": "vitest run"` script — created in Plan 01 Task 1, covers the 8 behavior cases (window-boundary arithmetic, family-set correctness, region resolution, byMonth union) as REAL executed assertions — corrects FM-5's finding that the prior plan would have produced a second never-executed spec
- [x] No `tests/conftest.py` / pytest fixture changes needed — pipeline untouched
- [x] No new test framework install needed — `vitest` is already a devDependency; wiring its existing `scripts` entry is a one-line change, not a new dependency (locked "zero new dependencies" decision holds)

*Existing infrastructure (vitest already installed, astro check, and the `.mjs` validator suite pattern) covers this phase's requirements once both are wired in Wave 1.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No new derived JSON committed anywhere under **tracked** paths | FACET-06 (partial) | `git status --porcelain` (tracked files only — corrected per FM-12: this check is **structurally blind** to the gitignored `site/public/data/` tree, the one location a stray facet artifact would most plausibly land) | Run `git status --porcelain` after each plan's tasks; confirm only the files listed in that plan's `files_modified` frontmatter appear as changed. **This does NOT cover `site/public/data/`** — that gitignored tree is covered by `facets.mjs`'s recursive `/facet/i` filename walk (assertion 10), which IS automated and IS part of the Per-Task Verification Map above, not a manual check. |
| `pipeline/shared/schema.py` (CEAD `FAMILY_KEYS`) byte-unchanged | FACET-04 | This is a negative-diff check on a file this phase's plans never list in `files_modified` — verifying "nothing changed" is a git-diff read, not a script assertion. Note: `facets.mjs` assertion 3 ALSO live-parses this file at validate time and hard-fails if `FAMILY_KEYS` is not exactly 7 entries, so a drift here is caught automatically too, not only by this manual check. | Run `git diff --stat pipeline/shared/schema.py` after Plan 01/02; expect empty output |
| `freshness.mjs` red at phase close due to unpulled upstream cron commits | FACET-07 (gate composition, not a FACET requirement itself) | This is a live, time-dependent environmental condition (F-19) that cannot be pre-verified at planning time — whether it applies depends on the checkout's state at execution time | Follow the exact F-19 branch in `27-02-PLAN.md` Task 2 Step 2: verify both conditions (age-only failure + upstream commit within 3 days) before treating the phase as closeable on a 15/16 basis; record the STATE.md Blocker verbatim if so |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (facets.mjs and newsFacets.test.ts created ahead of their first consumers)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (all 4 tasks across both plans have an `<automated>` command)
- [x] Wave 0 covers all MISSING references (facets.mjs and newsFacets.test.ts are the two new test artifacts this phase needs, both built in Wave 1 before Wave 2 depends on them)
- [x] No watch-mode flags (all commands are one-shot: `vitest run`, `astro check`, `npm run build`, `npm run validate`, `pytest` without `--watch`)
- [x] Feedback latency < 90s (full chained gate; individual task checks are 1-20s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-30, revised 2026-07-30 (revision cycle 1 — corrected the false vitest-absence claim per FM-5, downgraded the FACET-06 manual check to its true tracked-files-only scope per FM-12, and aligned the freshness gate language with 27-02-PLAN.md's F-19 branch so this document and the plan cannot contradict each other during execution).
</content>
