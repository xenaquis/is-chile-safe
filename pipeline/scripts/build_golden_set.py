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
    --fill-verdicts     Reserved for a later task's live-call mode. This
                         invocation does NOT implement live calling — passing
                         this flag is a documented no-op that prints a clear
                         "not yet implemented in this invocation" message and
                         exits without touching the network.
    --out PATH          Override the default draft output path.

Bucketing is delegated entirely to `pipeline.news.clustering.bucket_incidents`
and `pipeline.news.clustering.prefilter_candidates` — this script never
reimplements the (cut,date) grouping loop (CLUS-02 single-source-of-truth
requirement).
"""
from __future__ import annotations

import argparse
import json
import logging
import pathlib
import sys
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

from pipeline.news.clustering import (  # noqa: E402
    _PREFILTER_THRESHOLD,
    bucket_incidents,
    prefilter_candidates,
)

logger = logging.getLogger(__name__)

INCIDENTS_PATH = REPO_ROOT / "data" / "incidents" / "current.json"
DEFAULT_DRAFT_PATH = (
    REPO_ROOT
    / ".planning"
    / "phases"
    / "26-event-clustering-spike"
    / "26-golden-set-draft.json"
)

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
        help="Reserved for a later task's live-call mode (not implemented here).",
    )
    parser.add_argument(
        "--out",
        type=pathlib.Path,
        default=DEFAULT_DRAFT_PATH,
        help="Override the default draft output path.",
    )
    args = parser.parse_args(argv)

    if args.fill_verdicts:
        print(
            "--fill-verdicts is not yet implemented in this invocation of "
            "build_golden_set.py — this mode is reserved for a later task "
            "that owns the live-call code path. No network call was made."
        )
        return 0

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
