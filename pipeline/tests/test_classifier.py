"""
pipeline/tests/test_classifier.py

Tests for pipeline/news/classifier.py — classification with mocked API.
The configured LLM provider is NEVER called live — all responses mocked via unittest.mock.patch.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from openai import NotFoundError

from pipeline.news import classifier as classifier_mod  # type: ignore
from pipeline.news.classifier import SYSTEM_PROMPT, classify  # type: ignore
from pipeline.news.classifier import _parse_content, _request_completion  # type: ignore

def _make_mock_response(data: dict) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = json.dumps(data)
    return mock_resp


# Base valid response using commune_name + region_hint (NEWS-01 redesign)
_VALID_RESPONSE = {
    "commune_name": "Las Condes",
    "region_hint": "Metropolitana",
    "family": "propiedad",
    "title_es": "Robo en Las Condes",
    "title_en": "Robbery in Las Condes",
    "summary": "A robbery occurred in Las Condes.",
    "confidence": 0.9,
}


# ---------------------------------------------------------------------------
# Test functions (NEWS-01 redesign behaviors)
# ---------------------------------------------------------------------------


def test_name_emit_passes_through():
    """Classifier returns ClassifierOutput with commune_name when LLM emits name+region_hint."""
    data = dict(_VALID_RESPONSE)

    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(data)
        result = classify("Robo en Las Condes", "Descripción del robo")

    assert result is not None, "Expected ClassifierOutput for valid response"
    assert result.commune_name == "Las Condes"
    assert result.region_hint == "Metropolitana"


def test_null_commune_name_allowed():
    """Classifier accepts null commune_name without crashing (location unknown path)."""
    data = dict(_VALID_RESPONSE, commune_name=None, region_hint=None, confidence=0.9)

    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(data)
        result = classify("Noticia sin ubicación", "Sin lugar específico")

    # Must not raise; confidence 0.9 means it passes the gate
    # The result may be a ClassifierOutput with commune_name=None
    assert result is not None
    assert result.commune_name is None


def test_low_confidence_still_rejected():
    """Classifier must return None when confidence < threshold (0.6)."""
    data = dict(_VALID_RESPONSE, confidence=0.3)

    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(data)
        result = classify("Robo en Santiago", "Descripción del robo")
    assert result is None, "Expected None for low-confidence classifier response"


def test_invalid_family_rejected():
    """Classifier must return None when the LLM responds with an unknown family key."""
    data = dict(_VALID_RESPONSE, family="banana")

    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(data)
        result = classify("Robo en Santiago", "Descripción del robo")
    assert result is None, "Expected None for invalid family key"


def test_family_internal_whitespace_normalized():
    """Granite 4.1 8B tokenizer artifact: 'robos_ violentos' must be normalized to 'robos_violentos'."""
    data = dict(_VALID_RESPONSE, family="robos_ violentos", confidence=0.9)

    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(data)
        result = classify("Robo violento en Santiago", "Descripción de robo violento")

    assert result is not None, "Expected ClassifierOutput after family whitespace normalization"
    assert result.family == "robos_violentos", f"Expected 'robos_violentos', got {result.family!r}"


def test_sexuales_family_classify_returns_valid_output():
    """classify() must return ClassifierOutput with family='sexuales' when LLM emits it (j6z Task 1)."""
    data = dict(_VALID_RESPONSE, family="sexuales", confidence=0.9,
                title_es="Hombre detenido por violacion en Valparaiso",
                title_en="Man arrested for rape in Valparaiso",
                summary="A man was arrested for rape in Valparaiso.")

    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(data)
        result = classify("Hombre detenido por violacion en Valparaiso", "Arrestado por delito sexual")

    assert result is not None, "Expected ClassifierOutput for sexuales family"
    assert result.family == "sexuales"


def test_default_provider_matches_model_config():
    """NREC-02 (BF-01): with NEWS_PROVIDER / NEWS_MODEL unset, the module defaults come
    from pipeline/news/model_config.py (34-01 A/B decision), never the delisted id."""
    from pipeline.news import model_config

    assert classifier_mod._PROVIDER == model_config.DEFAULT_PROVIDER
    if model_config.DEFAULT_PROVIDER == "openrouter":
        assert classifier_mod._MODEL == model_config.DEFAULT_OPENROUTER_MODEL
    else:  # G-08 DEEPSEEK_DIRECT
        assert model_config.DEFAULT_PROVIDER == "deepseek"
        assert classifier_mod._MODEL == "deepseek-v4-flash"
    assert "granite-4.1" not in classifier_mod._MODEL


# ---------------------------------------------------------------------------
# Seam tests (34-01 Task 1): _parse_content, _request_completion
# ---------------------------------------------------------------------------


def test_parse_content_none_and_empty_are_parse_error():
    assert _parse_content(None, "t") == ("parse_error", None)
    assert _parse_content("", "t") == ("parse_error", None)


def test_parse_content_non_object_json_is_parse_error():
    # 34-PREPUSH-REVIEW CR-01: valid JSON that is not an object must not raise.
    for raw in ('[{"commune_name": null}]', "null", '"x"', "42"):
        assert _parse_content(raw, "t") == ("parse_error", None)


def test_parse_content_fenced_valid_json_is_ok():
    data = dict(_VALID_RESPONSE, confidence=0.9)
    raw = "```json\n" + json.dumps(data) + "\n```"
    kind, out = _parse_content(raw, "t")
    assert kind == "ok"
    assert out is not None
    assert out.confidence == 0.9


def test_parse_content_low_confidence():
    data = dict(_VALID_RESPONSE, confidence=0.3)
    raw = json.dumps(data)
    kind, out = _parse_content(raw, "t")
    assert kind == "low_conf"
    assert out is not None
    assert out.confidence == 0.3


def test_parse_content_invalid_family_is_parse_error():
    data = dict(_VALID_RESPONSE, family="banana")
    kind, out = _parse_content(json.dumps(data), "t")
    assert kind == "parse_error"
    assert out is None


def test_parse_content_not_json_is_parse_error():
    kind, out = _parse_content("not json", "t")
    assert kind == "parse_error"
    assert out is None


def test_parse_content_r03_prose_wrapped_json_recovers():
    """R-03: json.loads fails on the whole text; a second attempt parses the first
    balanced top-level {...} object (string-aware brace counting)."""
    data = dict(_VALID_RESPONSE, confidence=0.9)
    raw = "Here is the JSON: " + json.dumps(data) + " hope it helps"
    kind, out = _parse_content(raw, "t")
    assert kind == "ok"
    assert out is not None


def test_parse_content_r03_unbalanced_object_is_parse_error():
    kind, out = _parse_content('{"a": 1', "t")
    assert kind == "parse_error"
    assert out is None


def test_parse_content_family_internal_whitespace_normalized():
    data = dict(_VALID_RESPONSE, family="robos_ violentos", confidence=0.9)
    kind, out = _parse_content(json.dumps(data), "t")
    assert kind == "ok"
    assert out is not None
    assert out.family == "robos_violentos"


def test_request_completion_openrouter_kwargs():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = "resp"

    result = _request_completion(
        mock_client, "m/x", "openrouter", "u", {"reasoning": {"enabled": False}}
    )

    assert result == "resp"
    mock_client.chat.completions.create.assert_called_once_with(
        model="m/x",
        temperature=0.0,
        max_tokens=512,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "u"},
        ],
        extra_body={"reasoning": {"enabled": False}},
    )


def test_request_completion_deepseek_adds_response_format():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = "resp"

    _request_completion(mock_client, "deepseek-v4-flash", "deepseek", "u", None)

    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["response_format"] == {"type": "json_object"}
    assert "extra_body" not in kwargs


def test_request_completion_extra_body_none_omits_kwarg():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = "resp"

    _request_completion(mock_client, "m/x", "openrouter", "u", None)

    _, kwargs = mock_client.chat.completions.create.call_args
    assert "extra_body" not in kwargs


def test_request_completion_propagates_not_found_error():
    mock_client = MagicMock()
    request = httpx.Request("POST", "https://x")
    response = httpx.Response(404, request=request)
    mock_client.chat.completions.create.side_effect = NotFoundError(
        "not found", response=response, body=None
    )

    with pytest.raises(NotFoundError):
        _request_completion(mock_client, "m/x", "openrouter", "u", None)


# ---------------------------------------------------------------------------
# 36-06 Part A (FID-01): headline fidelity — the LLM no longer authors title_es
# ---------------------------------------------------------------------------

_V3_GOLDEN = Path(__file__).parent / "fixtures" / "golden_set_v3.json"


def test_system_prompt_has_no_title_es_and_faithful_title_en():
    assert "title_es" not in SYSTEM_PROMPT
    assert SYSTEM_PROMPT.count('"title_en"') == 1
    assert "faithful English translation of the HEADLINE" in SYSTEM_PROMPT
    assert "family-relationship term" in SYSTEM_PROMPT
    assert "name" in SYSTEM_PROMPT
    assert "omit a trailing ' - <outlet name>'" in SYSTEM_PROMPT
    # DeepSeek JSON mode requires the word "json" in the prompt.
    assert "json" in SYSTEM_PROMPT.lower()


def test_parse_content_without_title_es_is_ok():
    data = {k: v for k, v in _VALID_RESPONSE.items() if k != "title_es"}
    kind, out = _parse_content(json.dumps(data), "t")
    assert kind == "ok"
    assert out is not None
    assert not hasattr(out, "title_es")
    assert out.title_en == "Robbery in Las Condes"


def test_shingle_guard_v3_items_vs_prompt_rules_text():
    """Premortem R-07 / T-36-16: no normalized 5-word shingle of any v3
    headline or description occurs in the prompt RULES text."""
    from pipeline.tests.shingle_guard import prompt_rules_text, shared_shingles

    rules_text = prompt_rules_text(SYSTEM_PROMPT, classifier_mod._COMMUNE_LIST_STR)
    items = json.loads(_V3_GOLDEN.read_text(encoding="utf-8"))
    assert len(items) > 0
    collisions = {}
    for it in items:
        for field in ("headline", "description"):
            shared = shared_shingles(it.get(field) or "", rules_text, n=5)
            if shared:
                collisions[(it["id"], field)] = sorted(shared)
    assert collisions == {}


def test_shingle_guard_scope_excludes_commune_block_and_schema_block():
    from pipeline.tests.shingle_guard import normalize, prompt_rules_text

    rules_text = prompt_rules_text(SYSTEM_PROMPT, classifier_mod._COMMUNE_LIST_STR)
    assert normalize("san pedro de la paz") in normalize(SYSTEM_PROMPT)
    assert normalize("san pedro de la paz") not in normalize(rules_text)
    assert '"commune_name": "<' in SYSTEM_PROMPT
    assert '"commune_name": "<' not in rules_text
    assert '"title_en": "<' not in rules_text
    assert "Rules:" in rules_text
