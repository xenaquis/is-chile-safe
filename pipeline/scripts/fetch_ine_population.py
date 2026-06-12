"""
One-time script: download the processed INE communal population projections CSV
from bastianolea/censo_proyecciones_poblacion, filter to year 2024, and write
data/ine/poblacion_comunal.json as a committed static asset.

Source (Assumption A6 — verify 5 communes against official INE before trusting):
  https://github.com/bastianolea/censo_proyecciones_poblacion
  Official INE: https://www.ine.gob.cl/estadisticas/sociales/demografia-y-vitales/proyecciones-de-poblacion

Run once to regenerate:
  python -m pipeline.scripts.fetch_ine_population
"""

import csv
import io
import pathlib
import sys

import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
OUTPUT_PATH = REPO_ROOT / "data" / "ine" / "poblacion_comunal.json"

# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------
CSV_URL = (
    "https://github.com/bastianolea/censo_proyecciones_poblacion/raw/main/"
    "datos/datos_procesados/censo_proyecciones_año.csv"
)

# Expected column names in the CSV
EXPECTED_YEAR_COLS = {"ano", "año", "year"}               # year column (variants)
EXPECTED_CUT_COLS = {"cut_comuna", "cut", "codigo_cut", "codigo"}  # CUT code column (variants)
EXPECTED_NAME_COLS = {"nombre_comuna", "comuna", "name"}           # commune name (variants)
EXPECTED_POP_COLS = {"poblacion", "población", "population", "pop"}  # population column (variants)

TARGET_YEAR = 2024
EXPECTED_COUNT = 346


def _find_col(headers: list[str], candidates: set[str]) -> str | None:
    """Return the first header (case-insensitive) that matches any candidate."""
    lower = {h.lower().strip(): h for h in headers}
    for c in candidates:
        if c in lower:
            return lower[c]
    return None


def fetch_and_convert() -> list[dict]:
    """Download CSV and return list of {cut, name, population_2024}."""
    print(f"Downloading: {CSV_URL}")
    resp = requests.get(CSV_URL, timeout=60)
    resp.raise_for_status()

    # The CSV uses Latin-1 (Windows-1252 compatible) encoding
    # Try UTF-8 first; fall back to Latin-1
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = resp.content.decode(enc)
            # Quick sanity: if the decoded text contains replacement chars, try next
            if "�" not in text:
                break
        except UnicodeDecodeError:
            continue
    else:
        text = resp.content.decode("latin-1", errors="replace")

    # Auto-detect delimiter: if first line contains semicolons, use ';'
    first_line = text.split("\n")[0]
    delimiter = ";" if ";" in first_line else ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = reader.fieldnames or []
    # Strip BOM and whitespace/quotes from header names
    headers = [h.strip().strip('"').strip("'") for h in headers]
    # Recreate reader with cleaned field names
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter,
                            fieldnames=headers)
    next(reader)  # skip original header row

    # Resolve column names
    year_col = _find_col(headers, EXPECTED_YEAR_COLS)
    cut_col = _find_col(headers, EXPECTED_CUT_COLS)
    name_col = _find_col(headers, EXPECTED_NAME_COLS)
    pop_col = _find_col(headers, EXPECTED_POP_COLS)

    missing = []
    if year_col is None:
        missing.append(f"year (tried: {EXPECTED_YEAR_COLS})")
    if cut_col is None:
        missing.append(f"cut (tried: {EXPECTED_CUT_COLS})")
    if pop_col is None:
        missing.append(f"population (tried: {EXPECTED_POP_COLS})")

    if missing:
        raise RuntimeError(
            f"CSV column resolution failed.\n"
            f"  Actual columns: {headers}\n"
            f"  Could not find: {missing}"
        )

    print(f"  year_col={year_col!r}, cut_col={cut_col!r}, "
          f"name_col={name_col!r}, pop_col={pop_col!r}")

    entries: list[dict] = []
    for row in reader:
        try:
            year = int(row[year_col])
        except (ValueError, KeyError):
            continue
        if year != TARGET_YEAR:
            continue

        cut_raw = str(row[cut_col]).strip()
        # Keep as string; strip any float suffix (.0) that may appear
        if cut_raw.endswith(".0"):
            cut_raw = cut_raw[:-2]
        cut_raw = cut_raw.lstrip("0") or "0"  # remove leading zeros if any

        name_raw = str(row[name_col]).strip() if name_col else ""

        try:
            pop = int(float(row[pop_col]))
        except (ValueError, KeyError) as exc:
            raise RuntimeError(
                f"Could not parse population from row {row}: {exc}"
            ) from exc

        entries.append({
            "cut": cut_raw,
            "name": name_raw,
            "population_2024": pop,
        })

    return entries


def main() -> None:
    entries = fetch_and_convert()

    count = len(entries)
    print(f"Filtered to year {TARGET_YEAR}: {count} communes")

    if count != EXPECTED_COUNT:
        raise SystemExit(
            f"ERROR: Expected exactly {EXPECTED_COUNT} communes for year "
            f"{TARGET_YEAR}, got {count}. "
            f"Do not commit partial data — investigate CSV source."
        )

    # Write via atomic write (same pattern as atomic_write.py)
    import json
    import os
    import tempfile

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=OUTPUT_PATH.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            json.dump(entries, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp_path, OUTPUT_PATH)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    print(f"Written: {OUTPUT_PATH} ({count} entries)")

    # Quick sanity: Santiago (13101) must have > 100000
    pop_map = {e["cut"]: e["population_2024"] for e in entries}
    santiago = pop_map.get("13101")
    if santiago is None:
        raise SystemExit("ERROR: Santiago (cut=13101) not found in output — check CUT parsing.")
    if santiago < 100_000:
        raise SystemExit(
            f"ERROR: Santiago population {santiago} is suspiciously low (expected > 100000)."
        )
    print(f"Sanity check: Santiago (13101) population_2024 = {santiago:,}  [OK]")


if __name__ == "__main__":
    main()
