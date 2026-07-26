"""
pipeline/tests/test_rejected_capture.py

Tests for pipeline/scrape_news.record_rejected.

Strategy:
- All I/O uses tmp_path (no permanent state)
- No hardcoded dates — derive month via datetime.now(timezone.utc)
- No network calls
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from pipeline.scrape_news import record_rejected


def _make_item(
    url: str = "https://emol.com/nota",
    outlet: str = "Emol",
    title: str = "Robo en calle X",
    description: str = "Se registró un robo",
    rejection_stage: str = "classifier_none",
    date: str | None = None,
) -> dict:
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "url": url,
        "outlet": outlet,
        "title": title,
        "description": description,
        "rejection_stage": rejection_stage,
        "date": date,
    }


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


# ---------------------------------------------------------------------------
# 1. Writes monthly file with correct envelope and fields
# ---------------------------------------------------------------------------

def test_record_rejected_writes_file(tmp_path):
    item = _make_item()
    record_rejected([item], tmp_path)

    month = _current_month()
    target = tmp_path / "rejected" / f"{month}.json"
    assert target.exists(), f"Expected file at {target}"

    envelope = json.loads(target.read_text("utf-8"))
    assert "generated" in envelope
    assert "items" in envelope
    assert len(envelope["items"]) == 1

    rec = envelope["items"][0]
    assert rec["url"] == item["url"]
    assert rec["outlet"] == item["outlet"]
    assert rec["title"] == item["title"]
    assert rec["rejection_stage"] == item["rejection_stage"]
    assert "id" in rec
    assert "first_seen" in rec


# ---------------------------------------------------------------------------
# 2. description capped at 500 chars and HTML stripped
# ---------------------------------------------------------------------------

def test_record_rejected_description_cap_and_strip(tmp_path):
    long_html = "<p>" + "a" * 1000 + "</p>"
    item = _make_item(description=long_html)
    record_rejected([item], tmp_path)

    month = _current_month()
    envelope = json.loads((tmp_path / "rejected" / f"{month}.json").read_text("utf-8"))
    desc = envelope["items"][0]["description"]

    # No HTML tags
    assert "<p>" not in desc
    assert "</p>" not in desc
    # Capped at 500 chars
    assert len(desc) <= 500


# ---------------------------------------------------------------------------
# 3. Dedup: calling twice with same URL does not duplicate; first_seen preserved
# ---------------------------------------------------------------------------

def test_record_rejected_dedup(tmp_path):
    item = _make_item(url="https://biobiochile.cl/nota/1")
    record_rejected([item], tmp_path)

    month = _current_month()
    target = tmp_path / "rejected" / f"{month}.json"
    first_envelope = json.loads(target.read_text("utf-8"))
    original_first_seen = first_envelope["items"][0]["first_seen"]

    # Call again with same URL
    record_rejected([item], tmp_path)
    second_envelope = json.loads(target.read_text("utf-8"))

    assert len(second_envelope["items"]) == 1, "Duplicate must not be added"
    assert second_envelope["items"][0]["first_seen"] == original_first_seen, \
        "first_seen must be preserved on dedup"


# ---------------------------------------------------------------------------
# 4. Stage labels round-trip correctly
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("stage", [
    "classifier_none",
    "commune_null",
    "resolver_fail",
    "centroid_fail",
])
def test_record_rejected_stage_labels(tmp_path, stage):
    item = _make_item(
        url=f"https://emol.com/{stage}",
        rejection_stage=stage,
    )
    record_rejected([item], tmp_path)

    month = _current_month()
    envelope = json.loads((tmp_path / "rejected" / f"{month}.json").read_text("utf-8"))
    rec = next(r for r in envelope["items"] if r["rejection_stage"] == stage)
    assert rec["rejection_stage"] == stage


# ---------------------------------------------------------------------------
# 5. Graceful when rejected/ dir does not pre-exist
# ---------------------------------------------------------------------------

def test_record_rejected_creates_dir(tmp_path):
    data_dir = tmp_path / "incidents"
    # Do NOT create data_dir/rejected/ — let record_rejected create it
    item = _make_item()
    record_rejected([item], data_dir)  # should not raise

    month = _current_month()
    assert (data_dir / "rejected" / f"{month}.json").exists()


# ---------------------------------------------------------------------------
# 6. Empty items list: no file written (noop)
# ---------------------------------------------------------------------------

def test_record_rejected_empty_list_noop(tmp_path):
    record_rejected([], tmp_path)
    assert not (tmp_path / "rejected").exists() or \
        len(list((tmp_path / "rejected").glob("*.json"))) == 0


# ---------------------------------------------------------------------------
# 7. Multiple items in one call
# ---------------------------------------------------------------------------

def test_record_rejected_multiple_items(tmp_path):
    items = [
        _make_item(url=f"https://emol.com/nota/{i}", rejection_stage="classifier_none")
        for i in range(5)
    ]
    record_rejected(items, tmp_path)

    month = _current_month()
    envelope = json.loads((tmp_path / "rejected" / f"{month}.json").read_text("utf-8"))
    assert len(envelope["items"]) == 5


# ---------------------------------------------------------------------------
# 8. Merges new items into existing file without dropping old ones
# ---------------------------------------------------------------------------

def test_record_rejected_merges_with_existing(tmp_path):
    item1 = _make_item(url="https://emol.com/1")
    item2 = _make_item(url="https://emol.com/2")

    record_rejected([item1], tmp_path)
    record_rejected([item2], tmp_path)

    month = _current_month()
    envelope = json.loads((tmp_path / "rejected" / f"{month}.json").read_text("utf-8"))
    urls = {r["url"] for r in envelope["items"]}
    assert "https://emol.com/1" in urls
    assert "https://emol.com/2" in urls
