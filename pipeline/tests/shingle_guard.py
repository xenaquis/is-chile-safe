"""
pipeline/tests/shingle_guard.py

5-word shingle guard shared by 36-02 (golden_set_v3 freeze) and 36-06 (prompt
iteration). Detects when a golden-set item's headline/description shares a
5-word run with the classifier prompt's RULES text — a sign the fixture was
(even accidentally) written to match the prompt rather than a real stored
production input (premortem R-07).

Only the RULES text is compared, not the whole SYSTEM_PROMPT: the JSON schema
block and the 346-commune list are expected to share vocabulary with almost
any Chilean crime-news item, so including them would make the guard useless
(match everything) instead of catching prompt-shaped fixture text.

Stdlib only, no repo imports — this module must stay importable without
pulling in pipeline.news.classifier (which requires data/cead/meta/index.json
to exist) so it can be unit-tested in isolation.
"""
from __future__ import annotations

import re
import unicodedata

# First line-anchored `{` ... `}` block (the JSON schema block in
# classifier.SYSTEM_PROMPT). MULTILINE so ^/$ match line boundaries; DOTALL so
# `.` spans the block's internal newlines.
_SCHEMA_BLOCK_RE = re.compile(r"^\{$.*?^\}$", re.MULTILINE | re.DOTALL)

_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WS_RE = re.compile(r"\s+")


def prompt_rules_text(system_prompt: str, commune_list_str: str) -> str:
    """`system_prompt` with the commune block and the JSON schema block removed.

    `commune_list_str` must be the exact `_COMMUNE_LIST_STR` string so it can be
    removed via a literal substring replace (it contains regex metacharacters —
    parentheses around region_id — so it is never used as a pattern).
    """
    text = system_prompt.replace(commune_list_str, "")
    text = _SCHEMA_BLOCK_RE.sub("", text)
    return text


def normalize(text: str) -> str:
    """NFD accent-strip, lowercase, punctuation -> space, whitespace collapsed."""
    if text is None:
        return ""
    nfd = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    lowered = stripped.lower()
    no_punct = _PUNCT_RE.sub(" ", lowered)
    return _WS_RE.sub(" ", no_punct).strip()


def _shingles(normalized_text: str, n: int) -> set[str]:
    words = normalized_text.split(" ") if normalized_text else []
    words = [w for w in words if w]
    if len(words) < n:
        return set()
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}


def shared_shingles(text: str, rules_text: str, n: int = 5) -> set[str]:
    """Normalized n-word shingles of `text` that also occur in `rules_text`."""
    text_shingles = _shingles(normalize(text), n)
    if not text_shingles:
        return set()
    rules_shingles = _shingles(normalize(rules_text), n)
    return text_shingles & rules_shingles
