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

from pydantic import ValidationError

from pipeline.news.schema import validate_incidents_file
from pipeline.shared.atomic_write import atomic_write_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_id(url: str) -> str:
    """Deterministic incident id: sha256(url)[:16] (D-11)."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def build_incident(
    *,
    url: str,
    cut: str,
    lat: float,
    lng: float,
    title_es: str,
    title_en: str,
    date: str,
    outlet: str,
    family: str,
    slug: str | None = None,
) -> dict:
    """Build a validated incident dict ready for merge_and_write.

    All attribution fields are required (NEWS-05).
    Returns a plain dict matching the IncidentRecord schema.
    """
    return {
        "id": make_id(url),
        "cut": cut,
        "lat": lat,
        "lng": lng,
        "title_es": title_es,
        "title_en": title_en,
        "date": date,
        "outlet": outlet,
        "url": url,
        "family": family,
        "slug": slug,
    }


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
) -> None:
    """
    Idempotent merge + 30-day rolling window + monthly archive + validated atomic write.

    Steps:
    1. Load existing incidents from current_path (or [] if absent).
    2. Merge new_incidents by id (dedup — existing wins).
    3. Compute cutoff = today - window_days days.
    4. Partition combined list: current (date >= cutoff) and aged_out (date < cutoff).
    5. For each YYYY-MM group of aged_out, merge into archive/YYYY-MM.json (dedup by id).
    6. Validate payload via validate_incidents_file — on ValidationError, log and skip write
       (last-good file preserved, D-15).
    7. atomic_write_json(current_path, payload).
    """
    ref_date = today or datetime.date.today()
    cutoff = ref_date - datetime.timedelta(days=window_days)

    # 1. Load existing
    existing = _load_incidents_list(current_path)

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
        archive_payload = {
            "generated": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
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

    # 6. Validate current payload
    payload = {
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "window_days": window_days,
        "incidents": current_incidents,
    }
    try:
        validate_incidents_file(payload)
    except ValidationError as exc:
        logger.error(
            "current.json failed validation — skipping write to preserve last-good: %s",
            exc,
        )
        return

    # 7. Atomic write
    atomic_write_json(current_path, payload)
