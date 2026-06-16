#!/usr/bin/env python3
"""
One-off data migration for backlog 999.1 (tarapaca-region-id-collision).

Re-derives every commune's region_id from its CUT by length (regions 1-9 are
4-digit CUTs, 10-16 are 5-digit), recomputes regional_rank with the corrected
grouping, and regenerates regions/*.json, national.json and meta/index.json
from the existing per-commune JSON — NO CEAD re-scrape.

Idempotent: running twice produces the same output. Run from repo root:
    python .planning/quick/260616-ldi-*/migrate_region_id.py
"""
from __future__ import annotations
import json, glob, datetime, pathlib

from pipeline.scrape_cead import (
    region_id_from_cut,
    _build_region_aggregates,
    _build_national_aggregate,
    build_meta_index,
)
from pipeline.cead.normalizer import compute_ranks
from pipeline.shared.schema import validate_all_communes
from pipeline.shared.atomic_write import atomic_write_json

DATA = pathlib.Path("data/cead")


def main() -> int:
    communes = [json.load(open(f, encoding="utf-8")) for f in glob.glob(str(DATA / "comunas" / "*.json"))]
    assert len(communes) == 346, f"expected 346 communes, got {len(communes)}"

    # Before snapshot for the collision pair
    before = {c["id"]: c["region_id"] for c in communes if c["id"] in ("1101", "1107", "11201", "5101")}

    # 1. Re-derive region_id (length-aware)
    changed = 0
    for c in communes:
        new = region_id_from_cut(c["id"])
        if c["region_id"] != new:
            changed += 1
        c["region_id"] = new

    # 2. Recompute ranks with corrected grouping (latest complete year)
    latest_year = max(
        (yr["year"] for c in communes for yr in c["series"] if not yr.get("partial")),
        default=datetime.date.today().year - 1,
    )
    compute_ranks(communes, year=latest_year)

    # 3. Validate (346 + plausibility) BEFORE writing anything (D-14)
    validate_all_communes(communes)

    # 4. Rebuild aggregates + meta index
    run_date = datetime.date.today()
    regions = _build_region_aggregates(communes, run_date)
    national = _build_national_aggregate(communes, run_date)
    meta_index = build_meta_index(communes)

    # 5. Write everything atomically
    for c in communes:
        atomic_write_json(DATA / "comunas" / f"{c['id']}.json", c)
    for rid, rdata in regions.items():
        atomic_write_json(DATA / "regions" / f"{rid}.json", rdata)
    atomic_write_json(DATA / "national.json", national)
    atomic_write_json(DATA / "meta" / "index.json", meta_index)

    # 6. Report
    after = {c["id"]: c["region_id"] for c in communes if c["id"] in ("1101", "1107", "11201", "5101")}
    print(f"region_id changed for {changed}/346 communes; latest_year={latest_year}")
    print("collision pair before -> after:")
    for cut in ("1101", "1107", "11201", "5101"):
        print(f"  {cut}: {before[cut]} -> {after[cut]}")
    empty = [rid for rid, r in regions.items() if not r["series"]]
    print(f"regions with empty series after migration: {sorted(empty, key=int) or 'NONE'}")
    san = next(c for c in communes if c["id"] == "13101")
    print(f"Santiago national_rank={san['national_rank']} regional_rank={san['regional_rank']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
