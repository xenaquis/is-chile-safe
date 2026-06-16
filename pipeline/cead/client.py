"""
pipeline/cead/client.py

CEAD HTTP client: session setup, commune batch fetch, raw caching, tenacity retry.

Key design constraints (from RESEARCH.md):
- Pitfall 1: Referer + Origin headers required or Azure gateway returns 403.
- Pitfall 3: Decode response.content.decode('latin-1') — NOT response.text.
- Pitfall 7: CUT codes MUST be sent as strings in the comuna[] array.
- D-03: 2–3 s inter-batch sleep belongs to the orchestrator loop, not here.
- D-04: Raw HTML cached to pipeline/cache/ (git-ignored).
"""
import pathlib
import requests
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_CEAD_BASE = (
    "https://cead.minsegpublica.gob.cl/wp-content/themes/gobcl-wp-master/data/"
)
_DATA_ENDPOINT = _CEAD_BASE + "get_estadisticas_delictuales.php"
_WARMUP_URL = "https://cead.minsegpublica.gob.cl/estadisticas-delictuales/"

CACHE_DIR = pathlib.Path(__file__).parent.parent / "cache"


# ---------------------------------------------------------------------------
# Session setup
# ---------------------------------------------------------------------------
def make_cead_session() -> requests.Session:
    """Create and warm-up a requests.Session suitable for CEAD requests.

    Sets the mandatory Referer/Origin/UA headers required by the Azure
    Application Gateway that fronts CEAD. Without these, every request
    returns HTTP 403 (Pitfall 1).

    The warm-up GET to the stats page sets the ``wpdm_client`` cookie that
    the gateway expects on subsequent POST requests.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (compatible; IsChileSafe data pipeline;"
                " +https://ischilesafe.com)"
            ),
            "Referer": "https://cead.minsegpublica.gob.cl/estadisticas-delictuales/",
            "Origin": "https://cead.minsegpublica.gob.cl",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
        }
    )
    # Warm-up: obtain wpdm_client cookie — without this, gateway returns 403
    session.get(_WARMUP_URL, timeout=15)
    return session


# ---------------------------------------------------------------------------
# Tenacity retry wrapper
# ---------------------------------------------------------------------------
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((requests.Timeout, requests.HTTPError)),
)
def _post_with_retry(session: requests.Session, url: str, data: dict) -> requests.Response:
    response = session.post(url, data=data, timeout=30)
    response.raise_for_status()
    return response


# ---------------------------------------------------------------------------
# Batch commune fetch
# ---------------------------------------------------------------------------
def fetch_communes_batch(
    session: requests.Session,
    cut_codes: list[str],
    year: int,
    familia_id: int,
) -> str:
    """Fetch CEAD rates for a batch of communes.

    Parameters
    ----------
    session:    Active requests.Session from make_cead_session().
    cut_codes:  List of CUT code strings (e.g. ['13101', '13102']).
    year:       Reference year (e.g. 2024).
    familia_id: Crime family ID (1–7, see FAMILIA_IDS in catalog.py).

    Returns
    -------
    Raw HTML string decoded with latin-1 (Pitfall 3).

    Notes
    -----
    - medida='2': rates per 100k — always use this (D-10).
    - tipoVal='1,2': police cases only (D-08).
    - descarga='true': returns HTML table with row class attributes.
    - CUT codes sent as str() — int silently fails (Pitfall 7).
    - region[] derived from first 2 digits of first CUT code.
    - Inter-batch sleep (D-03) is the caller's responsibility.
    """
    payload: dict = {
        "medida": "2",
        "tipoVal": "1,2",
        "anio[]": str(year),
        "familia[]": str(familia_id),
        "seleccion": "1",
        "descarga": "true",
    }

    # Build the comuna[] list — MUST be strings (Pitfall 7)
    payload["comuna[]"] = [str(cut) for cut in cut_codes]

    # region[] = first 2 digits of first CUT code
    payload["region[]"] = str(cut_codes[0])[:2]

    response = session.post(_DATA_ENDPOINT, data=payload, timeout=30)
    response.raise_for_status()

    # MUST use latin-1 — .text uses requests' charset detection which guesses wrong (Pitfall 3)
    return response.content.decode("latin-1")


# ---------------------------------------------------------------------------
# Subgroup batch fetch (Phase 14 — homicide subgroup 101)
# ---------------------------------------------------------------------------
def fetch_subgroup_batch(
    session: requests.Session,
    cut_codes: list[str],
    year: int,
    familia_id: int,
    subgrupo_id: int,
    medida: str = "2",
) -> str:
    """Fetch CEAD data for a specific crime subgroup for a batch of communes.

    CONFIRMED in Phase 14-01: the correct POST param is ``grupo[]=101``,
    NOT ``subgrupo[]=101`` (subgrupo[] is silently ignored, returns all-zero rows).
    Rate (medida="2") and count (medida="1") require two separate requests.

    Parameters
    ----------
    session:     Active requests.Session from make_cead_session().
    cut_codes:   List of CUT code strings (e.g. ['13101', '13102']).
    year:        Reference year (e.g. 2024).
    familia_id:  Crime family ID (1 = vida).
    subgrupo_id: Subgroup ID (101 = homicidios).
    medida:      "2" for rate per 100k (default), "1" for absolute count.

    Returns
    -------
    Raw HTML string decoded with latin-1 (Pitfall 3).
    """
    payload: dict = {
        "medida": medida,
        "tipoVal": "1,2",
        "anio[]": str(year),
        "familia[]": str(familia_id),
        "grupo[]": str(subgrupo_id),  # CONFIRMED: grupo[], NOT subgrupo[]
        "seleccion": "1",
        "descarga": "true",
    }

    # Build the comuna[] list — MUST be strings (Pitfall 7)
    payload["comuna[]"] = [str(cut) for cut in cut_codes]

    # region[] = first 2 digits of first CUT code
    payload["region[]"] = str(cut_codes[0])[:2]

    response = _post_with_retry(session, _DATA_ENDPOINT, payload)

    # MUST use latin-1 — .text uses requests' charset detection which guesses wrong (Pitfall 3)
    return response.content.decode("latin-1")


# ---------------------------------------------------------------------------
# Raw response cache (D-04)
# ---------------------------------------------------------------------------
def cache_raw(filename: str, content: str) -> None:
    """Cache raw HTML response to pipeline/cache/ (git-ignored).

    Never commit cache/ — it exists for debug/re-parse without re-scraping.
    """
    CACHE_DIR.mkdir(exist_ok=True)
    (CACHE_DIR / filename).write_text(content, encoding="utf-8")


def load_cached(filename: str) -> str | None:
    """Return cached content or None if file does not exist."""
    path = CACHE_DIR / filename
    return path.read_text(encoding="utf-8") if path.exists() else None
