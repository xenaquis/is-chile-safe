"""
pipeline/tests/test_news_evidence.py

Tests for pipeline/news_evidence.py — G-05 evidence extractor.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pipeline.news_evidence import evidence_iso

MODULE_PATH = Path(__file__).parent.parent / "news_evidence.py"


def test_evidence_iso_prefers_last_new_incident_at():
    payload = {
        "last_new_incident_at": "2026-06-01T10:00:00Z",
        "incidents": [{"date": "2026-05-01"}],
    }
    assert evidence_iso(payload) == "2026-06-01T10:00:00Z"


def test_evidence_iso_falls_back_to_max_date_plus_one_day():
    payload = {"incidents": [{"date": "2026-05-29"}, {"date": "2026-05-20"}]}
    assert evidence_iso(payload) == "2026-05-30T00:00:00Z"


def test_evidence_iso_absent_field_unparseable_falls_back():
    payload = {"last_new_incident_at": "not-a-date", "incidents": [{"date": "2026-05-29"}]}
    assert evidence_iso(payload) == "2026-05-30T00:00:00Z"


def test_evidence_iso_none_when_no_field_and_no_incidents():
    assert evidence_iso({"incidents": []}) is None
    assert evidence_iso({}) is None


def test_evidence_iso_ignores_malformed_incident_dates():
    payload = {"incidents": [{"date": "not-a-date"}, {"date": "2026-05-29"}]}
    assert evidence_iso(payload) == "2026-05-30T00:00:00Z"


def test_cli_prints_evidence_and_exits_0(tmp_path):
    current = tmp_path / "current.json"
    current.write_text(
        json.dumps({"last_new_incident_at": "2026-06-01T10:00:00Z", "incidents": []}),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH), str(current)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "2026-06-01T10:00:00Z"


def test_cli_missing_file_prints_empty_line_and_exits_0(tmp_path):
    missing = tmp_path / "does-not-exist.json"
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH), str(missing)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_cli_unparseable_json_prints_empty_line_and_exits_0(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH), str(bad)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_cli_no_evidence_prints_empty_line_and_exits_0(tmp_path):
    current = tmp_path / "current.json"
    current.write_text(json.dumps({"incidents": []}), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH), str(current)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_module_only_imports_stdlib():
    """The heartbeat runs this with system python3 and no deps installed."""
    text = MODULE_PATH.read_text(encoding="utf-8")
    import_lines = [
        line.strip() for line in text.splitlines()
        if line.strip().startswith("import ") or line.strip().startswith("from ")
    ]
    stdlib_prefixes = ("datetime", "json", "sys", "__future__")
    for line in import_lines:
        assert any(
            line == f"import {p}" or line.startswith(f"from {p}")
            for p in stdlib_prefixes
        ), f"non-stdlib import found: {line}"
