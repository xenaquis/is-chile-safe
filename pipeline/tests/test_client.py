"""
pipeline/tests/test_client.py

Unit tests for pipeline/cead/client.py.
All tests mock HTTP — no live CEAD calls.
"""
import pytest
from unittest.mock import MagicMock, patch, call


class TestMakeCeadSession:
    def test_referer_header_set(self):
        from pipeline.cead.client import make_cead_session
        with patch("pipeline.cead.client.requests.Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value = mock_session
            mock_session.get.return_value = MagicMock(status_code=200)
            session = make_cead_session()
            updated_headers = mock_session.headers.update.call_args[0][0]
            assert "Referer" in updated_headers
            assert "cead.minsegpublica.gob.cl" in updated_headers["Referer"]

    def test_origin_header_set(self):
        from pipeline.cead.client import make_cead_session
        with patch("pipeline.cead.client.requests.Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value = mock_session
            mock_session.get.return_value = MagicMock(status_code=200)
            make_cead_session()
            updated_headers = mock_session.headers.update.call_args[0][0]
            assert "Origin" in updated_headers
            assert "cead.minsegpublica.gob.cl" in updated_headers["Origin"]

    def test_warmup_get_called(self):
        from pipeline.cead.client import make_cead_session
        with patch("pipeline.cead.client.requests.Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value = mock_session
            mock_session.get.return_value = MagicMock(status_code=200)
            make_cead_session()
            assert mock_session.get.called


class TestFetchCommunesBatch:
    def _make_fake_session(self, html_content=b"<html><table></table></html>"):
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = html_content
        mock_response.raise_for_status.return_value = None
        session.post.return_value = mock_response
        return session

    def test_payload_medida_is_2(self):
        from pipeline.cead.client import fetch_communes_batch
        session = self._make_fake_session()
        fetch_communes_batch(session, ["13101", "13102"], 2024, 6)
        payload = session.post.call_args[1]["data"]
        assert payload["medida"] == "2"

    def test_payload_tipo_val(self):
        from pipeline.cead.client import fetch_communes_batch
        session = self._make_fake_session()
        fetch_communes_batch(session, ["13101", "13102"], 2024, 6)
        payload = session.post.call_args[1]["data"]
        assert payload["tipoVal"] == "1,2"

    def test_payload_seleccion_is_1(self):
        from pipeline.cead.client import fetch_communes_batch
        session = self._make_fake_session()
        fetch_communes_batch(session, ["13101", "13102"], 2024, 6)
        payload = session.post.call_args[1]["data"]
        assert payload["seleccion"] == "1"

    def test_payload_descarga_true(self):
        from pipeline.cead.client import fetch_communes_batch
        session = self._make_fake_session()
        fetch_communes_batch(session, ["13101", "13102"], 2024, 6)
        payload = session.post.call_args[1]["data"]
        assert payload["descarga"] == "true"

    def test_anio_is_string_of_year(self):
        from pipeline.cead.client import fetch_communes_batch
        session = self._make_fake_session()
        fetch_communes_batch(session, ["13101"], 2024, 6)
        payload = session.post.call_args[1]["data"]
        assert payload["anio[]"] == "2024"

    def test_familia_is_string_of_familia_id(self):
        from pipeline.cead.client import fetch_communes_batch
        session = self._make_fake_session()
        fetch_communes_batch(session, ["13101"], 2024, 3)
        payload = session.post.call_args[1]["data"]
        assert payload["familia[]"] == "3"

    def test_comuna_values_are_strings(self):
        """Pitfall 7: CUT codes must be sent as strings, not ints."""
        from pipeline.cead.client import fetch_communes_batch
        session = self._make_fake_session()
        fetch_communes_batch(session, ["13101", "13102"], 2024, 6)
        payload = session.post.call_args[1]["data"]
        for cut in payload["comuna[]"]:
            assert isinstance(cut, str), f"Expected str, got {type(cut)} for {cut}"

    def test_region_derived_from_first_two_digits(self):
        from pipeline.cead.client import fetch_communes_batch
        session = self._make_fake_session()
        fetch_communes_batch(session, ["13101", "13102"], 2024, 6)
        payload = session.post.call_args[1]["data"]
        assert payload["region[]"] == "13"

    def test_returns_latin1_decoded_string(self):
        """Pitfall 3: Must decode response.content as latin-1, not use .text."""
        from pipeline.cead.client import fetch_communes_batch
        # Simulate a response with latin-1 encoded accented content
        latin1_bytes = "Ñuñoa".encode("latin-1")
        session = self._make_fake_session(html_content=latin1_bytes)
        result = fetch_communes_batch(session, ["13115"], 2024, 6)
        assert result == "Ñuñoa"


class TestCacheRawAndLoadCached:
    def test_cache_roundtrip(self, tmp_path, monkeypatch):
        import pipeline.cead.client as client_module
        monkeypatch.setattr(client_module, "CACHE_DIR", tmp_path)
        client_module.cache_raw("test.html", "<html>test</html>")
        result = client_module.load_cached("test.html")
        assert result == "<html>test</html>"

    def test_load_cached_returns_none_if_missing(self, tmp_path, monkeypatch):
        import pipeline.cead.client as client_module
        monkeypatch.setattr(client_module, "CACHE_DIR", tmp_path)
        result = client_module.load_cached("nonexistent.html")
        assert result is None
