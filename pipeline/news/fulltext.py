"""
pipeline/news/fulltext.py

Courtesy-throttled full-text fetch and trafilatura article extraction.

IMPORTANT COPYRIGHT NOTE:
Full-text article copies are for PRIVATE research use only. Do NOT publish raw
article text publicly. Only APA attribution strings are retained for public-facing
outputs. Stored text is held in the operator's private Cloudflare R2 bucket.
"""
from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone

import requests
import trafilatura
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
USER_AGENT = "ischilesafe-research-archiver/1.0 (+https://ischilesafe.com)"
REQUEST_TIMEOUT = 15
REQUEST_DELAY = 1.5
MAX_TEXT_BYTES = 2 * 1024 * 1024  # 2 MB hard cap


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_article(
    url: str,
    *,
    timeout: int = REQUEST_TIMEOUT,
    user_agent: str = USER_AGENT,
    session=None,
) -> dict:
    """
    GET the article at *url*, following redirects, and extract text with trafilatura.

    Returns a dict:
        final_url, http_status, extraction_ok, text, lang

    On non-2xx or empty extraction: extraction_ok=False, text="".
    On RequestException after retries exhausted: re-raises (caller catches).
    """
    _get = session.get if session is not None else requests.get

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=8),
        retry=retry_if_exception_type((requests.RequestException,)),
        reraise=True,
    )
    def _do_get() -> requests.Response:
        return _get(
            url,
            allow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": user_agent},
        )

    resp = _do_get()
    final_url = getattr(resp, "url", url)
    http_status = resp.status_code

    if not (200 <= http_status < 300):
        return {
            "final_url": final_url,
            "http_status": http_status,
            "extraction_ok": False,
            "text": "",
            "lang": None,
        }

    text = trafilatura.extract(resp.text) or ""
    extraction_ok = bool(text.strip())

    return {
        "final_url": final_url,
        "http_status": http_status,
        "extraction_ok": extraction_ok,
        "text": text,
        "lang": None,  # lang detection kept optional
    }


# ---------------------------------------------------------------------------
# Article object builder
# ---------------------------------------------------------------------------

def build_article_object(inc: dict, fetch_result: dict) -> dict:
    """
    Build a research-archive article object from an incident dict and a fetch result.

    Enforces the 2 MB text cap BEFORE hashing — truncation is deterministic.
    """
    text: str = fetch_result.get("text") or ""

    # Enforce 2 MB cap
    b = text.encode("utf-8")
    if len(b) > MAX_TEXT_BYTES:
        text = b[:MAX_TEXT_BYTES].decode("utf-8", "ignore")

    text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    char_count = len(text)
    fetched_at = datetime.now(timezone.utc).isoformat()

    return {
        "id": inc.get("id", ""),
        "url": inc.get("url", ""),
        "final_url": fetch_result.get("final_url"),
        "fetched_at": fetched_at,
        "http_status": fetch_result.get("http_status"),
        "extraction_ok": fetch_result.get("extraction_ok", False),
        "text": text,
        "text_sha256": text_sha256,
        "char_count": char_count,
        "lang": fetch_result.get("lang"),
        # Incident metadata
        "date": inc.get("date", ""),
        "cut": inc.get("cut", ""),
        "slug": inc.get("slug"),
        "family": inc.get("family", ""),
        "outlet": inc.get("outlet", ""),
        "title_es": inc.get("title_es", ""),
        "title_en": inc.get("title_en", ""),
        "apa": inc.get("apa", ""),
    }
