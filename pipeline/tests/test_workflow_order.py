"""
pipeline/tests/test_workflow_order.py

Verifies that .github/workflows/cead-scraper.yml enforces the correct
three-step pipeline order:

  scrape CEAD -> build_composite_index -> build_map_payload -> commit

And that both the composite-index and map-payload steps carry
continue-on-error: true (D-11 graceful degrade).

D-11 semantics: if the composite-index step fails, the workflow must
still reach "Commit data if changed" and commit the refreshed CEAD data
written by the scraper.  continue-on-error on the two new steps is what
makes that hold — it is NOT left to an if: always() on the commit step.
"""
from __future__ import annotations

import pathlib

import pytest

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

WORKFLOW_PATH = (
    pathlib.Path(__file__).parent.parent.parent
    / ".github"
    / "workflows"
    / "cead-scraper.yml"
)


def _load_steps() -> list[dict]:
    """Return the ordered list of steps from the workflow's scrape job."""
    if yaml is None:
        pytest.skip("PyYAML not installed — install to run workflow order tests")
    with open(WORKFLOW_PATH, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data["jobs"]["scrape"]["steps"]


def _step_run(step: dict) -> str:
    return step.get("run", "")


def _find_step_index(steps: list[dict], fragment: str) -> int | None:
    for i, step in enumerate(steps):
        if fragment in _step_run(step):
            return i
    return None


def _find_commit_index(steps: list[dict]) -> int | None:
    """Find the 'Commit data if changed' step by name."""
    for i, step in enumerate(steps):
        name = step.get("name", "")
        if "commit" in name.lower() and "changed" in name.lower():
            return i
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_composite_index_step_exists():
    """A step running build_composite_index.py must be present."""
    steps = _load_steps()
    idx = _find_step_index(steps, "build_composite_index.py")
    assert idx is not None, (
        "No step running build_composite_index.py found in cead-scraper.yml"
    )


def test_map_payload_step_exists():
    """A step running build_map_payload.py must be present."""
    steps = _load_steps()
    idx = _find_step_index(steps, "build_map_payload.py")
    assert idx is not None, (
        "No step running build_map_payload.py found in cead-scraper.yml"
    )


def test_composite_index_before_map_payload():
    """build_composite_index.py step must precede build_map_payload.py step."""
    steps = _load_steps()
    idx_ci = _find_step_index(steps, "build_composite_index.py")
    idx_mp = _find_step_index(steps, "build_map_payload.py")
    assert idx_ci is not None, "build_composite_index.py step not found"
    assert idx_mp is not None, "build_map_payload.py step not found"
    assert idx_ci < idx_mp, (
        f"build_composite_index.py (step {idx_ci}) must come before "
        f"build_map_payload.py (step {idx_mp})"
    )


def test_both_new_steps_before_commit():
    """Both new steps must precede 'Commit data if changed'."""
    steps = _load_steps()
    idx_ci = _find_step_index(steps, "build_composite_index.py")
    idx_mp = _find_step_index(steps, "build_map_payload.py")
    idx_commit = _find_commit_index(steps)
    assert idx_ci is not None, "build_composite_index.py step not found"
    assert idx_mp is not None, "build_map_payload.py step not found"
    assert idx_commit is not None, "'Commit data if changed' step not found"
    assert idx_ci < idx_commit, (
        f"build_composite_index.py (step {idx_ci}) must be before commit (step {idx_commit})"
    )
    assert idx_mp < idx_commit, (
        f"build_map_payload.py (step {idx_mp}) must be before commit (step {idx_commit})"
    )


def test_composite_index_step_continue_on_error():
    """build_composite_index.py step must carry continue-on-error: true (D-11)."""
    steps = _load_steps()
    idx = _find_step_index(steps, "build_composite_index.py")
    assert idx is not None, "build_composite_index.py step not found"
    step = steps[idx]
    assert step.get("continue-on-error") is True, (
        "build_composite_index.py step must have continue-on-error: true "
        "(D-11: index failure must not block the CEAD data commit)"
    )


def test_map_payload_step_continue_on_error():
    """build_map_payload.py step must carry continue-on-error: true (D-11)."""
    steps = _load_steps()
    idx = _find_step_index(steps, "build_map_payload.py")
    assert idx is not None, "build_map_payload.py step not found"
    step = steps[idx]
    assert step.get("continue-on-error") is True, (
        "build_map_payload.py step must have continue-on-error: true "
        "(D-11: payload build failure must not block the CEAD data commit)"
    )
