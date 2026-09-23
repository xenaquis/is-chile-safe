#!/usr/bin/env python3
"""
pipeline/news_health_gate.py

Post-commit health gate (NREC-07 / G-04, amended by G-09).

stdlib only — runs after "Commit data if changed" in news-pipeline.yml, so a
zero exit status here must never gate the commit itself (the commit already
happened). It reads the run summary schema-1 dict written by
pipeline/scrape_news.py (NEWS_RUN_SUMMARY_PATH) and fails loud on either a
genuinely unhealthy run OR a missing/malformed summary (G-06 fail-closed).

Predicates (evaluate() returns the list of failure reasons):
  (a) attempted > 0 and responded == 0
  (b) attempted >= 10 and api_errors / attempted >= 0.5
  (c) backup_exhausted
  (d) attempted >= 10 and accepted == 0                       (G-09, NREC-07 literal)
  (e) attempted >= 10 and parse_errors / attempted >= 0.20    (G-09)
  (f) expired > 0 — items permanently lost                    (G-09)

budget_exhausted and failovers > 0 are ::warning:: only (R-03/R-04/R-11) —
they do not fail the gate on their own.

Usage:
  python pipeline/news_health_gate.py <summary.json>

Exit codes:
  0 = healthy (or a warning-only condition)
  1 = one or more G-04/G-09 predicates failed, OR the summary file is
      missing / not valid JSON / not schema 1 (fail-closed, G-06)
"""
from __future__ import annotations

import json
import sys


EXPECTED_SCHEMA = 1


def evaluate(summary: dict) -> list[str]:
    """Return the list of G-04/G-09 failure reasons for a run summary dict."""
    reasons: list[str] = []

    attempted = summary.get("attempted", 0) or 0
    responded = summary.get("responded", 0) or 0
    accepted = summary.get("accepted", 0) or 0
    api_errors = summary.get("api_errors", 0) or 0
    parse_errors = summary.get("parse_errors", 0) or 0
    expired = summary.get("expired", 0) or 0
    backup_exhausted = bool(summary.get("backup_exhausted", False))

    # (a)
    if attempted > 0 and responded == 0:
        reasons.append(
            f"(a) attempted={attempted} but responded=0 — no provider answered"
        )

    # (b)
    if attempted >= 10 and api_errors / attempted >= 0.5:
        reasons.append(
            f"(b) api_errors/attempted = {api_errors}/{attempted} >= 0.5"
        )

    # (c)
    if backup_exhausted:
        reasons.append("(c) backup_exhausted=true — both providers unavailable")

    # (d) G-09 / NREC-07 literal
    if attempted >= 10 and accepted == 0:
        reasons.append(
            f"(d) attempted={attempted} but accepted=0 — every response was a genuine reject or worse"
        )

    # (e) G-09
    if attempted >= 10 and parse_errors / attempted >= 0.20:
        reasons.append(
            f"(e) parse_errors/attempted = {parse_errors}/{attempted} >= 0.20"
        )

    # (f) G-09
    if expired > 0:
        reasons.append(f"(f) expired={expired} — items permanently lost from the retry queue")

    return reasons


def _load_summary(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        print(f"::error::Health gate (G-04/G-09): could not read/parse summary {path!r}: {exc}")
        return None
    if not isinstance(data, dict):
        print(f"::error::Health gate (G-04/G-09): summary {path!r} is not a JSON object")
        return None
    if data.get("schema") != EXPECTED_SCHEMA:
        print(
            f"::error::Health gate (G-04/G-09): summary {path!r} has schema="
            f"{data.get('schema')!r}, expected {EXPECTED_SCHEMA} — fail-closed (G-06)"
        )
        return None
    return data


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("::error::Health gate (G-04/G-09): usage: python pipeline/news_health_gate.py <summary.json>")
        return 1

    summary = _load_summary(argv[1])
    if summary is None:
        return 1

    reasons = evaluate(summary)

    # Warning-only conditions (R-03/R-04/R-11): logged regardless of pass/fail.
    if summary.get("budget_exhausted"):
        print("::warning::Health gate: budget_exhausted=true — some items were queued without an attempt")
    failovers = summary.get("failovers", 0) or 0
    if failovers > 0:
        print(
            f"::warning::Health gate: failovers={failovers} "
            f"(reason={summary.get('failover_reason')!r}) — the run failed over to the backup provider"
        )

    if reasons:
        for reason in reasons:
            print(f"::error::Health gate (G-04/G-09): {reason}")
        return 1

    print(
        "Health gate OK: attempted={attempted} responded={responded} api_errors={api_errors} "
        "failovers={failovers}".format(
            attempted=summary.get("attempted", 0),
            responded=summary.get("responded", 0),
            api_errors=summary.get("api_errors", 0),
            failovers=failovers,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
