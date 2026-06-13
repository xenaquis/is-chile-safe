"""
pipeline/tests/test_classifier.py

Tests for pipeline/news/classifier.py — DeepSeek classification with mocked API.
Wave-1 scaffold: skips if pipeline.news.classifier is not yet implemented.
DeepSeek NEVER called live — all responses mocked via unittest.mock.patch.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Skip entire module if Wave-1 module not yet implemented
try:
    from pipeline.news import classifier as classifier_mod  # type: ignore
    from pipeline.news.classifier import classify  # type: ignore
    _MODULE_AVAILABLE = True
except ImportError:
    _MODULE_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _MODULE_AVAILABLE,
    reason="pipeline.news.classifier not yet implemented (Wave 1)",
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_sample() -> dict:
    p = FIXTURES_DIR / "deepseek_response_sample.json"
    if not p.exists():
        pytest.skip("deepseek_response_sample.json not present")
    return json.loads(p.read_text(encoding="utf-8"))


def _make_mock_response(data: dict) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = json.dumps(data)
    return mock_resp


# ---------------------------------------------------------------------------
# Test functions (exact names per 05-VALIDATION.md)
# ---------------------------------------------------------------------------


def test_invalid_cut_rejected():
    """Classifier must return None when the LLM responds with a CUT not in 346 set."""
    sample = _load_sample()
    bad = dict(sample, commune_cut="99999")  # not a valid CUT

    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(bad)
        result = classify("Robo en Santiago", "Descripción del robo")
    assert result is None, "Expected None for CUT not in 346-commune set"


def test_low_confidence_rejected():
    """Classifier must return None when confidence < threshold (0.6)."""
    sample = _load_sample()
    low_conf = dict(sample, confidence=0.3)

    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(low_conf)
        result = classify("Robo en Santiago", "Descripción del robo")
    assert result is None, "Expected None for low-confidence classifier response"


def test_invalid_family():
    """Classifier must return None when the LLM responds with an unknown family key."""
    sample = _load_sample()
    bad_family = dict(sample, family="banditry")

    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(bad_family)
        result = classify("Robo en Santiago", "Descripción del robo")
    assert result is None, "Expected None for invalid family key"
