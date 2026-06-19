"""
pipeline/tests/test_fetch_enusc_vhdv.py

Tests for pipeline/snapshots/fetch_enusc_vhdv.py.

Run:
    python -m pytest pipeline/tests/test_fetch_enusc_vhdv.py -x
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys

import openpyxl
import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Helpers — build minimal XLSX fixtures in tmp_path
# ---------------------------------------------------------------------------

# Exact trimmed column headers from the real ENUSC VHDV XLSX (SEED-002 profile)
_HEADERS = [
    "Código comuna",
    "Nombre comuna",
    "Porcentaje de hogares víctimas de delitos violentos 2024",
    "Límite inferior",
    "Límite superior",
    "Tipo de estimación",
    "Coeficiente de variación logarítmico",
]


def _make_enusc_xlsx(path: pathlib.Path, n_rows: int = 136) -> pathlib.Path:
    """Write a minimal valid ENUSC VHDV XLSX (title row, blank row, header, n_rows data)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Hoja1"

    # Row 1: title (like the real file)
    ws.append(["Cuadro 1: VHDV por comuna 2024"] + [""] * 6)
    # Row 2: blank
    ws.append([""] * 7)
    # Row 3: headers (header=2 in pandas means row index 2, i.e. the 3rd row)
    ws.append(_HEADERS)
    # Rows 4 .. 4+n_rows-1: data
    for i in range(n_rows):
        cut = str(13100 + i + 1)
        ws.append([
            cut,
            f"Comuna {i + 1}",
            round(0.04 + i * 0.001, 4),
            round(0.03 + i * 0.001, 4),
            round(0.05 + i * 0.001, 4),
            "Directa y sintética",
            round(0.04 + i * 0.0001, 4),
        ])

    wb.save(str(path))
    return path


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Task 1 tests — RED (fetch_enusc_vhdv.py does not exist yet)
# ---------------------------------------------------------------------------


def test_cache_only_mode_exits_zero_with_valid_cache(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CACHE_ONLY=1 with a valid cache writes OUTPUT_FILE with >=136 records."""
    import pipeline.snapshots.fetch_enusc_vhdv as m  # type: ignore[import]

    cache_file = tmp_path / "enusc_vhdv.xlsx"
    output_file = tmp_path / "enusc_vhdv.json"

    _make_enusc_xlsx(cache_file, n_rows=136)
    good_sha = _sha256(cache_file)

    monkeypatch.setattr(m, "CACHE_FILE", cache_file)
    monkeypatch.setattr(m, "OUTPUT_FILE", output_file)
    monkeypatch.setattr(m, "KNOWN_SHA256", good_sha)
    monkeypatch.setenv("CACHE_ONLY", "1")

    m.main()

    assert output_file.exists(), "OUTPUT_FILE must be created"
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert "records" in payload
    assert len(payload["records"]) >= 136


def test_sha256_mismatch_raises(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cache file with wrong bytes must raise RuntimeError with 'sha256 mismatch'."""
    import pipeline.snapshots.fetch_enusc_vhdv as m  # type: ignore[import]

    cache_file = tmp_path / "enusc_vhdv.xlsx"
    output_file = tmp_path / "enusc_vhdv.json"

    # Write wrong bytes (not a valid XLSX)
    cache_file.write_bytes(b"this is not the right file content")
    wrong_sha = "0000000000000000000000000000000000000000000000000000000000000000"

    monkeypatch.setattr(m, "CACHE_FILE", cache_file)
    monkeypatch.setattr(m, "OUTPUT_FILE", output_file)
    monkeypatch.setattr(m, "KNOWN_SHA256", wrong_sha)
    monkeypatch.setenv("CACHE_ONLY", "1")

    with pytest.raises(RuntimeError, match="sha256 mismatch"):
        m.main()


def test_missing_cache_raises_file_not_found(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CACHE_ONLY=1 with absent cache file must raise FileNotFoundError."""
    import pipeline.snapshots.fetch_enusc_vhdv as m  # type: ignore[import]

    cache_file = tmp_path / "does_not_exist.xlsx"
    output_file = tmp_path / "enusc_vhdv.json"

    monkeypatch.setattr(m, "CACHE_FILE", cache_file)
    monkeypatch.setattr(m, "OUTPUT_FILE", output_file)
    monkeypatch.setattr(m, "KNOWN_SHA256", "irrelevant")
    monkeypatch.setenv("CACHE_ONLY", "1")

    with pytest.raises(FileNotFoundError):
        m.main()


def test_column_detection(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Parsed record must contain required keys: vhdv_rate, ci_lower, ci_upper, cut, name,
    tipo_estimacion, cv."""
    import pipeline.snapshots.fetch_enusc_vhdv as m  # type: ignore[import]

    cache_file = tmp_path / "enusc_vhdv.xlsx"
    output_file = tmp_path / "enusc_vhdv.json"

    _make_enusc_xlsx(cache_file, n_rows=136)
    good_sha = _sha256(cache_file)

    monkeypatch.setattr(m, "CACHE_FILE", cache_file)
    monkeypatch.setattr(m, "OUTPUT_FILE", output_file)
    monkeypatch.setattr(m, "KNOWN_SHA256", good_sha)
    monkeypatch.setenv("CACHE_ONLY", "1")

    m.main()

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(payload["records"]) > 0
    record = payload["records"][0]
    required_keys = {"vhdv_rate", "ci_lower", "ci_upper", "cut", "name", "tipo_estimacion", "cv"}
    missing = required_keys - set(record.keys())
    assert not missing, f"Record missing keys: {missing}"


def test_record_count_guard(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A truncated sheet with fewer than 136 rows must raise RuntimeError with 'Record count guard'."""
    import pipeline.snapshots.fetch_enusc_vhdv as m  # type: ignore[import]

    cache_file = tmp_path / "enusc_vhdv.xlsx"
    output_file = tmp_path / "enusc_vhdv.json"

    # Write a truncated sheet (10 rows — well below MIN_RECORDS=136)
    _make_enusc_xlsx(cache_file, n_rows=10)
    good_sha = _sha256(cache_file)

    monkeypatch.setattr(m, "CACHE_FILE", cache_file)
    monkeypatch.setattr(m, "OUTPUT_FILE", output_file)
    monkeypatch.setattr(m, "KNOWN_SHA256", good_sha)
    monkeypatch.setenv("CACHE_ONLY", "1")

    with pytest.raises(RuntimeError, match="Record count guard"):
        m.main()
