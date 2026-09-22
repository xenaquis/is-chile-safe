# Phase 26: Event Clustering Spike - Pattern Map

**Mapped:** 2026-07-29
**Files analyzed:** 6 (3 new, 3 modified)
**Analogs found:** 6 / 6

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `pipeline/news/clustering.py` | service (pure module, LLM-adjudication) | batch / request-response (LLM calls) + transform | `pipeline/news/classifier.py` (LLM call shape) + `pipeline/news/dedup.py` (bucket/threshold pattern) + `pipeline/news/store.py` (sha256 ID pattern) | role-match (composite — no single file covers all three concerns) |
| `pipeline/tests/test_clustering.py` | test | offline/mocked | `pipeline/tests/test_classifier.py` (mocking pattern) + `pipeline/tests/test_dedup.py` (bucket/threshold test style) | exact (mocking) / role-match (bucket tests) |
| `pipeline/tests/fixtures/clustering_golden_set.json` | fixture (test data) | file-I/O | `pipeline/tests/conftest.py`'s `FIXTURES_DIR` convention + `sample_cead_html` fixture pattern | role-match |
| `pipeline/news/schema.py` (MODIFY) | model | CRUD (Pydantic validation) | itself — extend existing `IncidentRecord` using the same optional-field-with-default pattern already used for `slug` | exact (self-precedent) |
| `pipeline/requirements.txt` (MODIFY) | config | — | itself — append one line at end of file, matching existing pin style (`name==version`) | exact |
| `pipeline/tests/test_schema_incidents.py` (MODIFY) | test | CRUD/regression | itself — extend using the exact `test_incident_record_slug_optional` backward-compat pattern | exact (self-precedent) |
| `pipeline/scripts/run_clustering_spike.py` | utility (CLI script) | batch | no close analog exists (no `pipeline/scripts/` dir found with a comparable one-shot CLI) — treat as net-new, compose from `clustering.py`'s public functions + `store.py`'s `_load_incidents_list`-style JSON reading | no analog |

## Pattern Assignments

### `pipeline/news/clustering.py` (service, LLM-adjudication + pure transform)

**Analogs:** `pipeline/news/classifier.py` (LLM call shape), `pipeline/news/dedup.py` (bucketing/threshold style), `pipeline/news/store.py` (sha256 ID derivation)

**Imports pattern** — mirror `classifier.py:31-46`:
```python
from __future__ import annotations

import json
import logging
import os
import re

from openai import AuthenticationError, OpenAI, RateLimitError
from openai import APIStatusError as _APIStatusError
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)
```
Note: `clustering.py` does NOT import from `classifier.py` (research explicitly says "call pattern reference only, not imported by clustering.py") — duplicate the client-construction block rather than share it, matching the way `classifier.py` itself duplicates per-provider blocks rather than abstracting them.

**LLM client construction pattern** (`classifier.py:75-79`, ping-validated in `26-00-SPIKE-PING.md:42-43`):
```python
client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY", "placeholder"),
    base_url="https://openrouter.ai/api/v1",
)
MODEL = "ibm-granite/granite-4.1-8b"
```

**Core call pattern with try/except ladder** (`classifier.py:211-247`, adapt `_call_api` → `_call_verdict_api`):
```python
def _call_verdict_api(user_content: str) -> str | None:
    try:
        resp = client.chat.completions.create(
            model=MODEL, temperature=0.0, max_tokens=220,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        content = resp.choices[0].message.content
        return content if content else None
    except AuthenticationError:
        logger.error("OpenRouter auth failed — check OPENROUTER_API_KEY")
        return None
    except RateLimitError:
        logger.warning("OpenRouter rate limited")
        return None
    except _APIStatusError as exc:
        logger.warning("OpenRouter HTTP %s: %s", exc.status_code, exc.message)
        return None
    except Exception as exc:
        logger.warning("OpenRouter call failed: %s: %s", type(exc).__name__, exc)
        return None
```
**Do not add the empty-content retry** from `classify()` (`classifier.py:161-166`) unless the planner explicitly wants it for the adjudication path — research's Standard Stack section notes `classifier.py` "hand-rolls one retry on empty content" but doesn't mandate mirroring it for clustering; keep call-count budget in mind (≤2,000 total).

**JSON-fence stripping** — reuse verbatim, do not reimplement (`classifier.py:136-137, 205-208`):
```python
_JSON_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)

def _strip_json_fence(raw: str) -> str:
    m = _JSON_FENCE_RE.match(raw)
    return m.group(1) if m else raw
```

**Pydantic verdict-parse-reject pattern** (mirrors `classifier.py:170-189`'s json.loads → ValidationError → None-on-failure):
```python
raw_stripped = _strip_json_fence(raw)
try:
    data = json.loads(raw_stripped)
except json.JSONDecodeError as exc:
    logger.warning("JSONDecodeError from verdict call: %s", exc)
    return _NO_MERGE_VERDICT  # fail-safe: unparseable -> no-merge (CLUS-03)
try:
    verdict = ClusterVerdict.model_validate(data)
except ValidationError as exc:
    logger.warning("ClusterVerdict validation failed: %s", exc)
    return _NO_MERGE_VERDICT
return verdict
```
Define `ClusterVerdict(BaseModel)` with the ping-validated shape (`26-00-SPIKE-PING.md:22`): `same_event: bool`, `confidence: Literal["high","low"]`, `facts: dict` (or nested submodel with `lugar_coincide/tipo_delito_coincide/actores_coinciden: bool|None`), `rationale: str`.

**Bucketing pattern** — mirror `dedup.py:85-104`'s `(cut, date)` bucket-then-threshold-compare structure:
```python
# Source: pipeline/news/dedup.py:85-104 (structure only — different scorer/threshold)
from collections import defaultdict
bucket_map: dict[tuple[str, str], list[dict]] = defaultdict(list)
for inc in incidents:
    bucket_map[(inc.get("cut", ""), inc.get("date", ""))].append(inc)
```
**Threshold-constant style** — mirror `dedup.py:21`'s module-level named constant, not a magic number inline:
```python
_PREFILTER_THRESHOLD: float = 45.0  # rapidfuzz token_set_ratio — separate calibration from dedup.py's 0.82
```

**Cluster-ID sha256 pattern** — direct precedent, `store.py:46-48`:
```python
# Source: pipeline/news/store.py:46-48 (make_id) — same library, same idea, applied to a sorted set
import hashlib

def cluster_id(member_ids: list[str]) -> str:
    joined = ",".join(sorted(member_ids))
    return hashlib.sha256(joined.encode()).hexdigest()
```

**Module docstring style** — mirror `dedup.py:1-11`'s header comment block (module path, one-line purpose + REQ ID, strategy bullets, explicit "no new dependency" note where relevant).

---

### `pipeline/tests/test_clustering.py` (test, offline/mocked)

**Analog:** `pipeline/tests/test_classifier.py`

**Mocking the LLM client** — exact pattern to copy, `test_classifier.py:11, 18-21, 45-51`:
```python
from unittest.mock import MagicMock, patch

def _make_mock_response(data: dict) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = json.dumps(data)
    return mock_resp

def test_adjudicate_pair_merges_on_high_confidence():
    data = {"same_event": True, "confidence": "high", "facts": {...}, "rationale": "..."}
    with patch("pipeline.news.clustering.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(data)
        verdict = adjudicate_pair(incident_a, incident_b)
    assert verdict.same_event is True
```
Note the docstring convention at top of `test_classifier.py:1-6` ("The configured LLM provider is NEVER called live — all responses mocked via unittest.mock.patch.") — copy this exact framing into `test_clustering.py`'s module docstring; it directly satisfies CLUS-08.

**Threshold/bucket test style** — mirror `pipeline/tests/test_dedup.py` for `test_prefilter_candidates` (read that file if further detail needed; not re-read here — structure already visible via `dedup.py`'s public `deduplicate()`/`are_duplicates()` functions being the thing under test, same shape expected for `prefilter_candidates()`).

**Fixture usage** — use `pipeline/tests/conftest.py`'s `FIXTURES_DIR = Path(__file__).parent / "fixtures"` constant (`conftest.py:9`) to locate `clustering_golden_set.json`; follow the `sample_cead_html`-style skip-if-absent guard (`conftest.py:12-21`) only if the fixture is expected to sometimes be missing — for the golden set it should be committed and always present, so a hard `FileNotFoundError`/normal `Path.read_text()` is more appropriate than a skip.

---

### `pipeline/tests/fixtures/clustering_golden_set.json` (fixture)

**Analog:** `pipeline/tests/conftest.py`'s existing fixtures directory convention — no direct JSON-fixture-of-this-shape precedent exists; follow the recommended format already specified in RESEARCH.md's "Golden-Set Construction Mechanics" section (pairs list with `pair_id`, `incident_a_id`, `incident_b_id`, `label`, `note`, `cached_verdict`).

---

### `pipeline/news/schema.py` (MODIFY — add `cluster_id`, `is_primary`)

**Analog:** itself — the existing `slug: str | None = None` optional-field-with-default pattern, `schema.py:61`:
```python
# Source: pipeline/news/schema.py:48-61 (existing IncidentRecord)
class IncidentRecord(BaseModel):
    ...
    slug: str | None = None  # resolved commune slug (NEWS-03); optional for back-compat
    # ADD (Phase 26, ON GO ONLY):
    cluster_id: str | None = None
    is_primary: bool = False
```
No new `@field_validator` needed unless the planner wants to validate `cluster_id` format (e.g., hex-string length) — `slug` has no validator either, so omitting one for these two fields is consistent with existing precedent.

---

### `pipeline/requirements.txt` (MODIFY — add rapidfuzz)

**Analog:** itself — append using the exact pinned `name==version` style already used for every other line (tail of file: `feedparser==6.0.11`, `openai==2.34.0`, `boto3`, `trafilatura`):
```
rapidfuzz==3.14.5
```
Note two lines (`boto3`, `trafilatura`) are unpinned in the current file — `rapidfuzz` should still be pinned per RESEARCH.md's explicit instruction (`rapidfuzz==3.14.5`), not left bare, since the version was independently verified.

---

### `pipeline/tests/test_schema_incidents.py` (MODIFY — backward-compat test for new fields)

**Analog:** itself — `test_incident_record_slug_optional` (`test_schema_incidents.py:221-226`) is the exact template for CLUS-09:
```python
# Source: pipeline/tests/test_schema_incidents.py:221-226 (existing pattern for slug)
def test_incident_record_slug_optional():
    """An IncidentRecord without slug still validates (back-compat with existing current.json)."""
    data = _valid_incident()
    data.pop("slug", None)  # ensure slug is absent
    record = IncidentRecord.model_validate(data)
    assert record.slug is None

# ADD, mirroring the above exactly:
def test_incident_record_cluster_fields_optional():
    """An IncidentRecord without cluster_id/is_primary still validates (back-compat)."""
    data = _valid_incident()
    data.pop("cluster_id", None)
    data.pop("is_primary", None)
    record = IncidentRecord.model_validate(data)
    assert record.cluster_id is None
    assert record.is_primary is False
```
Also extend `test_incidents_file_valid_round_trip` (`test_schema_incidents.py:53-64`) — the `set(incident.keys())` assertion at line 59-64 will need `"cluster_id"` and `"is_primary"` added to the expected key set, or that test breaks on the schema change; treat this as a required companion edit, not optional.

Use the existing `_valid_incident(**overrides)` helper (`test_schema_incidents.py:22-36`) unchanged — it already supports overrides via `base.update(overrides)`, so no new helper is needed.

---

### `pipeline/scripts/run_clustering_spike.py` (NEW — no analog)

No `pipeline/scripts/` directory with a comparable one-shot CLI report generator was found in this repo. Compose from:
- `store.py:88-99` (`_load_incidents_list`) for reading `current.json`/archive JSON safely (handles missing file, malformed JSON, `{"incidents": [...]}` wrapper shape) — read-only usage only, do not call `merge_and_write`.
- `clustering.py`'s own `prefilter_candidates()`, `adjudicate_pair()`, `assemble_clusters()`, `cluster_id()` as the pipeline stages.
- Plain `print()`/`logging` for the GO/NO-GO report — no existing report-writer precedent in this codebase to copy; keep it simple (stdout + optionally a written `.md`/`.json` report file under the phase dir, per RESEARCH.md's structure).

## Shared Patterns

### LLM client construction + error ladder
**Source:** `pipeline/news/classifier.py:75-79, 211-247`
**Apply to:** `pipeline/news/clustering.py`'s `adjudicate_pair()` / `_call_verdict_api()`
```python
client = OpenAI(api_key=os.environ.get("OPENROUTER_API_KEY", "placeholder"),
                 base_url="https://openrouter.ai/api/v1")
# try/except: AuthenticationError -> log.error; RateLimitError -> log.warning;
# APIStatusError -> log.warning w/ status code; bare Exception -> log.warning; all return None
```

### Mocking the LLM client in tests
**Source:** `pipeline/tests/test_classifier.py:11, 18-21, 45-51`
**Apply to:** `pipeline/tests/test_clustering.py` — every test that exercises `adjudicate_pair()`
```python
with patch("pipeline.news.clustering.client") as mock_client:
    mock_client.chat.completions.create.return_value = _make_mock_response(data)
```
Never patch `openai.OpenAI` itself — patch the module-level `client` singleton, matching this codebase's established convention (both `classifier.py` and the new `clustering.py` construct `client` at import time).

### sha256 deterministic ID derivation
**Source:** `pipeline/news/store.py:46-48` (`make_id`)
**Apply to:** `clustering.py`'s `cluster_id()` function
```python
hashlib.sha256(<deterministic-sorted-input>.encode()).hexdigest()
```

### Optional-field-with-default schema extension (backward compat)
**Source:** `pipeline/news/schema.py:61` (`slug`) + `pipeline/tests/test_schema_incidents.py:221-226`
**Apply to:** `schema.py`'s `cluster_id`/`is_primary` addition and its companion regression test
```python
field: Type | None = None   # or bool = False
# test: pop the field from a valid dict, assert model still validates with the default
```

### Pinned-dependency line style
**Source:** `pipeline/requirements.txt` (tail: `feedparser==6.0.11`, `openai==2.34.0`)
**Apply to:** the `rapidfuzz==3.14.5` addition

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `pipeline/scripts/run_clustering_spike.py` | utility (CLI) | batch | No `pipeline/scripts/` one-shot CLI/report-generator precedent exists in this codebase; compose from `store.py`'s read helper + `clustering.py`'s own functions per RESEARCH.md's Architecture Patterns diagram |
| `pipeline/tests/fixtures/clustering_golden_set.json` | fixture | file-I/O | No JSON fixture of this specific pairs-with-cached-verdicts shape exists yet; follow RESEARCH.md's specified format directly (see "Golden-Set Construction Mechanics" section, reproduced in Pattern Assignments above) |

## Metadata

**Analog search scope:** `pipeline/news/`, `pipeline/tests/`, `pipeline/requirements.txt`
**Files scanned:** `classifier.py`, `dedup.py`, `store.py`, `schema.py`, `conftest.py`, `test_classifier.py`, `test_schema_incidents.py`, `requirements.txt` (8 files read in full; all ≤ 250 lines, single-pass reads, no re-reads)
**Pattern extraction date:** 2026-07-29
