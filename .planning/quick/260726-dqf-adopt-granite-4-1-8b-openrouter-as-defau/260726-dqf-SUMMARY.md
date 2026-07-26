---
phase: quick-260726-dqf
plan: "01"
subsystem: pipeline/news
tags: [classifier, openrouter, granite, cost-reduction, provider-switch]
dependency_graph:
  requires: [spike-008-granite-openrouter-classifier]
  provides: [openrouter-default-provider, family-whitespace-normalization]
  affects: [pipeline/news/classifier.py, .github/workflows/news-pipeline.yml]
tech_stack:
  added: []
  patterns:
    - OpenRouter as OpenAI-compatible client (base_url=https://openrouter.ai/api/v1)
    - Three-branch provider selection (openrouter default, deepseek, minimax)
    - Family whitespace normalization guard before Pydantic validation
key_files:
  modified:
    - pipeline/news/classifier.py
    - pipeline/tests/test_classifier.py
    - pipeline/tests/test_classifier_traffic.py
    - .github/workflows/news-pipeline.yml
decisions:
  - OpenRouter/Granite 4.1 8B adopted as default (spike 008 validated: 100% commune accuracy, ~6x cheaper, ~2.5x faster than DeepSeek)
  - api_key falls back to literal 'placeholder' string when env var unset, allowing module import in tests without credentials
  - No NEWS_PROVIDER override in workflow — code default is openrouter, so Granite runs automatically
metrics:
  duration: ~8m
  completed: "2026-07-26"
  tasks: 3
  files: 4
---

# Phase quick-260726-dqf Plan 01: Adopt Granite 4.1 8B via OpenRouter as Default News Classifier

**One-liner:** OpenRouter/ibm-granite/granite-4.1-8b replaces DeepSeek as the default news classifier — 100% commune accuracy, ~6x cheaper, zero prompt changes, with a defensive family whitespace normalization guard for the Granite tokenizer artifact "robos_ violentos".

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add OpenRouter default provider + family whitespace normalization | 465e519 | pipeline/news/classifier.py |
| 2 | Update tests: openrouter default + whitespace normalization test | 914e997 | pipeline/tests/test_classifier.py, pipeline/tests/test_classifier_traffic.py |
| 3 | Wire OPENROUTER_API_KEY into news-pipeline workflow | 0dc42f7 | .github/workflows/news-pipeline.yml |

## What Was Done

**classifier.py changes:**
- Provider selection block refactored from 2 branches (minimax/deepseek) to 3 explicit branches (deepseek/minimax/openrouter) with openrouter as the default when NEWS_PROVIDER is unset or unrecognized
- Default: `_PROVIDER="openrouter"`, `_MODEL="ibm-granite/granite-4.1-8b"`, `base_url="https://openrouter.ai/api/v1"`, api_key from `OPENROUTER_API_KEY`
- DeepSeek and MiniMax remain selectable via `NEWS_PROVIDER=deepseek` / `NEWS_PROVIDER=minimax`
- `_call_api()` already gated `response_format` on `_PROVIDER == "deepseek"` — openrouter correctly follows the fence-stripping path with no changes needed
- `classify()` now normalizes `data["family"]` with `"".join(value.split())` after `json.loads` and before `model_validate`, turning "robos_ violentos" into "robos_violentos" (Granite tokenizer artifact per spike 008)
- Module header docstring updated with three-provider table, family-whitespace guard documentation, and spike 008 reference
- api_key falls back to `"placeholder"` (not `""`) to satisfy OpenAI client minimum credential requirement

**Tests:**
- `test_family_internal_whitespace_normalized`: mocked response with `family="robos_ violentos"` asserts `result.family == "robos_violentos"`
- `test_default_provider_is_openrouter`: asserts `_PROVIDER == "openrouter"` and `_MODEL == "ibm-granite/granite-4.1-8b"` at module load
- Header docstrings in both test files updated from "DeepSeek NEVER called live" to provider-neutral "The configured LLM provider is NEVER called live"

**Workflow:**
- `OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}` added to "Run news scraper" step env alongside `DEEPSEEK_API_KEY`
- No `NEWS_PROVIDER` override added — code default is now openrouter

## Deviations from Plan

**1. [Rule 1 - Bug] api_key placeholder instead of empty string**
- **Found during:** Task 1 verification
- **Issue:** OpenAI client v1.x raises `OpenAIError: Missing credentials` when `api_key=""` — newer SDK version than when deepseek/minimax branches were written
- **Fix:** Changed all three provider branches to use `"placeholder"` as the env var default instead of `""`. The placeholder is never sent to any API in tests (client is mocked); in production, the real secret overrides it
- **Files modified:** pipeline/news/classifier.py
- **Commit:** 465e519 (included in same task commit)

## Verification

- `python -m pytest pipeline/tests/test_classifier.py pipeline/tests/test_classifier_traffic.py -q` — 9 passed
- `_PROVIDER == "openrouter"` and `_MODEL == "ibm-granite/granite-4.1-8b"` with `NEWS_PROVIDER` unset — confirmed
- `OPENROUTER_API_KEY` and `DEEPSEEK_API_KEY` both present in scrape step env — confirmed via yaml parse
- `SYSTEM_PROMPT` unchanged from spike baseline — no edits to the prompt constant

## Known Stubs

None. No placeholder data or TODO wiring outstanding.

## Threat Flags

None. No new network endpoints or auth paths introduced — the OpenRouter client is used identically to the existing DeepSeek pattern (OpenAI SDK, api_key from env var, no new trust boundaries).

## Operator Next Steps

- Add `OPENROUTER_API_KEY` secret to GitHub repo Settings > Secrets > Actions (source: https://openrouter.ai/keys)
- The next scheduled news-pipeline run will automatically use Granite 4.1 8B
- DeepSeek remains available as `NEWS_PROVIDER=deepseek` for comparison or fallback

## Self-Check: PASSED

- pipeline/news/classifier.py — FOUND
- pipeline/tests/test_classifier.py — FOUND
- pipeline/tests/test_classifier_traffic.py — FOUND
- .github/workflows/news-pipeline.yml — FOUND
- Commits 465e519, 914e997, 0dc42f7 — verified in git log
