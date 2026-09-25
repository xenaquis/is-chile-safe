"""
pipeline/tests/test_fidelity.py

36-04 Task 1 (FID-01 / FID-07, G-28, G-29, premortem R-13, R-19): deterministic
title_en guard (kinship mismatch) and editorial filter (forbidden terms).
"""
from __future__ import annotations

import pathlib
import re

import pytest

from pipeline.news import fidelity
from pipeline.news.fidelity import (
    FORBIDDEN_TERMS,
    forbidden_term,
    guard_title_en,
    kinship_mismatch,
)

_REPO = pathlib.Path(__file__).resolve().parents[2]
_MJS = _REPO / "site" / "scripts" / "validate" / "forbidden-language.mjs"
_ASTRO = _REPO / "site" / "src" / "components" / "CommuneNewsSection.astro"


# ---------------------------------------------------------------------------
# kinship_mismatch — defect cases (V-06, G-27)
# ---------------------------------------------------------------------------


def test_v06_yerno_rendered_as_grandfather_is_mismatch():
    assert kinship_mismatch(
        "Detienen a yerno de Rosamel Fierro", "Grandfather of Rosamel Fierro arrested"
    ) is True


def test_v06_yerno_rendered_as_son_in_law_is_ok():
    assert kinship_mismatch(
        "Detienen a yerno de Rosamel Fierro", "Son-in-law of Rosamel Fierro arrested"
    ) is False


def test_g27_madre_rendered_as_grandmother_is_mismatch():
    assert kinship_mismatch(
        "Menor mató a su madre con un martillo", "Minor killed her grandmother with a hammer"
    ) is True


def test_g27_madre_rendered_as_mother_is_ok():
    assert kinship_mismatch(
        "Menor mató a su madre con un martillo", "Minor killed her mother with a hammer"
    ) is False


def test_no_kinship_either_side_is_ok():
    assert kinship_mismatch("Detienen a sujeto por robo", "Man arrested for robbery") is False


def test_en_introduces_kinship_absent_in_es_is_mismatch():
    assert kinship_mismatch("Detienen a sujeto por robo", "Father arrested for robbery") is True


# ---------------------------------------------------------------------------
# Matching: accent/case-insensitive, word-bounded, plural/feminine forms
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("src,en", [
    ("Robo en la madrugada en Maipú", "Robbery at dawn in Maipú"),
    ("Actualizan padrón electoral tras fraude", "Electoral roll updated after fraud"),
])
def test_word_boundaries_madrugada_padron(src, en):
    assert kinship_mismatch(src, en) is False


def test_accent_and_case_insensitive():
    assert kinship_mismatch("DETIENEN A SU MAMÁ", "his MOTHER arrested") is False
    assert kinship_mismatch("Detienen a su mama", "His grandmother arrested") is True


@pytest.mark.parametrize("word", [
    "hijos", "hijas", "hermana", "abuelos", "suegra", "nieta", "sobrina", "cuñada",
    "esposa", "nuera", "hijastra", "padrastro", "madrastra", "expareja", "ex pareja",
    "conviviente", "pololo", "polola", "padres", "mamá", "papá", "pareja", "yerno",
])
def test_kinship_forms_are_recognized(word):
    # A recognized ES kinship concept with no EN rendering must fire rule (a).
    assert kinship_mismatch(f"Detienen a {word} de la víctima", "Suspect arrested") is True


# ---------------------------------------------------------------------------
# False-positive guards (premortem R-13) — all False
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("src,en", [
    ("Fiscalía investiga robo en Padre Las Casas", "Prosecutor investigates robbery in Padre Las Casas"),
    ("Balacera en Padre Hurtado deja un herido", "Shooting in Padre Hurtado leaves one injured"),
    ("Niño baleado en Puente Alto", "Child shot in Puente Alto"),
    ("Asaltan a pareja en Maipú", "Couple robbed in Maipú"),
    ("Detienen a hijos de empresario", "Children of businessman arrested"),
    ("Mamá de víctima declara", "Victim's mother testifies"),
])
def test_false_positive_guards(src, en):
    assert kinship_mismatch(src, en) is False


def test_non_kin_child_words_never_trigger_rule_a():
    # niño/menor are not kinship: an EN without 'child' is fine.
    assert kinship_mismatch("Menor detenido por robo", "Teenager arrested for robbery") is False
    assert kinship_mismatch("Bebé rescatado de incendio", "Infant rescued from fire") is False


# ---------------------------------------------------------------------------
# guard_title_en
# ---------------------------------------------------------------------------


def test_guard_strips_outlet_suffix():
    src = "Detienen a sujeto en Calama"
    assert guard_title_en(src, "Man arrested in Calama - La Tercera", "La Tercera") == (
        "Man arrested in Calama", False,
    )


def test_guard_mismatch_falls_back_to_src():
    src = "Detienen a yerno de Rosamel Fierro"
    assert guard_title_en(src, "Grandfather of Rosamel Fierro arrested", "BioBioChile") == (src, True)


@pytest.mark.parametrize("en", ["", "   ", None])
def test_guard_empty_en_falls_back(en):
    src = "Detienen a sujeto en Calama"
    assert guard_title_en(src, en, "La Tercera") == (src, True)


def test_guard_suffix_only_en_falls_back():
    src = "Detienen a sujeto en Calama"
    assert guard_title_en(src, " - La Tercera", "La Tercera") == (src, True)


# ---------------------------------------------------------------------------
# forbidden_term (G-29)
# ---------------------------------------------------------------------------


def test_forbidden_terms_examples():
    assert forbidden_term("La comuna más peligrosa de Chile") == "mas peligrosa"
    assert forbidden_term("Balacera en zona peligrosa") == "zona peligrosa"
    assert forbidden_term("the safest city") == "the safest"
    assert forbidden_term("un sujeto peligroso") is None
    assert forbidden_term("") is None
    assert forbidden_term(None) is None


def test_forbidden_term_is_word_bounded():
    # 'the safest' must not match inside 'breathe safest' style joins
    assert forbidden_term("lathe safestool") is None


# ---------------------------------------------------------------------------
# Pin (G-29, premortem R-19): three copies of the list stay identical
# ---------------------------------------------------------------------------


def _parse_js_terms(path: pathlib.Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"const FORBIDDEN_TERMS\s*=\s*\[(.*?)\];", text, re.DOTALL)
    assert m, f"FORBIDDEN_TERMS array not found in {path}"
    return re.findall(r"'([^']*)'", m.group(1))


def test_forbidden_terms_pinned_to_site_validator():
    js = _parse_js_terms(_MJS)
    assert len(js) == 23
    assert set(FORBIDDEN_TERMS) == set(js)
    assert len(FORBIDDEN_TERMS) == len(js)


def test_commune_news_section_copy_pinned_to_site_validator():
    assert set(_parse_js_terms(_ASTRO)) == set(_parse_js_terms(_MJS))


def test_commune_names_loaded_for_masking():
    names = fidelity._commune_names()
    assert "padre las casas" in names
    assert "padre hurtado" in names
    assert len(names) >= 340
