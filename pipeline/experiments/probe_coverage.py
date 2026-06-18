"""Phase 17 Wave 0 — S2/S3 coverage check: comuna completeness + grouping."""
import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd  # noqa: E402

CACHE = REPO_ROOT / "pipeline" / "cache"


def spd():
    print("=" * 64)
    print("SPD VHC — comuna coverage + grouping")
    print("=" * 64)
    df = pd.read_excel(CACHE / "spd_vhc.xlsx", sheet_name="Base de Datos", engine="openpyxl")
    print(f"  total victim rows: {len(df):,}")
    print(f"  years (ID_ANO): {sorted(df['ID_ANO'].dropna().unique().tolist())}")
    comunas = df["COMUN_AGR"].dropna().astype(str).unique()
    print(f"  distinct COMUN_AGR: {len(comunas)}")
    grouped = [c for c in comunas if any(k in c.lower() for k in ("otra", "agrup", "resto", "varias", "sin "))]
    print(f"  grouping/'otras' style labels: {grouped[:20]}")
    # homicides per year, national
    print("  victims per year:")
    print(df.groupby("ID_ANO").size().to_string())
    # sample top comunas 2024
    d24 = df[df["ID_ANO"] == 2024]
    print(f"\n  2024 victims: {len(d24)} ; top 10 comunas:")
    print(d24["COMUN_AGR"].value_counts().head(10).to_string())


def sii():
    print("\n" + "=" * 64)
    print("SII empresas — comuna coverage (header on row 5)")
    print("=" * 64)
    df = pd.read_excel(CACHE / "sii_emp.xlsx", sheet_name="EMP_Reg_Com",
                       engine="openpyxl", header=5)
    df.columns = [str(c).strip() for c in df.columns]
    print(f"  columns: {list(df.columns)}")
    ycol = df.columns[0]
    ccol = "ID_Comuna"
    print(f"  total rows: {len(df):,}")
    years = pd.to_numeric(df[ycol], errors="coerce").dropna().astype(int)
    print(f"  year range: {years.min()}–{years.max()}")
    latest = years.max()
    dl = df[pd.to_numeric(df[ycol], errors="coerce") == latest]
    print(f"  {latest}: distinct comunas = {dl[ccol].nunique()}")
    print(f"  sample comuna names: {dl[ccol].dropna().astype(str).unique()[:8].tolist()}")
    wcol = [c for c in df.columns if "Trabajadores" in c][0]
    ecol = [c for c in df.columns if "Empresas" in c][0]
    print(f"  worker col: {wcol!r}")
    print(f"  firm col:   {ecol!r}")
    sample = dl[[ccol, ecol, wcol]].head(6)
    print(sample.to_string())


if __name__ == "__main__":
    spd()
    sii()
