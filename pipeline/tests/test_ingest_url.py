"""
pipeline/tests/test_ingest_url.py

FID-04 36-07: resolve_publisher_url (Google-News link -> publisher URL) and the
per-run DecodeBudget (G-31 courtesy: 1.5 s between decodes, 60 items, 180 s).
No network: decode_gnews_url is always patched.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipeline.news import ingest_url as iu
from pipeline.news.fulltext import REQUEST_DELAY

G = "https://news.google.com/rss/articles/CBMiXYZ?oc=5"


def _patched(result):
    return patch("pipeline.news.gnews_decoder.decode_gnews_url", return_value=result)


def test_publisher_url_utm_stripped():
    session = object()
    with _patched("https://www.biobiochile.cl/x?utm_source=a") as dec:
        assert iu.resolve_publisher_url(G, session, 10) == "https://www.biobiochile.cl/x"
    dec.assert_called_once_with(G, session=session, timeout=10)


def test_publisher_url_keeps_non_tracking_query():
    with _patched("https://www.t13.cl/n?id=7&utm_medium=rss"):
        assert iu.resolve_publisher_url(G, object(), 10) == "https://www.t13.cl/n?id=7"


@pytest.mark.parametrize("bad", [
    "https://news.google.com/rss/articles/other",
    "https://NEWS.GOOGLE.COM/x",
    "javascript:alert(1)",
    "ftp://example.cl/x",
    "",
    None,
    G,  # decoder hands back the input unchanged
])
def test_unusable_decoder_output_returns_none(bad):
    with _patched(bad):
        assert iu.resolve_publisher_url(G, object(), 10) is None


def test_decoder_exception_returns_none():
    with patch("pipeline.news.gnews_decoder.decode_gnews_url", side_effect=RuntimeError("x")):
        assert iu.resolve_publisher_url(G, object(), 10) is None


def test_default_timeout_is_10s():
    with _patched("https://www.biobiochile.cl/x") as dec:
        iu.resolve_publisher_url(G, object())
    assert dec.call_args.kwargs["timeout"] == 10.0


# ---------------------------------------------------------------------------
# DecodeBudget
# ---------------------------------------------------------------------------

class _Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def test_budget_defaults_match_g31():
    b = iu.DecodeBudget()
    assert (b.max_items, b.max_seconds, b.delay) == (60, 180.0, REQUEST_DELAY)
    assert REQUEST_DELAY == 1.5


def test_budget_item_cap():
    sleep = MagicMock()
    b = iu.DecodeBudget(max_items=60, max_seconds=180, clock=_Clock(), sleep=sleep)
    n = 0
    while b.allow():
        b.wait()
        b.charge()
        n += 1
        assert n <= 60
    assert n == 60 and b.items == 60
    assert b.allow() is False


def test_budget_seconds_cap():
    clock = _Clock()
    b = iu.DecodeBudget(max_items=60, max_seconds=180, clock=clock, sleep=lambda s: None)
    assert b.allow()
    b.wait()
    clock.t += 179.0
    b.charge()
    assert b.allow() is True
    b.wait()
    clock.t += 1.0
    b.charge()
    assert b.spent >= 180.0
    assert b.allow() is False


def test_budget_time_outside_decodes_not_charged():
    clock = _Clock()
    b = iu.DecodeBudget(max_items=60, max_seconds=180, clock=clock, sleep=lambda s: None)
    b.wait()
    clock.t += 1.0
    b.charge()
    clock.t += 500.0  # feed fetches / classification between decodes
    assert b.allow() is True
    assert b.spent == pytest.approx(1.0)


def test_budget_sleeps_between_decodes_never_before_first():
    sleep = MagicMock()
    b = iu.DecodeBudget(clock=_Clock(), sleep=sleep)
    b.wait()
    b.charge()
    assert sleep.call_count == 0
    b.wait()
    b.charge()
    b.wait()
    b.charge()
    assert [c.args[0] for c in sleep.call_args_list] == [REQUEST_DELAY, REQUEST_DELAY]


def test_budget_zero_items_never_allows():
    b = iu.DecodeBudget(max_items=0, clock=_Clock(), sleep=lambda s: None)
    assert b.allow() is False
