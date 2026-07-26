"""
pipeline/archive_r2.py

Consolidate all classified news incidents (current + monthly archives) and
upload a citable research dataset to the operator's Cloudflare R2 bucket.

Uploads to research-archive/ in the configured bucket:
  incidents.jsonl          — all incidents, one JSON object per line
  incidents.csv            — UTF-8 BOM CSV for spreadsheet consumers
  manifest.json            — metadata envelope
  url-ledger.jsonl         — per-incident fetch accounting (state store in R2)
  corpus-state.json        — aggregate stats: totals (per kind), by-outlet/family/month, corpus_sha256
  corpus-state-history/YYYY-MM-DD.json — daily snapshot of corpus-state
  articles/{id}.json       — full article text + metadata (append-only, private)
  rejected.jsonl           — rejected candidates with APA citations

SAFEGUARDS:
  - SHA-256 per article (text_sha256) + corpus_sha256 over sorted per-article hashes
  - Append-only article objects: fetched ids are never overwritten
  - Atomic single-object put_object uploads
  - Secrets logged by NAME only — never values
  - 2 MB article text cap (enforced in pipeline/news/fulltext.py)
  - Per-run fetch cap via ARCHIVE_MAX_FETCH (default 100); incidents consumed first
  - 15 s timeout + 1.5 s inter-request courtesy delay
  - Graceful exit 0 when any R2_* env var is missing
  - Legacy ledger rows without `kind` field default to "incident" on merge (T-gf7-06)

COPYRIGHT NOTE: Full article text is stored ONLY in the operator's private R2
bucket for research purposes. Do NOT publish raw article text publicly. APA
attribution is retained in all public-facing outputs.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import os
import pathlib
import sys
import time
from collections import Counter
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Repo-root resolution (mirrors scrape_news.py pattern)
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Dotenv load (no-op in CI; try/except mirrors scrape_news.py)
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=pathlib.Path(__file__).parent / ".env")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Module-level imports patchable by tests
# ---------------------------------------------------------------------------
from pipeline.news.fulltext import (  # noqa: E402
    fetch_article,
    build_article_object,
    REQUEST_DELAY,
)
import requests  # noqa: E402  (needed for except clause in main)
import boto3  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LEDGER_KEY = "research-archive/url-ledger.jsonl"
MAX_ATTEMPTS = 3
ARCHIVE_BASE = "research-archive"
SCHEMA_VERSION = 2  # bumped: per-kind totals + rejected_by_stage

_SPANISH_MONTHS = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


# ---------------------------------------------------------------------------
# APA-7 citation (Spanish)
# ---------------------------------------------------------------------------

def format_apa(inc: dict) -> str:
    """
    Build a Spanish APA-7 citation string for one incident.

    Pattern: "{outlet}. ({year}, {day} de {month}). {title_es}. {url}"
    Missing outlet → "s. a."
    Unparseable/missing date → "(s. f.)"
    """
    raw_outlet = (inc.get("outlet") or "").strip()
    outlet = raw_outlet if raw_outlet else None
    # Accept title_es for incidents, fall back to title for rejected items
    title = inc.get("title_es") or inc.get("title") or ""
    url = inc.get("url", "") or ""
    raw_date = inc.get("date", "") or ""

    try:
        d = datetime.strptime(raw_date[:10], "%Y-%m-%d")
        date_str = f"({d.year}, {d.day} de {_SPANISH_MONTHS[d.month]})"
    except (ValueError, KeyError):
        date_str = "(s. f.)"

    if outlet:
        return f"{outlet}. {date_str}. {title}. {url}"
    else:
        return f"s. a. {date_str}. {title}. {url}"


# ---------------------------------------------------------------------------
# Incident loading / consolidation
# ---------------------------------------------------------------------------

def _load_incidents_list(path: pathlib.Path) -> list:
    """Load incidents array from a JSON envelope file."""
    try:
        data = json.loads(path.read_text("utf-8"))
        if isinstance(data, dict):
            return data.get("incidents", [])
        return []
    except Exception:
        return []


def consolidate_incidents(data_dir: pathlib.Path) -> list:
    """
    Load current.json + all archive/*.json, dedup by id (current wins),
    attach apa to every record, return list sorted by date desc.
    """
    seen: dict[str, dict] = {}

    # Load archives first (lower priority)
    archive_dir = data_dir / "archive"
    if archive_dir.is_dir():
        for p in sorted(archive_dir.glob("*.json")):
            for inc in _load_incidents_list(p):
                inc_id = inc.get("id")
                if inc_id and inc_id not in seen:
                    seen[inc_id] = inc

    # Load current (wins on conflict)
    current_path = data_dir / "current.json"
    if current_path.exists():
        for inc in _load_incidents_list(current_path):
            inc_id = inc.get("id")
            if inc_id:
                seen[inc_id] = inc  # overwrite archive record

    # Attach APA citations
    result = []
    for inc in seen.values():
        inc = dict(inc)
        inc["apa"] = format_apa(inc)
        result.append(inc)

    # Sort by date descending (most recent first)
    result.sort(key=lambda x: x.get("date", ""), reverse=True)
    return result


def consolidate_rejected(data_dir: pathlib.Path) -> list:
    """
    Load all data_dir/rejected/*.json monthly envelopes, dedup by id (first-seen wins),
    attach apa to each record, return list.

    Tolerates missing rejected/ dir → returns [].
    """
    rejected_dir = data_dir / "rejected"
    if not rejected_dir.is_dir():
        return []

    seen: dict[str, dict] = {}
    for p in sorted(rejected_dir.glob("*.json")):
        try:
            envelope = json.loads(p.read_text("utf-8"))
            for item in envelope.get("items", []):
                item_id = item.get("id")
                if item_id and item_id not in seen:
                    # Build APA-compatible dict (rejected uses 'title', not 'title_es')
                    rec = dict(item)
                    rec["apa"] = format_apa(rec)
                    seen[item_id] = rec
        except Exception:
            pass

    return list(seen.values())


# ---------------------------------------------------------------------------
# R2 client factory
# ---------------------------------------------------------------------------

def _make_r2_client(endpoint_url: str, access_key: str, secret_key: str):
    """Thin boto3 S3 client factory pointing at Cloudflare R2."""
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def to_jsonl(incidents: list) -> bytes:
    """Encode incidents as UTF-8 JSONL bytes."""
    lines = [json.dumps(inc, ensure_ascii=False) for inc in incidents]
    return "\n".join(lines).encode("utf-8")


def to_csv(incidents: list) -> bytes:
    """
    Encode incidents as UTF-8 BOM CSV bytes.
    Header: id,date,cut,slug,family,outlet,title_es,title_en,url,lat,lng,apa
    """
    buf = io.StringIO()
    fieldnames = ["id", "date", "cut", "slug", "family", "outlet",
                  "title_es", "title_en", "url", "lat", "lng", "apa"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore",
                            lineterminator="\n")
    writer.writeheader()
    for inc in incidents:
        writer.writerow({f: inc.get(f, "") for f in fieldnames})
    return b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")


def build_manifest(incidents: list, generated: str) -> dict:
    return {
        "generated": generated,
        "total_incidents": len(incidents),
        "schema_version": SCHEMA_VERSION,
        "source_note": (
            "Datos de incidentes clasificados obtenidos de fuentes RSS de prensa chilena. "
            "Cada incidente incluye cita APA-7 en español con atribución al medio de origen. "
            "Uso permitido para investigación. No redistribuir texto completo de artículos."
        ),
    }


# ---------------------------------------------------------------------------
# Ledger helpers
# ---------------------------------------------------------------------------

def _download_ledger(client, bucket: str) -> dict:
    """
    Download url-ledger.jsonl from R2 and parse into a dict keyed by id.
    Returns {} on any error (first-run tolerated — never crashes).
    """
    try:
        resp = client.get_object(Bucket=bucket, Key=LEDGER_KEY)
        body = resp["Body"].read().decode("utf-8")
        rows = {}
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                rows[row["id"]] = row
            except (json.JSONDecodeError, KeyError):
                pass
        return rows
    except Exception:
        return {}


def merge_ledger(existing: dict, records: list, outcomes: dict, kind: str = "incident") -> dict:
    """
    Merge fetch outcomes into the ledger.

    Rules:
    - existing row with status "fetched" → UNCHANGED (append-only guard)
    - successful outcome → status "fetched", set final_url/text_sha256/char_count/fetched_at
    - failed outcome → attempts += 1; status "permanent_failure" if attempts >= MAX_ATTEMPTS
    - no outcome this run → keep prior status/attempts
    - legacy rows WITHOUT a kind field → default to "incident" on creation/merge (T-gf7-06)
    - existing rows with kind already set → NEVER overwrite kind
    Returns: dict keyed by id.
    """
    ledger = dict(existing)

    for rec in records:
        rec_id = rec.get("id", "")
        if not rec_id:
            continue

        # Existing fetched row — immutable (append-only guard)
        if rec_id in ledger and ledger[rec_id].get("status") == "fetched":
            continue

        # Start from existing row or create new
        row = ledger.get(rec_id) or {
            "id": rec_id,
            "url": rec.get("url", ""),
            "final_url": None,
            "status": "pending",
            "attempts": 0,
            "fetched_at": None,
            "text_sha256": None,
            "char_count": 0,
        }
        row = dict(row)

        # Set kind: prefer existing row's kind; default legacy rows to "incident" (T-gf7-06)
        if "kind" not in row:
            row["kind"] = kind

        outcome = outcomes.get(rec_id)
        if outcome is None:
            # No fetch attempted this run
            ledger[rec_id] = row
            continue

        if outcome.get("ok"):
            row["status"] = "fetched"
            row["final_url"] = outcome.get("final_url")
            row["text_sha256"] = outcome.get("text_sha256")
            row["char_count"] = outcome.get("char_count", 0)
            row["fetched_at"] = outcome.get("fetched_at")
        else:
            row["attempts"] = row.get("attempts", 0) + 1
            if row["attempts"] >= MAX_ATTEMPTS:
                row["status"] = "permanent_failure"
            else:
                row["status"] = "failed"

        ledger[rec_id] = row

    return ledger


# ---------------------------------------------------------------------------
# Corpus state (schema_version 2: per-kind totals + rejected_by_stage)
# ---------------------------------------------------------------------------

def build_corpus_state(ledger: dict, incidents: list, rejected: list | None = None) -> dict:
    """
    Summarise the research corpus from ledger rows + incidents + rejected metadata.

    Schema v2 totals are split by kind:
        totals = {
            "incidents": {fetched_ok, failed, pending, permanent_failure},
            "rejected":  {fetched_ok, failed, pending, permanent_failure},
        }

    by_outlet / by_family / by_month are derived from incidents only (existing behavior).
    rejected_by_stage is derived from the rejected list.
    corpus_sha256 covers all fetched sha256s regardless of kind.
    """
    if rejected is None:
        rejected = []

    # Build incident lookup for metadata
    inc_by_id: dict[str, dict] = {i.get("id", ""): i for i in incidents}

    # Per-kind totals
    kind_totals: dict[str, dict] = {
        "incidents": {"fetched_ok": 0, "failed": 0, "pending": 0, "permanent_failure": 0},
        "rejected": {"fetched_ok": 0, "failed": 0, "pending": 0, "permanent_failure": 0},
    }
    total_chars = 0
    fetched_sha256s: list[str] = []

    for row in ledger.values():
        status = row.get("status", "pending")
        # Legacy rows without kind default to "incident" (T-gf7-06)
        row_kind = row.get("kind", "incident")
        # Normalise to known kinds
        kind_key = "rejected" if row_kind == "rejected" else "incidents"
        bucket = kind_totals[kind_key]

        if status == "fetched":
            bucket["fetched_ok"] += 1
            total_chars += row.get("char_count", 0)
            sha = row.get("text_sha256")
            if sha:
                fetched_sha256s.append(sha)
        elif status == "permanent_failure":
            bucket["permanent_failure"] += 1
        elif status == "failed":
            bucket["failed"] += 1
        else:
            bucket["pending"] += 1

    # by_outlet / by_family / by_month from incidents list (incidents only, as before)
    by_outlet: dict[str, int] = Counter()
    by_family: dict[str, int] = Counter()
    by_month: dict[str, int] = Counter()
    for inc in incidents:
        outlet = inc.get("outlet") or "unknown"
        family = inc.get("family") or "unknown"
        month = (inc.get("date") or "")[:7] or "unknown"
        by_outlet[outlet] += 1
        by_family[family] += 1
        by_month[month] += 1

    # rejected_by_stage: Counter over rejected items
    rejected_by_stage: dict[str, int] = Counter(
        r.get("rejection_stage") or "unknown" for r in rejected
    )

    # corpus_sha256 = sha256 over sorted per-article text_sha256s joined by newline
    corpus_sha256 = hashlib.sha256(
        "\n".join(sorted(fetched_sha256s)).encode("utf-8")
    ).hexdigest()

    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "totals": kind_totals,
        "rejected_by_stage": dict(rejected_by_stage),
        "by_outlet": dict(by_outlet),
        "by_family": dict(by_family),
        "by_month": dict(by_month),
        "total_chars": total_chars,
        "corpus_sha256": corpus_sha256,
        "schema_version": SCHEMA_VERSION,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Consolidate incidents + rejected + full-text archive + upload to R2.

    Returns 0 always (clean CI exit). Uploads only happen when all R2_* vars present.
    """
    # Required R2 environment variables
    required_vars = ["R2_ENDPOINT_URL", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"]
    missing = [v for v in required_vars if not os.environ.get(v, "").strip()]
    if missing:
        for var in missing:
            logger.warning(
                "%s is not set — R2 archive upload skipped. "
                "Set it in pipeline/.env (dev) or as a repo secret (CI).",
                var,
            )
        return 0

    endpoint_url = os.environ["R2_ENDPOINT_URL"].strip()
    access_key = os.environ["R2_ACCESS_KEY_ID"].strip()
    secret_key = os.environ["R2_SECRET_ACCESS_KEY"].strip()
    # `or` fallback: GitHub Actions injects unset secrets as empty strings, so a
    # plain .get() default never kicks in and boto3 gets Bucket="" (run 30208466155).
    bucket = os.environ.get("R2_BUCKET", "").strip() or "ischilesafe"
    max_fetch = int(os.environ.get("ARCHIVE_MAX_FETCH", "100"))

    # Resolve data dir
    data_dir = _REPO_ROOT / "data" / "incidents"

    # Load + consolidate incidents and rejected
    incidents = consolidate_incidents(data_dir)
    logger.info("Consolidated %d unique incidents", len(incidents))
    rejected = consolidate_rejected(data_dir)
    logger.info("Consolidated %d rejected candidates", len(rejected))

    # Tag each record with kind in-memory for fetch bookkeeping
    for inc in incidents:
        inc["_kind"] = "incident"
    for rej in rejected:
        rej["_kind"] = "rejected"

    # Build R2 client + preflight: verify the bucket is reachable BEFORE spending
    # up to `max_fetch` courtesy-throttled article fetches. Bad credentials or a
    # wrong bucket must fail loud here (exit 1 → CI alert issue), not as 100
    # per-object upload warnings after minutes of wasted fetching.
    client = _make_r2_client(endpoint_url, access_key, secret_key)
    try:
        client.head_bucket(Bucket=bucket)
    except Exception as exc:
        logger.error(
            "R2 preflight failed for bucket %r: %s — aborting before any fetch. "
            "Check R2_* secrets and bucket name.",
            bucket, type(exc).__name__,
        )
        return 1

    ledger = _download_ledger(client, bucket)
    logger.info("Ledger loaded: %d rows", len(ledger))

    # Determine pending records — incidents first, then rejected (within cap)
    _not_done = {"pending", "failed"}

    def _is_pending(rec: dict) -> bool:
        rec_id = rec.get("id")
        return bool(
            rec_id
            and (
                rec_id not in ledger
                or ledger[rec_id].get("status") in _not_done
            )
        )

    pending_incidents = [inc for inc in incidents if _is_pending(inc)]
    pending_rejected = [rej for rej in rejected if _is_pending(rej)]

    # Incidents consume the cap first; rejected get the remainder
    pending_combined = (pending_incidents + pending_rejected)[:max_fetch]
    logger.info(
        "%d records pending fetch (cap %d): %d incidents, %d rejected",
        len(pending_combined), max_fetch,
        len([r for r in pending_combined if r.get("_kind") == "incident"]),
        len([r for r in pending_combined if r.get("_kind") == "rejected"]),
    )

    # Fetch articles
    outcomes: dict[str, dict] = {}
    fetched_this_run = 0
    for i, rec in enumerate(pending_combined):
        rec_id = rec["id"]

        # Skip if already fetched (double-guard)
        if ledger.get(rec_id, {}).get("status") == "fetched":
            logger.debug("Skip already-fetched %s", rec_id)
            continue

        # Courtesy delay between requests (not before the first one)
        if i > 0:
            time.sleep(REQUEST_DELAY)

        try:
            res = fetch_article(rec["url"])
        except Exception as exc:
            logger.warning("fetch_article failed for id=%s: %s", rec_id, type(exc).__name__)
            outcomes[rec_id] = {"ok": False}
            continue

        if res.get("extraction_ok"):
            # Build article object — for rejected items, map title → title_es
            article_rec = dict(rec)
            if article_rec.get("_kind") == "rejected" and "title_es" not in article_rec:
                article_rec["title_es"] = article_rec.get("title", "")
            obj = build_article_object(article_rec, res)
            # Tag article object with kind
            obj["kind"] = rec.get("_kind", "incident")
            try:
                client.put_object(
                    Bucket=bucket,
                    Key=f"{ARCHIVE_BASE}/articles/{rec_id}.json",
                    Body=json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                    ContentType="application/json",
                )
                fetched_this_run += 1
                outcomes[rec_id] = {
                    "ok": True,
                    "final_url": obj["final_url"],
                    "text_sha256": obj["text_sha256"],
                    "char_count": obj["char_count"],
                    "fetched_at": obj["fetched_at"],
                }
            except Exception as exc:
                logger.warning("put_object failed for id=%s: %s", rec_id, type(exc).__name__)
                outcomes[rec_id] = {"ok": False}
        else:
            outcomes[rec_id] = {"ok": False}

    # Merge incidents and rejected into ledger (two passes with correct kind)
    ledger = merge_ledger(ledger, incidents, outcomes, kind="incident")
    ledger = merge_ledger(ledger, rejected, outcomes, kind="rejected")

    ledger_body = "\n".join(
        json.dumps(row, ensure_ascii=False) for row in ledger.values()
    ).encode("utf-8")
    client.put_object(
        Bucket=bucket,
        Key=LEDGER_KEY,
        Body=ledger_body,
        ContentType="application/x-ndjson",
    )

    # Corpus state (v2)
    state = build_corpus_state(ledger, incidents, rejected)
    state_bytes = json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    client.put_object(
        Bucket=bucket,
        Key=f"{ARCHIVE_BASE}/corpus-state.json",
        Body=state_bytes,
        ContentType="application/json",
    )
    client.put_object(
        Bucket=bucket,
        Key=f"{ARCHIVE_BASE}/corpus-state-history/{today}.json",
        Body=state_bytes,
        ContentType="application/json",
    )

    # Upload incidents.jsonl / incidents.csv / manifest.json
    generated = datetime.now(timezone.utc).isoformat()
    client.put_object(
        Bucket=bucket,
        Key=f"{ARCHIVE_BASE}/incidents.jsonl",
        Body=to_jsonl(incidents),
        ContentType="application/x-ndjson",
    )
    client.put_object(
        Bucket=bucket,
        Key=f"{ARCHIVE_BASE}/incidents.csv",
        Body=to_csv(incidents),
        ContentType="text/csv; charset=utf-8",
    )
    manifest = build_manifest(incidents, generated)
    client.put_object(
        Bucket=bucket,
        Key=f"{ARCHIVE_BASE}/manifest.json",
        Body=json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    # Upload rejected.jsonl
    client.put_object(
        Bucket=bucket,
        Key=f"{ARCHIVE_BASE}/rejected.jsonl",
        Body=to_jsonl(rejected),
        ContentType="application/x-ndjson",
    )

    total_fetched = sum(1 for r in ledger.values() if r.get("status") == "fetched")
    total_pending = sum(
        1 for r in ledger.values() if r.get("status") in {"pending", "failed"}
    )
    logger.info(
        "Archive run complete. fetched_this_run=%d total_fetched=%d pending=%d",
        fetched_this_run, total_fetched, total_pending,
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    raise SystemExit(main())
