"""
pipeline/tests/test_store.py

Tests for pipeline/news/store.py — 30-day window, idempotent merge, archive write.
Wave-1 scaffold: skips if pipeline.news.store is not yet implemented.
Uses tmp_path pytest built-in fixture for isolation.
"""
from __future__ import annotations

import copy
import datetime
import json

import pytest

# Skip entire module if Wave-1 module not yet implemented
try:
    from pipeline.news.store import merge_and_write  # type: ignore
    _MODULE_AVAILABLE = True
except ImportError:
    _MODULE_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _MODULE_AVAILABLE,
    reason="pipeline.news.store not yet implemented (Wave 1)",
)


def _make_incident(uid: str, date_str: str, family: str = "propiedad") -> dict:
    return {
        "id": uid,
        "cut": "13101",
        "lat": -33.456,
        "lng": -70.654,
        "title_es": f"Incidente {uid}",
        "title_en": f"Incident {uid}",
        "date": date_str,
        "outlet": "BioBio Chile",
        "url": f"https://biobiochile.cl/article/{uid}",
        "family": family,
    }


def _today() -> str:
    return datetime.date.today().isoformat()


def _old_date() -> str:
    return (datetime.date.today() - datetime.timedelta(days=31)).isoformat()


def _fresh_date() -> str:
    return (datetime.date.today() - datetime.timedelta(days=5)).isoformat()


def _write_current(path, incidents: list) -> None:
    data = {
        "generated": "2026-06-01T00:00:00Z",
        "window_days": 30,
        "incidents": incidents,
    }
    path.write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------------------
# Test functions (exact names per 05-VALIDATION.md)
# ---------------------------------------------------------------------------


def test_30day_window(tmp_path):
    """An incident older than 30 days must be moved to archive; fresh one kept."""
    current_path = tmp_path / "current.json"
    archive_dir = tmp_path / "archive"

    old_incident = _make_incident("old001", _old_date())
    fresh_incident = _make_incident("fresh001", _fresh_date())
    _write_current(current_path, [old_incident, fresh_incident])

    merge_and_write([], current_path, archive_dir=archive_dir)

    result = json.loads(current_path.read_text(encoding="utf-8"))
    assert len(result["incidents"]) == 1
    assert result["incidents"][0]["id"] == "fresh001"

    # Archive should contain the old incident
    archive_files = list(archive_dir.glob("*.json"))
    assert len(archive_files) >= 1


def test_idempotent_merge(tmp_path):
    """Merging the same incident twice must not create duplicates."""
    current_path = tmp_path / "current.json"
    archive_dir = tmp_path / "archive"

    incident = _make_incident("dup001", _fresh_date())
    _write_current(current_path, [incident])

    # Merge the same incident again
    duplicate = copy.deepcopy(incident)
    merge_and_write([duplicate], current_path, archive_dir=archive_dir)

    result = json.loads(current_path.read_text(encoding="utf-8"))
    ids = [i["id"] for i in result["incidents"]]
    assert ids.count("dup001") == 1, "Duplicate incident must not be added twice"


def test_archive_write(tmp_path):
    """Aged-out incidents must be written to archive/YYYY-MM.json."""
    current_path = tmp_path / "current.json"
    archive_dir = tmp_path / "archive"

    old_date = _old_date()  # 31 days ago
    old_incident = _make_incident("arch001", old_date)
    _write_current(current_path, [old_incident])

    merge_and_write([], current_path, archive_dir=archive_dir)

    # Archive file should exist and contain the aged-out incident
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_files = list(archive_dir.glob("*.json"))
    assert len(archive_files) >= 1, "Archive file must be written for aged-out incidents"
    archive_data = json.loads(archive_files[0].read_text(encoding="utf-8"))
    archive_ids = [i["id"] for i in archive_data.get("incidents", [])]
    assert "arch001" in archive_ids
