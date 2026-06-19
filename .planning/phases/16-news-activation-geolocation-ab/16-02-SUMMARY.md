---
phase: 16-news-activation-geolocation-ab
plan: "02"
subsystem: pipeline/news
tags: [news, classifier, ab-test, golden-set, geolocation]
dependency_graph:
  requires: ["16-01"]
  provides: ["golden_set.json", "ab_score.py", "NEWS_PROVIDER-configurable classifier"]
  affects: ["pipeline/news/classifier.py", "pipeline/news/schema.py", "pipeline/experiments/ab_score.py"]
tech_stack:
  added: []
  patterns:
    - "NEWS_PROVIDER env selects provider at module import; deepseek default"
    - "MiniMax: no response_format=json_object; strip markdown fences from content"
    - "region_hint coerced int→str in Pydantic validator (LLM emits integer region IDs)"
key_files:
  created:
    - pipeline/tests/fixtures/golden_set.json
    - pipeline/experiments/ab_score.py
  modified:
    - pipeline/news/classifier.py
    - pipeline/news/schema.py
decisions:
  - "NEWS_PROVIDER env var read at classifier module import time; reload() used in ab_score to support per-invocation provider switching"
  - "region_hint coerced to str via Pydantic mode=before validator — LLM reliably emits integer region IDs that match region_id in index.json"
  - "MiniMax omits response_format=json_object (returns HTTP 400); JSON stripped from markdown fences via regex anchored ^/$ with re.DOTALL"
  - "Pricing constants marked [ASSUMED] A1/A2 — deepseek-v4-flash $0.27/$1.10 per 1M in/out; MiniMax-Text-01 $0.80/$1.60 per 1M in/out"
metrics:
  duration: "~20m"
  completed: "2026-06-18"
  tasks_completed: 2
  tasks_pending: 1
  files_changed: 4
---

# Phase 16 Plan 02: A/B Golden Set + Harness Summary

Provider-configurable classifier (NEWS_PROVIDER env), 47-item labelled golden set, and 5-metric A/B scoring harness — all key-free. Live A/B run gated at Task 3 (orchestrator checkpoint with API keys).

## Tasks Completed

### Task 1: golden_set.json + NEWS_PROVIDER-configurable classifier
**Commit:** dc9a786

- `pipeline/tests/fixtures/golden_set.json`: 47 labelled incidents; 44 labelled (commune + family), 3 null/non-crime items.
- Coverage: major cities (Santiago/Las Condes/Providencia/Valparaíso/Concepción), smaller communes (Cochamó/Quintero/Tomé), all 7 crime families (vida, propiedad, drogas, vif, armas, incivilidades), Punta Arenas (region 12).
- `pipeline/news/classifier.py` refactored: `_PROVIDER = os.environ.get("NEWS_PROVIDER", "deepseek")`; client + `_MODEL` constructed conditionally; `_call_api` omits `response_format` for MiniMax and strips markdown fences; deepseek default preserved.
- All 11 existing classifier+resolver tests pass.

### Task 2: ab_score.py scoring harness + schema bugfix
**Commit:** 827fd10

- `pipeline/experiments/ab_score.py`: CLI harness with argparse (`--provider`, `--golden`, `--output`); 5 metrics: `commune_accuracy`, `family_accuracy`, `null_rate`, `parse_failure_rate`, `mean_latency_ms`, plus `estimated_cost_usd` (pricing [ASSUMED] A1/A2).
- Imports `resolve_cut` from `pipeline/news/resolver.py`; compares `predicted_cut == ground_truth.cut`.
- No import-time API call (all logic under `if __name__ == "__main__"`).
- Graceful key-absent exit with clear message + `sys.exit(1)`.
- Writes JSON to `results/ab_{provider}.json`; prints markdown table to stdout.
- **Deviation (Rule 1 — Bug):** `ClassifierOutput.region_hint: str | None` was failing when LLM emitted integer region IDs (e.g., `6`, `12`). Fixed by adding a `mode="before"` Pydantic validator that coerces to `str`. All 15 tests still pass.

## Task 3 — Pending Checkpoint

Task 3 (live A/B run, DeepSeek vs MiniMax) is a `checkpoint:human-verify` with `gate="blocking-human"`. This task requires `DEEPSEEK_API_KEY` + `MINIMAX_API_KEY` and was NOT executed by this agent. The orchestrator will run it inline with the keys and document the winner in `16-VERIFICATION.md`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] region_hint integer coercion in ClassifierOutput**
- **Found during:** Task 2 (background ab_score.py run with real DeepSeek key surfaced the error)
- **Issue:** `ClassifierOutput.region_hint` typed as `str | None` but DeepSeek reliably emits integer region_ids (e.g., `6` for O'Higgins). Pydantic v2 rejects this with `Input should be a valid string`.
- **Fix:** Added `@field_validator("region_hint", mode="before")` in `schema.py` that converts non-None values to `str`.
- **Files modified:** `pipeline/news/schema.py`
- **Commit:** 827fd10

## Known Stubs

None — golden_set.json uses real CUT codes from index.json; no placeholder data.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes at trust boundaries beyond those already in the plan's threat model (T-16-04 through T-16-SC).

## Self-Check: PASSED

- `pipeline/tests/fixtures/golden_set.json` — exists, 47 items, 3 null-commune
- `pipeline/experiments/ab_score.py` — exists, parses, `commune_accuracy` present, no import-time API call
- `pipeline/news/classifier.py` — `NEWS_PROVIDER` present, default `deepseek-v4-flash`
- `pipeline/news/schema.py` — `region_hint` coercion validator present
- Commits dc9a786, 827fd10 — verified in git log
