"""
pipeline/tests/test_archive_r2.py

Tests for pipeline/archive_r2.py and pipeline/news/fulltext.py.

Strategy:
- NEVER hit live network — patch ft.requests and ft.trafilatura at module level
- NEVER construct a real boto3 client — patch ar._make_r2_client
- Dynamic dates via datetime — no hardcoded literal dates (time-bomb prevention)
- tmp_path for any data dir that needs to be on disk
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from collections import Counter
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

import pipeline.archive_r2 as ar
import pipeline.news.fulltext as ft


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_inc(inc_id="A", outlet="BioBioChile", date=None, family="robo",
              title_es="Titulo", url="https://biobiochile.cl/nota"):
    """Build a minimal incident dict."""
    if date is None:
        date = datetime.utcnow().strftime("%Y-%m-%d")
    return {
        "id": inc_id,
        "outlet": outlet,
        "date": date,
        "family": family,
        "title_es": title_es,
        "title_en": "Title",
        "url": url,
        "cut": "13101",
        "lat": -33.45,
        "lng": -70.67,
        "slug": "santiago",
        "apa": "",
    }


def _spanish_month(month_num: int) -> str:
    return ar._SPANISH_MONTHS[month_num]


# ---------------------------------------------------------------------------
# 1. test_apa_normal
# ---------------------------------------------------------------------------

def test_apa_normal():
    d = datetime.utcnow()
    month_name = _spanish_month(d.month)
    inc = {
        "outlet": "Emol",
        "date": d.strftime("%Y-%m-%d"),
        "title_es": "Robo en Santiago",
        "url": "https://emol.com/nota",
    }
    result = ar.format_apa(inc)
    assert result == f"Emol. ({d.year}, {d.day} de {month_name}). Robo en Santiago. https://emol.com/nota"


# ---------------------------------------------------------------------------
# 2. test_apa_missing_outlet
# ---------------------------------------------------------------------------

def test_apa_missing_outlet():
    d = datetime.utcnow()
    for outlet_val in ["", "   ", None]:
        inc = {
            "outlet": outlet_val,
            "date": d.strftime("%Y-%m-%d"),
            "title_es": "Titulo",
            "url": "https://x.cl",
        }
        result = ar.format_apa(inc)
        assert result.startswith("s. a. ("), f"Expected 's. a. (' prefix, got: {result!r}"


# ---------------------------------------------------------------------------
# 3. test_apa_malformed_date
# ---------------------------------------------------------------------------

def test_apa_malformed_date():
    for bad_date in ["not-a-date", "", None]:
        inc = {
            "outlet": "Emol",
            "date": bad_date,
            "title_es": "Titulo",
            "url": "https://x.cl",
        }
        result = ar.format_apa(inc)
        assert "(s. f.)" in result, f"Expected '(s. f.)' in: {result!r}"


# ---------------------------------------------------------------------------
# 4. test_consolidate_dedup_current_wins
# ---------------------------------------------------------------------------

def test_consolidate_dedup_current_wins(tmp_path):
    data_dir = tmp_path / "incidents"
    data_dir.mkdir()
    archive_dir = data_dir / "archive"
    archive_dir.mkdir()

    # Archive has id=X with outlet ArchiveOutlet + id=Y
    archive = {
        "generated": "2020-01-01",
        "window_days": 30,
        "incidents": [
            _make_inc("X", outlet="ArchiveOutlet"),
            _make_inc("Y", outlet="OtherOutlet"),
        ],
    }
    (archive_dir / "2020-01.json").write_text(json.dumps(archive), encoding="utf-8")

    # Current has id=X with outlet CurrentOutlet (should win)
    current = {
        "generated": "2026-07-01",
        "window_days": 30,
        "incidents": [
            _make_inc("X", outlet="CurrentOutlet"),
        ],
    }
    (data_dir / "current.json").write_text(json.dumps(current), encoding="utf-8")

    result = ar.consolidate_incidents(data_dir)

    ids = [i["id"] for i in result]
    assert len(result) == 2, f"Expected 2 records, got {len(result)}: {ids}"
    assert "X" in ids and "Y" in ids

    x_rec = next(i for i in result if i["id"] == "X")
    assert x_rec["outlet"] == "CurrentOutlet", f"Current should win, got {x_rec['outlet']}"

    for inc in result:
        assert inc.get("apa"), f"Missing apa for id={inc['id']}"


# ---------------------------------------------------------------------------
# 5. test_csv_has_bom_and_header
# ---------------------------------------------------------------------------

def test_csv_has_bom_and_header():
    inc = _make_inc()
    inc["apa"] = ar.format_apa(inc)
    csv_bytes = ar.to_csv([inc])
    assert csv_bytes[:3] == b"\xef\xbb\xbf", "CSV must start with UTF-8 BOM"
    text = csv_bytes.decode("utf-8-sig")
    first_line = text.splitlines()[0]
    assert first_line == "id,date,cut,slug,family,outlet,title_es,title_en,url,lat,lng,apa"


# ---------------------------------------------------------------------------
# 6. test_upload_calls_put_object
# ---------------------------------------------------------------------------

def test_upload_calls_put_object(monkeypatch):
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://r2.example.com")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "fakekey")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "fakesecret")
    monkeypatch.setenv("R2_BUCKET", "testbucket")
    monkeypatch.setenv("ARCHIVE_MAX_FETCH", "0")

    mock_client = MagicMock()
    # Simulate no ledger stored yet
    mock_client.get_object.side_effect = Exception("NoSuchKey")

    monkeypatch.setattr(ar, "_make_r2_client", lambda *a, **kw: mock_client)
    monkeypatch.setattr(ar, "consolidate_incidents", lambda _: [_make_inc("Z")])

    result = ar.main()
    assert result == 0

    called_keys = {call.kwargs.get("Key") or call.args[0] if call.args else None
                   for call in mock_client.put_object.call_args_list}
    # Flatten — collect from kwargs
    called_keys = set()
    for call in mock_client.put_object.call_args_list:
        k = call.kwargs.get("Key") or (call.args[1] if len(call.args) > 1 else None)
        if k:
            called_keys.add(k)

    assert any("incidents.jsonl" in k for k in called_keys), f"Missing incidents.jsonl in {called_keys}"
    assert any("incidents.csv" in k for k in called_keys), f"Missing incidents.csv in {called_keys}"
    assert any("manifest.json" in k for k in called_keys), f"Missing manifest.json in {called_keys}"
    assert any("url-ledger.jsonl" in k for k in called_keys), f"Missing url-ledger.jsonl in {called_keys}"
    assert any("corpus-state.json" in k for k in called_keys), f"Missing corpus-state.json in {called_keys}"


# ---------------------------------------------------------------------------
# 7. test_missing_env_returns_zero_no_client
# ---------------------------------------------------------------------------

def test_missing_env_returns_zero_no_client(monkeypatch):
    for var in ["R2_ENDPOINT_URL", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"]:
        monkeypatch.delenv(var, raising=False)

    mock_factory = MagicMock()
    monkeypatch.setattr(ar, "_make_r2_client", mock_factory)

    result = ar.main()
    assert result == 0
    mock_factory.assert_not_called()


# ---------------------------------------------------------------------------
# 8. test_fetch_article_mocked_success
# ---------------------------------------------------------------------------

def test_fetch_article_mocked_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://outlet.cl/final"
    mock_resp.text = "<html><body>Contenido</body></html>"

    with patch.object(ft, "requests") as mock_req, \
         patch.object(ft, "trafilatura") as mock_traf:
        mock_req.get.return_value = mock_resp
        mock_req.RequestException = Exception
        mock_traf.extract.return_value = "texto extraído"

        res = ft.fetch_article("https://news.google.com/rss/x")

    assert res["extraction_ok"] is True
    assert res["final_url"] == "https://outlet.cl/final"
    assert res["http_status"] == 200


# ---------------------------------------------------------------------------
# 9. test_fetch_article_non_2xx
# ---------------------------------------------------------------------------

def test_fetch_article_non_2xx():
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.url = "https://outlet.cl/not-found"
    mock_resp.text = ""

    with patch.object(ft, "requests") as mock_req, \
         patch.object(ft, "trafilatura"):
        mock_req.get.return_value = mock_resp
        mock_req.RequestException = Exception

        res = ft.fetch_article("https://outlet.cl/not-found")

    assert res["extraction_ok"] is False
    assert res["text"] == ""


# ---------------------------------------------------------------------------
# 10. test_fetch_article_empty_extraction
# ---------------------------------------------------------------------------

def test_fetch_article_empty_extraction():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://outlet.cl/ok"
    mock_resp.text = "<html></html>"

    with patch.object(ft, "requests") as mock_req, \
         patch.object(ft, "trafilatura") as mock_traf:
        mock_req.get.return_value = mock_resp
        mock_req.RequestException = Exception
        mock_traf.extract.return_value = ""

        res = ft.fetch_article("https://outlet.cl/ok")

    assert res["extraction_ok"] is False


# ---------------------------------------------------------------------------
# 11. test_build_article_object_2mb_cap
# ---------------------------------------------------------------------------

def test_build_article_object_2mb_cap():
    MB2 = 2 * 1024 * 1024
    long_text = "a" * (3 * 1024 * 1024)  # 3 MB of ASCII
    inc = _make_inc()
    inc["apa"] = "APA string"
    fetch_result = {
        "final_url": "https://x.cl/a",
        "http_status": 200,
        "extraction_ok": True,
        "text": long_text,
        "lang": None,
    }
    obj = ft.build_article_object(inc, fetch_result)

    assert len(obj["text"].encode("utf-8")) <= MB2
    assert obj["char_count"] == len(obj["text"])

    expected_sha = hashlib.sha256(obj["text"].encode("utf-8")).hexdigest()
    assert obj["text_sha256"] == expected_sha


# ---------------------------------------------------------------------------
# 12. test_merge_ledger_pending_to_fetched
# ---------------------------------------------------------------------------

def test_merge_ledger_pending_to_fetched():
    inc = _make_inc("A")
    outcomes = {
        "A": {
            "ok": True,
            "final_url": "https://outlet.cl/final",
            "text_sha256": "deadbeef",
            "char_count": 500,
            "fetched_at": "2026-07-26T05:30:00+00:00",
        }
    }
    result = ar.merge_ledger({}, [inc], outcomes)
    assert result["A"]["status"] == "fetched"
    assert result["A"]["text_sha256"] == "deadbeef"


# ---------------------------------------------------------------------------
# 13. test_merge_ledger_attempts_and_permanent_failure
# ---------------------------------------------------------------------------

def test_merge_ledger_attempts_and_permanent_failure():
    existing = {
        "A": {
            "id": "A",
            "url": "https://x.cl",
            "final_url": None,
            "status": "failed",
            "attempts": 2,
            "fetched_at": None,
            "text_sha256": None,
            "char_count": 0,
        }
    }
    inc = _make_inc("A")
    outcomes = {"A": {"ok": False}}

    result = ar.merge_ledger(existing, [inc], outcomes)
    assert result["A"]["attempts"] == 3
    assert result["A"]["status"] == "permanent_failure"


# ---------------------------------------------------------------------------
# 14. test_merge_ledger_append_only_fetched_unchanged
# ---------------------------------------------------------------------------

def test_merge_ledger_append_only_fetched_unchanged():
    existing = {
        "A": {
            "id": "A",
            "url": "https://x.cl",
            "final_url": "https://x.cl/final",
            "status": "fetched",
            "attempts": 1,
            "fetched_at": "2026-07-01T00:00:00+00:00",
            "text_sha256": "abc",
            "char_count": 100,
        }
    }
    inc = _make_inc("A")
    outcomes = {"A": {"ok": False}}  # Would normally degrade the row

    result = ar.merge_ledger(existing, [inc], outcomes)
    assert result["A"]["status"] == "fetched"
    assert result["A"]["text_sha256"] == "abc"
    assert result["A"]["attempts"] == 1


# ---------------------------------------------------------------------------
# 15. test_build_corpus_state_aggregation
# ---------------------------------------------------------------------------

def test_build_corpus_state_aggregation():
    ledger = {
        "A": {
            "id": "A", "status": "fetched",
            "char_count": 5, "text_sha256": "h1",
            "fetched_at": "2026-07-01T00:00:00+00:00",
        },
        "B": {
            "id": "B", "status": "failed",
            "char_count": 0, "text_sha256": None,
            "fetched_at": None,
        },
        "C": {
            "id": "C", "status": "pending",
            "char_count": 0, "text_sha256": None,
            "fetched_at": None,
        },
    }
    incidents = [
        {"id": "A", "outlet": "Emol", "family": "robo", "date": "2026-07-01"},
        {"id": "B", "outlet": "BioBio", "family": "vida", "date": "2026-06-15"},
        {"id": "C", "outlet": "Emol", "family": "robo", "date": "2026-06-20"},
    ]

    state = ar.build_corpus_state(ledger, incidents)

    assert state["totals"]["fetched_ok"] == 1
    assert state["totals"]["failed"] == 1
    assert state["totals"]["pending"] == 1
    assert state["total_chars"] == 5

    expected_sha = hashlib.sha256("h1".encode("utf-8")).hexdigest()
    assert state["corpus_sha256"] == expected_sha

    assert state["by_outlet"]["Emol"] == 2
    assert state["by_outlet"]["BioBio"] == 1
    assert state["by_family"]["robo"] == 2
    assert state["by_family"]["vida"] == 1
    assert state["by_month"]["2026-07"] == 1
    assert state["by_month"]["2026-06"] == 2
    assert state["schema_version"] == 1


# ---------------------------------------------------------------------------
# 16. test_append_only_guard_no_refetch
# ---------------------------------------------------------------------------

def test_append_only_guard_no_refetch(monkeypatch):
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://r2.example.com")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "fakekey")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "fakesecret")
    monkeypatch.setenv("R2_BUCKET", "testbucket")
    monkeypatch.setenv("ARCHIVE_MAX_FETCH", "10")

    existing_ledger = {
        "A": {
            "id": "A",
            "url": "https://x.cl",
            "final_url": "https://x.cl/final",
            "status": "fetched",
            "attempts": 1,
            "fetched_at": "2026-07-01T00:00:00+00:00",
            "text_sha256": "abc",
            "char_count": 100,
        }
    }

    mock_client = MagicMock()
    # Return the existing ledger from get_object
    ledger_body = "\n".join(json.dumps(row) for row in existing_ledger.values()).encode()
    mock_response = {"Body": MagicMock()}
    mock_response["Body"].read.return_value = ledger_body
    mock_client.get_object.return_value = mock_response

    monkeypatch.setattr(ar, "_make_r2_client", lambda *a, **kw: mock_client)

    inc_a = _make_inc("A")
    inc_a["apa"] = ar.format_apa(inc_a)
    monkeypatch.setattr(ar, "consolidate_incidents", lambda _: [inc_a])

    mock_fetch = MagicMock()
    monkeypatch.setattr(ft, "fetch_article", mock_fetch)

    result = ar.main()
    assert result == 0
    mock_fetch.assert_not_called()
