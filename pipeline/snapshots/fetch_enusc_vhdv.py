"""
pipeline/snapshots/fetch_enusc_vhdv.py

Source:   INE — Estadisticas Experimentales: Seguridad Ciudadana
Dataset:  ENUSC 2024 — VHDV (Victimizacion en Hogares por Delitos Violentos), modelo SAE
Landing:  https://www.ine.gob.cl/estadisticas/estadisticas-experimentales/seguridad-ciudadana
Vintage:  2024 (SAE first published 2026-01-21)
Licence:  Datos publicos del Estado de Chile (INE terms)

IMPORTANT: The sfvrsn URL below is unstable — INE may rotate it on republish.
The canonical download is manual via the INE "Cuadros Estadisticos" JS widget.
DO NOT run without CACHE_ONLY=1 in CI — pipeline/cache/enusc_vhdv.xlsx is
manually deposited and sha256-pinned.

Produces: data/snapshots/enusc_vhdv.json
  {source, source_url, landing_page, vintage, fetched, caveat, records:[...]}

CACHE_ONLY=1: parse from pipeline/cache/enusc_vhdv.xlsx, skip network download.
              Cache must be manually deposited (INE JS widget, not stable URL).

Run:
  CACHE_ONLY=1 python pipeline/snapshots/fetch_enusc_vhdv.py
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import pathlib
import sys
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
CACHE_FILE = CACHE_DIR / "enusc_vhdv.xlsx"
OUTPUT_FILE = REPO_ROOT / "data" / "snapshots" / "enusc_vhdv.json"
INDEX_FILE = REPO_ROOT / "data" / "cead" / "meta" / "index.json"

# sha256 of the manually-deposited INE XLSX (2026-01-21 release).
# Update if INE republishes the file.
KNOWN_SHA256 = "ad9503826fd21590eca7cf37629872df09f3115ad0c6d80dfe5cedcb63c3d4ba"

# XLSX schema constants (verified against real file in SEED-002)
ENUSC_SHEET = "Hoja1"
ENUSC_HEADER_ROW = 2  # 0-indexed (row 3 in Excel; pandas header=2)
MIN_RECORDS = 136

# Source URLs (sfvrsn parameter may rotate on INE republish)
RESOLVED_URL = (
    "https://www.ine.gob.cl/docs/default-source/estadisticas-experimentales-"
    "seguridad-ciudadana/cuadros-estadisticos/2024/"
    "tabulados-sae--enusc-2024-vhdv.xlsx?sfvrsn=671c099f_4"
)
LANDING_PAGE = (
    "https://www.ine.gob.cl/estadisticas/estadisticas-experimentales/seguridad-ciudadana"
)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
def _download(url: str, dest: pathlib.Path) -> None:
    """Download XLSX from INE. Only called when CACHE_ONLY=0 (manual/development use)."""
    import requests  # lazy import — not needed in CACHE_ONLY mode

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; IsChileSafe data pipeline; +https://ischilesafe.com)"
        ),
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
    }
    log.info("Downloading %s ...", url)
    time.sleep(1)  # courtesy delay
    r = requests.get(url, headers=headers, timeout=120)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    log.info("Saved %d bytes to %s", len(r.content), dest)


def _assert_sha256(path: pathlib.Path) -> None:
    """Verify sha256 of cache file before parse. Raises RuntimeError on mismatch."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != KNOWN_SHA256:
        raise RuntimeError(
            f"sha256 mismatch for {path}: expected {KNOWN_SHA256}, got {digest}. "
            "INE may have republished the file. Re-verify and update KNOWN_SHA256 "
            "in pipeline/snapshots/fetch_enusc_vhdv.py and data/snapshots/ATTRIBUTION.md."
        )
    log.info("sha256 verified: %s", digest)


def _build_cut_map() -> dict[str, tuple[str, str]]:
    """Build slug -> (cut, canonical_name) from data/cead/meta/index.json.
    Used as redundant cross-check only — primary join is direct col-A CUT digits.
    """
    entries = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    result: dict[str, tuple[str, str]] = {}
    for entry in entries:
        slug = make_slug(entry["name"])
        result[slug] = (entry["cut"], entry["name"])
    return result


def main() -> None:
    cache_only = os.environ.get("CACHE_ONLY", "").strip() in ("1", "true", "yes")

    if not cache_only:
        _download(RESOLVED_URL, CACHE_FILE)
    else:
        log.info("CACHE_ONLY=1 — skipping download, parsing %s", CACHE_FILE)

    if not CACHE_FILE.exists():
        raise FileNotFoundError(
            f"Cache file not found: {CACHE_FILE}. "
            "Manually deposit pipeline/cache/enusc_vhdv.xlsx "
            "(download from INE 'Cuadros Estadísticos' widget — see ATTRIBUTION.md). "
            "Do NOT enable non-CACHE_ONLY mode in CI (URL is unstable)."
        )

    # Verify integrity before parse (T-23-01 threat mitigation)
    _assert_sha256(CACHE_FILE)

    log.info("Parsing %s ...", CACHE_FILE)
    try:
        df = pd.read_excel(
            str(CACHE_FILE),
            sheet_name=ENUSC_SHEET,
            header=ENUSC_HEADER_ROW,
            engine="openpyxl",
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to parse {CACHE_FILE}: {exc}. "
            "File may be corrupt or sheet name / header row changed."
        ) from exc

    # Strip whitespace from headers (ENUSC XLSX has trailing spaces/newlines)
    df.columns = [str(c).strip() for c in df.columns]

    # Column name normalization: strip accents from column names for matching.
    # The real XLSX uses slightly different accents than the SEED-002 profile described
    # ("victimas" without accent, "logaritmico" without accent). We match by normalized
    # form to be robust against minor INE encoding variations.
    import unicodedata

    def _norm(s: str) -> str:
        """Normalize accents: NFD decompose, drop combining marks, lowercase."""
        return "".join(
            c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
        ).lower().strip()

    col_norm = {_norm(c): c for c in df.columns}

    # Normalized expected column names
    _EXPECTED_NORM = {
        "codigo comuna": "cut_col",
        "nombre comuna": "name_col",
        "porcentaje de hogares victimas de delitos violentos 2024": "vhdv_col",
        "limite inferior": "ci_lower_col",
        "limite superior": "ci_upper_col",
        "tipo de estimacion": "tipo_col",
        "coeficiente de variacion logaritmico": "cv_col",
    }

    missing_norm = [k for k in _EXPECTED_NORM if k not in col_norm]
    if missing_norm:
        raise RuntimeError(
            f"Expected columns not found in sheet '{ENUSC_SHEET}' (normalized match): {missing_norm}. "
            f"Found columns: {list(df.columns)}"
        )

    # Map normalized keys to actual column names in the file
    cut_col = col_norm["codigo comuna"]
    name_col = col_norm["nombre comuna"]
    vhdv_col = col_norm["porcentaje de hogares victimas de delitos violentos 2024"]
    ci_lower_col = col_norm["limite inferior"]
    ci_upper_col = col_norm["limite superior"]
    tipo_col = col_norm["tipo de estimacion"]
    cv_col = col_norm["coeficiente de variacion logaritmico"]

    # Build slug->CUT map for redundant cross-check (never fail on mismatch)
    cut_map = _build_cut_map()

    records = []
    for _, row in df.iterrows():
        # Primary join: col A is CUT as raw string digits (strip float suffix if any)
        cut = str(row[cut_col]).strip().split(".")[0]
        name = str(row[name_col]).strip()

        # Skip NaN / empty rows (blank rows at end of sheet)
        if cut in ("nan", "", "None"):
            continue

        vhdv_rate = float(row[vhdv_col])
        ci_lower = float(row[ci_lower_col])
        ci_upper = float(row[ci_upper_col])
        tipo = str(row[tipo_col]).strip()
        cv = float(row[cv_col])

        # Redundant cross-check: name→slug should resolve to the same CUT
        slug = make_slug(name)
        resolved = cut_map.get(slug)
        if resolved and resolved[0] != cut:
            log.warning(
                "CUT mismatch for '%s': col-A=%s, slug-resolved=%s (using col-A)",
                name,
                cut,
                resolved[0],
            )

        records.append(
            {
                "cut": cut,
                "name": name,
                "vhdv_rate": vhdv_rate,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
                "tipo_estimacion": tipo,
                "cv": cv,
            }
        )

    # VL-01: record count guard
    if len(records) < MIN_RECORDS:
        raise RuntimeError(
            f"Record count guard failed: expected >={MIN_RECORDS} records, "
            f"got {len(records)}. Parse may be truncated or header row changed."
        )

    # vhdv_rate stays as proportion 0-1 — do NOT rescale to per-100k
    payload = {
        "source": "INE — Estadisticas Experimentales: Seguridad Ciudadana (ENUSC 2024 SAE)",
        "source_url": RESOLVED_URL,
        "landing_page": LANDING_PAGE,
        "vintage": "2024",
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "caveat": (
            "Estadistica experimental (SAE). INE labels this 'etapa inicial de madurez'. "
            "Proportion of households reporting at least one violent crime (VHDV). "
            "136 of 346 comunas covered. NOT per-100k — proportion 0-1. "
            "Do not merge with CEAD per-100k composite."
        ),
        "records": sorted(records, key=lambda r: r["cut"]),
    }

    atomic_write_json(OUTPUT_FILE, payload)
    log.info("Wrote %d records to %s", len(records), OUTPUT_FILE)


if __name__ == "__main__":
    main()
