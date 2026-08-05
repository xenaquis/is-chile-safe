"""
pipeline/tests/test_workflow_guards.py

Phase 32 (F-81, F-86): two-direction pytest proofs for the shared bash guard
scripts (.github/scripts/require-env.sh, .github/scripts/check-heartbeat.sh),
shelling out to the real scripts with real subprocess calls.

F-86: on this dev machine, bare `subprocess.run(["bash", ...])` resolves to
C:\\WINDOWS\\system32\\bash.EXE (the WSL launcher stub), which returns rc=1
with EMPTY stdout and a WSL relay error on stderr when no distro is
installed. Every "must exit 1" assertion is therefore vacuously satisfiable
by a process that never ran the script at all. This file resolves bash
explicitly to Git for Windows' real interpreter, and ships a canary test
that must pass first -- if it doesn't, every other test here is meaningless.
"""
import platform
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / ".github" / "scripts"
REQUIRE_ENV = SCRIPTS_DIR / "require-env.sh"
CHECK_HEARTBEAT = SCRIPTS_DIR / "check-heartbeat.sh"


def _find_bash() -> str:
    """Resolve a real bash interpreter, never the bare name (F-86).

    On Windows, `shutil.which("bash")` (and a fortiori a bare "bash" argv[0])
    can resolve to the WSL launcher stub at C:\\WINDOWS\\system32\\bash.EXE,
    which is not a real POSIX shell unless a WSL distro is installed. Git for
    Windows ships a real bash at one of two well-known paths; prefer those
    explicitly before falling back to PATH resolution.
    """
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


def run_script(path: Path, args=None, env_overrides=None):
    """Run a bash script with explicit bash resolution, real subprocess.

    Returns the CompletedProcess. env_overrides replaces the environment
    passed to the subprocess (merged over a minimal base) -- used so tests
    can control exactly which vars are set/unset/blank without leaking the
    test runner's own environment into assertions.
    """
    import os

    args = args or []
    env = dict(os.environ)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [BASH, str(path), *args],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


def test_bash_interpreter_is_usable():
    """F-86 canary: the resolved bash must actually run. If this fails,
    every other test in this file is meaningless -- it means bash resolved
    to the WSL stub or another non-functional interpreter, and every
    "must exit 1" assertion downstream would be vacuously true."""
    result = subprocess.run(
        [BASH, "-c", "echo hello; exit 3"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 3
    assert result.stdout.strip() == "hello"
    assert "WSL" not in result.stderr


class TestRequireEnv:
    def test_fails_on_blank_secret(self):
        result = run_script(REQUIRE_ENV, ["CF_HOOK"], env_overrides={"CF_HOOK": ""})
        assert result.returncode == 1
        assert "::error::CF_HOOK is not set" in result.stdout

    def test_fails_on_all_blank(self):
        result = run_script(
            REQUIRE_ENV,
            ["VAR_A", "VAR_B"],
            env_overrides={"VAR_A": "", "VAR_B": ""},
        )
        assert result.returncode == 1
        assert "::error::VAR_A is not set" in result.stdout
        assert "::error::VAR_B is not set" in result.stdout

    def test_fails_on_unset_var(self):
        import os

        env = dict(os.environ)
        env.pop("TOTALLY_UNSET_VAR_32", None)
        result = subprocess.run(
            [BASH, str(REQUIRE_ENV), "TOTALLY_UNSET_VAR_32"],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        assert result.returncode == 1
        assert "::error::TOTALLY_UNSET_VAR_32 is not set" in result.stdout

    def test_passes_on_all_present(self):
        result = run_script(
            REQUIRE_ENV,
            ["VAR_A", "VAR_B"],
            env_overrides={"VAR_A": "x", "VAR_B": "y"},
        )
        assert result.returncode == 0
        assert "All required secrets present: VAR_A VAR_B" in result.stdout

    def test_passes_with_url_containing_special_chars(self):
        result = run_script(
            REQUIRE_ENV,
            ["CF_HOOK"],
            env_overrides={
                "CF_HOOK": "https://api.cloudflare.com/hook?token=a&b=c#frag"
            },
        )
        assert result.returncode == 0

    def test_never_prints_secret_value(self):
        secret_value = "sk-super-secret-token-xyz-123"
        result = run_script(
            REQUIRE_ENV, ["MY_SECRET"], env_overrides={"MY_SECRET": secret_value}
        )
        # Non-vacuous per F-86: assert the success line IS present (the
        # script genuinely ran) AND the secret value is absent from output.
        assert result.returncode == 0
        assert "All required secrets present: MY_SECRET" in result.stdout
        assert secret_value not in result.stdout
        assert secret_value not in result.stderr

    def test_cf_hook_blank_fails(self):
        """F-84: the guard must be wired to the variable the run: step
        actually consumes (CF_HOOK), not the secret's alias name
        (CF_DEPLOY_HOOK_URL)."""
        result = run_script(REQUIRE_ENV, ["CF_HOOK"], env_overrides={"CF_HOOK": ""})
        assert result.returncode == 1
        assert "CF_HOOK is not set" in result.stdout


def _iso_days_ago(days: float) -> str:
    from datetime import datetime, timedelta, timezone

    ts = datetime.now(timezone.utc) - timedelta(days=days)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


class TestCheckHeartbeatR2:
    def test_passes_within_threshold(self):
        ts = _iso_days_ago(1)
        result = run_script(CHECK_HEARTBEAT, ["r2", "4", ts])
        assert result.returncode == 0
        assert "r2 heartbeat OK" in result.stdout

    def test_fails_beyond_threshold(self):
        ts = _iso_days_ago(5)
        result = run_script(CHECK_HEARTBEAT, ["r2", "4", ts])
        assert result.returncode == 1
        assert "::error::r2 heartbeat" in result.stdout


class TestCheckHeartbeatCead:
    def test_passes_within_threshold(self):
        # The measured real gap: 104 days, threshold 150.
        ts = _iso_days_ago(104)
        result = run_script(CHECK_HEARTBEAT, ["cead", "150", ts])
        assert result.returncode == 0
        assert "cead heartbeat OK" in result.stdout

    def test_fails_beyond_threshold(self):
        ts = _iso_days_ago(151)
        result = run_script(CHECK_HEARTBEAT, ["cead", "150", ts])
        assert result.returncode == 1
        assert "::error::cead heartbeat" in result.stdout

    def test_boundary_exactly_at_threshold_passes(self):
        ts = _iso_days_ago(150)
        result = run_script(CHECK_HEARTBEAT, ["cead", "150", ts])
        assert result.returncode == 0
        assert "cead heartbeat OK" in result.stdout


class TestCheckHeartbeatNews:
    def test_passes_within_threshold(self):
        ts = _iso_days_ago(1)
        result = run_script(CHECK_HEARTBEAT, ["news", "3", ts])
        assert result.returncode == 0
        assert "news heartbeat OK" in result.stdout

    def test_fails_beyond_threshold(self):
        ts = _iso_days_ago(4)
        result = run_script(CHECK_HEARTBEAT, ["news", "3", ts])
        assert result.returncode == 1
        assert "::error::news heartbeat" in result.stdout

    def test_boundary_exactly_at_threshold_passes(self):
        ts = _iso_days_ago(3)
        result = run_script(CHECK_HEARTBEAT, ["news", "3", ts])
        assert result.returncode == 0
        assert "news heartbeat OK" in result.stdout


class TestCheckHeartbeatCommon:
    def test_fails_on_empty_timestamp(self):
        result = run_script(CHECK_HEARTBEAT, ["news", "3", ""])
        assert result.returncode == 1
        assert "no timestamp evidence found" in result.stdout

    def test_fails_on_unparseable_timestamp(self):
        result = run_script(CHECK_HEARTBEAT, ["news", "3", "not-a-timestamp"])
        assert result.returncode == 1
        assert "could not be parsed" in result.stdout

    def test_rejects_unknown_mode(self):
        result = run_script(CHECK_HEARTBEAT, ["bogus", "3", _iso_days_ago(1)])
        assert result.returncode == 2
        assert "Usage:" in result.stderr

    def test_usage_error_on_missing_args(self):
        result = run_script(CHECK_HEARTBEAT, ["news", "3"])
        assert result.returncode == 2
        assert "Usage:" in result.stderr
