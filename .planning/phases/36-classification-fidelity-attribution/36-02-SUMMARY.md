---
phase: 36-classification-fidelity-attribution
plan: 02
subsystem: news-pipeline
tags: [eval, fidelity, golden-set, FID-02, G-38, G-39, G-77, shingle-guard]

requires:
  - phase: 34-news-classification-restore
    provides: golden_set_v2.json, eval_classifier.py run_full/select_winner seam
provides:
  - "eval_classifier.py score_fidelity() + --score CLI (offline FID-02 scorer)"
  - "run_full() rejected_in_prod / predicted_family on null/not_crime items"
  - "pipeline/tests/fixtures/golden_set_v3.json (79-item FID-02 gate set)"
  - "pipeline/tests/shingle_guard.py (shared 36-02/36-06 5-word collision guard)"
affects: [36-06, 36-08, 36-10]

tech-stack:
  added: []
  patterns:
    - "TDD RED via `git checkout -- <file>` to a clean prior commit, not stash (worktree-safe)"
    - "deterministic over-supply draws via random.Random(<fixed seed>) over sorted ids"

key-files:
  created:
    - pipeline/tests/fixtures/golden_set_v3.json
    - pipeline/tests/test_golden_v3.py
    - pipeline/tests/shingle_guard.py
    - pipeline/tests/test_shingle_guard.py
    - .planning/phases/36-classification-fidelity-attribution/36-GOLDEN-V3.md
  modified:
    - pipeline/experiments/eval_classifier.py
    - pipeline/tests/test_eval_classifier.py

key-decisions:
  - "NB-04 applied: score_fidelity's v2 commune/family subsets count only status=='ok' rows, not run_full's informational commune_match/family_match on low_conf rows."
  - "rejected_in_prod stays short-circuited behind `out.commune_name is None or resolve_cut(...) is None` (not called unconditionally) to avoid an extra resolve_cut() call on items with a null commune, preserving the existing single-call test assertion."
  - "G-77 boundary shortfall: a second 40-row pool (926 stored matches, random.Random(3602)) was labelled by a second independent fresh-opus blind labeller after the first pool gave only 4 boundary crimes (< 8). Combined boundary = 10, of which 8 resolve to a valid CUT."
  - "G-39 shortfall: suicide cue yielded 0 usable non-crime candidates; its 3-item quota was filled from institutional_preventive's surplus (which also covered the gap to the 24-item target), recorded as EFFECTIVE_QUOTAS."

requirements-completed: [FID-02]

duration: "~90 min"
completed: 2026-09-26
---

# Phase 36 Plan 02: FID-02 offline scorer + golden_set_v3 (Tasks 1-2) Summary

Adds an offline FID-02 fidelity scorer to `eval_classifier.py` (non-crime rejection rate, v2 subset scoring on the 41 uncontested ids per G-38, a family confusion matrix with a `not_crime` row) and freezes `golden_set_v3.json`, a 79-item gate set (47 v2 + 24 not_crime + 8 boundary crimes) built from two rounds of blind fresh-opus labelling over real stored `rejected/*.json` production inputs. **Task 3 (baseline eval run of the current prompt on v3) is explicitly left pending for the orchestrator** — it requires a paid LLM call this plan does not make.

## Performance

- **Duration:** ~90 min across two sessions (pool-build/scorer session + resume for blind-label assembly)
- **Tasks:** 2 of 3 (Task 3 is orchestrator-owned)
- **Files modified:** 7

## Accomplishments

- `score_fidelity()` + `--score` CLI: offline, no network, never calls `decide()`/`select_winner()`, never touches Phase-34 RESULTS files. Reproducibility pin against the committed G-16 run confirms uncontested commune 41/41, family 39/41 (all-44: 44/44, 42/44), matching G-38 exactly.
- `run_full()` now records `rejected_in_prod` and `predicted_family` on null/not_crime items using production semantics (low_conf, or accepted with a null/unresolvable commune).
- `golden_set_v3.json`: 79 items, v2's 47 byte-identical, 24 not_crime (accident 6, death_no_crime 3, fire_emergency 2, institutional_preventive 13, suicide 0), 8 boundary crimes across 5 families. Zero shingle collisions with the current prompt's rules text.
- G-77 boundary-shortfall extension executed: a second, independently-labelled 40-row pool raised boundary crimes from 4 to a combined 10 (8 resolvable), clearing the plan's own STOP bar without pausing.
- `pipeline/tests/shingle_guard.py`: shared 5-word-shingle collision guard (stdlib only), reused by 36-06.

## Task Commits

1. **Task 1: eval_classifier.py — rejected_in_prod + score_fidelity + --score CLI** — `4618d2b` (test, RED) → `fd74192` (feat, GREEN)
2. **Task 2 (partial, prior session): shingle_guard.py + availability/pool notes** — `a7ce16b` (feat)
3. **Task 2 (assembly): golden_set_v3.json + test_golden_v3.py** — `e2e3391` (feat)

RED for Task 1 was produced by reverting `eval_classifier.py` to its pre-plan committed state with `git checkout -- <file>` (not `git stash`, which is prohibited), running the new tests to confirm 15 failures, committing the test file, then restoring the implementation from a saved patch for GREEN.

## Files Created/Modified

- `pipeline/experiments/eval_classifier.py` - `score_fidelity()`, `load_v2_ids()`, `_write_fidelity_md()`, `--score`/`--out-json`/`--out-md` CLI flags, `run_full()` rejected_in_prod/predicted_family
- `pipeline/tests/test_eval_classifier.py` - 15 new tests (rejected_in_prod semantics, score_fidelity branches incl. NB-04 and negative control, G-16 reproducibility pin, `--score` CLI)
- `pipeline/tests/fixtures/golden_set_v3.json` - the 79-item FID-02 gate set
- `pipeline/tests/test_golden_v3.py` - structure/quota/boundary/shingle tests (8)
- `pipeline/tests/shingle_guard.py` - `prompt_rules_text`, `normalize`, `shared_shingles`
- `pipeline/tests/test_shingle_guard.py` - 7 unit tests + a sanity check against the real prompt
- `.planning/phases/36-classification-fidelity-attribution/36-GOLDEN-V3.md` - full fixture policy: availability, both pools' labels, G-39/G-77 shortfall handling, exclusions, per-item table, v3 source_ids for the 36-08/36-10 leakage guard

## Decisions Made

See `key-decisions` in frontmatter. In addition: `other_non_crime` (8 available items, not a listed nominal category) was intentionally left unused in v3 — the 24-item target was already met via `institutional_preventive`'s surplus, so `other_non_crime` stays available for a future `golden_set_v4.json` if quotas change.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `rejected_in_prod` called `resolve_cut` unconditionally on the first draft, breaking an existing test**
- **Found during:** Task 1 GREEN verification
- **Issue:** The first implementation always called `resolve_cut(out.commune_name, out.region_hint)` regardless of whether `commune_name` was `None`. Since `resolve_cut(None, ...)` is a no-op returning `None`, the boolean result was unaffected, but it added an extra observed call, breaking `test_run_full_end_to_end_calls_parse_content_once_per_item_and_records_fields`'s `mock_resolve.assert_called_once()`.
- **Fix:** Restored the literal short-circuit from the plan's `<behavior>` text: `out.commune_name is None or resolve_cut(out.commune_name, out.region_hint) is None`.
- **Files modified:** pipeline/experiments/eval_classifier.py
- **Verification:** Full `test_eval_classifier.py` suite green (43 tests) after the fix.
- **Committed in:** fd74192 (Task 1 GREEN commit)

**2. [Rule 4 twin, resolved by orchestrator as G-77] Boundary quota shortfall required a second labelling pool**
- **Found during:** Task 2 step 2 (blind labelling of the 70-item pool)
- **Issue:** The plan's step-1 pool (25 listed ids + suicide cue + institutional cue) produced only 4 boundary crimes against the plan's own `< 8 => STOP` rule — the pool never searched for a boundary cue.
- **Resolution:** This was an architectural/composition gap (Rule 4 territory), so it was surfaced to the orchestrator rather than auto-fixed. The orchestrator issued G-77 (owner-delegated) directing a second, independently-labelled 40-row pool over a boundary-cue regex. This executor built that pool's assembly (not its labelling — a fresh opus subagent did that, per the plan's blind-labelling requirement) and incorporated both pools into `golden_set_v3.json`.
- **Files modified:** pipeline/tests/fixtures/golden_set_v3.json, .planning/phases/36-classification-fidelity-attribution/36-GOLDEN-V3.md
- **Committed in:** e2e3391

---

**Total deviations:** 2 (1 auto-fixed bug, 1 orchestrator-resolved architectural gap via G-77)
**Impact on plan:** Both were necessary — the bug fix preserves an existing regression test's correctness guarantee; G-77 kept the gate set methodologically sound (independently-drawn, independently-labelled) instead of loosening the boundary floor or reusing the same labeller/pool.

## Issues Encountered

None beyond the deviations above. The negative control specified in Task 1's verify (treating `parse_error` as `rejected_in_prod` inflates the non-crime rate) was confirmed in an isolated subprocess without touching any repo file.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `golden_set_v3.json` and `score_fidelity()` are ready for **Task 3** (orchestrator): run the current prompt against v3 with `--provider openrouter --model deepseek/deepseek-v4.1-flash --reasoning enabled_false --spend-cap 0.10`, then `--score` it into `36-EVAL-BASELINE.json`/`.md`. This plan does not perform that run (it requires a paid LLM call).
- 36-06 (prompt iteration) can reuse `pipeline/tests/shingle_guard.py` directly and must gate against v3's `score_fidelity()` output, not v2.
- 36-08 and 36-10 must exclude the 32 `source_id`s listed in `36-GOLDEN-V3.md`'s "v3 source_ids" section from their audit samples (leakage guard).

---
*Phase: 36-classification-fidelity-attribution*
*Completed: 2026-09-26*

## Task 3 — baseline eval (orchestrator, 2026-09-26)

Command: the plan's eval command, openrouter deepseek/deepseek-v4.1-flash, reasoning disabled, on golden_set_v3.json (79 items). Run COMPLETE. The file was renamed to eval/run-baseline.json and scored into 36-EVAL-BASELINE.{json,md}.

| Metric | Result |
|---|---|
| Non-crime rejection | **12/24 = 0.50** (gate needs ≥ 0.80) |
| accident | 0/6 |
| death_no_crime | 0/3 |
| fire_emergency | 0/2 |
| institutional_preventive | 12/13 |
| v2 uncontested | commune 41/41, family 39/41 |
| v2 all 44 | commune 44/44, family 42/44 |
| Parse / empty / truncation | 0 / 0 / 0 |
| Null v2 items | 3/3 correct |
| **Boundary family (no-regression floor for 36-06)** | **5/8** |
| Spend | USD 0.0212 (cap 0.10) |

Contested v2 items (reported only): gs-030 accepted as incivilidades, gs-032 as propiedad, gs-038 as propiedad.

The baseline is not gated. The 0.50 rate confirms V-07 on live-like inputs: accidents and natural deaths are accepted as crimes. 36-06 must reach ≥ 0.80 without dropping below 5/8 on boundary items.
