"""
pipeline/news/classifier.py

Provider-configurable closed-list classifier for Chilean crime news (NEWS-02).

Provider selection (NEWS_PROVIDER env var):
  - OpenRouter (DEFAULT, unset or "openrouter"): OpenAI client → openrouter.ai/api/v1;
    model ibm-granite/granite-4.1-8b; NO response_format (JSON from fence-stripping path).
    Validated in spike 008: 100% commune accuracy, parity on family, 0% parse failures,
    ~6x cheaper, ~2.5x faster than DeepSeek. OPENROUTER_API_KEY required.
  - DeepSeek ("deepseek"): OpenAI client → api.deepseek.com; model deepseek-v4-flash;
    response_format json_object. DEEPSEEK_API_KEY required.
  - MiniMax ("minimax"): OpenAI client → api.minimaxi.chat/v1; model MiniMax-Text-01;
    NO response_format (json_object returns HTTP 400 on MiniMax); JSON is parsed from
    content string after stripping optional markdown fences. MINIMAX_API_KEY required.

Family whitespace normalization:
  Granite 4.1 8B may emit a tokenizer artifact like "robos_ violentos" (internal space
  after underscore). classify() collapses internal whitespace in the family value after
  json.loads and before Pydantic validation, so "robos_ violentos" → "robos_violentos".
  Guard is defensive: only applied when family is a str; None/missing untouched.
  (Spike 008 artifact — see .planning/spikes/008-granite-openrouter-classifier/README.md)

Anti-hallucination guards (NEWS-01 redesign):
- temperature = 0.0 for all providers
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

_PROVIDER: str = os.environ.get("NEWS_PROVIDER", "openrouter").lower()

if _PROVIDER == "deepseek":
    client = OpenAI(
        api_key=os.environ.get("DEEPSEEK_API_KEY", "placeholder"),
        base_url="https://api.deepseek.com",
    )
    _MODEL: str = "deepseek-v4-flash"
elif _PROVIDER == "minimax":
    client = OpenAI(
        api_key=os.environ.get("MINIMAX_API_KEY", "placeholder"),
        base_url="https://api.minimaxi.chat/v1",
    )
    _MODEL = "MiniMax-Text-01"
else:
    # Default: openrouter (ibm-granite/granite-4.1-8b — spike 008 validated)
    _PROVIDER = "openrouter"
    client = OpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", "placeholder"),
        base_url="https://openrouter.ai/api/v1",
    )
    _MODEL = "ibm-granite/granite-4.1-8b"

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

# FAMILY_KEYS as comma-joined enum string for CEAD internal use.
_FAMILY_ENUM_STR: str = ", ".join(FAMILY_KEYS)

# NEWS-ONLY enum for the classifier prompt: adds "sexuales" to the 7 CEAD families.
# "sexuales" has no CEAD rate; it is a news-incident-only classification bucket.
_NEWS_FAMILY_ENUM_STR: str = ", ".join([*FAMILY_KEYS, "sexuales"])

# ---------------------------------------------------------------------------
# System prompt (MUST contain the word "json" per DeepSeek JSON mode docs)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT: str = f"""You are a Chilean crime news classifier. You respond in json only.

Given a news headline and summary, output exactly this JSON structure:
{{
  "commune_name": "<exact Spanish commune name from CHILEAN COMMUNES below, or null if location unknown>",
  "region_hint": "<region name or number hint to disambiguate, or null>",
  "family": "<one of: {_NEWS_FAMILY_ENUM_STR}>",
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
- Traffic accidents, road collisions, and vehicle crashes are NOT crime incidents even if they result in fatalities. If an article is primarily about a traffic accident (colisión, accidente de tránsito, choque, atropello sin culpa criminal), you MUST set confidence to 0.0.
- Sexual crimes (violacion, abuso sexual, estupro, grooming, pornografia infantil, acoso sexual, agresion sexual, delitos de connotacion sexual) MUST use family "sexuales", NOT "vida". Exception: if the incident is a killing (homicidio, femicidio) the family stays "vida" even when a sexual assault accompanied the death — death dominates classification.
- family MUST be exactly one of: {_NEWS_FAMILY_ENUM_STR}
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

    kind, result = _parse_content(raw, title)
    if kind == "ok":
        return result
    if kind == "low_conf":
        logger.warning(
            "Rejected: confidence below %.2f for %r",
            CONFIDENCE_THRESHOLD,
            title[:60],
        )
        return None
    return None


def _strip_json_fence(raw: str) -> str:
    """Remove optional ```json ... ``` fences from LLM output (MiniMax may emit these)."""
    m = _JSON_FENCE_RE.match(raw)
    return m.group(1) if m else raw


def _extract_balanced_object(text: str) -> str | None:
    """Extract the first balanced top-level {...} object from text (R-03).

    String- and escape-aware brace counting: braces inside JSON string literals
    (including escaped quotes) are not counted. Returns None if no balanced
    top-level object is found.
    """
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _parse_content(raw: str | None, title: str) -> tuple[str, ClassifierOutput | None]:
    """Production parse path, shared by classify() and the eval runner (34-01).

    Returns:
    - ("parse_error", None): raw is None/empty, JSON cannot be decoded (even after
      the R-03 balanced-object recovery attempt), or Pydantic validation fails.
    - ("low_conf", out): validated but confidence < CONFIDENCE_THRESHOLD.
    - ("ok", out): validated and confidence >= CONFIDENCE_THRESHOLD.
    """
    if not raw:
        return "parse_error", None

    raw_stripped = _strip_json_fence(raw)
    try:
        data = json.loads(raw_stripped)
    except json.JSONDecodeError:
        # R-03: try recovering the first balanced top-level {...} object before
        # giving up. Shared by the eval runner (34-01) and production so both
        # parse identically.
        recovered = _extract_balanced_object(raw_stripped)
        if recovered is None:
            logger.warning("JSONDecodeError from %s for %r", _PROVIDER, title[:60])
            return "parse_error", None
        try:
            data = json.loads(recovered)
        except json.JSONDecodeError as exc:
            logger.warning("JSONDecodeError from %s for %r: %s", _PROVIDER, title[:60], exc)
            return "parse_error", None

    # Normalize family whitespace before Pydantic validation.
    # Granite 4.1 8B tokenizer artifact: "robos_ violentos" → "robos_violentos".
    # Guard is defensive — only applied when family is a non-empty str.
    if isinstance(data.get("family"), str):
        data["family"] = "".join(data["family"].split())

    # Validate with Pydantic (rejects invalid family, missing fields, etc.)
    try:
        result = ClassifierOutput.model_validate(data)
    except ValidationError as exc:
        logger.warning("ClassifierOutput validation failed for %r: %s", title[:60], exc)
        return "parse_error", None

    if result.confidence < CONFIDENCE_THRESHOLD:
        return "low_conf", result

    return "ok", result


def _request_completion(
    client_: "OpenAI",
    model: str,
    provider: str,
    user_content: str,
    extra_body: dict | None = None,
):
    """One chat.completions.create call with the production kwargs.

    Returns the raw response object. RAISES openai exceptions (no swallowing) —
    the caller (production `_call_api` or the eval runner) is responsible for
    exception handling.
    """
    kwargs: dict = dict(
        model=model,
        temperature=0.0,
        max_tokens=512,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )
    # DeepSeek supports response_format=json_object; OpenRouter and MiniMax omit it
    # (OpenRouter uses fence-stripping path; MiniMax returns HTTP 400 on json_object)
    if provider == "deepseek":
        kwargs["response_format"] = {"type": "json_object"}
    if extra_body is not None:
        kwargs["extra_body"] = extra_body

    return client_.chat.completions.create(**kwargs)


def _call_api(user_content: str) -> str | None:
    """Make one API call to the configured provider. Returns the content string or None."""
    try:
        resp = _request_completion(client, _MODEL, _PROVIDER, user_content, None)
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
