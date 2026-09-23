"""
pipeline/news/model_config.py

Single source of truth for the news-pipeline model ids and the measured
reasoning-disable request bodies (NREC-02, Phase 34-02).

stdlib only, NO side effects on import (no clients, no file reads, no network):
both pipeline/news/classifier.py and pipeline/news/clustering.py import it.

Provenance — values copied VERBATIM from
.planning/phases/34-news-classification-restore/34-AB-RESULTS.json:
  decision.status == "WINNER" (strict tier, G-02/G-06/G-10/G-13), recorded as
  G-16 in .planning/v2.2-AUTONOMOUS-DIRECTIVE.md § Decision log:
    decision.winner.model                = deepseek/deepseek-v4.1-flash
    decision.winner.reasoning_extra_body = {"reasoning": {"enabled": false}}
    backup.reasoning_extra_body          = {"thinking": {"type": "disabled"}}
  (G-08 DEEPSEEK_DIRECT branch not taken: status is WINNER, so the primary is
  OpenRouter and DeepSeek direct is the backup.)

Env overrides resolve through resolve(): an empty string — which is what an
unset GitHub repo variable / secret arrives as — falls back to the default (R-09).
"""
from __future__ import annotations

import os

# G-16 WINNER → primary provider is OpenRouter (G-08: "deepseek" only on DEEPSEEK_DIRECT).
DEFAULT_PROVIDER: str = "openrouter"

# G-16: 34-AB-RESULTS.json decision.winner.model
DEFAULT_OPENROUTER_MODEL: str = "deepseek/deepseek-v4.1-flash"

# DeepSeek direct backup model (api.deepseek.com, DEEPSEEK_API_KEY) — NREC-04.
DEFAULT_BACKUP_MODEL: str = "deepseek-v4-flash"

# G-16: 34-AB-RESULTS.json decision.winner.reasoning_extra_body (measured, variant enabled_false)
REASONING_EXTRA_BODY_OPENROUTER: dict | None = {"reasoning": {"enabled": False}}

# G-16: 34-AB-RESULTS.json backup.reasoning_extra_body (measured, variant thinking_disabled;
# equals ab/probe-direct-deepseek-v4-flash.json chosen_extra_body)
REASONING_EXTRA_BODY_DEEPSEEK: dict | None = {"thinking": {"type": "disabled"}}


def resolve(env_name: str, default: str) -> str:
    """Return the stripped env value, or `default` when unset OR empty (R-09)."""
    return os.environ.get(env_name, "").strip() or default
