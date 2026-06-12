"""
pipeline/tests/test_atomic_write.py

Tests for pipeline/shared/atomic_write.py — atomic JSON write utility.
"""
import json
from pathlib import Path

import pytest

from pipeline.shared.atomic_write import atomic_write_json


def test_round_trip_basic(tmp_path):
    """Written dict round-trips via json.loads to the same value."""
    dest = tmp_path / "output.json"
    data = {"key": "value", "number": 42}
    atomic_write_json(dest, data)
    result = json.loads(dest.read_text(encoding="utf-8"))
    assert result == data


def test_creates_parent_directories(tmp_path):
    """Parent directories are created if missing."""
    dest = tmp_path / "nested" / "deep" / "output.json"
    assert not dest.parent.exists()
    atomic_write_json(dest, {"ok": True})
    assert dest.exists()


def test_no_tmp_file_remains_after_success(tmp_path):
    """No .tmp file remains in the directory after a successful write."""
    dest = tmp_path / "output.json"
    atomic_write_json(dest, {"x": 1})
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert tmp_files == [], f"Unexpected .tmp files: {tmp_files}"


def test_utf8_accented_name_round_trips(tmp_path):
    """UTF-8 content with accented Chilean commune name survives the round-trip."""
    dest = tmp_path / "accented.json"
    data = {"name": "Ñuñoa"}
    atomic_write_json(dest, data)
    result = json.loads(dest.read_text(encoding="utf-8"))
    assert result["name"] == "Ñuñoa"


def test_list_data_round_trips(tmp_path):
    """list input (not just dict) is written and read back correctly."""
    dest = tmp_path / "list.json"
    data = [{"id": "13101"}, {"id": "01101"}]
    atomic_write_json(dest, data)
    result = json.loads(dest.read_text(encoding="utf-8"))
    assert result == data


def test_overwrites_existing_file(tmp_path):
    """Calling atomic_write_json twice on the same path overwrites the file."""
    dest = tmp_path / "output.json"
    atomic_write_json(dest, {"version": 1})
    atomic_write_json(dest, {"version": 2})
    result = json.loads(dest.read_text(encoding="utf-8"))
    assert result == {"version": 2}
