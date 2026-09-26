"""
pipeline/news/classifier.py

Provider-configurable closed-list classifier for Chilean crime news (NEWS-02),
hardened in Phase 34-02 (NREC-02..06) so that a provider/model failure is loud and
non-destructive.

Model selection (NREC-02) — ids live in pipeline/news/model_config.py (34-01 A/B
decision G-16); env overrides need no code edit (an empty string, i.e. an unset repo
variable, falls back to the default — R-09):
  - NEWS_PROVIDER (default model_config.DEFAULT_PROVIDER = "openrouter"):
      * "openrouter": OpenAI client → openrouter.ai/api/v1; model NEWS_MODEL or
        model_config.DEFAULT_OPENROUTER_MODEL; NO response_format (JSON from the
        fence-stripping / balanced-object path); reasoning disabled per request with
        model_config.REASONING_EXTRA_BODY_OPENROUTER. OPENROUTER_API_KEY required.
        (The previous Granite 4.1 default was delisted 2026-09-04 — V-01.)
      * "deepseek": OpenAI client → api.deepseek.com; model NEWS_MODEL or
        deepseek-v4-flash; response_format json_object; thinking disabled with
        model_config.REASONING_EXTRA_BODY_DEEPSEEK. DEEPSEEK_API_KEY required.
      * "minimax": OpenAI client → api.minimaxi.chat/v1; model MiniMax-Text-01;
        NO response_format (json_object returns HTTP 400 on MiniMax). MINIMAX_API_KEY.
  - Backup (NREC-04): DeepSeek direct, model NEWS_BACKUP_MODEL or
    model_config.DEFAULT_BACKUP_MODEL (OpenRouter DEFAULT_OPENROUTER_MODEL when the
    primary itself is DeepSeek direct — G-08).

Failure handling (G-03 / G-09):
  - classify_outcome() returns a typed ClassifyResult (OK / NOT_CRIME / PARSE_ERROR /
    API_ERROR). API_ERROR is never "not a crime": the caller queues it (pending.json)
    instead of burning the URL into seen.json.
  - tenacity is the ONLY retry layer (SDK max_retries=0, timeout 30 s): 429 / 5xx /
    connection / timeout → 3 attempts, 2 s then 4 s waits. 400/401/403/404 → no retry.
  - ProviderRouter (per run): OpenRouter preflight, circuit breaker at 5 consecutive
    API_ERRORs per provider, same-run re-dispatch of the tripping streak to the backup,
    run time budget NEWS_RUN_BUDGET_S (default 1200 s).
  - classify() is kept as a compat wrapper: ClassifierOutput iff OK, else None.

Family whitespace normalization:
  Some models emit a tokenizer artifact like "robos_ violentos" (internal space after
  underscore). _parse_content collapses internal whitespace in the family value after
  json.loads and before Pydantic validation. Guard is defensive: only applied when
  family is a str; None/missing untouched. (Spike 008 artifact.)

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
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Literal

import requests
from openai import (
    APIConnectionError,
    APIStatusError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from pydantic import ValidationError
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

from pipeline.news import model_config
from pipeline.news.schema import VALID_FAMILIES, ClassifierOutput
from pipeline.shared.schema import FAMILY_KEYS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLD: float = 0.6  # D-07 / RESEARCH A3

# G-03 failure knobs
BREAKER_THRESHOLD: int = 5
RETRY_MAX_ATTEMPTS: int = 3
RETRY_WAIT_FIRST_S: int = 2
RETRY_WAIT_MAX_S: int = 20
REQUEST_TIMEOUT_S: float = 30.0
# G-09 run time budget (env NEWS_RUN_BUDGET_S overrides)
RUN_BUDGET_DEFAULT_S: int = 1200

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MINIMAX_BASE_URL = "https://api.minimaxi.chat/v1"

# Patchable sleep used by the tenacity retry layer (tests replace it with a recorder).
_sleep: Callable[[float], None] = time.sleep


def _make_client(api_key: str, base_url: str) -> OpenAI:
    """OpenAI-compatible client with SDK retries disabled (G-03: tenacity is the only
    retry layer — the SDK default max_retries=2 would turn 3 attempts into 9)."""
    return OpenAI(
        api_key=api_key or "placeholder",
        base_url=base_url,
        max_retries=0,
        timeout=REQUEST_TIMEOUT_S,
    )


# ---------------------------------------------------------------------------
# Provider selection (NEWS_PROVIDER env var) — import-time compat globals.
# build_router_from_env() builds FRESH clients at call time (R-12); these module
# globals only serve classify()/classify_outcome(spec=None) and the unit tests that
# patch `pipeline.news.classifier.client`.
# ---------------------------------------------------------------------------

_PROVIDER: str = model_config.resolve("NEWS_PROVIDER", model_config.DEFAULT_PROVIDER).lower()

if _PROVIDER == "deepseek":
    client = _make_client(os.environ.get("DEEPSEEK_API_KEY", "placeholder"), DEEPSEEK_BASE_URL)
    _MODEL: str = model_config.resolve("NEWS_MODEL", "deepseek-v4-flash")
    _EXTRA_BODY: dict | None = model_config.REASONING_EXTRA_BODY_DEEPSEEK
elif _PROVIDER == "minimax":
    client = _make_client(os.environ.get("MINIMAX_API_KEY", "placeholder"), MINIMAX_BASE_URL)
    _MODEL = "MiniMax-Text-01"
    _EXTRA_BODY = None
else:
    # Default: openrouter — model from model_config (34-01 A/B decision, G-16)
    _PROVIDER = "openrouter"
    client = _make_client(os.environ.get("OPENROUTER_API_KEY", "placeholder"), OPENROUTER_BASE_URL)
    _MODEL = model_config.resolve("NEWS_MODEL", model_config.DEFAULT_OPENROUTER_MODEL)
    _EXTRA_BODY = model_config.REASONING_EXTRA_BODY_OPENROUTER

# Backup: DeepSeek direct (NREC-04).
backup_client = _make_client(os.environ.get("DEEPSEEK_API_KEY", "placeholder"), DEEPSEEK_BASE_URL)
_BACKUP_MODEL: str = model_config.resolve("NEWS_BACKUP_MODEL", model_config.DEFAULT_BACKUP_MODEL)

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
  "title_en": "<faithful English translation of the HEADLINE exactly as given (omit a trailing ' - <outlet name>'); keep every fact, name, number, place and family-relationship term; do not summarise, add or drop anything; max 200 chars, plain text>",
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
- Deaths or injuries where the article alleges no crime are NOT crime incidents: natural death, suicide (suicidio), drowning (inmersión), a body found with no crime established, or authorities ruling out third-party involvement. The same applies to every kind of accident: workplace or mining (accidente laboral), aviation, sport or recreation, domestic, explosive remnants or landmines, and traffic (rule above). A death is a crime incident only if the article names an aggressor, a suspect, or a criminal investigation into the death; a person reported dead, found dead, who fell, or who died of illness with none of these is NOT a crime incident. A routine police or prosecutor inquiry to establish the cause of a death, including a body found, is not by itself a criminal investigation. An accident stays NOT a crime incident even when police, firefighters, emergency services or a prosecutor respond or investigate its causes, unless a person is accused of causing it.
- Fires (incendio), explosions, emergencies and natural disasters are NOT crime incidents unless the article alleges arson (incendio intencional) or another crime.
- Institutional, policy, budget or administrative news is NOT a crime incident: meetings, statements, plans, preventive security deployments, enforcement or operation balances and statistics (balance), prisoner transfers (traslado de reos) or prison policy, and protests announced without incidents. The same applies to court or administrative proceedings not tied to a concrete crime incident (rulings on prison transfers or prison conditions, pension or benefit disputes), statements by officials or politicians, protests or commemorations about past cases, and authorities requesting more police.
- For the three non-crime categories above, set commune_name to null and confidence to 0.0.
- News about a specific, identifiable crime case (arrest, charge, formalization, trial or sentence) IS in scope; family = the family of the underlying crime.
- Family boundaries follow the CEAD catalog: vida = homicide, femicide, attempted homicide or injuries (lesiones), including any shooting or attack where a person is hit or targeted; armas = weapons possession, trafficking or unjustified discharge (disparo injustificado) with no person targeted; kidnapping or deprivation of liberty to obtain money or goods = robos_violentos; threats, harassment, damage or theft against a current or former partner or a family member, including breach of a restraining order = vif; escape or evasion from custody, or helping a prisoner escape = incivilidades, never vida; robbery with violence or intimidation, including when it causes injuries but no death = robos_violentos; robbery or theft without confrontation = propiedad; intra-family violence without death = vif; sexual crimes = sexuales (rule below). Never use vida as a default just because someone died.
- Sexual crimes (violacion, abuso sexual, estupro, grooming, pornografia infantil, acoso sexual, agresion sexual, delitos de connotacion sexual) MUST use family "sexuales", NOT "vida". Exception: if the incident is a killing (homicidio, femicidio) the family stays "vida" even when a sexual assault accompanied the death — death dominates classification.
- family MUST be exactly one of: {_NEWS_FAMILY_ENUM_STR}
- Output plain text only for title_en and summary — no HTML, no markdown.
"""

# Regex to strip markdown JSON fences (used for MiniMax which omits response_format)
_JSON_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


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

    # Valid JSON that is not an object (array, null, bare string) is a parse error,
    # not a crash: without response_format the model may answer with a list.
    if not isinstance(data, dict):
        logger.warning("Non-object JSON from %s for %r", _PROVIDER, title[:60])
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



# ---------------------------------------------------------------------------
# Typed outcomes (NREC-05)
# ---------------------------------------------------------------------------

class Outcome(str, Enum):
    OK = "ok"
    NOT_CRIME = "not_crime"
    PARSE_ERROR = "parse_error"
    API_ERROR = "api_error"


@dataclass(frozen=True)
class ClassifyResult:
    outcome: Outcome
    output: ClassifierOutput | None
    provider: str
    model: str
    status_code: int | None = None
    # exception type name | "empty_content" | "finish_length" (G-09)
    error: str | None = None
    # OpenRouter response `provider` attr if present, else resp.model (R-10)
    served_by: str | None = None
    finish_reason: str | None = None
    # {prompt_tokens, completion_tokens, reasoning_tokens, cost?} (R-12)
    usage: dict | None = None


@dataclass(frozen=True)
class PreflightResult:
    status: Literal["ok", "zero_endpoints", "model_unknown", "no_credit", "unknown", "skipped"]
    endpoints: int | None


@dataclass
class ProviderSpec:
    provider: str
    model: str
    client_getter: Callable[[], OpenAI]
    extra_body: dict | None
    key_present: bool
    # Env var NAME holding the key (for log messages — never the value).
    key_env: str = ""
    # Key value, only used for the authenticated OpenRouter credit preflight (R-04).
    api_key: str | None = field(default=None, repr=False)

    @property
    def label(self) -> str:
        return f"{self.provider}:{self.model}"


# ---------------------------------------------------------------------------
# Retry layer (G-03)
# ---------------------------------------------------------------------------

def _is_retryable(exc: BaseException) -> bool:
    """429 / 5xx / connection / timeout → retry; every other status (400/401/403/404/
    409/422) and every non-openai exception → no retry."""
    if isinstance(exc, (RateLimitError, InternalServerError, APIConnectionError)):
        return True  # APITimeoutError subclasses APIConnectionError
    if isinstance(exc, APIStatusError):
        code = getattr(exc, "status_code", None)
        return code == 429 or (isinstance(code, int) and code >= 500)
    return False


def _retrying_create(spec: ProviderSpec, user_content: str):
    """_request_completion wrapped in tenacity: 3 attempts, waits 2 s then 4 s (cap 20 s)."""
    retryer = Retrying(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=RETRY_WAIT_FIRST_S, exp_base=2, max=RETRY_WAIT_MAX_S),
        sleep=lambda s: _sleep(s),
        reraise=True,
    )
    return retryer(
        _request_completion,
        spec.client_getter(),
        spec.model,
        spec.provider,
        user_content,
        spec.extra_body,
    )


def _num(value) -> int | float | None:
    if isinstance(value, bool):
        return None
    return value if isinstance(value, (int, float)) else None


def _str_or_none(value) -> str | None:
    return value if isinstance(value, str) and value else None


def _response_meta(resp) -> tuple[str | None, str | None, dict | None]:
    """(served_by, finish_reason, usage) from a chat completion response (R-10, R-12)."""
    served_by = _str_or_none(getattr(resp, "provider", None)) or _str_or_none(
        getattr(resp, "model", None)
    )
    finish_reason = None
    try:
        finish_reason = _str_or_none(resp.choices[0].finish_reason)
    except Exception:
        pass
    usage = None
    u = getattr(resp, "usage", None)
    if u is not None:
        details = getattr(u, "completion_tokens_details", None)
        reasoning = _num(getattr(details, "reasoning_tokens", None)) if details is not None else None
        usage = {
            "prompt_tokens": _num(getattr(u, "prompt_tokens", None)),
            "completion_tokens": _num(getattr(u, "completion_tokens", None)),
            "reasoning_tokens": reasoning or 0,
        }
        cost = _num(getattr(u, "cost", None))
        if cost is not None:
            usage["cost"] = cost
    return served_by, finish_reason, usage


def _primary_compat_spec() -> ProviderSpec:
    """Primary spec over the import-time module `client`, read at CALL time so the
    unit tests that patch `pipeline.news.classifier.client` keep working."""
    return ProviderSpec(
        provider=_PROVIDER,
        model=_MODEL,
        client_getter=lambda: client,
        extra_body=_EXTRA_BODY,
        key_present=True,
    )


# ---------------------------------------------------------------------------
# Classifier functions
# ---------------------------------------------------------------------------

def classify_outcome(
    title: str, description: str, spec: ProviderSpec | None = None
) -> ClassifyResult:
    """Classify one news item on one provider and return a typed outcome.

    - API_ERROR: any exception (after tenacity retries for 429/5xx/connection), empty
      content after one immediate re-call ("empty_content"), or finish_reason ==
      "length" ("finish_length"). Transient — the caller must NOT mark the URL seen.
    - PARSE_ERROR: non-empty, non-truncated content that fails _parse_content.
    - NOT_CRIME: validated answer with confidence < CONFIDENCE_THRESHOLD (output attached).
    - OK: validated answer at or above the threshold.

    Never runs the preflight and never does network I/O besides the completion call.
    """
    spec = spec or _primary_compat_spec()
    user_content = f"HEADLINE: {title}\nSUMMARY: {description[:500]}"

    def _api_error(exc: BaseException) -> ClassifyResult:
        status = getattr(exc, "status_code", None)
        status = status if isinstance(status, int) else None
        # Log exception type + status only (T-34-05: never keys or bodies).
        logger.warning(
            "%s API error: %s status=%s for %r",
            spec.label, type(exc).__name__, status, title[:60],
        )
        return ClassifyResult(
            Outcome.API_ERROR, None, spec.provider, spec.model,
            status_code=status, error=type(exc).__name__,
        )

    try:
        resp = _retrying_create(spec, user_content)
    except Exception as exc:  # noqa: BLE001 — every failure is a typed API_ERROR
        return _api_error(exc)

    served_by, finish_reason, usage = _response_meta(resp)
    meta = dict(served_by=served_by, finish_reason=finish_reason, usage=usage)

    if finish_reason == "length":
        logger.warning("%s finish_reason=length for %r", spec.label, title[:60])
        return ClassifyResult(
            Outcome.API_ERROR, None, spec.provider, spec.model, error="finish_length", **meta
        )

    raw = _content_of(resp)
    if not raw:
        # Empty-content re-call (Pitfall 4) — exactly one, not a tenacity attempt.
        logger.warning("Empty %s response for %r — retrying once", spec.label, title[:60])
        try:
            resp = _retrying_create(spec, user_content)
        except Exception as exc:  # noqa: BLE001
            return _api_error(exc)
        served_by, finish_reason, usage = _response_meta(resp)
        meta = dict(served_by=served_by, finish_reason=finish_reason, usage=usage)
        if finish_reason == "length":
            return ClassifyResult(
                Outcome.API_ERROR, None, spec.provider, spec.model, error="finish_length", **meta
            )
        raw = _content_of(resp)
        if not raw:
            return ClassifyResult(
                Outcome.API_ERROR, None, spec.provider, spec.model, error="empty_content", **meta
            )

    kind, out = _parse_content(raw, title)
    if kind == "ok":
        return ClassifyResult(Outcome.OK, out, spec.provider, spec.model, **meta)
    if kind == "low_conf":
        logger.warning(
            "Rejected: confidence below %.2f for %r", CONFIDENCE_THRESHOLD, title[:60]
        )
        return ClassifyResult(Outcome.NOT_CRIME, out, spec.provider, spec.model, **meta)
    return ClassifyResult(Outcome.PARSE_ERROR, None, spec.provider, spec.model, **meta)


def _content_of(resp) -> str | None:
    try:
        content = resp.choices[0].message.content
    except Exception:
        return None
    return content if isinstance(content, str) and content else None


def classify(title: str, description: str) -> ClassifierOutput | None:
    """Compat wrapper: ClassifierOutput iff the outcome is OK, else None.

    The LLM client is NEVER called in unit tests — mock `pipeline.news.classifier.client`.
    """
    res = classify_outcome(title, description)
    return res.output if res.outcome is Outcome.OK else None


# ---------------------------------------------------------------------------
# OpenRouter preflight (NREC-03) — metadata GETs only, never a completion call
# ---------------------------------------------------------------------------

def preflight_openrouter(
    model: str,
    *,
    api_key: str | None = None,
    http_get: Callable | None = None,
    timeout: float = 15.0,
) -> PreflightResult:
    """Check the model has live OpenRouter endpoints (and, with api_key, credit).

    - 200 + endpoints == [] → "zero_endpoints"; 200 + ≥1 → "ok"; 404 → "model_unknown";
      anything else / exception / bad JSON → "unknown".
    - R-04: with api_key, GET /api/v1/key; data.limit_remaining a number ≤ 0 →
      "no_credit"; null / > 0 / failure → no change.
    `http_get` defaults to requests.get resolved at CALL time (patchable in tests).
    """
    get = http_get or requests.get
    status: str = "unknown"
    endpoints: int | None = None
    try:
        resp = get(f"{OPENROUTER_BASE_URL}/models/{model}/endpoints", timeout=timeout)
        code = getattr(resp, "status_code", None)
        if code == 200:
            eps = resp.json()["data"]["endpoints"]
            endpoints = len(eps)
            status = "ok" if endpoints > 0 else "zero_endpoints"
        elif code == 404:
            status = "model_unknown"
        else:
            logger.warning("OpenRouter preflight: endpoints HTTP %s", code)
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenRouter preflight: endpoints check failed (%s)", type(exc).__name__)
        status = "unknown"

    if api_key and status in ("ok", "unknown"):
        try:
            kresp = get(
                f"{OPENROUTER_BASE_URL}/key",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=timeout,
            )
            kcode = getattr(kresp, "status_code", None)
            if kcode == 200:
                remaining = (kresp.json().get("data") or {}).get("limit_remaining")
                if _num(remaining) is not None and remaining <= 0:
                    status = "no_credit"
            else:
                logger.warning("OpenRouter preflight: key check HTTP %s", kcode)
        except Exception as exc:  # noqa: BLE001
            logger.warning("OpenRouter preflight: key check failed (%s)", type(exc).__name__)

    logger.info("OpenRouter preflight for %s: %s (endpoints=%s)", model, status, endpoints)
    return PreflightResult(status, endpoints)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ProviderRouter — per-run failover / breaker / re-dispatch / budget (G-03, G-09)
# ---------------------------------------------------------------------------

def _budget_from_env() -> float:
    raw = os.environ.get("NEWS_RUN_BUDGET_S", "").strip()
    if not raw:
        return float(RUN_BUDGET_DEFAULT_S)
    try:
        val = float(raw)
        return val if val > 0 else float(RUN_BUDGET_DEFAULT_S)
    except ValueError:
        logger.warning("NEWS_RUN_BUDGET_S invalid — falling back to %d", RUN_BUDGET_DEFAULT_S)
        return float(RUN_BUDGET_DEFAULT_S)


class ProviderRouter:
    """Per-run routing state. One instance per scrape_news run."""

    def __init__(
        self,
        primary: ProviderSpec,
        backup: ProviderSpec | None,
        *,
        clock: Callable[[], float] = time.monotonic,
        budget_s: float | None = None,
        force_backup: bool = False,
    ):
        self.primary = primary
        self.backup = backup
        self._clock = clock
        self.budget_s: float = _budget_from_env() if budget_s is None else float(budget_s)
        self._start = clock()

        self.active: Literal["primary", "backup", "none"] = "primary"
        self.failovers: int = 0
        self.failover_reason: str | None = None
        self.backup_exhausted: bool = False
        self.budget_exhausted: bool = False
        self.preflight_status: str = "skipped"

        self._consec = {"primary": 0, "backup": 0}
        # Current primary API_ERROR streak: (key, title, description, result)
        self._streak: list[tuple[str | None, str, str, ClassifyResult]] = []
        self._redispatched: list[tuple[str | None, ClassifyResult]] = []

        if force_backup:
            self._failover("forced")
        elif not primary.key_present:
            self._failover("primary_key_absent")

    # -- labels / key presence (consumed by scrape_news) --------------------
    @property
    def primary_label(self) -> str:
        return self.primary.label

    @property
    def backup_label(self) -> str | None:
        return self.backup.label if self.backup is not None else None

    @property
    def any_key_present(self) -> bool:
        return self.primary.key_present or bool(self.backup and self.backup.key_present)

    @property
    def key_env_names(self) -> list[str]:
        names = [self.primary.key_env]
        if self.backup is not None:
            names.append(self.backup.key_env)
        return [n for n in names if n]

    # -- state transitions ---------------------------------------------------
    def _failover(self, reason: str) -> None:
        if self.backup is None or not self.backup.key_present:
            logger.error(
                "Failover (%s) requested but backup is unavailable (%s not set) — "
                "remaining items will be queued",
                reason, self.backup.key_env if self.backup else "no backup configured",
            )
            self.active = "none"
            self.backup_exhausted = True
            self.failover_reason = "backup_unavailable"
            return
        self.failovers += 1
        self.failover_reason = reason
        self.active = "backup"
        logger.warning(
            "Failover %s → %s (reason: %s)", self.primary.label, self.backup.label, reason
        )

    def _budget_spent(self) -> bool:
        if self._clock() - self._start >= self.budget_s:
            if not self.budget_exhausted:
                logger.warning(
                    "Run time budget %.0f s exhausted — remaining items will be queued",
                    self.budget_s,
                )
            self.budget_exhausted = True
            return True
        return False

    def preflight(self) -> PreflightResult:
        if self.active != "primary" or self.primary.provider != "openrouter":
            self.preflight_status = "skipped"
            return PreflightResult("skipped", None)
        res = preflight_openrouter(self.primary.model, api_key=self.primary.api_key)
        self.preflight_status = res.status
        if res.status in ("zero_endpoints", "model_unknown", "no_credit"):
            self._failover(f"preflight_{res.status}")
        elif res.status == "unknown":
            logger.warning("OpenRouter preflight inconclusive — staying on primary %s", self.primary.label)
        return res

    def _classify_backup(self, title: str, description: str) -> ClassifyResult:
        assert self.backup is not None
        res = classify_outcome(title, description, self.backup)
        if res.outcome is Outcome.API_ERROR:
            self._consec["backup"] += 1
            if self._consec["backup"] >= BREAKER_THRESHOLD:
                logger.error(
                    "Backup %s breaker tripped (%d consecutive API errors) — backup exhausted",
                    self.backup.label, BREAKER_THRESHOLD,
                )
                self.backup_exhausted = True
                self.active = "none"
        else:
            self._consec["backup"] = 0
        return res

    def _redispatch(self, streak) -> None:
        """R-04 / G-09: re-classify the tripping streak on the backup, same run."""
        for key, title, description, original in streak:
            if self.active != "backup" or self._budget_spent():
                self._redispatched.append((key, original))
                continue
            self._redispatched.append((key, self._classify_backup(title, description)))

    def classify(self, title: str, description: str, key: str | None = None) -> ClassifyResult | None:
        """Classify on the active provider. None = not attempted (exhausted or budget)."""
        if self._budget_spent():
            return None
        if self.active == "none":
            return None
        if self.active == "backup":
            return self._classify_backup(title, description)

        res = classify_outcome(title, description, self.primary)
        if res.outcome is Outcome.API_ERROR:
            self._consec["primary"] += 1
            self._streak.append((key, title, description, res))
            if self._consec["primary"] >= BREAKER_THRESHOLD:
                streak, self._streak = self._streak, []
                logger.error(
                    "Primary %s breaker tripped (%d consecutive API errors)",
                    self.primary.label, BREAKER_THRESHOLD,
                )
                self._failover("breaker")
                if self.active == "backup":
                    self._redispatch(streak)
        else:
            self._consec["primary"] = 0
            self._streak = []
        return res

    def pop_redispatched(self) -> list[tuple[str | None, ClassifyResult]]:
        out, self._redispatched = self._redispatched, []
        return out


def _spec(provider: str, model: str, key_env: str, base_url: str, extra_body: dict | None) -> ProviderSpec:
    key = os.environ.get(key_env, "").strip()
    new_client = _make_client(key, base_url)
    return ProviderSpec(
        provider=provider,
        model=model,
        client_getter=lambda: new_client,
        extra_body=extra_body,
        key_present=bool(key),
        key_env=key_env,
        api_key=key or None,
    )


def build_router_from_env() -> ProviderRouter:
    """Build a ProviderRouter from os.environ read at CALL time (R-12): fresh clients,
    never the import-time module globals. GH Actions injects unset secrets/vars as "",
    which count as absent (key) / default (model, provider)."""
    provider = model_config.resolve("NEWS_PROVIDER", model_config.DEFAULT_PROVIDER).lower()
    deepseek_backup = lambda: _spec(  # noqa: E731
        "deepseek",
        model_config.resolve("NEWS_BACKUP_MODEL", model_config.DEFAULT_BACKUP_MODEL),
        "DEEPSEEK_API_KEY", DEEPSEEK_BASE_URL, model_config.REASONING_EXTRA_BODY_DEEPSEEK,
    )
    if provider == "deepseek":
        # G-08 DEEPSEEK_DIRECT shape: DeepSeek direct primary, OpenRouter backup.
        primary = _spec(
            "deepseek", model_config.resolve("NEWS_MODEL", "deepseek-v4-flash"),
            "DEEPSEEK_API_KEY", DEEPSEEK_BASE_URL, model_config.REASONING_EXTRA_BODY_DEEPSEEK,
        )
        backup = _spec(
            "openrouter",
            model_config.resolve("NEWS_BACKUP_MODEL", model_config.DEFAULT_OPENROUTER_MODEL),
            "OPENROUTER_API_KEY", OPENROUTER_BASE_URL, model_config.REASONING_EXTRA_BODY_OPENROUTER,
        )
    elif provider == "minimax":
        primary = _spec("minimax", "MiniMax-Text-01", "MINIMAX_API_KEY", MINIMAX_BASE_URL, None)
        backup = deepseek_backup()
    else:
        primary = _spec(
            "openrouter",
            model_config.resolve("NEWS_MODEL", model_config.DEFAULT_OPENROUTER_MODEL),
            "OPENROUTER_API_KEY", OPENROUTER_BASE_URL, model_config.REASONING_EXTRA_BODY_OPENROUTER,
        )
        backup = deepseek_backup()

    force = os.environ.get("NEWS_FORCE_BACKUP", "").strip().lower() == "true"
    return ProviderRouter(primary, backup, force_backup=force)
