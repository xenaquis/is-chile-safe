"""
pipeline/news/fidelity.py

Deterministic headline fidelity guards (FID-01 / FID-07, G-28, G-29). Stdlib only.

- guard_title_en(title_src, title_en, outlet) -> (title_en_to_store, fell_back)
    The LLM's English headline is stored only if it passes a kinship check against
    the outlet's verbatim headline (title_src). Otherwise title_src itself is stored
    (shown in EN as "Original Spanish headline (not translated)", G-36).
    Defect class: V-06 (yerno -> "Grandfather"), G-27 (madre -> "grandmother").

- kinship_mismatch(src, en) -> bool
    After masking commune names (Padre Las Casas, Padre Hurtado, ...) on both sides:
      (a) an ES kinship concept present in src has none of its EN renderings in en, or
      (b) an EN kinship rendering present in en maps to no concept present in src
          (kinship, or the non-kinship child words niño/menor/bebé/guagua for the
          child-like renderings only).
    Matching is accent- and case-insensitive (NFD strip + lowercase) and
    word-bounded with the same lookaround as forbidden-language.mjs; longer forms
    are matched first and consumed ("son-in-law" never also counts as "son").

- forbidden_term(text) -> str | None
    Editorial filter (G-29). FORBIDDEN_TERMS is a MIRROR of
    site/scripts/validate/forbidden-language.mjs (FORBIDDEN_TERMS array), kept in
    sync by pipeline/tests/test_fidelity.py (which also pins the copy in
    CommuneNewsSection.astro). The validator's allow-list is deliberately NOT
    applied: headlines we publish must be stricter than qualified site copy.
"""
from __future__ import annotations

import functools
import json
import logging
import pathlib
import re
import unicodedata

logger = logging.getLogger(__name__)

_INDEX_FILE = pathlib.Path(__file__).parents[2] / "data" / "cead" / "meta" / "index.json"

# Mirror of site/scripts/validate/forbidden-language.mjs FORBIDDEN_TERMS (pinned by test).
FORBIDDEN_TERMS: tuple[str, ...] = (
    # Spanish
    "zona peligrosa",
    "area peligrosa",
    "comuna peligrosa",
    "barrio peligroso",
    "ranking definitivo",
    "zona segura garantizada",
    "zona segura",
    "100% seguro",
    "seguridad garantizada",
    "la mas segura",
    "mas peligrosa",
    "mas peligroso",
    "el mas seguro",
    # English
    "dangerous zone",
    "dangerous area",
    "dangerous commune",
    "dangerous neighborhood",
    "definitive ranking",
    "guaranteed safe",
    "100% safe",
    "guaranteed safety",
    "the safest",
    "most dangerous",
)

# ES kinship concept -> (ES surface forms, accepted EN renderings). Gendered pairs
# share one concept: the guard targets relationship-class errors (son-in-law vs
# grandfather), not gender agreement.
KINSHIP: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "yerno": (("yerno", "yernos"),
              ("son-in-law", "sons-in-law", "in-law", "in-laws")),
    "nuera": (("nuera", "nueras"),
              ("daughter-in-law", "daughters-in-law", "in-law", "in-laws")),
    "suegro": (("suegro", "suegra", "suegros", "suegras"),
               ("father-in-law", "mother-in-law", "fathers-in-law", "mothers-in-law",
                "parents-in-law", "in-law", "in-laws")),
    "cunado": (("cunado", "cunada", "cunados", "cunadas"),
               ("brother-in-law", "sister-in-law", "brothers-in-law", "sisters-in-law",
                "in-law", "in-laws")),
    "abuelo": (("abuelo", "abuela", "abuelos", "abuelas", "abuelito", "abuelita",
                "abuelitos", "abuelitas"),
               ("grandfather", "grandmother", "grandfathers", "grandmothers",
                "grandparent", "grandparents", "grandpa", "grandma", "granny")),
    "nieto": (("nieto", "nieta", "nietos", "nietas"),
              ("grandson", "granddaughter", "grandsons", "granddaughters",
               "grandchild", "grandchildren")),
    "padre": (("padre", "papa"),
              ("father", "fathers", "dad", "dads")),
    "madre": (("madre", "mama"),
              ("mother", "mothers", "mom", "moms", "mum", "mums")),
    "padres": (("padres",),
               ("parents", "parent", "fathers", "father")),
    "hijo": (("hijo", "hija", "hijos", "hijas"),
             ("son", "sons", "daughter", "daughters", "child", "children")),
    "hermano": (("hermano", "hermana", "hermanos", "hermanas"),
                ("brother", "brothers", "sister", "sisters", "sibling", "siblings")),
    "tio": (("tio", "tia", "tios", "tias"),
            ("uncle", "uncles", "aunt", "aunts")),
    "primo": (("primo", "prima", "primos", "primas"),
              ("cousin", "cousins")),
    "sobrino": (("sobrino", "sobrina", "sobrinos", "sobrinas"),
                ("nephew", "nephews", "niece", "nieces")),
    "esposo": (("esposo", "esposa", "esposos", "esposas", "marido", "maridos"),
               ("husband", "husbands", "wife", "wives", "spouse", "spouses")),
    "hijastro": (("hijastro", "hijastra", "hijastros", "hijastras"),
                 ("stepson", "stepdaughter", "stepsons", "stepdaughters",
                  "stepchild", "stepchildren")),
    "padrastro": (("padrastro", "padrastros"),
                  ("stepfather", "stepfathers", "stepdad")),
    "madrastra": (("madrastra", "madrastras"),
                  ("stepmother", "stepmothers", "stepmom")),
    "pareja": (("pareja", "parejas"),
               ("couple", "couples", "partner", "partners", "boyfriend", "girlfriend",
                "wife", "husband", "spouse")),
    "expareja": (("expareja", "ex pareja", "exparejas", "ex parejas", "exesposo",
                  "exesposa", "ex esposo", "ex esposa", "exconviviente",
                  "ex conviviente", "expololo", "expolola", "ex pololo", "ex polola"),
                 ("partner", "ex-partner", "former partner", "boyfriend", "girlfriend",
                  "ex-boyfriend", "ex-girlfriend", "ex-wife", "ex-husband",
                  "former wife", "former husband", "former boyfriend",
                  "former girlfriend")),
    "conviviente": (("conviviente", "convivientes"),
                    ("partner", "partners", "live-in partner", "cohabitant",
                     "boyfriend", "girlfriend", "wife", "husband")),
    "pololo": (("pololo", "polola", "pololos", "pololas", "novio", "novia"),
               ("boyfriend", "girlfriend", "partner", "fiance", "fiancee")),
    "matrimonio": (("matrimonio", "matrimonios"),
                   ("couple", "couples", "married couple", "spouses", "husband", "wife")),
}

# Non-kinship ES child words (premortem R-13): they satisfy the child-like EN
# renderings for rule (b) only; they never trigger rule (a).
NON_KIN_CHILD_ES: tuple[str, ...] = (
    "nino", "nina", "ninos", "ninas", "menor", "menores", "bebe", "bebes",
    "guagua", "guaguas", "infantil", "infantiles",
)
NON_KIN_CHILD_EN: frozenset[str] = frozenset({
    "child", "children", "minor", "minors", "baby", "babies", "kid", "kids",
})

_MASK = " \x00 "


def _norm(text: str) -> str:
    """NFD accent strip + lowercase (mirrors forbidden-language.mjs:80-82)."""
    return "".join(
        c for c in unicodedata.normalize("NFD", (text or "").lower())
        if unicodedata.category(c) != "Mn"
    )


def _bounded(alternatives: list[str]) -> re.Pattern:
    """Word-bounded alternation, longest first (JS lookaround, not \\b)."""
    alts = sorted(set(alternatives), key=lambda s: (-len(s), s))
    body = "|".join(re.escape(a) for a in alts)
    return re.compile(rf"(?<![a-z0-9])(?:{body})(?![a-z0-9])")


def _build_tables():
    es_to_concept: dict[str, str] = {}
    en_to_concepts: dict[str, set[str]] = {}
    for concept, (es_forms, en_forms) in KINSHIP.items():
        for f in es_forms:
            es_to_concept[_norm(f)] = concept
        for f in en_forms:
            en_to_concepts.setdefault(_norm(f), set()).add(concept)
    es_re = _bounded(list(es_to_concept) + [_norm(w) for w in NON_KIN_CHILD_ES])
    en_re = _bounded(list(en_to_concepts))
    return es_to_concept, en_to_concepts, es_re, en_re


_ES_TO_CONCEPT, _EN_TO_CONCEPTS, _ES_RE, _EN_RE = _build_tables()
_NON_KIN_ES = frozenset(_norm(w) for w in NON_KIN_CHILD_ES)


@functools.lru_cache(maxsize=1)
def _commune_names() -> tuple[str, ...]:
    """Normalized commune names from data/cead/meta/index.json (longest first)."""
    try:
        index = json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - resolver.py fails loudly on this too
        logger.warning("fidelity: commune index unavailable (%s) — masking disabled", exc)
        return ()
    names = {_norm(row.get("name") or "").strip() for row in index}
    names.discard("")
    return tuple(sorted(names, key=lambda s: (-len(s), s)))


@functools.lru_cache(maxsize=1)
def _commune_re() -> re.Pattern | None:
    names = _commune_names()
    return _bounded(list(names)) if names else None


def _mask_communes(text_norm: str) -> str:
    pattern = _commune_re()
    return pattern.sub(_MASK, text_norm) if pattern is not None else text_norm


def _es_concepts(src: str) -> tuple[set[str], bool]:
    """(kinship concepts present, any non-kinship child word present)."""
    concepts: set[str] = set()
    non_kin = False
    for m in _ES_RE.finditer(_mask_communes(_norm(src))):
        word = m.group(0)
        if word in _NON_KIN_ES:
            non_kin = True
        else:
            concepts.add(_ES_TO_CONCEPT[word])
    return concepts, non_kin


def _en_renderings(en: str) -> list[str]:
    return [m.group(0) for m in _EN_RE.finditer(_mask_communes(_norm(en)))]


def kinship_mismatch(src: str, en: str) -> bool:
    """True iff the EN headline's kinship terms disagree with the ES source headline."""
    src_concepts, src_non_kin = _es_concepts(src)
    renderings = _en_renderings(en)
    covered: set[str] = set()
    for r in renderings:
        concepts = _EN_TO_CONCEPTS[r]
        covered |= concepts
        # rule (b): EN kinship with no source concept behind it
        if not (concepts & src_concepts) and not (src_non_kin and r in NON_KIN_CHILD_EN):
            return True
    # rule (a): ES kinship concept with no EN rendering
    return bool(src_concepts - covered)


def _strip_outlet_suffix(text: str, outlet: str) -> str:
    outlet = (outlet or "").strip()
    if outlet:
        suffix = f" - {outlet}"
        if text.endswith(suffix):
            return text[: -len(suffix)].strip()
        if text == suffix.strip():
            return ""
    return text


def guard_title_en(title_src: str, title_en: str | None, outlet: str) -> tuple[str, bool]:
    """Return (title_en to store, fell_back). Falls back to title_src on empty/mismatch."""
    en = " ".join((title_en or "").split())
    en = _strip_outlet_suffix(en, outlet)
    if not en or kinship_mismatch(title_src, en):
        return title_src, True
    return en, False


_TERM_PATTERNS = tuple(
    (term, re.compile(rf"(?<![a-z0-9]){re.escape(_norm(term))}(?![a-z0-9])"))
    for term in FORBIDDEN_TERMS
)


def forbidden_term(text: str | None) -> str | None:
    """First FORBIDDEN_TERMS entry found in text (JS-equivalent matching), else None."""
    if not text:
        return None
    norm = _norm(text)
    for term, pattern in _TERM_PATTERNS:
        if pattern.search(norm):
            return term
    return None
