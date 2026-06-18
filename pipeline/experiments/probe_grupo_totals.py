"""
pipeline/experiments/probe_grupo_totals.py

Phase 17 Wave 0 — refinement of test_subgroup_discovery.py.

The original spike's _nonzero_rows() heuristic was structurally blind: it
expected flat int/float cells, but parse_cead_table returns nested
{'name', 'class', 'values': {year: 'NNN,0000000000'}} string rows. So every
grupo printed nonzero=0 and the per-grupo magnitudes were never shown.

This probe extracts the TOTAL PAIS (formato_1) magnitude for each candidate
grupo so we can actually identify lesiones (high count) and secuestros (low),
and confirms the S4 additivity arithmetic with parsed numbers.
"""

import sys
import pathlib
import json

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pipeline.cead.client import (  # noqa: E402
    make_cead_session,
    fetch_subgroup_batch,
    _DATA_ENDPOINT,
)
from pipeline.cead.parser import parse_cead_table  # noqa: E402

TEST_COMMUNES = ["13101", "13123", "13127"]
TEST_YEAR = 2024
FAMILIA_VIDA = 1


def _to_float(s: str) -> float:
    # "1.019,0000000000" -> 1019.0  (CL format: '.' thousands, ',' decimal)
    return float(s.replace(".", "").replace(",", "."))


def _total_pais(html: str) -> str | None:
    rows = parse_cead_table(html)
    for r in rows:
        cls = r.get("class", []) or []
        if "formato_1" in cls or "PA" in r.get("name", "").upper():
            return r["values"].get(str(TEST_YEAR))
    return rows[0]["values"].get(str(TEST_YEAR)) if rows else None


def probe_grupos() -> None:
    print("=" * 64)
    print("S1 (refined) — TOTAL PAIS count per candidate grupo (familia 1)")
    print("medida=1 (absolute counts), tipoVal=1,2 (scraper default)")
    print("=" * 64)
    session = make_cead_session()
    # Extend the candidate window; 101=homicide confirmed.
    for grupo in range(101, 121):
        try:
            html = fetch_subgroup_batch(
                session, TEST_COMMUNES, TEST_YEAR, FAMILIA_VIDA, grupo, medida="1"
            )
        except Exception as exc:
            print(f"  grupo={grupo}: request failed: {exc}")
            continue
        total = _total_pais(html)
        try:
            num = _to_float(total) if total else 0.0
        except ValueError:
            num = -1.0
        flag = "  <-- HAS DATA" if num > 0 else ""
        print(f"  grupo={grupo}: TOTAL_PAIS_2024 = {total!r}  (~{num:,.0f}){flag}")


def confirm_s4() -> None:
    print("\n" + "=" * 64)
    print("S4 (refined) — tipoVal additivity, parsed numbers (grupo 101)")
    print("=" * 64)
    session = make_cead_session()
    vals = {}
    for tv in ["1", "2", "3", "1,2", "1,2,3"]:
        payload = {
            "medida": "1",
            "tipoVal": tv,
            "anio[]": str(TEST_YEAR),
            "familia[]": str(FAMILIA_VIDA),
            "grupo[]": "101",
            "seleccion": "1",
            "descarga": "true",
            "comuna[]": [str(c) for c in TEST_COMMUNES],
            "region[]": "13",
        }
        resp = session.post(_DATA_ENDPOINT, data=payload, timeout=30)
        total = _total_pais(resp.content.decode("latin-1"))
        vals[tv] = _to_float(total) if total else 0.0
        print(f"  tipoVal={tv!r}: TOTAL_PAIS_2024 = {vals[tv]:,.0f}")
    print("\n  additivity checks:")
    print(f"    '1'+'2'      = {vals['1']+vals['2']:,.0f}   vs '1,2'   = {vals['1,2']:,.0f}   "
          f"-> {'ADDITIVE' if abs(vals['1']+vals['2']-vals['1,2'])<0.5 else 'NOT additive'}")
    print(f"    '1'+'2'+'3'  = {vals['1']+vals['2']+vals['3']:,.0f}   vs '1,2,3' = {vals['1,2,3']:,.0f}   "
          f"-> {'ADDITIVE' if abs(vals['1']+vals['2']+vals['3']-vals['1,2,3'])<0.5 else 'NOT additive'}")


if __name__ == "__main__":
    probe_grupos()
    confirm_s4()
