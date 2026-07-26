"""
pipeline/tests/test_store.py

Tests for pipeline/news/store.py — 30-day window, idempotent merge, archive write.
Uses tmp_path pytest built-in fixture for isolation.
"""
from __future__ import annotations

import copy
import datetime
import json

import pytest

from pipeline.news.store import merge_and_write  # type: ignore


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


def test_build_incident_passes_slug():
    """build_incident with slug= returns a dict whose 'slug' == the given value."""
    from pipeline.news.store import build_incident
    incident = build_incident(
        url="https://biobiochile.cl/article/slug-test",
        cut="13101",
        lat=-33.456,
        lng=-70.654,
        title_es="Incidente con slug",
        title_en="Incident with slug",
        date="2026-06-13",
        outlet="BioBio Chile",
        family="propiedad",
        slug="las-condes",
    )
    assert incident["slug"] == "las-condes"


def test_build_incident_accepts_http_url():
    """build_incident with an http URL returns a valid incident dict (not None)."""
    from pipeline.news.store import build_incident
    result = build_incident(
        url="http://biobiochile.cl/article/test",
        cut="13101",
        lat=-33.456,
        lng=-70.654,
        title_es="Incidente http",
        title_en="Incident http",
        date="2026-06-15",
        outlet="BioBio Chile",
        family="propiedad",
    )
    assert result is not None
    assert result["url"] == "http://biobiochile.cl/article/test"


def test_build_incident_accepts_https_url():
    """build_incident with an https URL returns a valid incident dict (not None)."""
    from pipeline.news.store import build_incident
    result = build_incident(
        url="https://biobiochile.cl/article/test",
        cut="13101",
        lat=-33.456,
        lng=-70.654,
        title_es="Incidente https",
        title_en="Incident https",
        date="2026-06-15",
        outlet="BioBio Chile",
        family="propiedad",
    )
    assert result is not None
    assert result["url"] == "https://biobiochile.cl/article/test"


def test_build_incident_rejects_javascript_url():
    """build_incident with a javascript: URL must return None (TD-05, T-19-04)."""
    from pipeline.news.store import build_incident
    result = build_incident(
        url="javascript:alert(1)",
        cut="13101",
        lat=-33.456,
        lng=-70.654,
        title_es="Incidente malicioso",
        title_en="Malicious incident",
        date="2026-06-15",
        outlet="BioBio Chile",
        family="propiedad",
    )
    assert result is None, "javascript: URL must be rejected by build_incident"


def test_build_incident_rejects_data_url():
    """build_incident with a data: URL must return None (TD-05, T-19-04)."""
    from pipeline.news.store import build_incident
    result = build_incident(
        url="data:text/html,<script>alert(1)</script>",
        cut="13101",
        lat=-33.456,
        lng=-70.654,
        title_es="Incidente data",
        title_en="Data incident",
        date="2026-06-15",
        outlet="BioBio Chile",
        family="propiedad",
    )
    assert result is None, "data: URL must be rejected by build_incident"


def test_build_incident_rejects_ftp_url():
    """build_incident with an ftp: URL must return None (TD-05, T-19-04)."""
    from pipeline.news.store import build_incident
    result = build_incident(
        url="ftp://example.com/file.txt",
        cut="13101",
        lat=-33.456,
        lng=-70.654,
        title_es="Incidente ftp",
        title_en="FTP incident",
        date="2026-06-15",
        outlet="BioBio Chile",
        family="propiedad",
    )
    assert result is None, "ftp: URL must be rejected by build_incident"


def test_build_incident_rejects_malformed_url():
    """build_incident with an unparseable URL must return None (TD-05, T-19-04)."""
    from pipeline.news.store import build_incident
    result = build_incident(
        url="not a url at all !!",
        cut="13101",
        lat=-33.456,
        lng=-70.654,
        title_es="Incidente malformado",
        title_en="Malformed incident",
        date="2026-06-15",
        outlet="BioBio Chile",
        family="propiedad",
    )
    assert result is None, "Malformed URL must be rejected by build_incident"


def test_merge_and_write_excludes_invalid_url_incidents(tmp_path):
    """merge_and_write must not persist incidents whose url scheme is not http/https."""
    from pipeline.news.store import build_incident
    current_path = tmp_path / "current.json"
    archive_dir = tmp_path / "archive"

    # Build one valid and one that would be invalid (manually craft since build_incident would reject)
    valid_incident = build_incident(
        url="https://biobiochile.cl/article/valid",
        cut="13101",
        lat=-33.456,
        lng=-70.654,
        title_es="Válido",
        title_en="Valid",
        date=_fresh_date(),
        outlet="BioBio Chile",
        family="propiedad",
    )
    assert valid_incident is not None

    # Simulate a bad incident sneaking in (e.g. from old data) with non-http scheme
    bad_incident = {
        "id": "bad000000000001",
        "cut": "13101",
        "lat": -33.456,
        "lng": -70.654,
        "title_es": "Malo",
        "title_en": "Bad",
        "date": _fresh_date(),
        "outlet": "Unknown",
        "url": "javascript:alert(1)",
        "family": "propiedad",
        "slug": None,
    }

    merge_and_write([valid_incident, bad_incident], current_path, archive_dir=archive_dir)

    import json
    result = json.loads(current_path.read_text(encoding="utf-8"))
    urls = [i["url"] for i in result["incidents"]]
    assert "javascript:alert(1)" not in urls, "Non-http(s) URL must not be persisted"
    assert "https://biobiochile.cl/article/valid" in urls, "Valid http(s) URL must be persisted"


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
