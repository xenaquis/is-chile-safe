"""
pipeline/tests/test_golden_v3.py

Structure-only tests for pipeline/tests/fixtures/golden_set_v3.json (36-02
Task 2). No data/incidents reads (the fixture is already frozen); importing
pipeline.news.classifier is allowed (it only reads data/cead/meta/index.json).
"""
from __future__ import annotations

import json
import pathlib

from pipeline.news import classifier as classifier_mod
from pipeline.news import feeds as feeds_mod
from pipeline.news.schema import VALID_CUTS
from pipeline.tests import shingle_guard as sg

_FIXTURES = pathlib.Path(__file__).parent / "fixtures"
_V2_PATH = _FIXTURES / "golden_set_v2.json"
_V3_PATH = _FIXTURES / "golden_set_v3.json"

# EFFECTIVE_QUOTAS (G-39 shortfall rule, recorded in 36-GOLDEN-V3.md): the
# suicide cue yielded 0 non-crime candidates in the stored data (at most 2 of
# the 6 suicide-cue rows were non-crime, and 0 were in Chile), so its 3-item
# nominal quota is unmet by construction. The shortfall (3) plus the
# remaining gap to the target-24 total (4 more) were both filled from
# institutional_preventive, which had ample surplus (29 available).
EFFECTIVE_QUOTAS = {
    "accident": 6,
    "suicide": 0,
    "death_no_crime": 3,
    "fire_emergency": 2,
    "institutional_preventive": 13,
}


def _load(path: pathlib.Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_ids_unique():
    v3 = _load(_V3_PATH)
    ids = [it["id"] for it in v3]
    assert len(ids) == len(set(ids))


def test_first_47_equal_golden_v2():
    v2 = _load(_V2_PATH)
    v3 = _load(_V3_PATH)
    assert v3[:47] == v2


def test_not_crime_items_at_least_20_and_pass_is_crime_item():
    v3 = _load(_V3_PATH)
    not_crime = [it for it in v3 if it["ground_truth"].get("not_crime")]
    assert len(not_crime) >= 20
    for it in not_crime:
        assert feeds_mod.is_crime_item({"title": it["headline"], "description": it["description"]})


def test_effective_quotas_met():
    v3 = _load(_V3_PATH)
    not_crime = [it for it in v3 if it["ground_truth"].get("not_crime")]
    counts: dict[str, int] = {}
    for it in not_crime:
        cat = it["ground_truth"].get("category")
        counts[cat] = counts.get(cat, 0) + 1
    for cat, minimum in EFFECTIVE_QUOTAS.items():
        assert counts.get(cat, 0) >= minimum, f"{cat}: {counts.get(cat, 0)} < effective quota {minimum}"
    assert sum(counts.values()) == len(not_crime)


def test_no_v3_item_excluded():
    v3 = _load(_V3_PATH)
    for it in v3:
        assert it.get("exclude") is not True


def test_boundary_items_at_least_8_with_valid_family_and_cut():
    from pipeline.news.schema import VALID_FAMILIES

    v3 = _load(_V3_PATH)
    boundary = [it for it in v3 if it["ground_truth"].get("boundary")]
    assert len(boundary) >= 8
    for it in boundary:
        gt = it["ground_truth"]
        assert gt.get("family") in VALID_FAMILIES
        assert gt.get("cut") in VALID_CUTS


def test_no_html_entity_remnants_in_description():
    v3 = _load(_V3_PATH)
    for it in v3:
        assert "&#" not in it["description"]
        assert "&nbsp;" not in it["description"]


def test_shingle_guard_no_collision_with_prompt_rules_text():
    v3 = _load(_V3_PATH)
    rules_text = sg.prompt_rules_text(classifier_mod.SYSTEM_PROMPT, classifier_mod._COMMUNE_LIST_STR)
    collisions = []
    for it in v3:
        if sg.shared_shingles(it["headline"], rules_text, n=5):
            collisions.append((it["id"], "headline"))
        if sg.shared_shingles(it["description"], rules_text, n=5):
            collisions.append((it["id"], "description"))
    assert collisions == []
