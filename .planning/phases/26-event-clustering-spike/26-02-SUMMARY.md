---
phase: 26-event-clustering-spike
plan: 02
subsystem: pipeline/news (event clustering — CLUS-01 golden set)
tags: [clustering, golden-set, openrouter, granite, evaluation-fixture]
dependency-graph:
  requires: ["26-01"]
  provides: ["pipeline/tests/fixtures/clustering_golden_set.json", "pipeline/scripts/build_golden_set.py --fill-verdicts"]
  affects: ["pipeline/news/clustering.py (adjudicate_pair parse-recovery fix)"]
tech-stack:
  added: []
  patterns:
    - "append-only cumulative call ledger with try/finally logging on every exit path"
    - "json.JSONDecoder().raw_decode() recovery for LLM outputs with trailing prose after valid JSON"
key-files:
  created:
    - pipeline/tests/fixtures/clustering_golden_set.json
    - .planning/phases/26-event-clustering-spike/26-CALL-LOG.md
  modified:
    - pipeline/scripts/build_golden_set.py
    - pipeline/news/clustering.py
    - pipeline/tests/test_clustering.py
    - .planning/phases/26-event-clustering-spike/26-golden-set-draft.json
decisions:
  - "Fixed a reproducible clustering.py bug found during the live fill: the model sometimes emits valid JSON followed by trailing prose despite the 'SOLO JSON' instruction (deterministic at temp=0.0 for one pair); adjudicate_pair now recovers the leading JSON object via raw_decode instead of fail-safing on otherwise-valid output (Rule 1/3 deviation, not architectural)."
  - "Budget guard (_budget_guard) is a standalone, network-free function so test_call_budget_refuses_to_start can assert the refusal path without any live call, while fill_verdicts still calls it inline before the mandatory preflight probe."
  - ".env must be loaded before importing pipeline.news.clustering, since that module constructs its OpenAI client at import time from os.environ — moved the dotenv load to the top of build_golden_set.py, before the clustering import, to avoid a permanent placeholder-key auth failure for the whole process."
metrics:
  duration: "~35 min"
  completed: "2026-07-29"
  live_calls_this_run: 2
  cumulative_ledger_total: 105
---

# Phase 26 Plan 02: CLUS-01 Golden Set — Task 3 (Live Verdict Fill) Summary

Implemented `build_golden_set.py --fill-verdicts`: a mandatory single-call preflight (dotenv load, API-key emptiness/placeholder check, one probe call that aborts the whole task if `source != "model"`), an append-only budget ledger with a refuse-to-start guard under the phase's 2,000-call cap, and a resumable/idempotent fill loop that populates `cached_verdict` on every `proposed: true` pair (94 of 94) via live `adjudicate_pair()` calls against `ibm-granite/granite-4.1-8b` — while `proposed: false` pairs (none existed in this draft) are structurally never entered into the loop. Finalized `pipeline/tests/fixtures/clustering_golden_set.json` and both required tests.

## What Was Built

- **`pipeline/scripts/build_golden_set.py`** — `--fill-verdicts` mode:
  - `.env` loaded at module top (before importing `pipeline.news.clustering`, whose OpenAI client is constructed at import time from `os.environ`).
  - `_check_api_key()` rejects empty/`"placeholder"` `OPENROUTER_API_KEY` before any call.
  - `_budget_guard()` — pure, network-free function: reads `26-CALL-LOG.md`'s last `cumulative_total` (seeding the ledger with the 3-call spike-ping baseline if absent), refuses to start (raising `BudgetExceededError` and appending a `NO-GO-by-cost` row) if `last_cumulative + projected > 2000`.
  - Preflight probe call against a trivial synthetic pair; aborts the entire task via `SystemExit` if the returned verdict's `source != "model"`.
  - Fill loop: skips pairs already carrying a `source=="model"` `cached_verdict` (idempotent resume), resolves incidents from `current.json` by ID (or the synthesized `incident_a`/`incident_b` dicts for the typo/homophone sub-set), persists the draft to disk every 10 pairs, retries once on a non-model outcome (mirrors `classifier.py`'s hand-rolled retry, no `tenacity`), and aborts after 3 consecutive non-model outcomes.
  - `try/finally` around the whole flow appends a ledger row on every exit path (refusal, preflight abort, early abort, failed-pairs-non-empty, or success).
  - On success, writes the final fixture with the required `meta` block (`model`, `base_url`, `system_prompt_sha256`, `max_tokens`, `temperature`, `mergeable_rule`, `generated`, `calls`, `selected_buckets`, `total_pairs`) and preserves `meta.blind_second_pass` from the draft verbatim.

- **`pipeline/tests/fixtures/clustering_golden_set.json`** — final committed fixture: 94 pairs total, 86 non-excluded (8 carry `excluded: "label_disputed"` from the blind second pass, per F-13), every non-excluded `proposed: true` pair has a `cached_verdict` dict with `source == "model"`.

- **`pipeline/tests/test_clustering.py`** — added `test_golden_set_shape` (60-100 non-excluded pairs, both-direction `cached_verdict` checks, mandatory-bucket representation, all three CLUS-01 categories represented), `test_call_budget_refuses_to_start` (fully offline, stubs `_read_last_cumulative_total`, asserts `adjudicate_pair` is never called and a `NO-GO-by-cost` row is appended), and a regression test for the parse-recovery fix below.

- **`pipeline/news/clustering.py`** (bug fix, discovered live during the fill run) — `adjudicate_pair` now recovers a leading JSON verdict via `json.JSONDecoder().raw_decode()` when the model appends trailing prose after an otherwise-valid JSON object, instead of fail-safing. This was reproducible/deterministic at `temperature=0.0` for one specific pair (`4102-2026-07-01-585fb5-e499c4`) across 6 consecutive calls before the fix.

## Live Run

- **Actual live call count this run: 2** (final successful invocation — after the fix; two prior invocations spent 1 + 96 + 3 = 100 calls on preflight aborts and the one stubborn parse-failure pair before the `clustering.py` fix was applied).
- **Cumulative ledger total: 105** (3 spike-ping baseline + 1 + 96 + 3 + 2), well under the 2,000-call phase budget.
- `total_possible_in_bucket_pairs`: 99 (recorded in every ledger row from `draft["meta"]["total_pairs"]`).
- `data/` directory verified byte-unchanged (`git diff --stat -- data/` empty).
- Full suite: `python -m pytest pipeline/tests -q` → 315 passed (312 baseline + 3 new tests).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `adjudicate_pair` fail-safed on valid JSON followed by trailing prose**
- **Found during:** live fill loop, pair `4102-2026-07-01-585fb5-e499c4` (Tongoy 8-article bucket).
- **Issue:** At `temperature=0.0`, the Granite model deterministically returned a syntactically valid `ClusterVerdict` JSON object followed by an unsolicited "**Explicación detallada**" prose block, which `json.loads` rejected as trailing data (`JSONDecodeError: Extra data`), causing a permanent `failsafe_parse` verdict for this pair across 6 consecutive live calls (2 in the fill loop's built-in retry, 4 in manual reproduction).
- **Fix:** `adjudicate_pair` now falls back to `json.JSONDecoder().raw_decode()` on a `JSONDecodeError`, recovering the leading JSON object and ignoring trailing content. Still fail-safes on genuinely malformed JSON at position 0 (`raw_decode` raises the same way `loads` does in that case) — strictly more permissive, never less.
- **Files modified:** `pipeline/news/clustering.py`, `pipeline/tests/test_clustering.py` (regression test added).
- **Commit:** `525bb8e`

**2. [Rule 3 - Blocking] `.env` loaded too late, permanently binding the OpenAI client to the placeholder key**
- **Found during:** first live preflight attempt — `OpenRouter auth failed` despite a valid key present in `.env`.
- **Issue:** `pipeline.news.clustering` constructs its module-level `client = OpenAI(api_key=os.environ.get("OPENROUTER_API_KEY", "placeholder"), ...)` at import time. `build_golden_set.py`'s original design called `load_dotenv()` inside `fill_verdicts()`, which runs after the `from pipeline.news.clustering import ...` statement at the top of the file — so the client was permanently bound to `"placeholder"` for the whole process regardless of any later env-var fix.
- **Fix:** Moved the `dotenv` load to the top of `build_golden_set.py`, immediately after the `REPO_ROOT` sys.path shim and before the `pipeline.news.clustering` import.
- **Files modified:** `pipeline/scripts/build_golden_set.py`.
- **Commit:** `525bb8e`

No architectural changes; no Rule 4 escalations.

## Known Stubs

None. This plan produces a static evaluation fixture, not runtime UI/data flow.

## Threat Flags

None — no new network endpoints, auth paths, or trust-boundary changes beyond what the plan's `<threat_model>` already anticipated (T-26-05, T-26-06, T-26-07, T-26-13, T-26-14, all mitigated as designed).

## Self-Check: PASSED

- `pipeline/tests/fixtures/clustering_golden_set.json` — FOUND
- `.planning/phases/26-event-clustering-spike/26-CALL-LOG.md` — FOUND
- `pipeline/scripts/build_golden_set.py` — FOUND (contains `fill_verdicts`, `_budget_guard`)
- Commit `525bb8e` — FOUND in `git log --oneline`
- `python -m pytest pipeline/tests -q` — 315 passed
- `git diff --stat -- data/` — empty
