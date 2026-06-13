"""
pipeline/news/dedup.py

Cross-source deduplication for RSS incident records (NEWS-03).
Pure stdlib — difflib, re, unicodedata. No rapidfuzz, no LLM (D-10).

Strategy:
1. Canonical-URL dedup: strip utm_* tracking params, collapse same URL.
2. Title-similarity dedup within (cut, date) buckets using difflib.SequenceMatcher.
   Threshold: 0.82 (D-10 — start value).
"""
from __future__ import annotations

import difflib
import re
import unicodedata
import urllib.parse
from collections import defaultdict


_THRESHOLD: float = 0.82


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _canonical_url(url: str) -> str:
    """Strip utm_* and other common tracking query parameters."""
    parsed = urllib.parse.urlparse(url)
    if not parsed.query:
        return url
    params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    cleaned = {k: v for k, v in params.items() if not k.lower().startswith("utm_")}
    new_query = urllib.parse.urlencode(cleaned, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


def normalize_title(t: str) -> str:
    """NFD-normalize + lowercase + ascii-encode(ignore) + strip punctuation + collapse whitespace."""
    # NFD decompose
    nfd = unicodedata.normalize("NFD", t)
    # lowercase + ascii-only
    ascii_str = nfd.encode("ascii", "ignore").decode("ascii").lower()
    # strip punctuation (keep alphanumeric and spaces)
    no_punct = re.sub(r"[^a-z0-9\s]", " ", ascii_str)
    # collapse whitespace
    return re.sub(r"\s+", " ", no_punct).strip()


def are_duplicates(t1: str, t2: str, threshold: float = _THRESHOLD) -> bool:
    """Return True if the two titles are near-duplicates (SequenceMatcher ratio >= threshold)."""
    n1 = normalize_title(t1)
    n2 = normalize_title(t2)
    ratio = difflib.SequenceMatcher(None, n1, n2).ratio()
    return ratio >= threshold


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def deduplicate(incidents: list[dict]) -> list[dict]:
    """
    Deduplicate a list of incident dicts.

    1. Collapse exact canonical-URL duplicates (keep first occurrence).
    2. Within each (cut, date) bucket, drop title-similar near-duplicates
       using difflib.SequenceMatcher (threshold 0.82), keeping first occurrence.

    Order is preserved; attribution fields are not modified.
    """
    # --- Phase 1: canonical-URL dedup ---
    seen_urls: set[str] = set()
    url_deduped: list[dict] = []
    for inc in incidents:
        canon = _canonical_url(inc.get("url", ""))
        if canon in seen_urls:
            continue
        seen_urls.add(canon)
        url_deduped.append(inc)

    # --- Phase 2: title-similarity dedup within (cut, date) buckets ---
    # Map bucket -> list of already-kept normalized titles
    bucket_titles: dict[tuple[str, str], list[str]] = defaultdict(list)
    result: list[dict] = []

    for inc in url_deduped:
        cut = inc.get("cut", "")
        date = inc.get("date", "")
        bucket = (cut, date)
        norm = normalize_title(inc.get("title_es", ""))

        is_near_dup = any(
            are_duplicates(norm, kept, threshold=_THRESHOLD)
            for kept in bucket_titles[bucket]
        )
        if is_near_dup:
            continue

        bucket_titles[bucket].append(norm)
        result.append(inc)

    return result
