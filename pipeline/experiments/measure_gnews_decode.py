#!/usr/bin/env python3
"""
pipeline/experiments/measure_gnews_decode.py

FID-04 36-07 Task 1 (V-10 fix step 3): measure the Google-News decode success
rate on a seeded sample of 50 news.google.com URLs from
data/incidents/current.json, BEFORE the ingest wiring ships.

Read-only on data/. No LLM calls. Network: only news.google.com (the article
GET and the hardcoded batchexecute POST inside gnews_decoder, T-gf7-04); the
publisher URL is never fetched. Courtesy: fulltext.REQUEST_DELAY between URLs,
fulltext.USER_AGENT, 10 s timeout.

Each outcome is one of:
  old_format  — decoded offline from the base64 token (_try_old_format)
  new_format  — decoded via decode_gnews_url(session=...) (GET + batchexecute)
  failed      — no usable publisher URL (None, news.google.com host, or a
                non-http(s) scheme per store.is_safe_url)

Usage:
  python pipeline/experiments/measure_gnews_decode.py [--n 50] [--seed 3607] [--out rows.json]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys
import time
from urllib.parse import urlparse

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import requests  # noqa: E402

from pipeline.news import gnews_decoder  # noqa: E402
from pipeline.news.fulltext import REQUEST_DELAY, USER_AGENT  # noqa: E402
from pipeline.news.store import is_safe_url  # noqa: E402

SEED = 3607
N = 50
TIMEOUT = 10.0
GNEWS_HOST = "news.google.com"


def _host(url: str | None) -> str:
    try:
        return (urlparse(url or "").hostname or "").lower()
    except Exception:
        return ""


def _usable(decoded: str | None) -> bool:
    return bool(decoded) and is_safe_url(decoded) and _host(decoded) not in ("", GNEWS_HOST)


def sample_urls(current_path: pathlib.Path, n: int, seed: int) -> tuple[list[str], int]:
    envelope = json.loads(current_path.read_text(encoding="utf-8"))
    items = envelope.get("incidents", []) if isinstance(envelope, dict) else envelope
    urls = sorted({it["url"] for it in items if _host(it.get("url")) == GNEWS_HOST})
    rng = random.Random(seed)
    return rng.sample(urls, min(n, len(urls))), len(urls)


def measure(urls: list[str], sleep=time.sleep) -> tuple[list[dict], float]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    rows: list[dict] = []
    t0 = time.monotonic()
    for i, url in enumerate(urls):
        if i > 0:
            sleep(REQUEST_DELAY)
        started = time.monotonic()
        decoded = gnews_decoder._try_old_format(url)
        path = "old_format"
        if not _usable(decoded):
            decoded = gnews_decoder.decode_gnews_url(url, session=session, timeout=TIMEOUT)
            path = "new_format"
        ok = _usable(decoded)
        rows.append({
            "gn_url": url,
            "outcome": path if ok else "failed",
            "decoded_host": _host(decoded) if decoded else None,
            "host_differs": bool(decoded) and _host(decoded) != GNEWS_HOST,
            "is_safe_url": bool(decoded) and is_safe_url(decoded),
            "seconds": round(time.monotonic() - started, 2),
        })
    return rows, time.monotonic() - t0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--current", default=str(_REPO_ROOT / "data" / "incidents" / "current.json"))
    ap.add_argument("--out", default=None, help="optional per-row JSON output path")
    args = ap.parse_args()

    urls, population = sample_urls(pathlib.Path(args.current), args.n, args.seed)
    rows, seconds = measure(urls)
    counts = {k: sum(1 for r in rows if r["outcome"] == k) for k in ("old_format", "new_format", "failed")}
    n = len(rows)
    summary = {
        "n": n,
        "population_google": population,
        "seed": args.seed,
        **counts,
        "success_rate": round((counts["old_format"] + counts["new_format"]) / n, 4) if n else 0.0,
        "seconds": round(seconds, 1),
    }
    if args.out:
        pathlib.Path(args.out).write_text(
            json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
