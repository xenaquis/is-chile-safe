#!/usr/bin/env python3
"""
pipeline/scripts/audit_incidents.py

D-16 human-UAT gate: read-only audit tool for spot-checking commune assignment.

Default (TSV) mode reads data/incidents/current.json, samples up to 50 random
incidents, and prints a TSV table of (title_es, outlet, url, assigned_cut,
commune_name) to stdout for human review of commune hallucination.

Scored mode (`--score`, GL-03) samples up to 50 incidents and, for each, checks
whether the stored `cut` is internally consistent: a valid index CUT resolves to
a slug via pipeline.news.resolver.slug_for_cut. Any incident whose stored cut is
NOT in the closed 346-commune index counts as a resolver failure (hallucinated /
orphan assignment). It prints a machine accuracy figure and a PASS/FAIL line
against ACCURACY_THRESHOLD. The scored summary intentionally omits incident URLs
and titles — counts and accuracy only. Scored mode adds no network or LLM calls;
it is deterministic and offline.

Usage:
  python pipeline/scripts/audit_incidents.py            # TSV human-review mode
  python pipeline/scripts/audit_incidents.py --score    # machine-scored accuracy gate

Exit codes:
  0 = TSV table printed, OR scored accuracy >= ACCURACY_THRESHOLD
  1 = current.json not found (run scrape_news.py first)
  2 = scored mode only: accuracy < ACCURACY_THRESHOLD
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys

# Ensure the repo root is importable when run standalone
# (`python pipeline/scripts/audit_incidents.py`): sys.path[0] would otherwise be
# this script's directory, hiding the top-level `pipeline` package. Harmless under
# pytest (pythonpath=.. already puts the repo root on the path).
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.news.resolver import slug_for_cut  # noqa: E402
INCIDENTS_PATH = REPO_ROOT / "data" / "incidents" / "current.json"
COMUNAS_DIR = REPO_ROOT / "data" / "cead" / "comunas"

# GL-03 gate. Prior phases reported ~95% name→CUT resolver accuracy
# (Phase 16, name→CUT resolver 95.45% comuna accuracy); 0.90 leaves headroom for
# 50-incident sampling variance while still failing on material hallucination.
ACCURACY_THRESHOLD = 0.90

SAMPLE_SIZE = 50

# Lazy-load commune name lookup from static JSON files
_COMMUNE_NAMES: dict[str, str] | None = None


def _get_commune_name(cut: str) -> str:
    global _COMMUNE_NAMES
    if _COMMUNE_NAMES is None:
        _COMMUNE_NAMES = {}
        for path in COMUNAS_DIR.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                commune_cut = path.stem
                name = data.get("name", "")
                if name:
                    _COMMUNE_NAMES[commune_cut] = name
            except Exception:
                pass
    return _COMMUNE_NAMES.get(cut, f"CUT={cut}")


def score_incidents(
    incidents: list[dict],
    sample_size: int = SAMPLE_SIZE,
    rng: random.Random | None = None,
) -> tuple[int, int, float]:
    """Score a list of incident records for resolver consistency.

    A stored ``cut`` is valid when it resolves to a slug in the closed index
    (``slug_for_cut(cut) is not None``). Returns ``(sampled, valid, accuracy)``
    where accuracy = valid / sampled (0.0 when nothing was sampled).
    """
    n = min(sample_size, len(incidents))
    if n == 0:
        return (0, 0, 0.0)
    picker = rng or random
    sample = picker.sample(incidents, n)
    valid = sum(1 for inc in sample if slug_for_cut(inc.get("cut", "")) is not None)
    return (n, valid, valid / n)


def run_scored(incidents_path: pathlib.Path = INCIDENTS_PATH) -> int:
    """Scored accuracy mode. Returns the process exit code (0 / 1 / 2)."""
    if not incidents_path.exists():
        print(f"ERROR: {incidents_path} not found — run scrape_news.py first.")
        return 1

    data = json.loads(incidents_path.read_text(encoding="utf-8"))
    incidents = data.get("incidents", [])

    if not incidents:
        print(f"ERROR: no incidents in {incidents_path} — nothing to score.")
        return 1

    sampled, valid, accuracy = score_incidents(incidents)
    result = "PASS" if accuracy >= ACCURACY_THRESHOLD else "FAIL"
    # Counts + accuracy only — no incident URLs or titles in the scored summary.
    print(
        f"SCORED AUDIT: sampled={sampled} valid_cut={valid} "
        f"accuracy={accuracy:.3f} threshold={ACCURACY_THRESHOLD:.2f}"
    )
    print(f"RESULT: {result}")
    return 0 if accuracy >= ACCURACY_THRESHOLD else 2


def run_tsv(incidents_path: pathlib.Path = INCIDENTS_PATH) -> int:
    """Default human-review TSV mode (behavior preserved from D-16)."""
    if not incidents_path.exists():
        raise SystemExit(
            f"ERROR: {incidents_path} not found — run scrape_news.py first."
        )

    data = json.loads(incidents_path.read_text(encoding="utf-8"))
    incidents = data.get("incidents", [])

    if not incidents:
        print("No incidents found in current.json.")
        return 0

    sample_size = min(SAMPLE_SIZE, len(incidents))
    sample = random.sample(incidents, sample_size)

    header = "\t".join(["#", "title_es", "outlet", "url", "cut", "commune"])
    separator = "-" * 120
    print(separator)
    print(f"AUDIT: {sample_size} of {len(incidents)} incidents sampled from {incidents_path}")
    print(f"Generated: {data.get('generated', 'unknown')}")
    print(separator)
    print(header)
    print(separator)

    for i, inc in enumerate(sample, 1):
        cut = inc.get("cut", "")
        commune_name = _get_commune_name(cut)
        row = "\t".join([
            str(i),
            inc.get("title_es", "")[:80],
            inc.get("outlet", ""),
            inc.get("url", "")[:80],
            cut,
            commune_name,
        ])
        print(row)

    print(separator)
    print("Review: verify each assigned commune matches the article location.")
    print("Flag hallucinations where commune name clearly does not match the article.")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Audit commune assignment in data/incidents/current.json."
    )
    parser.add_argument(
        "--score",
        action="store_true",
        help="machine-scored accuracy gate (GL-03): prints accuracy + PASS/FAIL, "
        "exits 0 (>= threshold), 2 (< threshold), or 1 (current.json missing).",
    )
    args = parser.parse_args(argv)

    if args.score:
        raise SystemExit(run_scored())
    run_tsv()


if __name__ == "__main__":
    main()
