"""
pipeline/tests/test_eval_classifier.py

Offline tests for pipeline/experiments/eval_classifier.py (34-01 Task 2).
No network I/O — an autouse fixture patches requests.get and openai.OpenAI to
raise if a test forgets to mock them.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from pipeline.experiments import eval_classifier as ev
from pipeline.news import classifier as classifier_mod

FAMILY_MIN = 40  # mirrors G-15 (ev.FAMILY_MIN_V2)


# ---------------------------------------------------------------------------
# Autouse network guard
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def _raise_get(*a, **k):
        raise AssertionError("unmocked requests.get call in test")

    def _raise_openai(*a, **k):
        raise AssertionError("unmocked openai.OpenAI() call in test")

    monkeypatch.setattr(ev.requests, "get", _raise_get)
    # Only guard direct OpenAI() construction; individual tests build their own
    # MagicMock clients instead of calling _make_client for logic-only tests.
    yield


def _mk_candidate(**overrides) -> dict:
    base = {
        "provider": "openrouter",
        "model": "deepseek/deepseek-v4-flash",
        "status": "COMPLETE",
        "commune_correct": 42,
        "family_correct": FAMILY_MIN,
        "parse_errors": 0,
        "endpoints": 2,
        "empty_content_count": 0,
        "finish_length_count": 0,
        "reasoning_tokens_total": 0,
        "blended_usd_per_item": 0.001,
        "reasoning_variant": "enabled_false",
        "reasoning_extra_body": {"reasoning": {"enabled": False}},
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# select_winner — strict tier qualification
# ---------------------------------------------------------------------------


def test_select_winner_qualifies_strict():
    c = _mk_candidate()
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    assert result["decision"]["status"] == "WINNER"
    assert result["decision"]["winner"]["model"] == c["model"]


def test_select_winner_disqualified_commune():
    c = _mk_candidate(commune_correct=41)
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    cand = result["candidates"][0]
    assert "commune" in cand["disqualified_by_strict"]
    assert result["decision"]["status"] != "WINNER"


def test_select_winner_disqualified_family():
    c = _mk_candidate(family_correct=FAMILY_MIN - 1)
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    cand = result["candidates"][0]
    assert "family" in cand["disqualified_by_strict"]


def test_select_winner_disqualified_parse_fail():
    c = _mk_candidate(parse_errors=1)
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    cand = result["candidates"][0]
    assert "parse_fail" in cand["disqualified_by_strict"]


def test_select_winner_disqualified_endpoints():
    c = _mk_candidate(endpoints=1)
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    cand = result["candidates"][0]
    assert "endpoints" in cand["disqualified_by_strict"]


# ---------------------------------------------------------------------------
# G-13: transient truncation / empty disqualify in BOTH tiers
# ---------------------------------------------------------------------------


def test_select_winner_finish_length_disqualifies_both_tiers():
    c = _mk_candidate(finish_length_count=1, reasoning_tokens_total=0)
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    cand = result["candidates"][0]
    assert "transient_truncation" in cand["disqualified_by_strict"]
    assert "transient_truncation" in cand["disqualified_by_fallback"]


def test_select_winner_empty_content_disqualifies_both_tiers():
    c = _mk_candidate(empty_content_count=1)
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    cand = result["candidates"][0]
    assert "transient_empty" in cand["disqualified_by_strict"]
    assert "transient_empty" in cand["disqualified_by_fallback"]


def test_select_winner_reasoning_tokens_positive_still_qualifies():
    c = _mk_candidate(reasoning_tokens_total=5, empty_content_count=0, finish_length_count=0)
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    assert result["decision"]["status"] == "WINNER"


def test_select_winner_finish_length_complete_not_incomplete():
    """A candidate with only finish_length_count=1 (no other api_errors) stays
    COMPLETE and disqualified, not INCOMPLETE (D-R2-04)."""
    c = _mk_candidate(finish_length_count=1, status="COMPLETE")
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    cand = result["candidates"][0]
    assert cand["status"] == "COMPLETE"
    assert "incomplete" not in cand["disqualified_by_strict"]
    assert "transient_truncation" in cand["disqualified_by_strict"]


def test_select_winner_incomplete_never_wins():
    c = _mk_candidate(status="INCOMPLETE")
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    cand = result["candidates"][0]
    assert cand["disqualified_by_strict"] == ["incomplete"]
    assert result["decision"]["status"] != "WINNER"


# ---------------------------------------------------------------------------
# Winner tie-break determinism
# ---------------------------------------------------------------------------


def test_select_winner_tie_break_endpoints_then_price_deterministic_under_shuffle():
    a = _mk_candidate(model="a", family_correct=FAMILY_MIN, endpoints=3, blended_usd_per_item=0.002)
    b = _mk_candidate(model="b", family_correct=FAMILY_MIN, endpoints=5, blended_usd_per_item=0.005)
    c = _mk_candidate(model="c", family_correct=FAMILY_MIN, endpoints=5, blended_usd_per_item=0.001)

    for order in ([a, b, c], [c, b, a], [b, a, c]):
        result = ev.select_winner(list(order), family_min_v2=FAMILY_MIN)
        assert result["decision"]["winner"]["model"] == "c"  # most endpoints (5), cheapest


# ---------------------------------------------------------------------------
# G-08 fallback tiers
# ---------------------------------------------------------------------------


def test_select_winner_fallback_winner_when_no_strict_qualifier():
    c = _mk_candidate(commune_correct=41, family_correct=FAMILY_MIN - 5, parse_errors=1)
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    assert result["decision"]["status"] == "FALLBACK_WINNER"
    assert result["decision"]["no_qualifier"] is True
    assert result["decision"]["winner"]["model"] == c["model"]


def test_select_winner_fallback_ineligible_with_finish_length():
    c = _mk_candidate(
        commune_correct=41, family_correct=FAMILY_MIN - 5, parse_errors=1, finish_length_count=1
    )
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    assert result["decision"]["status"] == "DEEPSEEK_DIRECT"


def test_select_winner_deepseek_direct_when_nothing_qualifies():
    c = _mk_candidate(commune_correct=10, family_correct=1, parse_errors=10, endpoints=0)
    backup = {"reasoning_variant": "thinking_disabled", "reasoning_extra_body": {"thinking": {"type": "disabled"}}}
    result = ev.select_winner([c], backup=backup, family_min_v2=FAMILY_MIN)
    d = result["decision"]
    assert d["status"] == "DEEPSEEK_DIRECT"
    assert d["no_qualifier"] is True
    assert d["winner"]["provider"] == "deepseek"
    assert d["winner"]["model"] == "deepseek-v4-flash"
    assert d["winner"]["reasoning_extra_body"] == {"thinking": {"type": "disabled"}}


def test_select_winner_all_incomplete_status_incomplete():
    c = _mk_candidate(status="INCOMPLETE")
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    assert result["decision"]["status"] == "INCOMPLETE"


def test_select_winner_raises_without_family_min_when_module_constant_unset(monkeypatch):
    monkeypatch.setattr(ev, "FAMILY_MIN_V2", None)
    with pytest.raises(ValueError):
        ev.select_winner([_mk_candidate()])


# ---------------------------------------------------------------------------
# Probe variant choice
# ---------------------------------------------------------------------------


def test_choose_probe_variant_first_clean_variant_wins():
    per_variant = {
        "enabled_false": {"reasoning_tokens_total": 3, "empty": 0, "api_errors": 0},
        "effort_none": {"reasoning_tokens_total": 0, "empty": 0, "api_errors": 0},
        "none": {"reasoning_tokens_total": 0, "empty": 0, "api_errors": 0},
    }
    variant, unfixable = ev.choose_probe_variant(per_variant, ["enabled_false", "effort_none", "none"])
    assert variant == "effort_none"
    assert unfixable is False


def test_choose_probe_variant_falls_back_to_empty_zero():
    per_variant = {
        "enabled_false": {"reasoning_tokens_total": 3, "empty": 0, "api_errors": 0},
        "effort_none": {"reasoning_tokens_total": 5, "empty": 1, "api_errors": 0},
        "none": {"reasoning_tokens_total": 2, "empty": 0, "api_errors": 0},
    }
    variant, unfixable = ev.choose_probe_variant(per_variant, ["enabled_false", "effort_none", "none"])
    assert variant == "enabled_false"
    assert unfixable is False


def test_choose_probe_variant_reasoning_unfixable():
    per_variant = {
        "enabled_false": {"reasoning_tokens_total": 3, "empty": 1, "api_errors": 0},
        "effort_none": {"reasoning_tokens_total": 5, "empty": 1, "api_errors": 0},
        "none": {"reasoning_tokens_total": 2, "empty": 1, "api_errors": 0},
    }
    variant, unfixable = ev.choose_probe_variant(per_variant, ["enabled_false", "effort_none", "none"])
    assert variant == "enabled_false"  # first in order
    assert unfixable is True


def test_select_winner_reasoning_unfixable_disqualifies_both_tiers():
    c = _mk_candidate(reasoning_unfixable=True)
    result = ev.select_winner([c], family_min_v2=FAMILY_MIN)
    cand = result["candidates"][0]
    assert "reasoning_unfixable" in cand["disqualified_by_strict"]
    assert "reasoning_unfixable" in cand["disqualified_by_fallback"]


# ---------------------------------------------------------------------------
# Spend guard (NB-07)
# ---------------------------------------------------------------------------


def test_spend_cap_allows_boundary_exact_cap_allowed():
    assert ev.spend_cap_allows(0.4975, 0.0025, 0.50) is True


def test_spend_cap_allows_over_cap_denied():
    assert ev.spend_cap_allows(0.499, 0.0025, 0.50) is False


def test_ledger_accumulates_across_two_main_style_invocations(tmp_path):
    ledger_path = tmp_path / "ledger.json"

    allowed1, ledger1 = ev._check_and_load_ledger(ledger_path, 0.50, 0.001)
    assert allowed1 is True
    ev.record_charge(ledger_path, ledger1, "m", "v", 0.499)

    # Simulate a second process: fresh load from disk.
    allowed2, ledger2 = ev._check_and_load_ledger(ledger_path, 0.50, 0.0025)
    assert allowed2 is False  # 0.499 + 0.0025 > 0.50

    reloaded = ev.load_ledger(ledger_path)
    assert reloaded["total_usd"] == pytest.approx(0.499)


# ---------------------------------------------------------------------------
# _classify_one_item: empty-content re-call, finish_length transient
# ---------------------------------------------------------------------------


def _mock_resp(content, finish_reason="stop", prompt_tokens=100, completion_tokens=50, reasoning_tokens=0, provider="OpenRouterTest"):
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content
    resp.choices[0].finish_reason = finish_reason
    resp.usage = MagicMock()
    resp.usage.prompt_tokens = prompt_tokens
    resp.usage.completion_tokens = completion_tokens
    resp.usage.cost = None
    resp.usage.completion_tokens_details = MagicMock()
    resp.usage.completion_tokens_details.reasoning_tokens = reasoning_tokens
    resp.provider = provider
    resp.model = "some-model"
    return resp


_PRICING = {"in_min": 0.1, "in_max": 0.2, "out_min": 0.5, "out_max": 0.6, "endpoints": 2}


def test_classify_one_item_empty_then_valid_is_ok_with_empty_first_try(tmp_path):
    valid = json.dumps({
        "commune_name": "Las Condes", "region_hint": "Metropolitana", "family": "propiedad",
        "title_es": "t", "title_en": "t", "summary": "s", "confidence": 0.9,
    })
    client = MagicMock()
    client.chat.completions.create.side_effect = [_mock_resp(""), _mock_resp(valid)]

    with patch.object(classifier_mod, "_parse_content", wraps=classifier_mod._parse_content) as spy:
        res = ev._classify_one_item(
            client, "m", "openrouter", "enabled_false", None, "h", "d",
            tmp_path / "ledger.json", 0.50, _PRICING,
        )
    assert res["kind"] == "ok"
    assert res["empty_first_try"] == 1
    spy.assert_called_once()


def test_classify_one_item_empty_twice_is_transient_and_skips_parse(tmp_path):
    client = MagicMock()
    client.chat.completions.create.side_effect = [_mock_resp(""), _mock_resp("")]

    with patch.object(classifier_mod, "_parse_content", wraps=classifier_mod._parse_content) as spy:
        res = ev._classify_one_item(
            client, "m", "openrouter", "enabled_false", None, "h", "d",
            tmp_path / "ledger.json", 0.50, _PRICING,
        )
    assert res["kind"] == "transient"
    assert res["reason"] == "empty_after_recall"
    spy.assert_not_called()


def test_classify_one_item_finish_length_is_transient_and_skips_parse(tmp_path):
    valid = json.dumps({
        "commune_name": "Las Condes", "region_hint": "Metropolitana", "family": "propiedad",
        "title_es": "t", "title_en": "t", "summary": "s hope it helps", "confidence": 0.9,
    })
    client = MagicMock()
    client.chat.completions.create.return_value = _mock_resp(valid + " and some trailing prose", finish_reason="length")

    with patch.object(classifier_mod, "_parse_content", wraps=classifier_mod._parse_content) as spy:
        res = ev._classify_one_item(
            client, "m", "openrouter", "enabled_false", None, "h", "d",
            tmp_path / "ledger.json", 0.50, _PRICING,
        )
    assert res["kind"] == "transient"
    assert res["reason"] == "finish_length"
    spy.assert_not_called()


# ---------------------------------------------------------------------------
# End-to-end run_full: mocked client, mocked resolver, per_item rows
# ---------------------------------------------------------------------------


def _golden_items():
    return [
        {
            "id": "gs-001", "headline": "h1", "description": "d1",
            "ground_truth": {"commune_name": "Las Condes", "cut": "13114", "family": "propiedad"},
        },
        {
            "id": "gs-002", "headline": "h2", "description": "d2",
            "ground_truth": {"commune_name": None, "cut": None, "family": None},
        },
    ]


def test_run_full_end_to_end_calls_parse_content_once_per_item_and_records_fields(tmp_path):
    valid = json.dumps({
        "commune_name": "Las Condes", "region_hint": "Metropolitana", "family": "propiedad",
        "title_es": "t", "title_en": "t", "summary": "s", "confidence": 0.9,
    })
    null_resp = json.dumps({
        "commune_name": None, "region_hint": None, "family": "propiedad",
        "title_es": "t", "title_en": "t", "summary": "s", "confidence": 0.9,
    })
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _mock_resp(valid, prompt_tokens=120, completion_tokens=60, reasoning_tokens=0),
        _mock_resp(null_resp, prompt_tokens=110, completion_tokens=40, reasoning_tokens=0),
    ]

    with patch("pipeline.news.resolver.resolve_cut", return_value=("13114", "las-condes")) as mock_resolve, \
         patch.object(classifier_mod, "_parse_content", wraps=classifier_mod._parse_content) as spy:
        candidate = ev.run_full(
            client, "m", "openrouter", "enabled_false", _golden_items(),
            tmp_path / "ledger.json", 0.50, _PRICING,
        )

    assert spy.call_count == 2
    assert candidate["commune_correct"] == 1
    assert candidate["family_correct"] == 1
    assert candidate["parse_errors"] == 0
    assert candidate["status"] == "COMPLETE"
    row0 = candidate["per_item"][0]
    assert row0["prompt_tokens"] == 120
    assert row0["completion_tokens"] == 60
    assert row0["reasoning_tokens"] == 0
    assert row0["finish_reason"] == "stop"
    assert row0["served_by"] == "OpenRouterTest"
    mock_resolve.assert_called_once()


# ---------------------------------------------------------------------------
# --decide writes 34-AB-RESULTS.md with confusion matrix + served_by
# ---------------------------------------------------------------------------


def test_decide_writes_results_md_with_confusion_matrix_and_served_by(tmp_path, monkeypatch):
    out_dir = tmp_path / "ab"
    out_dir.mkdir()

    candidate = _mk_candidate(
        model="deepseek/deepseek-v4-flash", provider="openrouter",
        served_by_counts={"OpenRouterTest": 2},
        per_item=[
            {"id": "gs-001", "ground_truth_family": "propiedad", "predicted_family": "propiedad"},
        ],
    )
    (out_dir / "run-deepseek-deepseek-v4-flash.json").write_text(json.dumps(candidate), encoding="utf-8")

    results_json = tmp_path / "34-AB-RESULTS.json"
    results_md = tmp_path / "34-AB-RESULTS.md"
    monkeypatch.setattr(ev, "RESULTS_JSON", results_json)
    monkeypatch.setattr(ev, "RESULTS_MD", results_md)
    monkeypatch.setattr(ev, "fetch_catalog", lambda provider, model: {"endpoints": 2})

    result = ev.decide(out_dir, family_min_v2=FAMILY_MIN)

    assert results_json.exists()
    assert results_md.exists()
    md_text = results_md.read_text(encoding="utf-8")
    assert "propiedad" in md_text
    assert "OpenRouterTest" in md_text
    assert result["decision"]["status"] == "WINNER"
    assert "\"decision\"" in results_json.read_text(encoding="utf-8")
