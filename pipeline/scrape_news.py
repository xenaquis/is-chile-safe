#!/usr/bin/env python3
"""
pipeline/scrape_news.py

RSS news pipeline entrypoint. Runs the full pipeline:
  1. Load VALID_CUTS set and per-feed FEEDS registry
  2. For each feed: fetch entries, filter by keyword (D-02), skip seen URLs (D-03)
  3. Retry queue (data/incidents/pending.json, G-03) items first, then fresh candidates;
     cap at MAX_CLASSIFICATIONS_PER_RUN to bound LLM cost (D-17)
  4. For each candidate: ProviderRouter.classify (Phase 34-02 — preflight, DeepSeek-direct
     failover, breaker, run budget) returns a typed outcome:
       OK → resolve/centroid/build; NOT_CRIME → rejected "low_confidence";
       PARSE_ERROR → rejected "parse_error" (all three mark the URL seen, CR-02);
       API_ERROR → queued in pending.json, NEVER seen, never rejected
  5. Resolve centroid (lat, lng) from centroids.json (D-08); skip if unknown CUT
  6. Build IncidentRecord dicts with full attribution (outlet, url, date — NEWS-05)
  7. Deduplicate across sources (NEWS-03)
  8. merge_and_write into data/incidents/current.json (NEWS-04, D-15 atomic gate)
  9. Update + save seen-URL ledger (D-03) and the retry queue
 10. Emit the run summary (schema 1) to the log, NEWS_RUN_SUMMARY_PATH and GITHUB_OUTPUT

Exit codes:
  0 = success (including the graceful no-key skip)
  1 = validation failure or unrecoverable error (D-14), including a failed summary write

Usage:
  python pipeline/scrape_news.py
  NEWS_DATA_DIR=/custom/path python pipeline/scrape_news.py
  NEWS_MAX_CLASSIFY=50 python pipeline/scrape_news.py
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import pathlib
import re
import socket
import sys
import time
from datetime import datetime, timezone

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


def _strip_html_simple(text: str) -> str:
    """Strip HTML tags for rejected record description (no BeautifulSoup dep at module level)."""
    return re.sub(r"<[^>]+>", "", text or "").strip()


def record_rejected(items: list[dict], data_dir: pathlib.Path) -> None:
    """
    Persist rejected news candidates to data_dir/rejected/YYYY-MM.json.

    Envelope: {"generated": <ISO UTC>, "items": [...]}.
    Deduplicates by url id within the month file (first_seen preserved, no overwrites).
    A failure here MUST NOT propagate — caller wraps in try/except.
    """
    if not items:
        return

    now = datetime.now(timezone.utc)
    month_key = now.strftime("%Y-%m")
    rejected_dir = data_dir / "rejected"
    rejected_dir.mkdir(parents=True, exist_ok=True)
    target = rejected_dir / f"{month_key}.json"

    # Load existing file (tolerate missing/malformed)
    existing_items: dict[str, dict] = {}
    if target.exists():
        try:
            envelope = json.loads(target.read_text("utf-8"))
            for record in envelope.get("items", []):
                rec_id = record.get("id")
                if rec_id:
                    existing_items[rec_id] = record
        except Exception:
            pass

    first_seen_iso = now.isoformat()

    for item in items:
        url = item.get("url") or ""
        item_id = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

        # Dedup: skip if already present (preserve original first_seen)
        if item_id in existing_items:
            continue

        description_raw = item.get("description") or ""
        description = _strip_html_simple(description_raw)[:500]

        existing_items[item_id] = {
            "id": item_id,
            "url": url,
            "outlet": item.get("outlet") or "",
            "date": item.get("date") or "",
            "title": item.get("title") or "",
            "description": description,
            "rejection_stage": item.get("rejection_stage") or "",
            "first_seen": first_seen_iso,
        }

    envelope = {
        "generated": now.isoformat(),
        "items": list(existing_items.values()),
    }
    target.write_text(json.dumps(envelope, indent=2, ensure_ascii=False), encoding="utf-8")


def _get_data_dir() -> pathlib.Path:
    override = os.environ.get("NEWS_DATA_DIR")
    return pathlib.Path(override) if override else _DEFAULT_DATA_DIR


# ---------------------------------------------------------------------------
# Per-run classification cap (D-17 cost control)
# ---------------------------------------------------------------------------
def _int_env(name: str, default: int) -> int:
    """Parse an int env var, falling back to default on any malformed value
    rather than crashing the always-exit-0 pipeline (WR-03)."""
    try:
        val = int(os.environ.get(name, str(default)))
        return val if val >= 0 else default
    except ValueError:
        logger.warning("%s invalid — falling back to %d", name, default)
        return default


MAX_CLASSIFICATIONS_PER_RUN: int = _int_env("NEWS_MAX_CLASSIFY", 200)


# ---------------------------------------------------------------------------
# Run summary (schema 1 — the 34-03 health-gate contract, G-04 / G-09)
# ---------------------------------------------------------------------------

RUN_SUMMARY_SCHEMA = 1


def _base_summary(router) -> dict:
    return {
        "schema": RUN_SUMMARY_SCHEMA,
        "attempted": 0,
        "responded": 0,
        "accepted": 0,
        "genuine_rejects": 0,
        "parse_errors": 0,
        "api_errors": 0,
        "failovers": getattr(router, "failovers", 0),
        "failover_reason": getattr(router, "failover_reason", None),
        "backup_exhausted": bool(getattr(router, "backup_exhausted", False)),
        "queued": 0,
        "expired": 0,
        "not_attempted": 0,
        "downstream_rejects": 0,
        "preflight": getattr(router, "preflight_status", "skipped"),
        "primary": getattr(router, "primary_label", None),
        "backup": getattr(router, "backup_label", None),
        "skipped_reason": None,
        "empty_content": 0,
        "finish_length": 0,
        "redispatched": 0,
        "recovered_by_redispatch": 0,
        "budget_exhausted": bool(getattr(router, "budget_exhausted", False)),
        "served_by_counts": {},
    }


def _gh_output_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _emit_summary(summary: dict) -> None:
    """Log the summary and write it to NEWS_RUN_SUMMARY_PATH / GITHUB_OUTPUT when set.

    Write failures are NOT swallowed: missing evidence must never look healthy — the
    caller's except turns them into exit 1."""
    logger.info("Run summary: %s", json.dumps(summary, sort_keys=True))

    summary_path = os.environ.get("NEWS_RUN_SUMMARY_PATH", "").strip()
    if summary_path:
        path = pathlib.Path(summary_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    gh_output = os.environ.get("GITHUB_OUTPUT", "").strip()
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as fh:
            for key in sorted(summary):
                value = summary[key]
                if isinstance(value, (dict, list)):
                    continue  # scalars only
                fh.write(f"{key}={_gh_output_value(value)}\n")


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

    data_dir = _get_data_dir()
    current_path = data_dir / "current.json"
    archive_dir = data_dir / "archive"
    seen_path = data_dir / "seen.json"
    pending_path = data_dir / "pending.json"

    try:
        from pipeline.news.classifier import Outcome, build_router_from_env

        # Provider router (NREC-02/04): primary from model_config / NEWS_PROVIDER /
        # NEWS_MODEL, DeepSeek-direct backup. Clients built from os.environ NOW (R-12).
        router = build_router_from_env()

        # T-05-04-02 / T-16-09: key check — log env var NAMES only, never a key value.
        # Degrade gracefully (CLAUDE.md: "pipeline debe fallar con gracia y alertar"):
        # with neither the primary nor the backup key the pipeline cannot classify, so
        # skip this run cleanly (exit 0) — no key -> no data change -> no commit/deploy.
        if not router.any_key_present:
            logger.warning(
                "%s is not set — skipping news classification this run. "
                "Set it in pipeline/.env (dev) or as a repo secret (CI) to enable the pipeline. "
                "Exiting cleanly with no data change.",
                " / ".join(router.key_env_names) or "API key",
            )
            summary = _base_summary(router)
            summary["skipped_reason"] = "no_api_key"
            _emit_summary(summary)
            return 0

        logger.info("News pipeline starting. Output dir: %s", data_dir)
        logger.info("MAX_CLASSIFICATIONS_PER_RUN = %d (D-17)", MAX_CLASSIFICATIONS_PER_RUN)
        logger.info("Classifier primary=%s backup=%s", router.primary_label, router.backup_label)

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
            source_headline,
            strip_html,
        )
        from pipeline.news.centroids import get_centroid
        from pipeline.news.fidelity import forbidden_term, guard_title_en
        from pipeline.news.dedup import deduplicate
        from pipeline.news.store import build_incident, make_id, merge_and_write
        from pipeline.news.schema import VALID_CUTS, IncidentRecord
        from pydantic import ValidationError
        from pipeline.news.resolver import resolve_cut
        from pipeline.news.fulltext import REQUEST_DELAY
        from pipeline.news import pending as pq

        # NREC-03: OpenRouter preflight once, before any completion call.
        router.preflight()

        now = datetime.now(timezone.utc)

        # Load seen-URL ledger (D-03)
        seen = load_seen(path=seen_path)

        rejected_items: list[dict] = []
        expired_count = 0

        def _expire(entry: dict) -> None:
            """G-03: expired queue item → rejected/ api_error_expired + seen, so the
            feed cannot re-queue it forever."""
            nonlocal expired_count
            expired_count += 1
            rejected_items.append({
                "url": entry["url"],
                "title": entry.get("title") or "",
                "description": entry.get("description") or "",
                "date": entry.get("date") or "",
                "outlet": entry.get("outlet") or "",
                "rejection_stage": "api_error_expired",
            })
            seen[entry["url"]] = entry.get("date") or now.date().isoformat()

        # Retry queue (G-03): expire stale items BEFORE classification (not attempted).
        pending = pq.load_pending(pending_path)
        pending, expired_before = pq.split_expired(pending, now)
        for entry in expired_before:
            _expire(entry)

        seen_set: set[str] = set(seen.keys())
        pending_urls: set[str] = {p["url"] for p in pending}

        # Collect all unseen crime candidates across feeds
        fresh: list[dict] = []
        fetched_total = 0
        keyword_passed = 0

        for i, (feed_name, feed_url) in enumerate(FEEDS.items()):
            if i > 0:
                # SEC-06/F-108: courtesy delay toward press/RSS hosts (5 of 9
                # feeds hit news.google.com back-to-back) -- reuses the same
                # 1.5s constant fulltext.py already applies (archive_r2.py
                # precedent), never sleeping before the first feed.
                time.sleep(REQUEST_DELAY)
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

                    # Skip seen URLs (D-03) — also tracks within-run duplicates.
                    # Items already in the retry queue are classified once, from the queue.
                    if url in seen_set or url in pending_urls:
                        continue
                    # Mark as seen within this run to deduplicate across feeds/entries
                    seen_set.add(url)

                    outlet = resolve_outlet(entry, feed_name)
                    fresh.append({
                        "url": url,
                        "title": title,
                        "description": description,
                        "date": pub_date.isoformat(),
                        "outlet": outlet,
                        # FID-01 (G-28): the outlet's verbatim headline; derived, so
                        # never persisted to pending.json (upsert_failure picks keys).
                        "title_src": source_headline(title, outlet),
                    })

            except Exception as exc:
                logger.warning("[%s] Per-feed error (skipping): %s", feed_name, exc)
                continue

        logger.info(
            "Fetch summary: fetched=%d, keyword_passed=%d, unseen_candidates=%d",
            fetched_total, keyword_passed, len(fresh),
        )

        # Queued items first (first_queued order), then fresh candidates.
        queued_candidates = [
            {k: p.get(k) or "" for k in ("url", "title", "description", "date", "outlet")}
            for p in sorted(pending, key=lambda p: (p.get("first_queued") or "", p.get("id") or ""))
        ]
        for q in queued_candidates:
            q["title_src"] = source_headline(q["title"], q["outlet"])  # FID-01
        if queued_candidates:
            logger.info("Retry queue: %d pending item(s) re-attempted first", len(queued_candidates))
        candidates = queued_candidates + fresh

        # D-17: cap candidates to bound LLM API cost
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
        downstream_rejects = 0
        title_en_fallbacks = 0
        editorial_filtered = 0
        not_attempted = 0
        redispatched = 0
        recovered_by_redispatch = 0
        served_by_counts: dict[str, int] = {}
        final: dict[str, object] = {}       # key -> final ClassifyResult (after re-dispatch)
        by_key: dict[str, dict] = {}

        def _count_served(res) -> None:
            if getattr(res, "served_by", None):
                served_by_counts[res.served_by] = served_by_counts.get(res.served_by, 0) + 1

        def _answered(item: dict, key: str, res) -> None:
            """A provider answered (OK / NOT_CRIME / PARSE_ERROR)."""
            nonlocal pending, classified, rejected, downstream_rejects
            nonlocal title_en_fallbacks, editorial_filtered
            # Leaves the retry queue (this also reverses any attempt increment made
            # earlier in this run when the backup recovers it — R-04).
            pending = pq.remove(pending, key)
            # CR-02: mark the URL seen as soon as a provider ANSWERED — before any reject
            # path — so genuine rejects are never re-classified (D-17 cost guardrail).
            # API_ERROR outcomes never reach here: they go to pending.json, never seen.
            seen[item["url"]] = item["date"]

            if res.outcome is Outcome.NOT_CRIME:
                logger.debug("Rejected (low confidence): url=%s title=%r", item["url"], item["title"][:60])
                rejected += 1
                rejected_items.append({**item, "rejection_stage": "low_confidence"})
                return
            if res.outcome is Outcome.PARSE_ERROR:
                logger.debug("Rejected (parse error): url=%s title=%r", item["url"], item["title"][:60])
                rejected += 1
                rejected_items.append({**item, "rejection_stage": "parse_error"})
                return

            result = res.output
            # T-16-07: Resolve LLM commune_name → (cut, slug) via deterministic closed-set lookup.
            # Returns None for unknown/hallucinated names → drop incident (anti-hallucination guard).
            # Never let an unresolved name reach the store.
            resolved = resolve_cut(result.commune_name, result.region_hint) if result.commune_name else None
            if resolved is None:
                stage = "commune_null" if not result.commune_name else "resolver_fail"
                logger.debug(
                    "Rejected (unresolved commune name %r): title=%r",
                    result.commune_name, item["title"][:60],
                )
                rejected += 1
                downstream_rejects += 1
                rejected_items.append({**item, "rejection_stage": stage})
                return
            cut, slug = resolved

            centroid = get_centroid(cut)
            if centroid is None:
                logger.warning(
                    "Rejected (centroid not found for CUT %s): title=%r",
                    cut, item["title"][:60],
                )
                rejected += 1
                downstream_rejects += 1
                rejected_items.append({**item, "rejection_stage": "centroid_fail"})
                return

            lat, lng = centroid

            def _downstream_reject(stage: str) -> None:
                nonlocal rejected, downstream_rejects
                rejected += 1
                downstream_rejects += 1
                rejected_items.append({**item, "rejection_stage": stage})

            # FID-01 / FID-07 (G-28): store the outlet's verbatim headline; the
            # classifier's title_en passes the deterministic kinship guard.
            title_en, fell_back = guard_title_en(item["title_src"], result.title_en, item["outlet"])
            # G-29 editorial filter: absolute safety wording is never published.
            term = forbidden_term(item["title_src"]) or forbidden_term(title_en)
            if term:
                logger.info("Rejected (editorial filter %r): title=%r", term, item["title"][:60])
                editorial_filtered += 1
                _downstream_reject("editorial_filter")
                return
            if fell_back:
                title_en_fallbacks += 1

            incident = build_incident(
                url=item["url"],
                cut=cut,
                lat=lat,
                lng=lng,
                title_src=item["title_src"],
                title_en=title_en,
                date=item["date"],
                outlet=item["outlet"],
                family=result.family,
                slug=slug,
            )
            # Per-row guard (premortem R-14; mirrors the backfill twin): a None or a
            # schema-invalid incident is rejected on its own — never a crash in
            # deduplicate() and never an all-or-nothing skip in merge_and_write().
            if incident is None:
                _downstream_reject("url_rejected")
                return
            try:
                IncidentRecord.model_validate(incident)
            except ValidationError as exc:
                logger.warning("Rejected (invalid record): url=%s: %s", item["url"], exc)
                _downstream_reject("invalid_record")
                return
            new_incidents.append(incident)
            classified += 1

        for item in candidates:
            key = pq.item_id(item["url"])
            by_key[key] = item

            res = router.classify(item["title"], item["description"], key=key)
            if res is None:
                # Router exhausted or run budget spent (G-09): queue WITHOUT an attempt
                # increment; never seen, never rejected.
                pending = pq.upsert_failure(pending, item, now, None, attempted=False)
                not_attempted += 1
            else:
                final[key] = res
                _count_served(res)
                if res.outcome is Outcome.API_ERROR:
                    # Provider/transport failure (incl. G-09 empty_content / finish_length):
                    # NOT an answer → never seen, never rejected/, queued for retry.
                    pending = pq.upsert_failure(
                        pending, item, now, f"{res.error}:{res.status_code}", attempted=True,
                    )
                else:
                    _answered(item, key, res)

            # R-04 / G-09: the breaker trip re-dispatches the tripping streak to the
            # backup in the same run; apply the backup's answers to those items.
            for rkey, rres in router.pop_redispatched():
                redispatched += 1
                ritem = by_key.get(rkey)
                if ritem is None:
                    continue
                _count_served(rres)
                if rres.outcome is Outcome.API_ERROR:
                    continue  # backup failed too — the single attempt increment stays
                recovered_by_redispatch += 1
                final[rkey] = rres
                _answered(ritem, rkey, rres)

        # Deferred expiry (G-03): items that reached the attempt cap in this run.
        pending, expired_after = pq.split_expired(pending, now)
        for entry in expired_after:
            _expire(entry)

        logger.info(
            "Classification summary: classified=%d, rejected=%d",
            classified, rejected,
        )

        outcomes = list(final.values())
        api_error_results = [r for r in outcomes if r.outcome is Outcome.API_ERROR]
        summary = _base_summary(router)
        summary.update({
            "attempted": len(outcomes),
            "responded": sum(1 for r in outcomes if r.outcome in (Outcome.OK, Outcome.NOT_CRIME)),
            "accepted": classified,
            "genuine_rejects": sum(1 for r in outcomes if r.outcome is Outcome.NOT_CRIME),
            "parse_errors": sum(1 for r in outcomes if r.outcome is Outcome.PARSE_ERROR),
            "api_errors": len(api_error_results),
            "queued": len(pending),
            "expired": expired_count,
            "not_attempted": not_attempted,
            "downstream_rejects": downstream_rejects,
            "empty_content": sum(1 for r in api_error_results if r.error == "empty_content"),
            "finish_length": sum(1 for r in api_error_results if r.error == "finish_length"),
            "redispatched": redispatched,
            "recovered_by_redispatch": recovered_by_redispatch,
            "served_by_counts": dict(sorted(served_by_counts.items())),
            # FID-01 36-04: dict → skipped by _emit_summary's GITHUB_OUTPUT scalars.
            "fidelity": {
                "title_en_fallbacks": title_en_fallbacks,
                "editorial_filtered": editorial_filtered,
            },
        })

        # Persist rejected candidates for selection-bias research corpus
        try:
            record_rejected(rejected_items, data_dir)
        except Exception as _rej_exc:
            logger.warning("record_rejected failed (non-fatal): %s", _rej_exc)

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

        # Retry queue (written only when its content changed)
        if pq.save_pending(pending_path, pending):
            logger.info("Retry queue saved (%d pending)", len(pending))

        _emit_summary(summary)

        logger.info("News pipeline completed successfully.")
        return 0

    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
