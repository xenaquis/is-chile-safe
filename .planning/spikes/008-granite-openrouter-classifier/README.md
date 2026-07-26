---
spike: 008
name: granite-openrouter-classifier
type: comparison
validates: "Given the labelled golden set (47 items), when the production classifier prompt runs on Granite 4.1 8B via OpenRouter, then commune/family/null metrics match or beat the DeepSeek v4-flash baseline at lower cost"
verdict: VALIDATED
related: [ab_score NEWS-02 harness (Phase 16)]
tags: [news, llm, classifier, openrouter, granite, cost]
---

# Spike 008: Granite 4.1 8B (OpenRouter) as news classifier

## What This Validates

Given the labelled golden set (`pipeline/tests/fixtures/golden_set.json`, 47 items:
44 labelled + 3 null), when the **production prompt/parse path**
(`pipeline.news.classifier`) runs against `ibm-granite/granite-4.1-8b` on
OpenRouter, then metrics should match/beat the DeepSeek v4-flash baseline
(`pipeline/results/ab_deepseek.json`) at ~6x lower cost. If not → discard.

## Research

- OpenRouter models API (2026-07-26): `ibm-granite/granite-4.1-8b`, ctx 131k,
  **$0.05/1M in, $0.10/1M out** — vs DeepSeek v4-flash $0.27/$1.10 (≈6x cheaper on
  input, 11x on output).
- Single endpoint only: **CoreWeave, bf16** (`/models/.../endpoints`). No routing
  variance across providers — but see nondeterminism finding below.
- Reused Phase 16 A/B methodology (`pipeline/experiments/ab_score.py`) verbatim:
  same golden set, same metrics, same resolver. Spike scripts monkeypatch the
  classifier module (client/model/prompt) — **production code untouched**.

## How to Run

```bash
# Full golden-set eval (production prompt + family-whitespace fix):
python .planning/spikes/008-granite-openrouter-classifier/run_granite_golden.py --normalize-family

# With the is_crime_incident-first prompt variant:
python .planning/spikes/008-granite-openrouter-classifier/run_granite_golden.py --normalize-family --variant-prompt

# Null-guard / traffic-accident probes (raw JSON output, prompt A/B):
python .planning/spikes/008-granite-openrouter-classifier/probe_null_guard.py
```

Requires `OPENROUTER_API_KEY` in repo-root `.env`. Cost per full run ≈ $0.006.

## What to Expect

Per-item `cut OK/X` + `fam OK/X` lines, then a metrics block comparable 1:1 with
`pipeline/results/ab_deepseek.json`.

## Investigation Trail

1. **Smoke (3 items, raw prompt):** 100% parse failure — Granite emits
   `"robos_ violentos"` (space inside enum token). `response_format=json_object`
   does NOT fix it (JSON is valid; the enum string is what's broken). It is a
   tokenizer artifact, deterministic across items.
2. **Fix:** strip internal whitespace in `family` before Pydantic validation
   (1-line deterministic guard). Parse failures → 0.
3. **Full run #1 (production prompt):** commune 100% (beats DeepSeek 95.45%),
   family 65.91% (= DeepSeek exactly), latency 1.4s (vs 3.7s), **null_rate 33%
   (vs 100%)** — Granite extracted communes for a recycling campaign and a
   hospital inauguration instead of obeying the "non-crime → confidence 0.0" rule.
4. **Probe:** small model ignores buried rules. Variant prompt adding
   `is_crime_incident` as FIRST output field + explicit rule → all 5 non-crime/
   traffic probes correct (confidence 0.0), crime control intact. Also fixed an
   atropello the production prompt scored 0.95.
5. **Full run with variant:** null 2/3, commune 95.45%. Initially suspected
   endpoint nondeterminism vs the probe — WRONG: the probe used truncated
   descriptions. With identical inputs the endpoint is **perfectly deterministic**
   (3 runs per prompt, byte-identical metrics and identical failing items).
6. **Variant commune misses are genuine extraction errors** (headline says Tomé →
   predicted Talcahuano; says Coquimbo → predicted La Serena), reproducible 3/3.
   The production prompt gets both right 3/3. The is_crime-first field slightly
   degrades extraction attention.
7. **Null-guard deficit is not production-relevant:** all 3 golden null items fail
   the keyword pre-filter (`pipeline.news.feeds.is_crime_item`) and would never
   reach the LLM. The real exposure is keyword-passing non-crime (traffic with
   "muerto"/"fallecido", court-phase stories) — and on the 147 production
   incidents Granite **rejected 4+ traffic-accident items that DeepSeek had
   accepted into current.json** (e.g. "Colisión deja al menos un muerto…",
   "Fallecido en accidente en Concepción…"). Granite's traffic guard ≥ DeepSeek's
   on real data. Known edge: an atropello probe passes at 0.95 with the
   production prompt.

## Results

3 runs per configuration — fully deterministic (identical metrics and items each run):

| config | commune | family | null (golden) | parse fail | mean lat | cost/1M in/out |
|---|---|---|---|---|---|---|
| DeepSeek v4-flash (baseline, Phase 16) | 95.45% | 65.91% | 100% | 4.26% | 3695ms | $0.27 / $1.10 |
| **Granite 4.1 8B, production prompt** | **100%** | 65.91% | 33%* | **0%** | ~1380ms | **$0.05 / $0.10** |
| Granite 4.1 8B, is_crime-first variant | 95.45% | 65.91% | 67%* | 0% | ~1500ms | $0.05 / $0.10 |

\* not production-relevant — all golden nulls are blocked by the keyword pre-filter
before the LLM (see trail #7).

Secondary check (147 production incidents, title_es-only proxy input): 18 rejected
(mostly traffic/court items — several are DeepSeek false-accepts), cut agreement
81.4%, family agreement 72.9% of accepted. Weak signal (degraded input, DeepSeek
output ≠ ground truth) but no red flags.

**VERDICT: VALIDATED — adopt Granite 4.1 8B via OpenRouter with the production
prompt unchanged.** Required adoption changes:
1. `classifier.py`: add `NEWS_PROVIDER=openrouter` block (base_url
   `https://openrouter.ai/api/v1`, key `OPENROUTER_API_KEY`, model
   `ibm-granite/granite-4.1-8b`, no response_format) and make it the default.
2. `classifier.py`: normalize whitespace inside the `family` value before Pydantic
   validation (Granite tokenizer artifact; benign for other providers).
3. GitHub Actions: add `OPENROUTER_API_KEY` repo secret + env in
   `scrape-news.yml` (DeepSeek stays available via `NEWS_PROVIDER=deepseek`).

## Observability

Each run writes full per-item JSON (`results_*.json`) with predicted vs
ground-truth CUT/family, confidence, and per-item latency.

## Notes / Side findings

- **Golden-set label quality is questionable**: gs-001..003 are portonazos/asaltos
  labelled `family: vida`; both DeepSeek and Granite predict `robos_violentos`.
  The 65.91% family ceiling both models hit is partly a *label* problem, not a
  model problem. Worth a separate data-quality pass on
  `pipeline/tests/fixtures/golden_set.json`.
- Production incidents (`data/incidents/current.json`, 147 items) store only
  processed output (title_es/cut/family), not the original RSS text — they can't
  serve as re-runnable golden inputs without re-fetching the source articles.
