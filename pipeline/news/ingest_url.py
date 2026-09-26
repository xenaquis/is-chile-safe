"""
pipeline/news/ingest_url.py

FID-04 (36-07, G-31): at ingest, turn a fresh Google-News item link into the
publisher URL, under a bounded, courteous per-run decode budget.

- resolve_publisher_url(gn_url, session, timeout) -> publisher URL | None
  Delegates to gnews_decoder.decode_gnews_url (whose batchexecute POST host is
  hardcoded, T-gf7-04). The decoded value is attacker-influenceable, so it is
  accepted only when store.is_safe_url passes (http/https) and its host is not
  news.google.com (T-36-19). utm_* parameters are stripped with the dedup
  canonicaliser. The publisher URL itself is never fetched (T-36-18).

- DecodeBudget: at most max_items decodes and max_seconds of decode time
  (waits + decode calls) per run, with `delay` seconds between decodes and
  never before the first (T-36-20). Decode time is spent from the G-09 run
  budget, so the 180 s cap leaves >= 1,020 s of the 1,200 s for classification.

The scrape_news caller performs the decode only AFTER the keyword prefilter and
the seen/pending check on the Google link, and never for queued items.
"""
from __future__ import annotations

import logging
import time
from typing import Callable
from urllib.parse import urlparse

from pipeline.news import gnews_decoder
from pipeline.news.dedup import _canonical_url
from pipeline.news.fulltext import REQUEST_DELAY
from pipeline.news.store import is_safe_url

logger = logging.getLogger(__name__)

GNEWS_HOST = "news.google.com"
DECODE_TIMEOUT_S = 10.0
MAX_DECODES_PER_RUN = 60
DECODE_BUDGET_S = 180.0


def is_gnews_url(url: str | None) -> bool:
    try:
        return (urlparse(url or "").hostname or "").lower() == GNEWS_HOST
    except Exception:
        return False


def resolve_publisher_url(gn_url: str, session, timeout: float = DECODE_TIMEOUT_S) -> str | None:
    """Decode a news.google.com link to its publisher URL, or None.

    Never raises. Returns None when the decoder fails, returns a non-http(s)
    value, or hands back a news.google.com URL (including the input itself)."""
    try:
        # Module attribute lookup at call time (patchable; key_link to decode_gnews_url).
        decoded = gnews_decoder.decode_gnews_url(gn_url, session=session, timeout=timeout)
    except Exception:
        logger.debug("gnews ingest decode raised for %s", (gn_url or "")[:80])
        return None
    if not decoded or not isinstance(decoded, str):
        return None
    if not is_safe_url(decoded):
        return None
    try:
        host = (urlparse(decoded).hostname or "").lower()
    except Exception:
        return None
    if not host or host == GNEWS_HOST:
        return None
    try:
        return _canonical_url(decoded)
    except Exception:
        return None


class DecodeBudget:
    """Per-run decode budget and courtesy pacing (G-31).

    Usage per candidate:
        if budget.allow():
            budget.wait()      # sleeps `delay` except before the first decode
            ... decode ...
            budget.charge()    # adds the wait + decode time to `spent`
    """

    def __init__(
        self,
        max_items: int = MAX_DECODES_PER_RUN,
        max_seconds: float = DECODE_BUDGET_S,
        delay: float = REQUEST_DELAY,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.max_items = int(max_items)
        self.max_seconds = float(max_seconds)
        self.delay = float(delay)
        self._clock = clock or time.monotonic
        # Resolved at call time so a patched time.sleep is honoured.
        self._sleep = sleep
        self.items = 0
        self.spent = 0.0
        self._mark: float | None = None

    def allow(self) -> bool:
        return self.items < self.max_items and self.spent < self.max_seconds

    def wait(self) -> None:
        self._mark = self._clock()
        if self.items > 0:
            (self._sleep or time.sleep)(self.delay)
        self.items += 1

    def charge(self) -> None:
        if self._mark is not None:
            self.spent += max(0.0, self._clock() - self._mark)
            self._mark = None
