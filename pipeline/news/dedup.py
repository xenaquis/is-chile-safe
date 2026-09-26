"""
pipeline/news/dedup.py

Cross-source deduplication for RSS incident records (NEWS-03).
Pure stdlib — difflib, re, unicodedata. No rapidfuzz, no LLM (D-10).

Strategy:
1. Canonical-URL dedup: strip utm_* tracking params, collapse same URL.
   FID-04 (36-05): url and via_url are one identity.
2. Title-similarity dedup within (cut, date) buckets using difflib.SequenceMatcher.
   Threshold: 0.82 (D-10 — start value).

FID-05 (36-05): the same rule runs cross-run inside store.merge_and_write
(prune_near_duplicates / filter_new_against). Deterministic; no LLM clustering
(v2.1 lock).
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


DroppedPair = tuple[dict, str, str]


def _url_keys(inc: dict) -> set[str]:
    """URL identity (FID-04): canonical url, plus canonical via_url when present."""
    keys = {_canonical_url(inc.get("url", ""))}
    via = inc.get("via_url")
    if via:
        keys.add(_canonical_url(via))
    return keys


def _title_match(norm: str, kept: list[tuple[str, str]]) -> tuple[str, float] | None:
    """Return (kept_id, ratio) of the first kept title in the bucket with ratio >= threshold."""
    for kept_norm, kept_id in kept:
        ratio = difflib.SequenceMatcher(None, norm, kept_norm).ratio()
        if ratio >= _THRESHOLD:
            return kept_id, ratio
    return None


def _filter(
    items: list[dict],
    seen_urls: dict[str, str],
    bucket_titles: dict[tuple[str, str], list[tuple[str, str]]],
) -> tuple[list[dict], list[DroppedPair]]:
    """Two-phase keep-first filter against (and updating) the seeded url/title state."""
    dropped: list[DroppedPair] = []

    # --- Phase 1: canonical-URL identity (url | via_url) ---
    url_kept: list[dict] = []
    for inc in items:
        keys = _url_keys(inc)
        hit = next((seen_urls[k] for k in keys if k in seen_urls), None)
        if hit is not None:
            dropped.append((inc, hit, "url"))
            continue
        for k in keys:
            seen_urls[k] = inc.get("id", "")
        url_kept.append(inc)

    # --- Phase 2: title-similarity within (cut, date) buckets ---
    result: list[dict] = []
    for inc in url_kept:
        bucket = (inc.get("cut", ""), inc.get("date", ""))
        norm = normalize_title(inc.get("title_es", ""))
        match = _title_match(norm, bucket_titles[bucket])
        if match is not None:
            dropped.append((inc, match[0], f"title:{match[1]:.3f}"))
            continue
        bucket_titles[bucket].append((norm, inc.get("id", "")))
        result.append(inc)

    return result, dropped


def prune_near_duplicates(items: list[dict]) -> tuple[list[dict], list[DroppedPair]]:
    """
    FID-05: cross-run, deterministic; no LLM clustering (v2.1 lock).

    1. URL identity: an item whose canonical url OR via_url matches a kept item's
       url or via_url is a duplicate (reason "url").
    2. Within each (cut, date) bucket, an item whose normalized title_es has
       SequenceMatcher ratio >= 0.82 with a kept title is a duplicate
       (reason "title:<ratio>").

    Keep-first, order-stable. Returns (kept, dropped) where each dropped entry is
    (item, kept_id, reason).
    """
    return _filter(items, {}, defaultdict(list))


def filter_new_against(
    existing: list[dict], new: list[dict]
) -> tuple[list[dict], list[DroppedPair]]:
    """
    FID-05: cross-run, deterministic; no LLM clustering (v2.1 lock).

    Seed url keys and bucket titles from `existing` (never dropping or modifying
    existing), then keep-first filter `new` with the same rule as
    prune_near_duplicates. Returns (kept_new, dropped).
    """
    seen_urls: dict[str, str] = {}
    bucket_titles: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for inc in existing:
        for k in _url_keys(inc):
            seen_urls.setdefault(k, inc.get("id", ""))
        bucket = (inc.get("cut", ""), inc.get("date", ""))
        bucket_titles[bucket].append((normalize_title(inc.get("title_es", "")), inc.get("id", "")))
    return _filter(new, seen_urls, bucket_titles)


def deduplicate(incidents: list[dict]) -> list[dict]:
    """
    Deduplicate a list of incident dicts (thin wrapper over prune_near_duplicates).

    1. Collapse canonical-URL duplicates (url | via_url identity; keep first occurrence).
    2. Within each (cut, date) bucket, drop title-similar near-duplicates
       using difflib.SequenceMatcher (threshold 0.82), keeping first occurrence.

    Order is preserved; attribution fields are not modified.
    """
    return prune_near_duplicates(incidents)[0]
