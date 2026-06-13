#!/usr/bin/env python3
"""
pipeline/scripts/audit_incidents.py

D-16 human-UAT gate: read-only audit tool for spot-checking commune assignment.

Reads data/incidents/current.json, samples up to 50 random incidents,
and prints a TSV table of (title_es, outlet, url, assigned_cut, commune_name)
to stdout for human review of commune hallucination.

Usage:
  python pipeline/scripts/audit_incidents.py

Exit codes:
  0 = audit table printed successfully
  1 = current.json not found (run scrape_news.py first)
"""
from __future__ import annotations

import json
import pathlib
import random

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
INCIDENTS_PATH = REPO_ROOT / "data" / "incidents" / "current.json"
COMUNAS_DIR = REPO_ROOT / "data" / "cead" / "comunas"

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


def main() -> None:
    if not INCIDENTS_PATH.exists():
        raise SystemExit(
            f"ERROR: {INCIDENTS_PATH} not found — run scrape_news.py first."
        )

    data = json.loads(INCIDENTS_PATH.read_text(encoding="utf-8"))
    incidents = data.get("incidents", [])

    if not incidents:
        print("No incidents found in current.json.")
        return

    sample_size = min(50, len(incidents))
    sample = random.sample(incidents, sample_size)

    header = "\t".join(["#", "title_es", "outlet", "url", "cut", "commune"])
    separator = "-" * 120
    print(separator)
    print(f"AUDIT: {sample_size} of {len(incidents)} incidents sampled from {INCIDENTS_PATH}")
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
    print(f"Review: verify each assigned commune matches the article location.")
    print("Flag hallucinations where commune name clearly does not match the article.")


if __name__ == "__main__":
    main()
