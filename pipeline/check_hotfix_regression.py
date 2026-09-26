"""
pipeline/check_hotfix_regression.py

FID-07 (36-09): a committed, repeatable regression check that later plans and the
close gate re-run to prove the owner's hotfixes are not resurrected or displaced.

Covers two hotfixes:
  - quick-260922-t59 (commit 45c2650): dropped 8 defamation-risk ids (Fierro
    kinship cluster + prison suicides) and retitled 1 id (514872e1d06db7f2).
  - G-27 (commit f3a84af): dropped 1 defamation-risk id (63fb0c3ef0adca19).

The 9 dropped ids and the 2 retitled strings are hardcoded from the source
SUMMARYs:
  - .planning/quick/260922-t59-hotfix-live-erroneous-news-cards/260922-t59-SUMMARY.md
    (ids, "Retitled" section)
  - G-27 (`git log -S 63fb0c3ef0adca19`, commit f3a84af)

The 9 dropped URLs were extracted ONCE at execution time (2026-09-25) with:

    python -c "
    import json, subprocess
    def load(rev):
        out = subprocess.run(['git', 'show', rev + ':data/incidents/current.json'],
                              capture_output=True, text=True, encoding='utf-8').stdout
        return json.loads(out)
    ids8 = ['c3db293fd1316ad1', 'd468d43eeda0316d', 'f9031873f12b9479',
            '8f18cd275b4a6692', '836e500e4e4b1f30', '60fa7e16887af782',
            'efa0fae52180e3e2', 'c53a579a6c972705']
    data1 = load('45c2650^')
    by_id = {i['id']: i for i in data1['incidents']}
    for i in ids8:
        print(i, by_id.get(i, {}).get('url'))
    data2 = load('f3a84af^')
    by_id2 = {i['id']: i for i in data2['incidents']}
    print('63fb0c3ef0adca19', by_id2.get('63fb0c3ef0adca19', {}).get('url'))
    "

Usage:
    python pipeline/check_hotfix_regression.py --data DATA_DIR
    python pipeline/check_hotfix_regression.py --html FILE [FILE ...] [--current CURRENT_JSON]

Exit codes: 0 = PASS, 1 = a hotfixed id/url resurfaced or the retitled card
regressed/was lost, 2 = missing/malformed input.

Stdlib only (imports json, pathlib, argparse, html, sys).
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import sys

# The 8 t59 ids (Fierro kinship cluster + prison suicides).
T59_DROPPED_IDS: tuple[str, ...] = (
    "c3db293fd1316ad1",
    "d468d43eeda0316d",
    "f9031873f12b9479",
    "8f18cd275b4a6692",
    "836e500e4e4b1f30",
    "60fa7e16887af782",
    "efa0fae52180e3e2",
    "c53a579a6c972705",
)

# G-27's dropped id (commit f3a84af).
G27_DROPPED_ID = "63fb0c3ef0adca19"

# All 9 dropped ids.
DROPPED_IDS: tuple[str, ...] = T59_DROPPED_IDS + (G27_DROPPED_ID,)

# The retitled id and its exact strings (t59 SUMMARY, "Retitled").
RETITLED_ID = "514872e1d06db7f2"
RETITLED_TITLE_ES = "Detienen a prófugo por violento robo a trabajadores forestales en Carahue"
RETITLED_TITLE_EN = "Fugitive arrested over violent robbery of forestry workers in Carahue"

# The 9 dropped URLs, extracted from `git show 45c2650^:data/incidents/current.json`
# (the 8 t59 ids) and `git show f3a84af^:data/incidents/current.json` (G-27's id).
# See the module docstring for the exact extraction command.
DROPPED_URLS: tuple[str, ...] = (
    "https://news.google.com/rss/articles/CBMi3wFBVV95cUxNalVXaTY0TDVGMjhzaFdvU2pvdXZja3Byd2hzVnhtRExxemFwU1Y4UERSeW9aamJyaGFhMFpVdHQxZUtvN1NzMlBwbGJ3WGk4a2JzNU45b01ReXJrLVMzTGlCZGRSM1p2NUhCbzZKWnFiR25vOEtKU1JrUm9tdENlSmk2eXVDQWdLQl9zWXJsT0ZyZmFiUnRFeU1nODhhdmx3U1d5MGhfelBad3BSbm9jS25DOHJ6bUZUcXIxc1ZyYkNyZ1FEX3lIQ2hpeU9vWmZlZkM5dGtESkdlNThEX1Q4?oc=5",
    "https://news.google.com/rss/articles/CBMijAJBVV95cUxPb1MtU25Td2h6TExOSDlKclFnOG1tVFpvNUVGZ2xOQ0NZclZ0aFBab2g2ZmRmdXlrNmdhN3VOeXAxOEN4aTFjTkJoNVA5THc4M0pOWF9vQ2VodEROOEkwRXZiUTFTYWlDdFBYQmFzQXljaF9MRXpDRWhnWFhURVNXQXh6eXllZVQwZjg4ck1kQ3U0UDF3aGNnZE1RWERfa1RGXzJZR3psYktmYkJsRFNpY0ZwM0xZNHJNTWEwWUR4OUxLQlIzaUU0TVVDME0waDZ3TUt4WFFuQTNlclJQTERVYzNHWFFaWW82clB4bkM5YVg3eG93eHptQ3pJdTkxajVSeGMwQTBsRWxoU2hR?oc=5",
    "https://news.google.com/rss/articles/CBMizgFBVV95cUxPdzVweUROMThnYUJqY09Ed3RKNW54QmFVTEVIM3pWNUVRMzVFdGxLOU9DU1NDcExRMDlaVFdyc0x4X2xBQVg4Sk9FTHY0QnY3a0FUUzMtcXMwcjQtNEFKaUdVOUhTVXJLcGFoSnJ6MHc5TUlIZFIzZnNBTk5udW1nSHMtQ213aU1WVUdEYkJYOWZmd1l5anZaR2RqaUswSlRXdVVFdEtmbThvWEZLdGVLYTAwMEZhRk1Vdl9xQXRGeEIwNUtUckVES1dBTmhNZ9IB4gFBVV95cUxPTzB6X2JFTzFkQ2NZcmVJNFM3VE0zRkdkeHFkUXpXdE80eFliS29HNDZBUHU5bGxxN3QwdmxLSHBwVFZlbExuSUNhS1RhSEFlRTE0S0pjelNubU94SjBCbTlLLXkzMDFLd0Z0eGt2Y2JjWFFnakF3LXgxbTdZSkRlLUhhWEdVVktYQXRjMjhSTENXcmdadDJVRHB4dFd1NjhmN09aczZUU2pPaUNWS0stZVFVUlJTVlc4UG8zTzV2d3IwNDFlZ0U0SXU1V0pMQy00VDhEaUlJUzhJeV9QeEtrSU13?oc=5",
    "https://news.google.com/rss/articles/CBMiygFBVV95cUxPdkZsV1RSZm9vcjlBV2lFQndxbmoyTW1mTXhyWklGQzJQQkFLVzkwNGdYRmpycGdFUGR1MVJpRkF5bDczcW9yYzdWZ2ZuRlFIMzlDdzdNZ0F5aFpqQWFHM1JRMFo1aHgyLXBZeWFmZ3ZCS2gxXzBkdFF6QlQ5bVhOaV81VDIzbXpUS21pV2kwX1pFUnVsRUhRYm9ZTUFxWVRzRUVIRjNGclBKLS0xRjliYjNlenNRRWdhbk1IZlhaWTl0T3lncGN2SHJn0gHPAUFVX3lxTE5YOU1NM240OGNoQXJSbkRRTUFBRkp5a1FHcm51QkptNV9yamJNbFlaaktubldlWU5Ka1FORGthcVZ4S0piaGNkc25IOG1BSDNMa2pnSkRUWFpFeC11cHNGX2lpNGFKeEJhRkhWang5WXJBMTBJQXlzUEFJZFdFZlJmMzJxU0VoS05Ob1BfUGF3WXEtUDJrSG13NG5iQUVqbnlQb01wYURtMkY0S0VnUi03X0hDZFB2M2NXMFN6OXdjVFFhT0o1RWR6ektuRDA2dw?oc=5",
    "https://news.google.com/rss/articles/CBMioAFBVV95cUxOUVhBelpzQjNZV1hIQVltTDZtV3pRNkZybDVTOVRWTkRVUGU2QkZRbzRtcUJQcXo2d0RrbjJENnNlT05DNnRXYm9TNWltYjBRVW5LRDl3THZnUG5ER01OX09WWUUtdTFtbm1CLXNmYmJ2dm1weS01bHNhZXZQYnJUX1BpcGFoNm5JcS1DbmtpQWMzalY5WDMyc2JqZUhSS0kz?oc=5",
    "https://news.google.com/rss/articles/CBMizwFBVV95cUxOWDlNTTNuNDhjaEFyUm5EUU1BQUZKeWtRR3JudUJKbTVfcmpiTWxZWmpLbm5XZVlOSmtRTkRrYXFWeEtKYmhjZHNuSDhtQUgzTGtqZ0pEVFhaRXgtdXBzRl9paTRhSnhCYUZIVmp4OVlyQTEwSUF5c1BBSWRXRWZSZjMycVNFaEtOTm9QX1Bhd1lxLVAya0htdzRuYkFFam55UG9NcGFEbTJGNEtFZ1ItN19IQ2RQdjNjVzBTejl3Y1RRYU9KNUVkenpLbkQwNnfSAc8BQVVfeXFMTlg5TU0zbjQ4Y2hBclJuRFFNQUFGSnlrUUdybnVCSm01X3JqYk1sWVpqS25uV2VZTkprUU5Ea2FxVnhLSmJoY2Rzbkg4bUFIM0xramdKRFRYWkV4LXVwc0ZfaWk0YUp4QmFGSFZqeDlZckExMElBeXNQQUlkV0VmUmYzMnFTRWhLTk5vUF9QYXdZcS1QMmtIbXc0bmJBRWpueVBvTXBhRG0yRjRLRWdSLTdfSENkUHYzY1cwU3o5d2NUUWFPSjVFZHp6S25EMDZ3?oc=5",
    "https://www.latercera.com/nacional/noticia/reo-se-quito-la-vida-en-carcel-de-valparaiso-defensa-acredito-enajenacion-mental-y-esperaba-cupo-en-psiquiatrico-horwitz/",
    "https://www.biobiochile.cl/noticias/nacional/region-de-valparaiso/2026/08/25/interno-provisional-se-quita-la-vida-en-carcel-de-valparaiso-esperaba-cupo-para-psiquiatrico-horwitz.shtml",
    "https://www.lacuarta.com/chile/noticia/la-mato-con-un-martillo-durmio-junto-al-cuerpo-e-hizo-confesion-menor-de-14-anos-relato-parricidio-en-san-joaquin/",
)


def _iter_incident_files(data_dir: pathlib.Path) -> list[pathlib.Path]:
    """current.json + every archive/*.json under data_dir."""
    files: list[pathlib.Path] = []
    current = data_dir / "current.json"
    if current.exists():
        files.append(current)
    archive_dir = data_dir / "archive"
    if archive_dir.is_dir():
        files.extend(sorted(archive_dir.glob("*.json")))
    return files


def _load_incidents(path: pathlib.Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    incidents = payload.get("incidents") if isinstance(payload, dict) else payload
    if not isinstance(incidents, list):
        raise TypeError(f"{path}: incidents is not a list")
    return incidents


def check_data(data_dir: pathlib.Path) -> list[str]:
    """Returns a list of failure messages (empty = PASS)."""
    failures: list[str] = []
    files = _iter_incident_files(data_dir)
    if not files:
        failures.append(f"no incident files found under {data_dir}")
        return failures

    retitled_hit: dict | None = None

    for path in files:
        try:
            incidents = _load_incidents(path)
        except Exception as exc:  # malformed JSON / shape
            failures.append(f"{path}: unreadable ({exc})")
            continue

        by_id = {i.get("id"): i for i in incidents if isinstance(i, dict)}

        for dropped_id in DROPPED_IDS:
            if dropped_id in by_id:
                failures.append(f"{path}: hotfixed id resurfaced: {dropped_id}")

        if RETITLED_ID in by_id:
            retitled_hit = by_id[RETITLED_ID]
            title_es = retitled_hit.get("title_es")
            title_en = retitled_hit.get("title_en")
            if title_es != RETITLED_TITLE_ES:
                failures.append(
                    f"{path}: {RETITLED_ID} title_es regressed: {title_es!r} != {RETITLED_TITLE_ES!r}"
                )
            if title_en != RETITLED_TITLE_EN:
                failures.append(
                    f"{path}: {RETITLED_ID} title_en regressed: {title_en!r} != {RETITLED_TITLE_EN!r}"
                )

    if retitled_hit is None:
        failures.append(f"retitled card lost: {RETITLED_ID} absent from current + all archive files")

    return failures


def check_html(html_paths: list[pathlib.Path], current_path: pathlib.Path | None) -> list[str]:
    """Returns a list of failure messages (empty = PASS)."""
    failures: list[str] = []

    contents: dict[pathlib.Path, str] = {}
    for path in html_paths:
        try:
            contents[path] = path.read_text(encoding="utf-8")
        except Exception as exc:
            failures.append(f"{path}: unreadable ({exc})")

    for path, text in contents.items():
        for url in DROPPED_URLS:
            if url in text or html.escape(url) in text:
                failures.append(f"{path}: dropped url resurfaced: {url}")

    if current_path is not None:
        try:
            incidents = _load_incidents(current_path)
        except Exception as exc:
            failures.append(f"{current_path}: unreadable ({exc})")
            incidents = []
        by_id = {i.get("id"): i for i in incidents if isinstance(i, dict)}
        if RETITLED_ID in by_id:
            en_found = any(
                RETITLED_TITLE_EN in text or html.escape(RETITLED_TITLE_EN) in text
                for path, text in contents.items()
                if "/news/" in str(path).replace("\\", "/")
            )
            es_found = any(
                RETITLED_TITLE_ES in text or html.escape(RETITLED_TITLE_ES) in text
                for path, text in contents.items()
                if "/noticias/" in str(path).replace("\\", "/")
            )
            en_candidates = [p for p in contents if "/news/" in str(p).replace("\\", "/")]
            es_candidates = [p for p in contents if "/noticias/" in str(p).replace("\\", "/")]
            if en_candidates:
                if not en_found:
                    failures.append(
                        f"retitled EN string not found in EN html: {RETITLED_TITLE_EN!r}"
                    )
            if es_candidates:
                if not es_found:
                    failures.append(
                        f"retitled ES string not found in ES html: {RETITLED_TITLE_ES!r}"
                    )
            if not en_candidates and not es_candidates:
                print(
                    "check_hotfix_regression: note — --current given but no /news/ or "
                    "/noticias/ path among --html args; retitled-string check skipped"
                )
        else:
            print(
                f"check_hotfix_regression: note — {RETITLED_ID} absent from --current "
                "file; retitled-string check skipped"
            )

    return failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="FID-07: hotfixed cards (quick-260922-t59, G-27) never resurface"
    )
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--data", metavar="DATA_DIR", help="data/incidents directory")
    group.add_argument("--html", metavar="FILE", nargs="+", help="served HTML file(s)")
    ap.add_argument(
        "--current",
        metavar="CURRENT_JSON",
        default=None,
        help="the current.json served alongside --html (retitled-string check)",
    )
    args = ap.parse_args(argv)

    if args.current and not args.html:
        ap.error("--current requires --html")

    if args.data is not None:
        data_dir = pathlib.Path(args.data)
        if not data_dir.is_dir():
            print(f"::error::check_hotfix_regression: data dir not found: {data_dir}")
            return 2
        failures = check_data(data_dir)
    else:
        html_paths = [pathlib.Path(p) for p in args.html]
        for p in html_paths:
            if not p.exists():
                print(f"::error::check_hotfix_regression: html file not found: {p}")
                return 2
        current_path = pathlib.Path(args.current) if args.current else None
        if current_path is not None and not current_path.exists():
            print(f"::error::check_hotfix_regression: --current file not found: {current_path}")
            return 2
        failures = check_html(html_paths, current_path)

    if failures:
        for f in failures:
            print(f"check_hotfix_regression: FAIL — {f}")
        return 1

    print("check_hotfix_regression: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
