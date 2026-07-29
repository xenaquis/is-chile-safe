#!/usr/bin/env python3
"""
pipeline/scripts/run_clustering_spike.py

Phase 26 Wave 3 (CLUS-06, CLUS-07, CLUS-08): read-only evidence-generation
CLI for the event-clustering GO/NO-GO decision.

Loads the finalized golden-set fixture (pipeline/tests/fixtures/
clustering_golden_set.json), computes pair-level precision/recall/cost
metrics via `compute_pairwise_metrics()` (the single source of truth also
imported by pipeline/tests/test_clustering.py — never duplicate this
formula), assembles clusters via pipeline.news.clustering.assemble_clusters,
and writes the full pairwise decision matrix plus the measured evidence to
.planning/phases/26-event-clustering-spike/26-SPIKE-REPORT.md.

This script makes ZERO live LLM calls — every verdict it reads comes from
the fixture's `cached_verdict` field, recorded once during the golden-set
build (26-02). It NEVER adjusts the golden-set labels, the mergeable-state
rule, or the frozen pre-filter threshold to change the measured outcome.

Usage:
    python pipeline/scripts/run_clustering_spike.py
"""
from __future__ import annotations

import json
import pathlib
import sys

# Ensure the repo root is importable when run standalone
# (`python pipeline/scripts/run_clustering_spike.py`): sys.path[0] would
# otherwise be this script's directory, hiding the top-level `pipeline`
# package. Mirrors pipeline/scripts/audit_incidents.py:38-43. Harmless under
# pytest (pythonpath=.. already puts the repo root on the path).
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.news.clustering import assemble_clusters, cluster_id  # noqa: E402

GOLDEN_SET_PATH = REPO_ROOT / "pipeline" / "tests" / "fixtures" / "clustering_golden_set.json"
CALL_LOG_PATH = REPO_ROOT / ".planning" / "phases" / "26-event-clustering-spike" / "26-CALL-LOG.md"
REPORT_PATH = REPO_ROOT / ".planning" / "phases" / "26-event-clustering-spike" / "26-SPIKE-REPORT.md"

_METRIC_KEYS = (
    "tp", "fp", "fn", "fn_prefiltered", "fn_llm_rejected", "tn",
    "precision", "recall", "n_pairs", "n_failsafe",
)


def compute_pairwise_metrics(pairs: list[dict]) -> dict:
    """Compute pair-level TP/FP/FN/TN/precision/recall/n_failsafe.

    Operates on the fixture's (already excluded-filtered-by-caller-or-not)
    `pairs` list. Excluded pairs (`excluded` truthy, i.e. label_disputed per
    F-13) are dropped from the metric entirely here — they are never counted
    toward tp/fp/fn/tn/n_pairs/n_failsafe.

    `proposed_pairs` (`proposed is True`) apply the mergeable-state rule
    (`cached_verdict.same_event is True AND cached_verdict.confidence ==
    "high"`) to decide whether an edge is drawn, then classify at the PAIR
    level against the golden `label`.

    `prefiltered_pairs` (`proposed is False`) NEVER have `cached_verdict`
    read (it is always null for these pairs per 26-02's Fable-locked
    contract) — only `label` is consulted: `label == "merge"` counts toward
    `fn_prefiltered`; `label == "no_merge"` counts toward nothing (the
    pipeline never adjudicated it, so no decision was ever made).

    Returns exactly the keys in `_METRIC_KEYS`. `precision = None` when
    `tp + fp == 0` (never 1.0 — a run that merges nothing is unmeasured, not
    passing, per F-07). `recall = None` when `tp + fn == 0`.
    """
    non_excluded = [p for p in pairs if not p.get("excluded")]

    proposed_pairs = [p for p in non_excluded if p.get("proposed") is True]
    prefiltered_pairs = [p for p in non_excluded if p.get("proposed") is False]

    tp = fp = tn = fn_llm_rejected = n_failsafe = 0
    fn_prefiltered = 0

    for p in prefiltered_pairs:
        # NEVER read cached_verdict here -- it is always null for
        # proposed:false pairs per 26-02's Fable-locked contract.
        if p.get("label") == "merge":
            fn_prefiltered += 1
        # label == "no_merge" for a never-adjudicated pair contributes
        # nothing -- not a TN, since no decision was ever made about it.

    for p in proposed_pairs:
        cv = p["cached_verdict"]
        if cv.get("source") != "model":
            n_failsafe += 1

        edge_drawn = cv.get("same_event") is True and cv.get("confidence") == "high"
        label = p.get("label")

        if label == "merge" and edge_drawn:
            tp += 1
        elif label == "no_merge" and edge_drawn:
            fp += 1
        elif label == "merge" and not edge_drawn:
            fn_llm_rejected += 1
        elif label == "no_merge" and not edge_drawn:
            tn += 1

    fn = fn_prefiltered + fn_llm_rejected
    n_pairs = len(proposed_pairs) + len(prefiltered_pairs)

    precision = (tp / (tp + fp)) if (tp + fp) > 0 else None
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else None

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "fn_prefiltered": fn_prefiltered,
        "fn_llm_rejected": fn_llm_rejected,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "n_pairs": n_pairs,
        "n_failsafe": n_failsafe,
    }


def _edge_drawn(p: dict) -> bool:
    """Whether the pipeline would draw a merge edge for a proposed pair."""
    if p.get("proposed") is not True:
        return False
    cv = p["cached_verdict"]
    return cv.get("same_event") is True and cv.get("confidence") == "high"


def _classification(p: dict) -> str:
    """Per-row classification string for the pairwise decision matrix."""
    if p.get("excluded"):
        return "excluded (label_disputed)"
    if p.get("proposed") is False:
        return "fn_prefiltered" if p.get("label") == "merge" else "n/a (prefiltered, no_merge)"
    edge = _edge_drawn(p)
    label = p.get("label")
    if label == "merge" and edge:
        return "TP"
    if label == "no_merge" and edge:
        return "FP"
    if label == "merge" and not edge:
        return "FN (fn_llm_rejected)"
    return "TN"


def _read_total_possible_in_bucket_pairs() -> str:
    if not CALL_LOG_PATH.exists():
        return "unknown (26-CALL-LOG.md not found)"
    text = CALL_LOG_PATH.read_text(encoding="utf-8")
    import re

    matches = re.findall(r"total_possible_in_bucket_pairs=(\d+)", text)
    if matches:
        return matches[-1]
    return "unknown"


def _build_report(fixture: dict, metrics: dict, clusters: dict, flagged: dict) -> str:
    pairs = fixture["pairs"]
    meta = fixture.get("meta", {})
    non_excluded = [p for p in pairs if not p.get("excluded")]
    excluded_pairs = [p for p in pairs if p.get("excluded")]
    proposed_pairs = [p for p in non_excluded if p.get("proposed") is True]

    conf_high = sum(1 for p in proposed_pairs if p["cached_verdict"].get("confidence") == "high")
    conf_low = sum(1 for p in proposed_pairs if p["cached_verdict"].get("confidence") == "low")

    total_possible = _read_total_possible_in_bucket_pairs()
    n_proposed = len(proposed_pairs)
    try:
        total_possible_int = int(total_possible)
        reduction_pct = (
            f"{(1 - n_proposed / total_possible_int) * 100:.1f}%" if total_possible_int else "n/a"
        )
    except (ValueError, TypeError):
        reduction_pct = "n/a"

    merge_labels_non_excluded = [p for p in non_excluded if p["label"] == "merge"]
    second_pass_confirmed = sum(
        1 for p in merge_labels_non_excluded if p.get("second_pass_confirmed")
    )
    blind = meta.get("blind_second_pass", {})

    negatives_in_set = sum(1 for p in non_excluded if p["label"] == "no_merge")
    negatives_adjudicated = sum(
        1 for p in proposed_pairs if p["label"] == "no_merge"
    )
    positives_adjudicated = sum(1 for p in proposed_pairs if p["label"] == "merge")
    filtered_pre_llm = len([p for p in non_excluded if p.get("proposed") is False])

    precision_str = (
        f"{metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)"
        if metrics["precision"] is not None
        else "None (zero denominator)"
    )
    recall_str = f"{metrics['recall']:.4f}" if metrics["recall"] is not None else "None (zero denominator)"

    lines: list[str] = []
    lines.append("# Phase 26 Wave 3 — Event Clustering Spike Report")
    lines.append("")
    lines.append(f"Generated by `pipeline/scripts/run_clustering_spike.py`. Source data: "
                 f"`pipeline/tests/fixtures/clustering_golden_set.json` "
                 f"(model=`{meta.get('model')}`, generated `{meta.get('generated')}`).")
    lines.append("")
    lines.append("## Provenance")
    lines.append("")
    lines.append(
        "The golden set was sourced from `data/incidents/current.json` ONLY. "
        "The R2 research archive (`26-RESEARCH.md`) holds only 2026-04 and "
        "2026-06 data, and neither month contains the mandatory 2026-07-01 "
        "buckets (comuna 2101 and comuna 4102/Tongoy) — so this report's "
        "audit trail is self-contained and does not depend on reading a "
        "separate archive-provenance plan file."
    )
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(
        "Measured on same-`(cut,date)` buckets only. The +-1-day window and "
        "cross-day procedural follow-ups are UNTESTED and out of scope for "
        "this verdict (F-04: no +-1-day bucket widening in Phase 26)."
    )
    lines.append(
        f"`_PREFILTER_THRESHOLD = 45.0` was pre-registered before any "
        f"precision measurement and was NOT tuned during this run (F-02)."
    )
    lines.append("")
    lines.append("## Headline Metrics")
    lines.append("")
    lines.append(f"- TP (true positives): **{metrics['tp']}**")
    lines.append(f"- FP (false positives / false merges): **{metrics['fp']}**")
    lines.append(
        f"- FN (false negatives, total): **{metrics['fn']}** "
        f"(fn_prefiltered={metrics['fn_prefiltered']}, fn_llm_rejected={metrics['fn_llm_rejected']})"
    )
    lines.append(f"- TN (true negatives): **{metrics['tn']}**")
    lines.append(f"- Precision: **{precision_str}**")
    lines.append(f"- Recall: **{recall_str}**")
    lines.append(f"- n_pairs (non-excluded pairs measured): **{metrics['n_pairs']}**")
    lines.append(f"- n_failsafe (proposed pairs whose verdict source != 'model'): **{metrics['n_failsafe']}**")
    lines.append("")
    lines.append("## Case Counts (separate integers, never only a percentage)")
    lines.append("")
    lines.append(f"- Negatives in golden set (label=no_merge, non-excluded): {negatives_in_set}")
    lines.append(f"- Negatives actually adjudicated by the LLM (proposed=true, label=no_merge): {negatives_adjudicated}")
    lines.append(f"- Positives adjudicated by the LLM (proposed=true, label=merge): {positives_adjudicated}")
    lines.append(f"- Pairs filtered pre-LLM (proposed=false, non-excluded): {filtered_pre_llm}")
    lines.append(f"- negatives_adjudicated / negatives = {negatives_adjudicated}/{negatives_in_set}")
    lines.append("")
    lines.append("## Confidence Distribution")
    lines.append("")
    lines.append(f"Over `proposed_pairs` only (n={n_proposed}): high={conf_high}, low={conf_low}.")
    if conf_low == 0:
        lines.append(
            f"The `confidence == 'high'` condition rejected 0 pairs on this "
            f"golden set; measured precision rests entirely on `same_event`."
        )
    lines.append("")
    lines.append("## Honest Reduction Ratio (Frozen Pre-filter)")
    lines.append("")
    lines.append(
        f"`total_possible_in_bucket_pairs` (from `26-CALL-LOG.md`): **{total_possible}**. "
        f"Pairs actually proposed by the pre-filter (proposed=true, non-excluded): **{n_proposed}**. "
        f"Reduction ratio: **~{reduction_pct}**."
    )
    lines.append(
        "On the two mandatory buckets the expected reduction is approx 0% "
        "(min observed `token_set_ratio` = 48.7 against a frozen threshold "
        "of 45.0). The real cost bound in this phase is `(cut,date)` "
        "bucketing itself, not the lexical pre-filter. Largest observed "
        "bucket sizes: comuna 2101/2026-07-01 has 9 articles -> 36 possible "
        "pairs; comuna 4102 (Tongoy)/2026-07-01 has 8 articles -> 28 "
        "possible pairs. (For context, a hypothetical 26-article bucket "
        "would yield 325 possible pairs, a 16-article bucket 120 possible "
        "pairs — no bucket in this sample reaches that size.)"
    )
    lines.append("")
    lines.append("## Second-Pass Label Confirmation")
    lines.append("")
    lines.append(
        f"merge-labels independently confirmed: {second_pass_confirmed}/"
        f"{len(merge_labels_non_excluded)} (blind second pass)"
    )
    if blind:
        lines.append(
            f"Blind second pass performed by: {blind.get('performed_by', 'n/a')} on "
            f"{blind.get('date', 'n/a')}. Raw totals over ALL merge-labeled pairs "
            f"(pre-exclusion): same={blind.get('raw_totals', {}).get('same')}, "
            f"different={blind.get('raw_totals', {}).get('different')}, "
            f"unsure={blind.get('raw_totals', {}).get('unsure')}. "
            f"{blind.get('merge_labels_disputed_excluded', 0)} pairs excluded as "
            f"`label_disputed` (F-13)."
        )
    lines.append("")
    lines.append("## Excluded / Disputed Pairs (label_disputed, out of precision/recall denominator)")
    lines.append("")
    if excluded_pairs:
        lines.append("| pair_id | excluded reason | label (pre-exclusion) | note |")
        lines.append("|---|---|---|---|")
        for p in excluded_pairs:
            lines.append(
                f"| {p['pair_id']} | {p.get('excluded')} | {p.get('label')} | "
                f"{(p.get('note') or '').replace(chr(10), ' ')[:160]} |"
            )
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Cluster Assembly")
    lines.append("")
    lines.append(
        f"`assemble_clusters()` over the full non-excluded incident-ID "
        f"universe and the merge-edge list drawn from `proposed_pairs` per "
        f"the mergeable-state rule: {len(clusters)} normal cluster(s), "
        f"{len(flagged)} flagged (oversized, >4 members) cluster(s)."
    )
    if clusters or flagged:
        lines.append("")
        lines.append("| cluster_id (sha256) | members | flagged |")
        lines.append("|---|---|---|")
        for members in clusters.values():
            lines.append(f"| {cluster_id(members)} | {', '.join(sorted(members))} | no |")
        for members in flagged.values():
            lines.append(f"| {cluster_id(members)} | {', '.join(sorted(members))} | YES |")
    lines.append("")

    # False-merge failure-mode analysis -- the most valuable output of the
    # whole spike for Phase 27/28.
    fp_pairs = [p for p in proposed_pairs if p["label"] == "no_merge" and _edge_drawn(p)]
    lines.append("## False-Merge Failure-Mode Analysis")
    lines.append("")
    lines.append(
        f"{len(fp_pairs)} false-merge pair(s) — every pair below was a "
        f"genuine model error (see F-15: 2 independent blind reviewers "
        f"judged all 11 FP pairs, 22/22 unanimous `different`, zero `same`, "
        f"zero `unsure`)."
    )
    lines.append("")
    if fp_pairs:
        lines.append("| pair_id | title_a | title_b | failure mode |")
        lines.append("|---|---|---|---|")
        for p in fp_pairs:
            ta = p["title_a"].replace("|", "/")
            tb = p["title_b"].replace("|", "/")
            rationale = p["cached_verdict"].get("rationale", "")
            # Heuristic failure-mode characterization from title/rationale text.
            mode = "aggregate-vs-component"
            if "detenidos" in ta.lower() or "detenidos" in tb.lower() or "operativo" in ta.lower() or "operativo" in tb.lower():
                if "condena" in ta.lower() or "condena" in tb.lower() or "años" in ta.lower() or "años" in tb.lower():
                    mode = "procedural-stage (arrest vs. sentencing conflated)"
                else:
                    mode = "aggregate-vs-component (same operativo, different sub-reports merged)"
            elif "años" in ta.lower() and "años" in tb.lower():
                mode = "conflicting-sentence (different sentence details treated as same case)"
            lines.append(f"| {p['pair_id']} | {ta} | {tb} | {mode} — {rationale[:100]} |")
    lines.append("")

    lines.append("## Full Pairwise Decision Matrix")
    lines.append("")
    lines.append(f"One row per non-excluded golden-set pair (n={len(non_excluded)}).")
    lines.append("")
    lines.append(
        "| pair_id | category | proposed | golden label | same_event | confidence | edge drawn | classification |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for p in non_excluded:
        proposed = p.get("proposed")
        if proposed is True:
            cv = p["cached_verdict"]
            same_event = str(cv.get("same_event"))
            confidence = str(cv.get("confidence"))
        else:
            same_event = "n/a (prefiltered)"
            confidence = "n/a (prefiltered)"
        edge = "yes" if _edge_drawn(p) else "no"
        cls = _classification(p)
        lines.append(
            f"| {p['pair_id']} | {p.get('category')} | {proposed} | {p.get('label')} | "
            f"{same_event} | {confidence} | {edge} | {cls} |"
        )
    lines.append("")

    lines.append("## GO/NO-GO Verdict")
    lines.append("")
    lines.append(
        f"Precision={precision_str.split(' ')[0]}, FP={metrics['fp']}, "
        f"TP={metrics['tp']}, n_failsafe={metrics['n_failsafe']}."
    )
    lines.append("")
    lines.append(
        "**GO/NO-GO verdict: [PENDING — Fable orchestrator confirms against "
        "locked gate: 100% precision, 0 false merges, tp > 0, n_failsafe == 0]**"
    )
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    fixture = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    pairs = fixture["pairs"]

    metrics = compute_pairwise_metrics(pairs)

    non_excluded = [p for p in pairs if not p.get("excluded")]
    proposed_pairs = [p for p in non_excluded if p.get("proposed") is True]

    incident_ids: set[str] = set()
    for p in non_excluded:
        incident_ids.add(p["incident_a_id"])
        incident_ids.add(p["incident_b_id"])

    merge_edges = [
        (p["incident_a_id"], p["incident_b_id"]) for p in proposed_pairs if _edge_drawn(p)
    ]

    clusters, flagged = assemble_clusters(sorted(incident_ids), merge_edges, max_size=4)

    # Assert no cluster with a false-merge edge silently escapes review: a
    # false-merge edge only exists between incidents whose combined pair is
    # an FP; cross-check that any such incident pair, if it lands in a
    # component, is present in either `clusters` or `flagged` (never simply
    # dropped).
    fp_incident_ids = {
        iid
        for p in proposed_pairs
        if p["label"] == "no_merge" and _edge_drawn(p)
        for iid in (p["incident_a_id"], p["incident_b_id"])
    }
    all_component_members = set()
    for members in list(clusters.values()) + list(flagged.values()):
        all_component_members.update(members)
    missing = fp_incident_ids - all_component_members
    assert not missing, f"FP-involved incidents missing from clusters/flagged: {missing}"

    report = _build_report(fixture, metrics, clusters, flagged)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(json.dumps(metrics, indent=2))
    print(f"\nWrote report to {REPORT_PATH}")
    print(f"clusters={len(clusters)} flagged={len(flagged)}")


if __name__ == "__main__":
    main()
