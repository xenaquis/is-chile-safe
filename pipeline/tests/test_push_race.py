"""
pipeline/tests/test_push_race.py

Phase 32 (F-91): the CRON-06 fetch-rebase-push retry loop
(.github/scripts/push-with-rebase.sh), proven in both race directions
against real local bare-clone git repos in pytest's tmp_path -- this is the
exact scenario executed manually during planning, now encoded so it re-runs
automatically instead of being remembered (F-81).

Two directions, per F-90's narrowed claim:
- DISJOINT paths (the real news-vs-CEAD shape): both writers' commits land
  on origin, exit 0.
- SAME-FILE conflict: the rebase aborts, script exits 1 with an ::error::
  substring, origin's history contains ONLY the first writer's commit --
  never a silent merge, never a silent loss.
"""
import platform
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".github" / "scripts" / "push-with-rebase.sh"


def _find_bash() -> str:
    if platform.system() == "Windows":
        candidates = [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
        ]
        for c in candidates:
            if Path(c).is_file():
                return c
    which = shutil.which("bash")
    if which:
        return which
    return "/usr/bin/bash"


BASH = _find_bash()


def _run(cmd, cwd):
    return subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, timeout=30, check=True
    )


def _git_init_clone_pair(tmp_path: Path):
    """Build origin (bare) + two clones (A, B) with an initial commit
    already pushed, mirroring the real news-vs-CEAD topology."""
    origin = tmp_path / "origin.git"
    clone_a = tmp_path / "clone-a"
    clone_b = tmp_path / "clone-b"

    _run(["git", "init", "--bare", "-q", str(origin)], cwd=tmp_path)
    _run(["git", "clone", "-q", str(origin), str(clone_a)], cwd=tmp_path)

    _run(["git", "config", "user.email", "a@example.com"], cwd=clone_a)
    _run(["git", "config", "user.name", "Writer A"], cwd=clone_a)
    (clone_a / "README.md").write_text("init\n", encoding="utf-8")
    _run(["git", "add", "."], cwd=clone_a)
    _run(["git", "commit", "-q", "-m", "init"], cwd=clone_a)
    _run(["git", "push", "-q", "origin", "master"], cwd=clone_a)

    _run(["git", "clone", "-q", str(origin), str(clone_b)], cwd=tmp_path)
    _run(["git", "config", "user.email", "b@example.com"], cwd=clone_b)
    _run(["git", "config", "user.name", "Writer B"], cwd=clone_b)

    return origin, clone_a, clone_b


def test_disjoint_path_race_survives_with_no_lost_commit(tmp_path):
    origin, clone_a, clone_b = _git_init_clone_pair(tmp_path)

    # Writer A commits and pushes first, touching data/file-a.txt.
    data_a = clone_a / "data"
    data_a.mkdir()
    (data_a / "file-a.txt").write_text("a\n", encoding="utf-8")
    _run(["git", "add", "."], cwd=clone_a)
    _run(["git", "commit", "-q", "-m", "from A"], cwd=clone_a)
    _run(["git", "push", "-q", "origin", "master"], cwd=clone_a)

    # Writer B, unaware of A's push, commits touching a DIFFERENT file.
    data_b = clone_b / "data"
    data_b.mkdir()
    (data_b / "file-b.txt").write_text("b\n", encoding="utf-8")
    _run(["git", "add", "."], cwd=clone_b)
    _run(["git", "commit", "-q", "-m", "from B"], cwd=clone_b)

    result = subprocess.run(
        [BASH, str(SCRIPT), "master", "5"],
        cwd=str(clone_b),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0
    assert "push succeeded" in result.stdout

    log = _run(["git", "log", "--oneline", "--all"], cwd=origin).stdout
    assert "from A" in log
    assert "from B" in log


def test_same_file_race_aborts_loudly_with_no_silent_loss(tmp_path):
    origin, clone_a, clone_b = _git_init_clone_pair(tmp_path)

    (clone_a / "data").mkdir()
    (clone_a / "data" / "current.json").write_text("base\n", encoding="utf-8")
    _run(["git", "add", "."], cwd=clone_a)
    _run(["git", "commit", "-q", "-m", "seed current.json"], cwd=clone_a)
    _run(["git", "push", "-q", "origin", "master"], cwd=clone_a)

    _run(["git", "pull", "-q", "origin", "master"], cwd=clone_b)

    # Writer A updates the SAME file and pushes first.
    (clone_a / "data" / "current.json").write_text("A-write\n", encoding="utf-8")
    _run(["git", "add", "."], cwd=clone_a)
    _run(["git", "commit", "-q", "-m", "from A"], cwd=clone_a)
    _run(["git", "push", "-q", "origin", "master"], cwd=clone_a)

    # Writer B, unaware, updates the SAME file with different content.
    (clone_b / "data" / "current.json").write_text("B-write\n", encoding="utf-8")
    _run(["git", "add", "."], cwd=clone_b)
    _run(["git", "commit", "-q", "-m", "from B"], cwd=clone_b)

    result = subprocess.run(
        [BASH, str(SCRIPT), "master", "5"],
        cwd=str(clone_b),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 1
    assert "::error::rebase conflict during data commit" in result.stdout

    log = _run(["git", "log", "--oneline", "--all"], cwd=origin).stdout
    assert "from A" in log
    assert "from B" not in log

    content = _run(
        ["git", "show", "master:data/current.json"], cwd=origin
    ).stdout
    assert content == "A-write\n"
