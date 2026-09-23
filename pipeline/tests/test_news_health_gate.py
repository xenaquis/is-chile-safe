"""
pipeline/tests/test_news_health_gate.py

Tests for pipeline/news_health_gate.py — G-04 (post-commit health gate,
NREC-07) amended by G-09.

BF-02 / R-13: the 100%-injected-error harness runs pipeline.scrape_news.main()
for real, so it MUST NOT write to the real repo's data/incidents. Every test
here that touches disk uses tmp_path (via NEWS_DATA_DIR / NEWS_RUN_SUMMARY_PATH),
and the harness additionally snapshots the real data/incidents tree before and
after to prove it never changed (BF-02 replaces an absolute
`git status --porcelain data/` assertion so this suite also passes when the
34-05 post-apply gate runs it with data/ intentionally dirty).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest
from openai import NotFoundError

from pipeline.news_health_gate import evaluate, main as gate_main

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_SCRIPT = REPO_ROOT / "pipeline" / "news_health_gate.py"
REAL_DATA_INCIDENTS = REPO_ROOT / "data" / "incidents"


def _base_summary(**overrides) -> dict:
    summary = {
        "schema": 1,
        "attempted": 0,
        "responded": 0,
        "accepted": 0,
        "genuine_rejects": 0,
        "parse_errors": 0,
        "api_errors": 0,
        "failovers": 0,
        "failover_reason": None,
        "backup_exhausted": False,
        "queued": 0,
        "expired": 0,
        "not_attempted": 0,
        "downstream_rejects": 0,
        "budget_exhausted": False,
    }
    summary.update(overrides)
    return summary


# ---------------------------------------------------------------------------
# G-04 boundaries
# ---------------------------------------------------------------------------


class TestEvaluateBoundaries:
    def test_a_attempted_positive_responded_zero_fails(self):
        reasons = evaluate(_base_summary(attempted=1, responded=0))
        assert any(r.startswith("(a)") for r in reasons)

    def test_a_attempted_zero_responded_zero_passes(self):
        reasons = evaluate(_base_summary(attempted=0, responded=0))
        assert not reasons

    def test_b_ten_attempted_five_errors_fails(self):
        reasons = evaluate(_base_summary(attempted=10, api_errors=5, responded=5, accepted=5))
        assert any(r.startswith("(b)") for r in reasons)

    def test_b_ten_attempted_four_errors_passes(self):
        reasons = evaluate(_base_summary(attempted=10, api_errors=4, responded=6, accepted=6))
        assert not reasons

    def test_b_nine_attempted_inapplicable_below_ten(self):
        """attempted=9 is below the (b)/(d)/(e) 10-item floor and (a) is not
        triggered (responded=4 > 0) — must pass."""
        reasons = evaluate(_base_summary(attempted=9, api_errors=5, responded=4, accepted=4))
        assert not reasons

    def test_c_backup_exhausted_fails_even_with_responses(self):
        reasons = evaluate(_base_summary(attempted=5, responded=3, accepted=3, backup_exhausted=True))
        assert any(r.startswith("(c)") for r in reasons)

    def test_d_g09_ten_attempted_zero_accepted_all_genuine_rejects_fails(self):
        reasons = evaluate(_base_summary(attempted=10, responded=10, accepted=0))
        assert any(r.startswith("(d)") for r in reasons)

    def test_d_g09_nine_attempted_zero_accepted_passes(self):
        reasons = evaluate(_base_summary(attempted=9, responded=9, accepted=0))
        assert not reasons

    def test_e_g09_ten_attempted_two_parse_errors_fails(self):
        reasons = evaluate(_base_summary(attempted=10, responded=10, accepted=8, parse_errors=2))
        assert any(r.startswith("(e)") for r in reasons)

    def test_e_g09_ten_attempted_one_parse_error_with_accepted_passes(self):
        reasons = evaluate(_base_summary(attempted=10, responded=10, accepted=9, parse_errors=1))
        assert not reasons

    def test_f_g09_expired_one_fails(self):
        reasons = evaluate(_base_summary(attempted=1, responded=1, accepted=1, expired=1))
        assert any(r.startswith("(f)") for r in reasons)

    def test_f_g09_expired_zero_no_f_reason(self):
        reasons = evaluate(_base_summary(attempted=1, responded=1, accepted=1, expired=0))
        assert not any(r.startswith("(f)") for r in reasons)

    def test_budget_exhausted_alone_passes_with_warning(self, tmp_path):
        summary_path = tmp_path / "summary.json"
        summary_path.write_text(
            json.dumps(_base_summary(attempted=1, responded=1, accepted=1, budget_exhausted=True)),
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(GATE_SCRIPT), str(summary_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "::warning::" in result.stdout

    def test_failovers_alone_passes_with_warning_naming_reason(self, tmp_path):
        summary_path = tmp_path / "summary.json"
        summary_path.write_text(
            json.dumps(_base_summary(
                attempted=1, responded=1, accepted=1,
                failovers=1, failover_reason="breaker",
            )),
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(GATE_SCRIPT), str(summary_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "::warning::" in result.stdout
        assert "breaker" in result.stdout

    def test_fail_closed_missing_file(self, tmp_path):
        missing = tmp_path / "does-not-exist.json"
        result = subprocess.run(
            [sys.executable, str(GATE_SCRIPT), str(missing)],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "::error::" in result.stdout

    def test_fail_closed_invalid_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(GATE_SCRIPT), str(bad)],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "::error::" in result.stdout

    def test_fail_closed_wrong_schema(self, tmp_path):
        bad = tmp_path / "bad_schema.json"
        bad.write_text(json.dumps(_base_summary(schema=2)), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(GATE_SCRIPT), str(bad)],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "::error::" in result.stdout


# ---------------------------------------------------------------------------
# 100%-injected-error harness (real scrape_news.main(), real ProviderRouter)
# ---------------------------------------------------------------------------


def _status_exc(cls, code):
    req = httpx.Request("POST", "https://x")
    return cls(f"HTTP {code}", response=httpx.Response(code, request=req), body=None)


def _make_entry(title, link, guid, description, pub_date):
    import time as _time
    entry = SimpleNamespace()
    entry.title = title
    entry.link = link
    entry.id = guid
    entry.summary = description
    entry.description = description
    entry.published_parsed = _time.strptime(pub_date, "%Y-%m-%dT%H:%M:%SZ")
    return entry


def _recent_iso(hour: int) -> str:
    import datetime as _dt
    d = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=1)
    return d.strftime("%Y-%m-%d") + f"T{hour:02d}:00:00Z"


def _crime_entries(n: int):
    return [
        _make_entry(
            title=f"Robo con violencia en Santiago deja un herido grave ({i})",
            link=f"https://www.biobiochile.cl/noticias/robo-santiago-{i}.shtml",
            guid=f"https://www.biobiochile.cl/?p={1000 + i}",
            description="Un hombre resultó herido durante un asalto en plena vía pública.",
            pub_date=_recent_iso(8),
        )
        for i in range(n)
    ]


def _snapshot(root: Path) -> dict:
    """sha256 snapshot of every file under root (BF-02)."""
    if not root.exists():
        return {}
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


@pytest.fixture(autouse=True)
def _no_live_network(monkeypatch):
    for var in ("NEWS_FORCE_BACKUP", "NEWS_RUN_BUDGET_S", "NEWS_PROVIDER", "NEWS_MODEL",
                "NEWS_BACKUP_MODEL", "GITHUB_OUTPUT"):
        monkeypatch.delenv(var, raising=False)


def _preflight_ok(*a, **k):
    from pipeline.news.classifier import PreflightResult
    return PreflightResult("ok", 5)


class TestHundredPercentInjectedErrorHarness:
    """R-03/R-04 harness: primary 404s on every call, breaker trips after 5,
    the tripping streak re-dispatches to the backup in the SAME run, and the
    backup also 404s on every call -> backup_exhausted."""

    def test_all_providers_fail_commit_path_reached_gate_fails(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data_dir"
        summary_path = tmp_path / "summary.json"
        monkeypatch.setenv("NEWS_DATA_DIR", str(data_dir))
        monkeypatch.setenv("NEWS_RUN_SUMMARY_PATH", str(summary_path))
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake-primary")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake-backup")

        before = _snapshot(REAL_DATA_INCIDENTS)

        entries = _crime_entries(12)
        test_feeds = {"BioBioChile": "https://www.biobiochile.cl/static/feed-rss"}

        def _always_404(*a, **k):
            raise _status_exc(NotFoundError, 404)

        with patch("pipeline.news.feeds.FEEDS", test_feeds), \
             patch("pipeline.news.feeds.fetch_feed", return_value=entries), \
             patch("pipeline.news.classifier.preflight_openrouter", _preflight_ok), \
             patch("pipeline.news.classifier._request_completion", side_effect=_always_404):
            from pipeline import scrape_news
            rc = scrape_news.main()

        assert rc == 0  # commit step would run

        pending = json.loads((data_dir / "pending.json").read_text(encoding="utf-8"))["items"]
        assert len(pending) == 12

        seen_path = data_dir / "seen.json"
        seen = json.loads(seen_path.read_text(encoding="utf-8")) if seen_path.exists() else {}
        pending_urls = {p["url"] for p in pending}
        assert not (set(seen.keys()) & pending_urls)

        rejected_dir = data_dir / "rejected"
        for f in rejected_dir.glob("*.json") if rejected_dir.exists() else []:
            items = json.loads(f.read_text(encoding="utf-8"))["items"]
            assert not any(it.get("rejection_stage") == "classifier_none" for it in items)

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary["attempted"] == 5
        assert summary["api_errors"] == 5
        assert summary["redispatched"] == 5
        assert summary["recovered_by_redispatch"] == 0
        assert summary["responded"] == 0
        assert summary["failovers"] == 1
        assert summary["backup_exhausted"] is True
        assert summary["not_attempted"] == 7

        # BF-02: the real repo data/incidents tree must be byte-identical.
        after = _snapshot(REAL_DATA_INCIDENTS)
        assert before == after

        # Every file this test created lies under tmp_path.
        for p in data_dir.rglob("*"):
            if p.is_file():
                assert str(p).startswith(str(tmp_path))

        gate_result = subprocess.run(
            [sys.executable, str(GATE_SCRIPT), str(summary_path)],
            capture_output=True, text=True,
        )
        assert gate_result.returncode == 1
        assert "::error::Health gate" in gate_result.stdout

    def test_primary_fails_backup_recovers_gate_passes_with_warning(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data_dir"
        summary_path = tmp_path / "summary.json"
        monkeypatch.setenv("NEWS_DATA_DIR", str(data_dir))
        monkeypatch.setenv("NEWS_RUN_SUMMARY_PATH", str(summary_path))
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake-primary")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake-backup")

        before = _snapshot(REAL_DATA_INCIDENTS)

        entries = _crime_entries(12)
        test_feeds = {"BioBioChile": "https://www.biobiochile.cl/static/feed-rss"}

        valid_output = {
            "commune_name": "Santiago",
            "region_hint": "Metropolitana",
            "family": "propiedad",
            "title_es": "Robo con violencia en Santiago",
            "title_en": "Violent robbery in Santiago",
            "summary": "A man was injured during a robbery.",
            "confidence": 0.9,
        }

        def _backup_ok_response():
            usage = SimpleNamespace(
                prompt_tokens=100, completion_tokens=20,
                completion_tokens_details=SimpleNamespace(reasoning_tokens=0),
            )
            return SimpleNamespace(
                choices=[SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(valid_output)),
                    finish_reason="stop",
                )],
                model="deepseek-v4.1-flash",
                usage=usage,
                provider="DeepSeek",
            )

        def _dispatch(client_, model, provider, user_content, extra_body):
            if provider == "deepseek":
                return _backup_ok_response()
            raise _status_exc(NotFoundError, 404)

        with patch("pipeline.news.feeds.FEEDS", test_feeds), \
             patch("pipeline.news.feeds.fetch_feed", return_value=entries), \
             patch("pipeline.news.classifier.preflight_openrouter", _preflight_ok), \
             patch("pipeline.news.classifier._request_completion", side_effect=_dispatch), \
             patch("pipeline.news.resolver.resolve_cut", return_value=("13101", "santiago")), \
             patch("pipeline.news.centroids.get_centroid", return_value=(-33.45, -70.65)):
            from pipeline import scrape_news
            rc = scrape_news.main()

        assert rc == 0

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary["failovers"] == 1
        assert summary["recovered_by_redispatch"] == 5
        assert summary["api_errors"] == 0
        pending = json.loads((data_dir / "pending.json").read_text(encoding="utf-8"))["items"] \
            if (data_dir / "pending.json").exists() else []
        assert pending == []

        after = _snapshot(REAL_DATA_INCIDENTS)
        assert before == after

        gate_result = subprocess.run(
            [sys.executable, str(GATE_SCRIPT), str(summary_path)],
            capture_output=True, text=True,
        )
        assert gate_result.returncode == 0
        assert "::warning::" in gate_result.stdout


# ---------------------------------------------------------------------------
# Workflow structure (YAML parse, same approach as test_workflow_order.py)
# ---------------------------------------------------------------------------

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

NEWS_PIPELINE_YML = REPO_ROOT / ".github" / "workflows" / "news-pipeline.yml"


def _load_scrape_steps():
    if yaml is None:
        pytest.skip("PyYAML not installed — install to run workflow structure tests")
    data = yaml.safe_load(NEWS_PIPELINE_YML.read_text(encoding="utf-8"))
    return data["jobs"]["scrape"]["steps"], data


def _step_index(steps, name_fragment):
    for i, step in enumerate(steps):
        if name_fragment in (step.get("name") or ""):
            return i
    return None


class TestNewsPipelineWorkflowStructure:
    def test_step_order(self):
        steps, _ = _load_scrape_steps()
        run_i = _step_index(steps, "Run news scraper")
        commit_i = _step_index(steps, "Commit data if changed")
        deploy_i = _step_index(steps, "Trigger Cloudflare Pages deploy")
        gate_i = _step_index(steps, "Health gate")
        label_i = _step_index(steps, "Ensure alert label exists")
        alert_i = _step_index(steps, "Alert via GitHub Issue on failure")

        assert None not in (run_i, commit_i, deploy_i, gate_i, label_i, alert_i)
        assert run_i < commit_i < deploy_i < gate_i < label_i < alert_i

    def test_health_gate_step_has_no_if_or_continue_on_error(self):
        steps, _ = _load_scrape_steps()
        gate_i = _step_index(steps, "Health gate")
        step = steps[gate_i]
        assert "if" not in step
        assert "continue-on-error" not in step
        assert step.get("run", "").strip() == 'python pipeline/news_health_gate.py "$NEWS_RUN_SUMMARY_PATH"'

    def test_scrape_and_gate_steps_share_summary_path_env(self):
        steps, _ = _load_scrape_steps()
        scrape_step = steps[_step_index(steps, "Run news scraper")]
        gate_step = steps[_step_index(steps, "Health gate")]
        expected = "${{ runner.temp }}/news-run-summary.json"
        assert scrape_step["env"]["NEWS_RUN_SUMMARY_PATH"] == expected
        assert gate_step["env"]["NEWS_RUN_SUMMARY_PATH"] == expected

    def test_both_alert_steps_keep_if_failure(self):
        steps, _ = _load_scrape_steps()
        label_step = steps[_step_index(steps, "Ensure alert label exists")]
        alert_step = steps[_step_index(steps, "Alert via GitHub Issue on failure")]
        assert label_step.get("if") == "failure()"
        assert alert_step.get("if") == "failure()"

    def test_no_expr_in_scrape_or_gate_run_bodies(self):
        steps, _ = _load_scrape_steps()
        for name in ("Run news scraper", "Health gate"):
            step = steps[_step_index(steps, name)]
            assert "${{" not in step.get("run", "")

    def test_r09_force_backup_dispatch_input(self):
        _, data = _load_scrape_steps()
        # PyYAML 1.1 resolves the bare `on:` key as boolean True.
        on_block = data.get("on", data.get(True))
        inputs = on_block["workflow_dispatch"]["inputs"]
        assert inputs["force_backup"]["type"] == "boolean"
        assert inputs["force_backup"]["default"] is False

    def test_r09_scrape_step_env_reads_vars_never_writes(self):
        steps, _ = _load_scrape_steps()
        scrape_step = steps[_step_index(steps, "Run news scraper")]
        env = scrape_step["env"]
        assert env["NEWS_FORCE_BACKUP"] == "${{ inputs.force_backup }}"
        assert env["NEWS_MODEL"] == "${{ vars.NEWS_MODEL }}"
        assert env["NEWS_BACKUP_MODEL"] == "${{ vars.NEWS_BACKUP_MODEL }}"
        assert env["NEWS_PROVIDER"] == "${{ vars.NEWS_PROVIDER }}"

        text = NEWS_PIPELINE_YML.read_text(encoding="utf-8")
        assert "gh variable set" not in text
        assert "gh secret set" not in text
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("run:") or stripped.startswith("gh api"):
                assert "gh api" not in stripped or (
                    "variables" not in stripped and "secrets" not in stripped
                )
