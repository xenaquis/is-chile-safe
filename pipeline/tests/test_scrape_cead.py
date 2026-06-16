"""
pipeline/tests/test_scrape_cead.py

Nyquist RED scaffold for the homicide accumulator (Phase 14, Plan 01).
These tests ASSERT the desired end-state of 14-02 implementation and are
EXPECTED TO FAIL until the homicide fetch loop is written.

Failure messages are designed to say "homicide_rate key missing" / "homicide_count
key missing", NOT import or collection errors.

Run:
    python -m pytest pipeline/tests/test_scrape_cead.py -q   # RED (expected)
    python -m pytest pipeline/tests/ -q                       # suite collects OK
"""
import json
import pathlib
import sys

import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers (mirror test_output.py _make_minimal_records, extended for homicide)
# ---------------------------------------------------------------------------

def _make_records_with_homicide(n: int = 5) -> list[dict]:
    """Minimal ComunaRecord-compatible dicts that include homicide fields.

    In the desired post-14-02 state, records should carry homicide_rate and
    homicide_count. These helpers pre-populate them to make the SIZE test
    realistic; the KEY tests below assert they exist on the payload entry,
    not on the input record.
    """
    from pipeline.shared.population import LOW_POPULATION_THRESHOLD

    records = []
    for i in range(n):
        cut = str(10000 + i)
        base = float((i % 50) + 1)
        records.append({
            "id": cut,
            "name": f"Commune {i}",
            "slug": f"commune-{i}",
            "region_id": str((i % 16) + 1),
            "population": LOW_POPULATION_THRESHOLD + 1000,
            "low_population": False,
            "national_rank": i + 1,
            "regional_rank": i + 1,
            "trend": "stable",
            # homicide fields: present in future post-14-02 records
            "homicide_rate": round(base * 0.05, 2),   # plausible /100k (0.05-2.5)
            "homicide_count": i + 1,                   # small integer
            "featured_rates": {"propiedad": {}, "homicidios": {}, "secuestros": {}},
            "series": [
                {
                    "year": 2024,
                    "rate_per_100k": base * 3,
                    "by_family": {
                        "vida": round(base * 0.1, 1),
                        "robos_violentos": round(base * 0.3, 1),
                        "vif": round(base * 0.2, 1),
                        "drogas": round(base * 0.15, 1),
                        "armas": round(base * 0.05, 1),
                        "propiedad": round(base * 1.5, 1),
                        "incivilidades": round(base * 0.6, 1),
                    },
                    "partial": False,
                }
            ],
            "last_updated": "2026-06-16",
        })
    return records


def _make_minimal_records_346() -> list[dict]:
    """346 records mirroring test_output.py shape but with homicide fields added."""
    from pipeline.shared.population import LOW_POPULATION_THRESHOLD

    records = []
    for i in range(346):
        cut = str(10000 + i)
        base = float((i % 50) + 1)
        records.append({
            "id": cut,
            "name": f"Commune {i}",
            "slug": f"commune-{i}",
            "region_id": str((i % 16) + 1),
            "population": LOW_POPULATION_THRESHOLD + 1000,
            "low_population": False,
            "national_rank": i + 1,
            "regional_rank": i + 1,
            "trend": "stable",
            "homicide_rate": round(base * 0.05, 2),
            "homicide_count": i + 1,
            "featured_rates": {"propiedad": {}, "homicidios": {}, "secuestros": {}},
            "series": [
                {
                    "year": 2024,
                    "rate_per_100k": base * 3,
                    "by_family": {
                        "vida": round(base * 0.1, 1),
                        "robos_violentos": round(base * 0.3, 1),
                        "vif": round(base * 0.2, 1),
                        "drogas": round(base * 0.15, 1),
                        "armas": round(base * 0.05, 1),
                        "propiedad": round(base * 1.5, 1),
                        "incivilidades": round(base * 0.6, 1),
                    },
                    "partial": False,
                }
            ],
            "last_updated": "2026-06-16",
        })
    return records


# ---------------------------------------------------------------------------
# Test 1: map-payload entries expose homicide_rate key  [RED until 14-02]
# ---------------------------------------------------------------------------

def test_map_payload_entry_has_homicide_rate():
    """Each map-payload entry MUST expose an "hr" key (abbreviated homicide_rate, int).

    The key is abbreviated to "hr" (vs "homicide_rate") to stay under the 30KB budget
    (D-09 compact encoding, same pattern as by_family compact list). The full name
    "homicide_rate" lives in per-commune JSON (featured_rates.homicidios).

    EXPECTED TO FAIL (RED) until 14-02 wires the homicide accumulator into
    build_map_payload. Failure reads: KeyError / AssertionError '"hr" key missing'.
    """
    from pipeline.scrape_cead import build_map_payload

    records = _make_records_with_homicide(5)
    all_rates = [r["series"][0]["rate_per_100k"] for r in records]
    payload = build_map_payload(records, year=2024, all_rates=all_rates)

    assert "comunas" in payload
    for entry in payload["comunas"]:
        assert "hr" in entry, (
            f'"hr" (homicide_rate) key missing from map-payload entry {entry.get("id")!r}. '
            "This test is RED until 14-02 implements the homicide accumulator loop."
        )
        val = entry["hr"]
        assert val is None or isinstance(val, (int, float)), (
            f'"hr" must be int, float, or None; got {type(val).__name__}'
        )


# ---------------------------------------------------------------------------
# Test 2: map-payload entries expose homicide_count key  [RED until 14-02]
# ---------------------------------------------------------------------------

def test_map_payload_entry_has_homicide_count():
    """homicide_count lives in featured_rates.homicidios_count (per-commune JSON),
    NOT in the compact map-payload (dropped for 30KB budget, Pitfall 3 escape).

    This test verifies the budget decision: homicide_count must NOT appear in map-payload
    entries (it would exceed 30KB with 346 communes). Consumers needing the count must
    read the per-commune commune JSON file (data/cead/comunas/{cut}.json).
    Also verifies that the abbreviated "hr" key IS present (homicide_rate).
    """
    from pipeline.scrape_cead import build_map_payload

    records = _make_records_with_homicide(5)
    all_rates = [r["series"][0]["rate_per_100k"] for r in records]
    payload = build_map_payload(records, year=2024, all_rates=all_rates)

    assert "comunas" in payload
    for entry in payload["comunas"]:
        # homicide_count intentionally absent from map-payload (budget: Pitfall 3)
        assert "homicide_count" not in entry, (
            f"homicide_count should NOT be in map-payload entry {entry.get('id')!r} "
            "(dropped for 30KB budget; it lives in per-commune JSON featured_rates.homicidios_count)."
        )
        # homicide_rate IS required in the map-payload (as abbreviated key "hr")
        assert "hr" in entry, (
            f'"hr" (homicide_rate) key missing from map-payload entry {entry.get("id")!r}.'
        )


# ---------------------------------------------------------------------------
# Test 3: 346-entry payload WITH homicide fields stays under 30720 bytes
# ---------------------------------------------------------------------------

def test_map_payload_346_entries_with_homicide_under_30kb():
    """A 346-entry payload carrying both homicide ints must still be < 30720 bytes.

    This test will PASS once homicide keys are added only if the keys are compact
    (int/None). It is RED until 14-02 adds the keys — at that point it serves as
    a size regression guard ensuring the additions don't blow the budget.

    If this test fails with a size error rather than a key-missing error after
    14-02 lands, the payload encoding needs to be made more compact.
    """
    from pipeline.scrape_cead import build_map_payload

    records = _make_minimal_records_346()
    all_rates = [r["series"][0]["rate_per_100k"] for r in records]
    payload = build_map_payload(records, year=2024, all_rates=all_rates)

    # Verify at least one entry has the abbreviated "hr" key (homicide_rate).
    # NOTE: key abbreviated to "hr" (vs "homicide_rate") for D-09 compactness.
    # homicide_count dropped from payload per Pitfall 3 budget escape; lives in per-commune JSON.
    if payload["comunas"]:
        entry = payload["comunas"][0]
        assert "hr" in entry, (
            '"hr" (homicide_rate) key missing — test is RED until 14-02 implements accumulator'
        )

    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert len(serialized) < 30720, (
        f"map-payload with homicide fields is too large: {len(serialized)} bytes (limit 30720)"
    )


# ---------------------------------------------------------------------------
# Test 4: parse_cead_table yields plausible homicide rates from fixture
# ---------------------------------------------------------------------------

def test_cead_subgroup101_rate_fixture_yields_plausible_rates():
    """parse_cead_table on the captured subgroup-101 rate fixture must yield
    rows whose 2024 value parses to a plausible homicide rate (0 < rate < 100/100k).

    This test exercises the PARSER against real captured HTML — it passes now
    because it only tests the parser, not the accumulator. The parser is stable.
    """
    from pipeline.cead.parser import parse_cead_table, parse_cead_float

    fixture = FIXTURES_DIR / "cead_subgroup101_rate_sample.html"
    if not fixture.exists():
        pytest.skip("cead_subgroup101_rate_sample.html not present")

    html = fixture.read_bytes().decode("latin-1")
    rows = parse_cead_table(html)

    assert len(rows) >= 1, "Fixture must yield at least 1 row"

    # At least one row must have a plausible homicide rate for 2024
    plausible = []
    for row in rows:
        val_str = row.get("values", {}).get("2024")
        if val_str is None:
            continue
        val = parse_cead_float(val_str)
        if val is not None and 0 < val < 100:
            plausible.append((row.get("name"), val))

    assert len(plausible) >= 1, (
        f"Expected at least 1 row with plausible homicide rate (0 < rate < 100/100k), "
        f"got rows: {[(r.get('name'), r.get('values')) for r in rows]}"
    )
