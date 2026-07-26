"""
pipeline/tests/test_gnews_decoder.py

Tests for pipeline/news/gnews_decoder.decode_gnews_url and
pipeline/news/fulltext.is_safe_url + security guards in fetch_article.

Strategy:
- NEVER hit live network — session.get/post mocked with MagicMock
- Build old-format token synthetically from a known URL
- No hardcoded calendar dates
"""
from __future__ import annotations

import base64
import json
import re
from unittest.mock import MagicMock, patch

import pytest

import pipeline.news.gnews_decoder as gnd
import pipeline.news.fulltext as ft


@pytest.fixture(autouse=True)
def _stub_dns(monkeypatch):
    """Default every test to a public-IP DNS resolution so is_safe_url's
    getaddrinfo never touches the live network. Tests that need a private
    resolution override this with their own monkeypatch."""
    monkeypatch.setattr(
        ft.socket, "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 0))],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_old_format_token(outlet_url: str) -> str:
    """
    Synthesise a base64url token that the old-format decoder can invert.
    The blob is: b'\\x08\\x13\\x22' + outlet_url.encode() + b'\\x00'
    (mimics the real Google blob structure; the decoder just regexes for https?://)
    """
    blob = b"\x08\x13\x22" + outlet_url.encode("utf-8") + b"\x00"
    token = base64.urlsafe_b64encode(blob).rstrip(b"=").decode("ascii")
    return token


def _make_gnews_url(token: str) -> str:
    return f"https://news.google.com/rss/articles/{token}"


# ---------------------------------------------------------------------------
# 1. Non-gnews URL passes through unchanged, no network call
# ---------------------------------------------------------------------------

def test_non_gnews_url_passthrough():
    url = "https://biobiochile.cl/nota/2026/01/test"
    session = MagicMock()
    result = gnd.decode_gnews_url(url, session=session)
    assert result == url
    session.get.assert_not_called()
    session.post.assert_not_called()


# ---------------------------------------------------------------------------
# 2. Old-format: decode known token without any network call
# ---------------------------------------------------------------------------

def test_old_format_decode_no_network():
    outlet_url = "https://emol.com/noticias/2026/nota-especial"
    token = _make_old_format_token(outlet_url)
    gnews_url = _make_gnews_url(token)

    session = MagicMock()
    result = gnd.decode_gnews_url(gnews_url, session=session)

    assert result == outlet_url, f"Expected {outlet_url!r}, got {result!r}"
    # Old-format must succeed without any network call
    session.get.assert_not_called()
    session.post.assert_not_called()


# ---------------------------------------------------------------------------
# 3. Garbage token falls through to new-format (or None if no session)
# ---------------------------------------------------------------------------

def test_garbage_token_returns_none_without_session():
    gnews_url = "https://news.google.com/rss/articles/ZZZZINVALIDZZZZ"
    result = gnd.decode_gnews_url(gnews_url, session=None)
    # Old-format fails (garbage), no session → None
    assert result is None


def test_garbage_token_newformat_unparseable_returns_none():
    """New-format mock returns unparseable body → returns None, never raises."""
    gnews_url = "https://news.google.com/rss/articles/ZZZZINVALIDZZZZ"

    session = MagicMock()
    # Old-format will fail (garbage); new-format GET returns page without data-n-a-sg
    mock_get_resp = MagicMock()
    mock_get_resp.text = "<html><body>No useful data here</body></html>"
    session.get.return_value = mock_get_resp

    result = gnd.decode_gnews_url(gnews_url, session=session)
    assert result is None


# ---------------------------------------------------------------------------
# 4. New-format batchexecute path (fully mocked)
# ---------------------------------------------------------------------------

def test_new_format_batchexecute_mock():
    """
    Full new-format path: GET returns a page with data-n-a-sg/ts, POST returns
    a canned batchexecute body with the decoded outlet URL.
    """
    outlet_url = "https://t13.cl/noticia/2026/07/crime-test"
    # Build a gnews URL where old-format decode fails (no valid base64 blob)
    gnews_url = "https://news.google.com/rss/articles/NEWFORMAT_ARTICLE_ID_XYZ"

    session = MagicMock()

    # GET page has the required data attributes
    mock_page = MagicMock()
    mock_page.text = (
        '<html><body>'
        ' <div data-n-a-sg="fake_sg_value" data-n-a-ts="fake_ts_value"></div>'
        '</body></html>'
    )
    session.get.return_value = mock_page

    # POST returns a batchexecute response body containing the outlet URL
    # Strip )]}' prefix is handled; we embed URL in a JSON-ish string
    canned_body = ")]}'\n" + json.dumps([[[outlet_url, "extra", "data"]]])
    mock_post_resp = MagicMock()
    mock_post_resp.text = canned_body
    session.post.return_value = mock_post_resp

    result = gnd.decode_gnews_url(gnews_url, session=session)

    assert result == outlet_url, f"Expected {outlet_url!r}, got {result!r}"
    session.get.assert_called_once()
    session.post.assert_called_once()

    # POST must go to hardcoded host — never news.google.com input (T-gf7-04)
    post_url = session.post.call_args[0][0]
    assert "news.google.com/_/DotsSplashUi/data/batchexecute" in post_url


# ---------------------------------------------------------------------------
# 5. Any exception in new-format → None, never raises
# ---------------------------------------------------------------------------

def test_new_format_exception_returns_none():
    gnews_url = "https://news.google.com/rss/articles/SOME_TOKEN"

    session = MagicMock()
    # GET raises an exception
    session.get.side_effect = RuntimeError("network down")

    result = gnd.decode_gnews_url(gnews_url, session=session)
    assert result is None


# ---------------------------------------------------------------------------
# 6. is_safe_url: allowed URLs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url", [
    "https://outlet.cl/x",
    "http://outlet.cl/x",
    "https://news.google.com/rss/articles/abc",
    "http://example.com/path?q=1",
])
def test_is_safe_url_allowed(url):
    # resolve_dns=False → pure syntactic check, hermetic (no live DNS)
    assert ft.is_safe_url(url, resolve_dns=False) is True


# ---------------------------------------------------------------------------
# 7. is_safe_url: rejected URLs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url", [
    "ftp://x.cl/file",
    "file:///etc/passwd",
    "javascript:alert(1)",
    "http://127.0.0.1/x",
    "http://10.0.0.5/x",
    "http://169.254.1.1/x",
    "http://user:pass@host.cl/x",
    "http://::1/x",  # IPv6 loopback
    "http://192.168.1.1/x",  # private
])
def test_is_safe_url_rejected(url):
    assert ft.is_safe_url(url, resolve_dns=False) is False


# ---------------------------------------------------------------------------
# 6b. is_safe_url: DNS-based SSRF (CR-02) — attacker A-record → private IP
# ---------------------------------------------------------------------------

def test_is_safe_url_dns_rebinding_rejected(monkeypatch):
    """A public hostname that resolves to a private IP must be rejected."""
    monkeypatch.setattr(
        ft.socket, "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("127.0.0.1", 0))],
    )
    assert ft.is_safe_url("https://evil.example.com/x") is False


def test_is_safe_url_dns_public_allowed(monkeypatch):
    monkeypatch.setattr(
        ft.socket, "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 0))],
    )
    assert ft.is_safe_url("https://outlet.cl/x") is True


def test_is_safe_url_dns_failure_rejected(monkeypatch):
    """Unresolvable host → unsafe (fail closed)."""
    def _boom(*a, **k):
        raise OSError("NXDOMAIN")
    monkeypatch.setattr(ft.socket, "getaddrinfo", _boom)
    assert ft.is_safe_url("https://nope.invalid/x") is False


def test_fetch_article_redirect_to_private_ip_blocked(monkeypatch):
    """CR-01: a public URL that 302-redirects to a private IP must not be fetched."""
    redirect = MagicMock()
    redirect.status_code = 302
    redirect.headers = {"Location": "http://169.254.169.254/latest/meta-data/"}
    redirect.close = MagicMock()

    sess = MagicMock()
    sess.get.return_value = redirect
    sess.RequestException = Exception
    # First hop host resolves public; is_safe_url on the redirect target sees a
    # literal link-local IP and rejects without DNS.
    monkeypatch.setattr(ft.socket, "getaddrinfo",
                        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 0))])

    result = ft.fetch_article("https://outlet.cl/nota", session=sess)
    assert result["extraction_ok"] is False
    assert "169.254.169.254" in result["final_url"]


# ---------------------------------------------------------------------------
# 8. fetch_article: gnews decode → None → extraction_ok=False, no raise
# ---------------------------------------------------------------------------

def test_fetch_article_gnews_decode_none_returns_failure():
    """When decode_gnews_url returns None for a gnews URL, fetch_article returns failure."""
    gnews_url = "https://news.google.com/rss/articles/UNDECODABLE"

    with patch.object(gnd, "_try_old_format", return_value=None), \
         patch.object(gnd, "_try_new_format", return_value=None):
        result = ft.fetch_article(gnews_url)

    assert result["extraction_ok"] is False
    assert result["http_status"] is None


# ---------------------------------------------------------------------------
# 9. fetch_article: unsafe URL rejected before fetch
# ---------------------------------------------------------------------------

def test_fetch_article_unsafe_url_rejected():
    with patch.object(ft, "requests") as mock_req:
        result = ft.fetch_article("ftp://evil.cl/payload")

    assert result["extraction_ok"] is False
    assert result["http_status"] is None
    # requests.get must never be called for unsafe URLs
    mock_req.get.assert_not_called()


# ---------------------------------------------------------------------------
# 10. fetch_article: streamed body > 5 MB → extraction_ok=False
# ---------------------------------------------------------------------------

def test_fetch_article_5mb_cap():
    """A mocked response that exceeds 5 MB in iter_content → extraction_ok=False."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://outlet.cl/big-article"
    mock_resp.headers = {"Content-Type": "text/html"}
    # Each chunk is 1 MB; 6 chunks = 6 MB > 5 MB cap
    chunk_1mb = b"x" * (1024 * 1024)
    mock_resp.iter_content.return_value = iter([chunk_1mb] * 6)

    with patch.object(ft, "requests") as mock_req, \
         patch.object(ft, "trafilatura"):
        mock_req.get.return_value = mock_resp
        mock_req.RequestException = Exception

        result = ft.fetch_article("https://outlet.cl/big-article")

    assert result["extraction_ok"] is False
    assert result["text"] == ""


# ---------------------------------------------------------------------------
# 11. fetch_article: non-text Content-Type → extraction_ok=False
# ---------------------------------------------------------------------------

def test_fetch_article_bad_content_type():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://outlet.cl/file.pdf"
    mock_resp.headers = {"Content-Type": "application/pdf"}
    mock_resp.iter_content.return_value = iter([b"PDF content"])

    with patch.object(ft, "requests") as mock_req, \
         patch.object(ft, "trafilatura"):
        mock_req.get.return_value = mock_resp
        mock_req.RequestException = Exception

        result = ft.fetch_article("https://outlet.cl/file.pdf")

    assert result["extraction_ok"] is False
    assert result["text"] == ""


# ---------------------------------------------------------------------------
# 12. fetch_article: decoded_from_gnews flag in result
# ---------------------------------------------------------------------------

def test_fetch_article_decoded_from_gnews_flag():
    """When a gnews URL decodes successfully, decoded_from_gnews=True in result."""
    outlet_url = "https://emol.com/nota-decoded"
    token = _make_old_format_token(outlet_url)
    gnews_url = _make_gnews_url(token)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = outlet_url
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.iter_content.return_value = iter([b"<html>article content</html>"])
    mock_resp.encoding = "utf-8"

    with patch.object(ft, "requests") as mock_req, \
         patch.object(ft, "trafilatura") as mock_traf:
        mock_req.get.return_value = mock_resp
        mock_req.RequestException = Exception
        mock_traf.extract.return_value = "article content"

        result = ft.fetch_article(gnews_url)

    assert result["decoded_from_gnews"] is True
    assert result["extraction_ok"] is True


# ---------------------------------------------------------------------------
# 13. fetch_article: non-gnews URL has decoded_from_gnews=False
# ---------------------------------------------------------------------------

def test_fetch_article_non_gnews_flag_false():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://outlet.cl/nota"
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.iter_content.return_value = iter([b"<html>content</html>"])
    mock_resp.encoding = "utf-8"

    with patch.object(ft, "requests") as mock_req, \
         patch.object(ft, "trafilatura") as mock_traf:
        mock_req.get.return_value = mock_resp
        mock_req.RequestException = Exception
        mock_traf.extract.return_value = "content"

        result = ft.fetch_article("https://outlet.cl/nota")

    assert result["decoded_from_gnews"] is False
