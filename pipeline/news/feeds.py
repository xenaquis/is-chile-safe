"""
pipeline/news/feeds.py

RSS feed fetch + per-feed graceful fallback + keyword pre-filter + seen-ledger (NEWS-01, D-02, D-03, D-04).
"""
from __future__ import annotations

import datetime
import json
import logging
import pathlib
import re
import urllib.parse
from typing import Any

import feedparser  # type: ignore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Google News URL builder
# ---------------------------------------------------------------------------

def google_news_url(query: str) -> str:
    """Build a Google News RSS search URL for the given query string.

    Uses percent-encoding so reserved chars (spaces, colons, parentheses) are
    correctly encoded by urllib.parse.quote.
    """
    q = urllib.parse.quote(query, safe="")
    return f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=CL&ceid=CL:es-419"


# ---------------------------------------------------------------------------
# Google News query registry (name -> query string)
# ---------------------------------------------------------------------------

_GOOGLE_NEWS_QUERIES: dict[str, str] = {
    "GoogleNews-Nacional": (
        'homicidio OR balacera OR portonazo OR "crimen organizado" chile when:2d'
    ),
    "GoogleNews-Antofagasta": (
        "(homicidio OR balacera OR robo OR portonazo) "
        "(Antofagasta OR Calama OR Tocopilla) when:3d"
    ),
    "GoogleNews-Tarapaca": (
        "(homicidio OR balacera OR robo) "
        "(Iquique OR \"Alto Hospicio\" OR Tarapaca) when:3d"
    ),
    "GoogleNews-Coquimbo": (
        "(homicidio OR balacera OR robo) "
        '("La Serena" OR Coquimbo OR Ovalle) when:3d'
    ),
    "GoogleNews-Araucania": (
        "(homicidio OR balacera OR robo OR atentado) "
        "(Temuco OR Araucania OR Angol) when:3d"
    ),
}

# ---------------------------------------------------------------------------
# Feed registry
# ---------------------------------------------------------------------------

FEEDS: dict[str, str] = {
    "BioBioChile": "https://www.biobiochile.cl/static/feed-rss",
    "Cooperativa": "https://www.cooperativa.cl/noticias/site/tax/port/all/rss_3_158__1.xml",
    "LaTercera": "https://www.latercera.com/arc/outboundfeeds/rss/?outputType=xml",
    "LaCuarta": "https://www.lacuarta.com/arc/outboundfeeds/rss/?outputType=xml",
    **{name: google_news_url(q) for name, q in _GOOGLE_NEWS_QUERIES.items()},
}

# Identifies the bot + project URL for politeness (D-04, CLAUDE.md)
USER_AGENT = "IsChileSafe-news-pipeline/1.0 (+https://ischilesafe.com)"

# ---------------------------------------------------------------------------
# Seen-ledger path (committed, survives CI runs — Pitfall 7)
# ---------------------------------------------------------------------------

_SEEN_PATH: pathlib.Path = (
    pathlib.Path(__file__).parents[2] / "data" / "incidents" / "seen.json"
)

# ---------------------------------------------------------------------------
# Keyword pre-filter (D-02) — any hit → send to classifier
# ---------------------------------------------------------------------------

CRIME_KEYWORDS: frozenset[str] = frozenset(
    {
        # Violent crime
        "homicidio", "asesinato", "femicidio", "balacera", "tiroteo", "disparo",
        "herido a bala", "matar", "muerto", "fallecido",
        # Property crime
        "robo", "asalto", "hurto", "portonazo", "encerronas", "carjacking",
        "receptacion", "receptación",
        # Drugs / weapons
        "narco", "droga", "cocaine", "cocaina", "cocaína", "marihuana", "fentanilo",
        "armas", "tráfico", "trafico",
        # Crime / law-enforcement terms
        "delito", "delincuente", "imputado", "detenido", "detenidos",
        "carabinero", "pdi", "investigaciones", "fiscalia", "fiscalía",
        "formalizacion", "formalización", "condena", "prisión", "prision",
        # Organised crime
        "tren de aragua", "pandilla", "banda criminal",
        "crimen organizado",
        # Generic crime
        "victima", "víctima", "agresor", "encubrimiento",
        "narcotráfico", "narcotrafico",
    }
)


# ---------------------------------------------------------------------------
# HTML stripping (Pitfall 8 — BioBio description contains HTML tags)
# ---------------------------------------------------------------------------

def strip_html(text: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", text or "")


# ---------------------------------------------------------------------------
# Canonical URL resolution (Pitfall 2)
# ---------------------------------------------------------------------------

def canonical_url(entry: Any, feed_name: str) -> str:
    """Return the canonical article URL for the given feed.

    BioBioChile's <guid> is a WordPress ?p= ID — use <link> instead.
    Google News item links are redirect URLs that land on the source article.
    Cooperativa, LaTercera, LaCuarta: <guid> IS the canonical permalink.
    """
    if feed_name == "BioBioChile":
        return getattr(entry, "link", "") or ""
    if feed_name.startswith("GoogleNews"):
        return getattr(entry, "link", "") or ""
    # Default: use entry.id (guid field)
    return getattr(entry, "id", "") or getattr(entry, "link", "") or ""


def resolve_outlet(entry: Any, feed_name: str) -> str:
    """Return the outlet name for an incident.

    For non-Google feeds, return the feed name unchanged.
    For Google News feeds, extract the outlet from the item's <source> tag,
    falling back to the constant "Google News" if absent or empty.
    """
    if not feed_name.startswith("GoogleNews"):
        return feed_name
    src = getattr(entry, "source", None)
    if src is None:
        return "Google News"
    # feedparser maps <source> to a FeedParserDict or dict-like object
    if isinstance(src, dict):
        title = src.get("title", "")
    else:
        title = getattr(src, "title", "")
    title = (title or "").strip()
    return title if title else "Google News"


# ---------------------------------------------------------------------------
# Feed fetch (D-04 — per-feed fallback; one feed never blocks others)
# ---------------------------------------------------------------------------

def fetch_feed(name: str, url: str) -> list[Any]:
    """Fetch and parse one RSS feed.

    Returns a list of feedparser entry objects on success.
    Returns [] on any error — does NOT raise (NEWS-01, D-04).
    """
    try:
        d = feedparser.parse(
            url,
            agent=USER_AGENT,
            request_headers={"Accept": "application/rss+xml, application/xml, text/xml"},
        )
        if d.bozo:
            logger.warning("[%s] Feed parse warning: %s", name, d.bozo_exception)
        return list(d.entries)
    except Exception as exc:
        logger.warning("[%s] Feed fetch failed: %s", name, exc)
        return []


# ---------------------------------------------------------------------------
# Keyword pre-filter (D-02)
# ---------------------------------------------------------------------------

def is_crime_item(item: dict[str, str]) -> bool:
    """Return True if (title + description) contains at least one crime keyword.

    item must have 'title' and optionally 'description' keys (plain text or HTML).
    """
    title = item.get("title", "") or ""
    description = strip_html(item.get("description", "") or "")
    combined = (title + " " + description).lower()
    return any(kw in combined for kw in CRIME_KEYWORDS)


# ---------------------------------------------------------------------------
# Publication date parsing (Pitfall 5)
# ---------------------------------------------------------------------------

def parse_pub_date(entry: Any) -> datetime.date:
    """Return the publication date as a UTC date.

    feedparser normalises all timezones to UTC in published_parsed.
    Falls back to today if unparseable.
    """
    pp = getattr(entry, "published_parsed", None)
    if pp:
        try:
            return datetime.datetime(*pp[:6]).date()
        except Exception:
            pass
    return datetime.date.today()


# ---------------------------------------------------------------------------
# Seen-ledger (D-03) — {url: "YYYY-MM-DD"} committed at data/incidents/seen.json
# ---------------------------------------------------------------------------

def load_seen(path: pathlib.Path | None = None) -> dict[str, str]:
    """Load the seen-URL ledger. Returns {} if file absent or malformed."""
    p = path or _SEEN_PATH
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to load seen-ledger at %s: %s", p, exc)
        return {}


def save_seen(
    seen: dict[str, str],
    path: pathlib.Path | None = None,
    prune_days: int = 60,
) -> None:
    """Save the seen-ledger, pruning entries older than prune_days (Pitfall 6).

    Creates parent directories if needed.
    """
    p = path or _SEEN_PATH
    cutoff = datetime.date.today() - datetime.timedelta(days=prune_days)
    pruned = {
        url: date_str
        for url, date_str in seen.items()
        if _parse_date_str(date_str) >= cutoff
    }
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(pruned, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_date_str(date_str: str) -> datetime.date:
    """Parse 'YYYY-MM-DD' or fall back to epoch on error."""
    try:
        return datetime.date.fromisoformat(date_str)
    except Exception:
        return datetime.date(1970, 1, 1)


def filter_seen(entries: list[dict[str, Any]], seen: set[str]) -> list[dict[str, Any]]:
    """Return only entries whose canonical 'link' key is NOT in the seen set."""
    return [e for e in entries if e.get("link", "") not in seen]
