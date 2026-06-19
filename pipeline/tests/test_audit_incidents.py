"""
pipeline/tests/test_audit_incidents.py

Tests for the GL-03 scored audit mode in pipeline/scripts/audit_incidents.py.

The scored mode flags any incident whose stored ``cut`` is not a valid index CUT
(slug_for_cut returns None) as a resolver failure. Valid CUTs are drawn at test
time from data/cead/meta/index.json so no hardcoded codes can drift. Fixtures use
tmp_path — the live data/incidents/current.json is never read.

Behaviors:
  1. All sampled incidents carry valid index CUTs → accuracy 1.0, exit 0.
  2. Enough incidents carry an out-of-index CUT → accuracy < threshold, exit 2.
  3. Missing current.json → exit 1 (unchanged from TSV mode).
"""
from __future__ import annotations

import json
import pathlib

from pipeline.scripts.audit_incidents import ACCURACY_THRESHOLD, run_scored

_INDEX_FILE = pathlib.Path(__file__).parents[2] / "data" / "cead" / "meta" / "index.json"
_INDEX: list[dict] = json.loads(_INDEX_FILE.read_text(encoding="utf-8"))

# A handful of real, in-index CUTs (valid). slug_for_cut(cut) is not None for these.
_VALID_CUTS = [e["cut"] for e in _INDEX[:10]]
# A CUT guaranteed absent from the closed index (hallucinated / orphan).
_INVALID_CUT = "99999"
assert _INVALID_CUT not in {e["cut"] for e in _INDEX}


def _write_incidents(path: pathlib.Path, cuts: list[str]) -> None:
    payload = {
        "generated": "2026-06-19T00:00:00Z",
        "incidents": [
            {"title_es": f"incident {i}", "outlet": "test", "url": f"http://x/{i}", "cut": cut}
            for i, cut in enumerate(cuts)
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_scored_all_valid_cuts_passes(tmp_path):
    incidents_path = tmp_path / "current.json"
    _write_incidents(incidents_path, _VALID_CUTS)

    exit_code = run_scored(incidents_path)

    assert exit_code == 0  # accuracy 1.0 >= threshold


def test_scored_orphan_cuts_below_threshold_exits_2(tmp_path):
    incidents_path = tmp_path / "current.json"
    # 5 valid + 5 orphan → accuracy 0.5, well below ACCURACY_THRESHOLD (0.90).
    cuts = _VALID_CUTS[:5] + [_INVALID_CUT] * 5
    assert (5 / len(cuts)) < ACCURACY_THRESHOLD
    _write_incidents(incidents_path, cuts)

    exit_code = run_scored(incidents_path)

    assert exit_code == 2


def test_scored_missing_current_json_exits_1(tmp_path):
    incidents_path = tmp_path / "does-not-exist.json"

    exit_code = run_scored(incidents_path)

    assert exit_code == 1
