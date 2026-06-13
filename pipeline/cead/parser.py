"""
pipeline/cead/parser.py

CEAD HTML table parser and decimal utility.

Key design constraints:
- Pitfall 2 (CRITICAL): CEAD uses Chilean locale — '1.154,3537' means 1154.3537.
  parse_cead_float handles this and maps missing-value markers to None.
- CEAD response MIME is vnd.ms-excel but body is always HTML.
- Row class 'formato_4' identifies commune rows (not region/national).
"""
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Decimal parsing utility (Pitfall 2 — applied to all CEAD numeric values)
# ---------------------------------------------------------------------------
def parse_cead_float(value: str) -> float | None:
    """Convert a Chilean-locale CEAD number string to float, or None if missing.

    CEAD uses:
      - Period (.) as thousands separator: '1.154' means one thousand one hundred fifty-four
      - Comma (,) as decimal separator: '0,35' means 0.35

    Missing-value markers ('-', 'S/I', 'N/A', '') all map to None.

    Examples
    --------
    >>> parse_cead_float('1.154,3537')
    1154.3537
    >>> parse_cead_float('-')  # no data
    None
    >>> parse_cead_float('0,0')
    0.0
    """
    v = value.strip()
    if v in ("", "-", "S/I", "N/A"):
        return None
    # Remove thousands separator, replace decimal comma with period
    return float(v.replace(".", "").replace(",", "."))


# ---------------------------------------------------------------------------
# HTML table parser
# ---------------------------------------------------------------------------
def parse_cead_table(html: str) -> list[dict]:
    """Parse a CEAD HTML response into a list of data rows.

    The CEAD response (with descarga=true) is HTML wrapped in a vnd.ms-excel
    MIME type. Each row has a CSS class:
      - formato_1: national aggregate
      - formato_2: regional aggregate
      - formato_3: provincial aggregate
      - formato_4: commune row (the ones we want)

    Returns
    -------
    List of row dicts: {'name': str, 'class': list[str], 'values': {year: str}}

    Skips label rows: 'DELITOS O FALTAS', 'UNIDAD TERRITORIAL', and empty rows.
    Year strings are extracted from the header row (the first row where any
    cell contains only digits, e.g. '2022', '2023', '2024').
    """
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    if not tables:
        return []

    data_table = tables[-1]  # last table is always the data table

    headers: list[str] = []
    rows: list[dict] = []

    for tr in data_table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
        if not cells:
            continue

        # Detect the year header row — any row where at least one cell is a
        # 4-digit year string (digits only)
        if not headers and any(c.isdigit() and len(c) == 4 for c in cells):
            headers = cells  # e.g. ['', '2022', '2023', '2024']
            continue

        # Skip label rows
        if cells[0] in ("", "DELITOS O FALTAS", "UNIDAD TERRITORIAL"):
            continue

        # Skip rows that appeared before we found the header
        if not headers:
            continue

        row_class = tr.get("class", [])
        rows.append(
            {
                "name": cells[0],
                "class": row_class,
                "values": {
                    headers[i]: cells[i]
                    for i in range(1, len(cells))
                    if i < len(headers)
                },
            }
        )

    return rows
