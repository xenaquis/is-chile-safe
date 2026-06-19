"""
pipeline/snapshots/fetch_fiscalia_secuestro.py

Source:   Fiscalia de Chile — Boletin Estadistico / Informe de Fenomenos Criminales: Secuestro
URL:      https://www.fiscaliadechile.cl/persecucion-penal/estadisticas
Vintage:  2023-2024 (regional aggregates from Wave 0 research, 2026-06-18)
Licence:  Public institutional statistics (Chile)

No machine-readable download exists (reports are PDFs only as of Wave 0 2026-06-18).
This script embeds the known regional secuestro series from the Wave 0 spike (S5)
and writes data/snapshots/fiscalia_secuestro.json.

Granularity is REGIONAL (fiscalia regions, which do NOT map 1:1 to administrative
regions — e.g., RM is split into RM Sur, RM Centro Norte, RM Oriente).
Comuna-level data was NOT found in any downloadable source (S5b deferred).

All figures are traceable to the Fiscalia Boletin Estadistico.

Run:
  python pipeline/snapshots/fetch_fiscalia_secuestro.py
"""
from __future__ import annotations

import logging
import sys
import pathlib
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pipeline.shared.atomic_write import atomic_write_json  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

OUTPUT_FILE = REPO_ROOT / "data" / "snapshots" / "fiscalia_secuestro.json"

# -------------------------------------------------------------------------
# Static series from Wave 0 S5 spike (2026-06-18).
# Source: Fiscalia de Chile — Boletin Estadistico / Informe de Fenomenos
#         Criminales: Secuestro (PDF reports).
# National totals confirmed: 2023=850, 2024=868 (+2.1%).
# Regional breakdown: top regions in 2024 are RM Sur, RM Centro Norte,
# Valparaiso. Per-region counts for most regions were not extracted from PDF
# in Wave 0; those are listed as None (awaiting S5b or future manual extraction).
# -------------------------------------------------------------------------
KNOWN_RECORDS = [
    # National totals (fiscal-year = calendar-year)
    {"region": "Nacional", "year": 2023, "secuestros": 850},
    {"region": "Nacional", "year": 2024, "secuestros": 868},
    # Regional breakdown 2024 — top regions confirmed from Wave 0 S5
    # Exact per-region counts not extracted from PDF in Wave 0; flagged as top-N.
    {"region": "RM Sur (Fiscalia)", "year": 2024, "secuestros": None,
     "note": "Top region 2024; exact count not extracted from PDF in Wave 0"},
    {"region": "RM Centro Norte (Fiscalia)", "year": 2024, "secuestros": None,
     "note": "Top region 2024; exact count not extracted from PDF in Wave 0"},
    {"region": "Valparaiso (Fiscalia)", "year": 2024, "secuestros": None,
     "note": "Top region 2024; exact count not extracted from PDF in Wave 0"},
]


def main() -> None:
    if not KNOWN_RECORDS:
        raise RuntimeError("KNOWN_RECORDS is empty — refusing to overwrite snapshot.")

    payload = {
        "source": "Fiscalia de Chile — Boletin Estadistico / Informe de Fenomenos Criminales: Secuestro",
        "source_url": "https://www.fiscaliadechile.cl/persecucion-penal/estadisticas",
        "vintage": "2023-2024",
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "caveat": (
            "Regional granularity only: Fiscalia regions do NOT map 1:1 to administrative "
            "regions (RM is split into multiple fiscalias: RM Sur, RM Centro Norte, "
            "RM Oriente, etc.). "
            "No downloadable commune-level dataset was found (reports are PDFs); "
            "commune-level secuestro data is deferred to S5b / Phase 18. "
            "This snapshot embeds static figures extracted manually from the Fiscalia "
            "Boletin Estadistico PDF (Wave 0 spike S5, 2026-06-18). "
            "REFERENCE-ONLY — not wired to any displayed metric."
        ),
        "records": KNOWN_RECORDS,
    }

    atomic_write_json(OUTPUT_FILE, payload)
    log.info("Wrote %d records to %s", len(KNOWN_RECORDS), OUTPUT_FILE)


if __name__ == "__main__":
    main()
