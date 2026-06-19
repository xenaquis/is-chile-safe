"""
pipeline/snapshots/fetch_spd_homicide.py

Source:   Subsecretaria de Prevencion del Delito / Centro para la Prevencion de Homicidios
URL:      https://prevenciondehomicidios.cl/wp-content/uploads/2026/03/Base_de_Datos_VHC_2018_2025.xlsx
Vintage:  2018-2025 (2025 partial/unconsolidated)
Licence:  Datos Abiertos Gobierno de Chile

Produces: data/snapshots/spd_homicide.json
  {source, source_url, vintage, fetched, caveat, records:[{cut, name, year, homicides}]}

CACHE_ONLY=1: parse from pipeline/cache/spd_vhc.xlsx, skip network download.

Run:
  CACHE_ONLY=1 python pipeline/snapshots/fetch_spd_homicide.py
"""
from __future__ import annotations

import json
import logging
import os
import sys
import pathlib
import time
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd  # noqa: E402
from tenacity import retry, stop_after_attempt, wait_exponential  # noqa: E402

from pipeline.cead.normalizer import make_slug  # noqa: E402
from pipeline.shared.atomic_write import atomic_write_json  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

CACHE_DIR = REPO_ROOT / "pipeline" / "cache"
CACHE_FILE = CACHE_DIR / "spd_vhc.xlsx"
OUTPUT_FILE = REPO_ROOT / "data" / "snapshots" / "spd_homicide.json"
INDEX_FILE = REPO_ROOT / "data" / "cead" / "meta" / "index.json"

SPD_URL = (
    "https://prevenciondehomicidios.cl/wp-content/uploads/2026/03/"
    "Base_de_Datos_VHC_2018_2025.xlsx"
)
MIN_RECORDS = 200
SHEET = "Base de Datos"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
def _download(url: str, dest: pathlib.Path) -> None:
    import requests  # lazy import — not needed in CACHE_ONLY mode

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; IsChileSafe data pipeline; +https://ischilesafe.com)"
        ),
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
    }
    log.info("Downloading %s ...", url)
    time.sleep(1)  # courtesy delay for government host
    r = requests.get(url, headers=headers, timeout=120)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    log.info("Saved %d bytes to %s", len(r.content), dest)


def _build_cut_map() -> dict[str, tuple[str, str]]:
    """Build slug -> (cut, canonical_name) from data/cead/meta/index.json."""
    entries = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    result: dict[str, tuple[str, str]] = {}
    for entry in entries:
        slug = make_slug(entry["name"])
        result[slug] = (entry["cut"], entry["name"])
    return result


def main() -> None:
    cache_only = os.environ.get("CACHE_ONLY", "").strip() in ("1", "true", "yes")

    if not cache_only:
        _download(SPD_URL, CACHE_FILE)
    else:
        log.info("CACHE_ONLY=1 — skipping download, parsing %s", CACHE_FILE)

    if not CACHE_FILE.exists():
        raise FileNotFoundError(
            f"Cache file not found: {CACHE_FILE}. "
            "Run without CACHE_ONLY=1 to download it first."
        )

    log.info("Parsing %s ...", CACHE_FILE)
    try:
        df = pd.read_excel(str(CACHE_FILE), sheet_name=SHEET, engine="openpyxl")
    except Exception as exc:
        raise RuntimeError(
            f"Failed to parse {CACHE_FILE}: {exc}. "
            "File may be corrupt or the sheet name changed."
        ) from exc

    required_cols = {"COMUN_AGR", "ID_ANO"}
    missing = required_cols - set(df.columns)
    if missing:
        raise RuntimeError(
            f"Expected columns {required_cols} not found in sheet '{SHEET}'. "
            f"Found: {list(df.columns)}"
        )

    # Count rows per (COMUN_AGR, ID_ANO) — each row is one victim
    df = df.dropna(subset=["COMUN_AGR", "ID_ANO"])
    agg = (
        df.groupby(["COMUN_AGR", "ID_ANO"])
        .size()
        .reset_index(name="homicides")
    )
    agg["ID_ANO"] = agg["ID_ANO"].astype(int)

    # Build CUT join map
    cut_map = _build_cut_map()

    records = []
    unmatched: set[str] = set()

    for _, row in agg.iterrows():
        comun_name: str = str(row["COMUN_AGR"]).strip()
        slug = make_slug(comun_name)
        if slug in cut_map:
            cut, canonical = cut_map[slug]
            records.append(
                {
                    "cut": cut,
                    "name": canonical,
                    "year": int(row["ID_ANO"]),
                    "homicides": int(row["homicides"]),
                }
            )
        else:
            unmatched.add(comun_name)

    if unmatched:
        log.warning(
            "SPD: %d COMUN_AGR names could not be joined to CUT (logging all): %s",
            len(unmatched),
            sorted(unmatched),
        )

    if len(records) < MIN_RECORDS:
        raise RuntimeError(
            f"Record count guard failed: expected >{MIN_RECORDS} records, "
            f"got {len(records)}. Parse may be truncated."
        )

    payload = {
        "source": "Subsecretaria de Prevencion del Delito / Centro para la Prevencion de Homicidios",
        "source_url": SPD_URL,
        "vintage": "2018-2025",
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "caveat": (
            "2025 data is partial and unconsolidated. "
            "Homicide count = victim-level row count per (COMUN_AGR, ID_ANO); "
            "communes with zero homicides 2018-2025 are absent (not zeroed). "
            "COMUN_AGR joined to CUT via make_slug normalization — ~31 communes "
            "expected absent (genuinely zero, not bucketed). "
            "REFERENCE-ONLY — not wired to any displayed metric."
        ),
        "records": sorted(records, key=lambda r: (r["cut"], r["year"])),
    }

    atomic_write_json(OUTPUT_FILE, payload)
    log.info(
        "Wrote %d records to %s",
        len(records),
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()
