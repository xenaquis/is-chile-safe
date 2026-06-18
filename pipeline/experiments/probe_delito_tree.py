"""Phase 17 Wave 0 — extract familia/grupo/subgrupo names from CEAD page HTML.

The delito selector tree is rendered server-side in the estadisticas page, not
via ajax_2.php. Fetch the page and pull every option that carries a ckH(...)
or data-value handler tied to familia/grupo/subgrupo, so grupo IDs (101..106)
get names and secuestro's familia/grupo is located.
"""
import sys
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pipeline.cead.client import make_cead_session  # noqa: E402

PAGE = "https://cead.minsegpublica.gob.cl/estadisticas-delictuales/"
CACHE = REPO_ROOT / "pipeline" / "cache"


def main():
    session = make_cead_session()
    resp = session.get(PAGE, timeout=30)
    html = resp.content.decode("utf-8", errors="replace")
    (CACHE / "cead_page.html").write_text(html, encoding="utf-8")
    print(f"page HTTP {resp.status_code} len={len(html)}")

    # ckH('familia_101', LEVEL, '101', 'Homicidios') style handlers
    pat = re.compile(r"ckH\('([a-z]+)_([0-9]+)'\s*,\s*([0-9]+)\s*,\s*'([0-9]+)'\s*,\s*'([^']+)'\)")
    seen = set()
    for m in pat.finditer(html):
        kind, idn, level, val, name = m.groups()
        key = (kind, val, name)
        if key in seen:
            continue
        seen.add(key)
        if kind in ("familia", "grupo", "subgrupo", "delito"):
            print(f"  {kind:9} id={val:>5} level={level} name={name!r}")

    if not seen:
        # fall back: dump any data-value items near 'delito'/'familia'
        print("\n  no ckH delito handlers found; searching id= patterns")
        for m in re.finditer(r'id="(familia|grupo|subgrupo|delito)_([0-9]+)"', html):
            print(f"  {m.group(1)} id={m.group(2)}")


if __name__ == "__main__":
    main()
