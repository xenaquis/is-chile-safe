# Phase 16 — Model A/B Results (NEWS-02)

**Run:** 2026-06-18 · Golden set: 47 incidents (44 labelled + 3 null/non-crime), 7 crime families · Harness: `pipeline/experiments/ab_score.py` · Raw: `pipeline/results/ab_deepseek.json`, `pipeline/results/ab_minimax.json`

## Result: DeepSeek (`deepseek-v4-flash`) wins → wired as default

| Metric | DeepSeek (`deepseek-v4-flash`) | MiniMax (`MiniMax-Text-01`) | Winner |
|--------|-------------------------------|------------------------------|--------|
| **commune_accuracy** | **0.9545** | 0.9545 | tie |
| family_accuracy | **0.6591** | 0.5227 | DeepSeek |
| null_rate (non-crime correctly → null) | **1.0000** | 0.3333 | DeepSeek |
| parse_failure_rate | 0.0426 | 0.0426 | tie |
| mean_latency_ms | **3695.3** | 4156.7 | DeepSeek |
| estimated_cost_usd (47 items) | **0.0329** | 0.0880 | DeepSeek (~2.7× cheaper) |

## Interpretation

- **The geolocation redesign is validated.** Both providers reach **95.45% comuna accuracy** with the name-emit + deterministic name→CUT resolver — vs the ~30–40% bare-CUT baseline documented in CONTEXT. This confirms NEWS-01's thesis: the bottleneck was the *design* (bare CUT codes), not the vendor. Comuna accuracy clears the >70% target by a wide margin.
- **DeepSeek is the better default** on every non-tied axis: higher family accuracy, perfect non-crime rejection (MiniMax wrongly assigns a comuna to 2/3 non-crime items), lower latency, and ~2.7× lower cost.
- `pipeline/news/classifier.py` default is `os.environ.get("NEWS_PROVIDER", "deepseek")` — already the winner; `NEWS_PROVIDER=minimax` remains available for override.

*Pricing is [ASSUMED] per the ab_score.py module docstring — cost ranking is directionally reliable (MiniMax materially pricier) but the absolute USD figures are estimates.*
