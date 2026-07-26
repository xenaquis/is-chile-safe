"""
Spike 008 — Granite 4.1 8B (OpenRouter) vs DeepSeek v4-flash baseline.

Runs the PRODUCTION classifier prompt/parse path (pipeline.news.classifier)
against the labelled golden set, but with the client monkeypatched to
OpenRouter + ibm-granite/granite-4.1-8b. Production code is NOT modified.

Metrics mirror pipeline/experiments/ab_score.py exactly so results are
directly comparable with pipeline/results/ab_deepseek.json.

Usage (from repo root):
  python .planning/spikes/008-granite-openrouter-classifier/run_granite_golden.py [--limit N] [--json-mode]
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import time

_REPO_ROOT = pathlib.Path(__file__).parents[3]
sys.path.insert(0, str(_REPO_ROOT))

MODEL = "ibm-granite/granite-4.1-8b"
# OpenRouter pricing fetched 2026-07-26 from /api/v1/models:
#   prompt $0.05/1M, completion $0.10/1M
PRICING = {"input_per_1m": 0.05, "output_per_1m": 0.10}
# Same token estimates as ab_score.py for comparability
EST_IN, EST_OUT = 2100, 120


def load_env_key() -> str:
    env = (_REPO_ROOT / ".env").read_text(encoding="utf-8")
    m = re.search(r"OPENROUTER_API_KEY=(\S+)", env)
    if not m:
        sys.exit("OPENROUTER_API_KEY not found in .env")
    return m.group(1).strip().strip('"')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="only first N golden items (smoke test)")
    ap.add_argument("--json-mode", action="store_true",
                    help="send response_format=json_object (test OpenRouter/Granite support)")
    ap.add_argument("--variant-prompt", action="store_true",
                    help="use the is_crime_incident-first prompt variant (see probe_null_guard.py)")
    ap.add_argument("--normalize-family", action="store_true",
                    help="strip internal whitespace from family value before validation "
                         "(Granite tokenizer emits e.g. 'robos_ violentos')")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    key = load_env_key()

    # DEEPSEEK_API_KEY may be absent — classifier builds a client at import
    # time but we replace it before any call.
    os.environ.setdefault("DEEPSEEK_API_KEY", "unused")
    os.environ["NEWS_PROVIDER"] = "deepseek"

    import pipeline.news.classifier as clf
    from openai import OpenAI
    from pipeline.news.resolver import resolve_cut

    clf.client = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")
    clf._MODEL = MODEL
    # _PROVIDER controls response_format: "deepseek" → json_object sent.
    clf._PROVIDER = "deepseek" if args.json_mode else "granite-openrouter"

    if args.variant_prompt:
        clf.SYSTEM_PROMPT = clf.SYSTEM_PROMPT.replace(
            '{\n  "commune_name":',
            '{\n  "is_crime_incident": <true or false — false for non-crime news '
            '(sports, weather, health, inaugurations, campaigns) AND for traffic '
            'accidents without criminal intent>,\n  "commune_name":',
        ).replace(
            "Rules:",
            "Rules:\n- FIRST decide is_crime_incident. If false: commune_name MUST "
            "be null and confidence MUST be 0.0.",
        )

    if args.normalize_family:
        # Granite splits enum tokens ("robos_ violentos"). Normalize inside the
        # raw JSON string before classify() parses it, by wrapping the fence
        # stripper (the only hook between the API call and json.loads).
        orig_strip = clf._strip_json_fence

        def _strip_and_normalize(raw: str) -> str:
            s = orig_strip(raw)
            try:
                data = json.loads(s)
                if isinstance(data.get("family"), str):
                    data["family"] = data["family"].replace(" ", "")
                return json.dumps(data, ensure_ascii=False)
            except Exception:
                return s

        clf._strip_json_fence = _strip_and_normalize

    golden_path = _REPO_ROOT / "pipeline" / "tests" / "fixtures" / "golden_set.json"
    golden: list[dict] = json.loads(golden_path.read_text(encoding="utf-8"))
    if args.limit:
        golden = golden[: args.limit]

    labelled = [i for i in golden if i["ground_truth"]["commune_name"] is not None]
    nulls = [i for i in golden if i["ground_truth"]["commune_name"] is None]

    commune_ok = family_ok = parse_fail = null_ok = 0
    lat: list[float] = []
    per_item: list[dict] = []

    for item in labelled:
        t0 = time.perf_counter()
        r = clf.classify(item["headline"], item["description"])
        ms = (time.perf_counter() - t0) * 1000
        lat.append(ms)
        gt = item["ground_truth"]
        if r is None:
            parse_fail += 1
            per_item.append({"id": item["id"], "status": "parse_failure", "latency_ms": round(ms, 1)})
            print(f"  {item['id']}: PARSE_FAIL ({ms:.0f}ms)", flush=True)
            continue
        resolved = resolve_cut(r.commune_name, r.region_hint)
        pcut = resolved[0] if resolved else None
        cm, fm = pcut == gt["cut"], r.family == gt["family"]
        commune_ok += cm
        family_ok += fm
        per_item.append({
            "id": item["id"], "status": "ok",
            "predicted_commune_name": r.commune_name, "predicted_cut": pcut,
            "ground_truth_cut": gt["cut"], "commune_match": cm,
            "predicted_family": r.family, "ground_truth_family": gt["family"],
            "family_match": fm, "confidence": r.confidence, "latency_ms": round(ms, 1),
        })
        print(f"  {item['id']}: cut {'OK' if cm else 'X ' + str(pcut) + '!=' + gt['cut']}"
              f" fam {'OK' if fm else 'X ' + r.family + '!=' + gt['family']} ({ms:.0f}ms)", flush=True)

    for item in nulls:
        t0 = time.perf_counter()
        r = clf.classify(item["headline"], item["description"])
        ms = (time.perf_counter() - t0) * 1000
        lat.append(ms)
        ok = r is None or r.commune_name is None
        null_ok += ok
        per_item.append({
            "id": item["id"], "status": "null_item", "null_correct": ok,
            "predicted_commune_name": r.commune_name if r else None, "latency_ms": round(ms, 1),
        })
        print(f"  {item['id']}: null {'OK' if ok else 'X predicted ' + str(r.commune_name)} ({ms:.0f}ms)", flush=True)

    n_lab, n_null, n_tot = len(labelled), len(nulls), len(golden)
    metrics = {
        "provider": "openrouter-granite",
        "model": MODEL,
        "json_mode": args.json_mode,
        "golden_set": str(golden_path),
        "n_total": n_tot, "n_labelled": n_lab, "n_null": n_null,
        "commune_accuracy": round(commune_ok / n_lab, 4) if n_lab else 0.0,
        "family_accuracy": round(family_ok / n_lab, 4) if n_lab else 0.0,
        "null_rate": round(null_ok / n_null, 4) if n_null else None,
        "parse_failure_rate": round(parse_fail / n_tot, 4) if n_tot else 0.0,
        "mean_latency_ms": round(sum(lat) / len(lat), 1) if lat else 0.0,
        "estimated_cost_usd": round(
            n_tot * EST_IN / 1e6 * PRICING["input_per_1m"]
            + n_tot * EST_OUT / 1e6 * PRICING["output_per_1m"], 6),
        "pricing_note": "OpenRouter live pricing 2026-07-26: $0.05/$0.10 per 1M in/out",
        "per_item": per_item,
    }

    out = pathlib.Path(args.output) if args.output else (
        _REPO_ROOT / ".planning/spikes/008-granite-openrouter-classifier/results_granite_golden.json")
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n== Granite 4.1 8B (OpenRouter) ==")
    for k in ("n_total", "commune_accuracy", "family_accuracy", "null_rate",
              "parse_failure_rate", "mean_latency_ms", "estimated_cost_usd"):
        print(f"  {k}: {metrics[k]}")
    print(f"  written: {out}")


if __name__ == "__main__":
    main()
