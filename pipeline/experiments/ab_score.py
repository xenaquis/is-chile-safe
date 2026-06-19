"""
pipeline/experiments/ab_score.py

A/B scoring harness for DeepSeek vs MiniMax classifier evaluation (NEWS-02).

Runs the classifier against the labelled golden_set.json and computes 5 metrics:

  1. commune_accuracy   — fraction of labelled items where predicted CUT == ground_truth.cut
  2. family_accuracy    — fraction of labelled items where predicted family == ground_truth.family
  3. null_rate          — fraction of null-commune items correctly classified as commune_name=None
  4. parse_failure_rate — fraction of items where the classifier returned None (API/parse error)
  5. mean_latency_ms    — average wall-clock latency per item (ms)
  6. estimated_cost_usd — token-based cost estimate (see pricing constants below)

Usage
-----
  # From repo root or pipeline/ directory:
  cd pipeline
  NEWS_PROVIDER=deepseek python experiments/ab_score.py --provider deepseek
  NEWS_PROVIDER=minimax  python experiments/ab_score.py --provider minimax

  # Custom paths:
  python experiments/ab_score.py --provider deepseek \\
      --golden tests/fixtures/golden_set.json \\
      --output results/ab_deepseek.json

Provider selection mechanism
-----------------------------
The classifier module reads NEWS_PROVIDER at import time and constructs the client.
This script sets os.environ["NEWS_PROVIDER"] BEFORE importing the classifier, so the
correct provider is selected. Pass --provider to set it; the script validates the key
for the chosen provider before running and exits gracefully if the key is absent.

Output
------
- JSON report written to --output (default: results/ab_{provider}.json)
- Markdown summary table printed to stdout

Pricing constants (token-based estimate)
-----------------------------------------
  DeepSeek v4-flash:  $0.27 / 1M input tokens, $1.10 / 1M output tokens  [ASSUMED - A1]
  MiniMax-Text-01:    $0.80 / 1M input tokens, $1.60 / 1M output tokens  [ASSUMED - A2]
  (Prices as of June 2026; verify at api-docs.deepseek.com / api.minimaxi.chat before billing.)
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time

# Ensure the repo root is on sys.path so `pipeline.*` imports resolve when
# running this script directly (mirrors the pattern used in probe_coverage.py).
_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Pricing constants [ASSUMED per RESEARCH Assumptions A1/A2]
# ---------------------------------------------------------------------------

_PRICING: dict[str, dict[str, float]] = {
    "deepseek": {
        "input_per_1m": 0.27,   # USD per 1M input tokens  [ASSUMED - A1]
        "output_per_1m": 1.10,  # USD per 1M output tokens [ASSUMED - A1]
    },
    "minimax": {
        "input_per_1m": 0.80,   # USD per 1M input tokens  [ASSUMED - A2]
        "output_per_1m": 1.60,  # USD per 1M output tokens [ASSUMED - A2]
    },
}

# Approximate prompt token count (system prompt + commune list is ~2000 tokens)
_ESTIMATED_INPUT_TOKENS_PER_ITEM: int = 2100
_ESTIMATED_OUTPUT_TOKENS_PER_ITEM: int = 120


def _resolve_paths(provider: str, golden: str | None, output: str | None) -> tuple[pathlib.Path, pathlib.Path]:
    """Resolve golden set and output paths relative to the pipeline/ directory."""
    # Determine pipeline root: the parent of the experiments/ directory
    pipeline_root = pathlib.Path(__file__).parent.parent

    golden_path = pathlib.Path(golden) if golden else pipeline_root / "tests" / "fixtures" / "golden_set.json"
    if not golden_path.is_absolute():
        golden_path = pipeline_root / golden_path

    default_output = pipeline_root / "results" / f"ab_{provider}.json"
    output_path = pathlib.Path(output) if output else default_output
    if not output_path.is_absolute():
        output_path = pipeline_root / output_path

    return golden_path, output_path


def _check_key(provider: str) -> bool:
    """Return True if the required API key is present and non-empty."""
    key_name = "DEEPSEEK_API_KEY" if provider == "deepseek" else "MINIMAX_API_KEY"
    return bool(os.environ.get(key_name, "").strip())


def _run_scoring(provider: str, golden_path: pathlib.Path, output_path: pathlib.Path) -> dict:
    """Run the classifier against the golden set and return the metrics dict."""
    # Import classifier AFTER setting NEWS_PROVIDER (it reads the env at import time).
    # importlib.reload() is NOT used: reload() cannot re-initialize module-level objects
    # (e.g. the OpenAI client) reliably across CPython versions, and silently scores the
    # wrong provider in multi-import scenarios.  Each provider MUST be run in a separate
    # process invocation (--provider X per process), which is the documented usage.
    if "pipeline.news.classifier" in sys.modules:
        print(
            f"[ab_score] ERROR: pipeline.news.classifier is already imported in this process "
            f"(possibly with a different provider). "
            f"Run each provider in a separate process invocation:\n"
            f"  NEWS_PROVIDER=deepseek python experiments/ab_score.py --provider deepseek\n"
            f"  NEWS_PROVIDER=minimax  python experiments/ab_score.py --provider minimax",
            file=sys.stderr,
        )
        sys.exit(1)
    import pipeline.news.classifier as classifier_mod
    classify = classifier_mod.classify

    # Import resolver for predicted_name → predicted_cut
    from pipeline.news.resolver import resolve_cut  # noqa: PLC0415

    golden: list[dict] = json.loads(golden_path.read_text(encoding="utf-8"))

    labelled_items = [item for item in golden if item["ground_truth"]["commune_name"] is not None]
    null_items = [item for item in golden if item["ground_truth"]["commune_name"] is None]

    commune_correct = 0
    family_correct = 0
    parse_failures = 0
    latencies_ms: list[float] = []
    per_item_results: list[dict] = []

    # Score labelled items (commune + family)
    for item in labelled_items:
        t0 = time.perf_counter()
        result = classify(item["headline"], item["description"])
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)

        gt = item["ground_truth"]
        if result is None:
            parse_failures += 1
            per_item_results.append({
                "id": item["id"],
                "status": "parse_failure",
                "latency_ms": round(elapsed_ms, 1),
            })
            continue

        # Resolve predicted commune_name → predicted_cut
        resolved = resolve_cut(result.commune_name, result.region_hint)
        predicted_cut = resolved[0] if resolved else None
        commune_match = predicted_cut == gt["cut"]
        family_match = result.family == gt["family"]

        if commune_match:
            commune_correct += 1
        if family_match:
            family_correct += 1

        per_item_results.append({
            "id": item["id"],
            "status": "ok",
            "predicted_commune_name": result.commune_name,
            "predicted_cut": predicted_cut,
            "ground_truth_cut": gt["cut"],
            "commune_match": commune_match,
            "predicted_family": result.family,
            "ground_truth_family": gt["family"],
            "family_match": family_match,
            "confidence": result.confidence,
            "latency_ms": round(elapsed_ms, 1),
        })

    # Score null items (should return commune_name=None or low confidence rejected)
    null_correct = 0
    for item in null_items:
        t0 = time.perf_counter()
        result = classify(item["headline"], item["description"])
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)

        # Correct null prediction: result is None (rejected) OR commune_name is None
        is_null_correct = result is None or result.commune_name is None
        if is_null_correct:
            null_correct += 1

        per_item_results.append({
            "id": item["id"],
            "status": "null_item",
            "null_correct": is_null_correct,
            "predicted_commune_name": result.commune_name if result else None,
            "latency_ms": round(elapsed_ms, 1),
        })

    n_labelled = len(labelled_items)
    n_null = len(null_items)
    n_total = len(golden)

    commune_accuracy = commune_correct / n_labelled if n_labelled else 0.0
    family_accuracy = family_correct / n_labelled if n_labelled else 0.0
    null_rate = null_correct / n_null if n_null else 0.0
    parse_failure_rate = parse_failures / n_total if n_total else 0.0
    mean_latency_ms = sum(latencies_ms) / len(latencies_ms) if latencies_ms else 0.0

    # Cost estimate
    pricing = _PRICING.get(provider, _PRICING["deepseek"])
    total_input_tokens = n_total * _ESTIMATED_INPUT_TOKENS_PER_ITEM
    total_output_tokens = n_total * _ESTIMATED_OUTPUT_TOKENS_PER_ITEM
    estimated_cost_usd = (
        total_input_tokens / 1_000_000 * pricing["input_per_1m"]
        + total_output_tokens / 1_000_000 * pricing["output_per_1m"]
    )

    metrics = {
        "provider": provider,
        "model": classifier_mod._MODEL,
        "golden_set": str(golden_path),
        "n_total": n_total,
        "n_labelled": n_labelled,
        "n_null": n_null,
        "commune_accuracy": round(commune_accuracy, 4),
        "family_accuracy": round(family_accuracy, 4),
        "null_rate": round(null_rate, 4),
        "parse_failure_rate": round(parse_failure_rate, 4),
        "mean_latency_ms": round(mean_latency_ms, 1),
        "estimated_cost_usd": round(estimated_cost_usd, 6),
        "pricing_note": "[ASSUMED] A1/A2 — verify at provider pricing page before billing",
        "per_item": per_item_results,
    }
    return metrics


def _print_markdown_table(metrics: dict) -> None:
    """Print a markdown summary table to stdout."""
    p = metrics["provider"]
    m = metrics["model"]
    print(f"\n## A/B Score Results — {p} ({m})\n")
    print(f"| Metric               | Value                         |")
    print(f"|----------------------|-------------------------------|")
    print(f"| Provider             | {p:<29} |")
    print(f"| Model                | {m:<29} |")
    print(f"| Items (total)        | {metrics['n_total']:<29} |")
    print(f"| Items (labelled)     | {metrics['n_labelled']:<29} |")
    print(f"| Items (null/non-crime)| {metrics['n_null']:<28} |")
    print(f"| commune_accuracy     | {metrics['commune_accuracy']:<29.4f} |")
    print(f"| family_accuracy      | {metrics['family_accuracy']:<29.4f} |")
    print(f"| null_rate            | {metrics['null_rate']:<29.4f} |")
    print(f"| parse_failure_rate   | {metrics['parse_failure_rate']:<29.4f} |")
    print(f"| mean_latency_ms      | {metrics['mean_latency_ms']:<29.1f} |")
    print(f"| estimated_cost_usd   | {metrics['estimated_cost_usd']:<29.6f} |")
    print(f"\n_Pricing: [ASSUMED] A1/A2 — see module docstring for sources._\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="A/B scoring harness for DeepSeek vs MiniMax news classifier (NEWS-02).",
    )
    parser.add_argument(
        "--provider",
        choices=["deepseek", "minimax"],
        default="deepseek",
        help="LLM provider to evaluate (default: deepseek). Sets NEWS_PROVIDER env before import.",
    )
    parser.add_argument(
        "--golden",
        default=None,
        help="Path to golden_set.json (default: pipeline/tests/fixtures/golden_set.json).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write results JSON (default: pipeline/results/ab_{provider}.json).",
    )
    args = parser.parse_args()

    provider = args.provider

    # Set NEWS_PROVIDER BEFORE importing the classifier
    os.environ["NEWS_PROVIDER"] = provider

    # Check for API key
    if not _check_key(provider):
        key_name = "DEEPSEEK_API_KEY" if provider == "deepseek" else "MINIMAX_API_KEY"
        print(
            f"\n[ab_score] Key absent — {key_name} is not set or empty.\n"
            f"Set it in pipeline/.env or export {key_name}=<your-key> and retry.\n"
            f"The golden set and harness are ready; only the live A/B run requires keys.\n",
            file=sys.stderr,
        )
        sys.exit(1)

    golden_path, output_path = _resolve_paths(provider, args.golden, args.output)

    if not golden_path.exists():
        print(f"[ab_score] Golden set not found: {golden_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[ab_score] Provider={provider} | Golden={golden_path} | Output={output_path}")

    metrics = _run_scoring(provider, golden_path, output_path)

    # Write JSON output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ab_score] Results written to {output_path}")

    _print_markdown_table(metrics)


if __name__ == "__main__":
    main()
