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


@pytest.fixture(autouse=True)
def _stub_dns(monkeypatch):
    """is_safe_url resolves DNS in production; stub it to a public IP so the
    mocked fetch tests never touch the live network."""
    monkeypatch.setattr(
        ft.socket, "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 0))],
    )


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
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.iter_content.return_value = iter([b"<html><body>Contenido</body></html>"])
    mock_resp.encoding = "utf-8"

    with patch.object(ft, "requests") as mock_req, \
         patch.object(ft, "trafilatura") as mock_traf:
        mock_req.get.return_value = mock_resp
        mock_req.RequestException = Exception
        mock_traf.extract.return_value = "texto extraído"

        # Use a non-gnews URL to avoid decoder path
        res = ft.fetch_article("https://outlet.cl/nota")

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
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.iter_content.return_value = iter([])

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
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.iter_content.return_value = iter([b"<html></html>"])
    mock_resp.encoding = "utf-8"

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
    """
    Schema v2: totals split by kind. Legacy rows without 'kind' default to "incident".
    """
    ledger = {
        "A": {
            "id": "A", "status": "fetched", "kind": "incident",
            "char_count": 5, "text_sha256": "h1",
            "fetched_at": "2026-07-01T00:00:00+00:00",
        },
        "B": {
            "id": "B", "status": "failed", "kind": "incident",
            "char_count": 0, "text_sha256": None,
            "fetched_at": None,
        },
        "C": {
            "id": "C", "status": "pending",  # legacy: no kind field → defaults to "incident"
            "char_count": 0, "text_sha256": None,
            "fetched_at": None,
        },
        "R1": {
            "id": "R1", "status": "pending", "kind": "rejected",
            "char_count": 0, "text_sha256": None,
            "fetched_at": None,
        },
    }
    incidents = [
        {"id": "A", "outlet": "Emol", "family": "robo", "date": "2026-07-01"},
        {"id": "B", "outlet": "BioBio", "family": "vida", "date": "2026-06-15"},
        {"id": "C", "outlet": "Emol", "family": "robo", "date": "2026-06-20"},
    ]
    rejected_list = [
        {"id": "R1", "rejection_stage": "classifier_none", "outlet": "T13", "date": "2026-07-01"},
    ]

    state = ar.build_corpus_state(ledger, incidents, rejected_list)

    # v2 nested totals
    assert state["totals"]["incidents"]["fetched_ok"] == 1
    assert state["totals"]["incidents"]["failed"] == 1
    assert state["totals"]["incidents"]["pending"] == 1   # legacy row C
    assert state["totals"]["rejected"]["pending"] == 1
    assert state["total_chars"] == 5

    expected_sha = hashlib.sha256("h1".encode("utf-8")).hexdigest()
    assert state["corpus_sha256"] == expected_sha

    assert state["by_outlet"]["Emol"] == 2
    assert state["by_outlet"]["BioBio"] == 1
    assert state["by_family"]["robo"] == 2
    assert state["by_family"]["vida"] == 1
    assert state["by_month"]["2026-07"] == 1
    assert state["by_month"]["2026-06"] == 2
    assert state["schema_version"] == 2

    # rejected_by_stage
    assert state["rejected_by_stage"]["classifier_none"] == 1


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


# ---------------------------------------------------------------------------
# 17. Empty R2_BUCKET secret falls back to default (run 30208466155 regression)
# ---------------------------------------------------------------------------

def test_empty_bucket_env_falls_back_to_default(monkeypatch):
    """GitHub Actions injects unset secrets as empty strings — Bucket must
    fall back to 'ischilesafe', never be ''."""
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://r2.example.com")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "fakekey")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "fakesecret")
    monkeypatch.setenv("R2_BUCKET", "")  # empty string, NOT missing
    monkeypatch.setenv("ARCHIVE_MAX_FETCH", "0")

    mock_client = MagicMock()
    mock_client.get_object.side_effect = Exception("NoSuchKey")
    monkeypatch.setattr(ar, "_make_r2_client", lambda *a, **kw: mock_client)
    monkeypatch.setattr(ar, "consolidate_incidents", lambda _: [_make_inc("Z")])

    result = ar.main()
    assert result == 0

    buckets = {c.kwargs.get("Bucket") for c in mock_client.put_object.call_args_list}
    assert buckets == {"ischilesafe"}, f"Expected default bucket, got {buckets}"


# ---------------------------------------------------------------------------
# 18. Preflight head_bucket failure aborts loud (exit 1) before any fetch
# ---------------------------------------------------------------------------

def test_preflight_failure_returns_1_no_fetch(monkeypatch):
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://r2.example.com")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "fakekey")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "fakesecret")
    monkeypatch.setenv("R2_BUCKET", "testbucket")

    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = Exception("403 Forbidden")
    monkeypatch.setattr(ar, "_make_r2_client", lambda *a, **kw: mock_client)
    monkeypatch.setattr(ar, "consolidate_incidents", lambda _: [_make_inc("Z")])

    fetch_spy = MagicMock()
    monkeypatch.setattr(ar, "fetch_article", fetch_spy, raising=False)

    result = ar.main()
    assert result == 1, "Bad credentials/bucket must fail loud (CI alert), not exit 0"
    fetch_spy.assert_not_called()
    mock_client.put_object.assert_not_called()


# ---------------------------------------------------------------------------
# 19. consolidate_rejected: reads monthly files, dedups, attaches apa
# ---------------------------------------------------------------------------

def test_consolidate_rejected_reads_and_deduplicates(tmp_path):
    import json as _json
    rejected_dir = tmp_path / "rejected"
    rejected_dir.mkdir()

    item1 = {
        "id": "aaaa1111",
        "url": "https://t13.cl/nota/1",
        "outlet": "T13",
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "title": "Robo en plaza",
        "description": "Descripción del evento",
        "rejection_stage": "classifier_none",
        "first_seen": "2026-07-01T00:00:00+00:00",
    }
    # Same id in two files → first-seen wins (dedup)
    file1 = {"generated": "2026-07-01T00:00:00", "items": [item1]}
    file2 = {"generated": "2026-07-02T00:00:00", "items": [{**item1, "outlet": "OTHER"}]}

    (rejected_dir / "2026-07.json").write_text(_json.dumps(file1), encoding="utf-8")
    (rejected_dir / "2026-06.json").write_text(_json.dumps(file2), encoding="utf-8")

    result = ar.consolidate_rejected(tmp_path)

    assert len(result) == 1, f"Expected 1 deduped record, got {len(result)}"
    assert "apa" in result[0], "apa should be attached"


def test_consolidate_rejected_missing_dir_returns_empty(tmp_path):
    result = ar.consolidate_rejected(tmp_path)
    assert result == []


# ---------------------------------------------------------------------------
# 20. merge_ledger backward-compat: legacy row without kind → kind="incident"
# ---------------------------------------------------------------------------

def test_merge_ledger_legacy_row_gains_incident_kind():
    """An existing legacy row WITHOUT 'kind' must gain kind='incident' and stay intact."""
    existing = {
        "A": {
            "id": "A",
            "url": "https://x.cl",
            "final_url": None,
            "status": "pending",
            "attempts": 0,
            "fetched_at": None,
            "text_sha256": None,
            "char_count": 0,
            # No 'kind' field — this is a legacy row
        }
    }
    inc = _make_inc("A")
    # No outcome this run
    result = ar.merge_ledger(existing, [inc], {}, kind="incident")
    assert result["A"].get("kind") == "incident", "Legacy row must gain kind='incident'"
    assert result["A"]["status"] == "pending"  # should not be corrupted


def test_merge_ledger_fetched_legacy_row_immutable():
    """A fetched legacy row (no kind) must remain immutable — kind added, status unchanged."""
    existing = {
        "A": {
            "id": "A",
            "url": "https://x.cl",
            "final_url": "https://x.cl/f",
            "status": "fetched",
            "attempts": 1,
            "fetched_at": "2026-07-01T00:00:00+00:00",
            "text_sha256": "abc123",
            "char_count": 100,
            # No 'kind' — legacy
        }
    }
    inc = _make_inc("A")
    outcomes = {"A": {"ok": False}}  # Would degrade if not immutable
    result = ar.merge_ledger(existing, [inc], outcomes, kind="incident")
    assert result["A"]["status"] == "fetched", "Fetched row must remain immutable"
    assert result["A"]["text_sha256"] == "abc123"


def test_merge_ledger_rejected_kind_set():
    """Records merged with kind='rejected' get kind='rejected' in ledger."""
    rej = {"id": "R1", "url": "https://emol.com/rej"}
    result = ar.merge_ledger({}, [rej], {}, kind="rejected")
    assert result["R1"]["kind"] == "rejected"


# ---------------------------------------------------------------------------
# 21. Rejected article uploaded with kind="rejected" and rejected.jsonl uploaded
# ---------------------------------------------------------------------------

def test_rejected_article_and_jsonl_uploaded(monkeypatch):
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://r2.example.com")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "fakekey")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "fakesecret")
    monkeypatch.setenv("R2_BUCKET", "testbucket")
    monkeypatch.setenv("ARCHIVE_MAX_FETCH", "10")

    mock_client = MagicMock()
    mock_client.get_object.side_effect = Exception("NoSuchKey")

    monkeypatch.setattr(ar, "_make_r2_client", lambda *a, **kw: mock_client)

    inc = _make_inc("INC1")
    inc["apa"] = ar.format_apa(inc)

    rej_item = {
        "id": "REJ1",
        "url": "https://t13.cl/rej/1",
        "outlet": "T13",
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "title": "Accidente de tráfico",
        "description": "Descripción corta",
        "rejection_stage": "classifier_none",
        "first_seen": "2026-07-26T00:00:00+00:00",
        "apa": "",
    }

    monkeypatch.setattr(ar, "consolidate_incidents", lambda _: [inc])
    monkeypatch.setattr(ar, "consolidate_rejected", lambda _: [rej_item])

    # Mock fetch_article to succeed for the rejected item
    fetch_results = {
        rej_item["url"]: {
            "final_url": rej_item["url"],
            "http_status": 200,
            "extraction_ok": True,
            "text": "article text here",
            "lang": None,
            "decoded_from_gnews": False,
        },
        inc["url"]: {
            "final_url": inc["url"],
            "http_status": 200,
            "extraction_ok": True,
            "text": "incident text here",
            "lang": None,
            "decoded_from_gnews": False,
        },
    }

    monkeypatch.setattr(ar, "fetch_article", lambda url, **kw: fetch_results.get(url, {"extraction_ok": False, "text": "", "final_url": url, "http_status": None, "lang": None, "decoded_from_gnews": False}))

    result = ar.main()
    assert result == 0

    called_keys = set()
    for call in mock_client.put_object.call_args_list:
        k = call.kwargs.get("Key") or (call.args[1] if len(call.args) > 1 else None)
        if k:
            called_keys.add(k)

    assert any("rejected.jsonl" in k for k in called_keys), f"Missing rejected.jsonl in {called_keys}"

    # Check that article objects for REJ1 were uploaded
    rej_article_keys = [k for k in called_keys if "articles/REJ1" in k]
    assert rej_article_keys, f"Expected articles/REJ1.json, got {called_keys}"

    # Verify kind="rejected" in the article body
    for call in mock_client.put_object.call_args_list:
        k = call.kwargs.get("Key", "")
        if "articles/REJ1" in k:
            body = json.loads(call.kwargs["Body"].decode("utf-8"))
            assert body.get("kind") == "rejected", f"Expected kind='rejected', got {body.get('kind')}"


# ---------------------------------------------------------------------------
# 22. Fetch priority: with max_fetch=1, incident gets fetched before rejected
# ---------------------------------------------------------------------------

def test_fetch_priority_incidents_before_rejected(monkeypatch):
    """With max_fetch=1 and one incident + one rejected pending, only the incident is fetched."""
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://r2.example.com")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "fakekey")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "fakesecret")
    monkeypatch.setenv("R2_BUCKET", "testbucket")
    monkeypatch.setenv("ARCHIVE_MAX_FETCH", "1")

    mock_client = MagicMock()
    mock_client.get_object.side_effect = Exception("NoSuchKey")

    monkeypatch.setattr(ar, "_make_r2_client", lambda *a, **kw: mock_client)

    inc = _make_inc("INC_PRIO", url="https://emol.com/inc-prio")
    inc["apa"] = ar.format_apa(inc)

    rej_item = {
        "id": "REJ_PRIO",
        "url": "https://t13.cl/rej-prio",
        "outlet": "T13",
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "title": "Noticia rechazada",
        "description": "desc",
        "rejection_stage": "classifier_none",
        "first_seen": "2026-07-26T00:00:00+00:00",
        "apa": "",
    }

    monkeypatch.setattr(ar, "consolidate_incidents", lambda _: [inc])
    monkeypatch.setattr(ar, "consolidate_rejected", lambda _: [rej_item])

    fetched_urls = []

    def _mock_fetch(url, **kw):
        fetched_urls.append(url)
        return {
            "final_url": url, "http_status": 200, "extraction_ok": True,
            "text": "text", "lang": None, "decoded_from_gnews": False,
        }

    monkeypatch.setattr(ar, "fetch_article", _mock_fetch)

    result = ar.main()
    assert result == 0

    # Only one URL should have been fetched (cap=1), and it must be the incident
    assert len(fetched_urls) == 1, f"Expected 1 fetch, got {len(fetched_urls)}: {fetched_urls}"
    assert fetched_urls[0] == inc["url"], (
        f"Incident must be fetched first (priority), got {fetched_urls[0]!r}"
    )


# ---------------------------------------------------------------------------
# Security hardening regression tests (review 260726-gf7)
# ---------------------------------------------------------------------------

def test_csv_formula_injection_neutralized():
    """A headline starting with = / + / - / @ must be prefixed with ' in the CSV."""
    inc = _make_inc(inc_id="X", title_es="=HYPERLINK(\"http://evil\")", outlet="@cmd")
    inc["apa"] = "-2+3"
    out = ar.to_csv([inc]).decode("utf-8-sig")
    rows = out.splitlines()
    data = rows[1]
    assert "'=HYPERLINK" in data
    assert "'@cmd" in data
    assert "'-2+3" in data


def test_csv_safe_leaves_normal_values():
    assert ar._csv_safe("Robo en Santiago") == "Robo en Santiago"
    assert ar._csv_safe("13101") == "13101"
    assert ar._csv_safe(None) == ""


def test_rejected_colliding_with_incident_id_dropped(tmp_path, monkeypatch):
    """A rejected record sharing an incident id must be dropped (WR-04)."""
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://r2.example.com")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "s")
    monkeypatch.setenv("R2_BUCKET", "b")
    monkeypatch.setenv("ARCHIVE_MAX_FETCH", "0")

    inc = _make_inc(inc_id="DUP", url="https://outlet.cl/shared")
    monkeypatch.setattr(ar, "consolidate_incidents", lambda _: [inc])
    monkeypatch.setattr(ar, "consolidate_rejected",
                        lambda _: [{"id": "DUP", "url": "https://outlet.cl/shared",
                                    "outlet": "X", "date": "2026-07-26", "title": "t"}])

    mock_client = MagicMock()
    mock_client.get_object.side_effect = Exception("NoSuchKey")
    monkeypatch.setattr(ar, "_make_r2_client", lambda *a, **k: mock_client)

    result = ar.main()
    assert result == 0
    rejected_bodies = [c.kwargs["Body"] for c in mock_client.put_object.call_args_list
                       if c.kwargs.get("Key", "").endswith("rejected.jsonl")]
    assert rejected_bodies, "rejected.jsonl must be uploaded"
    assert rejected_bodies[0].decode("utf-8").strip() == "", "colliding rejected dropped"


def test_malformed_max_fetch_does_not_crash(tmp_path, monkeypatch):
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://r2.example.com")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "s")
    monkeypatch.setenv("R2_BUCKET", "b")
    monkeypatch.setenv("ARCHIVE_MAX_FETCH", "not-a-number")

    monkeypatch.setattr(ar, "consolidate_incidents", lambda _: [])
    monkeypatch.setattr(ar, "consolidate_rejected", lambda _: [])
    mock_client = MagicMock()
    mock_client.get_object.side_effect = Exception("NoSuchKey")
    monkeypatch.setattr(ar, "_make_r2_client", lambda *a, **k: mock_client)

    assert ar.main() == 0  # must not raise ValueError
