#!/usr/bin/env python3
"""
pipeline/experiments/fid03_audit.py

Phase 36-08 (FID-03): a 50-item hand audit of a fresh 2-week sample under the
Phase-36 classifier, out-of-sample against golden_set_v3 (ids + event-siblings
excluded).

Four independent modes:
  --select    build the candidate pool from data/incidents/rejected/*.json:
              first_seen in [as_of - window_days, as_of), deduped by id,
              minus --exclude-ids-file and minus event-siblings of
              --exclude-siblings-file (SequenceMatcher ratio >= 0.60 over
              pipeline.news.dedup.normalize_title). Prints counts by stage and
              by epoch (outage = classifier_none, live = low_confidence /
              commune_null / resolver_fail). Writes the pool to --out-rows.
  --classify  replay the pool through the PRODUCTION classify path
              (backfill_classifier_outage.run_classify), capped by a
              SpendMeter. Refuses a --cache path under data/ (R-12 pattern:
              classifier imports stay function-local, loaded after the .env
              files).
  --sample N  deterministic random.Random(seed) draw of N "would-publish"
              items (OK, commune resolvable, centroid found, not
              editorial_filter) from the replayed pool. Writes the fields
              scrape_news/run_apply would publish (title_src, guarded
              title_en, title_en_fallback — never title_es). --blind-out
              additionally writes the pass-1 reviewer file with the decoded
              publisher_url (G-43: decode_gnews_url WITH a requests.Session).
  --score     compute agreement (q1 and q3) against a declared threshold,
              vida precision, and agreement per basis, from a --verdicts file.

No writes under data/ in any mode (T-36-24).

Exit codes (shared with backfill_classifier_outage where applicable):
  0 = done
  1 = error (bad input)
  2 = usage error (argparse)
  3 = spend cap reached (classify)
  4 = router exhausted (classify) — re-invoke later, never sample after this
  5 = would-publish pool < N (sample) — report, do not sample around it

Usage:
  python pipeline/experiments/fid03_audit.py --select --window-days 14 \
      --exclude-ids-file F --exclude-siblings-file T --out-rows R
  python pipeline/experiments/fid03_audit.py --classify --rows R --cache C \
      --spend-cap 0.90 [--spend-ledger L]
  python pipeline/experiments/fid03_audit.py --sample 50 --seed 3608 \
      --cache C --rows R --out S [--blind-out B]
  python pipeline/experiments/fid03_audit.py --score --verdicts V
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import math
import os
import pathlib
import random
import sys
import time
from collections import Counter
from typing import Callable, Iterable
from urllib.parse import urlparse

# NOTE (R-12): classifier imports stay function-local (its import-time compat
# client reads os.environ, so it must be imported only AFTER the .env files
# have been loaded). All other pipeline imports below are function-local too,
# to keep --select/--score light and importable without a full data tree.

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pipeline import backfill_classifier_outage as B  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FID03_MIN_AGREE = 43       # ceil(0.85 * 50), owner default
VIDA_MIN_RATE = 0.85
SAMPLE_N = 50
SEED = 3608
SIBLING_RATIO = 0.60

OUTAGE_STAGE = "classifier_none"
LIVE_STAGES = ("low_confidence", "commune_null", "resolver_fail")

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_CAP = B.EXIT_CAP          # 3
EXIT_EXHAUSTED = B.EXIT_EXHAUSTED  # 4
EXIT_POOL_TOO_SMALL = 5


def _iso_z(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _read_lines_file(path: pathlib.Path | None) -> list[str]:
    if path is None:
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


# ---------------------------------------------------------------------------
# --select
# ---------------------------------------------------------------------------

def _rejected_files(data_dir: pathlib.Path) -> list[pathlib.Path]:
    rejected_dir = data_dir / "rejected"
    if not rejected_dir.is_dir():
        return []
    return sorted(rejected_dir.glob("*.json"))


def _load_envelope(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise ValueError(f"{path}: not a rejected envelope")
    return data


def _epoch_of(row: dict) -> str | None:
    stage = row.get("rejection_stage")
    if stage == OUTAGE_STAGE:
        return "outage"
    if stage in LIVE_STAGES:
        return "live"
    return None


def select_pool(
    data_dir: pathlib.Path,
    as_of: dt.datetime,
    window_days: int,
    exclude_ids: Iterable[str] = frozenset(),
    exclude_siblings: Iterable[str] = (),
) -> tuple[list[dict], Counter, dict, list[tuple[str, str, float]]]:
    """FID-03 population (G-32/G-42/R-09): every rejected/*.json row whose
    parsed first_seen falls in [as_of - window_days, as_of), deduped by id
    (first occurrence, files scanned in sorted order), minus exclude_ids, then
    minus event-siblings of exclude_siblings (SequenceMatcher ratio >= 0.60
    over dedup.normalize_title(title), against any sibling headline).

    Returns (rows, stage_counts, epoch_counts, sibling_exclusions) where
    sibling_exclusions is a list of (id, matched_headline, ratio).
    """
    exclude_ids = set(exclude_ids)
    start = as_of - dt.timedelta(days=window_days)
    rows: list[dict] = []
    seen: set[str] = set()
    for path in _rejected_files(data_dir):
        envelope = _load_envelope(path)
        for row in envelope["items"]:
            if not isinstance(row, dict):
                continue
            rid = row.get("id")
            if not rid or rid in seen:
                continue
            fs = B.parse_dt(row.get("first_seen"))
            if fs is None or not (start <= fs < as_of):
                continue
            if rid in exclude_ids:
                continue
            seen.add(rid)
            rows.append(row)

    sibling_exclusions: list[tuple[str, str, float]] = []
    siblings = [s for s in exclude_siblings if s]
    if siblings:
        from pipeline.news.dedup import normalize_title

        norm_siblings = [(h, normalize_title(h)) for h in siblings]
        kept: list[dict] = []
        for row in rows:
            nt = normalize_title(row.get("title") or "")
            best_ratio = 0.0
            best_match = None
            for headline, nh in norm_siblings:
                ratio = difflib.SequenceMatcher(None, nt, nh).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = headline
            if best_match is not None and best_ratio >= SIBLING_RATIO:
                sibling_exclusions.append((row.get("id"), best_match, round(best_ratio, 4)))
            else:
                kept.append(row)
        rows = kept

    stage_counts = Counter(r.get("rejection_stage") for r in rows)
    epoch_counts = {
        "outage": sum(1 for r in rows if _epoch_of(r) == "outage"),
        "live": sum(1 for r in rows if _epoch_of(r) == "live"),
    }
    return rows, stage_counts, epoch_counts, sibling_exclusions


def cmd_select(args, out=None) -> int:
    out = out or sys.stdout
    as_of = B.parse_dt(args.as_of) if args.as_of else dt.datetime.now(dt.timezone.utc)
    if as_of is None:
        print(f"ERROR: invalid --as-of {args.as_of!r}", file=sys.stderr)
        return EXIT_ERROR
    exclude_ids = B._read_ids_file(args.exclude_ids_file) if args.exclude_ids_file else set()
    exclude_siblings = _read_lines_file(args.exclude_siblings_file)

    rows, stage_counts, epoch_counts, sibling_exclusions = select_pool(
        args.data_dir, as_of, args.window_days, exclude_ids, exclude_siblings,
    )

    print(f"as_of={_iso_z(as_of)}", file=out)
    print(f"window_days={args.window_days}", file=out)
    print(f"pool={len(rows)}", file=out)
    print(f"by_stage={json.dumps(dict(sorted((k or 'null', v) for k, v in stage_counts.items())))}",
          file=out)
    print(f"pool_by_epoch: outage={epoch_counts['outage']} live={epoch_counts['live']}", file=out)
    for rid, matched, ratio in sibling_exclusions:
        print(f"sibling_excluded id={rid} ratio={ratio} matched={matched!r}", file=out)
    print(f"sibling_exclusions={len(sibling_exclusions)}", file=out)

    if args.out_rows is not None:
        B._assert_outside(args.out_rows, args.data_dir, "--out-rows")
        args.out_rows.parent.mkdir(parents=True, exist_ok=True)
        args.out_rows.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8",
        )
    return EXIT_OK


# ---------------------------------------------------------------------------
# --classify
# ---------------------------------------------------------------------------

def _load_env_files(env_files: Iterable[pathlib.Path]) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for f in env_files:
        if f.exists():
            load_dotenv(dotenv_path=f, override=False)


def cmd_classify(
    args,
    *,
    env_files: Iterable[pathlib.Path] | None = None,
    router_hook: Callable | None = None,
) -> int:
    B._assert_outside(args.cache, args.data_dir, "--cache")
    if args.spend_ledger is not None:
        B._assert_outside(args.spend_ledger, args.data_dir, "--spend-ledger")
    if args.spend_cap is None:
        print("ERROR: --classify needs --spend-cap (G-45)", file=sys.stderr)
        return EXIT_ERROR

    rows = json.loads(args.rows.read_text(encoding="utf-8"))
    cache = B.load_cache(args.cache)
    pending = [r for r in rows if not B._is_final(cache.get(r["id"]))]
    if args.limit is not None:
        pending = pending[: args.limit]
    if not pending:
        print("classify: nothing to do (every row has a final cached outcome)")
        return EXIT_OK

    # R-12: keys from pipeline/.env then the repo-root .env (override=False),
    # and only THEN import the classifier — its import-time client reads
    # os.environ.
    _load_env_files(
        env_files if env_files is not None
        else [_REPO_ROOT / "pipeline" / ".env", _REPO_ROOT / ".env"]
    )
    from pipeline.news.classifier import build_router_from_env

    router = build_router_from_env()
    if router_hook is not None:
        router_hook(router)
    if not router.any_key_present:
        print(f"ERROR: no API key ({' / '.join(router.key_env_names)})", file=sys.stderr)
        return EXIT_ERROR
    router.preflight()

    ledger = args.spend_ledger or args.cache.with_name(args.cache.stem + ".spend.json")
    B._assert_outside(ledger, args.data_dir, "--spend-ledger")
    meter = B.SpendMeter(
        args.spend_cap, ledger,
        api_key=os.environ.get("OPENROUTER_API_KEY", "").strip() or None,
    )
    meter.start()
    code = B.run_classify(rows, args.cache, router, meter, limit=args.limit)
    final_cache = B.load_cache(args.cache)
    print(f"exit={code} spend_usd={meter.total:.6f} cap={meter.cap} "
          f"cached_final={sum(1 for r in rows if B._is_final(final_cache.get(r['id'])))} "
          f"uncached={sum(1 for r in rows if r['id'] not in final_cache)}")
    return code


# ---------------------------------------------------------------------------
# --sample
# ---------------------------------------------------------------------------

def _would_publish(row: dict, rec: dict | None) -> dict | None:
    """Fields scrape_news/run_apply would publish, or None if this row is not
    a would-publish item (OK, commune resolvable, centroid found, not
    editorial_filter — premortem R-16: title_src / guarded title_en, never
    the classifier's title_es)."""
    if not rec or rec.get("outcome") != "ok" or not rec.get("output"):
        return None

    from pydantic import ValidationError

    from pipeline.news import centroids, resolver
    from pipeline.news.feeds import source_headline
    from pipeline.news.fidelity import forbidden_term, guard_title_en
    from pipeline.news.schema import ClassifierOutput

    try:
        out = ClassifierOutput.model_validate(rec["output"])
    except ValidationError:
        return None
    if not out.commune_name:
        return None
    resolved = resolver.resolve_cut(out.commune_name, out.region_hint)
    if resolved is None:
        return None
    cut, _slug = resolved
    if centroids.get_centroid(cut) is None:
        return None

    outlet = row.get("outlet") or ""
    title_src = source_headline(row.get("title") or "", outlet)
    title_en, fell_back = guard_title_en(title_src, out.title_en, outlet)
    if forbidden_term(title_src) or forbidden_term(title_en):
        return None

    return {
        "id": row["id"],
        "url": row.get("url"),
        "outlet": outlet,
        "title": row.get("title"),
        "description": row.get("description"),
        "predicted_family": out.family,
        "commune_name": out.commune_name,
        "cut": cut,
        "title_src": title_src,
        "title_en": title_en,
        "title_en_fallback": fell_back,
    }


def _is_http_url(candidate: str | None) -> bool:
    if not candidate:
        return False
    try:
        return urlparse(candidate).scheme in {"http", "https"}
    except Exception:
        return False


def _build_blind_row(row: dict, publisher_url: str | None) -> dict:
    return {
        "id": row["id"],
        "title": row.get("title"),
        "description": row.get("description"),
        "url": row.get("url"),
        "publisher_url": publisher_url,
        "outlet": row.get("outlet"),
    }


def cmd_sample(
    args,
    out=None,
    *,
    decoder: Callable | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    out = out or sys.stdout
    rows = json.loads(args.rows.read_text(encoding="utf-8"))
    cache = B.load_cache(args.cache)

    pool: list[tuple[dict, dict]] = []
    for row in rows:
        info = _would_publish(row, cache.get(row["id"]))
        if info is not None:
            pool.append((row, info))

    print(f"would_publish_pool={len(pool)}", file=out)
    if len(pool) < args.sample:
        print(f"pool too small: {len(pool)} < {args.sample} — exit 5, do not sample around it",
              file=out)
        return EXIT_POOL_TOO_SMALL

    pool_sorted = sorted(pool, key=lambda p: p[0]["id"])
    rng = random.Random(args.seed)
    picked = rng.sample(pool_sorted, args.sample)

    B._assert_outside(args.out, args.data_dir, "--out")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps([info for _, info in picked], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"sampled={len(picked)} seed={args.seed} out={args.out}", file=out)

    if args.blind_out is not None:
        B._assert_outside(args.blind_out, args.data_dir, "--blind-out")
        if decoder is None:
            import requests

            from pipeline.news.fulltext import USER_AGENT
            from pipeline.news.gnews_decoder import decode_gnews_url

            session = requests.Session()
            session.headers.update({"User-Agent": USER_AGENT})

            def decoder(url):  # noqa: E306 — deliberate shadow, network-backed default
                return decode_gnews_url(url, session=session, timeout=10)

        blind_rows = []
        n_google = 0
        n_decoded = 0
        first_decode = True
        for row, _info in picked:
            url = row.get("url") or ""
            host = (urlparse(url).hostname or "").lower()
            if host == "news.google.com":
                n_google += 1
                if not first_decode:
                    sleep(1.5)
                first_decode = False
                decoded = decoder(url)
                decoded_host = (urlparse(decoded).hostname or "").lower() if decoded else ""
                publisher_url = decoded if (_is_http_url(decoded) and decoded_host != "news.google.com") else None
                if publisher_url is not None:
                    n_decoded += 1
            else:
                publisher_url = url
            blind_rows.append(_build_blind_row(row, publisher_url))

        args.blind_out.parent.mkdir(parents=True, exist_ok=True)
        args.blind_out.write_text(
            json.dumps(blind_rows, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        print(f"publisher_url_decoded: {n_decoded}/{n_google}", file=out)

    return EXIT_OK


# ---------------------------------------------------------------------------
# --score
# ---------------------------------------------------------------------------

def score_verdicts(verdicts: list[dict]) -> dict:
    n = len(verdicts)
    agreement = 0
    vida_n = 0
    vida_ok = 0
    by_basis: dict[str, dict[str, int]] = {}
    for v in verdicts:
        basis = v.get("basis") or "source"
        q1 = bool(v.get("q1"))
        pass1_family = v.get("family")
        predicted = v.get("predicted_family")
        q3 = pass1_family == predicted
        agree = q1 and q3
        if agree:
            agreement += 1
        bucket = by_basis.setdefault(basis, {"agree": 0, "n": 0})
        bucket["n"] += 1
        if agree:
            bucket["agree"] += 1
        if predicted == "vida":
            vida_n += 1
            if pass1_family == "vida":
                vida_ok += 1
    vida_pass = vida_ok >= math.ceil(VIDA_MIN_RATE * vida_n) if vida_n else True
    passed = agreement >= FID03_MIN_AGREE and vida_pass
    return {
        "n": n,
        "agreement": agreement,
        "agreement_min": FID03_MIN_AGREE,
        "vida_n": vida_n,
        "vida_ok": vida_ok,
        "vida_pass": vida_pass,
        "pass": passed,
        "agreement_by_basis": by_basis,
    }


def cmd_score(args, out=None) -> int:
    out = out or sys.stdout
    verdicts = json.loads(args.verdicts.read_text(encoding="utf-8"))
    result = score_verdicts(verdicts)
    print(json.dumps(result, indent=2, ensure_ascii=False), file=out)
    print(f"agreement: {result['agreement']}/{result['n']}", file=out)
    basis_line = " ".join(
        f"{b}={v['agree']}/{v['n']}" for b, v in sorted(result["agreement_by_basis"].items())
    )
    print(f"agreement_by_basis: {basis_line}", file=out)
    print(f"vida_precision: {result['vida_ok']}/{result['vida_n']}", file=out)
    print(f"**Decision**: {'PASS' if result['pass'] else 'FAILED'}", file=out)
    return EXIT_OK


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FID-03: 50-item audit of a fresh 2-week sample")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--select", action="store_true")
    mode.add_argument("--classify", action="store_true")
    mode.add_argument("--sample", type=int, metavar="N")
    mode.add_argument("--score", action="store_true")

    p.add_argument("--data-dir", type=pathlib.Path, default=B.DEFAULT_DATA_DIR)
    p.add_argument("--as-of", default=None, help="ISO datetime, default now (UTC)")
    p.add_argument("--window-days", type=int, default=14)
    p.add_argument("--exclude-ids-file", type=pathlib.Path, default=None)
    p.add_argument("--exclude-siblings-file", type=pathlib.Path, default=None)
    p.add_argument("--out-rows", type=pathlib.Path, default=None)

    p.add_argument("--rows", type=pathlib.Path, default=None)
    p.add_argument("--cache", type=pathlib.Path, default=None)
    p.add_argument("--spend-cap", type=float, default=None)
    p.add_argument("--spend-ledger", type=pathlib.Path, default=None)
    p.add_argument("--limit", type=int, default=None)

    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--out", type=pathlib.Path, default=None)
    p.add_argument("--blind-out", type=pathlib.Path, default=None)

    p.add_argument("--verdicts", type=pathlib.Path, default=None)
    return p


def main(argv: list[str] | None = None, **kwargs) -> int:
    args = _build_parser().parse_args(argv)

    if args.select:
        return cmd_select(args)
    if args.classify:
        if args.rows is None or args.cache is None:
            print("ERROR: --classify needs --rows and --cache", file=sys.stderr)
            return EXIT_ERROR
        return cmd_classify(
            args,
            env_files=kwargs.get("env_files"),
            router_hook=kwargs.get("router_hook"),
        )
    if args.sample is not None:
        if args.cache is None or args.rows is None or args.out is None:
            print("ERROR: --sample needs --cache, --rows and --out", file=sys.stderr)
            return EXIT_ERROR
        return cmd_sample(args, decoder=kwargs.get("decoder"), sleep=kwargs.get("sleep", time.sleep))
    if args.score:
        if args.verdicts is None:
            print("ERROR: --score needs --verdicts", file=sys.stderr)
            return EXIT_ERROR
        return cmd_score(args)
    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
