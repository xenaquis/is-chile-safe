"""
pipeline/tests/test_shingle_guard.py

Offline unit tests for pipeline/tests/shingle_guard.py (36-02 Task 2 step 4,
premortem R-07). No repo imports beyond shingle_guard itself — the
prompt-shaped closure checks against the real classifier.SYSTEM_PROMPT live in
test_golden_v3.py (36-02 Task 2 step 4), which is allowed to import
pipeline.news.classifier.
"""
from __future__ import annotations

from pipeline.tests import shingle_guard as sg


def test_normalize_strips_accents_lowercases_and_collapses_whitespace():
    assert sg.normalize("San Pedro DE LA Paz") == "san pedro de la paz"
    assert sg.normalize("Ñuñoa  tiene   acentos: á é í ó ú") == "nunoa tiene acentos a e i o u"


def test_normalize_empty_and_none_safe():
    assert sg.normalize("") == ""
    assert sg.normalize(None) == ""


def test_prompt_rules_text_removes_commune_block_and_schema_block():
    commune_block = "Las Condes (region_id:13)\nQuilicura (region_id:13)"
    prompt = (
        "Intro text.\n"
        "{\n"
        '  "commune_name": "<value>",\n'
        '  "family": "<value>"\n'
        "}\n"
        "\n"
        f"CHILEAN COMMUNES:\n{commune_block}\n"
        "\n"
        "Rules:\n"
        "- commune_name MUST be exact.\n"
    )
    rules = sg.prompt_rules_text(prompt, commune_block)
    assert commune_block not in rules
    assert '"commune_name": "<value>"' not in rules
    assert "Rules:" in rules
    assert "commune_name MUST be exact" in rules


def test_shared_shingles_detects_5word_overlap():
    rules_text = "commune_name MUST be exactly a commune name from the list"
    # Same 5-word run, different case/accents/punctuation.
    text = "El COMMUNE_NAME must be exactly á commune name aquí."
    shared = sg.shared_shingles(text, rules_text, n=5)
    assert "commune name must be exactly" in shared or "commune must be exactly a" in shared or len(shared) > 0


def test_shared_shingles_empty_when_no_overlap():
    rules_text = "commune_name MUST be exactly a commune name from the list"
    text = "Portonazo en Las Condes deja un herido de gravedad esta tarde"
    assert sg.shared_shingles(text, rules_text, n=5) == set()


def test_shared_shingles_short_text_below_n_words_returns_empty():
    rules_text = "commune_name MUST be exactly a commune name from the list"
    assert sg.shared_shingles("corto texto", rules_text, n=5) == set()


def test_shared_shingles_against_real_classifier_prompt_rules_text():
    """Sanity check against the real prompt (gate closure log, measured
    2026-09-25): rules_text is 1,445 of 10,359 chars and does not contain the
    schema marker or 'san pedro de la paz' (the commune-list collision)."""
    from pipeline.news import classifier as classifier_mod

    rules_text = sg.prompt_rules_text(classifier_mod.SYSTEM_PROMPT, classifier_mod._COMMUNE_LIST_STR)
    assert len(rules_text) < len(classifier_mod.SYSTEM_PROMPT)
    assert '"commune_name": "<' not in rules_text
    assert "san pedro de la paz" not in sg.normalize(rules_text)

    # A real crime headline should not collide with the rules text.
    headline = "Portonazo en Las Condes: delincuentes roban camioneta a punta de pistola"
    assert sg.shared_shingles(headline, rules_text, n=5) == set()
