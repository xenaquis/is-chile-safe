"""
Phase 17 Wave 0 — S2: SPD homicide source recon (prevenciondehomicidios.cl).

D-HOM switches the homicide metric to the SPD consolidated figure
(Carabineros + PDI + SML + Fiscalía). This probe replicates the CEAD-style
header/UA warmup against SPD and inspects each candidate page for:
  - reachability from THIS egress (sandbox = 403; local CL = expected OK)
  - downloadable datasets (CSV/XLSX/JSON/API) vs charts-only
  - granularity hints (comuna vs region vs national)
"""
import sys
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import requests  # noqa: E402

CACHE = REPO_ROOT / "pipeline" / "cache"
CACHE.mkdir(exist_ok=True)

BASE = "https://prevenciondehomicidios.cl"
PATHS = [
    "/",
    "/estadisticas",
    "/estadisticas/",
    "/cifras-oficiales",
    "/cifras-oficiales/",
    "/datos-abiertos",
]

GRANULARITY = re.compile(r"\b(comuna|comunal|regi[oó]n|regional|nacional|pa[ií]s)\b", re.I)
DOWNLOAD = re.compile(r'href="([^"]+\.(?:csv|xlsx?|json|geojson|zip))"', re.I)
APICALL = re.compile(r'(fetch\(|ajax|\.json|api/|wp-json|/data/)', re.I)


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (compatible; IsChileSafe data pipeline;"
                       " +https://ischilesafe.com)"),
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return s


def main():
    s = make_session()
    for path in PATHS:
        url = BASE + path
        try:
            r = s.get(url, timeout=25, allow_redirects=True)
        except Exception as exc:
            print(f"{url}\n    FAIL {type(exc).__name__}: {exc}")
            continue
        body = r.content.decode("utf-8", errors="replace")
        downloads = sorted(set(DOWNLOAD.findall(body)))
        gran = sorted(set(m.lower() for m in GRANULARITY.findall(body)))
        api = bool(APICALL.search(body))
        print(f"{url}")
        print(f"    HTTP {r.status_code}  final={r.url}  len={len(body)}")
        print(f"    granularity hits: {gran}")
        print(f"    download links: {downloads[:10]}")
        print(f"    has fetch/ajax/json: {api}")
        safe = path.strip("/").replace("/", "_") or "root"
        (CACHE / f"spd_{safe}.html").write_text(body, encoding="utf-8")


if __name__ == "__main__":
    main()
