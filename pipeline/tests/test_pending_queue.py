"""
pipeline/tests/test_pending_queue.py

Pure unit tests for pipeline/news/pending.py — the G-03 retry queue
(data/incidents/pending.json; tests only write to tmp_path).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from pipeline.news import pending as pq

NOW = datetime(2026, 9, 22, 12, 0, 0, tzinfo=timezone.utc)


def _cand(i: int) -> dict:
    return {
        "url": f"https://example.cl/n/{i}",
        "title": f"Robo {i}",
        "description": "desc",
        "date": "2026-09-21",
        "outlet": "BioBioChile",
    }


def test_knobs_match_g03():
    assert pq.PENDING_MAX_ATTEMPTS == 5
    assert pq.PENDING_MAX_AGE_DAYS == 14


def test_item_id_matches_store_make_id():
    from pipeline.news.store import make_id
    assert pq.item_id("https://example.cl/n/1") == make_id("https://example.cl/n/1")


def test_upsert_new_attempted_and_unattempted():
    items = pq.upsert_failure([], _cand(1), NOW, "NotFoundError:404", attempted=True)
    assert len(items) == 1
    it = items[0]
    assert it["attempts"] == 1 and it["last_error"] == "NotFoundError:404"
    assert it["id"] == pq.item_id(_cand(1)["url"])
    assert it["first_queued"] == "2026-09-22T12:00:00+00:00"
    assert set(it) == {"id", "url", "title", "description", "date", "outlet",
                       "first_queued", "attempts", "last_error"}

    items2 = pq.upsert_failure([], _cand(2), NOW, None, attempted=False)
    assert items2[0]["attempts"] == 0 and items2[0]["last_error"] is None


def test_upsert_existing_increments_only_when_attempted():
    items = pq.upsert_failure([], _cand(1), NOW, "e1", attempted=True)
    later = NOW + timedelta(hours=6)
    items = pq.upsert_failure(items, _cand(1), later, "e2", attempted=True)
    assert len(items) == 1
    assert items[0]["attempts"] == 2 and items[0]["last_error"] == "e2"
    assert items[0]["first_queued"] == "2026-09-22T12:00:00+00:00"  # preserved
    items = pq.upsert_failure(items, _cand(1), later, None, attempted=False)
    assert items[0]["attempts"] == 2 and items[0]["last_error"] == "e2"


def test_upsert_does_not_mutate_input():
    items = pq.upsert_failure([], _cand(1), NOW, "e", attempted=True)
    snapshot = json.dumps(items)
    pq.upsert_failure(items, _cand(1), NOW, "e", attempted=True)
    assert json.dumps(items) == snapshot


def test_remove():
    items = pq.upsert_failure([], _cand(1), NOW, "e", attempted=True)
    items = pq.upsert_failure(items, _cand(2), NOW, "e", attempted=True)
    left = pq.remove(items, pq.item_id(_cand(1)["url"]))
    assert [i["url"] for i in left] == [_cand(2)["url"]]


@pytest.mark.parametrize(
    "attempts,age_days,expired",
    [
        (4, 1, False),
        (5, 1, True),
        (1, 14, False),          # exactly 14 days is not "older than 14 days"
        (1, 14.0001, True),
        (0, 30, True),
    ],
)
def test_split_expired(attempts, age_days, expired):
    it = {
        "id": "x", "url": "u", "attempts": attempts,
        "first_queued": (NOW - timedelta(days=age_days)).isoformat(timespec="seconds"),
    }
    keep, exp = pq.split_expired([it], NOW)
    assert (exp == [it]) is expired
    assert (keep == [it]) is (not expired)


def test_split_expired_unparseable_date_kept():
    it = {"id": "x", "url": "u", "attempts": 1, "first_queued": "garbage"}
    keep, exp = pq.split_expired([it], NOW)
    assert keep == [it] and exp == []


def test_load_missing_is_empty(tmp_path):
    assert pq.load_pending(tmp_path / "pending.json") == []


def test_load_malformed_raises(tmp_path):
    p = tmp_path / "pending.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError):
        pq.load_pending(p)
    p.write_text('{"items": {}}', encoding="utf-8")
    with pytest.raises(ValueError):
        pq.load_pending(p)


def test_save_roundtrip_sorted_no_generated_field(tmp_path):
    p = tmp_path / "pending.json"
    a = pq.upsert_failure([], _cand(2), NOW, "e", attempted=True)
    b = pq.upsert_failure(a, _cand(1), NOW - timedelta(days=1), "e", attempted=True)
    assert pq.save_pending(p, b) is True
    env = json.loads(p.read_text(encoding="utf-8"))
    assert list(env) == ["items"]
    assert [i["url"] for i in env["items"]] == [_cand(1)["url"], _cand(2)["url"]]
    assert pq.load_pending(p) == env["items"]


def test_save_only_when_changed(tmp_path):
    p = tmp_path / "pending.json"
    items = pq.upsert_failure([], _cand(1), NOW, "e", attempted=True)
    assert pq.save_pending(p, items) is True
    before = (p.read_bytes(), p.stat().st_mtime_ns)
    # Same content, different order in memory → still no rewrite.
    assert pq.save_pending(p, list(reversed(items))) is False
    assert (p.read_bytes(), p.stat().st_mtime_ns) == before
    items2 = pq.upsert_failure(items, _cand(1), NOW, "e2", attempted=True)
    assert pq.save_pending(p, items2) is True


def test_save_empty_without_file_writes_nothing(tmp_path):
    p = tmp_path / "pending.json"
    assert pq.save_pending(p, []) is False
    assert not p.exists()


def test_save_empty_with_existing_file_clears_queue(tmp_path):
    p = tmp_path / "pending.json"
    pq.save_pending(p, pq.upsert_failure([], _cand(1), NOW, "e", attempted=True))
    assert pq.save_pending(p, []) is True
    assert json.loads(p.read_text(encoding="utf-8")) == {"items": []}
