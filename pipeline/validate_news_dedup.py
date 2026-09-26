"""
pipeline/validate_news_dedup.py

FID-05 (36-05): 0 drops over current.json. Applies the single dedup rule source
(pipeline.news.dedup.prune_near_duplicates — canonical url|via_url identity, then
(cut, date) bucket SequenceMatcher >= 0.82 on normalized title_es, keep-first)
to data["incidents"] and reports every (DROP, KEEP) pair.

Usage:
    python pipeline/validate_news_dedup.py FILE [--list] [--only-new-since IDS_FILE]

    --list                 print every pair (prints "(none)" on PASS)
    --only-new-since FILE  forward-only (premortem R-04): count only pairs where the
                           DROP id or the KEEP id is absent from FILE (one id per
                           line; blank lines and '#' comments ignored)

Exit codes: 0 = 0 drops, 1 = drops > 0, 2 = missing/malformed input.

Imports stdlib + pipeline.news.dedup only (runs under a bare python3).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pipeline.news import dedup  # noqa: E402


def _error(msg: str) -> int:
    print(f"::error::news-dedup: {msg}")
    return 2


def _load_ids(path: pathlib.Path) -> set[str]:
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        ids.add(s)
    return ids


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="FID-05: 0 near-duplicate drops over current.json")
    ap.add_argument("file")
    ap.add_argument("--list", action="store_true", help="print every pair, even on PASS")
    ap.add_argument("--only-new-since", metavar="IDS_FILE", default=None,
                    help="forward-only: ignore pairs whose ids are both in IDS_FILE")
    args = ap.parse_args(argv)

    path = pathlib.Path(args.file)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        incidents = data["incidents"]
        if not isinstance(incidents, list):
            raise TypeError("incidents is not a list")
    except FileNotFoundError:
        return _error(f"file not found: {path}")
    except Exception as exc:  # malformed JSON / shape
        return _error(f"malformed payload {path}: {exc}")

    baseline: set[str] | None = None
    if args.only_new_since is not None:
        ids_path = pathlib.Path(args.only_new_since)
        try:
            baseline = _load_ids(ids_path)
        except FileNotFoundError:
            return _error(f"ids file not found: {ids_path}")
        except Exception as exc:
            return _error(f"unreadable ids file {ids_path}: {exc}")

    _kept, dropped = dedup.prune_near_duplicates(incidents)
    if baseline is not None:
        dropped = [d for d in dropped if d[0].get("id") not in baseline or d[1] not in baseline]

    mode = "" if baseline is None else f" (forward-only since {len(baseline)} ids)"
    n = len(dropped)
    if n or args.list:
        for item, kept_id, reason in dropped:
            print(f"DROP {item.get('id')} ~ KEEP {kept_id} ({reason})")
        if not dropped:
            print("(none)")
    if n == 0:
        print(f"news-dedup: PASS — 0 drops over {len(incidents)} incidents{mode} drops=0")
        return 0
    print(f"news-dedup: FAIL — drops={n} over {len(incidents)} incidents{mode}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
