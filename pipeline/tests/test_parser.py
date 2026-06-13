"""
pipeline/tests/test_parser.py

Unit tests for pipeline/cead/parser.py.
Tests parse_cead_float and parse_cead_table (against fixture HTML).
"""
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestParseCeadFloat:
    def test_chilean_locale_number(self):
        from pipeline.cead.parser import parse_cead_float
        assert parse_cead_float("1.154,3537") == pytest.approx(1154.3537)

    def test_dash_returns_none(self):
        from pipeline.cead.parser import parse_cead_float
        assert parse_cead_float("-") is None

    def test_empty_string_returns_none(self):
        from pipeline.cead.parser import parse_cead_float
        assert parse_cead_float("") is None

    def test_si_returns_none(self):
        from pipeline.cead.parser import parse_cead_float
        assert parse_cead_float("S/I") is None

    def test_na_returns_none(self):
        from pipeline.cead.parser import parse_cead_float
        assert parse_cead_float("N/A") is None

    def test_zero_comma_zero(self):
        from pipeline.cead.parser import parse_cead_float
        assert parse_cead_float("0,0") == pytest.approx(0.0)

    def test_simple_integer_string(self):
        from pipeline.cead.parser import parse_cead_float
        assert parse_cead_float("100") == pytest.approx(100.0)

    def test_leading_trailing_whitespace(self):
        from pipeline.cead.parser import parse_cead_float
        assert parse_cead_float("  1.234,56  ") == pytest.approx(1234.56)


class TestParseCeadTable:
    @pytest.fixture
    def fixture_html(self):
        html_path = FIXTURES_DIR / "cead_response_sample.html"
        return html_path.read_text(encoding="utf-8")

    def test_returns_list_of_dicts(self, fixture_html):
        from pipeline.cead.parser import parse_cead_table
        result = parse_cead_table(fixture_html)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_row_has_required_keys(self, fixture_html):
        from pipeline.cead.parser import parse_cead_table
        rows = parse_cead_table(fixture_html)
        for row in rows:
            assert "name" in row
            assert "class" in row
            assert "values" in row

    def test_contains_formato_4_rows(self, fixture_html):
        from pipeline.cead.parser import parse_cead_table
        rows = parse_cead_table(fixture_html)
        formato4_rows = [r for r in rows if "formato_4" in r["class"]]
        assert len(formato4_rows) >= 2, "Expected at least 2 formato_4 commune rows"

    def test_formato4_row_values_keyed_by_year(self, fixture_html):
        from pipeline.cead.parser import parse_cead_table
        rows = parse_cead_table(fixture_html)
        formato4_rows = [r for r in rows if "formato_4" in r["class"]]
        for row in formato4_rows:
            assert len(row["values"]) > 0, "values dict should not be empty"
            for key in row["values"]:
                assert key.isdigit(), f"Year key '{key}' should be numeric"

    def test_label_rows_excluded(self, fixture_html):
        from pipeline.cead.parser import parse_cead_table
        rows = parse_cead_table(fixture_html)
        names = [r["name"] for r in rows]
        assert "DELITOS O FALTAS" not in names
        assert "UNIDAD TERRITORIAL" not in names

    def test_at_least_two_commune_rows(self, fixture_html):
        from pipeline.cead.parser import parse_cead_table
        rows = parse_cead_table(fixture_html)
        formato4_rows = [r for r in rows if "formato_4" in r["class"]]
        assert len(formato4_rows) >= 2
