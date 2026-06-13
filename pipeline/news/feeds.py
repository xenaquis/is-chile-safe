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
from typing import Any

import feedparser  # type: ignore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feed registry
# ---------------------------------------------------------------------------

FEEDS: dict[str, str] = {
    "BioBioChile": "https://www.biobiochile.cl/static/feed-rss",
    "Cooperativa": "https://www.cooperativa.cl/noticias/site/tax/port/all/rss_3_158__1.xml",
    "LaTercera": "https://www.latercera.com/arc/outboundfeeds/rss/?outputType=xml",
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
    Cooperativa and LaTercera: <guid> IS the canonical permalink.
    """
    if feed_name == "BioBioChile":
        return getattr(entry, "link", "") or ""
    # Default: use entry.id (guid field)
    return getattr(entry, "id", "") or getattr(entry, "link", "") or ""


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
