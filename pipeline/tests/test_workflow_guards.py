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

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / ".github" / "scripts"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
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

    def test_fails_on_whitespace_only_value(self):
        """F-102: found by Opus VERIFICATION, fixed inline after the two fix
        cycles were spent. A bare `[ -z ]` ACCEPTED a whitespace-only secret;
        `pipeline/archive_r2.py` then `.strip()`s it, treats it as absent and
        returns 0 -- a green job that archived nothing. That is a complete
        end-to-end silent green no-op surviving INSIDE the guard written to
        abolish silent green no-ops, so it is a defect of the phase's own
        headline invariant, not a nit."""
        for blank in ["   ", "\t", "\n", " \t\n "]:
            result = run_script(
                REQUIRE_ENV, ["MY_SECRET"], env_overrides={"MY_SECRET": blank}
            )
            assert result.returncode == 1, f"{blank!r} should be rejected"
            assert "empty or whitespace-only" in result.stdout

    def test_passes_with_internal_whitespace_value(self):
        """The other direction of F-102 (Operating Lesson 26: widening a guard
        on the axis it was attacked on routinely narrows it on another). The
        stripping must reject values that are ONLY whitespace without rejecting
        legitimate values that merely CONTAIN whitespace."""
        result = run_script(
            REQUIRE_ENV, ["MY_SECRET"], env_overrides={"MY_SECRET": "a b"}
        )
        assert result.returncode == 0
        assert "All required secrets present: MY_SECRET" in result.stdout

    def test_never_prints_secret_value_on_success(self):
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

    def test_never_prints_secret_value_on_failure_path(self):
        """L-06: the original test only covered the success path -- the ONE
        mutation of nine that survived the phase's mutation-testing sweep was
        `echo "${!v}"` added to require-env.sh's ERROR branch, which this
        test would have caught. A second, non-blank secret alongside the
        blank one under test proves the error branch (which iterates ALL
        named vars) does not leak a present secret's value while reporting
        the missing one."""
        present_secret_value = "sk-still-should-never-appear-456"
        result = run_script(
            REQUIRE_ENV,
            ["MY_SECRET", "OTHER_SECRET"],
            env_overrides={"MY_SECRET": "", "OTHER_SECRET": present_secret_value},
        )
        # Non-vacuous per F-86: assert the failure line IS present (the
        # script genuinely ran the error branch) AND the present secret's
        # value is absent from output.
        assert result.returncode == 1
        assert "::error::MY_SECRET is not set" in result.stdout
        assert present_secret_value not in result.stdout
        assert present_secret_value not in result.stderr

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
    """F-99: the boundary/precision cases below use FIXED, injected evidence
    and as-of timestamps -- never `_iso_days_ago()` -- so they cannot race a
    truncated-string evidence timestamp against a marginally later live
    `date` read in the subprocess (the exact mechanism BL-02 measured at
    3/12 runs red). Only the default-clock coverage test below uses the real
    wall clock, and only with a wide non-boundary margin."""

    def test_passes_within_threshold(self):
        result = run_script(
            CHECK_HEARTBEAT,
            ["r2", "4", "2026-05-31T00:00:00Z", "2026-06-01T00:00:00Z"],
        )
        assert result.returncode == 0
        assert "r2 heartbeat OK" in result.stdout

    def test_fails_beyond_threshold(self):
        result = run_script(
            CHECK_HEARTBEAT,
            ["r2", "4", "2026-05-27T00:00:00Z", "2026-06-01T00:00:00Z"],
        )
        assert result.returncode == 1
        assert "::error::r2 heartbeat" in result.stdout

    def test_boundary_exactly_at_threshold_passes(self):
        result = run_script(
            CHECK_HEARTBEAT,
            ["r2", "4", "2026-05-28T00:00:00Z", "2026-06-01T00:00:00Z"],
        )
        assert result.returncode == 0
        assert "r2 heartbeat OK" in result.stdout

    def test_seconds_precision_fails_just_past_threshold(self):
        """F-96: thresholds compare epoch SECONDS against max_days*86400, not
        truncated integer days -- integer-day division previously made a
        "4-day" threshold only fire after 4d23h59m. 4 days + 1 hour past must
        now fail (it would incorrectly PASS under the old integer-division
        form, since (now-ts)/86400 truncates to 4)."""
        result = run_script(
            CHECK_HEARTBEAT,
            ["r2", "4", "2026-05-27T23:00:00Z", "2026-06-01T00:00:00Z"],
        )
        assert result.returncode == 1
        assert "::error::r2 heartbeat" in result.stdout

    def test_default_as_of_uses_live_clock(self):
        """F-99: the as-of argument is optional; production callers omit it
        and fall back to the real clock (see check-heartbeat.sh's "no as-of
        supplied" branch). This is the only test in this class allowed to
        touch the wall clock, and it uses a wide 1-day margin against a
        4-day threshold, far from the boundary, so it cannot flake."""
        ts = _iso_days_ago(1)
        result = run_script(CHECK_HEARTBEAT, ["r2", "4", ts])
        assert result.returncode == 0
        assert "r2 heartbeat OK" in result.stdout

    def test_future_evidence_beyond_allowance_fails(self):
        """F-100: evidence more than 24h in the future must fail, distinctly
        from a normal staleness failure."""
        result = run_script(
            CHECK_HEARTBEAT,
            ["r2", "4", "2026-06-03T00:00:00Z", "2026-06-01T00:00:00Z"],
        )
        assert result.returncode == 1
        assert "::error::r2 heartbeat" in result.stdout
        assert "future" in result.stdout

    def test_future_evidence_within_allowance_passes(self):
        """F-100, second direction: 1h in the future is within the 24h clock-
        skew allowance and must pass normally."""
        result = run_script(
            CHECK_HEARTBEAT,
            ["r2", "4", "2026-06-01T01:00:00Z", "2026-06-01T00:00:00Z"],
        )
        assert result.returncode == 0
        assert "r2 heartbeat OK" in result.stdout


class TestCheckHeartbeatCead:
    """F-93: quarter-boundary based, not a flat day threshold. New interface:
    `check-heartbeat.sh cead <evidence_ts> [as_of_ts]` -- no max_age_days
    argument. The as-of date is ALWAYS injected explicitly in this test class;
    the live-clock default path is exercised only by the real workflow, never
    by tests, per F-93's requirement that the test path never depend on a
    live `date` call."""

    def test_one_boundary_elapsed_passes(self):
        # F-93 case 1: evidence 2026-06-19, as-of 2026-09-30 -> 1 boundary
        # (Jul 1) -> exit 0 (a maintainer running late is normal).
        result = run_script(
            CHECK_HEARTBEAT,
            ["cead", "2026-06-19T00:00:00Z", "2026-09-30T00:00:00Z"],
        )
        assert result.returncode == 0
        assert "cead heartbeat OK" in result.stdout
        assert "1 quarterly due date" in result.stdout

    def test_two_boundaries_elapsed_fails(self):
        # F-93 case 2: evidence 2026-06-19, as-of 2026-10-02 -> 2 boundaries
        # (Jul 1, Oct 1) -> exit 1 (a whole quarter was genuinely skipped).
        result = run_script(
            CHECK_HEARTBEAT,
            ["cead", "2026-06-19T00:00:00Z", "2026-10-02T00:00:00Z"],
        )
        assert result.returncode == 1
        assert "::error::cead heartbeat" in result.stdout
        assert "2 quarterly due dates" in result.stdout

    def test_recent_evidence_one_boundary_passes(self):
        # F-93 case 3: evidence 2026-09-15, as-of 2026-10-02 -> 1 boundary
        # (Oct 1) -> exit 0.
        result = run_script(
            CHECK_HEARTBEAT,
            ["cead", "2026-09-15T00:00:00Z", "2026-10-02T00:00:00Z"],
        )
        assert result.returncode == 0
        assert "cead heartbeat OK" in result.stdout

    def test_old_evidence_four_boundaries_fails(self):
        # F-93 case 4: evidence 2025-12-31, as-of 2026-10-02 -> 4 boundaries
        # (Jan 1, Apr 1, Jul 1, Oct 1 2026) -> exit 1.
        result = run_script(
            CHECK_HEARTBEAT,
            ["cead", "2025-12-31T00:00:00Z", "2026-10-02T00:00:00Z"],
        )
        assert result.returncode == 1
        assert "::error::cead heartbeat" in result.stdout
        assert "4 quarterly due dates" in result.stdout

    def test_evidence_exactly_at_boundary_counts_as_elapsed(self):
        # Evidence timestamped exactly ON a boundary must NOT count that same
        # boundary (the comparison is `b_epoch > ts_epoch`, strictly after).
        result = run_script(
            CHECK_HEARTBEAT,
            ["cead", "2026-07-01T00:00:00Z", "2026-07-01T00:00:00Z"],
        )
        assert result.returncode == 0
        assert "0 quarterly due date" in result.stdout

    def test_zero_boundaries_elapsed_passes(self):
        result = run_script(
            CHECK_HEARTBEAT,
            ["cead", "2026-08-01T00:00:00Z", "2026-08-15T00:00:00Z"],
        )
        assert result.returncode == 0
        assert "0 quarterly due date" in result.stdout

    def test_future_evidence_beyond_allowance_fails(self):
        """F-100/WR-04: evidence more than 24h in the future (e.g. a skewed
        maintainer clock, or a rewritten/cherry-picked commit) previously
        yielded zero boundaries and passed forever -- must now fail,
        distinctly from the normal quarter-skipped failure."""
        result = run_script(
            CHECK_HEARTBEAT,
            ["cead", "2026-08-06T00:00:00Z", "2026-08-04T00:00:00Z"],
        )
        assert result.returncode == 1
        assert "::error::cead heartbeat" in result.stdout
        assert "future" in result.stdout

    def test_future_evidence_within_allowance_passes(self):
        """F-100, second direction: 1h in the future is within the 24h
        clock-skew allowance and must pass normally."""
        result = run_script(
            CHECK_HEARTBEAT,
            ["cead", "2026-08-04T01:00:00Z", "2026-08-04T00:00:00Z"],
        )
        assert result.returncode == 0
        assert "cead heartbeat OK" in result.stdout


class TestCheckHeartbeatNews:
    """F-99: fixed, injected evidence/as-of timestamps for the boundary and
    precision cases -- see TestCheckHeartbeatR2's class docstring for why."""

    def test_passes_within_threshold(self):
        result = run_script(
            CHECK_HEARTBEAT,
            ["news", "3", "2026-05-31T00:00:00Z", "2026-06-01T00:00:00Z"],
        )
        assert result.returncode == 0
        assert "news heartbeat OK" in result.stdout

    def test_fails_beyond_threshold(self):
        result = run_script(
            CHECK_HEARTBEAT,
            ["news", "3", "2026-05-27T00:00:00Z", "2026-06-01T00:00:00Z"],
        )
        assert result.returncode == 1
        assert "::error::news heartbeat" in result.stdout

    def test_boundary_exactly_at_threshold_passes(self):
        result = run_script(
            CHECK_HEARTBEAT,
            ["news", "3", "2026-05-29T00:00:00Z", "2026-06-01T00:00:00Z"],
        )
        assert result.returncode == 0
        assert "news heartbeat OK" in result.stdout

    def test_seconds_precision_fails_just_past_threshold(self):
        """F-96: a "3-day" threshold now fires precisely past 3 days, not
        only past 3d23h59m. 3 days + 1 hour must fail (it would incorrectly
        PASS under the old integer-division form)."""
        result = run_script(
            CHECK_HEARTBEAT,
            ["news", "3", "2026-05-28T23:00:00Z", "2026-06-01T00:00:00Z"],
        )
        assert result.returncode == 1
        assert "::error::news heartbeat" in result.stdout

    def test_default_as_of_uses_live_clock(self):
        """F-99: exercises the production default-clock path with a wide,
        non-boundary margin (see TestCheckHeartbeatR2's equivalent test)."""
        ts = _iso_days_ago(1)
        result = run_script(CHECK_HEARTBEAT, ["news", "3", ts])
        assert result.returncode == 0
        assert "news heartbeat OK" in result.stdout

    def test_future_evidence_beyond_allowance_fails(self):
        result = run_script(
            CHECK_HEARTBEAT,
            ["news", "3", "2026-06-03T00:00:00Z", "2026-06-01T00:00:00Z"],
        )
        assert result.returncode == 1
        assert "::error::news heartbeat" in result.stdout
        assert "future" in result.stdout

    def test_future_evidence_within_allowance_passes(self):
        result = run_script(
            CHECK_HEARTBEAT,
            ["news", "3", "2026-06-01T01:00:00Z", "2026-06-01T00:00:00Z"],
        )
        assert result.returncode == 0
        assert "news heartbeat OK" in result.stdout


class TestCheckHeartbeatMessageFormat:
    def test_failure_message_reports_hours_not_self_contradictory_days(self):
        """WR-05: `age_days_display` used to stay integer-truncated while the
        comparison moved to seconds (F-96), producing a self-contradictory
        message like "3d old, exceeds 3d threshold" for evidence only
        fractionally past the boundary. The failure line now reports hours."""
        result = run_script(
            CHECK_HEARTBEAT,
            ["news", "3", "2026-05-28T23:00:00Z", "2026-06-01T00:00:00Z"],
        )
        assert result.returncode == 1
        assert "73h" in result.stdout
        assert "3d old, exceeds 3d" not in result.stdout


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


def _iter_workflow_files():
    return sorted(WORKFLOWS_DIR.glob("*.yml")) + sorted(WORKFLOWS_DIR.glob("*.yaml"))


def _python_run_steps_missing_setup(text: str):
    """H-02 class-level guard (review's own remedy): for a workflow file's raw
    text, return the list of `run: python ...` step lines that are not
    preceded (within the same job) by both an `actions/setup-python` step and
    a `pip install -r` step. Deliberately NOT a full YAML parse -- this repo's
    workflows use a consistent 6-space step indentation and 2-space job-name
    indentation, and a lightweight line scan is enough to catch the exact
    regression class H-02 found (a python step with no interpreter/deps
    earlier in its job) without adding a YAML dependency to pipeline/tests
    that pipeline/requirements.txt does not otherwise need.
    """
    missing = []
    seen_setup_python = False
    seen_pip_install = False
    for raw_line in text.splitlines():
        # A job-name line ("  <name>:") resets what "earlier in this job" means.
        if (
            raw_line.startswith("  ")
            and not raw_line.startswith("   ")
            and raw_line.rstrip().endswith(":")
            and "jobs:" not in raw_line
        ):
            seen_setup_python = False
            seen_pip_install = False
            continue
        stripped = raw_line.strip()
        if stripped.startswith("- uses: actions/setup-python"):
            seen_setup_python = True
            continue
        if stripped.startswith("run: pip install -r") or stripped == "run: pip install -r":
            seen_pip_install = True
            continue
        if "pip install -r" in stripped:
            seen_pip_install = True
            continue
        if stripped.startswith("run: python "):
            if not (seen_setup_python and seen_pip_install):
                missing.append(raw_line)
    return missing


class TestLintInstrumentIsWired:
    """WR-02: two cheap gaps the re-review found in the lint instrument
    itself. (1) nothing asserted `ci.yml` still calls the armed
    lint-workflows.sh script instead of the bare rhysd/actionlint action
    whose silent-shellcheck-disable defect (F-85) motivated building it --
    so H-03 could silently regress on the next ci.yml edit with nothing
    reddening. (2) lint-workflows.sh's actionlint pass only covers INLINE
    `run:` bodies in workflow YAML; the phase's own `.github/scripts/*.sh`
    files were linted by nothing automated."""

    def test_ci_yml_calls_lint_workflows_script(self):
        ci_text = (WORKFLOWS_DIR / "ci.yml").read_text(encoding="utf-8")
        assert "bash .github/scripts/lint-workflows.sh" in ci_text
        # `rhysd/actionlint` may still be mentioned in prose comments
        # explaining WHY it was replaced -- what must not exist is a live
        # `uses:` step invoking it.
        assert "uses: rhysd/actionlint" not in ci_text

    def test_lint_workflows_shellchecks_its_own_scripts_directly(self):
        text = (SCRIPTS_DIR / "lint-workflows.sh").read_text(encoding="utf-8")
        assert '"$SH" -s bash .github/scripts/*.sh' in text


class TestWorkflowPythonStepsHaveSetup:
    """H-02: the wave-2 rewrite of cead-scraper.yml deleted its
    actions/setup-python + pip install pair while keeping the `python ...`
    run steps, which turned the expected CRON-05 HTTP 403 into a
    ModuleNotFoundError. This is a class-level guard so the same regression
    shape in ANY workflow file fails the pytest suite, not just a one-off
    restore of the single file found by the review."""

    def test_every_workflow_python_step_has_setup_python_and_pip_install(self):
        offenders = {}
        for wf in _iter_workflow_files():
            missing = _python_run_steps_missing_setup(wf.read_text(encoding="utf-8"))
            if missing:
                offenders[wf.name] = missing
        assert not offenders, (
            "workflow(s) with a `run: python ...` step not preceded by both "
            f"actions/setup-python and pip install -r in the same job: {offenders}"
        )

    def test_guard_is_non_vacuous_against_a_synthetic_regression(self):
        """Mutate a copy of a real workflow to reproduce H-02's exact shape
        (delete the setup-python + pip install steps, keep the python run
        step) and confirm the guard function detects it -- proving the
        assertion above is load-bearing, not vacuously true because no
        workflow happens to declare a `run: python` step."""
        real_text = (WORKFLOWS_DIR / "cead-scraper.yml").read_text(encoding="utf-8")
        assert not _python_run_steps_missing_setup(real_text), (
            "sanity check: the real file must currently be clean before mutating it"
        )
        mutated_lines = []
        skip_next_pip_block = False
        for line in real_text.splitlines():
            if "uses: actions/setup-python@" in line:
                skip_next_pip_block = True
                continue
            if skip_next_pip_block and (
                "python-version:" in line
                or line.strip() == ""
                or "Install pipeline deps" in line
                or "run: pip install -r" in line
            ):
                if "run: pip install -r" in line:
                    skip_next_pip_block = False
                continue
            mutated_lines.append(line)
        mutated_text = "\n".join(mutated_lines)
        missing = _python_run_steps_missing_setup(mutated_text)
        assert missing, "mutation removed setup-python/pip install but the guard found nothing — vacuous test"
