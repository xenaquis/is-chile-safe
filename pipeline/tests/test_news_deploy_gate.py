"""
pipeline/tests/test_news_deploy_gate.py

FRESH-04 / V-12 (35-02): the news cron deploys only when the served incident set
changes (data/incidents/current.json or data/incidents/archive/), the decision runs
AFTER commit + push and fails open (R-09), and human data-only pushes deploy through
deploy-on-code.yml (R-04).

All git operations run in pytest tmp_path repos -- the real data/ is never touched.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path

import pytest

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / ".github" / "scripts"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
DEPLOY_NEEDED = SCRIPTS_DIR / "news-deploy-needed.sh"
NEWS_PIPELINE_YML = WORKFLOWS_DIR / "news-pipeline.yml"
DEPLOY_ON_CODE_YML = WORKFLOWS_DIR / "deploy-on-code.yml"
HEARTBEAT_YML = WORKFLOWS_DIR / "heartbeat.yml"

CANONICAL_CURL = (
    'curl -X POST --fail --silent --show-error --retry 3 --retry-all-errors '
    '--max-time 60 "$CF_HOOK"'
)


def _find_bash() -> str:
    """Same resolution as test_workflow_guards.py (F-86): never the WSL stub."""
    if platform.system() == "Windows":
        for c in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe"):
            if Path(c).is_file():
                return c
    return shutil.which("bash") or "/usr/bin/bash"


BASH = _find_bash()


def run_script(path: Path, args=None, cwd=None, env_overrides=None):
    env = dict(os.environ)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [BASH, str(path), *(args or [])],
        capture_output=True, text=True, timeout=30, cwd=cwd, env=env,
    )


# ---------------------------------------------------------------------------
# Temp git repo fixture
# ---------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, timeout=30, check=True,
    )
    return result.stdout


def _write(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q")
    _git(r, "config", "user.name", "test")
    _git(r, "config", "user.email", "test@example.invalid")
    _git(r, "config", "commit.gpgsign", "false")
    _git(r, "config", "core.autocrlf", "false")
    _write(r, "data/incidents/current.json", '{"incidents":[]}')
    _write(r, "data/incidents/seen.json", "{}")
    _write(r, "data/incidents/rejected/2026-09.json", "[]")
    _write(r, "data/incidents/archive/2026-08.json", '{"incidents":[]}')
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "baseline")
    return r


def _commit_change(repo: Path, changes: dict[str, str]) -> None:
    for rel, text in changes.items():
        _write(repo, rel, text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "change")


# ---------------------------------------------------------------------------
# Script behaviour
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"data/incidents/seen.json": '{"a":1}'}, "deploy=false"),
        ({"data/incidents/rejected/2026-09.json": '[{"a":1}]'}, "deploy=false"),
        ({"data/incidents/pending.json": "[]"}, "deploy=false"),
        ({"data/incidents/current.json": '{"incidents":[1]}'}, "deploy=true"),
        ({"data/incidents/archive/2026-09.json": '{"incidents":[]}'}, "deploy=true"),
        (
            {"data/incidents/seen.json": '{"b":2}', "data/incidents/current.json": '{"incidents":[2]}'},
            "deploy=true",
        ),
    ],
    ids=["seen-only", "rejected-only", "pending-only", "current", "new-archive", "seen+current"],
)
def test_deploy_decision(repo, changes, expected):
    _commit_change(repo, changes)
    result = run_script(DEPLOY_NEEDED, ["HEAD~1", "HEAD"], cwd=repo)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


def test_not_a_git_repo_errors(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    result = run_script(
        DEPLOY_NEEDED, ["HEAD~1", "HEAD"], cwd=plain,
        env_overrides={"GIT_CEILING_DIRECTORIES": str(tmp_path)},
    )
    assert result.returncode != 0
    assert "::error::" in result.stderr
    assert "deploy=" not in result.stdout


@pytest.mark.parametrize("args", [[], ["HEAD"], ["HEAD~1", "HEAD", "extra"]])
def test_wrong_arg_count_errors(repo, args):
    result = run_script(DEPLOY_NEEDED, args, cwd=repo)
    assert result.returncode != 0
    assert "::error::" in result.stderr
    assert "deploy=" not in result.stdout


def test_unknown_ref_errors(repo):
    result = run_script(DEPLOY_NEEDED, ["no-such-ref-35", "HEAD"], cwd=repo)
    assert result.returncode != 0
    assert "::error::" in result.stderr
    assert "deploy=" not in result.stdout


# ---------------------------------------------------------------------------
# Workflow structure (skipped without PyYAML, like test_news_health_gate.py)
# ---------------------------------------------------------------------------


def _load(path: Path) -> dict:
    if yaml is None:
        pytest.skip("PyYAML not installed — install to run workflow structure tests")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _step(steps, name_fragment):
    for i, step in enumerate(steps):
        if name_fragment in (step.get("name") or ""):
            return i, step
    raise AssertionError(f"step {name_fragment!r} not found")


def _news_steps():
    return _load(NEWS_PIPELINE_YML)["jobs"]["scrape"]["steps"]


def _commit_body() -> str:
    _, step = _step(_news_steps(), "Commit data if changed")
    return step["run"]


def _fallback_line() -> str:
    lines = [ln.strip() for ln in _commit_body().splitlines() if "news-deploy-needed.sh" in ln]
    assert len(lines) == 1, lines
    return lines[0]


class TestNewsPipelineDeployGate:
    def test_decision_runs_after_commit_and_push(self):
        body = _commit_body()
        decide = body.index("news-deploy-needed.sh HEAD~1 HEAD")
        assert body.index("git commit") < decide
        assert body.index("push-with-rebase.sh") < decide

    def test_decision_fails_open(self):
        line = _fallback_line()
        assert '>> "$GITHUB_OUTPUT"' in line
        fallback = line.split("|| {", 1)
        assert len(fallback) == 2, "fail-open fallback `|| {` missing"
        assert "deploy=true" in fallback[1]
        assert "::warning::" in fallback[1]

    def test_unchanged_branch_writes_changed_and_deploy_false(self):
        body = _commit_body()
        then_part = body.split("if git diff --staged --quiet; then", 1)[1].split("else", 1)[0]
        assert 'echo "changed=false" >> "$GITHUB_OUTPUT"' in then_part
        assert 'echo "deploy=false" >> "$GITHUB_OUTPUT"' in then_part

    def test_deploy_step_if_and_canonical_curl(self):
        _, step = _step(_news_steps(), "Trigger Cloudflare Pages deploy")
        assert step.get("if") == "steps.commit.outputs.deploy == 'true'"
        assert step["run"].strip() == CANONICAL_CURL

    def test_commit_body_has_no_expression_interpolation(self):
        assert "${{" not in _commit_body()


def _run_fallback(line: str, tmp_path: Path, cwd: Path):
    out = tmp_path / "github_output"
    out.write_text("", encoding="utf-8")
    # GitHub Actions runs `run:` bodies as `bash -e -o pipefail`.
    result = subprocess.run(
        [BASH, "-e", "-o", "pipefail", "-c", line],
        capture_output=True, text=True, timeout=30, cwd=cwd,
        env={**os.environ, "GITHUB_OUTPUT": str(out)},
    )
    return result, out.read_text(encoding="utf-8")


def test_fallback_fails_open_when_script_fails(tmp_path, repo):
    line = _fallback_line().replace(
        ".github/scripts/news-deploy-needed.sh", f'"{(tmp_path / "does-not-exist.sh").as_posix()}"',
    )
    result, output = _run_fallback(line, tmp_path, repo)
    assert result.returncode == 0, result.stderr
    assert output.strip().splitlines()[-1] == "deploy=true"
    assert "::warning::" in result.stdout


def test_fallback_passes_through_real_decision(tmp_path, repo):
    _commit_change(repo, {"data/incidents/seen.json": '{"c":3}'})
    line = _fallback_line().replace(
        ".github/scripts/news-deploy-needed.sh", f'"{DEPLOY_NEEDED.as_posix()}"',
    )
    result, output = _run_fallback(line, tmp_path, repo)
    assert result.returncode == 0, result.stderr
    assert output.strip().splitlines() == ["deploy=false"]
    assert "::warning::" not in result.stdout


# ---------------------------------------------------------------------------
# deploy-on-code.yml (R-04)
# ---------------------------------------------------------------------------


def test_deploy_on_code_triggers_on_human_data_pushes():
    data = _load(DEPLOY_ON_CODE_YML)
    on_block = data.get("on", data.get(True))  # PyYAML 1.1: bare `on` -> True
    push = on_block["push"]
    assert push["branches"] == ["master"]
    for path in (
        "site/**",
        ".github/workflows/deploy-on-code.yml",
        "data/incidents/current.json",
        "data/incidents/archive/**",
        "data/cead/**",
    ):
        assert path in push["paths"], path
