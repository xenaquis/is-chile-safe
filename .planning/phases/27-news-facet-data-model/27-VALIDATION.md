---
phase: 27
slug: news-facet-data-model
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-30
---

# Phase 27 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

This is a frontend/Node build-time-derivation phase with **no Python changes**. Honest accounting of what each layer actually covers:

| Property | Value |
|----------|-------|
| **Framework** | No Jest/Vitest configured in `site/`. Verification is via (a) `@astrojs/check` for TypeScript type safety, (b) custom Node `.mjs` validator scripts (`site/scripts/validate/*.mjs`, run via `node scripts/validate/all.mjs`), and (c) `pytest` on the Python pipeline side — **unaffected by this phase**, run only to reconfirm the untouched baseline. |
| **Config file** | None per-validator — each is a standalone `.mjs` script; `all.mjs` is the aggregator/registry. `pytest` uses `pipeline/pytest.ini` (pre-existing, untouched). |
| **Quick run command** | `node site/scripts/validate/facets.mjs` (targeted, ~1s) or `cd site && npx astro check` (type-check only, ~10-20s) |
| **Full suite command** | `cd site && npm run build && npm run validate` (MUST be chained in ONE command — OneDrive `dist/` desync gotcha) |
| **Estimated runtime** | ~60-90s for full build+validate; ~10-20s for astro check alone; ~30-60s for the pytest reconfirmation run (unaffected, run for baseline safety only) |

---

## Sampling Rate

- **After every task commit:** Run `node site/scripts/validate/facets.mjs` (once it exists, Plan 01 Task 2 onward) and `cd site && npx astro check` for fast type/logic signal.
- **After every plan wave:** Full `cd site && npm run build && npm run validate` (chained, OneDrive-safe).
- **Before `/gsd:verify-work`:** Full suite must be green (16/16 validators), `@astrojs/check` delta = 0 new errors vs the 4-error `ComparatorPairsLinks.astro` baseline, pytest reconfirmed at 344 passed / 1 skipped / 1 xfailed (untouched).
- **Max feedback latency:** ~90 seconds (full chained gate).

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 27-01-01 | 01 | 1 | FACET-01, FACET-02, FACET-03, FACET-04, FACET-05 | T-27-01, T-27-03 | `computeNewsFacets()` produces correct, deterministic facet buckets from data actually present; malformed archive months skipped, not fatal | unit (inline test script or facets.mjs cross-check) | `npx astro check` (delta 0) + behavior-case script | ✅ (created by task) | ⬜ pending |
| 27-01-02 | 01 | 1 | FACET-01, FACET-03, FACET-04, FACET-05, FACET-06 | T-27-02, T-27-04 | `facets.mjs` independently proves count-sum integrity, region resolution, family-set containment; never writes to `data/`/`site/**` | validator (standalone Node script) | `node site/scripts/validate/facets.mjs` | ✅ (created by task) | ⬜ pending |
| 27-02-01 | 02 | 2 | FACET-01, FACET-06 | T-27-05, T-27-06 | Both news pages consume the identical `computeNewsFacets()` call, no structural drift; existing graceful-degradation (`existsSync` guard) unchanged; no new artifact under `site/**` | build assertion | `cd site && npx astro build` (exit 0, both pages render) | ✅ (modifies existing files) | ⬜ pending |
| 27-02-02 | 02 | 2 | FACET-07 | T-27-07 | Full chained build+validate is 16/16 green; astro check shows zero new errors; pytest baseline reconfirmed untouched | integration / full suite | `cd site && npm run build && npm run validate` + `npx astro check` + `cd pipeline && python -m pytest` | ✅ (existing scripts) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

`facets.mjs` (the new validator) is itself Wave 0-equivalent test infrastructure for this phase — it is created in Plan 01, Task 2, before any page wiring happens in Plan 02, so Plan 02's Task 1 already has a real automated check (`node scripts/validate/facets.mjs` against the wired pages' actual build output) available before its own verification step runs. No separate pytest scaffold is needed since this phase introduces zero Python changes.

- [x] `site/scripts/validate/facets.mjs` — created in Plan 01 Task 2, covers FACET-01/02/03/04/05/06 sanity assertions (not a stub — this is the phase's only durable regression test for facet count integrity)
- [x] No `tests/conftest.py` / pytest fixture changes needed — pipeline untouched
- [x] No new test framework install needed — `@astrojs/check` + existing `.mjs` validator pattern already covers this phase's verification needs (locked "zero new dependencies" decision)

*Existing infrastructure (astro check + the `.mjs` validator suite pattern) covers this phase's requirements once `facets.mjs` is added in Wave 1.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No new derived JSON committed anywhere; no facet artifact under `site/**` | FACET-06 | Absence-of-a-file is a repo-hygiene/procedural claim, not a unit-testable assertion — `git status --porcelain` is the correct tool but its output must be human/executor-reviewed against the expected `files_modified` list, not pattern-matched blindly | Run `git status --porcelain` after each plan's tasks; confirm only the files listed in that plan's `files_modified` frontmatter appear as changed, and no file appears under `site/public/data/` or any other `site/**` data-artifact path |
| `pipeline/shared/schema.py` (CEAD `FAMILY_KEYS`) byte-unchanged | FACET-04 | This is a negative-diff check on a file this phase's plans never list in `files_modified` — verifying "nothing changed" is a git-diff read, not a script assertion | Run `git diff --stat pipeline/shared/schema.py` after Plan 01/02; expect empty output |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (facets.mjs created ahead of its first consumer)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (all 4 tasks across both plans have an `<automated>` command)
- [x] Wave 0 covers all MISSING references (facets.mjs is the one new test artifact this phase needs, and it is built in Wave 1 before Wave 2 depends on it)
- [x] No watch-mode flags (all commands are one-shot: `astro check`, `astro build`, `npm run validate`, `pytest` without `--watch`)
- [x] Feedback latency < 90s (full chained gate; individual task checks are 1-20s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-30 (planner self-certification; this phase's verification is genuinely covered by existing `@astrojs/check` + `.mjs` validator infrastructure plus the new `facets.mjs`, with two explicitly-scoped manual/procedural checks for artifact-absence claims that are not meaningfully scriptable).
</content>
