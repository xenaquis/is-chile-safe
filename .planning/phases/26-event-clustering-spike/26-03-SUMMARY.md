---
phase: 26-event-clustering-spike
plan: 03
subsystem: pipeline/news (event clustering spike — GO/NO-GO evidence)
tags: [clustering, precision-recall, golden-set, pytest, spike-report]
dependency-graph:
  requires: [26-01 (assemble_clusters/adjudicate_pair), 26-02 (finalized golden-set fixture)]
  provides: [compute_pairwise_metrics, 26-SPIKE-REPORT.md, offline GO/NO-GO regression suite]
  affects: [26-04 (Wave 4 GO/NO-GO confirmation + xfail quarantine)]
tech-stack:
  added: []
  patterns: [single-source-of-truth metric function imported by CLI + tests, zero-denominator-safe precision, opt-in live_llm marker gated by env var]
key-files:
  created:
    - pipeline/scripts/run_clustering_spike.py
    - .planning/phases/26-event-clustering-spike/26-SPIKE-REPORT.md
  modified:
    - pipeline/tests/test_clustering.py
    - pipeline/tests/conftest.py
    - pipeline/tests/fixtures/clustering_golden_set.json (meta.baseline recorded)
decisions:
  - "Measured evidence: TP=22, FP=11 over 86 non-excluded golden-set pairs — matches the orchestrator's independently-computed preview exactly."
  - "This is a NO-GO. Numbers were not adjusted, thresholds not retuned, labels not touched to reach a target."
metrics:
  duration: "~25m"
  completed: "2026-07-29"
---

# Phase 26 Plan 03: Event Clustering GO/NO-GO Evidence Summary

Computed the pair-level precision/recall evidence for the event-clustering spike's GO/NO-GO decision: `compute_pairwise_metrics()` yields **TP=22, FP=11, precision=0.6667 (66.67%), recall=0.7333** over the 86 non-excluded golden-set pairs — an honest **NO-GO** against the locked 100%-precision/zero-false-merge gate, encoded as a failing (by design) pytest regression rather than a silently-weakened assertion.

## What Was Built

**`pipeline/scripts/run_clustering_spike.py`** (Task 1): a read-only CLI that loads the finalized golden-set fixture, defines the single module-level `compute_pairwise_metrics(pairs)` function (imported by both this script and the test suite — no formula duplication), assembles clusters via `pipeline.news.clustering.assemble_clusters`, and writes `.planning/phases/26-event-clustering-spike/26-SPIKE-REPORT.md`:

- Full 86-row pairwise decision matrix (one row per non-excluded pair: pair_id, category, proposed, golden label, same_event, confidence, edge-drawn, classification)
- Headline metrics as separate integers (TP, FP, FN split into `fn_prefiltered`/`fn_llm_rejected`, TN, precision-or-`None`, recall, n_pairs, n_failsafe)
- Confidence distribution: high=86/86, low=0 — states explicitly that the confidence condition rejected 0 pairs, so precision rests entirely on `same_event`
- Honest reduction-ratio statement: 86/99 proposed (~13.1% on the full call-log denominator), but on the two mandatory buckets the reduction is ~0% (min score 48.7 vs frozen threshold 45.0) — the real cost bound is `(cut,date)` bucketing, not the pre-filter
- Excluded/disputed pairs sub-table (8 `label_disputed` pairs, all involving the ambiguous `9b1e83` article or unread-source cases)
- Second-pass confirmation line: `merge-labels independently confirmed: 30/30 (blind second pass)`
- False-merge failure-mode table for all 11 FPs: 10 characterized as `aggregate-vs-component` (same operativo, different sub-report merged), 1 as `conflicting-sentence` (Tongoy 19-year vs 8.5-year sentence conflated) — the most valuable output of the spike for Phase 27/28
- Ends with the greppable line `**GO/NO-GO verdict: [PENDING — Fable orchestrator confirms against locked gate: 100% precision, 0 false merges, tp > 0, n_failsafe == 0]**`

**Tests** (Task 2, `pipeline/tests/test_clustering.py` + `conftest.py`):

- `meta.baseline` recorded once into the fixture: `{tp:22, fp:11, fn:8, fn_prefiltered:0, fn_llm_rejected:8, tn:45, precision:0.6667, recall:0.7333, n_pairs:86, n_failsafe:0}`
- `test_golden_set_metrics_match_recorded_baseline` — always-green internal-consistency sentinel (asserts current metrics == recorded baseline)
- `test_golden_set_meets_go_gate` — the honest CLUS-08 signal; **fails by design** (`fp=11 != 0`); left unmodified per the plan's non-negotiable constraint — Wave 4 (26-04) will quarantine it with `@pytest.mark.xfail(strict=True)`
- `test_cached_verdicts_match_current_model_config` — model/prompt-staleness guard, recomputes `SYSTEM_PROMPT` sha256 and compares against `meta`
- `test_golden_set_live_reeval` — opt-in (`@pytest.mark.live_llm` + `CLUSTERING_LIVE_EVAL` env var), skipped by default; asserts only `fp == 0`, logs TP/FN drift
- `pipeline/tests/conftest.py`: `pytest_configure` registers the `live_llm` marker (no "unknown mark" warnings)

## Measured Evidence (exact metric dict)

```json
{
  "tp": 22, "fp": 11, "fn": 8, "fn_prefiltered": 0, "fn_llm_rejected": 8,
  "tn": 45, "precision": 0.6666666666666666, "recall": 0.7333333333333333,
  "n_pairs": 86, "n_failsafe": 0
}
```

This matches the orchestrator's independently-computed preview (TP=22, FP=11) exactly, and both false-merge label-direction checks (F-13 blind second pass on merges, F-15 symmetric blind audit on the 11 FPs) confirm the numbers are genuine model errors, not label artifacts.

## Suite Pass/Fail Counts

- `pytest pipeline/tests/test_clustering.py -q`: **16 passed, 1 failed (test_golden_set_meets_go_gate, by design), 1 skipped (test_golden_set_live_reeval, opt-in)**
- `pytest pipeline/tests -q` (full suite): **317 passed, 1 failed (same test), 1 skipped**. Matches the plan's "Expected end state" exactly.
- No "unknown mark" warnings for `live_llm`.

## Deviations from Plan

None — plan executed exactly as written, including the non-negotiable instruction to report the honest NO-GO without adjusting labels, thresholds, or the metric formula.

## Verification

- `python pipeline/scripts/run_clustering_spike.py` runs clean, writes the report, prints the metric JSON.
- `26-SPIKE-REPORT.md` pairwise table row count (86) matches the golden-set fixture's non-excluded pair count exactly (verified via awk row count).
- `git diff --stat -- data/` is empty — no mutation of `data/`.
- No live LLM calls made (`test_golden_set_live_reeval` skipped by default; all other tests read only cached `cached_verdict` data).
- No `git push` performed.

## Self-Check: PASSED

- FOUND: pipeline/scripts/run_clustering_spike.py
- FOUND: .planning/phases/26-event-clustering-spike/26-SPIKE-REPORT.md
- FOUND: commit 0d8177d (Task 1)
- FOUND: commit 6857d54 (Task 2)
