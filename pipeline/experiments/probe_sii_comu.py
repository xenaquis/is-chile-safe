"""Phase 17 Wave 0 — S3: verify PUB_COMU.xlsb (current SII comuna dataset)."""
import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import requests  # noqa: E402
import pandas as pd  # noqa: E402

CACHE = REPO_ROOT / "pipeline" / "cache"
URL = "https://www.sii.cl/sobre_el_sii/empresas/PUB_COMU.xlsb"
H = {"User-Agent": "Mozilla/5.0 (compatible; IsChileSafe data pipeline; +https://ischilesafe.com)",
     "Accept-Language": "es-CL,es;q=0.9"}

dest = CACHE / "sii_pub_comu.xlsb"
r = requests.get(URL, headers=H, timeout=120)
r.raise_for_status()
dest.write_bytes(r.content)
print(f"downloaded {len(r.content):,} bytes")

xl = pd.ExcelFile(dest, engine="pyxlsb")
print("sheets:", xl.sheet_names)
# header row unknown; read raw to find it
raw = xl.parse(xl.sheet_names[0], header=None, nrows=12)
print("\nfirst 12 raw rows (col0..col6):")
print(raw.iloc[:, :7].to_string())

# find header row = the one containing 'Comuna' or 'Trabajadores'
hdr = None
for i in range(len(raw)):
    rowvals = [str(v) for v in raw.iloc[i].tolist()]
    if any("omuna" in v or "rabajador" in v or "Comercial" in v for v in rowvals):
        hdr = i
        break
print(f"\ndetected header row index: {hdr}")
df = xl.parse(xl.sheet_names[0], header=hdr)
df.columns = [str(c).strip() for c in df.columns]
print("columns:", list(df.columns))
ycol = df.columns[0]
years = pd.to_numeric(df[ycol], errors="coerce").dropna().astype(int)
print(f"year range: {years.min()}-{years.max()}  rows={len(df)}")
latest = years.max()
dl = df[pd.to_numeric(df[ycol], errors="coerce") == latest]
ccol = [c for c in df.columns if "omuna" in c.lower()]
wcol = [c for c in df.columns if "rabajador" in c.lower()]
ecol = [c for c in df.columns if "mpresas" in c.lower()]
print(f"comuna col={ccol}  firm col={ecol}  worker col={wcol}")
if ccol:
    print(f"{latest}: distinct comunas = {dl[ccol[0]].nunique()}")
    cols = ccol + ecol + wcol
    print(dl[cols].head(6).to_string())
