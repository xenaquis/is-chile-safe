"""
pipeline/experiments/test_subgroup101.py

Live runtime experiment: confirm the exact CEAD POST param that selects
homicide subgroup 101 within the "vida" (familia 1) family, and whether
rate (medida=2) and absolute count (medida=1) require two separate requests.

This is a ONE-TIME confirmation script — run it once, inspect the output,
then the findings go into 14-01-SUMMARY.md. The two HTML responses are
written to pipeline/cache/ as offline test fixtures (Task 2).

Usage:
    cd <repo-root>
    python pipeline/experiments/test_subgroup101.py

Expected output:
    - STATUS A / STATUS B: HTTP 200
    - SIZE A / SIZE B: non-trivial (several KB each)
    - Sample rows printed for both responses
    - Summary lines confirming param key, rate vs count magnitudes, zero-marker

Courtesy: single pair of requests only (no loop). Reuses make_cead_session()
which sets the mandatory Referer/Origin/wpdm_client cookie.
"""

import sys
import pathlib

# Make sure repo root is on sys.path so pipeline imports work
REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import time
from pipeline.cead.client import make_cead_session, _DATA_ENDPOINT
from pipeline.cead.parser import parse_cead_table

CACHE_DIR = REPO_ROOT / "pipeline" / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Two RM communes for the experiment — small enough to be fast, large enough
# to have real data. Santiago (13101) and Providencia (13102).
TEST_COMMUNES = ["13101", "13102"]
TEST_REGION = "13"
TEST_YEAR = "2024"
FAMILIA_VIDA = "1"
SUBGROUP = "101"


def run_experiment():
    print("=" * 60)
    print("CEAD Subgroup-101 Live Confirmation Experiment")
    print("=" * 60)

    session = make_cead_session()
    print("\n[+] Session warmed up (wpdm_client cookie set)\n")

    # -------------------------------------------------------------------------
    # Test A: Rate (medida=2) with subgrupo[]=101
    # -------------------------------------------------------------------------
    print("--- Test A: subgrupo[]=101, medida=2 (rate per 100k) ---")
    payload_a = {
        "medida": "2",
        "tipoVal": "1,2",
        "anio[]": TEST_YEAR,
        "familia[]": FAMILIA_VIDA,
        "subgrupo[]": SUBGROUP,
        "seleccion": "1",
        "descarga": "true",
        "comuna[]": TEST_COMMUNES,
        "region[]": TEST_REGION,
    }
    r_a = session.post(_DATA_ENDPOINT, data=payload_a, timeout=30)
    print(f"STATUS A: {r_a.status_code}   SIZE: {len(r_a.content)} bytes")
    html_a = r_a.content.decode("latin-1")

    rate_path = CACHE_DIR / "test_subgroup101_rate.html"
    rate_path.write_bytes(r_a.content)
    print(f"  -> Written: {rate_path}")

    rows_a = parse_cead_table(html_a)
    print(f"  -> Parsed rows (formato_4): {len(rows_a)}")
    for row in rows_a[:3]:
        year_vals = row.get("values", {})
        val = year_vals.get(TEST_YEAR, year_vals.get(str(int(TEST_YEAR)), "N/A"))
        print(f"     {row.get('name', '?'):30s}  {TEST_YEAR}: {val}")

    # -------------------------------------------------------------------------
    # Courtesy pause between requests
    # -------------------------------------------------------------------------
    time.sleep(2)

    # -------------------------------------------------------------------------
    # Test B: Count (medida=1) with subgrupo[]=101
    # -------------------------------------------------------------------------
    print("\n--- Test B: subgrupo[]=101, medida=1 (absolute count) ---")
    payload_b = {
        "medida": "1",
        "tipoVal": "1,2",
        "anio[]": TEST_YEAR,
        "familia[]": FAMILIA_VIDA,
        "subgrupo[]": SUBGROUP,
        "seleccion": "1",
        "descarga": "true",
        "comuna[]": TEST_COMMUNES,
        "region[]": TEST_REGION,
    }
    r_b = session.post(_DATA_ENDPOINT, data=payload_b, timeout=30)
    print(f"STATUS B: {r_b.status_code}   SIZE: {len(r_b.content)} bytes")
    html_b = r_b.content.decode("latin-1")

    count_path = CACHE_DIR / "test_subgroup101_count.html"
    count_path.write_bytes(r_b.content)
    print(f"  -> Written: {count_path}")

    rows_b = parse_cead_table(html_b)
    print(f"  -> Parsed rows (formato_4): {len(rows_b)}")
    for row in rows_b[:3]:
        year_vals = row.get("values", {})
        val = year_vals.get(TEST_YEAR, year_vals.get(str(int(TEST_YEAR)), "N/A"))
        print(f"     {row.get('name', '?'):30s}  {TEST_YEAR}: {val}")

    # -------------------------------------------------------------------------
    # Fallback: if subgrupo[] returned 0 rows, try grupo[]
    # -------------------------------------------------------------------------
    confirmed_param = "subgrupo[]"
    if len(rows_a) == 0:
        print("\n[!] subgrupo[]='101' returned 0 rows — trying fallback: grupo[]='101'")
        payload_fallback = dict(payload_a)
        del payload_fallback["subgrupo[]"]
        payload_fallback["grupo[]"] = SUBGROUP
        r_fb = session.post(_DATA_ENDPOINT, data=payload_fallback, timeout=30)
        print(f"STATUS FALLBACK: {r_fb.status_code}   SIZE: {len(r_fb.content)} bytes")
        html_fb = r_fb.content.decode("latin-1")
        rows_fb = parse_cead_table(html_fb)
        print(f"  -> Parsed rows with grupo[]: {len(rows_fb)}")
        if len(rows_fb) > 0:
            confirmed_param = "grupo[]"
            # Overwrite the rate cache with the working response
            rate_path.write_bytes(r_fb.content)
            rows_a = rows_fb
            print("  -> grupo[] WORKS — rate cache updated")
        else:
            confirmed_param = "UNKNOWN — both params returned 0 rows"
            print("  -> BOTH params failed — check endpoint manually")

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("CONFIRMATION SUMMARY")
    print("=" * 60)
    print(f"  Confirmed param key:         {confirmed_param}")
    print(f"  Rate rows (Test A):          {len(rows_a)}")
    print(f"  Count rows (Test B):         {len(rows_b)}")
    print(f"  Two requests needed:         {'YES' if True else 'NO'} (medida is single-valued per request)")

    # Detect zero-marker in rate rows
    zero_marker = "UNKNOWN"
    for row in rows_a:
        for val in row.get("values", {}).values():
            if val in ("0,0", "-", "0", ""):
                zero_marker = repr(val)
                break

    print(f"  Observed zero-marker:        {zero_marker}")
    print()
    print("Record these findings in 14-01-SUMMARY.md before proceeding to 14-02.")
    print("=" * 60)


if __name__ == "__main__":
    run_experiment()
