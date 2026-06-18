"""
pipeline/experiments/test_subgroup_discovery.py

Phase 17 — Wave 0 spikes S1 + S4.

ONE-TIME live discovery script. Does NOT run from the Claude remote sandbox
(all CL government hosts return HTTP 403 from that egress IP). Run it from
GitHub Actions (workflow_dispatch) or a local/Chilean clean egress, the same
context where pipeline/scrape_cead.py succeeds.

Usage:
    cd <repo-root>
    python pipeline/experiments/test_subgroup_discovery.py

What it confirms:
  S1 — the CEAD `grupo[]` subgroup IDs for `lesiones` and `secuestros`
       (homicide=101 is already confirmed). It (a) tries to enumerate the
       CEAD group catalog per familia, then (b) probes candidate IDs and
       reports which return NON-ZERO rows.
  S4 — the `tipoVal` codes that isolate denuncias vs detenciones vs
       aprehendidos, and whether a single offence is double-counted across
       them (the D-AGG normalization constraint).

Findings go into 17-01-SUMMARY.md. Captured HTML responses are written to
pipeline/cache/ as offline fixtures. Courtesy: small, bounded request counts.
"""

import sys
import pathlib
import json

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import requests  # noqa: E402
from pipeline.cead.client import (  # noqa: E402
    make_cead_session,
    fetch_subgroup_batch,
    _CEAD_BASE,
    _DATA_ENDPOINT,
)
from pipeline.cead.parser import parse_cead_table  # noqa: E402

CACHE_DIR = REPO_ROOT / "pipeline" / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# A few RM communes with reliably non-zero data — keeps the probe fast.
TEST_COMMUNES = ["13101", "13123", "13127"]  # Santiago, Providencia, Recoleta
TEST_REGION = "13"
TEST_YEAR = 2024

# CEAD's 7 scraped families. Homicide(101) + lesiones live under familia 1
# (delitos contra la vida e integridad). Secuestro (delito contra la libertad)
# may NOT be inside 1-7 — that is exactly what we need to discover.
FAMILIA_VIDA = 1

# Candidate subgroup IDs to probe. Homicide is 101 (confirmed). The numbering
# convention (1xx within familia 1) suggests lesiones is a sibling 1xx code.
# These are GUESSES to probe, NOT confirmed — the script reports which return
# real data. Extend this list from the catalog enumeration output below.
CANDIDATE_GRUPOS = {
    FAMILIA_VIDA: [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
}

# tipoVal probe (S4). The current scraper uses "1,2" (casos policiales).
# Probe the individual codes to map denuncias / detenciones / aprehendidos.
TIPOVAL_CANDIDATES = ["1", "2", "3", "1,2", "1,2,3"]


def _nonzero_rows(html: str) -> tuple[int, int, list]:
    """Return (n_rows, n_nonzero, sample) from a parsed CEAD table."""
    try:
        rows = parse_cead_table(html)
    except Exception as exc:  # parser shape may differ — surface it
        print(f"      [parse error] {exc}")
        return (0, 0, [])
    nonzero = 0
    for r in rows:
        vals = [v for k, v in (r.items() if isinstance(r, dict) else []) ]
        if any(isinstance(v, (int, float)) and v not in (0, 0.0) for v in vals):
            nonzero += 1
    return (len(rows), nonzero, rows[:2])


def enumerate_group_catalog(session: requests.Session) -> None:
    """Best-effort: ask CEAD for the list of grupos within each familia.

    The commune catalog lives at ajax_2.php (seleccion=101). The group catalog
    is served by a sibling ajax endpoint; the exact param is not documented
    offline, so we try a couple of plausible shapes and dump whatever returns.
    """
    print("\n" + "=" * 64)
    print("S1a — enumerate CEAD group catalog (best-effort)")
    print("=" * 64)
    ajax2 = _CEAD_BASE + "ajax_2.php"
    attempts = [
        {"region": TEST_REGION, "seleccion": "201", "familia": "1"},
        {"region": TEST_REGION, "seleccion": "2", "familia": "1"},
        {"region": TEST_REGION, "familia": "1", "tipo": "grupo"},
    ]
    for i, payload in enumerate(attempts):
        try:
            resp = session.post(ajax2, data=payload, timeout=15)
            ct = resp.headers.get("content-type", "")
            body = resp.content.decode("latin-1", errors="replace")
            print(f"\n  attempt {i} {payload} -> HTTP {resp.status_code} ({ct})")
            print(f"  body[:400]: {body[:400]!r}")
            (CACHE_DIR / f"group_catalog_attempt_{i}.txt").write_text(body, encoding="utf-8")
        except Exception as exc:
            print(f"  attempt {i} failed: {exc}")


def probe_subgroups(session: requests.Session) -> None:
    print("\n" + "=" * 64)
    print("S1b — probe candidate grupo[] IDs for non-zero data")
    print("=" * 64)
    for familia_id, grupos in CANDIDATE_GRUPOS.items():
        for grupo in grupos:
            try:
                html = fetch_subgroup_batch(
                    session, TEST_COMMUNES, TEST_YEAR, familia_id, grupo, medida="2"
                )
            except Exception as exc:
                print(f"  familia={familia_id} grupo={grupo}: request failed: {exc}")
                continue
            n, nz, sample = _nonzero_rows(html)
            flag = "  <-- HAS DATA" if nz else ""
            print(f"  familia={familia_id} grupo={grupo}: rows={n} nonzero={nz}{flag}")
            if nz:
                print(f"      sample: {json.dumps(sample, ensure_ascii=False)[:300]}")
                (CACHE_DIR / f"grupo_{familia_id}_{grupo}_rate.html").write_text(
                    html, encoding="utf-8"
                )
    print(
        "\n  NOTE: secuestros may live OUTSIDE familia 1-7. If no 1xx candidate "
        "is kidnapping, enumerate other familias via the catalog output above "
        "and extend CANDIDATE_GRUPOS."
    )


def probe_tipoval(session: requests.Session) -> None:
    """S4 — map tipoVal codes to denuncias/detenciones/aprehendidos.

    Uses homicide (grupo 101, confirmed) as a fixed probe and varies tipoVal,
    reading absolute counts (medida=1) so magnitudes are comparable. If
    count(tipoVal='1,2') == count('1') + count('2') the codes are additive
    (and naive summing double-counts at the offence level — the D-AGG risk).
    """
    print("\n" + "=" * 64)
    print("S4 — map tipoVal codes (denuncias / detenciones / aprehendidos)")
    print("=" * 64)
    print("  Using homicide grupo=101, medida=1 (counts) as the fixed probe.\n")
    # fetch_subgroup_batch hardcodes tipoVal='1,2'; hit the endpoint directly
    # here so we can vary it. Mirrors the payload shape in client.py.
    for tv in TIPOVAL_CANDIDATES:
        payload = {
            "medida": "1",
            "tipoVal": tv,
            "anio[]": str(TEST_YEAR),
            "familia[]": str(FAMILIA_VIDA),
            "grupo[]": "101",
            "seleccion": "1",
            "descarga": "true",
            "comuna[]": [str(c) for c in TEST_COMMUNES],
            "region[]": str(TEST_COMMUNES[0])[:2],
        }
        try:
            resp = session.post(_DATA_ENDPOINT, data=payload, timeout=30)
            html = resp.content.decode("latin-1")
        except Exception as exc:
            print(f"  tipoVal={tv!r}: request failed: {exc}")
            continue
        n, nz, sample = _nonzero_rows(html)
        print(f"  tipoVal={tv!r}: rows={n} nonzero={nz} sample={json.dumps(sample, ensure_ascii=False)[:200]}")
    print(
        "\n  INTERPRET: compare counts for '1' vs '2' vs '1,2'. If '1,2' == '1'+'2', "
        "the measures are additive and the index must normalize per offence."
    )


def main() -> None:
    print("=" * 64)
    print("Phase 17 Wave 0 — CEAD subgroup + tipoVal discovery (S1 + S4)")
    print("=" * 64)
    session = make_cead_session()
    print("[+] Session warmed up (wpdm_client cookie set)")
    enumerate_group_catalog(session)
    probe_subgroups(session)
    probe_tipoval(session)
    print("\n[done] Record confirmed IDs/codes in 17-01-SUMMARY.md.")


if __name__ == "__main__":
    main()
