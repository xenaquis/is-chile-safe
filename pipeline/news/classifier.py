"""
pipeline/news/classifier.py

DeepSeek v4-flash closed-list classifier for Chilean crime news (NEWS-02).

Anti-hallucination guards:
- model = deepseek-v4-flash, temperature = 0.0
- response_format = {"type": "json_object"} (only supported type in DeepSeek)
- commune_cut must be in 346-CUT set or item is rejected
- confidence must be >= CONFIDENCE_THRESHOLD or item is rejected
- LLM never emits coordinates — use centroids.py for pin lat/lng (D-08)
"""
from __future__ import annotations

import json
import logging
import os

from openai import OpenAI
from pydantic import ValidationError

from pipeline.news.schema import VALID_CUTS, VALID_FAMILIES, ClassifierOutput
from pipeline.shared.schema import FAMILY_KEYS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLD: float = 0.6  # D-07 / RESEARCH A3

# Build the CUT list string once at module load (comma-joined, codes only — no names)
_CUT_LIST_STR: str = ",".join(sorted(VALID_CUTS))

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
  "commune_cut": "<5-digit CUT code from VALID_CUTS below, or null if location unknown>",
  "family": "<one of: {_FAMILY_ENUM_STR}>",
  "title_es": "<concise Spanish headline, max 120 chars, plain text>",
  "title_en": "<English translation of title_es, max 120 chars, plain text>",
  "summary": "<1-2 sentence neutral summary in English, plain text>",
  "confidence": <float 0.0-1.0 indicating location identification confidence>
}}

VALID_CUTS (346 Chilean commune CUT codes — commune_cut MUST be from this list or null):
{_CUT_LIST_STR}

Rules:
- commune_cut MUST be from VALID_CUTS exactly, or null if location unknown or not a crime item.
- family MUST be exactly one of: {_FAMILY_ENUM_STR}
- If the article is not about a crime incident, set commune_cut to null and confidence to 0.0.
- NEVER invent CUT codes. Only use codes from VALID_CUTS.
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
    - commune_cut is not in the 346-CUT set
    - confidence < CONFIDENCE_THRESHOLD
    - family is not a valid FAMILY_KEY (Pydantic rejects)

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

    # Reject if commune_cut not in 346-CUT set (T-05-02-01 anti-hallucination)
    if result.commune_cut is not None and result.commune_cut not in VALID_CUTS:
        logger.warning(
            "Rejected: commune_cut=%r not in 346-CUT set (title=%r)",
            result.commune_cut,
            title[:60],
        )
        return None

    # Reject if confidence below threshold (D-07)
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
