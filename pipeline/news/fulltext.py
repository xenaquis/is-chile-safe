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
import socket
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

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
MAX_REDIRECTS = 5  # manual redirect cap — each hop re-validated (CR-01)
ALLOWED_CONTENT_TYPES = ("text/html", "text/plain")  # T-gf7-03


# ---------------------------------------------------------------------------
# URL safety guard (T-gf7-01)
# ---------------------------------------------------------------------------

def _ip_is_blocked(ip: ipaddress._BaseAddress) -> bool:
    """True if an IP must never be fetched (SSRF targets)."""
    return (
        ip.is_private or ip.is_loopback or ip.is_link_local
        or ip.is_reserved or ip.is_multicast or ip.is_unspecified
    )


def is_safe_url(url: str, *, resolve_dns: bool = True) -> bool:
    """
    Return True only if the URL is safe to fetch.

    Rejects:
    - Non-http(s) schemes (ftp, file, javascript, etc.)
    - Embedded credentials (user:pass@host)
    - Private / loopback / link-local / reserved IP *literals*
    - (when resolve_dns) hostnames whose DNS resolution yields ANY blocked IP —
      closes the DNS-rebinding / attacker-A-record SSRF hole (CR-02). A
      hostname that fails to resolve is rejected.

    resolve_dns=False keeps the pure-syntactic check for unit tests that must
    not touch the network.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    # Reject embedded credentials (T-gf7-01)
    if parsed.username or parsed.password:
        return False

    hostname = parsed.hostname
    if hostname is None:
        if parsed.netloc:
            return False
        return False  # no host at all → unsafe

    # Literal IP → check directly, no DNS.
    try:
        ip = ipaddress.ip_address(hostname)
        return not _ip_is_blocked(ip)
    except ValueError:
        pass  # not a literal IP — it's a DNS name

    if not resolve_dns:
        return True

    # Resolve the hostname and reject if ANY address is blocked (CR-02).
    try:
        infos = socket.getaddrinfo(hostname, None)
    except Exception:
        logger.debug("is_safe_url: DNS resolution failed for %s", hostname)
        return False
    for info in infos:
        addr = info[4][0]
        try:
            if _ip_is_blocked(ipaddress.ip_address(addr)):
                logger.debug("is_safe_url: %s resolves to blocked IP", hostname)
                return False
        except ValueError:
            return False
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
        # The decoder needs a session-like object with .get/.post for the
        # new-format network path; the `requests` module itself qualifies and
        # keeps the ft.requests test seam (production callers pass no session,
        # which previously skipped decoding entirely — every gnews URL failed).
        decoded = decode_gnews_url(
            url,
            session=session if session is not None else requests,
            timeout=float(timeout),
        )
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
    def _do_get(target: str) -> requests.Response:
        # allow_redirects=False: we follow hops manually so is_safe_url runs on
        # EVERY landed host (CR-01). requests otherwise follows a 302 to an
        # internal address without re-checking, turning any public outlet that
        # redirects into a blind-SSRF gadget.
        return _get(
            target,
            allow_redirects=False,
            timeout=timeout,
            headers={"User-Agent": user_agent},
            stream=True,
        )

    # Manual redirect loop with per-hop revalidation (CR-01).
    current_url = fetch_url
    resp = None
    for _hop in range(MAX_REDIRECTS + 1):
        resp = _do_get(current_url)
        status = resp.status_code
        if status in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location")
            if not location:
                break
            next_url = urljoin(current_url, location)
            if not is_safe_url(next_url):
                logger.debug("fetch_article: redirect target rejected: %s", next_url[:80])
                if hasattr(resp, "close"):
                    resp.close()
                return {
                    "final_url": next_url,
                    "http_status": None,
                    "extraction_ok": False,
                    "text": "",
                    "lang": None,
                    "decoded_from_gnews": decoded_from_gnews,
                }
            if hasattr(resp, "close"):
                resp.close()
            current_url = next_url
            continue
        break
    else:
        # Redirect budget exhausted
        logger.debug("fetch_article: too many redirects from %s", fetch_url[:80])
        return {
            "final_url": current_url,
            "http_status": None,
            "extraction_ok": False,
            "text": "",
            "lang": None,
            "decoded_from_gnews": decoded_from_gnews,
        }

    final_url = getattr(resp, "url", current_url)
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
