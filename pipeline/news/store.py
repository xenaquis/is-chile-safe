"""
pipeline/news/store.py

Idempotent merge, 30-day rolling window, and monthly archive for RSS incidents
(NEWS-04, NEWS-05, D-15).

Public API:
    make_id(url) -> str            — deterministic sha256(url)[:16]
    merge_and_write(...)           — load, dedup-by-id, partition, validate, atomic write
"""
from __future__ import annotations

import datetime
import hashlib
import json
import logging
import pathlib
from collections import defaultdict
from urllib.parse import urlparse

from pydantic import ValidationError

from pipeline.news.schema import validate_incidents_file
from pipeline.shared.atomic_write import atomic_write_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def is_safe_url(url: str) -> bool:
    """Return True only when url has an http or https scheme (TD-05, T-19-04).

    Rejects javascript:, data:, ftp:, and unparseable URLs.
    """
    try:
        scheme = urlparse(url).scheme
        return scheme in ("http", "https")
    except Exception:
        return False


def make_id(url: str) -> str:
    """Deterministic incident id: sha256(url)[:16] (D-11)."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def build_incident(
    *,
    url: str,
    cut: str,
    lat: float,
    lng: float,
    title_en: str,
    date: str,
    outlet: str,
    family: str,
    slug: str | None = None,
    title_src: str | None = None,
    title_es: str | None = None,
    via_url: str | None = None,
) -> dict | None:
    """Build a validated incident dict ready for merge_and_write.

    All attribution fields are required (NEWS-05).
    Returns a plain dict matching the IncidentRecord schema,
    or None if the url (or via_url, when given) scheme is not http/https
    (TD-05, T-19-04, FID-04).

    Headline (FID-01, G-28):
    - title_src given: the outlet's verbatim headline; title_es := title_src and
      the dict gains "title_src" (and "via_url" when not None) after "slug".
      title_src wins if title_es is also passed.
    - only title_es given (legacy callers until 36-04): exactly the pre-36 dict —
      same keys, same order, no title_src/via_url (FRESH-04 no-op guard compares
      dicts by equality).
    - neither: ValueError.
    """
    if title_src is None and title_es is None:
        raise ValueError("build_incident needs title_src (FID-01)")
    if not is_safe_url(url):
        logger.warning("build_incident: rejected non-http(s) url %r", url)
        return None
    if via_url is not None and not is_safe_url(via_url):
        logger.warning("build_incident: rejected non-http(s) via_url %r", via_url)
        return None
    incident = {
        "id": make_id(url),
        "cut": cut,
        "lat": lat,
        "lng": lng,
        "title_es": title_src if title_src is not None else title_es,
        "title_en": title_en,
        "date": date,
        "outlet": outlet,
        "url": url,
        "family": family,
        "slug": slug,
    }
    if title_src is not None:
        incident["title_src"] = title_src
    if via_url is not None:
        incident["via_url"] = via_url
    return incident


def _load_incidents_list(path: pathlib.Path) -> list[dict]:
    """Load incidents list from a current.json or archive/YYYY-MM.json, or return []."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data.get("incidents", [])
        return []
    except Exception as exc:
        logger.warning("Could not read %s: %s — treating as empty", path, exc)
        return []


def _load_payload(path: pathlib.Path) -> dict:
    """Load the raw JSON dict from current_path (G-05), or {} if absent/unreadable.

    Kept separate from _load_incidents_list so that helper's return type
    (list[dict]) stays unchanged; this one preserves top-level keys like
    last_new_incident_at that _load_incidents_list discards.
    """
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.warning("Could not read %s: %s — treating as empty", path, exc)
        return {}


def _merge_by_id(existing: list[dict], new_items: list[dict]) -> list[dict]:
    """Merge new_items into existing, deduplicating by id (existing wins on conflict)."""
    seen: set[str] = {inc["id"] for inc in existing}
    merged = list(existing)
    for inc in new_items:
        if inc["id"] not in seen:
            seen.add(inc["id"])
            merged.append(inc)
    return merged


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def merge_and_write(
    new_incidents: list[dict],
    current_path: pathlib.Path,
    archive_dir: pathlib.Path,
    window_days: int = 30,
    today: datetime.date | None = None,
    now: datetime.datetime | None = None,
    bump_last_new: bool = True,
) -> int:
    """
    Idempotent merge + 30-day rolling window + monthly archive + validated atomic write.

    Steps:
    1. Load existing incidents from current_path (or [] if absent).
    2. Merge new_incidents by id (dedup — existing wins).
    3. Compute cutoff = today - window_days days.
    4. Partition combined list: current (date >= cutoff) and aged_out (date < cutoff).
    5. For each YYYY-MM group of aged_out, merge into archive/YYYY-MM.json (dedup by id).
       FRESH-04: a month file that already exists and gains no new id is NOT rewritten.
    6. Validate payload via validate_incidents_file — on ValidationError, log and skip write
       (last-good file preserved, D-15).
    7. FRESH-04 no-op guard: if the previous file had only known keys and its incidents,
       window_days and last_new_incident_at all equal the new payload's, skip the write
       (current.json stays byte-identical; `generated` is not bumped).
    8. Otherwise atomic_write_json(current_path, payload).

    FRESH-04 (35-02): `generated` means "the time current.json's content last changed",
    NOT "the time the pipeline last ran". The G-05 liveness signal remains
    `last_new_incident_at`. Archive month files use the same `now` clock (`ref_now`).

    G-05 (NEWS-08 freshness instrument): `now` is used for both `generated` and, when
    applicable, `last_new_incident_at`. When the count of ids landing in the current
    window that were not previously present (`existing`) is > 0 AND `bump_last_new`
    is True, `last_new_incident_at` is set to `now` (ISO Z). Otherwise the previous
    value is carried forward verbatim (or omitted if it was never set) — this holds
    even when `new_incidents` added ids that all aged straight into the archive.
    `bump_last_new=False` (G-07(a), R-02) is for the NREC-09 backfill: it must NEVER
    make a backfill look like live freshness evidence.

    Returns the count of ids landing in `current_incidents` that were not present in
    `existing` before the merge (callers may ignore it; pre-34-03 callers do).
    """
    ref_date = today or datetime.date.today()
    cutoff = ref_date - datetime.timedelta(days=window_days)
    ref_now = now or datetime.datetime.now(datetime.timezone.utc)

    # 1. Load existing
    existing = _load_incidents_list(current_path)
    existing_ids = {inc["id"] for inc in existing}
    previous_payload = _load_payload(current_path)
    previous_last_new = previous_payload.get("last_new_incident_at")

    # Filter out None results and non-http(s) incidents before merge (TD-05)
    new_incidents = [i for i in new_incidents if i is not None and is_safe_url(i.get("url", ""))]

    # 2. Merge by id
    combined = _merge_by_id(existing, new_incidents)

    # 3 & 4. Partition
    current_incidents: list[dict] = []
    aged_out: list[dict] = []
    for inc in combined:
        try:
            inc_date = datetime.date.fromisoformat(inc.get("date", ""))
        except ValueError:
            # Malformed date: keep in current to avoid silent data loss
            current_incidents.append(inc)
            continue
        if inc_date >= cutoff:
            current_incidents.append(inc)
        else:
            aged_out.append(inc)

    # 5. Archive aged-out incidents by YYYY-MM
    by_month: dict[str, list[dict]] = defaultdict(list)
    for inc in aged_out:
        month_key = inc["date"][:7]  # YYYY-MM
        by_month[month_key].append(inc)

    archive_dir.mkdir(parents=True, exist_ok=True)
    for month_key, aged_incidents in by_month.items():
        archive_path = archive_dir / f"{month_key}.json"
        existing_archive = _load_incidents_list(archive_path)
        merged_archive = _merge_by_id(existing_archive, aged_incidents)
        # FRESH-04: existing wins in _merge_by_id, so equal length == no new id.
        if archive_path.exists() and len(merged_archive) == len(existing_archive):
            continue
        archive_payload = {
            "generated": ref_now.isoformat().replace("+00:00", "Z"),
            "window_days": window_days,
            "incidents": merged_archive,
        }
        # Validate archive payload before writing
        try:
            validate_incidents_file(archive_payload)
        except ValidationError as exc:
            logger.error(
                "Archive %s failed validation — skipping write to preserve last-good: %s",
                archive_path,
                exc,
            )
            continue
        atomic_write_json(archive_path, archive_payload)

    # G-05: count of ids in the current window that were not present before this merge.
    new_in_window_count = sum(1 for inc in current_incidents if inc["id"] not in existing_ids)

    # 6. Validate current payload
    payload = {
        "generated": ref_now.isoformat().replace("+00:00", "Z"),
        "window_days": window_days,
        "incidents": current_incidents,
    }
    if new_in_window_count > 0 and bump_last_new:
        payload["last_new_incident_at"] = ref_now.isoformat().replace("+00:00", "Z")
    elif isinstance(previous_last_new, str):
        payload["last_new_incident_at"] = previous_last_new
    # else: omit the key (never set before, and not bumped this run)

    try:
        validate_incidents_file(payload)
    except ValidationError as exc:
        logger.error(
            "current.json failed validation — skipping write to preserve last-good: %s",
            exc,
        )
        return new_in_window_count

    # 7. FRESH-04 no-op guard: nothing added, nothing aged, same window, same G-05 field.
    if (
        previous_payload
        and set(previous_payload) <= {"generated", "window_days", "incidents", "last_new_incident_at"}
        and previous_payload.get("incidents") == current_incidents
        and previous_payload.get("window_days") == window_days
        and previous_payload.get("last_new_incident_at") == payload.get("last_new_incident_at")
    ):
        logger.info("current.json unchanged (no new or aged ids) — write skipped (FRESH-04)")
        return new_in_window_count

    # 8. Atomic write
    atomic_write_json(current_path, payload)
    return new_in_window_count
