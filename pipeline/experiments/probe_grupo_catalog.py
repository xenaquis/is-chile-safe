"""
pipeline/experiments/probe_grupo_catalog.py  (v2)

Phase 17 Wave 0 — pull the full CEAD grupo/subgrupo catalog.

The delito selectors are populated by POST ajax_2.php with seleccion=9
(familia -> grupos) / seleccion=10 (grupo -> subgrupos). The response carries
data.opcionGrupos / data.opcionSubgrupos as HTML whose items embed
ckH('grupo_<id>', LEVEL, '<id>', '<name>').

We call seleccion=9 once per familia (1..7) to dump every grupo name+id, and
seleccion=10 per grupo to dump subgrupos — locating lesiones and secuestro.
"""
import sys
import pathlib
import re
import json

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pipeline.cead.client import make_cead_session  # noqa: E402

AJAX = "https://cead.minsegpublica.gob.cl/wp-content/themes/gobcl-wp-master/data/ajax_2.php"
CACHE = REPO_ROOT / "pipeline" / "cache"

FAMILIAS = {
    1: "vida", 2: "robos_violentos", 3: "vif", 4: "drogas",
    5: "armas", 6: "propiedad", 7: "incivilidades",
}

CKH = re.compile(r"ckH\('[a-z]+_([0-9]+)'\s*,\s*[0-9]+\s*,\s*'([0-9]+)'\s*,\s*'([^']*)'\)")
DV = re.compile(r'data-value="([0-9]+)"[^>]*>(?:<input[^>]*>)?\s*([^<]+)<')


def parse_items(html_fragment: str):
    out = []
    for m in CKH.finditer(html_fragment):
        out.append((m.group(2), m.group(3)))
    if not out:
        for m in DV.finditer(html_fragment):
            out.append((m.group(1), m.group(2).strip()))
    return out


def main():
    session = make_cead_session()
    catalog = {}
    for fid, fname in FAMILIAS.items():
        payload = {"familia": str(fid), "grupo": "", "subgrupo": "", "seleccion": "9"}
        resp = session.post(AJAX, data=payload, timeout=20)
        try:
            data = resp.json()
        except Exception:
            print(f"familia {fid} ({fname}): non-JSON ({resp.status_code})")
            continue
        grupos_html = data.get("opcionGrupos", "") or ""
        subs_html = data.get("opcionSubgrupos", "") or ""
        grupos = parse_items(grupos_html)
        print(f"\n=== familia {fid} ({fname}) -> {len(grupos)} grupos ===")
        catalog[fid] = {"name": fname, "grupos": {}}
        for gid, gname in grupos:
            print(f"  grupo {gid:>4}  {gname}")
            catalog[fid]["grupos"][gid] = {"name": gname, "subgrupos": {}}
        # subgrupos for THIS familia come back in the same call
        subs = parse_items(subs_html)
        if subs:
            print(f"  -- subgrupos in familia {fid}:")
            for sid, sname in subs:
                print(f"     sub {sid:>5}  {sname}")

    (CACHE / "grupo_catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n[saved] {CACHE / 'grupo_catalog.json'}")


if __name__ == "__main__":
    main()
