"""
Tests for pipeline/cead/normalizer.py — trend, slug, ranks, featured flags, quintile level.
All tests are offline (no network, no live data).
"""
import pytest


# ---------------------------------------------------------------------------
# compute_trend
# ---------------------------------------------------------------------------

def test_compute_trend_up():
    from pipeline.cead.normalizer import compute_trend
    # Rate rises >5%: 100 -> 130 (30% increase)
    series = [
        {"year": 2019, "rate_per_100k": 100.0},
        {"year": 2020, "rate_per_100k": 105.0},
        {"year": 2021, "rate_per_100k": 115.0},
        {"year": 2022, "rate_per_100k": 130.0},
    ]
    assert compute_trend(series) == "up"


def test_compute_trend_down():
    from pipeline.cead.normalizer import compute_trend
    # Rate falls >5%: 100 -> 80 (-20%)
    series = [
        {"year": 2019, "rate_per_100k": 100.0},
        {"year": 2020, "rate_per_100k": 95.0},
        {"year": 2021, "rate_per_100k": 88.0},
        {"year": 2022, "rate_per_100k": 80.0},
    ]
    assert compute_trend(series) == "down"


def test_compute_trend_stable():
    from pipeline.cead.normalizer import compute_trend
    # Rate changes within ±5%: 100 -> 103
    series = [
        {"year": 2019, "rate_per_100k": 100.0},
        {"year": 2020, "rate_per_100k": 101.0},
        {"year": 2021, "rate_per_100k": 102.0},
        {"year": 2022, "rate_per_100k": 103.0},
    ]
    assert compute_trend(series) == "stable"


def test_compute_trend_short_series_returns_stable():
    from pipeline.cead.normalizer import compute_trend
    # Fewer than 4 data points → stable
    series = [
        {"year": 2021, "rate_per_100k": 100.0},
        {"year": 2022, "rate_per_100k": 200.0},
    ]
    assert compute_trend(series) == "stable"


def test_compute_trend_zero_start_rate_returns_stable():
    from pipeline.cead.normalizer import compute_trend
    # Starting rate is 0 → no division by zero → stable
    series = [
        {"year": 2019, "rate_per_100k": 0.0},
        {"year": 2020, "rate_per_100k": 0.0},
        {"year": 2021, "rate_per_100k": 5.0},
        {"year": 2022, "rate_per_100k": 100.0},
    ]
    assert compute_trend(series) == "stable"


def test_compute_trend_empty_series_returns_stable():
    from pipeline.cead.normalizer import compute_trend
    assert compute_trend([]) == "stable"


def test_compute_trend_exactly_at_threshold_returns_stable():
    from pipeline.cead.normalizer import compute_trend
    # Exactly 5% change → still stable (threshold is exclusive >5%)
    series = [
        {"year": 2019, "rate_per_100k": 100.0},
        {"year": 2020, "rate_per_100k": 101.0},
        {"year": 2021, "rate_per_100k": 102.0},
        {"year": 2022, "rate_per_100k": 105.0},
    ]
    assert compute_trend(series) == "stable"


# ---------------------------------------------------------------------------
# make_slug
# ---------------------------------------------------------------------------

def test_make_slug_nunoa():
    from pipeline.cead.normalizer import make_slug
    assert make_slug("Ñuñoa") == "nunoa"


def test_make_slug_ohiggins():
    from pipeline.cead.normalizer import make_slug
    assert make_slug("O'Higgins") == "ohiggins"


def test_make_slug_aysen():
    from pipeline.cead.normalizer import make_slug
    assert make_slug("Aysén") == "aysen"


def test_make_slug_lowercase_and_hyphens():
    from pipeline.cead.normalizer import make_slug
    slug = make_slug("Los Ángeles")
    assert slug == "los-angeles"


def test_make_slug_strip_leading_trailing_hyphens():
    from pipeline.cead.normalizer import make_slug
    # Ensure no leading/trailing hyphens
    result = make_slug("Santiago")
    assert not result.startswith("-")
    assert not result.endswith("-")


# ---------------------------------------------------------------------------
# compute_ranks
# ---------------------------------------------------------------------------

def _make_record(cut, region_id, rate, low_pop=False):
    """Build a minimal record dict for rank testing."""
    return {
        "id": cut,
        "region_id": region_id,
        "low_population": low_pop,
        "national_rank": None,
        "regional_rank": None,
        "series": [{"year": 2022, "rate_per_100k": rate, "by_family": {}, "partial": False}],
    }


def test_compute_ranks_highest_rate_gets_rank_1():
    from pipeline.cead.normalizer import compute_ranks
    records = [
        _make_record("13101", "13", 100.0),
        _make_record("13102", "13", 200.0),
        _make_record("13103", "13", 50.0),
    ]
    result = compute_ranks(records, 2022)
    # Highest rate (200) should get national_rank=1
    highest = next(r for r in result if r["id"] == "13102")
    assert highest["national_rank"] == 1


def test_compute_ranks_low_population_gets_none():
    from pipeline.cead.normalizer import compute_ranks
    records = [
        _make_record("13101", "13", 100.0),
        _make_record("99999", "99", 999.0, low_pop=True),
    ]
    result = compute_ranks(records, 2022)
    low_pop = next(r for r in result if r["id"] == "99999")
    assert low_pop["national_rank"] is None
    assert low_pop["regional_rank"] is None


def test_compute_ranks_regional_rank_scoped_to_region():
    from pipeline.cead.normalizer import compute_ranks
    records = [
        _make_record("13101", "13", 100.0),
        _make_record("13102", "13", 200.0),
        _make_record("05101", "05", 150.0),  # Different region
    ]
    result = compute_ranks(records, 2022)
    # Region 13: 13102 (200) is rank 1, 13101 (100) is rank 2
    r13102 = next(r for r in result if r["id"] == "13102")
    r13101 = next(r for r in result if r["id"] == "13101")
    r05101 = next(r for r in result if r["id"] == "05101")
    assert r13102["regional_rank"] == 1
    assert r13101["regional_rank"] == 2
    # Region 05 has only one eligible commune → rank 1
    assert r05101["regional_rank"] == 1


def test_compute_ranks_empty_series_excluded():
    from pipeline.cead.normalizer import compute_ranks
    records = [
        {"id": "13101", "region_id": "13", "low_population": False,
         "national_rank": None, "regional_rank": None, "series": []},
        _make_record("13102", "13", 200.0),
    ]
    result = compute_ranks(records, 2022)
    no_series = next(r for r in result if r["id"] == "13101")
    # No series → excluded from ranks → ranks remain None
    assert no_series["national_rank"] is None


# ---------------------------------------------------------------------------
# compute_level
# ---------------------------------------------------------------------------

def test_compute_level_min_returns_1():
    from pipeline.cead.normalizer import compute_level
    all_rates = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    assert compute_level(10.0, all_rates) == 1


def test_compute_level_max_returns_5():
    from pipeline.cead.normalizer import compute_level
    all_rates = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    assert compute_level(100.0, all_rates) == 5


def test_compute_level_returns_int_in_range():
    from pipeline.cead.normalizer import compute_level
    all_rates = list(range(1, 101))  # 1..100
    for rate in [1.0, 25.0, 50.0, 75.0, 100.0]:
        level = compute_level(rate, all_rates)
        assert isinstance(level, int)
        assert 1 <= level <= 5


def test_compute_level_midrange():
    from pipeline.cead.normalizer import compute_level
    # 10 equal buckets; rate at midpoint should be level 3
    all_rates = [float(i) for i in range(1, 101)]
    level = compute_level(50.0, all_rates)
    assert 2 <= level <= 4  # middle quintile


# ---------------------------------------------------------------------------
# FEATURED_FAMILIES constant
# ---------------------------------------------------------------------------

def test_featured_families_contains_expected_keys():
    from pipeline.cead.normalizer import FEATURED_FAMILIES
    assert "propiedad" in FEATURED_FAMILIES
    assert "vida" in FEATURED_FAMILIES


def test_featured_subgroups_has_homicidios():
    from pipeline.cead.normalizer import FEATURED_SUBGROUPS
    assert "homicidios" in FEATURED_SUBGROUPS
    # Homicidios subgroup ID should be 101
    assert FEATURED_SUBGROUPS["homicidios"] == 101


def test_featured_subgroups_has_secuestros():
    from pipeline.cead.normalizer import FEATURED_SUBGROUPS
    # Secuestros key must exist (even if ID is None/pending confirmation)
    assert "secuestros" in FEATURED_SUBGROUPS


# ---------------------------------------------------------------------------
# attach_featured
# ---------------------------------------------------------------------------

def test_attach_featured_returns_dict_with_expected_keys():
    from pipeline.cead.normalizer import attach_featured
    # Minimal commune data: one year with property and homicides data
    commune_data = {
        "propiedad_by_year": {2022: 500.0},
        "vida_by_year": {2022: 10.0},
        "homicidios_by_year": {2022: 3.0},
        "secuestros_by_year": {},
    }
    result = attach_featured(commune_data)
    assert isinstance(result, dict)
    assert "propiedad" in result
    assert "homicidios" in result
    assert "secuestros" in result
