"""
pipeline/tests/test_fid03_audit.py

Phase 36-08 Task 1: offline tests of the FID-03 audit tool. No network: an
autouse guard makes requests.get/Session.get/Session.post and
classifier._request_completion raise; every router is a fake. Every test
works on a tmp copy of a small fixture data dir — never on data/.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests

from pipeline.experiments import fid03_audit as F  # type: ignore
from pipeline.news import classifier as C  # type: ignore
from pipeline.news.classifier import ClassifyResult, Outcome  # type: ignore
from pipeline.news.schema import ClassifierOutput  # type: ignore


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network call attempted in an offline test")

    monkeypatch.setattr(requests, "get", boom)
    monkeypatch.setattr(requests.Session, "get", boom)
    monkeypatch.setattr(requests.Session, "post", boom)
    monkeypatch.setattr(C, "_request_completion", boom)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _row(rid, *, title=None, description=None, first_seen="2026-09-15T10:00:00+00:00",
         date="2026-09-15", stage="classifier_none", url=None, outlet="BioBioChile"):
    return {
        "id": rid,
        "url": url or f"https://www.biobiochile.cl/noticias/{rid}.shtml",
        "outlet": outlet,
        "date": date,
        "title": title or f"Titular {rid}",
        "description": description or f"Descripcion {rid}",
        "rejection_stage": stage,
        "first_seen": first_seen,
    }


def _write_envelope(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"generated": "2026-09-25T00:00:00Z", "items": items}, ensure_ascii=False),
        encoding="utf-8",
    )


def make_data_dir(tmp_path: Path, rows: list[dict], month="2026-09.json") -> Path:
    d = tmp_path / "data"
    _write_envelope(d / "rejected" / month, rows)
    return d


def _output(**over):
    base = {
        "commune_name": "Las Condes", "region_hint": "Metropolitana",
        "family": "propiedad", "title_en": "Vehicle theft in Las Condes",
        "summary": "A car was stolen.", "confidence": 0.9,
    }
    base.update(over)
    return base


def cache_line(rid, outcome, *, output=None, error=None, provider="openrouter",
               model="deepseek/deepseek-v4.1-flash"):
    return {"id": rid, "outcome": outcome, "status_code": None, "error": error,
            "output": output, "provider": provider, "model": model, "served_by": None,
            "usage": None, "ts": "2026-09-25T00:00:00Z"}


def write_cache(path: Path, lines: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for line in lines:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")
    return path


class FakeRouter:
    def __init__(self, script=None, default=None, exhaust_after=None):
        self.script = script or {}
        self.default = default
        self.exhaust_after = exhaust_after
        self.calls: list[str] = []
        self.budget_s = 1200.0
        self.any_key_present = True
        self.key_env_names = ["OPENROUTER_API_KEY"]

    def classify(self, title, description, key=None):
        if self.exhaust_after is not None and len(self.calls) >= self.exhaust_after:
            return None
        self.calls.append(key)
        return self.script.get(key, self.default)

    def pop_redispatched(self):
        return []

    def preflight(self):
        return None


def result(outcome: Outcome, *, provider="openrouter", model="deepseek/deepseek-v4.1-flash",
           output=None, error=None, status=None, usage=None):
    out = ClassifierOutput.model_validate(output) if output is not None else None
    return ClassifyResult(outcome, out, provider, model, status_code=status, error=error,
                          usage=usage)


# ---------------------------------------------------------------------------
# --select
# ---------------------------------------------------------------------------

def test_select_window_boundary_and_dedup(tmp_path):
    as_of = F.B.parse_dt("2026-10-01T00:00:00Z")
    rows = [
        _row("a0000000000000001", first_seen="2026-09-17T00:00:00Z"),  # exactly as_of - 14d, included
        _row("a0000000000000002", first_seen="2026-10-01T00:00:00Z"),  # exactly as_of, excluded
        _row("a0000000000000003", first_seen="2026-09-16T23:59:59Z"),  # 1s before window, excluded
        _row("a0000000000000004", first_seen="2026-09-20T00:00:00Z"),  # inside window
    ]
    d = make_data_dir(tmp_path, rows)
    pool, stages, epochs, sib = F.select_pool(d, as_of, 14)
    ids = {r["id"] for r in pool}
    assert ids == {"a0000000000000001", "a0000000000000004"}
    assert sib == []


def test_select_excludes_ids_file(tmp_path):
    as_of = F.B.parse_dt("2026-10-01T00:00:00Z")
    rows = [_row("b0000000000000001", first_seen="2026-09-20T00:00:00Z"),
            _row("b0000000000000002", first_seen="2026-09-20T00:00:00Z")]
    d = make_data_dir(tmp_path, rows)
    pool, *_ = F.select_pool(d, as_of, 14, exclude_ids={"b0000000000000001"})
    assert [r["id"] for r in pool] == ["b0000000000000002"]


def test_select_dedups_by_id_first_wins(tmp_path):
    as_of = F.B.parse_dt("2026-10-01T00:00:00Z")
    row = _row("c0000000000000001", first_seen="2026-09-20T00:00:00Z")
    d = make_data_dir(tmp_path, [row], month="2026-08.json")
    _write_envelope(d / "rejected" / "2026-09.json", [dict(row, title="Different title")])
    pool, *_ = F.select_pool(d, as_of, 14)
    assert len(pool) == 1
    assert pool[0]["title"] == row["title"]  # first file (sorted) wins


def test_select_sibling_exclusion_and_epoch_split(tmp_path):
    as_of = F.B.parse_dt("2026-10-01T00:00:00Z")
    rows = [
        _row("d0000000000000001", title="Formalizan a imputado por robo en Temuco",
             first_seen="2026-09-20T00:00:00Z", stage="classifier_none"),
        _row("d0000000000000002", title="Gobierno anuncia nuevo plan de vivienda social",
             first_seen="2026-09-20T00:00:00Z", stage="low_confidence"),
        _row("d0000000000000003", title="Otro robo distinto en Concepcion",
             first_seen="2026-09-20T00:00:00Z", stage="commune_null"),
    ]
    d = make_data_dir(tmp_path, rows)
    siblings = ["Formalizan a imputado por robo en Temuco - La Tercera"]
    pool, stages, epochs, sib = F.select_pool(d, as_of, 14, exclude_siblings=siblings)
    ids = {r["id"] for r in pool}
    assert "d0000000000000001" not in ids
    assert ids == {"d0000000000000002", "d0000000000000003"}
    assert len(sib) == 1 and sib[0][0] == "d0000000000000001"
    assert sib[0][1] == siblings[0]
    assert sib[0][2] >= 0.60
    assert epochs == {"outage": 0, "live": 2}


def test_select_cli_writes_rows_and_prints_pool(tmp_path, capsys):
    rows = [_row("e0000000000000001", first_seen="2026-09-20T00:00:00Z")]
    d = make_data_dir(tmp_path, rows)
    out_rows = tmp_path / "scr" / "pool.json"
    code = F.main(["--select", "--as-of", "2026-10-01T00:00:00Z", "--window-days", "14",
                   "--data-dir", str(d), "--out-rows", str(out_rows)])
    assert code == 0
    written = json.loads(out_rows.read_text(encoding="utf-8"))
    assert [r["id"] for r in written] == ["e0000000000000001"]
    out = capsys.readouterr().out
    assert "pool=1" in out
    assert "pool_by_epoch: outage=1 live=0" in out


# ---------------------------------------------------------------------------
# --classify
# ---------------------------------------------------------------------------

def test_classify_refuses_cache_under_data_dir(tmp_path):
    d = tmp_path / "data"
    (d / "rejected").mkdir(parents=True)
    rows_path = tmp_path / "scr" / "rows.json"
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    rows_path.write_text("[]", encoding="utf-8")
    with pytest.raises(SystemExit):
        F.main(["--classify", "--data-dir", str(d), "--rows", str(rows_path),
                "--cache", str(d / "c.jsonl"), "--spend-cap", "1.0"])


def test_classify_uses_router_via_hook(tmp_path, monkeypatch):
    rid = "f0000000000000001"
    rows = [{"id": rid, "title": "Robo en Las Condes", "description": "desc"}]
    rows_path = tmp_path / "scr" / "rows.json"
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    rows_path.write_text(json.dumps(rows), encoding="utf-8")
    cache = tmp_path / "scr" / "c.jsonl"
    data_dir = tmp_path / "data"
    (data_dir / "rejected").mkdir(parents=True)

    router = FakeRouter({rid: result(Outcome.OK, output=_output())})
    monkeypatch.setattr(C, "build_router_from_env", lambda: router)

    code = F.main(
        ["--classify", "--data-dir", str(data_dir), "--rows", str(rows_path),
         "--cache", str(cache), "--spend-cap", "1.0"],
        env_files=[],
    )
    assert code == 0
    assert F.B.load_cache(cache)[rid]["outcome"] == "ok"
    assert router.calls == [rid]


# ---------------------------------------------------------------------------
# --sample
# ---------------------------------------------------------------------------

def _sample_fixture(tmp_path):
    rows = [
        {"id": "ok1", "title": "Robo con violencia en Las Condes", "description": "desc",
         "url": "https://www.biobiochile.cl/n/ok1.shtml", "outlet": "BioBioChile", "date": "2026-09-15"},
        {"id": "ok2", "title": "Asalto en Maipu", "description": "desc",
         "url": "https://www.emol.com/n/ok2.html", "outlet": "Emol", "date": "2026-09-15"},
        {"id": "unresolvable", "title": "Robo en comuna inexistente", "description": "desc",
         "url": "https://www.emol.com/n/u.html", "outlet": "Emol", "date": "2026-09-15"},
        {"id": "notcrime", "title": "Reunion municipal", "description": "desc",
         "url": "https://www.emol.com/n/nc.html", "outlet": "Emol", "date": "2026-09-15"},
    ]
    rows_path = tmp_path / "scr" / "rows.json"
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    rows_path.write_text(json.dumps(rows), encoding="utf-8")

    cache = write_cache(tmp_path / "scr" / "c.jsonl", [
        cache_line("ok1", "ok", output=_output(commune_name="Las Condes")),
        cache_line("ok2", "ok", output=_output(commune_name="Maipu", family="propiedad",
                                               title_en="Robbery in Maipu")),
        cache_line("unresolvable", "ok", output=_output(commune_name="Comuna Que No Existe")),
        cache_line("notcrime", "not_crime"),
    ])
    return rows_path, cache


def test_sample_would_publish_pool_and_exit5(tmp_path, capsys):
    rows_path, cache = _sample_fixture(tmp_path)
    data_dir = tmp_path / "data"
    (data_dir / "rejected").mkdir(parents=True)
    out_path = tmp_path / "scr" / "sample.json"
    code = F.main(["--sample", "2", "--seed", "3608", "--data-dir", str(data_dir),
                   "--rows", str(rows_path), "--cache", str(cache), "--out", str(out_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert "would_publish_pool=2" in out

    code5 = F.main(["--sample", "50", "--seed", "3608", "--data-dir", str(data_dir),
                    "--rows", str(rows_path), "--cache", str(cache),
                    "--out", str(tmp_path / "scr" / "s2.json")])
    assert code5 == F.EXIT_POOL_TOO_SMALL


def test_sample_deterministic_for_fixed_seed(tmp_path):
    rows_path, cache = _sample_fixture(tmp_path)
    data_dir = tmp_path / "data"
    (data_dir / "rejected").mkdir(parents=True)
    out1 = tmp_path / "scr" / "s1.json"
    out2 = tmp_path / "scr" / "s2.json"
    for out in (out1, out2):
        code = F.main(["--sample", "2", "--seed", "3608", "--data-dir", str(data_dir),
                       "--rows", str(rows_path), "--cache", str(cache), "--out", str(out)])
        assert code == 0
    assert json.loads(out1.read_text(encoding="utf-8")) == json.loads(out2.read_text(encoding="utf-8"))


def test_sample_writes_published_fields_never_title_es(tmp_path):
    rows_path, cache = _sample_fixture(tmp_path)
    data_dir = tmp_path / "data"
    (data_dir / "rejected").mkdir(parents=True)
    out_path = tmp_path / "scr" / "sample.json"
    F.main(["--sample", "2", "--seed", "3608", "--data-dir", str(data_dir),
            "--rows", str(rows_path), "--cache", str(cache), "--out", str(out_path)])
    sample = json.loads(out_path.read_text(encoding="utf-8"))
    ids = {r["id"] for r in sample}
    assert ids == {"ok1", "ok2"}
    for item in sample:
        assert set(item) == {
            "id", "url", "outlet", "title", "description", "predicted_family",
            "commune_name", "cut", "title_src", "title_en", "title_en_fallback",
        }


def test_sample_blind_out_decodes_google_with_session(tmp_path, capsys):
    rows = [
        {"id": "g1", "title": "Robo con violencia en Las Condes", "description": "desc",
         "url": "https://news.google.com/rss/articles/g1token", "outlet": "La Tercera",
         "date": "2026-09-15"},
        {"id": "g2fail", "title": "Asalto en Maipu", "description": "desc",
         "url": "https://news.google.com/rss/articles/g2token", "outlet": "Emol",
         "date": "2026-09-15"},
        {"id": "direct", "title": "Portonazo en Providencia", "description": "desc",
         "url": "https://www.emol.com/n/direct.html", "outlet": "Emol", "date": "2026-09-15"},
    ]
    rows_path = tmp_path / "scr" / "rows.json"
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    rows_path.write_text(json.dumps(rows), encoding="utf-8")
    cache = write_cache(tmp_path / "scr" / "c.jsonl", [
        cache_line("g1", "ok", output=_output(commune_name="Las Condes")),
        cache_line("g2fail", "ok", output=_output(commune_name="Maipu")),
        cache_line("direct", "ok", output=_output(commune_name="Providencia")),
    ])
    data_dir = tmp_path / "data"
    (data_dir / "rejected").mkdir(parents=True)
    out_path = tmp_path / "scr" / "sample.json"
    blind_path = tmp_path / "scr" / "blind.json"

    received_sessions = []

    def fake_decoder_factory():
        # Mirrors main()'s default decoder construction but records the session.
        pass

    # Patch decode_gnews_url used by cmd_sample's default decoder path.
    import pipeline.news.gnews_decoder as gnews_decoder

    def fake_decode(url, session=None, timeout=10):
        received_sessions.append(session)
        if "g1token" in url:
            return "https://www.latercera.com/publisher-article"
        return None  # g2token fails to decode

    import pytest as _pytest
    monkeypatch = _pytest.MonkeyPatch()
    monkeypatch.setattr(gnews_decoder, "decode_gnews_url", fake_decode)
    try:
        from pipeline.experiments import fid03_audit as F2

        class Args:
            pass

        args = Args()
        args.rows = rows_path
        args.cache = cache
        args.sample = 3  # request the whole pool so both google rows are sampled
        args.seed = 3608
        args.out = out_path
        args.blind_out = blind_path
        args.data_dir = data_dir

        code = F2.cmd_sample(args, sleep=lambda s: None)
        assert code == 0
    finally:
        monkeypatch.undo()

    assert received_sessions, "decode_gnews_url was never called"
    assert all(s is not None for s in received_sessions), "BF-03: session must be non-None"

    blind = json.loads(blind_path.read_text(encoding="utf-8"))
    by_id = {b["id"]: b for b in blind}
    assert by_id["g1"]["publisher_url"] == "https://www.latercera.com/publisher-article"
    assert by_id["g2fail"]["publisher_url"] is None
    assert by_id["direct"]["publisher_url"] == "https://www.emol.com/n/direct.html"
    for b in blind:
        assert set(b) == {"id", "title", "description", "url", "publisher_url", "outlet"}

    out = capsys.readouterr().out
    assert "publisher_url_decoded: 1/2" in out


# ---------------------------------------------------------------------------
# --score
# ---------------------------------------------------------------------------

def _verdict(rid, *, q1=True, family="propiedad", predicted="propiedad", basis="source"):
    return {"id": rid, "q1": q1, "family": family, "predicted_family": predicted, "basis": basis}


def test_score_pass_43_of_50_with_vida(tmp_path, capsys):
    # 33 plain agreements + 10 vida agreements = 43/50 agreement; vida 10/11 (>= ceil(0.85*11)=10).
    verdicts = (
        [_verdict(f"agree{i}") for i in range(33)]
        + [_verdict(f"vidaok{i}", family="vida", predicted="vida") for i in range(10)]
        + [_verdict("vidabad", family="propiedad", predicted="vida")]
        + [_verdict(f"dis{i}", q1=False) for i in range(6)]
    )
    assert len(verdicts) == 50
    verdicts_path = tmp_path / "scr" / "verdicts.json"
    verdicts_path.parent.mkdir(parents=True, exist_ok=True)
    verdicts_path.write_text(json.dumps(verdicts), encoding="utf-8")
    code = F.main(["--score", "--verdicts", str(verdicts_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert "agreement: 43/50" in out
    assert "vida_precision: 10/11" in out
    assert "**Decision**: PASS" in out


def test_score_fail_42_of_50(tmp_path, capsys):
    verdicts = (
        [_verdict(f"agree{i}") for i in range(42)]
        + [_verdict(f"dis{i}", q1=False) for i in range(8)]
    )
    verdicts_path = tmp_path / "scr" / "verdicts.json"
    verdicts_path.parent.mkdir(parents=True, exist_ok=True)
    verdicts_path.write_text(json.dumps(verdicts), encoding="utf-8")
    F.main(["--score", "--verdicts", str(verdicts_path)])
    out = capsys.readouterr().out
    assert "agreement: 42/50" in out
    assert "**Decision**: FAILED" in out


def test_score_fail_vida_8_of_10(tmp_path, capsys):
    verdicts = (
        [_verdict(f"agree{i}") for i in range(33)]
        + [_verdict(f"vidaok{i}", family="vida", predicted="vida") for i in range(8)]
        + [_verdict(f"vidabad{i}", family="propiedad", predicted="vida") for i in range(2)]
        + [_verdict(f"dis{i}", q1=False) for i in range(7)]
    )
    assert len(verdicts) == 50
    verdicts_path = tmp_path / "scr" / "verdicts.json"
    verdicts_path.parent.mkdir(parents=True, exist_ok=True)
    verdicts_path.write_text(json.dumps(verdicts), encoding="utf-8")
    F.main(["--score", "--verdicts", str(verdicts_path)])
    out = capsys.readouterr().out
    assert "agreement: 41/50" in out
    assert "vida_precision: 8/10" in out
    assert "**Decision**: FAILED" in out


def test_score_negative_control_min_agree(monkeypatch, tmp_path, capsys):
    """Negative control (plan verify): FID03_MIN_AGREE = 42 must make the
    42/50 fixture PASS, proving the gate is load-bearing."""
    monkeypatch.setattr(F, "FID03_MIN_AGREE", 42)
    verdicts = (
        [_verdict(f"agree{i}") for i in range(42)]
        + [_verdict(f"dis{i}", q1=False) for i in range(8)]
    )
    verdicts_path = tmp_path / "scr" / "verdicts.json"
    verdicts_path.parent.mkdir(parents=True, exist_ok=True)
    verdicts_path.write_text(json.dumps(verdicts), encoding="utf-8")
    F.main(["--score", "--verdicts", str(verdicts_path)])
    out = capsys.readouterr().out
    assert "**Decision**: PASS" in out


def test_score_basis_breakdown(tmp_path, capsys):
    verdicts = (
        [_verdict(f"s{i}", basis="source") for i in range(30)]
        + [_verdict(f"h{i}", basis="headline_only") for i in range(15)]
        + [_verdict(f"hd{i}", basis="headline_only", q1=False) for i in range(5)]
    )
    assert len(verdicts) == 50
    verdicts_path = tmp_path / "scr" / "verdicts.json"
    verdicts_path.parent.mkdir(parents=True, exist_ok=True)
    verdicts_path.write_text(json.dumps(verdicts), encoding="utf-8")
    F.main(["--score", "--verdicts", str(verdicts_path)])
    out = capsys.readouterr().out
    assert "agreement_by_basis: headline_only=15/20 source=30/30" in out
