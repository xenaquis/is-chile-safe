---
phase: 26-event-clustering-spike
fixed_at: 2026-07-30T01:15:00.000Z
review_path: .planning/phases/26-event-clustering-spike/26-REVIEW-2.md
iteration: 2
findings_in_scope: 6
fixed: 6
skipped: 0
tests_passed: true
test_command: python -m pytest pipeline/tests -q
status: all_fixed
---

# Phase 26: Code Review Fix Report (cycle 2 of 2, final)

**Fixed at:** 2026-07-30
**Source review:** .planning/phases/26-event-clustering-spike/26-REVIEW-2.md
**Iteration:** 2

**Summary:**
- Findings in scope: 6 (RG-01, RG-02, RG-03, RG-04, RG-05, IN-01)
- Fixed: 6
- Skipped: 0
- Test gate: PASSED (`python -m pytest pipeline/tests -q`)

## Test Gate

- ✓ **PASSED** — `python -m pytest pipeline/tests -q` exited 0 after all fixes: **344 passed, 1 skipped, 1 xfailed**.

## Fixed Issues

### RG-01: `_build_report` still crashed on a null `cached_verdict`

**Files modified:** `pipeline/scripts/run_clustering_spike.py`, `pipeline/tests/test_clustering.py`
**Commit:** `dd09ccc`
**Applied fix:** Hardened the two remaining unguarded reads in `_build_report` (`conf_high`/`conf_low` computation and the pairwise decision-matrix row builder) to use `p.get("cached_verdict") or {}` instead of `p["cached_verdict"].get(...)`, matching the guard already present in `compute_pairwise_metrics`/`_edge_drawn`. A null verdict now renders as an explicit `"n/a (null verdict — failsafe)"` marker in the matrix row instead of raising `AttributeError`. Added `test_build_report_does_not_crash_on_null_cached_verdict`, which builds a fixture with one `proposed:true, cached_verdict:null` pair and asserts `_build_report` returns a report string (not a crash) containing that marker.

### RG-02: empty/missing titles were still adjudicated live instead of failing safe before any API call

**Files modified:** `pipeline/news/clustering.py`, `pipeline/tests/test_clustering.py`
**Commit:** `37c1f59`
**Applied fix:** `adjudicate_pair` now checks `_clean_title(...)` on both incidents' `title_es` and short-circuits to `_no_merge_verdict("failsafe_parse")` **before** calling `_build_user_content`/`_call_verdict_api` if either side is missing, `None`, non-string, or empty/whitespace-only. This closes the review's second, previously-unimplemented half of HI-07: an empty pair can no longer be sent live and recorded as a `source: "model"` verdict that could draw a merge edge. Added 4 new tests covering missing-key, `None`, empty-string, and whitespace-only titles on side A, plus a symmetric test for side B — all assert `mock_client.chat.completions.create.assert_not_called()` and `verdict.source == "failsafe_parse"`.

### RG-03: a report with a lost sentinel silently got the `[PENDING]` placeholder (fail-open); write was not atomic

**Files modified:** `pipeline/scripts/run_clustering_spike.py`, `pipeline/tests/test_clustering.py`
**Commit:** `6ce8f20`
**Applied fix:** `_assemble_report` now distinguishes "no report file exists yet" (uses the `[PENDING]` placeholder, as before) from "a report file exists but the sentinel cannot be found" (raises `SystemExit` with a loud FATAL message, leaving the existing file untouched). Added `_write_report_atomically`, which writes to a temp file in the same directory (`tempfile.mkstemp`) and then `os.replace`s it into place — closing the torn-write risk called out for this OneDrive-hosted repo. `main()` now calls `_write_report_atomically` instead of `REPORT_PATH.write_text`. Added 4 new tests: sentinel-missing abort (file untouched), placeholder-on-first-run, preserve-existing-human-section, and atomic-write-leaves-no-temp-file.

### RG-04 (regression): an existing `meta.baseline` was preserved unconditionally with no comparison, allowing silent drift

**Files modified:** `pipeline/scripts/build_golden_set.py`, `pipeline/tests/test_clustering.py`
**Commit:** `efa2c9e`
**Applied fix:** `fill_verdicts` now always recomputes `compute_pairwise_metrics(final_pairs)` and, when an existing `meta.baseline` is found, compares it against the recomputed value. If they match, the recorded baseline is kept silently (unchanged behavior). If they differ, the recorded baseline is still preserved (per HI-03's idempotency contract — `--fill-verdicts` never auto-regenerates an existing baseline), but a `logger.error` names old vs new and the fixture gets `meta.baseline_stale: true` plus `meta.baseline_recomputed_at_write`. Updated `test_golden_set_metrics_match_recorded_baseline`'s guidance text (the old "regenerate via `--fill-verdicts`" message was misleading for the stale-baseline case, since a re-fill will never move an already-present baseline) and added an assertion that the committed fixture never has `baseline_stale` set. Added 2 new tests exercising the write path directly: one confirms a mismatch is flagged (`baseline_stale=True`, `baseline_recomputed_at_write` populated, original baseline preserved verbatim) and one confirms a matching baseline stays silent (no marker written).

### RG-05: the in-loop budget-cap abort had no test coverage

**Files modified:** `pipeline/tests/test_clustering.py`
**Commit:** `7d8faa6`
**Applied fix:** Added `test_fill_verdicts_in_loop_budget_abort_fires_at_expected_call_count`, which bypasses the (deliberately conservative, and therefore never-naturally-tripped-if-correct) pre-flight projection by stubbing `_budget_guard` directly, then drives the real in-loop arithmetic with `last_cumulative=1990` and an all-model-success `adjudicate_pair` stub. Asserts the loop aborts exactly when `1990 + calls_this_run + 2 > 2000` (probe + 8 successful pairs = 9 calls before abort), that `mock_adjudicate.call_count == 9`, that the ledger note contains `"in-loop budget cap reached"`, and that the fixture is not finalized on a budget abort.
**Mutation check:** temporarily inverted the in-loop comparison (`>` → `<`) in `build_golden_set.py:592`. The new test failed as expected (`assert 1 == 9` — the loop no longer aborted, so only the probe call fired). Reverted the mutation; full suite re-confirmed green (42 passed in `test_clustering.py`, no regressions).

### IN-01: `26-VALIDATION.md` sign-off cited a stale hand-typed pytest count

**Files modified:** `.planning/phases/26-event-clustering-spike/26-VALIDATION.md`
**Commit:** `d60a532`
**Applied fix:** Appended the current cycle's actual count (344 passed, 1 skipped, 1 xfailed, exit 0) to the Approval line, and added an explicit note that this figure will keep changing as tests are added/removed — the authoritative figure is always whatever `python -m pytest pipeline/tests -q` reports at the time, not a hand-typed number in this document. The prior "331 passed" entry was left in place (historical record of that point in time) rather than overwritten, consistent with how the line already records the 317 → 331 progression.

## Skipped Issues

None — all 6 findings in scope were fixed.

---

## Verification (per the objective's `<verification_required>` block)

- `python -m pytest pipeline/tests -q` → **344 passed, 1 skipped, 1 xfailed**, exit 0.
- Independently recomputed metric dict (via `python pipeline/scripts/run_clustering_spike.py`, twice):
  ```json
  {"tp": 22, "fp": 11, "fn": 8, "fn_prefiltered": 0, "fn_llm_rejected": 8, "tn": 45,
   "precision": 0.6666666666666666, "recall": 0.7333333333333333, "n_pairs": 86, "n_failsafe": 0}
  ```
  **Byte-identical** to the value in `26-REVIEW-2.md` and to `f094142`'s baseline. No value moved.
- Ran `python pipeline/scripts/run_clustering_spike.py` twice: `git diff --stat` on `26-SPIKE-REPORT.md` was **empty** after both runs. Verdict line (`**GO/NO-GO verdict: NO-GO**`), all 11 FP `pair_id`s, and the "What Phase 27/28 should do with this" section confirmed intact in the preserved human-authored section.
- `git diff f094142..HEAD --stat -- pipeline/news/schema.py data/` → **empty**.
- `test_golden_set_meets_go_gate` still carries `@pytest.mark.xfail(strict=True, reason="Phase 26 NO-GO: fp=11 …")` with the assertion body byte-identical: `assert metrics["fp"] == 0 and metrics["tp"] > 0 and metrics["n_failsafe"] == 0`.
- RG-05 mutation check: inverting the in-loop comparison caused the new test to fail (`assert 1 == 9`); reverting restored a green suite. Confirmed the branch is genuinely covered, not dead code.

## Worktree/commit mechanics

All 6 fixes were made and committed inside an isolated worktree (`gsd-reviewfix/26-<pid>`, branched from `master` at `04062be`), then fast-forward-merged back onto `master` (`git merge --ff-only`, clean fast-forward, no divergence). The temp branch and worktree were removed and the recovery sentinel deleted after the fast-forward succeeded. `master` now sits at `d60a532` with all 6 commits (`dd09ccc`, `37c1f59`, `6ce8f20`, `efa2c9e`, `7d8faa6`, `d60a532`) in place.

---

_Fixed: 2026-07-30_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 2_
