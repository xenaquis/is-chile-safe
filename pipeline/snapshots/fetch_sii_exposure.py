"""
pipeline/snapshots/fetch_sii_exposure.py

Source:   SII — Estadisticas de empresas por comuna
URL:      https://www.sii.cl/sobre_el_sii/empresas/PUB_COMU.xlsb
Vintage:  2005-2024 (updated Oct 2025)
Licence:  Datos Abiertos Gobierno de Chile

Produces: data/snapshots/sii_exposure.json
  {source, source_url, vintage, fetched, caveat,
   records:[{cut, name, year, empresas, trabajadores}]}

CACHE_ONLY=1: parse from pipeline/cache/sii_pub_comu.xlsb, skip network download.

Run:
  CACHE_ONLY=1 python pipeline/snapshots/fetch_sii_exposure.py
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
CACHE_FILE = CACHE_DIR / "sii_pub_comu.xlsb"
OUTPUT_FILE = REPO_ROOT / "data" / "snapshots" / "sii_exposure.json"
INDEX_FILE = REPO_ROOT / "data" / "cead" / "meta" / "index.json"

SII_URL = "https://www.sii.cl/sobre_el_sii/empresas/PUB_COMU.xlsb"
SHEET = "Datos"
HEADER_ROW = 4
MIN_RECORDS = 200

# Row to drop — the "Sin Informacion" bucket is not a real commune
SIN_INFO_SLUG = "sin-informacion"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
def _download(url: str, dest: pathlib.Path) -> None:
    import requests  # lazy import

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; IsChileSafe data pipeline; +https://ischilesafe.com)"
        ),
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
    }
    log.info("Downloading %s ...", url)
    time.sleep(1)  # courtesy delay for government host
    r = requests.get(url, headers=headers, timeout=180)
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
        _download(SII_URL, CACHE_FILE)
    else:
        log.info("CACHE_ONLY=1 — skipping download, parsing %s", CACHE_FILE)

    if not CACHE_FILE.exists():
        raise FileNotFoundError(
            f"Cache file not found: {CACHE_FILE}. "
            "Run without CACHE_ONLY=1 to download it first."
        )

    log.info("Parsing %s (sheet=%s, header=%d) ...", CACHE_FILE, SHEET, HEADER_ROW)
    try:
        df = pd.read_excel(
            str(CACHE_FILE),
            sheet_name=SHEET,
            header=HEADER_ROW,
            engine="pyxlsb",
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to parse {CACHE_FILE}: {exc}. "
            "File may be corrupt or the sheet/header changed."
        ) from exc

    # Columns are accessed by position (pyxlsb encoding varies on some systems).
    # Position map (confirmed via Wave 0 probe):
    #   0 = Anio Comercial
    #   1 = Comuna del domicilio o casa matriz
    #   4 = Numero de empresas
    #   6 = Numero de trabajadores dependientes informados
    #   8 = Trabajadores ponderados por meses trabajados
    if df.shape[1] < 9:
        raise RuntimeError(
            f"SII sheet has only {df.shape[1]} columns; expected at least 9. "
            "File format may have changed."
        )

    cols = list(df.columns)
    col_year = cols[0]
    col_comuna = cols[1]
    col_empresas = cols[4]
    col_trabajadores = cols[6]
    # col_trabajadores_ponderados = cols[8]  # available but not output per plan

    log.info(
        "Using columns: year=%r, comuna=%r, empresas=%r, trabajadores=%r",
        col_year,
        col_comuna,
        col_empresas,
        col_trabajadores,
    )

    # Drop rows missing year or commune name
    df = df.dropna(subset=[col_year, col_comuna])

    # Drop the "Sin Informacion" bucket row
    sin_mask = df[col_comuna].astype(str).apply(make_slug) == SIN_INFO_SLUG
    dropped_sin = sin_mask.sum()
    if dropped_sin > 0:
        log.info("Dropped %d 'Sin Informacion' rows", dropped_sin)
    df = df[~sin_mask]

    # Coerce numerics
    df[col_year] = pd.to_numeric(df[col_year], errors="coerce")
    df[col_empresas] = pd.to_numeric(df[col_empresas], errors="coerce")
    df[col_trabajadores] = pd.to_numeric(df[col_trabajadores], errors="coerce")
    df = df.dropna(subset=[col_year])
    df[col_year] = df[col_year].astype(int)

    # Build CUT join map
    cut_map = _build_cut_map()

    records = []
    unmatched: set[str] = set()

    for _, row in df.iterrows():
        comun_name: str = str(row[col_comuna]).strip()
        slug = make_slug(comun_name)
        if slug in cut_map:
            cut, canonical = cut_map[slug]
            try:
                emp = int(row[col_empresas]) if pd.notna(row[col_empresas]) else None
                trab = int(row[col_trabajadores]) if pd.notna(row[col_trabajadores]) else None
            except (ValueError, OverflowError) as exc:
                log.warning("SII: skipping row with bad numeric value in %s: %s", comun_name, exc)
                continue
            records.append(
                {
                    "cut": cut,
                    "name": canonical,
                    "year": int(row[col_year]),
                    "empresas": emp,
                    "trabajadores": trab,
                }
            )
        else:
            unmatched.add(comun_name)

    if unmatched:
        log.warning(
            "SII: %d commune names could not be joined to CUT (logging all): %s",
            len(unmatched),
            sorted(unmatched),
        )

    if len(records) < MIN_RECORDS:
        raise RuntimeError(
            f"Record count guard failed: expected >{MIN_RECORDS} records, "
            f"got {len(records)}. Parse may be truncated."
        )

    payload = {
        "source": "Servicio de Impuestos Internos (SII) — Estadisticas de empresas por comuna",
        "source_url": SII_URL,
        "vintage": "2005-2024",
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "caveat": (
            "Domicile/HQ artifact: the commune is the firm's registered domicilio or casa "
            "matriz, not the physical work establishment. Multi-site firms attribute all "
            "workers to HQ, concentrating counts in business-district communes (Las Condes, "
            "Santiago, Providencia). Use as daytime-activity exposure proxy with awareness "
            "of this bias. REFERENCE-ONLY — not wired to any displayed metric."
        ),
        "records": sorted(records, key=lambda r: (r["cut"], r["year"])),
    }

    atomic_write_json(OUTPUT_FILE, payload)
    log.info("Wrote %d records to %s", len(records), OUTPUT_FILE)
    if unmatched:
        log.warning("Unmatched SII commune names (investigate join): %s", sorted(unmatched))


if __name__ == "__main__":
    main()
