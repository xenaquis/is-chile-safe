"""
pipeline/tests/test_validate_news_dedup.py

FID-05 (36-05): validate_news_dedup.py CLI (0 drops over current.json) and the
site/scripts/validate/news-dedup.mjs wrapper (validator #19, unregistered).
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

_REPO = pathlib.Path(__file__).resolve().parents[2]
_SCRIPT = _REPO / "pipeline" / "validate_news_dedup.py"
_MJS = _REPO / "site" / "scripts" / "validate" / "news-dedup.mjs"


def _inc(uid: str, title: str, url: str | None = None) -> dict:
    return {
        "id": uid,
        "cut": "13101",
        "lat": -33.456,
        "lng": -70.654,
        "title_es": title,
        "title_en": title,
        "date": "2026-09-20",
        "outlet": "BioBio Chile",
        "url": url or f"https://biobiochile.cl/article/{uid}",
        "family": "propiedad",
    }


A = _inc("aaaa000000000001", "Robo en Santiago deja un herido")
B = _inc("bbbb000000000002", "Robo en Santiago deja herido a hombre")  # near-dup of A
C = _inc("cccc000000000003", "Festival de música en La Serena celebra 30 años")
D = _inc("dddd000000000004", "Robo en Santiago deja a un herido")  # near-dup of A


def _write(tmp_path, incidents, name="current.json") -> pathlib.Path:
    p = tmp_path / name
    p.write_text(json.dumps({"generated": "2026-09-24T00:00:00Z", "window_days": 30,
                             "incidents": incidents}), encoding="utf-8")
    return p


def _run(*args) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, str(_SCRIPT), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def test_pass_on_duplicate_free(tmp_path):
    r = _run(_write(tmp_path, [A, C]))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "news-dedup: PASS — 0 drops over 2 incidents" in r.stdout


def test_fail_on_title_pair(tmp_path):
    r = _run(_write(tmp_path, [A, B, C]))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "drops=1" in r.stdout
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith("DROP ")]
    assert len(lines) == 1
    assert lines[0].startswith(f"DROP {B['id']} ~ KEEP {A['id']} (title:0.")


def test_missing_file_exit2(tmp_path):
    r = _run(tmp_path / "nope.json")
    assert r.returncode == 2
    assert "::error::" in r.stdout + r.stderr


def test_malformed_file_exit2(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    r = _run(p)
    assert r.returncode == 2
    assert "::error::" in r.stdout + r.stderr


def test_list_on_pass(tmp_path):
    r = _run(_write(tmp_path, [A, C]), "--list")
    assert r.returncode == 0
    assert "(none)" in r.stdout


def _ids_file(tmp_path, ids) -> pathlib.Path:
    p = tmp_path / "ids.txt"
    p.write_text("# S0 ids\n\n" + "\n".join(ids) + "\n", encoding="utf-8")
    return p


def test_only_new_since_ignores_legacy_pair(tmp_path):
    ids = _ids_file(tmp_path, [A["id"], B["id"]])
    r = _run(_write(tmp_path, [A, B, C]), "--only-new-since", ids)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "drops=0" in r.stdout
    assert "forward-only since 2 ids" in r.stdout


def test_only_new_since_counts_new_pair(tmp_path):
    ids = _ids_file(tmp_path, [A["id"], B["id"]])
    r = _run(_write(tmp_path, [A, B, C, D]), "--only-new-since", ids)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "drops=1" in r.stdout
    assert f"DROP {D['id']} ~ KEEP {A['id']}" in r.stdout


def test_only_new_since_missing_ids_file_exit2(tmp_path):
    r = _run(_write(tmp_path, [A, C]), "--only-new-since", tmp_path / "missing.txt")
    assert r.returncode == 2
    assert "::error::" in r.stdout + r.stderr


def test_imports_stdlib_only():
    code = (
        "import sys; sys.path.insert(0, r'%s'); "
        "import importlib.util as u; "
        "s = u.spec_from_file_location('vnd', r'%s'); m = u.module_from_spec(s); "
        "s.loader.exec_module(m); "
        "assert 'pydantic' not in sys.modules, 'pydantic imported'; print('ok')"
    ) % (_REPO, _SCRIPT)
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("incidents,expected", [([A, C], 0), ([A, B, C], 1)])
def test_mjs_wrapper_exit_code_matches(tmp_path, incidents, expected):
    p = _write(tmp_path, incidents)
    env = {**os.environ, "NEWS_DEDUP_CURRENT_JSON": str(p), "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run(["node", str(_MJS)], capture_output=True, text=True,
                       encoding="utf-8", env=env)
    assert r.returncode == expected, r.stdout + r.stderr
    assert r.returncode == _run(p).returncode
