"""
pipeline/cead/catalog.py

CEAD commune catalog fetcher, region ID map, and crime family ID map.

The catalog endpoint (ajax_2.php with seleccion=101) returns all 346 communes
with their CUT codes — this is the canonical source for commune IDs.

NOTE A1 (Assumption): seleccion=101 is assumed to return all 346 communes
regardless of the region parameter. If it returns only a subset, loop over
all 16 REGION_IDS and merge results.
"""
import json
import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_CATALOG_URL = (
    "https://cead.minsegpublica.gob.cl/wp-content/themes/gobcl-wp-master/data/ajax_2.php"
)

# 16 official regions (RESEARCH.md + como scrap.txt)
REGION_IDS: dict[int, str] = {
    15: "Arica y Parinacota",
    1: "Tarapacá",
    2: "Antofagasta",
    3: "Atacama",
    4: "Coquimbo",
    5: "Valparaíso",
    13: "Metropolitana",
    6: "O'Higgins",
    7: "Maule",
    16: "Ñuble",
    8: "Biobío",
    9: "La Araucanía",
    14: "Los Ríos",
    10: "Los Lagos",
    11: "Aysén",
    12: "Magallanes",
}

# 7 crime families (D-05)
FAMILIA_IDS: dict[int, str] = {
    1: "vida",
    2: "robos_violentos",
    3: "vif",
    4: "drogas",
    5: "armas",
    6: "propiedad",
    7: "incivilidades",
}


# ---------------------------------------------------------------------------
# Catalog fetch
# ---------------------------------------------------------------------------
def get_commune_catalog(session: requests.Session) -> dict[str, str]:
    """Return {cut_code: commune_name} for all 346 communes.

    Fetches ajax_2.php with seleccion=101 which returns ComunasDel — a JSON
    array of JSON-encoded strings, each with comDelId (CUT) and comDelNombre.

    See NOTE A1 above regarding the assumption that seleccion=101 returns all
    346 communes. If only a subset is returned, iterate over REGION_IDS.
    """
    response = session.post(
        _CATALOG_URL,
        data={"region": "13", "seleccion": "101"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    return {
        json.loads(c)["comDelId"]: json.loads(c)["comDelNombre"]
        for c in data["ComunasDel"]
    }
