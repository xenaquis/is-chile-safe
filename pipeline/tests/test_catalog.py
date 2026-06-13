"""
pipeline/tests/test_catalog.py

Unit tests for pipeline/cead/catalog.py.
All tests mock HTTP — no live CEAD calls.
"""
import json
import pytest
from unittest.mock import MagicMock


def _make_mocked_session(cut_name_pairs: list[tuple[str, str]]):
    """Return a mock session whose .post() returns a ComunasDel JSON response."""
    # CEAD returns a JSON where ComunasDel is a list of JSON-encoded strings
    comunas_del = [
        json.dumps({"comDelId": cut, "comDelNombre": name})
        for cut, name in cut_name_pairs
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = {"ComunasDel": comunas_del}
    session = MagicMock()
    session.post.return_value = mock_response
    return session


class TestGetCommuneCatalog:
    def test_returns_dict_cut_to_name(self):
        from pipeline.cead.catalog import get_commune_catalog
        session = _make_mocked_session([("13101", "Santiago"), ("13102", "Cerrillos")])
        result = get_commune_catalog(session)
        assert result["13101"] == "Santiago"
        assert result["13102"] == "Cerrillos"

    def test_returns_all_entries_from_mock(self):
        from pipeline.cead.catalog import get_commune_catalog
        pairs = [(str(10000 + i), f"Comuna{i}") for i in range(346)]
        session = _make_mocked_session(pairs)
        result = get_commune_catalog(session)
        assert len(result) == 346

    def test_posts_to_ajax2_endpoint(self):
        from pipeline.cead.catalog import get_commune_catalog
        session = _make_mocked_session([("13101", "Santiago")])
        get_commune_catalog(session)
        call_url = session.post.call_args[0][0]
        assert "ajax_2.php" in call_url

    def test_payload_uses_seleccion_101(self):
        from pipeline.cead.catalog import get_commune_catalog
        session = _make_mocked_session([("13101", "Santiago")])
        get_commune_catalog(session)
        payload = session.post.call_args[1]["data"]
        assert str(payload.get("seleccion")) == "101"


class TestRegionIds:
    def test_region_ids_has_16_entries(self):
        from pipeline.cead.catalog import REGION_IDS
        assert len(REGION_IDS) == 16

    def test_region_13_is_metropolitana(self):
        from pipeline.cead.catalog import REGION_IDS
        assert "Metropolitana" in REGION_IDS[13]


class TestFamiliaIds:
    def test_familia_ids_has_7_entries(self):
        from pipeline.cead.catalog import FAMILIA_IDS
        assert len(FAMILIA_IDS) == 7

    def test_all_familia_keys_present(self):
        from pipeline.cead.catalog import FAMILIA_IDS
        expected_keys = {"vida", "robos_violentos", "vif", "drogas", "armas", "propiedad", "incivilidades"}
        assert set(FAMILIA_IDS.values()) == expected_keys
