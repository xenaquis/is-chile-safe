"""
pipeline/tests/test_check_hotfix_regression.py

FID-07 (36-09): tests for pipeline/check_hotfix_regression.py — the hotfixed cards
(quick-260922-t59, G-27) never resurface in data/incidents nor in served HTML.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from pipeline import check_hotfix_regression as chr_mod  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "pipeline" / "check_hotfix_regression.py"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _incident(id_: str, **overrides) -> dict:
    base = {
        "id": id_,
        "cut": "13101",
        "lat": -33.0,
        "lng": -70.0,
        "title_es": "Un titulo cualquiera",
        "title_en": "Some headline",
        "date": "2026-01-01",
        "outlet": "TestOutlet",
        "url": "https://example.com/article",
        "family": "propiedad",
        "slug": "test",
    }
    base.update(overrides)
    return base


def _retitled_incident(**overrides) -> dict:
    fields = {
        "title_es": chr_mod.RETITLED_TITLE_ES,
        "title_en": chr_mod.RETITLED_TITLE_EN,
    }
    fields.update(overrides)
    return _incident(chr_mod.RETITLED_ID, **fields)


def _write_incidents(data_dir: pathlib.Path, current_incidents: list[dict],
                      archive: dict[str, list[dict]] | None = None) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "current.json").write_text(
        json.dumps({"incidents": current_incidents}, ensure_ascii=False), encoding="utf-8"
    )
    if archive:
        archive_dir = data_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        for name, incidents in archive.items():
            (archive_dir / name).write_text(
                json.dumps({"incidents": incidents}, ensure_ascii=False), encoding="utf-8"
            )


# ---------------------------------------------------------------------------
# --data mode
# ---------------------------------------------------------------------------


def test_real_tree_passes(tmp_path):
    """The real data/incidents tree at execution time exits 0 (also exercised via
    the plan's verify step directly against data/incidents)."""
    result = _run(["--data", str(REPO_ROOT / "data" / "incidents")])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout


def test_clean_fixture_passes(tmp_path):
    data_dir = tmp_path / "incidents"
    _write_incidents(data_dir, [_incident("safeid0000000001"), _retitled_incident()])
    result = _run(["--data", str(data_dir)])
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("dropped_id", list(chr_mod.T59_DROPPED_IDS))
def test_t59_id_readded_to_current_fails(tmp_path, dropped_id):
    data_dir = tmp_path / "incidents"
    _write_incidents(
        data_dir,
        [_incident("safeid0000000001"), _retitled_incident(), _incident(dropped_id)],
    )
    result = _run(["--data", str(data_dir)])
    assert result.returncode == 1
    assert dropped_id in result.stdout


def test_g27_id_readded_to_archive_fails(tmp_path):
    data_dir = tmp_path / "incidents"
    _write_incidents(
        data_dir,
        [_incident("safeid0000000001"), _retitled_incident()],
        archive={"2026-09.json": [_incident(chr_mod.G27_DROPPED_ID)]},
    )
    result = _run(["--data", str(data_dir)])
    assert result.returncode == 1
    assert chr_mod.G27_DROPPED_ID in result.stdout


def test_retitled_title_altered_fails(tmp_path):
    data_dir = tmp_path / "incidents"
    _write_incidents(
        data_dir,
        [_incident("safeid0000000001"), _retitled_incident(title_en="Something else entirely")],
    )
    result = _run(["--data", str(data_dir)])
    assert result.returncode == 1
    assert chr_mod.RETITLED_ID in result.stdout


def test_retitled_card_absent_everywhere_fails(tmp_path):
    data_dir = tmp_path / "incidents"
    _write_incidents(data_dir, [_incident("safeid0000000001")])
    result = _run(["--data", str(data_dir)])
    assert result.returncode == 1
    assert "retitled card lost" in result.stdout


def test_retitled_card_present_only_in_archive_passes(tmp_path):
    data_dir = tmp_path / "incidents"
    _write_incidents(
        data_dir,
        [_incident("safeid0000000001")],
        archive={"2026-09.json": [_retitled_incident()]},
    )
    result = _run(["--data", str(data_dir)])
    assert result.returncode == 0, result.stdout + result.stderr


def test_missing_data_dir_exits_2(tmp_path):
    result = _run(["--data", str(tmp_path / "does-not-exist")])
    assert result.returncode == 2


# ---------------------------------------------------------------------------
# --html mode
# ---------------------------------------------------------------------------


def test_html_clean_passes(tmp_path):
    html_path = tmp_path / "news.html"
    html_path.write_text("<html><body>Nothing here</body></html>", encoding="utf-8")
    result = _run(["--html", str(html_path)])
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("url", list(chr_mod.DROPPED_URLS))
def test_html_with_dropped_url_raw_fails(tmp_path, url):
    html_path = tmp_path / "news.html"
    html_path.write_text(f'<a href="{url}">link</a>', encoding="utf-8")
    result = _run(["--html", str(html_path)])
    assert result.returncode == 1
    assert url in result.stdout


def test_html_with_dropped_url_escaped_fails(tmp_path):
    url = chr_mod.DROPPED_URLS[0]
    escaped = url.replace("&", "&amp;")
    html_path = tmp_path / "news.html"
    html_path.write_text(f'<a href="{escaped}">link</a>', encoding="utf-8")
    result = _run(["--html", str(html_path)])
    assert result.returncode == 1


def test_html_multiple_files_one_dirty_fails(tmp_path):
    clean = tmp_path / "a.html"
    dirty = tmp_path / "b.html"
    clean.write_text("<html>clean</html>", encoding="utf-8")
    dirty.write_text(f'<a href="{chr_mod.DROPPED_URLS[1]}">x</a>', encoding="utf-8")
    result = _run(["--html", str(clean), str(dirty)])
    assert result.returncode == 1


def test_html_retitled_strings_present_passes(tmp_path):
    news_dir = tmp_path / "news"
    noticias_dir = tmp_path / "noticias"
    news_dir.mkdir()
    noticias_dir.mkdir()
    en_html = news_dir / "index.html"
    es_html = noticias_dir / "index.html"
    en_html.write_text(f"<html>{chr_mod.RETITLED_TITLE_EN}</html>", encoding="utf-8")
    es_html.write_text(f"<html>{chr_mod.RETITLED_TITLE_ES}</html>", encoding="utf-8")

    current = tmp_path / "current.json"
    current.write_text(
        json.dumps({"incidents": [_retitled_incident()]}, ensure_ascii=False), encoding="utf-8"
    )

    result = _run(["--html", str(en_html), str(es_html), "--current", str(current)])
    assert result.returncode == 0, result.stdout + result.stderr


def test_html_retitled_string_missing_fails(tmp_path):
    news_dir = tmp_path / "news"
    noticias_dir = tmp_path / "noticias"
    news_dir.mkdir()
    noticias_dir.mkdir()
    en_html = news_dir / "index.html"
    es_html = noticias_dir / "index.html"
    en_html.write_text("<html>no retitled string here</html>", encoding="utf-8")
    es_html.write_text(f"<html>{chr_mod.RETITLED_TITLE_ES}</html>", encoding="utf-8")

    current = tmp_path / "current.json"
    current.write_text(
        json.dumps({"incidents": [_retitled_incident()]}, ensure_ascii=False), encoding="utf-8"
    )

    result = _run(["--html", str(en_html), str(es_html), "--current", str(current)])
    assert result.returncode == 1
    assert "EN html" in result.stdout


def test_html_current_without_retitled_id_skips_check(tmp_path):
    news_dir = tmp_path / "news"
    news_dir.mkdir()
    en_html = news_dir / "index.html"
    en_html.write_text("<html>irrelevant</html>", encoding="utf-8")

    current = tmp_path / "current.json"
    current.write_text(
        json.dumps({"incidents": [_incident("safeid0000000001")]}, ensure_ascii=False),
        encoding="utf-8",
    )

    result = _run(["--html", str(en_html), "--current", str(current)])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "skipped" in (result.stdout + result.stderr)


def test_missing_html_file_exits_2(tmp_path):
    result = _run(["--html", str(tmp_path / "nope.html")])
    assert result.returncode == 2


def test_current_without_html_errors(tmp_path):
    current = tmp_path / "current.json"
    current.write_text(json.dumps({"incidents": []}), encoding="utf-8")
    result = _run(["--current", str(current)])
    assert result.returncode == 2


def test_data_and_html_mutually_exclusive(tmp_path):
    data_dir = tmp_path / "incidents"
    _write_incidents(data_dir, [_incident("safeid0000000001")])
    html_path = tmp_path / "news.html"
    html_path.write_text("<html></html>", encoding="utf-8")
    result = _run(["--data", str(data_dir), "--html", str(html_path)])
    assert result.returncode == 2
