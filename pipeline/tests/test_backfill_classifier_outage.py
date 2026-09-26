"""
pipeline/tests/test_backfill_classifier_outage.py

Phase 34-05 Task 1 (NREC-09): offline tests of the classifier-outage backfill tool.
NO network: an autouse guard makes requests.get and classifier._request_completion
raise; every router is a fake (or a real ProviderRouter over fake completions).
Every test works on a tmp copy of a small fixture data dir — never on data/.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from pipeline import backfill_classifier_outage as B  # type: ignore
from pipeline.news import classifier as C  # type: ignore
from pipeline.news.classifier import ClassifyResult, Outcome  # type: ignore
from pipeline.news.schema import ClassifierOutput  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[2]
TODAY = dt.date(2026, 9, 23)
SINCE = "2026-09-04T20:13:49Z"


# ---------------------------------------------------------------------------
# Network guard
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network call attempted in an offline test")

    monkeypatch.setattr(requests, "get", boom)
    monkeypatch.setattr(C, "_request_completion", boom)


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

def _row(rid, *, date="2026-09-10", first_seen="2026-09-10T10:00:00.000000+00:00",
         stage="classifier_none", url=None, title=None, description=None, outlet="BioBioChile"):
    return {
        "id": rid,
        "url": url or f"https://www.biobiochile.cl/noticias/{rid}.shtml",
        "outlet": outlet,
        "date": date,
        "title": title or f"Titular {rid}",
        "description": description or f"Descripción {rid}",
        "rejection_stage": stage,
        "first_seen": first_seen,
    }


EXISTING_INCIDENT = {
    "id": "exist000000000001",
    "cut": "13114",
    "lat": -33.41,
    "lng": -70.56,
    "title_es": "Robo con violencia en Las Condes deja un herido",
    "title_en": "Violent robbery in Las Condes leaves one injured",
    "date": "2026-09-10",
    "outlet": "Emol",
    "url": "https://www.emol.com/noticias/exist1.html",
    "family": "robos_violentos",
    "slug": "las-condes",
}


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))


def make_data_dir(tmp_path: Path, sept_rows, oct_rows=None, *, lni="2026-09-04T15:40:00Z",
                  archive=None) -> Path:
    d = tmp_path / "data" / "incidents"
    current = {"generated": "2026-09-22T20:00:00Z", "window_days": 30,
               "incidents": [dict(EXISTING_INCIDENT)]}
    if lni is not None:
        current["last_new_incident_at"] = lni
    _write(d / "current.json", current)
    _write(d / "seen.json", {"https://x/1": "2026-09-10"})
    _write(d / "archive" / "2026-08.json",
           {"generated": "2026-09-01T00:00:00Z", "window_days": 30, "incidents": archive or []})
    _write(d / "rejected" / "2026-08.json",
           {"generated": "2026-08-31T00:00:00+00:00",
            "items": [_row("aug0000000000001", date="2026-08-30",
                           first_seen="2026-08-30T10:00:00+00:00")]})
    _write(d / "rejected" / "2026-09.json",
           {"generated": "2026-09-22T20:49:36.848245+00:00", "items": sept_rows})
    if oct_rows is not None:
        _write(d / "rejected" / "2026-10.json",
               {"generated": "2026-10-01T00:00:00+00:00", "items": oct_rows})
    return d


def snapshot(root: Path) -> dict:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def _output(**over):
    base = {
        "commune_name": "Las Condes", "region_hint": "Metropolitana",
        "family": "propiedad", "title_es": "Robo de vehículo en Las Condes",
        "title_en": "Vehicle theft in Las Condes", "summary": "A car was stolen.",
        "confidence": 0.9,
    }
    base.update(over)
    return base


def result(outcome: Outcome, *, provider="openrouter", model="deepseek/deepseek-v4.1-flash",
           output=None, error=None, status=None, usage=None):
    out = ClassifierOutput.model_validate(output) if output is not None else None
    return ClassifyResult(outcome, out, provider, model, status_code=status, error=error,
                          usage=usage)


def cache_line(rid, outcome, *, output=None, error=None, provider="openrouter",
               model="deepseek/deepseek-v4.1-flash"):
    return {"id": rid, "outcome": outcome, "status_code": None, "error": error,
            "output": output, "provider": provider, "model": model, "served_by": None,
            "usage": None, "ts": "2026-09-23T00:00:00Z"}


def write_cache(path: Path, lines) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        for line in lines:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")
    return path


class FakeRouter:
    """Duck-typed ProviderRouter: script maps id → ClassifyResult (or None)."""

    def __init__(self, script=None, default=None, exhaust_after=None, redispatch=None):
        self.script = script or {}
        self.default = default
        self.exhaust_after = exhaust_after
        self.redispatch = redispatch or {}
        self.calls: list[str] = []
        self.budget_s = 1200.0
        self._pending: list = []

    def classify(self, title, description, key=None):
        if self.exhaust_after is not None and len(self.calls) >= self.exhaust_after:
            return None
        self.calls.append(key)
        if key in self.redispatch:
            self._pending.extend(self.redispatch[key])
        res = self.script.get(key, self.default)
        return res

    def pop_redispatched(self):
        out, self._pending = self._pending, []
        return out


def meter(tmp_path, cap=100.0, **kw):
    return B.SpendMeter(cap, tmp_path / "scr" / "spend.json", **kw)


# ---------------------------------------------------------------------------
# Selection (G-06)
# ---------------------------------------------------------------------------

def test_selection_parses_datetimes_and_stage(tmp_path):
    rows = [
        _row("a000000000000001", first_seen="2026-09-04T20:13:49.524591+00:00"),
        _row("a000000000000002", first_seen="2026-09-04T20:13:48.999999+00:00"),
        _row("a000000000000003", stage="commune_null"),
        _row("a000000000000004", stage="low_confidence"),
        _row("a000000000000005", first_seen="2026-09-04T20:13:49Z"),
    ]
    d = make_data_dir(tmp_path, rows)
    ids = {r["id"] for r in B.select_outage_rows(d, SINCE)}
    assert ids == {"a000000000000001", "a000000000000005"}
    # A string compare would have dropped the .524591 row ("." < "Z").
    assert "2026-09-04T20:13:49.524591+00:00" < SINCE


def test_selection_dedups_across_month_files_and_oct_optional(tmp_path):
    shared = _row("b000000000000001")
    d = make_data_dir(tmp_path, [shared, _row("b000000000000002")],
                      oct_rows=[dict(shared), _row("b000000000000003", date="2026-10-01",
                                                   first_seen="2026-10-01T01:00:00+00:00")])
    ids = [r["id"] for r in B.select_outage_rows(d, SINCE)]
    assert sorted(ids) == ["b000000000000001", "b000000000000002", "b000000000000003"]
    # Without the October file
    d2 = make_data_dir(tmp_path / "x", [shared])
    assert [r["id"] for r in B.select_outage_rows(d2, SINCE)] == ["b000000000000001"]


def test_selection_order(tmp_path):
    rows = [_row("c1", date="2026-09-10"), _row("c2", date="2021-09-16"),
            _row("c3", date="2026-09-23"), _row("c4", date="2026-09-05")]
    d = make_data_dir(tmp_path, rows)
    dates = [r["date"] for r in B.select_outage_rows(d, SINCE)]
    assert dates == ["2026-09-05", "2026-09-10", "2026-09-23", "2021-09-16"]


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------

def test_dry_run_zero_writes(tmp_path, capsys):
    rows = [_row("d000000000000001", date="2026-08-01"),
            _row("d000000000000002", first_seen="2026-09-22T20:49:36.848245+00:00"),
            _row("d000000000000003", first_seen="2026-09-23T01:00:00+00:00"),
            _row("d000000000000004", stage="resolver_fail")]
    d = make_data_dir(tmp_path, rows)
    cache = tmp_path / "scr" / "bf-cache.jsonl"
    before = snapshot(d)
    code = B.main(["--dry-run", "--data-dir", str(d), "--cache", str(cache), "--today", "2026-09-23"])
    assert code == 0
    assert snapshot(d) == before
    assert not cache.exists()
    out = capsys.readouterr().out
    assert "selected=3" in out
    assert 'by_file={"2026-09.json": 3}' in out
    assert "frozen_subset=2" in out
    assert "would_archive=1" in out
    assert "already_cached=0" in out
    assert "planned_calls=3" in out


def test_dry_run_counts_already_cached(tmp_path, capsys):
    rows = [_row("e000000000000001"), _row("e000000000000002")]
    d = make_data_dir(tmp_path, rows)
    cache = write_cache(tmp_path / "scr" / "c.jsonl", [
        cache_line("e000000000000001", "ok", output=_output()),
        cache_line("e000000000000002", "api_error", error="APIConnectionError"),
    ])
    B.main(["--dry-run", "--data-dir", str(d), "--cache", str(cache)])
    out = capsys.readouterr().out
    assert "already_cached=1" in out and "planned_calls=1" in out


def test_paths_inside_data_dir_refused(tmp_path):
    d = make_data_dir(tmp_path, [_row("f000000000000001")])
    with pytest.raises(SystemExit):
        B.main(["--dry-run", "--data-dir", str(d), "--cache", str(d / "c.jsonl")])


# ---------------------------------------------------------------------------
# Classify phase
# ---------------------------------------------------------------------------

def _ids(n, prefix="g"):
    return [f"{prefix}{i:015d}" for i in range(n)]


def test_classify_writes_cache_only_and_retries_api_errors(tmp_path):
    ids = _ids(4)
    d = make_data_dir(tmp_path, [_row(i) for i in ids])
    before = snapshot(d)
    cache = tmp_path / "scr" / "c.jsonl"
    router = FakeRouter({
        ids[0]: result(Outcome.OK, output=_output()),
        ids[1]: result(Outcome.NOT_CRIME, output=_output(confidence=0.1)),
        ids[2]: result(Outcome.PARSE_ERROR),
        ids[3]: result(Outcome.API_ERROR, error="RateLimitError", status=429),
    })
    rows = B.select_outage_rows(d, SINCE)
    assert B.run_classify(rows, cache, router, meter(tmp_path)) == 0
    assert snapshot(d) == before
    lines = cache.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 4
    assert {json.loads(x)["outcome"] for x in lines} == {"ok", "not_crime", "parse_error", "api_error"}

    router2 = FakeRouter(default=result(Outcome.OK, output=_output()))
    assert B.run_classify(rows, cache, router2, meter(tmp_path)) == 0
    assert router2.calls == [ids[3]]
    assert B.load_cache(cache)[ids[3]]["outcome"] == "ok"


@pytest.mark.parametrize("err", ["empty_content", "finish_length"])
def test_g09_transient_errors_are_retried_and_untouched(tmp_path, err):
    rid = "h000000000000001"
    d = make_data_dir(tmp_path, [_row(rid)])
    cache = tmp_path / "scr" / "c.jsonl"
    rows = B.select_outage_rows(d, SINCE)
    B.run_classify(rows, cache, FakeRouter(default=result(Outcome.API_ERROR, error=err)),
                   meter(tmp_path))
    before = json.loads((d / "rejected" / "2026-09.json").read_text("utf-8"))
    code, rep = B.run_apply(d, cache, since=B.parse_dt(SINCE), exclude_ids=set(),
                            withhold_ids=set(), today=TODAY, now=dt.datetime.now(dt.timezone.utc))
    assert code == 0
    assert rep["api_error_remaining"] == 1 and rep["api_error_breakdown"][err] == 1
    after = json.loads((d / "rejected" / "2026-09.json").read_text("utf-8"))
    assert after == before
    r2 = FakeRouter(default=result(Outcome.OK, output=_output()))
    B.run_classify(rows, cache, r2, meter(tmp_path))
    assert r2.calls == [rid]


def test_exhausted_router_exits_4_and_resumes(tmp_path):
    ids = _ids(5, "i")
    d = make_data_dir(tmp_path, [_row(i) for i in ids])
    cache = tmp_path / "scr" / "c.jsonl"
    rows = B.select_outage_rows(d, SINCE)
    r = FakeRouter(default=result(Outcome.OK, output=_output()), exhaust_after=2)
    assert B.run_classify(rows, cache, r, meter(tmp_path)) == B.EXIT_EXHAUSTED
    assert len(B.load_cache(cache)) == 2
    r2 = FakeRouter(default=result(Outcome.OK, output=_output()))
    assert B.run_classify(rows, cache, r2, meter(tmp_path)) == 0
    assert len(r2.calls) == 3
    assert len(B.load_cache(cache)) == 5


def test_budget_is_unbounded_with_real_router(tmp_path, monkeypatch):
    """BF-04: a fake clock advancing 10,000 s per call never stops classification."""
    ids = _ids(4, "j")
    d = make_data_dir(tmp_path, [_row(i) for i in ids])
    ok_resp = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(_output())),
                                 finish_reason="stop")],
        model="m", usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20,
                                         completion_tokens_details=None))
    monkeypatch.setattr(C, "_request_completion", lambda *a, **k: ok_resp)
    t = {"now": 0.0}

    def clock():
        t["now"] += 10_000.0
        return t["now"]

    spec = C.ProviderSpec("openrouter", "m", lambda: None, None, True, "OPENROUTER_API_KEY")
    router = C.ProviderRouter(spec, None, clock=clock, budget_s=1200)
    cache = tmp_path / "scr" / "c.jsonl"
    code = B.run_classify(B.select_outage_rows(d, SINCE), cache, router, meter(tmp_path))
    assert code == 0
    assert router.budget_s == float("inf")
    assert len(B.load_cache(cache)) == 4
    assert all(v["outcome"] == "ok" for v in B.load_cache(cache).values())


def test_redispatch_lines_supersede_api_errors(tmp_path):
    """NB-06: re-dispatched results are written, last line per key = ok."""
    ids = _ids(6, "k")
    d = make_data_dir(tmp_path, [_row(i, date="2026-09-06") for i in ids])
    rows = B.select_outage_rows(d, SINCE)
    order = [r["id"] for r in rows]
    streak = order[:5]
    ok = result(Outcome.OK, provider="deepseek", model="deepseek-v4-flash", output=_output(),
                usage={"prompt_tokens": 3700, "completion_tokens": 150})
    script = {k: result(Outcome.API_ERROR, error="InternalServerError", status=503) for k in streak}
    script[order[5]] = ok
    router = FakeRouter(script, redispatch={streak[-1]: [(k, ok) for k in streak]})
    cache = tmp_path / "scr" / "c.jsonl"
    assert B.run_classify(rows, cache, router, meter(tmp_path)) == 0
    c = B.load_cache(cache)
    assert all(c[k]["outcome"] == "ok" for k in order)
    code, rep = B.run_apply(d, cache, since=B.parse_dt(SINCE), exclude_ids=set(),
                            withhold_ids=set(), today=TODAY, now=dt.datetime.now(dt.timezone.utc))
    assert code == 0 and rep["api_error_remaining"] == 0


def test_spend_cap_exit_3_then_partial_apply(tmp_path):
    ids = _ids(10, "l")
    d = make_data_dir(tmp_path, [_row(i, date="2026-09-06") for i in ids])
    rows = B.select_outage_rows(d, SINCE)
    usage = {"prompt_tokens": 4000, "completion_tokens": 200}
    # DeepSeek at peak: 4000*0.30e-6 + 200*1.20e-6 = 0.00144 per call
    ok = result(Outcome.OK, provider="deepseek", model="deepseek-v4-flash",
                output=_output(), usage=usage)
    m = B.SpendMeter(0.01, tmp_path / "scr" / "spend.json", next_call_ceiling=0.00144)
    cache = tmp_path / "scr" / "c.jsonl"
    code = B.run_classify(rows, cache, FakeRouter(default=ok), m)
    assert code == B.EXIT_CAP
    ledger = json.loads((tmp_path / "scr" / "spend.json").read_text("utf-8"))
    assert ledger["total_usd"] <= 0.01
    assert ledger["deepseek_estimate_usd"] == pytest.approx(0.00144 * ledger["calls"], abs=1e-6)
    n_cached = len(B.load_cache(cache))
    assert 0 < n_cached < 10
    code, rep = B.run_apply(d, cache, since=B.parse_dt(SINCE), exclude_ids=set(),
                            withhold_ids=set(), today=TODAY, now=dt.datetime.now(dt.timezone.utc),
                            spend_ledger=tmp_path / "scr" / "spend.json")
    assert code == 0
    assert rep["not_attempted"] == 10 - n_cached
    assert rep["spend_usd"] == ledger["total_usd"]


def test_spend_meter_uses_measured_usage_delta(tmp_path):
    values = iter([10.0, 10.25])

    def get(url, headers=None, timeout=None):
        assert url == B.OPENROUTER_KEY_URL and headers["Authorization"] == "Bearer k"
        return SimpleNamespace(status_code=200, json=lambda: {"data": {"usage": next(values)}})

    m = B.SpendMeter(5.0, None, api_key="k", http_get=get, checkpoint_every=2)
    m.start()
    r = result(Outcome.OK, output=_output(), usage={"prompt_tokens": 1, "completion_tokens": 1,
                                                     "cost": 0.001})
    m.charge(r)
    assert m.total == pytest.approx(0.001)
    m.charge(r)  # checkpoint → measured 0.25 replaces the estimates
    assert m.total == pytest.approx(0.25)
    assert m.measured_checkpoints == 1


def test_spend_meter_falls_back_to_catalog_max_without_cost(tmp_path):
    m = B.SpendMeter(5.0, None)
    r = result(Outcome.OK, output=_output(), usage={"prompt_tokens": 1_000_000,
                                                     "completion_tokens": 0})
    assert m.estimate(r) == pytest.approx(B.OPENROUTER_MAX_IN)


def test_r12_dotenv_loaded_before_classifier_import(tmp_path):
    d = make_data_dir(tmp_path, [_row("m000000000000001")])
    env_file = tmp_path / "dot.env"
    env_file.write_text("OPENROUTER_API_KEY=k1\n", encoding="utf-8")
    cache = tmp_path / "scr" / "c.jsonl"
    code = (
        "import sys, requests\n"
        "def boom(*a, **k): raise RuntimeError('network blocked')\n"
        "requests.get = boom\n"
        "import pipeline.backfill_classifier_outage as b\n"
        "assert 'pipeline.news.classifier' not in sys.modules, 'eager classifier import'\n"
        "def hook(router):\n"
        "    import pipeline.news.classifier as c\n"
        "    print(router.primary.api_key, router.primary.client_getter().api_key, c.client.api_key)\n"
        "    raise SystemExit(0)\n"
        f"b.main(['--classify', '--data-dir', r'{d}', '--cache', r'{cache}', '--spend-cap', '1'],\n"
        f"       env_files=[__import__('pathlib').Path(r'{env_file}')], router_hook=hook)\n"
        "raise SystemExit(9)\n"
    )
    env = {k: v for k, v in os.environ.items()
           if k.upper() in ("SYSTEMROOT", "PATH", "TEMP", "TMP", "WINDIR", "HOME", "USERPROFILE")}
    env["PYTHONIOENCODING"] = "utf-8"
    out = subprocess.run([sys.executable, "-c", code], cwd=str(REPO_ROOT), env=env,
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip().splitlines()[-1] == "k1 k1 k1"
    assert not cache.exists()


# ---------------------------------------------------------------------------
# Apply phase
# ---------------------------------------------------------------------------

def _apply(d, cache, **kw):
    kw.setdefault("exclude_ids", set())
    kw.setdefault("withhold_ids", set())
    return B.run_apply(d, cache, since=B.parse_dt(SINCE), today=TODAY,
                       now=dt.datetime(2026, 9, 23, 12, 0, tzinfo=dt.timezone.utc), **kw)


@pytest.fixture
def apply_case(tmp_path):
    rows = [
        # FID-01 36-04: the stored headline is the row title minus " - <outlet>".
        _row("n_ok_in_window01", date="2026-09-12", title="Asalto en Las Condes - BioBioChile"),
        _row("n_ok_archived001", date="2026-08-01"),
        _row("n_not_crime00001"),
        _row("n_parse_error001"),
        _row("n_commune_null01"),
        _row("n_resolver_fail1"),
        _row("n_centroid_fail1"),
        _row("n_url_rejected01", url="ftp://bad.example/x"),
        _row("n_dedup_dup00001", date="2026-09-10",
             title="Robo con violencia en Las Condes deja a un herido"),
        _row("n_editorial00001", title="La comuna más peligrosa de Chile"),
        _row("n_api_error00001"),
        _row("n_uncached000001"),
        _row("n_excluded000001"),
        _row("n_withheld000001"),
        _row("n_other_stage001", stage="commune_null"),
    ]
    d = make_data_dir(tmp_path, rows)
    cache = write_cache(tmp_path / "scr" / "c.jsonl", [
        cache_line("n_ok_in_window01", "ok", output=_output(family="robos_violentos",
                                                            title_es="Asalto en Las Condes")),
        cache_line("n_ok_archived001", "ok", output=_output(commune_name="Temuco",
                                                            region_hint="Araucanía")),
        cache_line("n_not_crime00001", "not_crime", output=_output(confidence=0.1)),
        cache_line("n_parse_error001", "parse_error"),
        cache_line("n_commune_null01", "ok", output=_output(commune_name=None)),
        cache_line("n_resolver_fail1", "ok", output=_output(commune_name="Gotham")),
        cache_line("n_centroid_fail1", "ok", output=_output(commune_name="Providencia")),
        cache_line("n_url_rejected01", "ok", output=_output()),
        cache_line("n_dedup_dup00001", "ok", output=_output(
            family="robos_violentos",
            title_es="Robo con violencia en Las Condes deja a un herido")),
        cache_line("n_api_error00001", "api_error", error="APIConnectionError"),
        cache_line("n_excluded000001", "ok", output=_output()),
        cache_line("n_withheld000001", "ok", output=_output()),
        cache_line("n_editorial00001", "ok", output=_output()),
    ])
    withhold = tmp_path / "scr" / "withhold.txt"
    withhold.write_text("# G-11\nn_withheld000001\n", encoding="utf-8")
    return SimpleNamespace(d=d, cache=cache, withhold=withhold, rows={r["id"]: r for r in rows})


def _patch_centroid_none_for(monkeypatch, cut_to_fail):
    from pipeline.news import centroids
    real = centroids.get_centroid
    monkeypatch.setattr(centroids, "get_centroid",
                        lambda cut: None if cut == cut_to_fail else real(cut))


def _providencia_cut():
    from pipeline.news.resolver import resolve_cut
    return resolve_cut("Providencia")[0]


def test_apply_full_split(apply_case, monkeypatch):
    _patch_centroid_none_for(monkeypatch, _providencia_cut())
    d = apply_case.d
    seen_before = (d / "seen.json").read_bytes()
    lni_before = json.loads((d / "current.json").read_text("utf-8"))["last_new_incident_at"]
    code, rep = _apply(d, apply_case.cache, exclude_ids={"n_excluded000001"},
                       withhold_ids=B._read_ids_file(apply_case.withhold))
    assert code == 0, rep

    cur = json.loads((d / "current.json").read_text("utf-8"))
    cur_ids = {i["id"] for i in cur["incidents"]}
    inc = next(i for i in cur["incidents"]
               if i["url"] == apply_case.rows["n_ok_in_window01"]["url"])
    row = apply_case.rows["n_ok_in_window01"]
    assert inc["date"] == row["date"] and inc["outlet"] == row["outlet"]
    # FID-01 36-04: title_es == title_src (outlet headline), not the classifier's title_es
    assert inc["title_es"] == "Asalto en Las Condes" and inc["family"] == "robos_violentos"
    assert inc["title_src"] == "Asalto en Las Condes"
    assert inc["title_en"] == "Vehicle theft in Las Condes"
    # G-07(a) / R-02
    assert cur["last_new_incident_at"] == lni_before
    assert rep["last_new_incident_at_before"] == rep["last_new_incident_at_after"] == lni_before
    # archived
    arch = json.loads((d / "archive" / "2026-08.json").read_text("utf-8"))
    assert any(i["url"] == apply_case.rows["n_ok_archived001"]["url"] for i in arch["incidents"])
    assert rep["accepted_in_window"] == 1 and rep["accepted_archived"] == 1
    # dedup against the EXISTING incident
    assert len(cur_ids) == 2

    items = {r["id"]: r for r in json.loads((d / "rejected" / "2026-09.json").read_text("utf-8"))["items"]}
    assert "n_ok_in_window01" not in items and "n_ok_archived001" not in items
    expect = {
        "n_not_crime00001": "low_confidence", "n_parse_error001": "parse_error",
        "n_commune_null01": "commune_null", "n_resolver_fail1": "resolver_fail",
        "n_centroid_fail1": "centroid_fail", "n_url_rejected01": "url_rejected",
        "n_dedup_dup00001": "dedup_duplicate", "n_excluded000001": "manual_exclusion",
        "n_editorial00001": "editorial_filter",
    }
    for rid, stage in expect.items():
        assert items[rid]["rejection_stage"] == stage, rid
        assert items[rid]["reclassified_at"] == "2026-09-23T12:00:00Z"
        assert list(items[rid])[:8] == list(apply_case.rows[rid])  # key order preserved
    assert items["n_excluded000001"]["reclassified_model"] == "openrouter:deepseek/deepseek-v4.1-flash"
    for rid in ("n_api_error00001", "n_uncached000001", "n_withheld000001", "n_other_stage001"):
        assert items[rid] == apply_case.rows[rid], rid
    assert not any(i["url"] == apply_case.rows["n_withheld000001"]["url"] for i in cur["incidents"])

    assert rep["by_stage"] == {s: 1 for s in expect.values()}
    assert rep["api_error_remaining"] == 1 and rep["not_attempted"] == 1
    assert rep["withheld"] == 1 and rep["excluded"] == 1
    assert rep["fidelity"] == {"title_en_fallbacks": 0, "editorial_filtered": 1}
    assert rep["selected"] == 14  # +n_editorial00001 (36-04)
    assert (d / "seen.json").read_bytes() == seen_before
    # line endings preserved (LF fixtures stay LF even on Windows)
    for p in d.rglob("*.json"):
        assert b"\r\n" not in p.read_bytes(), p
    # August file (outside the since month) untouched
    assert json.loads((d / "rejected" / "2026-08.json").read_text("utf-8"))["items"][0][
        "rejection_stage"] == "classifier_none"


def test_apply_is_idempotent(apply_case, monkeypatch):
    _patch_centroid_none_for(monkeypatch, _providencia_cut())
    kw = dict(exclude_ids={"n_excluded000001"}, withhold_ids={"n_withheld000001"})
    assert _apply(apply_case.d, apply_case.cache, **kw)[0] == 0
    first = snapshot(apply_case.d)
    code, rep = _apply(apply_case.d, apply_case.cache, **kw)
    assert code == 0
    assert snapshot(apply_case.d) == first
    assert rep["accepted_in_window"] == 0 and rep["by_stage"] == {}


def test_apply_lni_absent_stays_absent(tmp_path):
    d = make_data_dir(tmp_path, [_row("o000000000000001", date="2026-09-12")], lni=None)
    cache = write_cache(tmp_path / "scr" / "c.jsonl",
                        [cache_line("o000000000000001", "ok", output=_output())])
    code, rep = _apply(d, cache)
    assert code == 0 and rep["accepted_in_window"] == 1
    assert "last_new_incident_at" not in json.loads((d / "current.json").read_text("utf-8"))
    assert rep["last_new_incident_at_after"] is None


def test_apply_recovers_already_present_id(tmp_path):
    row = _row("p000000000000001", date="2026-09-12")
    d = make_data_dir(tmp_path, [row])
    from pipeline.news.store import make_id
    cur = json.loads((d / "current.json").read_text("utf-8"))
    cur["incidents"].append({**EXISTING_INCIDENT, "id": make_id(row["url"]), "url": row["url"],
                             "title_es": "Otro", "date": "2026-09-12"})
    _write(d / "current.json", cur)
    cur_bytes = (d / "current.json").read_bytes()
    cache = write_cache(tmp_path / "scr" / "c.jsonl",
                        [cache_line(row["id"], "ok", output=_output())])
    code, rep = _apply(d, cache)
    assert code == 0 and rep["already_present"] == 1 and rep["accepted_in_window"] == 0
    assert (d / "current.json").read_bytes() == cur_bytes
    items = json.loads((d / "rejected" / "2026-09.json").read_text("utf-8"))["items"]
    assert row["id"] not in {i["id"] for i in items}


def test_apply_cli_writes_report(apply_case, monkeypatch, tmp_path, capsys):
    _patch_centroid_none_for(monkeypatch, _providencia_cut())
    report = tmp_path / "scr" / "report.json"
    code = B.main(["--apply", "--data-dir", str(apply_case.d), "--cache", str(apply_case.cache),
                   "--exclude-ids", "n_excluded000001", "--withhold-ids", str(apply_case.withhold),
                   "--report", str(report), "--today", "2026-09-23"])
    assert code == 0
    rep = json.loads(report.read_text("utf-8"))
    for key in ("selected", "frozen_subset", "frozen_subset_resolved", "accepted_in_window",
                "accepted_archived", "by_stage", "api_error_remaining", "api_error_breakdown",
                "not_attempted", "withheld", "excluded", "spend_usd", "window_cutoff",
                "last_new_incident_at_before", "last_new_incident_at_after"):
        assert key in rep, key
    assert rep["window_cutoff"] == "2026-08-24"


def test_apply_kinship_guard_falls_back_to_title_src(tmp_path):
    # FID-07 / V-06: a wrong-kinship title_en is replaced by the verbatim headline.
    row = _row("k000000000000001", date="2026-09-12",
               title="Detienen a yerno de Rosamel Fierro - BioBioChile")
    d = make_data_dir(tmp_path, [row])
    cache = write_cache(tmp_path / "scr" / "c.jsonl", [cache_line(row["id"], "ok", output=_output(
        title_es="Detienen a suegro", title_en="Grandfather of Rosamel Fierro arrested"))])
    code, rep = _apply(d, cache)
    assert code == 0 and rep["accepted_in_window"] == 1
    inc = next(i for i in json.loads((d / "current.json").read_text("utf-8"))["incidents"]
               if i["url"] == row["url"])
    assert inc["title_src"] == inc["title_es"] == "Detienen a yerno de Rosamel Fierro"
    assert inc["title_en"] == "Detienen a yerno de Rosamel Fierro"
    assert rep["fidelity"] == {"title_en_fallbacks": 1, "editorial_filtered": 0}


def test_apply_blank_title_rejected_empty_title(tmp_path):
    # Pre-push F-1: a whitespace-only title would make build_incident raise and
    # abort the whole apply; the row is rejected on its own, the rest proceed.
    blank = _row("e000000000000001", date="2026-09-12", title="   ")
    ok = _row("e000000000000002", date="2026-09-12", title="Asalto en Las Condes - BioBioChile")
    d = make_data_dir(tmp_path, [blank, ok])
    cache = write_cache(tmp_path / "scr" / "c.jsonl",
                        [cache_line(blank["id"], "ok", output=_output()),
                         cache_line(ok["id"], "ok", output=_output())])
    code, rep = _apply(d, cache)
    assert code == 0, rep
    assert rep["accepted_in_window"] == 1
    urls = {i["url"] for i in json.loads((d / "current.json").read_text("utf-8"))["incidents"]}
    assert ok["url"] in urls and blank["url"] not in urls
    items = {r["id"]: r for r in json.loads((d / "rejected" / "2026-09.json").read_text("utf-8"))["items"]}
    assert items[blank["id"]]["rejection_stage"] == "empty_title"
    assert ok["id"] not in items


def test_classify_sends_entity_free_description(tmp_path):
    # FID-06 parity: the stored raw description carries entities; the classifier
    # must receive the same decoded text as the live path.
    rid = "e000000000000001"
    d = make_data_dir(tmp_path, [_row(rid, description=(
        "Duane &#8220;Keffe D&#8221; Davis&nbsp;fue detenido por homicidio"))])
    seen: list[str] = []

    class Capturing(FakeRouter):
        def classify(self, title, description, key=None):
            seen.append(description)
            return super().classify(title, description, key=key)

    router = Capturing(default=result(Outcome.OK, output=_output()))
    assert B.run_classify(B.select_outage_rows(d, SINCE), tmp_path / "scr" / "c.jsonl",
                          router, meter(tmp_path)) == 0
    assert len(seen) == 1
    assert "“Keffe D”" in seen[0]
    assert "&#" not in seen[0] and "&nbsp;" not in seen[0]


# ---------------------------------------------------------------------------
# Review / audit sample
# ---------------------------------------------------------------------------

def test_review_prints_regex_hits(tmp_path, capsys):
    rows = [_row("q000000000000001", title="Detienen a hijo por robo"),
            _row("q000000000000002", title="Robo en local comercial"),
            _row("q000000000000003", title="Asalto en México - BioBioChile"),]
    d = make_data_dir(tmp_path, rows)
    cache = write_cache(tmp_path / "scr" / "c.jsonl", [
        cache_line("q000000000000001", "ok", output=_output()),
        cache_line("q000000000000002", "ok", output=_output()),
        cache_line("q000000000000003", "ok", output=_output(title_es="Asalto en México")),
    ])
    assert B.main(["--review", "--data-dir", str(d), "--cache", str(cache)]) == 0
    out = capsys.readouterr().out
    assert "q000000000000001" in out and "q000000000000003" in out
    assert "q000000000000002" not in out
    assert "review_hits=2" in out
    # premortem R-16: the review shows what gets published (title_src + guarded title_en)
    hit = next(json.loads(x) for x in out.splitlines() if "q000000000000003" in x)
    assert hit["title_src"] == "Asalto en México"
    assert hit["title_en"] == "Vehicle theft in Las Condes" and hit["title_en_fallback"] is False
    assert "title_es" not in hit


def test_review_ignores_classifier_title_es(tmp_path, capsys):
    # The classifier's own title_es is never published (FID-01) → never a review hit.
    rows = [_row("q000000000000004", title="Asalto")]
    d = make_data_dir(tmp_path, rows)
    cache = write_cache(tmp_path / "scr" / "c.jsonl", [
        cache_line("q000000000000004", "ok", output=_output(title_es="Asalto en México")),
    ])
    assert B.main(["--review", "--data-dir", str(d), "--cache", str(cache)]) == 0
    assert "review_hits=0" in capsys.readouterr().out


BIOBIO_GNEWS = dict(
    title="Seguridad, crimen organizado y cárceles: Gobierno recibe a ministros y fiscal de "
          "El Salvador - BioBioChile",
    description="Seguridad, crimen organizado y cárceles: Gobierno recibe a ministros y fiscal "
                "de El Salvador&nbsp;&nbsp;BioBioChile",
    url="https://news.google.com/rss/articles/CBMiabc?oc=5",
)


def test_stratum_real_format_gnews_row():
    assert B.stratum_of(_row("r1", **BIOBIO_GNEWS)) == B.STRATUM_GNEWS
    assert B.stratum_of(_row("r2", title="Balacera en Colombia")) == B.STRATUM_NON_CHILE
    # gnews wins over the non-Chile cue (disjoint, priority order)
    assert B.stratum_of(_row("r3", url="https://news.google.com/x",
                             title="Crimen en México")) == B.STRATUM_GNEWS
    assert B.stratum_of(_row("r4")) == B.STRATUM_RANDOM


def _audit_fixture(tmp_path, n_gnews, n_nonchile, n_random):
    rows, lines = [], []
    for i in range(n_gnews):
        r = _row(f"sg{i:014d}", url=f"https://news.google.com/rss/articles/{i}")
        rows.append(r)
    for i in range(n_nonchile):
        rows.append(_row(f"sn{i:014d}", title=f"Detenido en Argentina {i}"))
    for i in range(n_random):
        rows.append(_row(f"sr{i:014d}"))
    for r in rows:
        lines.append(cache_line(r["id"], "ok", output=_output()))
    d = make_data_dir(tmp_path, rows)
    cache = write_cache(tmp_path / "scr" / "c.jsonl", lines)
    return d, cache


def test_audit_sample_quotas_and_determinism(tmp_path, capsys):
    d, cache = _audit_fixture(tmp_path, 40, 20, 60)
    out1, out2 = tmp_path / "scr" / "a1.jsonl", tmp_path / "scr" / "a2.jsonl"
    before = snapshot(d)
    for out in (out1, out2):
        assert B.main(["--audit-sample", "50", "--seed", "3405", "--data-dir", str(d),
                       "--cache", str(cache), "--out", str(out)]) == 0
    assert snapshot(d) == before
    assert out1.read_bytes() == out2.read_bytes()
    lines = [json.loads(x) for x in out1.read_text("utf-8").splitlines()]
    assert len(lines) == 50 and len({x["id"] for x in lines}) == 50
    from collections import Counter
    assert Counter(x["stratum"] for x in lines) == {"gnews_title_only": 20, "non_chile_cue": 10,
                                                   "random": 20}
    first = lines[0]
    for key in ("id", "stratum", "title", "description", "url", "outlet", "date", "output"):
        assert key in first
    assert first["output"]["cut"] and first["output"]["slug"] and first["output"]["title_src"]
    assert first["output"]["title_en"] and first["output"]["title_en_fallback"] is False
    assert "title_es" not in first["output"]  # premortem R-16


def test_audit_sample_exit_5_when_stratum_empty(tmp_path, capsys):
    d, cache = _audit_fixture(tmp_path, 0, 15, 40)
    code = B.main(["--audit-sample", "50", "--data-dir", str(d), "--cache", str(cache),
                   "--out", str(tmp_path / "scr" / "a.jsonl")])
    assert code == B.EXIT_STRATUM
    assert "gnews_title_only" in capsys.readouterr().out
    assert not (tmp_path / "scr" / "a.jsonl").exists()


def test_audit_sample_shortfall_filled_from_random(tmp_path, capsys):
    d, cache = _audit_fixture(tmp_path, 5, 20, 60)
    out = tmp_path / "scr" / "a.jsonl"
    assert B.main(["--audit-sample", "50", "--data-dir", str(d), "--cache", str(cache),
                   "--out", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "shortfall gnews_title_only" in printed
    lines = [json.loads(x) for x in out.read_text("utf-8").splitlines()]
    from collections import Counter
    assert Counter(x["stratum"] for x in lines) == {"gnews_title_only": 5, "non_chile_cue": 10,
                                                   "random": 35}


def test_audit_resample_excludes_withheld_without_exit_5(tmp_path, capsys):
    """G-14 (ii): re-audit 30 from the NOT-withheld remainder; a fully withheld stratum
    is not a broken definition."""
    d, cache = _audit_fixture(tmp_path, 25, 15, 60)
    withhold = tmp_path / "scr" / "w.txt"
    withhold.write_text("\n".join(f"sg{i:014d}" for i in range(25)) + "\n", encoding="utf-8")
    out = tmp_path / "scr" / "a.jsonl"
    assert B.main(["--audit-sample", "30", "--seed", "3406", "--data-dir", str(d),
                   "--cache", str(cache), "--out", str(out), "--withhold-ids", str(withhold)]) == 0
    lines = [json.loads(x) for x in out.read_text("utf-8").splitlines()]
    assert len(lines) == 30
    assert not any(x["id"].startswith("sg") for x in lines)


# ---------------------------------------------------------------------------
# CLI --classify exit codes (0 / 3 / 4) through main()
# ---------------------------------------------------------------------------

class _CliRouter(FakeRouter):
    any_key_present = True
    key_env_names = ["OPENROUTER_API_KEY"]
    primary_label = "openrouter:fake"
    backup_label = "deepseek:fake"
    failovers = 0

    def preflight(self):
        return None


def _cli_classify(tmp_path, monkeypatch, router, cap="5"):
    ids = _ids(3, "t")
    d = make_data_dir(tmp_path, [_row(i) for i in ids])
    monkeypatch.setattr(C, "build_router_from_env", lambda: router)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    cache = tmp_path / "scr" / "c.jsonl"
    before = snapshot(d)
    argv = ["--classify", "--data-dir", str(d), "--cache", str(cache),
            "--spend-ledger", str(tmp_path / "scr" / "spend.json")]
    if cap is not None:
        argv += ["--spend-cap", cap]
    code = B.main(argv, env_files=[])
    assert snapshot(d) == before
    return code, cache


def test_cli_classify_exit_0(tmp_path, monkeypatch):
    ok = result(Outcome.OK, output=_output(), usage={"prompt_tokens": 3700, "completion_tokens": 150})
    code, cache = _cli_classify(tmp_path, monkeypatch, _CliRouter(default=ok))
    assert code == 0 and len(B.load_cache(cache)) == 3
    ledger = json.loads((tmp_path / "scr" / "spend.json").read_text("utf-8"))
    assert 0 < ledger["total_usd"] < 5


def test_cli_classify_exit_4(tmp_path, monkeypatch):
    ok = result(Outcome.OK, output=_output())
    code, cache = _cli_classify(tmp_path, monkeypatch, _CliRouter(default=ok, exhaust_after=1))
    assert code == B.EXIT_EXHAUSTED and len(B.load_cache(cache)) == 1


def test_cli_classify_exit_3(tmp_path, monkeypatch):
    ok = result(Outcome.OK, output=_output())
    code, cache = _cli_classify(tmp_path, monkeypatch, _CliRouter(default=ok), cap="0.001")
    assert code == B.EXIT_CAP and not B.load_cache(cache)


def test_cli_classify_requires_spend_cap(tmp_path, monkeypatch):
    code, _ = _cli_classify(tmp_path, monkeypatch, _CliRouter(), cap=None)
    assert code == B.EXIT_ERROR
