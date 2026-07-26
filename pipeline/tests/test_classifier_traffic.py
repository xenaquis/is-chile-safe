"""
pipeline/tests/test_classifier_traffic.py

Regression tests for traffic-accident exclusion in the news classifier (P1-6 pipeline).

The configured LLM provider is NEVER called live — all API responses are mocked via unittest.mock.patch.
Ensures that when the LLM correctly emits confidence=0.0 for a traffic-collision headline,
classify() returns None (rejected by the CONFIDENCE_THRESHOLD gate).
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from pipeline.news import classifier as classifier_mod  # type: ignore
from pipeline.news.classifier import classify, SYSTEM_PROMPT  # type: ignore


def _make_mock_response(data: dict) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = json.dumps(data)
    return mock_resp


# ---------------------------------------------------------------------------
# Traffic-accident exclusion tests
# ---------------------------------------------------------------------------


def test_traffic_accident_rejected():
    """When LLM emits vida-classified collision with confidence=0.0, classify() returns None."""
    traffic_response = {
        "commune_name": "Carahue",
        "region_hint": "La Araucanía",
        "family": "vida",
        "title_es": "Colisión deja al menos un muerto en Carahue",
        "title_en": "Collision leaves at least one dead in Carahue",
        "summary": "A road collision on Route 5 South near Carahue resulted in at least one fatality.",
        "confidence": 0.0,
    }

    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(traffic_response)
        result = classify(
            "Colisión deja al menos un muerto en Carahue",
            "Un accidente de tránsito en la Ruta 5 Sur dejó al menos un fallecido.",
        )

    assert result is None, (
        "Expected None for traffic accident with confidence=0.0 "
        "(rejected by CONFIDENCE_THRESHOLD gate)"
    )


def test_zero_confidence_traffic_rejected():
    """Any classification with confidence=0.0 is rejected regardless of family."""
    atropello_response = {
        "commune_name": None,
        "region_hint": None,
        "family": "vida",
        "title_es": "Atropello fatal en avenida principal",
        "title_en": "Fatal pedestrian hit on main avenue",
        "summary": "A pedestrian was struck and killed by a vehicle on a major road.",
        "confidence": 0.0,
    }

    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(atropello_response)
        result = classify(
            "Atropello fatal en avenida principal",
            "Un peatón fue atropellado y murió en escena.",
        )

    assert result is None, "Expected None for zero-confidence traffic event"


def test_system_prompt_contains_traffic_exclusion():
    """SYSTEM_PROMPT must contain the traffic-accident exclusion rule."""
    keywords = ["traffic", "tránsito", "colisión"]
    found = any(kw.lower() in SYSTEM_PROMPT.lower() for kw in keywords)
    assert found, (
        f"SYSTEM_PROMPT must contain at least one of {keywords} "
        "to enforce traffic-accident exclusion rule"
    )
