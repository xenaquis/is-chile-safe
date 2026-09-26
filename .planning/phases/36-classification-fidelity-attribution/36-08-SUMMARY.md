---
phase: 36-classification-fidelity-attribution
plan: 08
subsystem: news-pipeline
tags: [classifier, fidelity, FID-03, gnews-decoder, out-of-sample-audit, G-32, G-42, G-43, G-45, R-09, R-10, R-16, R-21, BF-03, BF-07]

requires:
  - phase: 36-06
    provides: "shipped classifier.py prompt (blob dcc33ead...), golden_set_v3 FID-02 gate"
  - phase: 36-07
    provides: "gnews_decoder.decode_gnews_url session-based new-format decode (G-43 groundwork)"
provides:
  - "pipeline/experiments/fid03_audit.py: --select/--classify/--sample/--score, offline-tested, replays the production classify path"
  - "36-FID03-AUDIT.md: FID-03 outcome FAILED/Partial (37/50, vida 19/25), full pool/spend/verdict record, G-33 decision text"
affects: [36-09, 36-10, 36-11]

tech-stack:
  added: []
  patterns:
    - "population = offline replay of a stored rejected/ stream through the production classify path, deduped and sibling-excluded against a golden set, sampled with a fixed seed"
    - "two-pass blind audit: q3 computed from a frozen pass-1 verdict, never asked directly, to avoid reviewer anchoring on the model's own label"
    - "a failing extra-iteration prompt candidate is gated on the in-sample golden set BEFORE any further out-of-sample spend"

key-files:
  created:
    - pipeline/experiments/fid03_audit.py
    - pipeline/tests/test_fid03_audit.py
    - .planning/phases/36-classification-fidelity-attribution/36-FID03-AUDIT.md
  modified: []

key-decisions:
  - "FID-03 = FAILED/Partial: agreement 37/50 (min 43), vida precision 19/25 (min 22). 36-09 ships classifier.py iteration 2 anyway (FID-02 passed, improves on live G-18 q1 40/50)."
  - "The one permitted extra iteration (36-06 iteration 3, e5f866e) was evaluated on golden_set_v3 FIRST per BF-07/G-38 and failed FID-02 (18/24 vs 20/24) — reverted (c0c58b9) without a seed-3609 re-audit, since auditing a prompt that cannot ship would not change the decision."
  - "G-33 recorded: Granite-era re-classification stays NO (owner default); FID-03 failure added to deferred-live as an owner question (accept / extend golden set + new rule / evaluate another model)."
  - "Ledger-overwrite-across-invocations in backfill_classifier_outage.SpendMeter.persist() is a tooling defect, documented as a deviation and NOT fixed (shared code, out of this plan's file scope); cumulative spend across the 5 classify chunks was hand-summed from the per-chunk ledger snapshots."

requirements-completed: [FID-03]

duration: "~1h (tool + tests) + orchestrator-run replay/audit"
completed: 2026-09-26
---

# Phase 36 Plan 08: FID-03 out-of-sample audit Summary

FID-03 measured the Phase-36 classifier (36-06 iteration 2) on a fresh, blind, out-of-sample 14-day replay: 1,380 candidate rows minus golden_set_v3 ids and event-siblings, 622 would-publish items, a seeded 50-item sample audited two-pass by a fresh reviewer. The audit FAILED the declared gate (37/50 agreement, vida precision 19/25), but the one permitted extra prompt iteration failed FID-02 in-sample first and was reverted, so 36-09 ships the already-gated iteration 2 regardless.

## Task Commits

1. **Task 1: fid03_audit.py (select/classify/sample/score)** - `b778bcd` (feat)
2. **Task 2: Select + replay-classify the 14-day pool** - `8526db8` (docs)
3. **Task 3: Blind 50-item audit + mechanical decision + G-33** - `475b11f` (docs)

**Plan metadata:** this SUMMARY commit (docs: complete plan)

## Files Created/Modified

- `pipeline/experiments/fid03_audit.py` - `--select` (14-day window + id/sibling exclusion + epoch split), `--classify` (replays backfill_classifier_outage.run_classify with a SpendMeter, refuses cache paths under data/), `--sample` (deterministic would-publish draw + blind-out with session-based Google-News decode), `--score` (q1∧q3 agreement, vida precision, per-basis breakdown, mechanical PASS/FAILED)
- `pipeline/tests/test_fid03_audit.py` - 16 offline tests (network-guarded), incl. the plan's fixed negative control (FID03_MIN_AGREE=42 flips the 42/50 fixture to PASS)
- `.planning/phases/36-classification-fidelity-attribution/36-FID03-AUDIT.md` - full record: pool (1380, outage=1210/live=170, 13 sibling exclusions), spend (0.2006 across 5 chunks), would-publish (622, vida 51.13% vs current.json's 64.93%), 50-item verdict table, failure categories, iteration-3 revert, G-33 text

## Decisions Made

See `key-decisions` in frontmatter. In addition: `sample_by_epoch`/`agreement_by_epoch` came back `outage=50 live=0` — the 622-item would-publish pool is dominated by the outage-era stage (`classifier_none`, 1210/1380 rows), so an unweighted random draw at seed 3608 landed entirely in that epoch; this is informational only (NB-01), not gated.

## Deviations from Plan

### Auto-fixed / Documented Issues

**1. [Rule 3 - blocking, environment] Classify run killed by a memory-pressure reaper mid-execution**
- **Found during:** Task 2
- **Issue:** The foreground `--classify` invocation exceeded the tool's 120s timeout and was auto-backgrounded; concurrent `until`-loop monitors I spawned to wait on it were killed by the harness's background-shell-pressure reaper (system critically low on memory), along with the classify process itself, at 303/1380 rows.
- **Fix:** The orchestrator resumed the same cache in 4 further foreground chunks (no background monitors), completing all 1380 rows with `cached_final=1380 uncached=0`. No data/ writes occurred at any point (cache is append-only JSONL outside data/).
- **Files modified:** none (scratchpad cache only)
- **Verification:** `wc -l` on the cache = 1380; `git diff --quiet -- data/` clean.

**2. [Not fixed - documented] SpendMeter ledger overwrite across invocations**
- **Found during:** Task 2 (5-chunk classify run)
- **Issue:** `backfill_classifier_outage.SpendMeter.persist()` writes the full ledger state on every call, but does not read/merge a prior invocation's total — so splitting one logical classify run into 5 process invocations (forced by the memory-pressure kill) left the ledger file reflecting only the last invocation's own total, not the cumulative spend.
- **Fix:** NOT applied — this is shared code (`pipeline/backfill_classifier_outage.py`) reused as-is by `fid03_audit.py --classify`, and is out of this plan's `files_modified` scope. Cumulative spend (USD 0.2006) was computed by hand-summing the 5 per-chunk ledger snapshots and recorded in 36-FID03-AUDIT.md.
- **Files modified:** none
- **Verification:** manual arithmetic cross-checked against the orchestrator's independently reported per-chunk figures (exact match).

**3. [Rule 4-adjacent, plan-declared path] Extra-iteration re-audit not run**
- **Found during:** Task 3 step 3
- **Issue:** The plan's decision rule calls for a seed-3609 re-audit after any extra prompt iteration. The one permitted extra iteration (36-06 iteration 3, `e5f866e`) failed FID-02 on golden_set_v3 first (18/24 vs the 20/24 gate).
- **Fix:** Per BF-07/G-38 order (evaluate in-sample before further out-of-sample spend), the failing iteration was reverted (`c0c58b9`) instead of re-audited — auditing a prompt that cannot ship would not change the FID-03 decision and would spend budget for no purpose.
- **Files modified:** `pipeline/news/classifier.py` (reverted to blob `dcc33ead...`)
- **Verification:** `git hash-object pipeline/news/classifier.py` == `dcc33ead6c517787f9fde2858b06571702421f3c` (the 36-06-shipped blob), confirmed after the revert commit.

**Total deviations:** 3 (1 environment interruption recovered without data loss, 1 documented-not-fixed tooling defect, 1 plan-order-compliant skip of a step that would not have changed the outcome).
**Impact on plan:** No scope creep; FID-03's own numbers and gate are unaffected by any of the three.

## Issues Encountered

None beyond the deviations above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

36-09 can ship classifier.py iteration 2 (FID-02 PASS, blob `dcc33ead6c517787f9fde2858b06571702421f3c`) since FID-03's failure is documented-not-blocking per the plan's own "36-09 may still ship if FID-02 passed" rule. The deferred-live owner question (accept / extend golden set + new pre-declared rule / evaluate another model) should be resolved before any further prompt-iteration spend against these specific failure classes (procedural/statement non-crime, and vida/armas/vif/robos_violentos boundaries).

---
*Phase: 36-classification-fidelity-attribution*
*Completed: 2026-09-26*
