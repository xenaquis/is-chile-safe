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
import ipaddress
import logging
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
import trafilatura
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pipeline.news.gnews_decoder import decode_gnews_url  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
USER_AGENT = "ischilesafe-research-archiver/1.0 (+https://ischilesafe.com)"
REQUEST_TIMEOUT = 15
REQUEST_DELAY = 1.5
MAX_TEXT_BYTES = 2 * 1024 * 1024  # 2 MB hard cap
MAX_DOWNLOAD_BYTES = 5 * 1024 * 1024  # 5 MB streamed download cap (T-gf7-02)
ALLOWED_CONTENT_TYPES = ("text/html", "text/plain")  # T-gf7-03


# ---------------------------------------------------------------------------
# URL safety guard (T-gf7-01)
# ---------------------------------------------------------------------------

def is_safe_url(url: str) -> bool:
    """
    Return True only if the URL is safe to fetch.

    Rejects:
    - Non-http(s) schemes (ftp, file, javascript, etc.)
    - Embedded credentials (user:pass@host)
    - Private / loopback / link-local / reserved IP literals (no DNS resolution)

    Does NOT perform DNS resolution — only literal IP addresses are checked.
    Public hostnames (non-IP) are allowed.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    # Scheme must be http or https
    if parsed.scheme not in {"http", "https"}:
        return False

    # Reject embedded credentials (T-gf7-01)
    if parsed.username or parsed.password:
        return False

    # Check if hostname is an IP literal
    # urlparse.hostname is None for malformed/unbracketed IPv6 (http://::1/x) —
    # treat a missing hostname as unsafe if netloc is non-empty.
    hostname = parsed.hostname
    if hostname is None:
        # If netloc is present but hostname couldn't be parsed → reject
        if parsed.netloc:
            return False
        hostname = ""
    try:
        ip = ipaddress.ip_address(hostname)
        # Reject private/loopback/link-local/reserved IPs
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False
    except ValueError:
        # Not an IP literal — treat as DNS name, allow
        pass

    return True


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

    Wiring:
    - If url host is news.google.com: decode via decode_gnews_url first.
    - Both original and decoded URLs are checked with is_safe_url.
    - Response is streamed with a 5 MB hard ceiling (T-gf7-02).
    - Content-Type must be text/html or text/plain (T-gf7-03).

    Returns a dict:
        final_url, http_status, extraction_ok, text, lang, decoded_from_gnews

    On non-2xx or empty extraction: extraction_ok=False, text="".
    On RequestException after retries exhausted: re-raises (caller catches).
    """
    _get = session.get if session is not None else requests.get

    decoded_from_gnews = False

    # Guard original URL (T-gf7-01)
    if not is_safe_url(url):
        logger.debug("fetch_article: original URL rejected by is_safe_url: %s", url[:80])
        return {
            "final_url": url,
            "http_status": None,
            "extraction_ok": False,
            "text": "",
            "lang": None,
            "decoded_from_gnews": False,
        }

    fetch_url = url

    # Google News decode wiring
    parsed_url = urlparse(url)
    if (parsed_url.hostname or "").lower() == "news.google.com":
        decoded = decode_gnews_url(url, session=session, timeout=float(timeout))
        if decoded is None or decoded == url:
            # Decode failed (None) or returned unchanged (shouldn't happen for gnews host)
            if decoded is None:
                logger.debug("fetch_article: gnews decode returned None for %s", url[:80])
                return {
                    "final_url": url,
                    "http_status": None,
                    "extraction_ok": False,
                    "text": "",
                    "lang": None,
                    "decoded_from_gnews": False,
                }
        else:
            # Guard decoded URL too (T-gf7-01)
            if not is_safe_url(decoded):
                logger.debug("fetch_article: decoded URL rejected by is_safe_url: %s", decoded[:80])
                return {
                    "final_url": url,
                    "http_status": None,
                    "extraction_ok": False,
                    "text": "",
                    "lang": None,
                    "decoded_from_gnews": True,
                }
            fetch_url = decoded
            decoded_from_gnews = True

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=8),
        retry=retry_if_exception_type((requests.RequestException,)),
        reraise=True,
    )
    def _do_get() -> requests.Response:
        return _get(
            fetch_url,
            allow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": user_agent},
            stream=True,
        )

    resp = _do_get()
    final_url = getattr(resp, "url", fetch_url)
    http_status = resp.status_code

    if not (200 <= http_status < 300):
        return {
            "final_url": final_url,
            "http_status": http_status,
            "extraction_ok": False,
            "text": "",
            "lang": None,
            "decoded_from_gnews": decoded_from_gnews,
        }

    # Content-Type guard (T-gf7-03)
    content_type = (resp.headers.get("Content-Type") or "").lower()
    if not any(content_type.startswith(ct) for ct in ALLOWED_CONTENT_TYPES):
        logger.debug(
            "fetch_article: rejected Content-Type %r for %s",
            content_type, fetch_url[:80],
        )
        return {
            "final_url": final_url,
            "http_status": http_status,
            "extraction_ok": False,
            "text": "",
            "lang": None,
            "decoded_from_gnews": decoded_from_gnews,
        }

    # Streamed 5 MB cap (T-gf7-02)
    accumulated = bytearray()
    over_limit = False
    for chunk in resp.iter_content(chunk_size=8192):
        if chunk:
            accumulated.extend(chunk)
            if len(accumulated) > MAX_DOWNLOAD_BYTES:
                over_limit = True
                break

    if over_limit:
        logger.debug(
            "fetch_article: download exceeded 5 MB cap for %s", fetch_url[:80]
        )
        return {
            "final_url": final_url,
            "http_status": http_status,
            "extraction_ok": False,
            "text": "",
            "lang": None,
            "decoded_from_gnews": decoded_from_gnews,
        }

    # Decode body
    encoding = getattr(resp, "encoding", None) or "utf-8"
    body_text = accumulated.decode(encoding, errors="ignore")

    text = trafilatura.extract(body_text) or ""
    extraction_ok = bool(text.strip())

    return {
        "final_url": final_url,
        "http_status": http_status,
        "extraction_ok": extraction_ok,
        "text": text,
        "lang": None,  # lang detection kept optional
        "decoded_from_gnews": decoded_from_gnews,
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
        "decoded_from_gnews": fetch_result.get("decoded_from_gnews", False),
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
