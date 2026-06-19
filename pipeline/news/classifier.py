"""
pipeline/news/classifier.py

Provider-configurable closed-list classifier for Chilean crime news (NEWS-02).

Provider selection:
  - Set NEWS_PROVIDER=deepseek (default) or NEWS_PROVIDER=minimax in environment.
  - DeepSeek: OpenAI client → api.deepseek.com; model deepseek-v4-flash; response_format json_object.
  - MiniMax:  OpenAI client → api.minimaxi.chat/v1; model MiniMax-Text-01; NO response_format
              (json_object returns HTTP 400 on MiniMax); JSON is parsed from content string
              after stripping optional markdown fences.

Anti-hallucination guards (NEWS-01 redesign):
- temperature = 0.0 for both providers
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
import re

from openai import AuthenticationError, OpenAI, RateLimitError
from openai import APIStatusError as _APIStatusError
from pydantic import ValidationError

from pipeline.news.schema import VALID_FAMILIES, ClassifierOutput
from pipeline.shared.schema import FAMILY_KEYS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLD: float = 0.6  # D-07 / RESEARCH A3

# ---------------------------------------------------------------------------
# Provider selection (NEWS_PROVIDER env var)
# ---------------------------------------------------------------------------

_PROVIDER: str = os.environ.get("NEWS_PROVIDER", "deepseek").lower()

if _PROVIDER == "minimax":
    client = OpenAI(
        api_key=os.environ.get("MINIMAX_API_KEY", ""),
        base_url="https://api.minimaxi.chat/v1",
    )
    _MODEL: str = "MiniMax-Text-01"
else:
    # Default: deepseek
    _PROVIDER = "deepseek"
    client = OpenAI(
        api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        base_url="https://api.deepseek.com",
    )
    _MODEL = "deepseek-v4-flash"

# ---------------------------------------------------------------------------
# Build commune list once at module load — one entry per line:
# "<name> (region_id:<region_id>)"
# ---------------------------------------------------------------------------

_INDEX_FILE = pathlib.Path(__file__).parents[2] / "data" / "cead" / "meta" / "index.json"
if not _INDEX_FILE.exists():
    raise FileNotFoundError(
        f"index.json not found at {_INDEX_FILE}. "
        "Run the CEAD scraper first (python pipeline/scrape_cead.py) to generate "
        "data/cead/meta/index.json before importing the classifier."
    )
_INDEX: list[dict] = json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
_COMMUNE_LIST_STR: str = "\n".join(
    f"{entry['name']} (region_id:{entry['region_id']})" for entry in _INDEX
)

# FAMILY_KEYS as comma-joined enum string for the prompt
_FAMILY_ENUM_STR: str = ", ".join(FAMILY_KEYS)

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

# Regex to strip markdown JSON fences (used for MiniMax which omits response_format)
_JSON_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


# ---------------------------------------------------------------------------
# Classifier function
# ---------------------------------------------------------------------------

def classify(title: str, description: str) -> ClassifierOutput | None:
    """Classify a news item using the configured LLM provider (NEWS_PROVIDER).

    Returns a validated ClassifierOutput on success.
    Returns None if:
    - API call fails
    - Response JSON is malformed or empty
    - confidence < CONFIDENCE_THRESHOLD
    - family is not a valid FAMILY_KEY (Pydantic rejects)

    commune_name→CUT resolution is handled downstream by pipeline/news/resolver.py.
    This function no longer rejects on CUT membership — the LLM emits a name, not a CUT.

    The LLM client is NEVER called in unit tests — mock `pipeline.news.classifier.client`.
    """
    user_content = f"HEADLINE: {title}\nSUMMARY: {description[:500]}"

    # First attempt
    raw = _call_api(user_content)
    if raw is None:
        # Empty-content retry (Pitfall 4)
        logger.warning("Empty %s response for %r — retrying once", _PROVIDER, title[:60])
        raw = _call_api(user_content)
    if raw is None:
        return None

    # Parse JSON (strip markdown fences for MiniMax)
    raw_stripped = _strip_json_fence(raw)
    try:
        data = json.loads(raw_stripped)
    except json.JSONDecodeError as exc:
        logger.warning("JSONDecodeError from %s for %r: %s", _PROVIDER, title[:60], exc)
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


def _strip_json_fence(raw: str) -> str:
    """Remove optional ```json ... ``` fences from LLM output (MiniMax may emit these)."""
    m = _JSON_FENCE_RE.match(raw)
    return m.group(1) if m else raw


def _call_api(user_content: str) -> str | None:
    """Make one API call to the configured provider. Returns the content string or None."""
    try:
        kwargs: dict = dict(
            model=_MODEL,
            temperature=0.0,
            max_tokens=512,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        # DeepSeek supports response_format=json_object; MiniMax returns HTTP 400 on it
        if _PROVIDER == "deepseek":
            kwargs["response_format"] = {"type": "json_object"}

        resp = client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content
        return content if content else None
    except AuthenticationError:
        logger.error(
            "%s API call: authentication failed — check %s_API_KEY",
            _PROVIDER, _PROVIDER.upper(),
        )
        return None
    except RateLimitError:
        logger.warning("%s API call: rate limited — will retry next run", _PROVIDER)
        return None
    except _APIStatusError as exc:
        logger.warning(
            "%s API call failed HTTP %s: %s", _PROVIDER, exc.status_code, exc.message
        )
        return None
    except Exception as exc:
        logger.warning("%s API call failed (unexpected): %s: %s", _PROVIDER, type(exc).__name__, exc)
        return None
