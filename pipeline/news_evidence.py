#!/usr/bin/env python3
"""
pipeline/news_evidence.py

G-05 evidence extractor for the news heartbeat (NEWS-08).

stdlib only (json, sys, datetime) — the heartbeat job runs this with system
python3 and has NO actions/setup-python / pip install step (H-02 guard),
so no third-party import is allowed here.

evidence_iso(payload) -> str | None:
  - payload["last_new_incident_at"] (a str) wins when present.
  - Else, fall back to max(incident["date"]) + 1 day at 00:00:00Z (freshness
    cannot be measured any more precisely than "the newest incident date"
    when the field is absent — e.g. old data written before 34-03 shipped).
  - Else (no field, no incidents, or all incident dates unparseable) -> None.

CLI: `python3 pipeline/news_evidence.py <file>` prints the evidence (or an
empty line) and ALWAYS exits 0 — a missing timestamp is communicated by the
empty line, not by a non-zero exit, so check-heartbeat.sh (not this script)
is the single place that turns "no evidence" into a failure.
"""
from __future__ import annotations

import datetime
import json
import sys


def evidence_iso(payload: dict) -> str | None:
    """Return the G-05 evidence timestamp (ISO Z) for a current.json payload dict."""
    last_new = payload.get("last_new_incident_at")
    if isinstance(last_new, str) and last_new.strip():
        try:
            datetime.datetime.fromisoformat(last_new.replace("Z", "+00:00"))
        except ValueError:
            pass  # unparseable -> fall through to the max(date)+1d fallback
        else:
            return last_new

    incidents = payload.get("incidents")
    if not isinstance(incidents, list):
        return None

    max_date: datetime.date | None = None
    for inc in incidents:
        if not isinstance(inc, dict):
            continue
        date_str = inc.get("date")
        if not isinstance(date_str, str):
            continue
        try:
            d = datetime.date.fromisoformat(date_str)
        except ValueError:
            continue
        if max_date is None or d > max_date:
            max_date = d

    if max_date is None:
        return None

    fallback = datetime.datetime(
        max_date.year, max_date.month, max_date.day, tzinfo=datetime.timezone.utc
    ) + datetime.timedelta(days=1)
    return fallback.isoformat().replace("+00:00", "Z")


def _load_payload(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("")
        return 0
    payload = _load_payload(argv[1])
    result = evidence_iso(payload)
    print(result or "")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
