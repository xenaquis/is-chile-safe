"""
pipeline/build_enusc_enrichment.py

Additive enrichment: writes the enusc_vhdv key into the 136 covered commune JSONs.

Guarantees:
  - Additive-only: touches NO existing key in commune JSON files.
  - Graceful degrade: if enusc_vhdv.json is absent, exits 0 (CEAD pipeline never broken).
  - Coverage assertion: RuntimeError if resolved != EXPECTED_COVERAGE (136).
  - Overwrite-refusal: RuntimeError if enusc_vhdv is already set to a DIFFERENT value.
  - Idempotent: re-running with identical snapshot is a no-op (no error).

Phase-18 fields that MUST remain byte-unchanged:
  composite_index, featured_rates, series, national_rank, regional_rank,
  trend, spd_homicide_rate, sii_exposure_index

Run:
    python pipeline/build_enusc_enrichment.py
"""
from __future__ import annotations

import json
import logging
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).parent.parent
EXPECTED_COVERAGE = 136

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

sys.path.insert(0, str(REPO_ROOT))

from pipeline.shared.atomic_write import atomic_write_json  # noqa: E402


def main() -> None:
    data_dir = REPO_ROOT / "data" / "cead"
    snapshot_path = REPO_ROOT / "data" / "snapshots" / "enusc_vhdv.json"

    # VL-01: graceful degrade when snapshot absent
    if not snapshot_path.exists():
        log.warning(
            "enusc_vhdv.json not found at %s — skipping enrichment "
            "(ENUSC fetch step may have failed; CEAD pipeline continues unaffected)",
            snapshot_path,
        )
        sys.exit(0)

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    enusc_by_cut = {r["cut"]: r for r in snapshot["records"]}

    resolved = 0
    for cut, vhdv_data in enusc_by_cut.items():
        commune_path = data_dir / "comunas" / f"{cut}.json"
        if not commune_path.exists():
            log.warning("CUT %s not found in comunas/ — skipping", cut)
            continue

        commune = json.loads(commune_path.read_text(encoding="utf-8"))

        new_vhdv = {
            "vhdv_rate": vhdv_data["vhdv_rate"],
            "ci_lower": vhdv_data["ci_lower"],
            "ci_upper": vhdv_data["ci_upper"],
            "tipo_estimacion": vhdv_data["tipo_estimacion"],
            "cv": vhdv_data["cv"],
            "vintage": 2024,
        }

        existing = commune.get("enusc_vhdv")
        if existing is not None and existing != new_vhdv:
            raise RuntimeError(
                f"enusc_vhdv already set differently for CUT {cut} — refusing overwrite. "
                f"Existing: {existing!r}. New: {new_vhdv!r}"
            )

        # Additive only: set enusc_vhdv, touch NO other key
        commune["enusc_vhdv"] = new_vhdv
        atomic_write_json(commune_path, commune)
        resolved += 1

    # VL-02: build-time coverage assertion
    if resolved != EXPECTED_COVERAGE:
        raise RuntimeError(
            f"Coverage assertion failed: expected {EXPECTED_COVERAGE} CUTs resolved, "
            f"got {resolved}. Check that all 136 ENUSC CUTs exist in data/cead/comunas/."
        )

    log.info("Enriched %d commune files with enusc_vhdv", resolved)


if __name__ == "__main__":
    main()
