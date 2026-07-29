---
phase: 26
slug: event-clustering-spike
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-29
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `26-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.* (`pipeline/requirements.txt`) |
| **Config file** | none dedicated — discovery via `pipeline/tests/test_*.py`; shared fixtures in `pipeline/tests/conftest.py` |
| **Quick run command** | `python -m pytest pipeline/tests/test_clustering.py -q` |
| **Full suite command** | `python -m pytest pipeline/tests -q` |
| **Estimated runtime** | quick ~5s · full ~60s (301 tests collected 2026-07-29) |

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
| CLUS-01 | Golden-set fixture exists, 60–100 labeled pairs, includes cut 2101/2026-07-01 and cut 4102/2026-07-01 buckets | unit | `pytest pipeline/tests/test_clustering.py::test_golden_set_shape -x` | ❌ W0 | ⬜ pending |
| CLUS-02 | rapidfuzz pre-filter proposes correct candidate pairs, drops unrelated titles | unit | `pytest pipeline/tests/test_clustering.py::test_prefilter_candidates -x` | ❌ W0 | ⬜ pending |
| CLUS-03 | Unparseable / off-schema LLM output rejected as no-merge | unit | `pytest pipeline/tests/test_clustering.py::test_adjudicate_pair_rejects_malformed -x` | ❌ W0 | ⬜ pending |
| CLUS-04 | Injected instruction text inside a headline cannot flip the verdict | unit | `pytest pipeline/tests/test_clustering.py::test_prompt_injection_resistance -x` | ❌ W0 | ⬜ pending |
| CLUS-05 | `cluster_id` byte-identical across runs with shuffled input order; sha256 of sorted member IDs | unit | `pytest pipeline/tests/test_clustering.py::test_cluster_id_deterministic -x` | ❌ W0 | ⬜ pending |
| CLUS-06 | Cluster >4 members flagged, never silently published; pairwise matrix logged | unit | `pytest pipeline/tests/test_clustering.py::test_oversized_cluster_flagged -x` | ❌ W0 | ⬜ pending |
| CLUS-07 | Pairwise precision from golden-set cached verdicts == 1.0; recall + cost reported | integration (offline) | `pytest pipeline/tests/test_clustering.py::test_golden_set_precision_100pct -x` | ❌ W0 | ⬜ pending |
| CLUS-08 | Whole clustering test file runs with zero live network calls (client patched) | integration | `pytest pipeline/tests/test_clustering.py -q` | ❌ W0 | ⬜ pending |
| CLUS-09 | `IncidentRecord` with `cluster_id=None, is_primary=False` still validates existing `current.json` / archive shape | regression | `pytest pipeline/tests -k backward_compat -x` | ⚠️ extend existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pipeline/requirements.txt` — add `rapidfuzz==3.14.5` (installed locally but absent from the manifest; clean CI fails on import without it)
- [ ] `pipeline/tests/test_clustering.py` — new file, covers CLUS-01..CLUS-08
- [ ] `pipeline/tests/fixtures/clustering_golden_set.json` — hand-labeled pairs + cached LLM verdicts (CLUS-01 deliverable; also makes CLUS-07/08 runnable offline)
- [ ] Backward-compat test case for CLUS-09 in the existing incident-schema test file
- [ ] `pipeline/news/clustering.py` — module under test

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|---|---|---|---|
| Golden-set ground-truth labels are *correct* (not merely present) | CLUS-01 | Ground truth is a human/Fable judgement over article text; no oracle exists to automate it | Fable orchestrator reviews the labeled pairs for the two mandatory hard buckets (2101, 4102) against the article titles/URLs, records acceptance in the spike report |
| Live-LLM run cost and call count | CLUS-07 | Requires real OpenRouter calls; capped at ≤2,000 for the whole phase per directive | One-time live run logged to the phase dir with call count + token totals; the pytest gate then runs offline against the cached verdicts |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or a Wave 0 dependency
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
