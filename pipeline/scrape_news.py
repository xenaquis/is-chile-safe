#!/usr/bin/env python3
"""
pipeline/scrape_news.py

RSS news pipeline entrypoint. Runs the full pipeline:
  1. Load VALID_CUTS set and per-feed FEEDS registry
  2. For each feed: fetch entries, filter by keyword (D-02), skip seen URLs (D-03)
  3. Cap candidates at MAX_CLASSIFICATIONS_PER_RUN to bound DeepSeek cost (D-17)
  4. For each candidate: classify via DeepSeek v4-flash; reject if None (commune invalid /
     low confidence / parse error)
  5. Resolve centroid (lat, lng) from centroids.json (D-08); skip if unknown CUT
  6. Build IncidentRecord dicts with full attribution (outlet, url, date — NEWS-05)
  7. Deduplicate across sources (NEWS-03)
  8. merge_and_write into data/incidents/current.json (NEWS-04, D-15 atomic gate)
  9. Update + save seen-URL ledger (D-03)

Exit codes:
  0 = success
  1 = key absent, validation failure, or unrecoverable error (D-14)

Usage:
  python pipeline/scrape_news.py
  NEWS_DATA_DIR=/custom/path python pipeline/scrape_news.py
  NEWS_MAX_CLASSIFY=50 python pipeline/scrape_news.py
"""
from __future__ import annotations

import logging
import os
import pathlib
import socket
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Repo-relative output directory (overridable via env for tests)
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).parent.parent

# Ensure the repo root is importable when run as a script
# (`python pipeline/scrape_news.py` in CI/cron): sys.path[0] would otherwise be this
# script's directory, hiding the top-level `pipeline` package and breaking the
# `from pipeline.news...` imports in main(). Latent until DEEPSEEK_API_KEY was set in
# CI — the key-absent guard returns cleanly before those imports ever run.
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_DEFAULT_DATA_DIR = _REPO_ROOT / "data" / "incidents"


def _get_data_dir() -> pathlib.Path:
    override = os.environ.get("NEWS_DATA_DIR")
    return pathlib.Path(override) if override else _DEFAULT_DATA_DIR


# ---------------------------------------------------------------------------
# Per-run classification cap (D-17 cost control)
# ---------------------------------------------------------------------------
MAX_CLASSIFICATIONS_PER_RUN: int = int(os.environ.get("NEWS_MAX_CLASSIFY", "200"))


# ---------------------------------------------------------------------------
# main() — orchestrator entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Run the full RSS news pipeline.

    Returns:
        0 on success, 1 on any failure.
    """
    # CR-01: bound every network read (feedparser has no native timeout) so a single
    # stalled feed server cannot hang the whole cron run indefinitely.
    socket.setdefaulttimeout(30)

    # Load dotenv early so env vars are available (no-op in CI where secrets are set directly)
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=pathlib.Path(__file__).parent / ".env")
    except ImportError:
        pass  # python-dotenv not installed — env vars must be set by caller

    # T-05-04-02 / T-16-09: Provider-aware key check — log clear message, never print key value.
    # Degrade gracefully (CLAUDE.md: "pipeline debe fallar con gracia y alertar"):
    # without a key the pipeline cannot classify, so skip this run cleanly (exit 0)
    # instead of failing the scheduled CI job every 6h. No key -> no data change ->
    # no commit/deploy.
    # Pitfall 6 (Plan 03): key check must be provider-aware. Must mirror the
    # provider→key mapping in pipeline/news/classifier.py (default: openrouter
    # → OPENROUTER_API_KEY since quick-260726-dqf / spike 008).
    _provider = os.environ.get("NEWS_PROVIDER", "openrouter").strip().lower()
    _key_env = {
        "minimax": "MINIMAX_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }.get(_provider, "OPENROUTER_API_KEY")
    api_key = os.environ.get(_key_env, "").strip()
    if not api_key:
        logger.warning(
            "%s is not set — skipping news classification this run. "
            "Set it in pipeline/.env (dev) or as a repo secret (CI) to enable the pipeline. "
            "Exiting cleanly with no data change.",
            _key_env,
        )
        return 0

    data_dir = _get_data_dir()
    current_path = data_dir / "current.json"
    archive_dir = data_dir / "archive"
    seen_path = data_dir / "seen.json"

    logger.info("News pipeline starting. Output dir: %s", data_dir)
    logger.info("MAX_CLASSIFICATIONS_PER_RUN = %d (D-17)", MAX_CLASSIFICATIONS_PER_RUN)

    try:
        # Local imports mirror scrape_cead.py pattern (injected after env setup)
        from pipeline.news.feeds import (
            FEEDS,
            canonical_url,
            fetch_feed,
            filter_seen,
            is_crime_item,
            load_seen,
            parse_pub_date,
            resolve_outlet,
            save_seen,
            strip_html,
        )
        from pipeline.news.classifier import classify
        from pipeline.news.centroids import get_centroid
        from pipeline.news.dedup import deduplicate
        from pipeline.news.store import build_incident, make_id, merge_and_write
        from pipeline.news.schema import VALID_CUTS
        from pipeline.news.resolver import resolve_cut

        # Load seen-URL ledger (D-03)
        seen = load_seen(path=seen_path)
        seen_set: set[str] = set(seen.keys())

        # Collect all unseen crime candidates across feeds
        candidates: list[dict] = []
        fetched_total = 0
        keyword_passed = 0

        for feed_name, feed_url in FEEDS.items():
            try:
                entries = fetch_feed(feed_name, feed_url)
                fetched_total += len(entries)
                if not entries:
                    logger.warning("[%s] No entries returned (feed down or empty)", feed_name)
                    continue
                logger.info("[%s] Fetched %d entries", feed_name, len(entries))

                for entry in entries:
                    url = canonical_url(entry, feed_name)
                    if not url:
                        continue

                    title = getattr(entry, "title", "") or ""
                    raw_desc = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
                    description = strip_html(raw_desc)
                    pub_date = parse_pub_date(entry)

                    # Keyword pre-filter (D-02)
                    if not is_crime_item({"title": title, "description": description}):
                        continue
                    keyword_passed += 1

                    # Skip seen URLs (D-03) — also tracks within-run duplicates
                    if url in seen_set:
                        continue
                    # Mark as seen within this run to deduplicate across feeds/entries
                    seen_set.add(url)

                    candidates.append({
                        "url": url,
                        "title": title,
                        "description": description,
                        "date": pub_date.isoformat(),
                        "outlet": resolve_outlet(entry, feed_name),
                    })

            except Exception as exc:
                logger.warning("[%s] Per-feed error (skipping): %s", feed_name, exc)
                continue

        logger.info(
            "Fetch summary: fetched=%d, keyword_passed=%d, unseen_candidates=%d",
            fetched_total, keyword_passed, len(candidates),
        )

        # D-17: cap candidates to bound DeepSeek API cost
        if len(candidates) > MAX_CLASSIFICATIONS_PER_RUN:
            logger.warning(
                "Capping candidates from %d to %d (NEWS_MAX_CLASSIFY / D-17)",
                len(candidates), MAX_CLASSIFICATIONS_PER_RUN,
            )
            candidates = candidates[:MAX_CLASSIFICATIONS_PER_RUN]

        # Classify + resolve centroid
        new_incidents: list[dict] = []
        classified = 0
        rejected = 0

        for item in candidates:
            # CR-02: mark the URL seen as soon as we attempt classification — BEFORE any
            # reject path. Otherwise rejected URLs (low confidence / bad CUT / no centroid)
            # are never recorded and get re-classified on every run, defeating the D-17 cost
            # guardrail and burning DeepSeek quota indefinitely.
            seen[item["url"]] = item["date"]

            # RESEARCH Open Q1: log rejection reason where available
            result = classify(item["title"], item["description"])
            if result is None:
                logger.debug(
                    "Rejected (classifier): url=%s title=%r",
                    item["url"], item["title"][:60],
                )
                rejected += 1
                continue

            # T-16-07: Resolve LLM commune_name → (cut, slug) via deterministic closed-set lookup.
            # Returns None for unknown/hallucinated names → drop incident (anti-hallucination guard).
            # Never let an unresolved name reach the store.
            resolved = resolve_cut(result.commune_name, result.region_hint) if result.commune_name else None
            if resolved is None:
                logger.debug(
                    "Rejected (unresolved commune name %r): title=%r",
                    result.commune_name, item["title"][:60],
                )
                rejected += 1
                continue
            cut, slug = resolved

            centroid = get_centroid(cut)
            if centroid is None:
                logger.warning(
                    "Rejected (centroid not found for CUT %s): title=%r",
                    cut, item["title"][:60],
                )
                rejected += 1
                continue

            lat, lng = centroid
            incident = build_incident(
                url=item["url"],
                cut=cut,
                lat=lat,
                lng=lng,
                title_es=result.title_es,
                title_en=result.title_en,
                date=item["date"],
                outlet=item["outlet"],
                family=result.family,
                slug=slug,
            )
            new_incidents.append(incident)
            classified += 1
            # (URL already marked seen at loop top — CR-02)

        logger.info(
            "Classification summary: classified=%d, rejected=%d",
            classified, rejected,
        )

        # Cross-source deduplication (NEWS-03)
        deduped = deduplicate(new_incidents)
        logger.info(
            "Deduplication: %d -> %d incidents (removed %d near-duplicates)",
            len(new_incidents), len(deduped), len(new_incidents) - len(deduped),
        )

        # Merge into rolling window + validate + atomic write (NEWS-04, D-15)
        data_dir.mkdir(parents=True, exist_ok=True)
        merge_and_write(deduped, current_path, archive_dir)
        logger.info("Written to %s", current_path)

        # Save updated seen-ledger (D-03)
        save_seen(seen, path=seen_path)
        logger.info("Seen-ledger saved (%d entries)", len(seen))

        logger.info("News pipeline completed successfully.")
        return 0

    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
