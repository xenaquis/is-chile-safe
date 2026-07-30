#!/usr/bin/env python3
"""
pipeline/scripts/build_golden_set.py

CLUS-01 golden-set builder — sampling + labeling-draft + (future) live-verdict
population CLI, per `.planning/phases/26-event-clustering-spike/26-02-PLAN.md`.

This script is READ-ONLY with respect to `data/`: it only reads
`data/incidents/current.json`. It never imports or calls `merge_and_write`,
`atomic_write_json`, or any other write path under `pipeline.news.store`.

CLI contract:
    --dry-run          Sample + report counts, write nothing to disk.
    (no flag)           Write the draft to disk (default action).
    --fill-verdicts     LIVE, money-spending mode (W-1: this flag IS
                         implemented — it is NOT a no-op). Loads a draft,
                         makes one preflight probe call, then makes ~1 live
                         OpenRouter call per pending pair (up to 2 on a
                         retry), checkpoints the draft to disk every 10
                         pairs, and on success writes the finalized fixture
                         to pipeline/tests/fixtures/clustering_golden_set.json.
                         Every call is appended to the cumulative
                         26-CALL-LOG.md ledger, guarded by a refuse-to-start
                         check against the phase's 2,000-call budget cap
                         (_budget_guard). Resumable/idempotent: re-running
                         only re-adjudicates pairs that don't already carry
                         a model-sourced cached_verdict.
    --out PATH          Override the default draft output path.

Bucketing is delegated entirely to `pipeline.news.clustering.bucket_incidents`
and `pipeline.news.clustering.prefilter_candidates` — this script never
reimplements the (cut,date) grouping loop (CLUS-02 single-source-of-truth
requirement).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import logging
import os
import pathlib
import sys
import time
from itertools import combinations

# ---------------------------------------------------------------------------
# Repo root resolution — mirrors pipeline/scripts/audit_incidents.py:38-45
# exactly, so `pipeline.news.clustering` imports correctly whether this
# script is invoked directly (sys.path[0] == this file's directory) or under
# pytest (repo root already on the path via pythonpath config).
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Load .env BEFORE importing pipeline.news.clustering: that module constructs
# its OpenAI `client` at import time from os.environ.get("OPENROUTER_API_KEY",
# "placeholder") (clustering.py:56-59) — if dotenv loads any later than this,
# the client is permanently bound to the placeholder key for the whole
# process, and every live call fails auth regardless of a later preflight
# check. Mirrors pipeline/scrape_news.py:162-167's try/except pattern.
try:
    from dotenv import load_dotenv as _load_dotenv_early

    _load_dotenv_early(dotenv_path=REPO_ROOT / ".env")
except ImportError:
    pass  # python-dotenv not installed -- env vars must be set by caller

from pipeline.news.clustering import (  # noqa: E402
    MODEL,
    SYSTEM_PROMPT,
    _PREFILTER_THRESHOLD,
    adjudicate_pair,
    bucket_incidents,
    prefilter_candidates,
)
from pipeline.scripts.run_clustering_spike import compute_pairwise_metrics  # noqa: E402

logger = logging.getLogger(__name__)

INCIDENTS_PATH = REPO_ROOT / "data" / "incidents" / "current.json"
DEFAULT_DRAFT_PATH = (
    REPO_ROOT
    / ".planning"
    / "phases"
    / "26-event-clustering-spike"
    / "26-golden-set-draft.json"
)
DEFAULT_CALL_LOG_PATH = (
    REPO_ROOT
    / ".planning"
    / "phases"
    / "26-event-clustering-spike"
    / "26-CALL-LOG.md"
)
DEFAULT_FINAL_FIXTURE_PATH = (
    REPO_ROOT / "pipeline" / "tests" / "fixtures" / "clustering_golden_set.json"
)

# Base URL / hyperparameters mirrored from clustering.py's client construction
# and _call_verdict_api — recorded verbatim into the fixture's meta block.
_BASE_URL = "https://openrouter.ai/api/v1"
_MAX_TOKENS = 220
_TEMPERATURE = 0.0
_MERGEABLE_RULE = "same_event and confidence=='high'"
_CALL_BUDGET_CAP = 2000

# Trivial, unambiguous probe pair for the mandatory single preflight call —
# deliberately NOT part of the real golden-set pairs.
_PROBE_INCIDENT_A = {
    "id": "preflight-probe-a",
    "cut": "0000",
    "date": "2026-01-01",
    "title_es": "Robo con violencia registrado en Santiago",
}
_PROBE_INCIDENT_B = {
    "id": "preflight-probe-b",
    "cut": "0000",
    "date": "2026-01-01",
    "title_es": "Incendio forestal afecta a Valparaiso",
}


class BudgetExceededError(RuntimeError):
    """Raised when the projected call count would exceed the phase's
    2,000-call OpenRouter budget. Callers must not proceed to the live fill
    loop when this is raised."""

MANDATORY_BUCKETS: list[tuple[str, str]] = [
    ("2101", "2026-07-01"),
    ("4102", "2026-07-01"),
]

# Base pair count already accounted for before supplemental sampling:
# 36 (2101, 9 articles -> C(9,2)) + 28 (4102, 8 articles -> C(8,2)) + 10
# (fixed typo/homophone sub-set) = 74. This value is a Fable-locked constant
# for this plan — do not recompute it dynamically from bucket sizes, because
# the arithmetic in the plan is pinned to these exact real-data counts.
_BASE_PAIR_COUNT = 36 + 28 + 10

_MAX_TOTAL_PAIRS = 100

# ---------------------------------------------------------------------------
# Typo/homophone confusable comuna pairs — verified against
# data/ine/poblacion_comunal.json (per 26-02-PLAN.md <interfaces>).
# Fixed at exactly 10 pairs (not all 12 available) so the golden-set
# arithmetic in step 4 is deterministic.
# ---------------------------------------------------------------------------
_TYPO_HOMOPHONE_PAIRS: list[tuple[str, str, str, str]] = [
    # (comuna_a, cut_a, comuna_b, cut_b)
    ("Los Andes", "5301", "Los Angeles", "8301"),
    ("Quilaco", "8308", "Quilleco", "8309"),
    ("San Carlos", "16301", "San Pablo", "10307"),
    ("Colina", "13301", "Molina", "7304"),
    ("Caldera", "3102", "Calera", "5502"),
    ("Chanco", "7202", "Lanco", "14103"),
    ("Cochrane", "11301", "Colchane", "1403"),
    ("Pemuco", "16105", "Penco", "8107"),
    ("Peumo", "6112", "Pirque", "13202"),
    ("Talca", "7101", "Taltal", "2104"),
]
assert len(_TYPO_HOMOPHONE_PAIRS) == 10

# Synthesized, clearly distinct crime descriptions per comuna side — chosen so
# the pair is lexically confusable (comuna name) but factually a different
# incident by construction.
_TYPO_TITLES: dict[str, tuple[str, str]] = {
    "Los Andes": ("Robo con violencia registrado en Los Andes", "5301"),
    "Los Angeles": ("Detienen a sospechoso de hurto en Los Angeles", "8301"),
    "Quilaco": ("Denuncian abigeato en sector rural de Quilaco", "8308"),
    "Quilleco": ("Incendio intencional afecta bodega en Quilleco", "8309"),
    "San Carlos": ("Riña con arma blanca deja un herido en San Carlos", "16301"),
    "San Pablo": ("Sustraen vehículo estacionado en San Pablo", "10307"),
    "Colina": ("Vecinos denuncian estafa telefónica en Colina", "13301"),
    "Molina": ("Encuentran vehículo con encargo por robo en Molina", "7304"),
    "Caldera": ("Fiscalización detecta contrabando en el puerto de Caldera", "3102"),
    "Calera": ("Detienen a conductor en estado de ebriedad en Calera", "5502"),
    "Chanco": ("Incautan drogas en control vehicular en Chanco", "7202"),
    "Lanco": ("Denuncian violencia intrafamiliar en Lanco", "14103"),
    "Cochrane": ("Reportan extravío de turista en Cochrane", "11301"),
    "Colchane": ("Carabineros detecta ingreso irregular de migrantes en Colchane", "1403"),
    "Pemuco": ("Vecinos denuncian corte de cercos y abigeato en Pemuco", "16105"),
    "Penco": ("Riña vecinal termina con detenido en Penco", "8107"),
    "Peumo": ("Roban maquinaria agrícola en Peumo", "6112"),
    "Pirque": ("Detienen a conductor tras persecución en Pirque", "13202"),
    "Talca": ("Asalto a local comercial en el centro de Talca", "7101"),
    "Taltal": ("Naufragio de embarcación menor reportado en Taltal", "2104"),
}


_LEDGER_HEADER = """# Phase 26 — Cumulative OpenRouter Call Ledger

Append-only. Never edit or delete existing rows — only append new ones.
Budget cap: 2,000 OpenRouter calls for the whole phase
(`.planning/v2.1-AUTONOMOUS-DIRECTIVE.md`).

| timestamp | script | calls_this_run | cumulative_total | notes |
|---|---|---|---|---|
| 2026-07-29T00:00:00Z | 26-00-SPIKE-PING.md | 3 | 3 | spike ping baseline (3/3 PASS) |
"""


def _read_last_cumulative_total(path: pathlib.Path) -> int:
    """Read the ledger's latest cumulative_total. Seeds the ledger (with the
    3-call spike-ping baseline row) if it does not exist yet. Pure read/seed
    — never makes a network call, safe to unit test offline."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_LEDGER_HEADER, encoding="utf-8")
        return 3
    text = path.read_text(encoding="utf-8")
    rows = [
        line
        for line in text.splitlines()
        if line.strip().startswith("|") and not line.strip().startswith("|---")
    ]
    if len(rows) < 2:
        return 3
    data_rows = rows[1:]  # rows[0] is the header row
    last = data_rows[-1]
    cols = [c.strip() for c in last.strip().strip("|").split("|")]
    return int(cols[3])


def _append_ledger_row(
    path: pathlib.Path, *, calls_this_run: int, cumulative_total: int, notes: str
) -> None:
    """Append one row. Never rewrites/removes existing rows (append-only)."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_LEDGER_HEADER, encoding="utf-8")
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = (
        f"| {timestamp} | build_golden_set.py --fill-verdicts | "
        f"{calls_this_run} | {cumulative_total} | {notes} |\n"
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(row)


def _budget_guard(
    call_log_path: pathlib.Path, projected: int, cap: int = _CALL_BUDGET_CAP
) -> int:
    """Refuse to start if last_cumulative_total + projected > cap.

    Returns last_cumulative_total on success. On refusal: appends a
    "NO-GO-by-cost" row to the ledger and raises BudgetExceededError.
    NEVER calls adjudicate_pair or touches the network — safe to unit test
    fully offline (per 26-02-PLAN.md's test_call_budget_refuses_to_start).
    """
    last_cumulative = _read_last_cumulative_total(call_log_path)
    if last_cumulative + projected > cap:
        _append_ledger_row(
            call_log_path,
            calls_this_run=0,
            cumulative_total=last_cumulative,
            notes=(
                f"NO-GO-by-cost: refused to start -- last_cumulative="
                f"{last_cumulative} + projected={projected} > cap={cap}"
            ),
        )
        raise BudgetExceededError(
            f"Refusing to start fill-verdicts: {last_cumulative} + "
            f"{projected} > {cap}"
        )
    return last_cumulative


def _load_dotenv_if_available() -> None:
    """Mirrors pipeline/scrape_news.py:162-167's try/except dotenv pattern."""
    try:
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=REPO_ROOT / ".env")
    except ImportError:
        pass  # python-dotenv not installed -- env vars must be set by caller


def _check_api_key() -> None:
    """Assert OPENROUTER_API_KEY is set and non-placeholder. Checks emptiness
    explicitly (project gotcha: unset GitHub secrets surface as EMPTY
    STRINGS, not missing keys) -- never just presence."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key or key == "placeholder":
        raise SystemExit(
            "FATAL: OPENROUTER_API_KEY is empty or the literal 'placeholder' "
            "-- aborting before any live call."
        )


def _load_incidents_list(path: pathlib.Path) -> list[dict]:
    """Read-only load of a current.json-shaped file. Mirrors
    pipeline/news/store.py:88-99's `_load_incidents_list` logic exactly —
    reimplemented locally (not imported) to avoid pulling in store.py's
    write-side surface (`merge_and_write`, `atomic_write_json`) into this
    read-only script's import graph.
    """
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data.get("incidents", [])
        return []
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not read %s: %s — treating as empty", path, exc)
        return []


def _build_typo_homophone_pairs() -> list[dict]:
    """Construct the fixed 10-pair cross-bucket typo/homophone negative
    sub-set. These deliberately bypass (cut,date) bucketing by construction
    (bypasses_bucket: true) — CLUS-01's class (b) adversarial negative
    (lexically confusable comuna names) can never occur inside strict
    (cut,date) bucketing, so it is hand-built here.
    """
    entries: list[dict] = []
    for comuna_a, cut_a, comuna_b, cut_b in _TYPO_HOMOPHONE_PAIRS:
        title_a, _ = _TYPO_TITLES[comuna_a]
        title_b, _ = _TYPO_TITLES[comuna_b]
        incident_a = {
            "id": f"typo-{cut_a}-01",
            "cut": cut_a,
            "date": "2026-07-01",
            "title_es": title_a,
            "outlet": "synthesized",
            "url": "",
        }
        incident_b = {
            "id": f"typo-{cut_b}-02",
            "cut": cut_b,
            "date": "2026-07-01",
            "title_es": title_b,
            "outlet": "synthesized",
            "url": "",
        }
        entries.append(
            {
                "pair_id": f"typo-{cut_a}-{cut_b}",
                "incident_a_id": incident_a["id"],
                "incident_b_id": incident_b["id"],
                "cut_a": cut_a,
                "cut_b": cut_b,
                "title_a": title_a,
                "title_b": title_b,
                "outlet_a": "synthesized",
                "outlet_b": "synthesized",
                "url_a": "",
                "url_b": "",
                "prefilter_score": None,
                "proposed": True,
                "category": "typo_homophone_negative",
                "bypasses_bucket": True,
                "label": None,
                "incident_a": incident_a,
                "incident_b": incident_b,
            }
        )
    return entries


def _select_supplemental_buckets(
    buckets: dict[tuple[str, str], list[dict]]
) -> tuple[list[tuple[str, str]], int]:
    """Deterministic supplemental bucket accumulation (Task 1 step 4).

    Eligible buckets: size 2-5, excluding the two mandatory buckets. Sorted
    by (cut, date) string order, walked in order, adding WHOLE buckets while
    total_pairs + C(size,2) <= 100. Starting total = 74 (64 mandatory-bucket
    pairs + 10 typo/homophone pairs). Never trims individual pairs.
    """
    eligible: list[tuple[tuple[str, str], int]] = []
    for key, members in buckets.items():
        if key in MANDATORY_BUCKETS:
            continue
        size = len(members)
        if 2 <= size <= 5:
            eligible.append((key, size))

    eligible.sort(key=lambda item: item[0])

    total_pairs = _BASE_PAIR_COUNT
    selected: list[tuple[str, str]] = []
    for key, size in eligible:
        c = size * (size - 1) // 2
        if total_pairs + c <= _MAX_TOTAL_PAIRS:
            total_pairs += c
            selected.append(key)
        else:
            break

    return selected, total_pairs


def _bucketed_pair_entries(
    bucket_key: tuple[str, str],
    bucket: list[dict],
    *,
    is_mandatory: bool,
) -> list[dict]:
    """Emit draft pair entries for one bucket.

    Mandatory buckets: ALL intra-bucket pairs are emitted regardless of
    prefilter result (proposed reflects whether the pair would have passed
    the threshold). Supplemental buckets: only prefilter-passing pairs are
    emitted (the real production candidate-generation path).
    """
    from rapidfuzz import fuzz  # local import mirrors clustering.py's pattern

    cut, date = bucket_key
    entries: list[dict] = []

    if is_mandatory:
        pairs_iter = combinations(bucket, 2)
    else:
        pairs_iter = prefilter_candidates(bucket, threshold=_PREFILTER_THRESHOLD)

    for a, b in pairs_iter:
        score = fuzz.token_set_ratio(a.get("title_es", ""), b.get("title_es", ""))
        proposed = score >= _PREFILTER_THRESHOLD
        if not is_mandatory and not proposed:
            # prefilter_candidates() already only returns passing pairs, but
            # keep this defensive in case of a future signature change.
            continue

        category = "mandatory_pending_label" if is_mandatory else "sampled"
        a_id, b_id = a.get("id", ""), b.get("id", "")
        pair_id = f"{cut}-{date}-{a_id[:6]}-{b_id[:6]}"
        entries.append(
            {
                "pair_id": pair_id,
                "incident_a_id": a_id,
                "incident_b_id": b_id,
                "cut_a": a.get("cut", ""),
                "cut_b": b.get("cut", ""),
                "title_a": a.get("title_es", ""),
                "title_b": b.get("title_es", ""),
                "outlet_a": a.get("outlet", ""),
                "outlet_b": b.get("outlet", ""),
                "url_a": a.get("url", ""),
                "url_b": b.get("url", ""),
                "prefilter_score": score,
                "proposed": proposed,
                "category": category,
                "bypasses_bucket": False,
                "label": None,
            }
        )
    return entries


def build_draft(incidents: list[dict]) -> dict:
    buckets = bucket_incidents(incidents)

    # Step 6 FIRST — typo/homophone sub-set sized before bucket accumulation.
    typo_entries = _build_typo_homophone_pairs()

    # Step 4 — deterministic supplemental sampling.
    selected_buckets, total_pairs = _select_supplemental_buckets(buckets)

    pairs: list[dict] = []

    # Mandatory buckets — always included, all intra-bucket pairs emitted.
    for key in MANDATORY_BUCKETS:
        bucket = buckets.get(key, [])
        pairs.extend(_bucketed_pair_entries(key, bucket, is_mandatory=True))

    # Supplemental buckets.
    for key in selected_buckets:
        bucket = buckets[key]
        pairs.extend(_bucketed_pair_entries(key, bucket, is_mandatory=False))

    # Typo/homophone sub-set.
    pairs.extend(typo_entries)

    meta = {
        "selected_buckets": [list(k) for k in selected_buckets],
        "total_pairs": total_pairs,
        "mandatory_buckets": [list(k) for k in MANDATORY_BUCKETS],
    }

    return {"meta": meta, "pairs": pairs}


def _print_summary(draft: dict) -> None:
    pairs = draft["pairs"]
    meta = draft["meta"]
    proposed_true = sum(1 for p in pairs if p["proposed"])
    proposed_false = sum(1 for p in pairs if not p["proposed"])
    typo_count = sum(1 for p in pairs if p["category"] == "typo_homophone_negative")

    print(f"Total buckets sampled (supplemental): {len(meta['selected_buckets'])}")
    print(f"Selected buckets: {meta['selected_buckets']}")
    print(f"Mandatory buckets: {meta['mandatory_buckets']}")
    print(f"Total candidate pairs: {len(pairs)}")
    print(f"  proposed=true:  {proposed_true}")
    print(f"  proposed=false: {proposed_false}")
    print(f"  typo/homophone: {typo_count}")
    print(f"Recorded meta.total_pairs: {meta['total_pairs']}")
    if not (60 <= len(pairs) <= 100):
        logger.warning(
            "Draft pair count %d is outside the 60-100 target range", len(pairs)
        )
        print(f"WARNING: total pair count {len(pairs)} outside 60-100 range")
    else:
        print(f"Range check OK: {len(pairs)} pairs within 60-100")


def _has_model_verdict(pair: dict) -> bool:
    cv = pair.get("cached_verdict")
    return isinstance(cv, dict) and cv.get("source") == "model"


def fill_verdicts(
    draft_path: pathlib.Path = DEFAULT_DRAFT_PATH,
    call_log_path: pathlib.Path = DEFAULT_CALL_LOG_PATH,
    final_fixture_path: pathlib.Path = DEFAULT_FINAL_FIXTURE_PATH,
) -> int:
    """Live verdict-fill mode (Task 3). Resumable, idempotent, budget-ledgered.

    Returns 0 on success (final fixture written, failed_pairs empty), 1 on
    any non-fatal stop (budget refusal, failed_pairs non-empty). Raises
    SystemExit only for the preflight abort conditions.
    """
    calls_this_run = 0
    exit_note = "unknown exit path"
    budget_already_logged = False
    total_possible_note = "n/a"

    try:
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
        pairs = draft["pairs"]
        meta = draft.setdefault("meta", {})
        total_possible_note = meta.get("total_pairs", len(pairs))

        pending = [p for p in pairs if p.get("proposed") and not _has_model_verdict(p)]
        # Worst case is 2 calls per pending pair (primary + one retry on any
        # non-model outcome, see the retry block below) +1 for the mandatory
        # single preflight probe call. A projection of len(pending)+1 (one
        # call per pair) ignores the retry path entirely and can be overrun
        # up to ~2x with no refusal (HI-01).
        projected = 2 * len(pending) + 1

        try:
            last_cumulative = _budget_guard(call_log_path, projected)
        except BudgetExceededError:
            budget_already_logged = True
            exit_note = "NO-GO-by-cost (budget guard refused to start)"
            print(f"NO-GO-by-cost: {exit_note}")
            return 1

        # --- Preflight: load .env, assert key, exactly ONE probe call ---
        _load_dotenv_if_available()
        _check_api_key()
        probe_verdict = adjudicate_pair(_PROBE_INCIDENT_A, _PROBE_INCIDENT_B)
        calls_this_run += 1
        if probe_verdict.source != "model":
            exit_note = (
                f"aborted: preflight probe returned source={probe_verdict.source} "
                "(not 'model') -- entire task aborted before the fill loop"
            )
            raise SystemExit(
                "FATAL: preflight probe call did not reach the model "
                f"(source={probe_verdict.source}) -- aborting fill-verdicts "
                "before entering the fill loop."
            )

        # --- Idempotent, resumable fill loop ---
        incidents_by_id = {
            inc.get("id"): inc for inc in _load_incidents_list(INCIDENTS_PATH)
        }
        failed_pairs: list[str] = list(meta.get("failed_pairs", []))
        consecutive_failures = 0
        processed_since_write = 0

        def _persist() -> None:
            meta["failed_pairs"] = failed_pairs
            draft_path.write_text(
                json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        aborted_early = False
        budget_aborted_early = False
        for p in pending:
            # In-loop re-check (HI-01): the pre-flight projection admits a
            # run based on a worst-case estimate, but re-verify before EVERY
            # pair that spending up to 2 more calls (primary + retry) would
            # not push the cumulative total past the cap. A run that started
            # under budget must never silently overrun it mid-loop.
            if last_cumulative + calls_this_run + 2 > _CALL_BUDGET_CAP:
                exit_note = (
                    f"aborted: in-loop budget cap reached "
                    f"(last_cumulative={last_cumulative} + "
                    f"calls_this_run={calls_this_run} + 2 > cap={_CALL_BUDGET_CAP})"
                )
                aborted_early = True
                budget_aborted_early = True
                break

            a = p.get("incident_a") or incidents_by_id.get(p["incident_a_id"])
            b = p.get("incident_b") or incidents_by_id.get(p["incident_b_id"])
            if a is None or b is None:
                logger.warning(
                    "Could not resolve incidents for pair %s -- marking failed",
                    p["pair_id"],
                )
                if p["pair_id"] not in failed_pairs:
                    failed_pairs.append(p["pair_id"])
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    aborted_early = True
                    break
                continue

            verdict = adjudicate_pair(a, b)
            calls_this_run += 1

            if verdict.source == "model":
                p["cached_verdict"] = verdict.model_dump()
                if p["pair_id"] in failed_pairs:
                    failed_pairs.remove(p["pair_id"])
                consecutive_failures = 0
            else:
                # Single hand-rolled retry on a rate-limit-shaped failure,
                # mirroring classifier.py's retry pattern (no tenacity dep).
                time.sleep(2)
                retry_verdict = adjudicate_pair(a, b)
                calls_this_run += 1
                if retry_verdict.source == "model":
                    p["cached_verdict"] = retry_verdict.model_dump()
                    if p["pair_id"] in failed_pairs:
                        failed_pairs.remove(p["pair_id"])
                    consecutive_failures = 0
                else:
                    p["cached_verdict"] = None
                    if p["pair_id"] not in failed_pairs:
                        failed_pairs.append(p["pair_id"])
                    consecutive_failures += 1

            processed_since_write += 1
            if processed_since_write >= 10:
                _persist()
                processed_since_write = 0

            if consecutive_failures >= 3:
                logger.error(
                    "Aborting fill loop after 3 consecutive non-model outcomes"
                )
                aborted_early = True
                break

        _persist()

        if aborted_early:
            if not budget_aborted_early:
                exit_note = (
                    f"aborted after 3 consecutive non-model outcomes; "
                    f"{len(failed_pairs)} failed_pairs remain"
                )
            return 1

        if failed_pairs:
            exit_note = (
                f"loop completed but failed_pairs non-empty ({len(failed_pairs)}); "
                "fixture NOT finalized"
            )
            print(
                f"WARNING: {len(failed_pairs)} pairs never got a model verdict: "
                f"{failed_pairs} -- fixture not written."
            )
            return 1

        # --- Finalize the committed fixture ---
        system_prompt_sha256 = hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest()
        generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        final_meta = {
            "model": MODEL,
            "base_url": _BASE_URL,
            "system_prompt_sha256": system_prompt_sha256,
            "max_tokens": _MAX_TOKENS,
            "temperature": _TEMPERATURE,
            "mergeable_rule": _MERGEABLE_RULE,
            "generated": generated,
            "calls": calls_this_run,
            "selected_buckets": meta.get("selected_buckets", []),
            "total_pairs": len(pairs),
        }
        if "blind_second_pass" in meta:
            final_meta["blind_second_pass"] = meta["blind_second_pass"]

        final_pairs: list[dict] = []
        for p in pairs:
            entry: dict = {
                "pair_id": p["pair_id"],
                "incident_a_id": p["incident_a_id"],
                "incident_b_id": p["incident_b_id"],
                "title_a": p.get("title_a"),
                "title_b": p.get("title_b"),
                "outlet_a": p.get("outlet_a"),
                "outlet_b": p.get("outlet_b"),
                "url_a": p.get("url_a"),
                "url_b": p.get("url_b"),
                "label": p.get("label"),
                "category": p.get("category"),
                "label_basis": p.get("label_basis"),
                "prefilter_score": p.get("prefilter_score"),
                "proposed": p.get("proposed"),
                "bypasses_bucket": p.get("bypasses_bucket", False),
                "cached_verdict": p.get("cached_verdict") if p.get("proposed") else None,
            }
            if p.get("label_confidence"):
                entry["label_confidence"] = p["label_confidence"]
            if p.get("second_pass_confirmed") is not None:
                entry["second_pass_confirmed"] = p["second_pass_confirmed"]
            if p.get("second_pass_note"):
                entry["second_pass_note"] = p["second_pass_note"]
            if p.get("excluded"):
                entry["excluded"] = p["excluded"]
            if p.get("note"):
                entry["note"] = p["note"]
            final_pairs.append(entry)

        # HI-03: `meta.baseline` is the value `test_golden_set_metrics_match_
        # recorded_baseline` asserts against -- it must be WRITTEN by this
        # generation path, not hand-typed into the fixture. Idempotent: if a
        # baseline already exists in the fixture currently on disk, preserve
        # it verbatim rather than recomputing (a legitimate re-run of
        # --fill-verdicts must never silently rewrite the recorded baseline
        # out from under the internal-consistency sentinel that exists to
        # catch exactly that kind of drift).
        existing_baseline = None
        if final_fixture_path.exists():
            try:
                existing_data = json.loads(final_fixture_path.read_text(encoding="utf-8"))
                existing_baseline = existing_data.get("meta", {}).get("baseline")
            except (json.JSONDecodeError, OSError):
                existing_baseline = None
        if existing_baseline is not None:
            final_meta["baseline"] = existing_baseline
        else:
            final_meta["baseline"] = compute_pairwise_metrics(final_pairs)

        final_fixture_path.parent.mkdir(parents=True, exist_ok=True)
        final_fixture_path.write_text(
            json.dumps({"meta": final_meta, "pairs": final_pairs}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(
            f"Final fixture written to {final_fixture_path} "
            f"({len(final_pairs)} pairs, {calls_this_run} calls this run)"
        )
        exit_note = (
            f"completed successfully; final fixture written "
            f"({len(final_pairs)} pairs, {calls_this_run} calls this run)"
        )
        return 0

    finally:
        if not budget_already_logged:
            last_cumulative = _read_last_cumulative_total(call_log_path)
            new_cumulative = last_cumulative + calls_this_run
            _append_ledger_row(
                call_log_path,
                calls_this_run=calls_this_run,
                cumulative_total=new_cumulative,
                notes=(
                    f"{exit_note} (total_possible_in_bucket_pairs="
                    f"{total_possible_note})"
                ),
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Sample + report counts, write nothing to disk.",
    )
    parser.add_argument(
        "--fill-verdicts",
        action="store_true",
        help=(
            "LIVE mode: makes real OpenRouter calls (~1 per pending pair, "
            "up to 2,000 cumulative-budget-guarded) and writes the "
            "finalized golden-set fixture on success. NOT a no-op."
        ),
    )
    parser.add_argument(
        "--out",
        type=pathlib.Path,
        default=DEFAULT_DRAFT_PATH,
        help="Override the default draft output path.",
    )
    args = parser.parse_args(argv)

    if args.fill_verdicts:
        try:
            return fill_verdicts(draft_path=args.out)
        except SystemExit as exc:
            print(str(exc))
            return 1
        except BudgetExceededError as exc:
            print(f"NO-GO-by-cost: {exc}")
            return 1

    incidents = _load_incidents_list(INCIDENTS_PATH)
    if not incidents:
        print(f"No incidents found at {INCIDENTS_PATH} — nothing to sample.")
        return 1

    draft = build_draft(incidents)
    _print_summary(draft)

    if args.dry_run:
        print("(--dry-run: nothing written to disk)")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Draft written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
