"""
pipeline/news/pending.py

Retry queue for news items whose classification failed with a transient provider
error (API_ERROR — G-03 / G-09, NREC-05). File: data/incidents/pending.json.

Envelope (deterministic, no volatile "generated" field so a no-op run leaves the
file byte-identical — Phase-35 FRESH-04):
    {"items": [{"id", "url", "title", "description", "date", "outlet",
                "first_queued", "attempts", "last_error"}, ...]}
sorted by (first_queued, id).

G-03 knobs: an item expires after PENDING_MAX_ATTEMPTS attempts or
PENDING_MAX_AGE_DAYS days in the queue; the caller then records it in rejected/
with stage "api_error_expired" (never "classifier_none") and marks it seen.
"""
from __future__ import annotations

import hashlib
import json
import logging
import pathlib
from datetime import datetime, timedelta, timezone

from pipeline.shared.atomic_write import atomic_write_json

logger = logging.getLogger(__name__)

PENDING_MAX_ATTEMPTS = 5
PENDING_MAX_AGE_DAYS = 14


def item_id(url: str) -> str:
    """sha256(url)[:16] — same id scheme as rejected/ and store.make_id."""
    return hashlib.sha256((url or "").encode("utf-8")).hexdigest()[:16]


def _sorted(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda it: (it.get("first_queued") or "", it.get("id") or ""))


def _serialize(items: list[dict]) -> str:
    # Must match atomic_write_json(compact=False) byte-for-byte.
    return json.dumps({"items": _sorted(items)}, ensure_ascii=False, indent=2)


def load_pending(path: pathlib.Path) -> list[dict]:
    """Load the queue. Missing file → []. A malformed file RAISES (fail loudly:
    silently dropping queued items would recreate the lost-item outage)."""
    path = pathlib.Path(path)
    if not path.exists():
        return []
    envelope = json.loads(path.read_text(encoding="utf-8"))
    items = envelope.get("items")
    if not isinstance(items, list):
        raise ValueError(f"{path}: 'items' must be a list")
    return [dict(it) for it in items if isinstance(it, dict) and it.get("url")]


def save_pending(path: pathlib.Path, items: list[dict]) -> bool:
    """Write the queue only if its content changed. Returns True when written.

    An empty queue with no file on disk is not written (keeps no-op runs and the
    no-key path free of new files)."""
    path = pathlib.Path(path)
    text = _serialize(items)
    if path.exists():
        if path.read_text(encoding="utf-8") == text:
            return False
    elif not items:
        return False
    atomic_write_json(path, {"items": _sorted(items)})
    return True


def upsert_failure(items: list[dict], cand: dict, now: datetime, error: str | None,
                   attempted: bool) -> list[dict]:
    """Return a new list with `cand` queued.

    attempted=True  → attempts += 1 and last_error = error (new entry: attempts 1).
    attempted=False → attempts unchanged (new entry: attempts 0) — router exhausted
                      or run budget spent (G-09); last_error untouched.
    """
    key = cand.get("id") or item_id(cand["url"])
    out: list[dict] = []
    found = False
    for it in items:
        if it.get("id") == key:
            found = True
            it = dict(it)
            if attempted:
                it["attempts"] = int(it.get("attempts") or 0) + 1
                it["last_error"] = error
        out.append(it)
    if not found:
        out.append({
            "id": key,
            "url": cand["url"],
            "title": cand.get("title") or "",
            "description": cand.get("description") or "",
            "date": cand.get("date") or "",
            "outlet": cand.get("outlet") or "",
            "first_queued": now.astimezone(timezone.utc).isoformat(timespec="seconds"),
            "attempts": 1 if attempted else 0,
            "last_error": error if attempted else None,
        })
    return out


def remove(items: list[dict], key: str) -> list[dict]:
    return [it for it in items if it.get("id") != key]


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def split_expired(items: list[dict], now: datetime) -> tuple[list[dict], list[dict]]:
    """(keep, expired): expired when attempts >= PENDING_MAX_ATTEMPTS or the item has
    been queued for more than PENDING_MAX_AGE_DAYS."""
    keep: list[dict] = []
    expired: list[dict] = []
    max_age = timedelta(days=PENDING_MAX_AGE_DAYS)
    for it in items:
        queued_at = _parse_ts(it.get("first_queued"))
        too_old = queued_at is not None and (now - queued_at) > max_age
        if int(it.get("attempts") or 0) >= PENDING_MAX_ATTEMPTS or too_old:
            expired.append(it)
        else:
            if queued_at is None:
                logger.warning("pending item %s has unparseable first_queued", it.get("id"))
            keep.append(it)
    return keep, expired
