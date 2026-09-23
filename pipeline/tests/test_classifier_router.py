"""
pipeline/tests/test_classifier_router.py

Phase 34-02 (NREC-02..06): typed outcomes, tenacity retry, OpenRouter preflight,
ProviderRouter failover / breaker / same-run re-dispatch / run budget, and
build_router_from_env. NO live network: every client is a fake, requests.get is
patched to raise, and the tenacity sleep is a recorder.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
import requests
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    NotFoundError,
    RateLimitError,
)

from pipeline.news import classifier as C  # type: ignore
from pipeline.news import model_config  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"

_VALID = {
    "commune_name": "Las Condes",
    "region_hint": "Metropolitana",
    "family": "propiedad",
    "title_es": "Robo en Las Condes",
    "title_en": "Robbery in Las Condes",
    "summary": "A robbery occurred in Las Condes.",
    "confidence": 0.9,
}


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

def _resp(content=None, *, data=None, finish="stop", provider="CoreWeave", model="m/x",
          prompt=100, completion=20, reasoning=0, cost=None):
    if data is not None:
        content = json.dumps(data)
    usage = SimpleNamespace(
        prompt_tokens=prompt,
        completion_tokens=completion,
        completion_tokens_details=SimpleNamespace(reasoning_tokens=reasoning),
    )
    if cost is not None:
        usage.cost = cost
    r = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason=finish)],
        model=model,
        usage=usage,
    )
    if provider is not None:
        r.provider = provider
    return r


def _ok():
    return _resp(data=_VALID)


def _status_exc(cls, code):
    req = httpx.Request("POST", "https://x")
    return cls(f"HTTP {code}", response=httpx.Response(code, request=req), body=None)


def _e404():
    return _status_exc(NotFoundError, 404)


def _client(side_effect):
    cl = MagicMock()
    cl.chat.completions.create.side_effect = side_effect
    return cl


def _spec(cl, provider="openrouter", model="m/x", key_present=True, extra_body=None, key_env="K"):
    return C.ProviderSpec(
        provider=provider,
        model=model,
        client_getter=lambda: cl,
        extra_body=extra_body,
        key_present=key_present,
        key_env=key_env,
    )


def _calls(cl):
    return cl.chat.completions.create.call_count


class _HttpResp:
    def __init__(self, status_code, payload=None, raise_json=False):
        self.status_code = status_code
        self._payload = payload
        self._raise = raise_json

    def json(self):
        if self._raise:
            raise ValueError("invalid json")
        return self._payload


def _fixture_json(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# The delisted model id is read from the verbatim NREC-03 fixture so that no .py file
# under pipeline/ carries the dead literal (G-06 grep instrument).
_DEAD_ID = _fixture_json("openrouter_endpoints_granite_4_1_8b.json")["data"]["id"]


@pytest.fixture(autouse=True)
def _no_network_no_sleep(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr(C, "_sleep", lambda s: sleeps.append(s))

    def _boom(*a, **k):
        raise requests.ConnectionError("network disabled in tests")

    monkeypatch.setattr(requests, "get", _boom)
    for var in ("NEWS_FORCE_BACKUP", "NEWS_RUN_BUDGET_S", "NEWS_PROVIDER", "NEWS_MODEL",
                "NEWS_BACKUP_MODEL"):
        monkeypatch.delenv(var, raising=False)
    return sleeps


# ---------------------------------------------------------------------------
# NREC-03 preflight
# ---------------------------------------------------------------------------

def test_preflight_zero_endpoints_verbatim_fixture():
    body = _fixture_json("openrouter_endpoints_granite_4_1_8b.json")
    assert body["data"]["endpoints"] == []
    seen_urls = []

    def get(url, **kw):
        seen_urls.append(url)
        return _HttpResp(200, body)

    res = C.preflight_openrouter(_DEAD_ID, http_get=get)
    assert res.status == "zero_endpoints"
    assert res.endpoints == 0
    assert seen_urls == [f"https://openrouter.ai/api/v1/models/{_DEAD_ID}/endpoints"]


def test_preflight_two_endpoints_ok():
    body = {"data": {"id": "a/b", "endpoints": [{"name": "x"}, {"name": "y"}]}}
    res = C.preflight_openrouter("a/b", http_get=lambda url, **k: _HttpResp(200, body))
    assert res.status == "ok" and res.endpoints == 2


@pytest.mark.parametrize(
    "getter,expected",
    [
        (lambda url, **k: _HttpResp(404, {"error": "nope"}), "model_unknown"),
        (lambda url, **k: _HttpResp(503, None), "unknown"),
        (lambda url, **k: _HttpResp(200, None, raise_json=True), "unknown"),
    ],
)
def test_preflight_status_mapping(getter, expected):
    assert C.preflight_openrouter("a/b", http_get=getter).status == expected


def test_preflight_connection_error_unknown():
    def get(url, **k):
        raise requests.ConnectionError("down")

    assert C.preflight_openrouter("a/b", http_get=get).status == "unknown"


def _dispatch(endpoints_body, key_resp):
    calls = []

    def get(url, **kw):
        calls.append((url, kw))
        if url.endswith("/key"):
            if isinstance(key_resp, Exception):
                raise key_resp
            return key_resp
        return _HttpResp(200, endpoints_body)

    return get, calls


_TWO_EP = {"data": {"endpoints": [{"n": 1}, {"n": 2}]}}


def test_preflight_key_no_credit():
    get, calls = _dispatch(_TWO_EP, _HttpResp(200, _fixture_json("openrouter_key_no_credit.json")))
    res = C.preflight_openrouter("a/b", api_key="sk-secret", http_get=get)
    assert res.status == "no_credit"
    key_call = [c for c in calls if c[0] == "https://openrouter.ai/api/v1/key"]
    assert len(key_call) == 1
    assert key_call[0][1]["headers"] == {"Authorization": "Bearer sk-secret"}


@pytest.mark.parametrize(
    "key_resp",
    [
        _HttpResp(200, {"data": {"limit_remaining": None}}),
        _HttpResp(200, {"data": {"limit_remaining": 3.5}}),
        requests.ConnectionError("down"),
        _HttpResp(500, None),
    ],
)
def test_preflight_key_credit_ok_or_unknown_no_change(key_resp):
    get, _ = _dispatch(_TWO_EP, key_resp)
    assert C.preflight_openrouter("a/b", api_key="sk", http_get=get).status == "ok"


def test_preflight_without_key_does_not_call_key_endpoint():
    get, calls = _dispatch(_TWO_EP, _HttpResp(200, {"data": {"limit_remaining": 0}}))
    assert C.preflight_openrouter("a/b", http_get=get).status == "ok"
    assert len(calls) == 1


def test_router_preflight_zero_endpoints_fails_over_before_first_completion(monkeypatch):
    body = _fixture_json("openrouter_endpoints_granite_4_1_8b.json")
    monkeypatch.setattr(requests, "get", lambda url, **k: _HttpResp(200, body))
    prim, back = _client([_ok()]), _client([_ok()])
    r = C.ProviderRouter(
        _spec(prim, model=_DEAD_ID), _spec(back, provider="deepseek")
    )
    pf = r.preflight()
    assert pf.status == "zero_endpoints"
    assert r.preflight_status == "zero_endpoints"
    assert r.failovers == 1 and r.failover_reason == "preflight_zero_endpoints"
    res = r.classify("t", "d", key="k1")
    assert res.outcome is C.Outcome.OK
    assert _calls(prim) == 0
    assert _calls(back) == 1


def test_router_preflight_no_credit_fails_over(monkeypatch):
    get, _ = _dispatch(_TWO_EP, _HttpResp(200, _fixture_json("openrouter_key_no_credit.json")))
    monkeypatch.setattr(requests, "get", get)
    prim_spec = _spec(_client([]))
    prim_spec.api_key = "sk-x"
    r = C.ProviderRouter(prim_spec, _spec(_client([]), provider="deepseek"))
    r.preflight()
    assert r.failover_reason == "preflight_no_credit"
    assert r.active == "backup"


def test_router_preflight_unknown_stays_on_primary(caplog):
    # requests.get raises (autouse) → "unknown"
    prim = _client([_ok()])
    r = C.ProviderRouter(_spec(prim), _spec(_client([]), provider="deepseek"))
    with caplog.at_level("WARNING"):
        assert r.preflight().status == "unknown"
    assert r.active == "primary" and r.failovers == 0
    assert "inconclusive" in caplog.text
    r.classify("t", "d")
    assert _calls(prim) == 1


def test_router_preflight_skipped_for_non_openrouter_primary():
    r = C.ProviderRouter(_spec(_client([]), provider="deepseek"), None)
    assert r.preflight().status == "skipped"


# ---------------------------------------------------------------------------
# NREC-06 retry mapping
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("exc,code", [(_e404(), 404), (_status_exc(AuthenticationError, 401), 401)])
def test_non_retryable_status_called_once(exc, code, _no_network_no_sleep):
    cl = _client([exc, _ok()])
    res = C.classify_outcome("t", "d", _spec(cl))
    assert _calls(cl) == 1
    assert res.outcome is C.Outcome.API_ERROR
    assert res.status_code == code
    assert _no_network_no_sleep == []


def test_429_retried_three_times_with_2_4_waits(_no_network_no_sleep):
    cl = _client([_status_exc(RateLimitError, 429)] * 3)
    res = C.classify_outcome("t", "d", _spec(cl))
    assert _calls(cl) == 3
    assert _no_network_no_sleep == [2, 4]
    assert res.outcome is C.Outcome.API_ERROR and res.status_code == 429
    assert res.error == "RateLimitError"


def test_500_then_success_is_ok(_no_network_no_sleep):
    cl = _client([_status_exc(InternalServerError, 500), _ok()])
    res = C.classify_outcome("t", "d", _spec(cl))
    assert _calls(cl) == 2
    assert res.outcome is C.Outcome.OK
    assert _no_network_no_sleep == [2]


@pytest.mark.parametrize("exc_factory", [
    lambda: APIConnectionError(request=httpx.Request("POST", "https://x")),
    lambda: APITimeoutError(request=httpx.Request("POST", "https://x")),
])
def test_connection_errors_retried_like_429(exc_factory, _no_network_no_sleep):
    cl = _client([exc_factory() for _ in range(3)])
    res = C.classify_outcome("t", "d", _spec(cl))
    assert _calls(cl) == 3
    assert res.outcome is C.Outcome.API_ERROR and res.status_code is None
    assert _no_network_no_sleep == [2, 4]


def test_non_openai_exception_is_api_error_not_retried():
    cl = _client([ValueError("weird"), _ok()])
    res = C.classify_outcome("t", "d", _spec(cl))
    assert _calls(cl) == 1
    assert res.outcome is C.Outcome.API_ERROR and res.error == "ValueError"


def test_is_retryable_matrix():
    assert C._is_retryable(_status_exc(RateLimitError, 429))
    assert C._is_retryable(_status_exc(InternalServerError, 502))
    for code, cls in [(400, None), (403, None), (404, NotFoundError), (409, None), (422, None)]:
        from openai import APIStatusError
        exc = _status_exc(cls or APIStatusError, code)
        assert not C._is_retryable(exc), code


# ---------------------------------------------------------------------------
# G-09 / R-03 content outcomes
# ---------------------------------------------------------------------------

def test_empty_content_one_recall_then_transient_api_error():
    cl = _client([_resp(""), _resp(None)])
    res = C.classify_outcome("t", "d", _spec(cl))
    assert _calls(cl) == 2
    assert res.outcome is C.Outcome.API_ERROR
    assert res.error == "empty_content" and res.status_code is None


def test_empty_then_valid_is_ok():
    cl = _client([_resp(""), _ok()])
    assert C.classify_outcome("t", "d", _spec(cl)).outcome is C.Outcome.OK


def test_finish_length_is_transient_no_recall():
    cl = _client([_resp('{"commune_name": "Las', finish="length"), _ok()])
    res = C.classify_outcome("t", "d", _spec(cl))
    assert _calls(cl) == 1
    assert res.outcome is C.Outcome.API_ERROR and res.error == "finish_length"
    assert res.finish_reason == "length"


def test_prose_wrapped_json_ok():
    cl = _client([_resp("Here you go: " + json.dumps(_VALID) + " thanks")])
    assert C.classify_outcome("t", "d", _spec(cl)).outcome is C.Outcome.OK


@pytest.mark.parametrize("content", ["not json at all", json.dumps(dict(_VALID, family="banana"))])
def test_bad_json_or_family_is_parse_error(content):
    res = C.classify_outcome("t", "d", _spec(_client([_resp(content)])))
    assert res.outcome is C.Outcome.PARSE_ERROR and res.output is None


def test_low_confidence_is_not_crime_with_output():
    res = C.classify_outcome("t", "d", _spec(_client([_resp(data=dict(_VALID, confidence=0.3))])))
    assert res.outcome is C.Outcome.NOT_CRIME
    assert res.output is not None and res.output.confidence == 0.3


# ---------------------------------------------------------------------------
# R-10 / R-12 response metadata
# ---------------------------------------------------------------------------

def test_served_by_finish_reason_usage_with_cost():
    cl = _client([_resp(data=_VALID, provider="DeepInfra", prompt=3810, completion=133,
                        reasoning=0, cost=0.0002)])
    res = C.classify_outcome("t", "d", _spec(cl))
    assert res.served_by == "DeepInfra"
    assert res.finish_reason == "stop"
    assert res.usage == {"prompt_tokens": 3810, "completion_tokens": 133,
                         "reasoning_tokens": 0, "cost": 0.0002}


def test_served_by_falls_back_to_resp_model():
    cl = _client([_resp(data=_VALID, provider=None, model="deepseek-v4-flash", reasoning=7)])
    res = C.classify_outcome("t", "d", _spec(cl))
    assert res.served_by == "deepseek-v4-flash"
    assert res.usage["reasoning_tokens"] == 7
    assert "cost" not in res.usage


# ---------------------------------------------------------------------------
# Breaker, failover, re-dispatch (G-03, G-09, R-04)
# ---------------------------------------------------------------------------

def test_breaker_trips_after_5_and_sixth_goes_to_backup():
    prim = _client([_e404() for _ in range(10)])
    back = _client([_ok() for _ in range(10)])
    r = C.ProviderRouter(_spec(prim), _spec(back, provider="deepseek"))
    for i in range(5):
        assert r.classify("t", "d", key=f"k{i+1}").outcome is C.Outcome.API_ERROR
    assert r.failovers == 1 and r.failover_reason == "breaker"
    assert r.active == "backup"
    res6 = r.classify("t", "d", key="k6")
    assert res6.outcome is C.Outcome.OK and res6.provider == "deepseek"
    assert _calls(prim) == 5
    assert _calls(back) == 6  # 5 re-dispatched + the 6th


def test_non_consecutive_errors_do_not_trip():
    prim = _client([_e404()] * 4 + [_ok()] + [_e404()] * 4)
    r = C.ProviderRouter(_spec(prim), _spec(_client([]), provider="deepseek"))
    for _ in range(9):
        r.classify("t", "d")
    assert r.failovers == 0 and r.active == "primary"
    assert r.pop_redispatched() == []


def test_redispatch_backup_ok_pairs_then_empty():
    prim = _client([_e404() for _ in range(5)])
    back = _client([_ok() for _ in range(5)])
    r = C.ProviderRouter(_spec(prim), _spec(back, provider="deepseek"))
    for i in range(1, 5):
        r.classify("t", "d", key=f"k{i}")
        assert r.pop_redispatched() == []
    r.classify("t", "d", key="k5")
    pairs = r.pop_redispatched()
    assert [k for k, _ in pairs] == ["k1", "k2", "k3", "k4", "k5"]
    assert all(res.outcome is C.Outcome.OK for _, res in pairs)
    assert r.pop_redispatched() == []


def test_redispatch_backup_failing_pairs_are_api_error_and_count_toward_backup_breaker():
    prim = _client([_e404() for _ in range(5)])
    back = _client([_e404() for _ in range(10)])
    r = C.ProviderRouter(_spec(prim), _spec(back, provider="deepseek"))
    for i in range(1, 6):
        r.classify("t", "d", key=f"k{i}")
    pairs = r.pop_redispatched()
    assert len(pairs) == 5
    assert all(res.outcome is C.Outcome.API_ERROR for _, res in pairs)
    # 5 re-dispatched backup errors trip the backup breaker
    assert r.backup_exhausted is True and r.active == "none"
    before = (_calls(prim), _calls(back))
    assert r.classify("t", "d", key="k6") is None
    assert (_calls(prim), _calls(back)) == before


def test_backup_exhausts_mid_redispatch_remaining_keep_original():
    prim = _client([_e404() for _ in range(5)])
    # backup: 4 errors already counted? start forced-free: first make backup fail 5 on redispatch
    back = _client([_e404() for _ in range(5)])
    r = C.ProviderRouter(_spec(prim), _spec(back, provider="deepseek"))
    r._consec["backup"] = 3  # pretend prior backup errors: exhausts after 2 re-dispatches
    for i in range(1, 6):
        r.classify("t", "d", key=f"k{i}")
    pairs = r.pop_redispatched()
    assert len(pairs) == 5
    assert _calls(back) == 2
    assert all(res.outcome is C.Outcome.API_ERROR for _, res in pairs)
    assert pairs[4][1].provider == "openrouter"  # original primary result


def test_backup_breaker_after_trip():
    prim = _client([_e404() for _ in range(5)])
    back = _client([_ok()] * 5 + [_e404()] * 5)
    r = C.ProviderRouter(_spec(prim), _spec(back, provider="deepseek"))
    for i in range(5):
        r.classify("t", "d", key=f"k{i}")
    r.pop_redispatched()
    for i in range(5):
        assert r.classify("t", "d").outcome is C.Outcome.API_ERROR
    assert r.backup_exhausted is True
    n = _calls(back)
    assert r.classify("t", "d") is None
    assert _calls(back) == n


def test_primary_key_absent_starts_on_backup():
    back = _client([_ok()])
    prim = _client([])
    r = C.ProviderRouter(_spec(prim, key_present=False), _spec(back, provider="deepseek"))
    assert r.active == "backup" and r.failover_reason == "primary_key_absent"
    assert r.preflight().status == "skipped"
    r.classify("t", "d")
    assert _calls(prim) == 0 and _calls(back) == 1


def test_backup_key_absent_when_primary_trips():
    prim = _client([_e404() for _ in range(6)])
    back = _client([])
    r = C.ProviderRouter(_spec(prim), _spec(back, provider="deepseek", key_present=False))
    for i in range(5):
        r.classify("t", "d", key=f"k{i}")
    assert r.backup_exhausted is True
    assert r.failover_reason == "backup_unavailable"
    assert r.active == "none"
    assert r.classify("t", "d") is None
    assert _calls(back) == 0
    assert r.pop_redispatched() == []


# ---------------------------------------------------------------------------
# R-11 run budget
# ---------------------------------------------------------------------------

def test_run_budget_stops_classification():
    now = [0.0]

    def create(**kw):
        now[0] += 100.0
        return _ok()

    prim = MagicMock()
    prim.chat.completions.create.side_effect = create
    r = C.ProviderRouter(_spec(prim), None, clock=lambda: now[0], budget_s=1200)
    results = [r.classify("t", "d") for _ in range(20)]
    assert sum(1 for x in results if x is not None) == 12
    assert all(x is None for x in results[12:])
    assert r.budget_exhausted is True
    assert _calls(prim) == 12


def test_run_budget_env_default(monkeypatch):
    r = C.ProviderRouter(_spec(_client([])), None)
    assert r.budget_s == 1200
    monkeypatch.setenv("NEWS_RUN_BUDGET_S", "60")
    assert C.ProviderRouter(_spec(_client([])), None).budget_s == 60
    monkeypatch.setenv("NEWS_RUN_BUDGET_S", "")
    assert C.ProviderRouter(_spec(_client([])), None).budget_s == 1200


# ---------------------------------------------------------------------------
# build_router_from_env (R-09, R-12, G-08)
# ---------------------------------------------------------------------------

@pytest.fixture
def keys(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-key")


def test_force_backup(monkeypatch, keys):
    monkeypatch.setenv("NEWS_FORCE_BACKUP", "TRUE")
    r = C.build_router_from_env()
    assert r.active == "backup" and r.failovers == 1 and r.failover_reason == "forced"
    assert r.preflight().status == "skipped"


def test_empty_env_strings_fall_back_to_defaults(monkeypatch, keys):
    monkeypatch.setenv("NEWS_PROVIDER", "")
    monkeypatch.setenv("NEWS_MODEL", "")
    monkeypatch.setenv("NEWS_BACKUP_MODEL", "")
    r = C.build_router_from_env()
    assert r.primary.provider == model_config.DEFAULT_PROVIDER
    assert r.primary.model == model_config.DEFAULT_OPENROUTER_MODEL
    assert r.backup.provider == "deepseek"
    assert r.backup.model == model_config.DEFAULT_BACKUP_MODEL
    assert r.primary_label == f"openrouter:{model_config.DEFAULT_OPENROUTER_MODEL}"


def test_env_overrides_without_code_edit(monkeypatch, keys):
    monkeypatch.setenv("NEWS_MODEL", "x/y")
    monkeypatch.setenv("NEWS_BACKUP_MODEL", "deepseek-other")
    r = C.build_router_from_env()
    assert r.primary.model == "x/y" and r.backup.model == "deepseek-other"


def test_fresh_clients_read_env_at_call_time(monkeypatch):
    assert C.client.api_key != "k-new"
    monkeypatch.setenv("OPENROUTER_API_KEY", "k-new")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    r = C.build_router_from_env()
    assert r.primary.client_getter().api_key == "k-new"
    assert r.primary.client_getter() is not C.client
    assert r.primary.key_present is True
    assert r.backup.key_present is False  # "" from an unset GH secret == absent


def test_whitespace_primary_key_is_absent(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "   ")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds")
    r = C.build_router_from_env()
    assert r.active == "backup" and r.failover_reason == "primary_key_absent"
    assert r.any_key_present is True


def test_clients_max_retries_zero_timeout_30(keys):
    for cl in (C.client, C.backup_client):
        assert cl.max_retries == 0
        assert cl.timeout == 30.0
    r = C.build_router_from_env()
    for spec in (r.primary, r.backup):
        assert spec.client_getter().max_retries == 0
        assert spec.client_getter().timeout == 30.0


def test_create_kwargs_per_provider(monkeypatch, keys):
    made = []

    def fake_make(key, base_url):
        m = _client([_e404()] * 5 + [_ok()] * 10)
        made.append((base_url, m))
        return m

    monkeypatch.setattr(C, "_make_client", fake_make)
    r = C.build_router_from_env()
    for i in range(5):
        r.classify("t", "d", key=f"k{i}")
    prim = dict(made)[C.OPENROUTER_BASE_URL]
    back = dict(made)[C.DEEPSEEK_BASE_URL]
    pk = prim.chat.completions.create.call_args.kwargs
    assert pk["extra_body"] == model_config.REASONING_EXTRA_BODY_OPENROUTER
    assert "response_format" not in pk
    assert pk["model"] == model_config.DEFAULT_OPENROUTER_MODEL
    bk = back.chat.completions.create.call_args.kwargs
    assert bk["response_format"] == {"type": "json_object"}
    assert bk["extra_body"] == model_config.REASONING_EXTRA_BODY_DEEPSEEK
    assert bk["model"] == model_config.DEFAULT_BACKUP_MODEL


def test_compat_classify_returns_none_on_api_error(monkeypatch):
    monkeypatch.setattr(C, "client", _client([_e404()]))
    assert C.classify("t", "d") is None


# ---------------------------------------------------------------------------
# NREC-02 import-time defaults (subprocess, fresh interpreter)
# ---------------------------------------------------------------------------

def _run_py(code: str, **env_over) -> str:
    env = {k: v for k, v in os.environ.items()
           if k not in ("NEWS_PROVIDER", "NEWS_MODEL", "NEWS_BACKUP_MODEL", "NEWS_FORCE_BACKUP")}
    env.update(env_over)
    env["PYTHONIOENCODING"] = "utf-8"
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=str(REPO_ROOT), env=env,
        capture_output=True, text=True, timeout=120,
    )
    assert out.returncode == 0, out.stderr
    return out.stdout.strip().splitlines()[-1]


def test_subprocess_news_model_env_override():
    line = _run_py("import pipeline.news.classifier as c; print(c._MODEL)", NEWS_MODEL="x/y")
    assert line == "x/y"


def test_subprocess_unset_defaults_to_model_config():
    line = _run_py(
        "import pipeline.news.classifier as c, pipeline.news.model_config as m;"
        "print(c._PROVIDER == m.DEFAULT_PROVIDER, c._MODEL, c.client.max_retries, c.client.timeout)",
        NEWS_PROVIDER="", NEWS_MODEL="",
    )
    ok, model, retries, timeout = line.split()
    assert ok == "True"
    assert model == model_config.DEFAULT_OPENROUTER_MODEL
    assert "granite-4.1" not in model
    assert retries == "0" and float(timeout) == 30.0


def test_subprocess_deepseek_direct_default_provider():
    """G-08 DEEPSEEK_DIRECT: primary DeepSeek direct, backup OpenRouter deepseek model."""
    code = (
        "import json, pipeline.news.model_config as m\n"
        "m.DEFAULT_PROVIDER = 'deepseek'\n"
        "import pipeline.news.classifier as c\n"
        "r = c.build_router_from_env()\n"
        "print(json.dumps([c._PROVIDER, c._MODEL, r.primary.provider, r.primary.model,"
        " r.backup.provider, r.backup.model, r.backup.extra_body, r.primary.extra_body]))\n"
    )
    vals = json.loads(_run_py(code, OPENROUTER_API_KEY="a", DEEPSEEK_API_KEY="b"))
    assert vals[0] == "deepseek" and vals[1] == "deepseek-v4-flash"
    assert vals[2] == "deepseek" and vals[3] == "deepseek-v4-flash"
    assert vals[4] == "openrouter" and vals[5] == model_config.DEFAULT_OPENROUTER_MODEL
    assert vals[6] == model_config.REASONING_EXTRA_BODY_OPENROUTER
    assert vals[7] == model_config.REASONING_EXTRA_BODY_DEEPSEEK
