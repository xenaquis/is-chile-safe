"""
pipeline/experiments/eval_classifier.py

Model-parameterized eval runner for NREC-01 (34-01, V-08). Scores any
provider/model pair against the golden set through the SAME production seam
`classify()` uses (`_request_completion` / `_parse_content` in
`pipeline/news/classifier.py`), then picks a winner mechanically under
G-02/G-06/G-08/G-10/G-13 (see .planning/v2.2-AUTONOMOUS-DIRECTIVE.md § Decision
log). The orchestrator does not choose by hand — `select_winner()` is a pure,
unit-tested function.

Usage
-----
  # Probe the reasoning-disable flag (3 golden items x each candidate variant):
  python pipeline/experiments/eval_classifier.py --probe --provider openrouter \\
      --model deepseek/deepseek-v4-flash

  # Full 47-item run (uses the probe's chosen variant):
  python pipeline/experiments/eval_classifier.py --provider openrouter \\
      --model deepseek/deepseek-v4-flash --reasoning auto

  # Mechanically decide the winner from every run-*.json in --out-dir:
  python pipeline/experiments/eval_classifier.py --decide

Why a new file instead of extending ab_score.py: see 34-01-PLAN.md objective.
`ab_score.py` stays untouched (imports the classifier through module globals,
one provider per process; no usage/reasoning capture; no spend meter).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
from typing import Any

import requests
from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

# ---------------------------------------------------------------------------
# sys.path bootstrap (mirrors ab_score.py:56-58)
# ---------------------------------------------------------------------------

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pipeline.news import classifier as classifier_mod  # noqa: E402

# ---------------------------------------------------------------------------
# G-10/G-15: family threshold. Re-scored Phase-16 DeepSeek baseline on
# golden_set_v2.json (Task 0, 34-GOLDEN-V2-RELABEL.md), recorded as G-15.
# select_winner() raises if this is ever unset and no explicit override is
# passed (defensive — Task 0 already landed this value).
# ---------------------------------------------------------------------------
FAMILY_MIN_V2 = 40  # G-15 (re-scored Phase-16 DeepSeek baseline on golden_set_v2, /44)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_GOLDEN = _REPO_ROOT / "pipeline" / "tests" / "fixtures" / "golden_set_v2.json"
DEFAULT_OUT_DIR = _REPO_ROOT / ".planning" / "phases" / "34-news-classification-restore" / "ab"
RESULTS_JSON = _REPO_ROOT / ".planning" / "phases" / "34-news-classification-restore" / "34-AB-RESULTS.json"
RESULTS_MD = _REPO_ROOT / ".planning" / "phases" / "34-news-classification-restore" / "34-AB-RESULTS.md"

PROBE_ITEM_IDS = ("gs-001", "gs-002", "gs-003")

REASONING_ORDER: dict[str, list[str]] = {
    "openrouter": ["enabled_false", "effort_none", "none"],
    "deepseek": ["thinking_disabled", "none"],
}

VARIANT_EXTRA_BODY: dict[str, dict | None] = {
    "none": None,
    "enabled_false": {"reasoning": {"enabled": False}},
    "effort_none": {"reasoning": {"effort": "none"}},
    "thinking_disabled": {"thinking": {"type": "disabled"}},
}

# DeepSeek direct pricing (docs pricing page, fetched 2026-09-22): input cache-miss
# 0.15 off-peak / 0.30 peak, output 0.60 / 1.20, per 1M tokens. endpoints is null —
# DeepSeek direct is not an OpenRouter catalog entry.
DEEPSEEK_DIRECT_PRICING: dict[str, Any] = {
    "endpoints": None,
    "in_min": 0.15,
    "in_median": 0.225,
    "in_max": 0.30,
    "out_min": 0.60,
    "out_median": 0.90,
    "out_max": 1.20,
    "response_format_all_endpoints": None,
    "source": "https://api-docs.deepseek.com/quick_start/pricing",
}

# Per-call spend ceiling assumption (measured this session): 4,500 input tokens
# (o200k + 20% tokenizer margin + template) and 512 output tokens (max_tokens).
CEILING_INPUT_TOKENS = 4_500
CEILING_OUTPUT_TOKENS = 512


def _slug(provider: str, model: str) -> str:
    """D-R2-08 slug rule: '/' and '.' -> '-'; 'direct-' prefix for DeepSeek direct.

    deepseek/deepseek-v4-flash (openrouter) -> deepseek-deepseek-v4-flash
    deepseek-v4-flash (deepseek direct)     -> direct-deepseek-v4-flash
    """
    base = model.replace("/", "-").replace(".", "-")
    return f"direct-{base}" if provider == "deepseek" else base


# ---------------------------------------------------------------------------
# Spend ledger (T-34-03) — persists across processes via a JSON file rewritten
# atomically after every call.
# ---------------------------------------------------------------------------


def load_ledger(path: pathlib.Path) -> dict:
    path = pathlib.Path(path)
    if not path.exists():
        return {"total_usd": 0.0, "calls": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_ledger(path: pathlib.Path, ledger: dict) -> None:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def spend_cap_allows(ledger_total: float, ceiling_next_call: float, spend_cap: float) -> bool:
    """Abort BEFORE a call that could cross the cap.

    The rule aborts only when total + ceiling > cap; the boundary (== cap) is allowed.
    Rounded to 8 decimals to avoid float noise at the exact-cap boundary.
    """
    return round(ledger_total + ceiling_next_call, 8) <= round(spend_cap, 8)


def call_ceiling_usd(pricing: dict) -> float:
    """Per-call ceiling = 4,500 input tokens x max_in + 512 output tokens x max_out."""
    max_in = pricing.get("in_max") or 0.0
    max_out = pricing.get("out_max") or 0.0
    return (CEILING_INPUT_TOKENS * max_in + CEILING_OUTPUT_TOKENS * max_out) / 1_000_000.0


def _check_and_load_ledger(
    ledger_path: pathlib.Path, spend_cap: float, ceiling_next_call: float
) -> tuple[bool, dict]:
    """Load the ledger fresh from disk (so totals survive process boundaries) and
    check the cap for the next call. Returns (allowed, ledger)."""
    ledger = load_ledger(ledger_path)
    allowed = spend_cap_allows(ledger.get("total_usd", 0.0), ceiling_next_call, spend_cap)
    return allowed, ledger


def record_charge(ledger_path: pathlib.Path, ledger: dict, model: str, variant: str, usd: float) -> None:
    ledger["total_usd"] = round(ledger.get("total_usd", 0.0) + usd, 8)
    ledger.setdefault("calls", []).append(
        {"model": model, "variant": variant, "usd": usd, "ts": time.time()}
    )
    save_ledger(ledger_path, ledger)


# ---------------------------------------------------------------------------
# Transient network-error retry (G-03 numbers): stop_after_attempt(3),
# waits 2s then 4s (wait_exponential(multiplier=2, exp_base=2, max=20)).
# ---------------------------------------------------------------------------


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (APIConnectionError, RateLimitError, InternalServerError)):
        return True
    status = getattr(exc, "status_code", None)
    return status is not None and (status == 429 or 500 <= status < 600)


def _call_once(client: OpenAI, model: str, provider: str, user_content: str, extra_body: dict | None):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, exp_base=2, max=20),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
    )
    def _inner():
        return classifier_mod._request_completion(client, model, provider, user_content, extra_body)

    return _inner()


def _content_of(resp: Any) -> str | None:
    try:
        return resp.choices[0].message.content
    except Exception:
        return None


def _finish_reason_of(resp: Any) -> str | None:
    try:
        return resp.choices[0].finish_reason
    except Exception:
        return None


def _served_by_of(resp: Any) -> str | None:
    provider_field = getattr(resp, "provider", None)
    if provider_field:
        return provider_field
    return getattr(resp, "model", None)


def _usage_fields(resp: Any) -> dict:
    usage = getattr(resp, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
    reasoning_tokens = 0
    details = getattr(usage, "completion_tokens_details", None) if usage else None
    if details is not None:
        reasoning_tokens = getattr(details, "reasoning_tokens", 0) or 0
    return {
        "prompt_tokens": prompt_tokens or 0,
        "completion_tokens": completion_tokens or 0,
        "reasoning_tokens": reasoning_tokens or 0,
    }


def _usage_usd(resp: Any, pricing: dict) -> tuple[float, bool]:
    usage = getattr(resp, "usage", None)
    cost = getattr(usage, "cost", None) if usage else None
    if cost is not None:
        return float(cost), True
    fields = _usage_fields(resp)
    usd = (
        fields["prompt_tokens"] * (pricing.get("in_max") or 0.0)
        + fields["completion_tokens"] * (pricing.get("out_max") or 0.0)
    ) / 1_000_000.0
    return usd, False


def _guarded_call(
    client: OpenAI,
    model: str,
    provider: str,
    variant: str,
    user_content: str,
    extra_body: dict | None,
    ledger_path: pathlib.Path,
    spend_cap: float,
    pricing: dict,
) -> tuple[str, Any, float, bool]:
    """Returns (status, resp_or_none, usd_charged, usage_cost_present).

    status: "ok" | "aborted_cap" | "api_error"
    """
    ceiling = call_ceiling_usd(pricing)
    allowed, ledger = _check_and_load_ledger(ledger_path, spend_cap, ceiling)
    if not allowed:
        return "aborted_cap", None, 0.0, False
    try:
        resp = _call_once(client, model, provider, user_content, extra_body)
    except Exception:
        return "api_error", None, 0.0, False
    usd, usage_cost_present = _usage_usd(resp, pricing)
    record_charge(ledger_path, ledger, model, variant, usd)
    return "ok", resp, usd, usage_cost_present


# ---------------------------------------------------------------------------
# Per-item classification through the production seam (mirrors classify()'s
# single immediate re-call on empty content — classifier.py:162-166 — and
# G-13's transient handling for finish_reason == "length").
# ---------------------------------------------------------------------------


def _classify_one_item(
    client: OpenAI,
    model: str,
    provider: str,
    variant: str,
    extra_body: dict | None,
    headline: str,
    description: str,
    ledger_path: pathlib.Path,
    spend_cap: float,
    pricing: dict,
) -> dict:
    user_content = f"HEADLINE: {headline}\nSUMMARY: {description[:500]}"
    t0 = time.perf_counter()

    status, resp, usd, usage_cost_present = _guarded_call(
        client, model, provider, variant, user_content, extra_body, ledger_path, spend_cap, pricing
    )
    if status == "aborted_cap":
        return {"kind": "aborted_cap"}
    if status == "api_error":
        return {"kind": "api_error", "latency_ms": (time.perf_counter() - t0) * 1000.0}

    content = _content_of(resp)
    finish_reason = _finish_reason_of(resp)
    empty_first_try = 0

    if not content:
        empty_first_try = 1
        status2, resp2, usd2, usage_cost_present2 = _guarded_call(
            client, model, provider, variant, user_content, extra_body, ledger_path, spend_cap, pricing
        )
        if status2 == "aborted_cap":
            return {"kind": "aborted_cap"}
        if status2 == "api_error":
            return {"kind": "api_error", "latency_ms": (time.perf_counter() - t0) * 1000.0}
        resp = resp2
        usd += usd2
        usage_cost_present = usage_cost_present or usage_cost_present2
        content = _content_of(resp)
        finish_reason = _finish_reason_of(resp)
        if not content:
            return {
                "kind": "transient",
                "reason": "empty_after_recall",
                "empty_first_try": empty_first_try,
                "latency_ms": (time.perf_counter() - t0) * 1000.0,
                "usd": usd,
                "usage_cost_present": usage_cost_present,
                "served_by": _served_by_of(resp),
                "finish_reason": finish_reason,
                **_usage_fields(resp),
            }

    if finish_reason == "length":
        return {
            "kind": "transient",
            "reason": "finish_length",
            "empty_first_try": empty_first_try,
            "latency_ms": (time.perf_counter() - t0) * 1000.0,
            "usd": usd,
            "usage_cost_present": usage_cost_present,
            "served_by": _served_by_of(resp),
            "finish_reason": finish_reason,
            **_usage_fields(resp),
        }

    kind, out = classifier_mod._parse_content(content, headline)
    return {
        "kind": kind,
        "out": out,
        "empty_first_try": empty_first_try,
        "latency_ms": (time.perf_counter() - t0) * 1000.0,
        "usd": usd,
        "usage_cost_present": usage_cost_present,
        "served_by": _served_by_of(resp),
        "finish_reason": finish_reason,
        **_usage_fields(resp),
    }


# ---------------------------------------------------------------------------
# Probe mode: choose the reasoning-disable variant empirically.
# ---------------------------------------------------------------------------


def choose_probe_variant(per_variant: dict[str, dict], order: list[str]) -> tuple[str, bool]:
    """Pick the first variant with reasoning_tokens_total==0 AND empty==0 AND
    api_errors==0. If none qualifies, pick the first variant with empty==0.
    If none qualifies again, mark "reasoning_unfixable" (NB-02) and use order[0].
    """
    for variant in order:
        s = per_variant.get(variant)
        if s and s.get("reasoning_tokens_total", 0) == 0 and s.get("empty", 0) == 0 and s.get("api_errors", 0) == 0:
            return variant, False
    for variant in order:
        s = per_variant.get(variant)
        if s and s.get("empty", 0) == 0:
            return variant, False
    return order[0], True


def probe_model(
    client: OpenAI,
    model: str,
    provider: str,
    golden_items: list[dict],
    ledger_path: pathlib.Path,
    spend_cap: float,
    pricing: dict,
    out_dir: pathlib.Path | None = None,
) -> dict:
    order = REASONING_ORDER[provider]
    probe_items = [it for it in golden_items if it["id"] in PROBE_ITEM_IDS]

    per_variant: dict[str, dict] = {}
    for variant in order:
        extra_body = VARIANT_EXTRA_BODY[variant]
        reasoning_tokens_total = 0
        empty = 0
        api_errors = 0
        for item in probe_items:
            res = _classify_one_item(
                client, model, provider, variant, extra_body,
                item["headline"], item["description"], ledger_path, spend_cap, pricing,
            )
            if res["kind"] in ("aborted_cap", "api_error"):
                api_errors += 1
                continue
            reasoning_tokens_total += res.get("reasoning_tokens", 0)
            if res["kind"] == "transient" and res.get("reason") == "empty_after_recall":
                empty += 1
        per_variant[variant] = {
            "reasoning_tokens_total": reasoning_tokens_total,
            "empty": empty,
            "api_errors": api_errors,
        }

    chosen_variant, reasoning_unfixable = choose_probe_variant(per_variant, order)
    result = {
        "provider": provider,
        "model": model,
        "chosen_variant": chosen_variant,
        "chosen_extra_body": VARIANT_EXTRA_BODY[chosen_variant],
        "reasoning_unfixable": reasoning_unfixable,
        "per_variant": per_variant,
    }
    if out_dir is not None:
        slug = _slug(provider, model)
        path = pathlib.Path(out_dir) / f"probe-{slug}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


# ---------------------------------------------------------------------------
# Full mode: score all 47 items — mirrors ab_score.py metric definitions.
# ---------------------------------------------------------------------------


def run_full(
    client: OpenAI,
    model: str,
    provider: str,
    variant: str,
    golden_items: list[dict],
    ledger_path: pathlib.Path,
    spend_cap: float,
    pricing: dict,
    endpoints: int | None = None,
) -> dict:
    from pipeline.news.resolver import resolve_cut  # noqa: PLC0415

    extra_body = VARIANT_EXTRA_BODY[variant]

    per_item: list[dict] = []
    commune_correct = 0
    family_correct = 0
    parse_errors = 0
    null_correct = 0
    empty_first_try_total = 0
    empty_content_count = 0
    finish_length_count = 0
    api_errors = 0
    transient = 0
    reasoning_tokens_total = 0
    latencies: list[float] = []
    prompt_tokens_list: list[float] = []
    completion_tokens_list: list[float] = []
    served_by_counts: dict[str, int] = {}
    spend_usd = 0.0
    usage_cost_present_any = False
    aborted = False

    for item in golden_items:
        gt = item["ground_truth"]
        is_labelled = gt.get("commune_name") is not None

        res = _classify_one_item(
            client, model, provider, variant, extra_body,
            item["headline"], item["description"], ledger_path, spend_cap, pricing,
        )

        if res["kind"] == "aborted_cap":
            aborted = True
            break

        row: dict[str, Any] = {"id": item["id"]}

        if res["kind"] == "api_error":
            api_errors += 1
            row["status"] = "api_error"
            per_item.append(row)
            continue

        spend_usd += res.get("usd", 0.0)
        usage_cost_present_any = usage_cost_present_any or res.get("usage_cost_present", False)
        empty_first_try_total += res.get("empty_first_try", 0)
        served_by = res.get("served_by")
        if served_by:
            served_by_counts[served_by] = served_by_counts.get(served_by, 0) + 1
        latencies.append(res.get("latency_ms", 0.0))
        prompt_tokens_list.append(res.get("prompt_tokens", 0))
        completion_tokens_list.append(res.get("completion_tokens", 0))
        reasoning_tokens_total += res.get("reasoning_tokens", 0)

        row["finish_reason"] = res.get("finish_reason")
        row["served_by"] = served_by
        row["prompt_tokens"] = res.get("prompt_tokens", 0)
        row["completion_tokens"] = res.get("completion_tokens", 0)
        row["reasoning_tokens"] = res.get("reasoning_tokens", 0)
        row["latency_ms"] = round(res.get("latency_ms", 0.0), 1)
        if is_labelled:
            row["ground_truth_family"] = gt.get("family")

        if res["kind"] == "transient":
            transient += 1
            api_errors += 1
            if res.get("reason") == "empty_after_recall":
                empty_content_count += 1
                row["status"] = "transient_empty"
            else:
                finish_length_count += 1
                row["status"] = "transient_finish_length"
            per_item.append(row)
            continue

        if res["kind"] == "parse_error":
            # G-13: parse_errors counts only non-empty, non-truncated content
            # that fails _parse_content — over ALL 47 items, not just labelled.
            parse_errors += 1
            row["status"] = "parse_error"
            per_item.append(row)
            continue

        out = res["out"]
        if is_labelled:
            resolved = resolve_cut(out.commune_name, out.region_hint) if out else None
            predicted_cut = resolved[0] if resolved else None
            commune_match = predicted_cut == gt.get("cut")
            family_match = bool(out) and out.family == gt.get("family")
            if res["kind"] == "low_conf":
                row["status"] = "low_conf"
            else:
                row["status"] = "ok"
                if commune_match:
                    commune_correct += 1
                if family_match:
                    family_correct += 1
            row["predicted_commune_name"] = out.commune_name if out else None
            row["predicted_cut"] = predicted_cut
            row["predicted_family"] = out.family if out else None
            row["commune_match"] = commune_match
            row["family_match"] = family_match
        else:
            is_null_correct = res["kind"] == "low_conf" or (res["kind"] == "ok" and out.commune_name is None)
            if is_null_correct:
                null_correct += 1
            row["status"] = "null_item"
            row["null_correct"] = is_null_correct
            row["predicted_commune_name"] = out.commune_name if out else None

        per_item.append(row)

    n_total = len(golden_items)
    n_labelled = len([it for it in golden_items if it["ground_truth"].get("commune_name") is not None])
    n_null = n_total - n_labelled

    # transient is a subset of api_errors (G-13); a candidate goes INCOMPLETE
    # only when NON-transient API errors remain after the retry pass (D-R2-04).
    incomplete = (api_errors - transient) > 0

    mean_prompt = sum(prompt_tokens_list) / len(prompt_tokens_list) if prompt_tokens_list else 0.0
    mean_completion = sum(completion_tokens_list) / len(completion_tokens_list) if completion_tokens_list else 0.0
    mean_latency = sum(latencies) / len(latencies) if latencies else 0.0

    blended_usd_per_item = (
        mean_prompt * (pricing.get("in_min") or 0.0) + mean_completion * (pricing.get("out_min") or 0.0)
    ) / 1_000_000.0

    candidate = {
        "provider": provider,
        "model": model,
        "slug": _slug(provider, model),
        "reasoning_variant": variant,
        "reasoning_extra_body": extra_body,
        "endpoints": endpoints if endpoints is not None else pricing.get("endpoints"),
        "commune_correct": commune_correct,
        "family_correct": family_correct,
        "parse_errors": parse_errors,
        "null_correct": null_correct,
        "n_total": n_total,
        "n_labelled": n_labelled,
        "n_null": n_null,
        "empty_first_try": empty_first_try_total,
        "empty_content_count": empty_content_count,
        "finish_length_count": finish_length_count,
        "api_errors": api_errors,
        "transient": transient,
        "reasoning_tokens_total": reasoning_tokens_total,
        "mean_latency_ms": round(mean_latency, 1),
        "mean_prompt_tokens": round(mean_prompt, 1),
        "mean_completion_tokens": round(mean_completion, 1),
        "served_by_counts": served_by_counts,
        "spend_usd": round(spend_usd, 6),
        "usage_cost_present": usage_cost_present_any,
        "blended_usd_per_item": round(blended_usd_per_item, 6),
        "response_format_all_endpoints": pricing.get("response_format_all_endpoints"),
        "status": "INCOMPLETE" if incomplete else "COMPLETE",
        "aborted_spend_cap": aborted,
        "reasoning_unfixable": False,
        "per_item": per_item,
        "pricing": pricing,
    }
    return candidate


# ---------------------------------------------------------------------------
# G-02/G-06/G-08/G-10/G-13 selection (select_winner is the mechanical,
# unit-tested rule — the orchestrator does not choose by hand).
# ---------------------------------------------------------------------------


def _disqualify_reasons(candidate: dict, family_min: int, tier: str) -> list[str]:
    if candidate.get("status") != "COMPLETE":
        return ["incomplete"]

    reasons: list[str] = []
    if candidate.get("reasoning_unfixable"):
        reasons.append("reasoning_unfixable")
    # G-13: truncation/empty disqualify in BOTH tiers, whatever reasoning_tokens reports.
    if candidate.get("finish_length_count", 0) > 0:
        reasons.append("transient_truncation")
    if candidate.get("empty_content_count", 0) > 0:
        reasons.append("transient_empty")

    if tier == "strict":
        if candidate.get("commune_correct", 0) < 42:
            reasons.append("commune")
        if candidate.get("family_correct", 0) < family_min:
            reasons.append("family")
        if candidate.get("parse_errors", 0) > 0:
            reasons.append("parse_fail")
        if (candidate.get("endpoints") or 0) < 2:
            reasons.append("endpoints")
    else:  # G-08 fallback tier
        if (candidate.get("endpoints") or 0) < 2:
            reasons.append("endpoints")
        if candidate.get("parse_errors", 0) > 1:
            reasons.append("parse_fail")
        if candidate.get("commune_correct", 0) < 41:
            reasons.append("commune")

    return reasons


def _winner_payload(candidate: dict) -> dict:
    return {
        "model": candidate.get("model"),
        "provider": candidate.get("provider"),
        "reasoning_variant": candidate.get("reasoning_variant"),
        "reasoning_extra_body": candidate.get("reasoning_extra_body"),
        "endpoints": candidate.get("endpoints"),
        "family_correct": candidate.get("family_correct"),
        "commune_correct": candidate.get("commune_correct"),
    }


def select_winner(
    candidates: list[dict],
    backup: dict | None = None,
    family_min_v2: int | None = None,
) -> dict:
    """G-02/G-06 strict tier, then G-08 fallback tiers (G-10 family threshold,
    G-13 transient disqualification). Pure function — deterministic under input
    order. `backup` is the DeepSeek-direct informational row; never eligible to
    win, but its measured reasoning variant seeds the DEEPSEEK_DIRECT decision.
    """
    if family_min_v2 is None:
        family_min_v2 = FAMILY_MIN_V2
    if family_min_v2 is None:
        raise ValueError(
            "FAMILY_MIN_V2 is not set (Task 0 pending) — pass family_min_v2 explicitly "
            "or set the module constant from its G-NN."
        )

    annotated = []
    for c in candidates:
        strict_reasons = _disqualify_reasons(c, family_min_v2, "strict")
        fallback_reasons = _disqualify_reasons(c, family_min_v2, "fallback")
        annotated.append({
            **c,
            "disqualified_by_strict": strict_reasons,
            "disqualified_by_fallback": fallback_reasons,
            "qualifies_strict": len(strict_reasons) == 0,
            "qualifies_fallback": len(fallback_reasons) == 0,
        })

    complete = [c for c in annotated if c.get("status") == "COMPLETE"]
    if candidates and not complete:
        return {
            "candidates": annotated,
            "decision": {
                "status": "INCOMPLETE",
                "no_qualifier": True,
                "winner": None,
                "tie_set": [],
                "reason": "every candidate is INCOMPLETE",
                "rule_applied": None,
            },
        }

    qualifiers = [c for c in annotated if c["qualifies_strict"]]
    if qualifiers:
        max_family = max(c["family_correct"] for c in qualifiers)
        tie_set = [c for c in qualifiers if c["family_correct"] >= max_family - 1]
        tie_set_sorted = sorted(
            tie_set,
            key=lambda c: (
                -(c.get("endpoints") or 0),
                c.get("blended_usd_per_item", float("inf")),
                c.get("model", ""),
            ),
        )
        winner = tie_set_sorted[0]
        return {
            "candidates": annotated,
            "decision": {
                "status": "WINNER",
                "no_qualifier": False,
                "winner": _winner_payload(winner),
                "tie_set": [c.get("model") for c in tie_set],
                "reason": f"max family_correct={max_family} among strict qualifiers (G-02/G-06/G-10)",
                "rule_applied": "G-02/G-06",
            },
        }

    # G-08 fallback tier 1: FALLBACK_WINNER
    fallback_pool = [c for c in complete if c["qualifies_fallback"]]
    if fallback_pool:
        fallback_sorted = sorted(
            fallback_pool,
            key=lambda c: (
                c.get("parse_errors", 0),
                -c.get("commune_correct", 0),
                -c.get("family_correct", 0),
                -(c.get("endpoints") or 0),
            ),
        )
        winner = fallback_sorted[0]
        return {
            "candidates": annotated,
            "decision": {
                "status": "FALLBACK_WINNER",
                "no_qualifier": True,
                "winner": _winner_payload(winner),
                "tie_set": [],
                "reason": "G-08 fallback: no strict qualifier",
                "rule_applied": "G-08",
            },
        }

    # G-08 fallback tier 2: DEEPSEEK_DIRECT
    backup_variant = backup.get("reasoning_variant") if backup else None
    backup_extra_body = backup.get("reasoning_extra_body") if backup else None
    return {
        "candidates": annotated,
        "decision": {
            "status": "DEEPSEEK_DIRECT",
            "no_qualifier": True,
            "winner": {
                "provider": "deepseek",
                "model": "deepseek-v4-flash",
                "reasoning_variant": backup_variant,
                "reasoning_extra_body": backup_extra_body,
            },
            "tie_set": [],
            "reason": "G-08 fallback: no strict or fallback-tier qualifier",
            "rule_applied": "G-08",
        },
    }


# ---------------------------------------------------------------------------
# Catalog fetch
# ---------------------------------------------------------------------------


def _median(xs: list[float]) -> float | None:
    if not xs:
        return None
    n = len(xs)
    mid = n // 2
    return xs[mid] if n % 2 else (xs[mid - 1] + xs[mid]) / 2


def fetch_catalog(provider: str, model: str) -> dict:
    """GET the OpenRouter endpoints catalog for `model`, or the hardcoded
    DeepSeek-direct pricing constants (no catalog for direct API access)."""
    if provider == "deepseek":
        return dict(DEEPSEEK_DIRECT_PRICING)

    resp = requests.get(f"https://openrouter.ai/api/v1/models/{model}/endpoints", timeout=15)
    resp.raise_for_status()
    data = resp.json()
    endpoints = (data.get("data") or {}).get("endpoints") or []

    in_prices: list[float] = []
    out_prices: list[float] = []
    supports_response_format: list[bool] = []
    for ep in endpoints:
        pricing = ep.get("pricing") or {}
        try:
            in_prices.append(float(pricing.get("prompt", 0)) * 1_000_000)
        except (TypeError, ValueError):
            pass
        try:
            out_prices.append(float(pricing.get("completion", 0)) * 1_000_000)
        except (TypeError, ValueError):
            pass
        supports_response_format.append("response_format" in (ep.get("supported_parameters") or []))

    in_prices.sort()
    out_prices.sort()

    return {
        "endpoints": len(endpoints),
        "in_min": in_prices[0] if in_prices else None,
        "in_median": _median(in_prices),
        "in_max": in_prices[-1] if in_prices else None,
        "out_min": out_prices[0] if out_prices else None,
        "out_median": _median(out_prices),
        "out_max": out_prices[-1] if out_prices else None,
        "response_format_all_endpoints": bool(endpoints) and all(supports_response_format),
    }


# ---------------------------------------------------------------------------
# Decide mode
# ---------------------------------------------------------------------------


def _family_confusion_matrix(candidate: dict) -> dict[str, dict[str, int]]:
    matrix: dict[str, dict[str, int]] = {}
    for row in candidate.get("per_item", []):
        gtf = row.get("ground_truth_family")
        if gtf is None:
            continue
        pf = str(row.get("predicted_family"))
        matrix.setdefault(gtf, {})
        matrix[gtf][pf] = matrix[gtf].get(pf, 0) + 1
    return matrix


def _write_results_md(result: dict) -> None:
    rows = list(result.get("candidates", []))
    backup = result.get("backup")

    lines = [
        "# 34-AB-RESULTS",
        "",
        f"Generated: {result.get('generated')}",
        f"Rule: {result.get('rule')}",
        "",
        "## A/B table",
        "",
        "| model | commune | family | parse_errors | endpoints | status | disqualified_by (strict) |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in rows:
        dq = ", ".join(c.get("disqualified_by_strict", []))
        lines.append(
            f"| {c.get('model')} | {c.get('commune_correct')}/44 | {c.get('family_correct')}/44 "
            f"| {c.get('parse_errors')}/47 | {c.get('endpoints')} | {c.get('status')} | {dq} |"
        )
    if backup:
        lines.append(
            f"| {backup.get('model')} (backup) | {backup.get('commune_correct')}/44 | "
            f"{backup.get('family_correct')}/44 | {backup.get('parse_errors')}/47 | "
            f"{backup.get('endpoints')} | {backup.get('status')} | not eligible (backup) |"
        )

    lines += ["", "## Served-by providers seen", ""]
    for c in rows + ([backup] if backup else []):
        served = c.get("served_by_counts", {})
        lines.append(f"- {c.get('model')}: {sorted(served.keys())}")

    lines += ["", "## Family confusion matrix per candidate", ""]
    for c in rows + ([backup] if backup else []):
        lines.append(f"### {c.get('model')}")
        matrix = _family_confusion_matrix(c)
        if not matrix:
            lines.append("_(no per_item family rows)_")
        for gtf, preds in sorted(matrix.items()):
            row_str = ", ".join(f"{pf}={n}" for pf, n in sorted(preds.items()))
            lines.append(f"- {gtf}: {row_str}")
        lines.append("")

    d = result.get("decision", {})
    lines += ["## Decision", "", f"**{d.get('status')}** — {d.get('reason')} (rule {d.get('rule_applied')})"]
    if d.get("winner"):
        lines.append(f"\nWinner: `{json.dumps(d['winner'], ensure_ascii=False)}`")
    lines.append(f"\nspend_total_usd: {result.get('spend_total_usd')}")

    RESULTS_MD.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def decide(out_dir: pathlib.Path, family_min_v2: int | None = None) -> dict:
    out_dir = pathlib.Path(out_dir)
    run_files = sorted(out_dir.glob("run-*.json"))

    candidates: list[dict] = []
    backup: dict | None = None
    for f in run_files:
        c = json.loads(f.read_text(encoding="utf-8"))
        try:
            fresh = fetch_catalog(c["provider"], c["model"])
            c["endpoints"] = fresh.get("endpoints")
        except Exception:
            pass  # keep the run-time endpoint count if the refresh fails
        if c.get("provider") == "deepseek":
            backup = c
        else:
            candidates.append(c)

    result = select_winner(candidates, backup=backup, family_min_v2=family_min_v2)
    result["rule"] = "G-02/G-06/G-08/G-10/G-13"
    result["generated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    result["backup"] = backup
    result["spend_total_usd"] = round(
        sum(c.get("spend_usd", 0.0) for c in candidates) + (backup.get("spend_usd", 0.0) if backup else 0.0),
        6,
    )

    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_results_md(result)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _load_env() -> None:
    load_dotenv(_REPO_ROOT / "pipeline" / ".env", override=False)
    load_dotenv(_REPO_ROOT / ".env", override=False)


def _make_client(provider: str) -> OpenAI:
    if provider == "deepseek":
        return OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY", "placeholder"),
            base_url="https://api.deepseek.com",
            max_retries=0,
            timeout=30.0,
        )
    return OpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", "placeholder"),
        base_url="https://openrouter.ai/api/v1",
        max_retries=0,
        timeout=30.0,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Model-parameterized eval runner (NREC-01, 34-01 V-08).",
    )
    parser.add_argument("--provider", choices=["openrouter", "deepseek"], default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--reasoning",
        choices=["auto", "none", "enabled_false", "effort_none", "thinking_disabled"],
        default="auto",
    )
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--golden", default=str(DEFAULT_GOLDEN))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--spend-ledger", default=None)
    parser.add_argument("--spend-cap", type=float, default=0.50)
    parser.add_argument("--decide", action="store_true")
    args = parser.parse_args(argv)

    _load_env()

    out_dir = pathlib.Path(args.out_dir)
    ledger_path = pathlib.Path(args.spend_ledger) if args.spend_ledger else out_dir / "spend-ledger.json"

    if args.decide:
        result = decide(out_dir, family_min_v2=FAMILY_MIN_V2)
        status = result["decision"]["status"]
        print(status)
        return 0 if status != "INCOMPLETE" else 1

    if not args.provider or not args.model:
        parser.error("--provider and --model are required unless --decide")

    golden_items = json.loads(pathlib.Path(args.golden).read_text(encoding="utf-8"))
    client = _make_client(args.provider)
    pricing = fetch_catalog(args.provider, args.model)
    slug = _slug(args.provider, args.model)

    if args.probe:
        result = probe_model(
            client, args.model, args.provider, golden_items, ledger_path, args.spend_cap, pricing, out_dir=out_dir
        )
        print(result["chosen_variant"])
        return 0

    if args.reasoning == "auto":
        probe_path = out_dir / f"probe-{slug}.json"
        if not probe_path.exists():
            print(f"No probe JSON for {slug}; run --probe first", file=sys.stderr)
            return 2
        probe_data = json.loads(probe_path.read_text(encoding="utf-8"))
        variant = probe_data["chosen_variant"]
        reasoning_unfixable = probe_data.get("reasoning_unfixable", False)
    else:
        variant = args.reasoning
        reasoning_unfixable = False

    candidate = run_full(client, args.model, args.provider, variant, golden_items, ledger_path, args.spend_cap, pricing)
    candidate["reasoning_unfixable"] = reasoning_unfixable

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"run-{slug}.json").write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")

    if candidate.get("aborted_spend_cap"):
        print("ABORTED_SPEND_CAP")
        return 3

    print(candidate["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
