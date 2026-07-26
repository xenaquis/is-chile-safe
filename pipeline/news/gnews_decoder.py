"""
pipeline/news/gnews_decoder.py

Decode news.google.com RSS article URLs to the underlying outlet URL before
full-text fetch.

Google News RSS items use one of two encoding schemes:
  - Old-format: /rss/articles/<base64url-token> — the token decodes to a byte
    blob containing exactly one https?:// URL. No network needed.
  - New-format: JS-gated splash page. We must GET the article page to extract
    data-n-a-sg / data-n-a-ts / article-id, then POST to the batchexecute
    endpoint to get the decoded URL.

Security constraints (T-gf7-04):
  - The batchexecute POST host is HARDCODED — never derived from the input URL.
  - Any error in either path returns None. Never raises. Never logs response bodies.

No new package dependencies — all inline with stdlib + requests (already a dep).
"""
from __future__ import annotations

import base64
import json
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Hardcoded batchexecute endpoint (T-gf7-04 — never derived from input)
_BATCHEXECUTE_URL = "https://news.google.com/_/DotsSplashUi/data/batchexecute"

# Import USER_AGENT lazily to avoid circular imports at module load time
_USER_AGENT: str | None = None


def _get_user_agent() -> str:
    global _USER_AGENT
    if _USER_AGENT is None:
        try:
            from pipeline.news.fulltext import USER_AGENT  # noqa: PLC0415
            _USER_AGENT = USER_AGENT
        except Exception:
            _USER_AGENT = "ischilesafe-research-archiver/1.0 (+https://ischilesafe.com)"
    return _USER_AGENT


def _fix_b64_padding(token: str) -> str:
    """Append '=' chars so len is a multiple of 4."""
    pad = (4 - len(token) % 4) % 4
    return token + "=" * pad


def _is_http_url(candidate: str) -> bool:
    """Scheme allowlist for decoder output — the decoded blob is
    attacker-influenceable, so only plain http/https may leave this module
    (WR-05). fulltext.is_safe_url still re-checks host/IP downstream."""
    try:
        return urlparse(candidate).scheme in {"http", "https"}
    except Exception:
        return False


def _extract_url_from_bytes(data: bytes) -> str | None:
    """
    Regex-scan raw bytes for a plausible https?:// URL.
    Returns the URL if exactly one match found; None otherwise.
    """
    try:
        text = data.decode("latin-1")
    except Exception:
        return None
    matches = re.findall(r"https?://[^\x00-\x20\"'\x7f-\xff]+", text)
    # Filter out likely garbage (too short) and non-http schemes
    matches = [m for m in matches if len(m) > 10 and _is_http_url(m)]
    if len(matches) == 1:
        return matches[0]
    return None


def _try_old_format(url: str) -> str | None:
    """
    Attempt old-format decode: extract base64url token from URL path, decode,
    regex for a single https?:// URL. Returns URL or None. No network.
    """
    parsed = urlparse(url)
    # Token is the last path segment after /articles/
    m = re.search(r"/articles/([A-Za-z0-9_\-]+)", parsed.path)
    if not m:
        return None
    token = m.group(1)
    # Decode urlsafe base64
    try:
        data = base64.urlsafe_b64decode(_fix_b64_padding(token))
    except Exception:
        return None
    return _extract_url_from_bytes(data)


def _try_new_format(url: str, session, timeout: float) -> str | None:
    """
    New-format decode via batchexecute. Requires a network session.
    Wrap entire block in try/except — any error returns None.
    """
    try:
        parsed = urlparse(url)

        # Extract article id from URL path
        m = re.search(r"/articles/([A-Za-z0-9_\-]+)", parsed.path)
        if not m:
            return None
        article_id = m.group(1)

        headers = {"User-Agent": _get_user_agent()}

        # GET the article splash page
        resp = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)

        page_text = resp.text if hasattr(resp, "text") else ""

        # Extract data-n-a-sg and data-n-a-ts from page
        sg_match = re.search(r'data-n-a-sg="([^"]+)"', page_text)
        ts_match = re.search(r'data-n-a-ts="([^"]+)"', page_text)
        if not sg_match or not ts_match:
            return None

        sg = sg_match.group(1)
        ts = ts_match.group(1)

        # Build batchexecute f-request payload — "garturlreq" structure (the
        # protocol the googlenewsdecoder package documents; anything simpler
        # gets an error envelope back). ts must be an int, sg a string.
        garturlreq = [
            "garturlreq",
            [
                ["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1,
                 None, None, None, None, None, 0, 1],
                "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0,
            ],
            article_id,
            int(ts) if ts.isdigit() else ts,  # real protocol sends int; tolerate drift
            sg,
        ]
        freq = json.dumps([[["Fbv4je", json.dumps(garturlreq), None, "generic"]]])

        # dict form → requests percent-encodes the body correctly
        post_resp = session.post(
            _BATCHEXECUTE_URL,
            data={"f.req": freq},
            headers={
                "User-Agent": _get_user_agent(),
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            },
            timeout=timeout,
        )

        raw = post_resp.text if hasattr(post_resp, "text") else ""

        # Structured parse first: response is ")]}'\n\n<json>"; the decoded URL
        # lives at json.loads(envelope[i][2])[1] for the "wrb.fr" element.
        try:
            chunk = raw.split("\n\n")[1]
            envelope = json.loads(chunk)
            for item in envelope:
                if isinstance(item, list) and len(item) > 2 and item[0] == "wrb.fr" and item[2]:
                    decoded = json.loads(item[2])
                    candidate = decoded[1] if len(decoded) > 1 else None
                    if isinstance(candidate, str) and _is_http_url(candidate):
                        return candidate
        except Exception:
            pass

        # Fallback: regex scan of the stripped body for a non-Google URL
        stripped = re.sub(r"^\)\]\}'[\s]*", "", raw)
        urls_found = re.findall(r"https?://[^\x00-\x20\"'\x5c\x7f-\xff]{10,}", stripped)
        urls_found = [
            u for u in urls_found
            if "google.com" not in u and "gstatic.com" not in u and _is_http_url(u)
        ]
        if urls_found:
            return urls_found[0]

        return None

    except Exception:
        # T-gf7-05: never log full response bodies or raise
        logger.debug("gnews new-format decode failed for %s", url[:80])
        return None


def decode_gnews_url(url: str, session=None, timeout: float = 15.0) -> str | None:
    """
    Decode a news.google.com RSS URL to its underlying outlet URL.

    - If host is NOT news.google.com: returns url unchanged (fast path, no network).
    - Old-format token (no network): tries base64url decode first.
    - New-format (requires session/network): falls back to batchexecute POST.
    - Any failure → returns None; never raises; never logs response bodies.

    Args:
        url: The URL to decode (may be any URL).
        session: requests.Session (or compatible). Required for new-format fallback.
        timeout: Network timeout in seconds.

    Returns:
        Decoded outlet URL string, the original url unchanged (non-gnews), or None on failure.
    """
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()

        # Fast path: not a Google News URL — return as-is, no network
        if host != "news.google.com":
            return url

        # Try old-format first (no network needed)
        result = _try_old_format(url)
        if result:
            logger.debug("gnews old-format decode succeeded for %s", url[:80])
            return result

        # Fall back to new-format (network required)
        if session is None:
            logger.debug("gnews new-format skipped: no session provided for %s", url[:80])
            return None

        result = _try_new_format(url, session, timeout)
        if result:
            logger.debug("gnews new-format decode succeeded for %s", url[:80])
        else:
            logger.debug("gnews decode failed (both paths) for %s", url[:80])
        return result

    except Exception:
        logger.debug("decode_gnews_url unexpected error for %s", url[:80])
        return None
