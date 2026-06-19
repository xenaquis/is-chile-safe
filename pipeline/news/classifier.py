"""
pipeline/news/classifier.py

DeepSeek v4-flash closed-list classifier for Chilean crime news (NEWS-02).

Anti-hallucination guards (NEWS-01 redesign):
- model = deepseek-v4-flash, temperature = 0.0
- response_format = {"type": "json_object"} (only supported type in DeepSeek)
- LLM emits commune_name (Spanish name) + region_hint — NOT a bare CUT code
- CUT resolution happens in pipeline/news/resolver.py (deterministic, closed-set)
- confidence must be >= CONFIDENCE_THRESHOLD or item is rejected
- LLM never emits coordinates — use centroids.py for pin lat/lng (D-08)
"""
from __future__ import annotations

import json
import logging
import os
import pathlib

from openai import OpenAI
from pydantic import ValidationError

from pipeline.news.schema import VALID_FAMILIES, ClassifierOutput
from pipeline.shared.schema import FAMILY_KEYS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLD: float = 0.6  # D-07 / RESEARCH A3

# Build the commune list string once at module load — one entry per line:
# "<name> (region_id:<region_id>)"
# This gives the LLM correct Spanish spellings to choose from.
_INDEX_FILE = pathlib.Path(__file__).parents[2] / "data" / "cead" / "meta" / "index.json"
_INDEX: list[dict] = json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
_COMMUNE_LIST_STR: str = "\n".join(
    f"{entry['name']} (region_id:{entry['region_id']})" for entry in _INDEX
)

# FAMILY_KEYS as comma-joined enum string for the prompt
_FAMILY_ENUM_STR: str = ", ".join(FAMILY_KEYS)

# ---------------------------------------------------------------------------
# OpenAI client wired to DeepSeek API (V2 — key from env only, never hardcoded)
# ---------------------------------------------------------------------------

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
    base_url="https://api.deepseek.com",
)

# ---------------------------------------------------------------------------
# System prompt (MUST contain the word "json" per DeepSeek JSON mode docs)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT: str = f"""You are a Chilean crime news classifier. You respond in json only.

Given a news headline and summary, output exactly this JSON structure:
{{
  "commune_name": "<exact Spanish commune name from CHILEAN COMMUNES below, or null if location unknown>",
  "region_hint": "<region name or number hint to disambiguate, or null>",
  "family": "<one of: {_FAMILY_ENUM_STR}>",
  "title_es": "<concise Spanish headline, max 120 chars, plain text>",
  "title_en": "<English translation of title_es, max 120 chars, plain text>",
  "summary": "<1-2 sentence neutral summary in English, plain text>",
  "confidence": <float 0.0-1.0 indicating location identification confidence>
}}

CHILEAN COMMUNES (346 entries — commune_name MUST be spelled exactly as below or null):
{_COMMUNE_LIST_STR}

Rules:
- commune_name MUST be exactly a commune name from the list above, spelled in Spanish, or null.
- NEVER invent or approximate a commune name. Copy it character-for-character from the list.
- region_hint helps disambiguate; set to the region number or name from the list entry if known.
- If the article is not about a crime incident, set commune_name to null and confidence to 0.0.
- family MUST be exactly one of: {_FAMILY_ENUM_STR}
- Output plain text only for title_es, title_en, and summary — no HTML, no markdown.
"""


# ---------------------------------------------------------------------------
# Classifier function
# ---------------------------------------------------------------------------

def classify(title: str, description: str) -> ClassifierOutput | None:
    """Classify a news item using DeepSeek v4-flash.

    Returns a validated ClassifierOutput on success.
    Returns None if:
    - API call fails
    - Response JSON is malformed or empty
    - confidence < CONFIDENCE_THRESHOLD
    - family is not a valid FAMILY_KEY (Pydantic rejects)

    commune_name→CUT resolution is handled downstream by pipeline/news/resolver.py.
    This function no longer rejects on CUT membership — the LLM emits a name, not a CUT.

    DeepSeek is NEVER called in unit tests — mock `pipeline.news.classifier.client`.
    """
    user_content = f"HEADLINE: {title}\nSUMMARY: {description[:500]}"

    # First attempt
    raw = _call_api(user_content)
    if raw is None:
        # Empty-content retry (Pitfall 4)
        logger.warning("Empty DeepSeek response for %r — retrying once", title[:60])
        raw = _call_api(user_content)
    if raw is None:
        return None

    # Parse JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("JSONDecodeError from DeepSeek for %r: %s", title[:60], exc)
        return None

    # Validate with Pydantic (rejects invalid family, missing fields, etc.)
    try:
        result = ClassifierOutput.model_validate(data)
    except ValidationError as exc:
        logger.warning("ClassifierOutput validation failed for %r: %s", title[:60], exc)
        return None

    # Reject if confidence below threshold (D-07)
    # NOTE: commune_name→CUT resolution (anti-hallucination) happens downstream in resolver.py
    if result.confidence < CONFIDENCE_THRESHOLD:
        logger.warning(
            "Rejected: confidence=%.2f < %.2f for %r",
            result.confidence,
            CONFIDENCE_THRESHOLD,
            title[:60],
        )
        return None

    return result


def _call_api(user_content: str) -> str | None:
    """Make one API call. Returns the content string or None on any failure."""
    try:
        resp = client.chat.completions.create(
            model="deepseek-v4-flash",
            temperature=0.0,
            max_tokens=512,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        content = resp.choices[0].message.content
        return content if content else None
    except Exception as exc:
        logger.warning("DeepSeek API call failed: %s", exc)
        return None
