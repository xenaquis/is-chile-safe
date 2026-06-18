"""
Phase 17 Wave 0 — S2/S3: download + inspect the SPD and SII datasets.

S2  SPD homicide  : Base_de_Datos_VHC_2018_2025.xlsx (Víctimas Homicidios Consumados)
S3  SII exposure  : PUB_Reg_Com.xlsx (empresas + trabajadores dependientes por comuna)

Confirms: reachable from this egress, sheet/column structure, the granularity
column (comuna vs region), year coverage, and whether a worker-count column
exists for the exposure denominator.
"""
import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import requests  # noqa: E402
import pandas as pd  # noqa: E402

CACHE = REPO_ROOT / "pipeline" / "cache"
CACHE.mkdir(exist_ok=True)

SOURCES = {
    "spd_vhc": "https://prevenciondehomicidios.cl/wp-content/uploads/2026/03/Base_de_Datos_VHC_2018_2025.xlsx",
    "sii_emp": "https://www.sii.cl/estadisticas/region/PUB_Reg_Com.xlsx",
}

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (compatible; IsChileSafe data pipeline;"
                   " +https://ischilesafe.com)"),
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
}


def download(name: str, url: str) -> pathlib.Path | None:
    dest = CACHE / f"{name}.xlsx"
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
        r.raise_for_status()
    except Exception as exc:
        print(f"[{name}] DOWNLOAD FAIL {type(exc).__name__}: {exc}")
        return None
    dest.write_bytes(r.content)
    print(f"[{name}] downloaded {len(r.content):,} bytes -> {dest.name}")
    return dest


def inspect(name: str, path: pathlib.Path) -> None:
    print(f"\n{'='*64}\n{name} — {path.name}\n{'='*64}")
    try:
        xl = pd.ExcelFile(path, engine="openpyxl")
    except Exception as exc:
        print(f"  cannot open: {exc}")
        return
    print(f"  sheets: {xl.sheet_names}")
    for sheet in xl.sheet_names[:4]:
        try:
            df = xl.parse(sheet, nrows=12)
        except Exception as exc:
            print(f"  [{sheet}] parse fail: {exc}")
            continue
        print(f"\n  --- sheet {sheet!r}: shape(head)={df.shape} ---")
        print(f"  columns: {list(df.columns)[:25]}")
        # print first few rows compactly
        with pd.option_context("display.max_columns", 20, "display.width", 200):
            print(df.head(8).to_string()[:2000])


def main():
    for name, url in SOURCES.items():
        path = download(name, url)
        if path:
            inspect(name, path)


if __name__ == "__main__":
    main()
