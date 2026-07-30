---
phase: 26
slug: event-clustering-spike
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-29
revised: 2026-07-29
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `26-RESEARCH.md` § Validation Architecture, revised per `26-PREMORTEM.md` amendments and the revision-cycle-2 blocker/warning fixes.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.* (`pipeline/requirements.txt`) |
| **Config file** | none dedicated — discovery via `pipeline/tests/test_*.py`; shared fixtures + marker registration in `pipeline/tests/conftest.py` |
| **Quick run command** | `python -m pytest pipeline/tests/test_clustering.py -q` |
| **Full suite command** | `python -m pytest pipeline/tests -q` |
| **Estimated runtime** | quick ~5s · full ~60s (301 tests collected 2026-07-29, +~13 in this phase) |

Frontend validators (14) are unaffected by this phase but must stay green:
`cd site && npm run build && npm run validate` (single chained command — OneDrive gotcha).

---

## Sampling Rate

- **After every task commit:** `python -m pytest pipeline/tests/test_clustering.py -q`
- **After every plan wave:** `python -m pytest pipeline/tests -q`
- **Before verification:** full suite green + 14/14 validators
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|
| CLUS-01 | Golden-set fixture exists, 60–100 labeled pairs (population = all non-excluded pairs including proposed:false), includes cut 2101/2026-07-01 and cut 4102/2026-07-01 buckets, includes exactly-10-pair hand-constructed typo/homophone negative sub-set, every pair carries a `category` and all three CLUS-01 adversarial classes are represented, proposed:false pairs carry a permanently null `cached_verdict` | unit | `pytest pipeline/tests/test_clustering.py::test_golden_set_shape -x` | ✅ | ✅ green (1 passed) |
| CLUS-02 | rapidfuzz pre-filter proposes correct candidate pairs, drops unrelated titles; `bucket_incidents` is the single shared `(cut,date)` grouping function | unit | `pytest pipeline/tests/test_clustering.py -k "prefilter or bucket_incidents" -x` | ✅ | ✅ green (passed) |
| CLUS-03 | Unparseable / off-schema LLM output rejected as no-merge, with machine-detectable `source`/`rationale` fail-safe provenance | unit | `pytest pipeline/tests/test_clustering.py::test_adjudicate_pair_rejects_malformed -x` | ✅ | ✅ green (1 passed) |
| CLUS-04 | Injected instruction text inside a headline cannot flip the verdict | unit | `pytest pipeline/tests/test_clustering.py::test_prompt_injection_resistance -x` | ✅ | ✅ green (1 passed) |
| CLUS-05 | `cluster_id` byte-identical across runs with shuffled input order; sha256 of sorted member IDs | unit | `pytest pipeline/tests/test_clustering.py::test_cluster_id_deterministic -x` | ✅ | ✅ green (1 passed) |
| CLUS-06 | Cluster >4 members flagged, never silently published; pairwise matrix logged | unit | `pytest pipeline/tests/test_clustering.py::test_oversized_cluster_flagged -x` | ✅ | ✅ green (1 passed) |
| CLUS-07 | Pairwise precision from golden-set cached verdicts, computed via `compute_pairwise_metrics` with an honest zero-denominator guard and a proposed:false skip guard (never reads cached_verdict on those pairs); recall + cost + confidence distribution reported | integration (offline) | `pytest pipeline/tests/test_clustering.py::test_golden_set_meets_go_gate -x` | ✅ | ✅ green (1 xfailed, strict — honest NO-GO signal, exit 0; see 26-SPIKE-REPORT.md) |
| CLUS-08 | Whole clustering test file runs with zero live network calls by default (client patched or `live_llm`-gated); model/prompt staleness caught by a dedicated regression | integration | `pytest pipeline/tests/test_clustering.py -q` | ✅ | ✅ green (30 passed, 1 skipped, 1 xfailed) |
| CLUS-09 | Satisfied via the NO-GO branch: `IncidentRecord` never gains `cluster_id`/`is_primary` this phase; `pipeline/news/schema.py` and `data/` byte-unchanged | regression | `pytest pipeline/tests/test_schema_incidents.py::test_incident_record_has_no_cluster_fields_no_go_branch -x` (replaces the original `-k cluster_fields_optional` command, which selected 0 tests and exited 0 while verifying nothing — W-4) | ✅ | ✅ green (1 passed) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `pipeline/requirements.txt` — add `rapidfuzz==3.14.5` (installed locally but absent from the manifest; clean CI fails on import without it)
- [x] `pipeline/tests/test_clustering.py` — new file, covers CLUS-01..CLUS-08
- [x] `pipeline/tests/fixtures/clustering_golden_set.json` — hand-labeled pairs + cached LLM verdicts (CLUS-01 deliverable; also makes CLUS-07/08 runnable offline)
- [x] `pipeline/tests/conftest.py` — `pytest_configure` registers the `live_llm` marker (`config.addinivalue_line("markers", "live_llm: makes real OpenRouter calls, skipped by default")`) before `test_golden_set_live_reeval` is collected
- [x] Backward-compat test case for CLUS-09 in the existing incident-schema test file (`test_incident_record_has_no_cluster_fields_no_go_branch`, added post-review per W-4)
- [x] `pipeline/news/clustering.py` — module under test

---

## Additional Tests Introduced by Revision (26-PREMORTEM.md amendments + revision cycle 2)

| Test | Plan/Task | Type | Automated Command | Default state |
|---|---|---|---|---|
| `test_golden_set_metrics_match_recorded_baseline` | 26-03 T2 | unit (offline) | `pytest pipeline/tests/test_clustering.py::test_golden_set_metrics_match_recorded_baseline -x` | always green — internal-consistency sentinel against `meta.baseline` |
| `test_golden_set_meets_go_gate` | 26-03 T2 | integration (offline) | `pytest pipeline/tests/test_clustering.py::test_golden_set_meets_go_gate -x` | honest GO/NO-GO signal; on NO-GO gains `@pytest.mark.xfail(strict=True)` in 26-04 T1 — never weakened |
| `test_cached_verdicts_match_current_model_config` | 26-03 T2 | unit (offline) | `pytest pipeline/tests/test_clustering.py::test_cached_verdicts_match_current_model_config -x` | always green until model/prompt config drifts from `meta` |
| `test_golden_set_live_reeval` | 26-03 T2 | integration (live, opt-in) | `CLUSTERING_LIVE_EVAL=1 pytest pipeline/tests/test_clustering.py::test_golden_set_live_reeval -m live_llm -x` | skipped by default (`live_llm` marker + env-var gate); hard assertion is `fp == 0` only — any TP/FN drift vs `meta.baseline` is logged, never asserted (model nondeterminism) |
| `test_bucket_incidents_groups_by_cut_date` / `test_prefilter_never_crosses_bucket` | 26-01 T1 | unit (offline) | `pytest pipeline/tests/test_clustering.py -k "bucket_incidents or never_crosses_bucket" -x` | always run, offline |
| `test_call_budget_refuses_to_start` | 26-02 T3 | unit (offline, stubbed counter) | `pytest pipeline/tests/test_clustering.py::test_call_budget_refuses_to_start -x` | **required** — always run, offline; with a stubbed `last_cumulative_total + projected > 2000` the fill loop must refuse to start and write a NO-GO-by-cost row |

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|---|---|---|---|
| Golden-set ground-truth labels are *correct* (not merely present) | CLUS-01 | Ground truth is a human/Fable judgement over article text; no oracle exists to automate it | Fable orchestrator reviews the labeled pairs for the two mandatory hard buckets (2101, 4102) and the typo/homophone sub-set against the article titles/URLs, records acceptance in the spike report |
| Blind second pass on every `merge`-labeled pair | CLUS-01 | Requires an independent subagent judgment with no access to the first pass's label or `cached_verdict`; cannot be scripted as a pytest assertion since it is itself a labeling judgment, not a code check | `26-02-PLAN.md` Task 2: spawn a separate subagent (Agent tool) per `merge`-labeled pair (batching permitted), seeing only `title_a/title_b/outlet_a/outlet_b/url_a/url_b`; record `second_pass_confirmed`/downgrade/`excluded` outcome on the pair incrementally; Fable orchestrator spot-checks the confirmation count against `26-SPIKE-REPORT.md`'s `merge-labels independently confirmed: N/N` line |
| Live-LLM run cost and call count | CLUS-01/CLUS-07 | Requires real OpenRouter calls; capped at ≤2,000 cumulative for the whole phase per directive, enforced via the `26-CALL-LOG.md` append-only ledger | One-time (resumable) live run logged to the phase dir with cumulative call count + `total_possible_in_bucket_pairs`, written on every exit path (try/finally); the pytest gate then runs offline against the cached verdicts |

---

## Validation Sign-Off

- [x] All tasks have automated verify or a Wave 0 dependency
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references, including `live_llm` marker registration
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** APPROVED 2026-07-29 — gsd-verifier (Opus), `26-VERIFICATION.md`: status passed, 5/5 ROADMAP success criteria verified, 9/9 CLUS-01..CLUS-09 requirements satisfied (CLUS-09 via the documented NO-GO branch). `python -m pytest pipeline/tests -q` independently re-run: 317 passed, 1 skipped, 1 xfailed (strict), exit 0, at time of verification. Post-review-fix (code-review 8 HIGH + verification 4 warnings addressed): 331 passed, 1 skipped, 1 xfailed, exit 0.
</content>
