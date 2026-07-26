"""
pipeline/tests/test_classifier.py

Tests for pipeline/news/classifier.py — classification with mocked API.
The configured LLM provider is NEVER called live — all responses mocked via unittest.mock.patch.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.news import classifier as classifier_mod  # type: ignore
from pipeline.news.classifier import classify  # type: ignore

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


def test_default_provider_is_openrouter():
    """With NEWS_PROVIDER unset, the module must default to openrouter/ibm-granite/granite-4.1-8b."""
    assert classifier_mod._PROVIDER == "openrouter", (
        f"Expected _PROVIDER='openrouter', got {classifier_mod._PROVIDER!r}"
    )
    assert classifier_mod._MODEL == "ibm-granite/granite-4.1-8b", (
        f"Expected _MODEL='ibm-granite/granite-4.1-8b', got {classifier_mod._MODEL!r}"
    )
