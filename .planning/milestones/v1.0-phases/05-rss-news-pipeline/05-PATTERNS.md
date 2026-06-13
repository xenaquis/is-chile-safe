# Phase 5: RSS News Pipeline — Pattern Map

**Mapped:** 2026-06-13
**Files analyzed:** 16 new/modified files
**Analogs found:** 16 / 16

---

## File Classification

| New / Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---------------------|------|-----------|----------------|---------------|
| `pipeline/news/__init__.py` | utility | — | `pipeline/cead/__init__.py` (empty) | exact |
| `pipeline/news/feeds.py` | service | request-response | `pipeline/cead/client.py` | role-match |
| `pipeline/news/classifier.py` | service | request-response | `pipeline/cead/client.py` + RESEARCH.md examples | role-match |
| `pipeline/news/centroids.py` | utility | transform | `pipeline/cead/catalog.py` | role-match |
| `pipeline/news/dedup.py` | utility | transform | `pipeline/cead/normalizer.py` (transform/validate style) | role-match |
| `pipeline/news/store.py` | service | CRUD | `pipeline/shared/atomic_write.py` usage in `scrape_cead.py` | role-match |
| `pipeline/news/schema.py` | model | — | `pipeline/shared/schema.py` | exact |
| `pipeline/scripts/build_centroids.py` | utility | batch | `pipeline/scripts/fetch_ine_population.py` | exact |
| `pipeline/scripts/audit_incidents.py` | utility | batch | `pipeline/scripts/fetch_ine_population.py` | role-match |
| `pipeline/scrape_news.py` | controller | request-response | `pipeline/scrape_cead.py` | exact |
| `pipeline/tests/test_feeds.py` | test | — | `pipeline/tests/test_client.py` | exact |
| `pipeline/tests/test_classifier.py` | test | — | `pipeline/tests/test_schema.py` | exact |
| `pipeline/tests/test_dedup.py` | test | — | `pipeline/tests/test_normalizer.py` | exact |
| `pipeline/tests/test_store.py` | test | — | `pipeline/tests/test_atomic_write.py` | exact |
| `pipeline/tests/test_centroids.py` | test | — | `pipeline/tests/test_catalog.py` | exact |
| `pipeline/tests/test_schema.py` (extend) | test | — | `pipeline/tests/test_schema.py` | exact |
| `pipeline/tests/fixtures/feed_*.xml` | fixture | — | `pipeline/tests/fixtures/cead_response_sample.html` | role-match |
| `pipeline/requirements.txt` (modify) | config | — | existing file | exact |

---

## Pattern Assignments

### `pipeline/news/__init__.py` (utility, package marker)

**Analog:** any existing `pipeline/cead/__init__.py` — empty file.

**Pattern:** empty file; package marker only. No content needed.

---

### `pipeline/news/feeds.py` (service, request-response)

**Analog:** `pipeline/cead/client.py`

**Imports pattern** (lines 1–20 of client.py):
```python
import pathlib
import requests
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
```
For feeds.py, replace `requests` with `feedparser` and keep `tenacity` imports.

**User-Agent convention** (lines 48–55 of client.py):
```python
session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (compatible; IsChileSafe data pipeline;"
            " +https://ischilesafe.com)"
        ),
        ...
    }
)
```
feeds.py uses a module-level constant instead:
```python
USER_AGENT = "IsChileSafe-news-pipeline/1.0 (+https://ischilesafe.com)"
```

**Tenacity retry decorator** (lines 68–76 of client.py):
```python
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((requests.Timeout, requests.HTTPError)),
)
def _post_with_retry(session: requests.Session, url: str, data: dict) -> requests.Response:
    response = session.post(url, data=data, timeout=30)
    response.raise_for_status()
    return response
```
feeds.py does NOT wrap feedparser in tenacity (feedparser handles HTTP internally); tenacity is used only if adding a raw `requests` pre-flight check for feed health.

**Per-feed try/except fallback** (lines 362–398 of scrape_cead.py — batch loop):
```python
try:
    ...
    html = fetch_communes_batch(...)
    ...
except Exception as exc:
    logger.warning(
        "Failed batch region=%d familia=%d year=%d: %s",
        region_id, familia_id, year, exc,
    )
    # Continue — partial data will fail validation if too much is missing
```
feeds.py mirrors this: each feed gets its own `try/except`; failure logs a warning and returns `[]` — never propagates.

**Logging pattern** (lines 31–35 of scrape_cead.py):
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)
```
All `pipeline/news/` modules use `logger = logging.getLogger(__name__)` only; `basicConfig` is called once in the orchestrator (`scrape_news.py`).

---

### `pipeline/news/classifier.py` (service, request-response)

**Analog:** `pipeline/cead/client.py` for retry/error style; RESEARCH.md §DeepSeek Classification for the actual client call.

**OpenAI SDK client construction** (RESEARCH.md lines 601–606):
```python
import json, os
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)
```

**Chat completion call with JSON mode** (RESEARCH.md lines 632–648):
```python
resp = client.chat.completions.create(
    model="deepseek-v4-flash",
    temperature=0.0,
    max_tokens=512,
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"HEADLINE: {title}\nSUMMARY: {description[:500]}"},
    ],
)
content = resp.choices[0].message.content
if not content:
    return None
return json.loads(content)
```

**CRITICAL constraints (CLAUDE.md + RESEARCH.md):**
- Model ID MUST be `"deepseek-v4-flash"` — never `"deepseek-chat"` or `"deepseek-reasoner"`.
- `response_format={"type": "json_object"}` ONLY — `json_schema` is NOT supported by DeepSeek.
- Prompt must contain the word `"json"` (DeepSeek requirement).
- `temperature=0.0` (D-06, closed-list anti-hallucination).
- `max_tokens=512` (prevents truncated JSON, Pitfall 4).

**Error handling pattern** (mirrors client.py + RESEARCH.md):
```python
except (json.JSONDecodeError, Exception):
    return None
```
Return `None` on any error; caller handles rejection.

**Pydantic v2 validation gate after LLM response** (mirrors schema.py lines 150–162):
```python
from pydantic import BaseModel, field_validator, ValidationError

class ClassifierOutput(BaseModel):
    commune_cut: str | None
    family: str
    title_es: str
    title_en: str
    summary: str
    confidence: float

    @field_validator("family")
    @classmethod
    def family_must_be_valid(cls, v: str) -> str:
        if v not in VALID_FAMILIES:
            raise ValueError(f"Invalid family: {v!r}")
        return v
```
Use `ClassifierOutput.model_validate(raw_dict)` — never `parse_obj` (Pydantic v1, banned).

---

### `pipeline/news/centroids.py` (utility, transform)

**Analog:** `pipeline/cead/catalog.py` for lazy-load module-level cache pattern.

**Lazy-load singleton pattern** (catalog.py lines 58+, adapted):
```python
import json, pathlib

_CENTROIDS: dict[str, dict] | None = None

def get_centroid(cut: str) -> tuple[float, float] | None:
    global _CENTROIDS
    if _CENTROIDS is None:
        path = pathlib.Path(__file__).parents[2] / "data" / "incidents" / "centroids.json"
        _CENTROIDS = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    entry = _CENTROIDS.get(cut)
    return (entry["lat"], entry["lng"]) if entry else None
```

**Path construction pattern** (mirrors all pipeline modules):
```python
_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent  # pipeline/news/ → repo root
```

---

### `pipeline/news/dedup.py` (utility, transform)

**Analog:** `pipeline/cead/normalizer.py` (transform/validate style). No direct analog for title-similarity; logic is from RESEARCH.md.

**Imports pattern** (standard for transform utilities):
```python
import difflib
import re
import unicodedata
from pipeline.news.schema import IncidentRecord
```

**Normalization + similarity** (RESEARCH.md lines 437–443):
```python
def normalize_title(t: str) -> str:
    t = unicodedata.normalize('NFD', t.lower()).encode('ascii', errors='ignore').decode()
    t = re.sub(r'[^\w\s]', '', t)
    return re.sub(r'\s+', ' ', t).strip()

def are_duplicates(t1: str, t2: str, threshold: float = 0.82) -> bool:
    return difflib.SequenceMatcher(None, normalize_title(t1), normalize_title(t2)).ratio() >= threshold
```

**No new dependencies** — `difflib`, `unicodedata`, `re` are all stdlib.

---

### `pipeline/news/store.py` (service, CRUD)

**Analog:** `pipeline/shared/atomic_write.py` + usage in `scrape_cead.py` `_write_all_outputs`.

**`atomic_write_json` signature** (atomic_write.py lines 13–35):
```python
def atomic_write_json(path: pathlib.Path, data: dict | list, compact: bool = False) -> None:
    """Write JSON atomically: write to a .tmp file, then os.replace() to final path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    if compact:
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    else:
        text = json.dumps(data, ensure_ascii=False, indent=2)
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
```
Call as: `atomic_write_json(path, data)` — never open/write directly.

**Write-after-validate pattern** (scrape_cead.py lines 228–231):
```python
# Step 1: Validate (D-14 gate — all-or-nothing)
_validate_communes(communes)
# Only if validation passes:
_atomic_write(output_dir / "file.json", data)
```
store.py mirrors this: call `IncidentsFile.model_validate(payload)` BEFORE calling `atomic_write_json`. If `ValidationError`, log and return without writing (last-good file preserved).

**Directory creation** (atomic_write.py line 28):
```python
path.parent.mkdir(parents=True, exist_ok=True)
```
atomic_write_json handles this internally — no need to pre-create `data/incidents/archive/`.

**Idempotent merge by id** (RESEARCH.md lines 451–470 — the merge algorithm):
```python
# Dedup by id (D-11)
existing_ids = {i["id"] for i in existing}
new_unique = [i for i in new_incidents if i["id"] not in existing_ids]
combined = existing + new_unique
# Partition by 30-day window
cutoff = datetime.date.today() - datetime.timedelta(days=30)
current = [i for i in combined if datetime.date.fromisoformat(i["date"]) >= cutoff]
aged_out = [i for i in combined if datetime.date.fromisoformat(i["date"]) < cutoff]
```

---

### `pipeline/news/schema.py` (model, —)

**Analog:** `pipeline/shared/schema.py` — extend with new models. New file in `pipeline/news/`; do NOT modify `pipeline/shared/schema.py` (shared module).

**Pydantic v2 model pattern** (schema.py lines 1–12, 40–73):
```python
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, field_validator

class IncidentRecord(BaseModel):
    id: str          # sha256(url)[:16]
    cut: str         # validated against VALID_CUTS
    lat: float
    lng: float
    title_es: str
    title_en: str
    date: str        # YYYY-MM-DD
    outlet: str
    url: str
    family: str      # validated against VALID_FAMILIES

    @field_validator("cut")
    @classmethod
    def cut_must_be_valid(cls, v: str) -> str:
        if v not in VALID_CUTS:
            raise ValueError(f"CUT {v!r} not in 346-commune list")
        return v

    @field_validator("family")
    @classmethod
    def family_must_be_valid(cls, v: str) -> str:
        if v not in VALID_FAMILIES:
            raise ValueError(f"Invalid family: {v!r}")
        return v

class IncidentsFile(BaseModel):
    generated: str   # ISO-8601 timestamp
    window_days: int # = 30
    incidents: list[IncidentRecord]
```

**Validation gate function** (mirrors schema.py lines 138–162):
```python
def validate_incidents_file(data: dict) -> IncidentsFile:
    """Validate all-or-nothing. Raises ValidationError on any field failure (D-15)."""
    return IncidentsFile.model_validate(data)
```

**FAMILY_KEYS constant** — import from `pipeline.shared.schema`, do not redefine:
```python
from pipeline.shared.schema import FAMILY_KEYS
VALID_FAMILIES: set[str] = set(FAMILY_KEYS)
```

**VALID_CUTS** — loaded at module import from static file (Open Question 2 resolution):
```python
import json, pathlib
_CUT_FILE = pathlib.Path(__file__).parents[2] / "data" / "incidents" / "cut_list.json"
VALID_CUTS: set[str] = set(json.loads(_CUT_FILE.read_text()) if _CUT_FILE.exists() else [])
```

**Never use Pydantic v1 patterns** (banned per CLAUDE.md):
- No `@validator` — use `@field_validator`
- No `parse_obj()` — use `model_validate()`
- No `class Config` — use `model_config = ConfigDict(...)`

---

### `pipeline/scripts/build_centroids.py` (utility, batch)

**Analog:** `pipeline/scripts/fetch_ine_population.py`

**Module-level path pattern** (fetch_ine_population.py lines 24–26):
```python
REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
OUTPUT_PATH = REPO_ROOT / "data" / "ine" / "poblacion_comunal.json"
```
build_centroids.py mirrors:
```python
REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
TOPO_PATH = REPO_ROOT / "data" / "cead" / "geo" / "communes.topo.json"
OUTPUT_PATH = REPO_ROOT / "data" / "incidents" / "centroids.json"
```

**Atomic write pattern** (fetch_ine_population.py lines 157–173):
```python
import json, os, tempfile
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
tmp_fd, tmp_path = tempfile.mkstemp(dir=OUTPUT_PATH.parent, suffix=".tmp")
try:
    with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp_path, OUTPUT_PATH)
except Exception:
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    raise
```
Alternatively use `atomic_write_json` from `pipeline/shared/atomic_write.py` (preferred — it is the canonical pattern in this codebase):
```python
from pipeline.shared.atomic_write import atomic_write_json
atomic_write_json(OUTPUT_PATH, centroids_dict)
```

**Sanity check pattern** (fetch_ine_population.py lines 177–186):
```python
santiago = pop_map.get("13101")
if santiago is None:
    raise SystemExit("ERROR: Santiago (cut=13101) not found in output")
```
build_centroids.py mirrors: assert `len(centroids) == 346` and spot-check a known CUT (e.g. `"13101"` → lat near -33.4).

**main() + `__main__` guard** (fetch_ine_population.py lines 143–191):
```python
def main() -> None:
    ...
    print(f"Written: {OUTPUT_PATH} ({count} entries)")

if __name__ == "__main__":
    main()
```

**TopoJSON decode approach** — Node.js one-shot (RESEARCH.md lines 328–334):
```python
import subprocess, json, pathlib, tempfile

def decode_topojson_to_geojson(topo_path: pathlib.Path) -> dict:
    """Decode TopoJSON to GeoJSON using topojson-client (already in site/node_modules/)."""
    script = f"""
const topo = require('./site/node_modules/topojson-client');
const fs = require('fs');
const t = JSON.parse(fs.readFileSync('{topo_path.as_posix()}','utf8'));
const geo = topo.feature(t, t.objects['communes-rekeyed']);
process.stdout.write(JSON.stringify(geo));
"""
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)
```

**Shoelace centroid** (RESEARCH.md lines 344–365):
```python
def ring_centroid(coords: list[list[float]]) -> tuple[float, float]:
    area = cx = cy = 0.0
    n = len(coords)
    for i in range(n):
        x0, y0 = coords[i][0], coords[i][1]
        x1, y1 = coords[(i + 1) % n][0], coords[(i + 1) % n][1]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    area /= 2.0
    if abs(area) < 1e-10:
        return coords[0][1], coords[0][0]
    cx /= (6.0 * area)
    cy /= (6.0 * area)
    return cy, cx  # (lat, lng) — GeoJSON is [lng, lat]
```

**TopoJSON property key:** object key = `"communes-rekeyed"`, property `"id"` = CUT code string (RESEARCH.md, confirmed by Python probe).

---

### `pipeline/scripts/audit_incidents.py` (utility, batch — D-16)

**Analog:** `pipeline/scripts/fetch_ine_population.py`

**Pattern:** standalone script with `main()` + `__main__` guard; reads `data/incidents/current.json`, samples 50 random incidents, prints a formatted table. No writes — read-only audit tool.

**Path pattern** (fetch_ine_population.py lines 24–25):
```python
REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
INCIDENTS_PATH = REPO_ROOT / "data" / "incidents" / "current.json"
```

**Graceful missing-file handling** (mirrors fetch_ine_population.py pattern):
```python
if not INCIDENTS_PATH.exists():
    raise SystemExit(f"ERROR: {INCIDENTS_PATH} not found — run scrape_news.py first.")
```

**Output format** — print TSV/table to stdout for human review; no file write needed.

---

### `pipeline/scrape_news.py` (controller, request-response)

**Analog:** `pipeline/scrape_cead.py` — mirror exactly.

**File header and logging setup** (scrape_cead.py lines 1–35):
```python
#!/usr/bin/env python3
"""
pipeline/scrape_news.py

RSS news pipeline entrypoint. Runs the full pipeline:
  1. Fetch RSS from confirmed feeds (BioBioChile, Cooperativa, LaTercera)
  2. Keyword pre-filter + seen-ledger dedup (D-02, D-03)
  3. Classify each candidate with DeepSeek v4-flash (D-05/D-06)
  4. Validate, centroid-lookup, build IncidentRecord (D-07/D-08)
  5. Cross-source dedup (D-10)
  6. Merge into current.json, archive aged-out (D-12)
  7. Pydantic v2 validate + atomic write (D-15)

Exit codes: 0 = success, 1 = failure
"""
from __future__ import annotations
import datetime, logging, sys, pathlib
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
```

**Output dir pattern** (scrape_cead.py lines 40–46):
```python
_REPO_ROOT = pathlib.Path(__file__).parent.parent
_DEFAULT_DATA_DIR = _REPO_ROOT / "data" / "incidents"

def _get_data_dir() -> pathlib.Path:
    override = os.environ.get("NEWS_DATA_DIR")
    return pathlib.Path(override) if override else _DEFAULT_DATA_DIR
```

**main() structure** (scrape_cead.py lines 576–605):
```python
def main() -> int:
    run_date = datetime.date.today()
    output_dir = _get_data_dir()
    logger.info("News pipeline starting. Output dir: %s", output_dir)
    try:
        # ... pipeline logic
        logger.info("Pipeline completed successfully.")
        return 0
    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Internal import pattern** (scrape_cead.py lines 322–331):
```python
def _run_pipeline(...):
    from pipeline.cead.catalog import FAMILIA_IDS, REGION_IDS
    from pipeline.cead.client import cache_raw, fetch_communes_batch
    ...
```
scrape_news.py mirrors: local imports inside functions to avoid circular import issues and to allow easy mocking in tests.

**Per-run classification cap** (D-17) — add a module-level constant and counter:
```python
MAX_CLASSIFICATIONS_PER_RUN = int(os.environ.get("NEWS_MAX_CLASSIFY", "200"))
```

**dotenv loading** (referenced in CLAUDE.md):
```python
from dotenv import load_dotenv
load_dotenv()  # no-op in CI where env is set via repo secrets
```

---

### `pipeline/tests/test_feeds.py` (test)

**Analog:** `pipeline/tests/test_client.py` + `pipeline/tests/conftest.py`

**Test file structure** (test_schema.py lines 1–15):
```python
"""
pipeline/tests/test_feeds.py

Tests for pipeline/news/feeds.py — RSS fetch, keyword pre-filter, seen-ledger.
"""
import pytest
from pipeline.news.feeds import fetch_feed, is_crime_item, filter_seen
```

**Fixture pattern** (conftest.py lines 9–22):
```python
FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def sample_feed_xml():
    xml_path = FIXTURES_DIR / "feed_biobio_sample.xml"
    if not xml_path.exists():
        pytest.skip("feed_biobio_sample.xml not present")
    return xml_path.read_text(encoding="utf-8")
```

**Skip pattern for missing fixtures** (conftest.py lines 18–20):
```python
if not html_path.exists():
    pytest.skip("fixture file not present — create it first")
```

**Test naming convention** (test_schema.py):
- `test_<function>_<condition>_<outcome>` e.g. `test_keyword_filter_crime_item_passes`
- `test_<function>_<bad_condition>_is_rejected` e.g. `test_seen_ledger_known_url_is_skipped`

---

### `pipeline/tests/test_classifier.py` (test)

**Analog:** `pipeline/tests/test_schema.py`

**Mock pattern** — do NOT call live DeepSeek API in tests (RESEARCH.md §DeepSeek Classifier Test Strategy):
```python
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_openai_response():
    """Fixture: mock OpenAI response returning valid classifier JSON."""
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = json.dumps({
        "commune_cut": "13101",
        "family": "propiedad",
        "title_es": "Robo en Santiago",
        "title_en": "Robbery in Santiago",
        "summary": "A robbery occurred.",
        "confidence": 0.87,
    })
    return mock_resp

def test_invalid_cut_rejected(mock_openai_response):
    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_openai_response
        # Inject a non-existent CUT into the response
        mock_openai_response.choices[0].message.content = json.dumps({
            "commune_cut": "99999",  # not in 346-CUT set
            ...
        })
        result = classify("headline", "description", cut_list=[...])
        assert result is None  # rejected
```

**ValidationError assertion pattern** (test_schema.py lines 43–46):
```python
with pytest.raises(ValidationError):
    IncidentRecord.model_validate(bad_dict)
```

---

### `pipeline/tests/test_dedup.py` (test)

**Analog:** `pipeline/tests/test_normalizer.py` (transform/validate style)

**Fixture pattern** — use inline dicts (no file fixtures needed):
```python
@pytest.fixture
def incident_a():
    return {"id": "abc123", "cut": "13101", "date": "2026-06-13",
            "title_es": "Robo en Santiago deja un herido", "url": "https://example.com/1"}

@pytest.fixture
def incident_b_near_duplicate(incident_a):
    import copy
    d = copy.deepcopy(incident_a)
    d["url"] = "https://example.com/2"
    d["title_es"] = "Robo en Santiago deja herido a hombre"  # near-duplicate title
    return d
```

---

### `pipeline/tests/test_store.py` (test)

**Analog:** `pipeline/tests/test_atomic_write.py`

**Temp directory pattern** — use `tmp_path` pytest built-in fixture:
```python
def test_30day_window(tmp_path):
    from pipeline.news.store import merge_and_write
    current_path = tmp_path / "current.json"
    # pre-populate with one old incident (31 days ago) and one fresh
    ...
    merge_and_write([], current_path, archive_dir=tmp_path / "archive")
    result = json.loads(current_path.read_text())
    assert len(result["incidents"]) == 1  # old one moved to archive
```

---

### `pipeline/tests/test_centroids.py` (test)

**Analog:** `pipeline/tests/test_catalog.py`

**Fixture pattern** — minimal centroids.json in temp dir:
```python
@pytest.fixture
def centroids_file(tmp_path):
    data = {"13101": {"lat": -33.456, "lng": -70.654}, "2101": {"lat": -18.5, "lng": -70.3}}
    (tmp_path / "centroids.json").write_text(json.dumps(data), encoding="utf-8")
    return tmp_path / "centroids.json"
```

**Monkeypatch for singleton cache** — reset `_CENTROIDS` between tests:
```python
def test_valid_cut_returns_latlon(monkeypatch, centroids_file):
    import pipeline.news.centroids as mod
    monkeypatch.setattr(mod, "_CENTROIDS", None)
    monkeypatch.setattr(mod, "_CENTROID_PATH", centroids_file)
    lat, lng = mod.get_centroid("13101")
    assert abs(lat - (-33.456)) < 0.001
```

---

### `pipeline/tests/fixtures/feed_*.xml` (fixture files)

**Analog:** `pipeline/tests/fixtures/cead_response_sample.html` pattern — static files committed for deterministic tests.

**Required files:**
- `pipeline/tests/fixtures/feed_biobio_sample.xml` — 5 items: 2 crime, 2 sport, 1 ambiguous. Use `<link>` (not `<guid>`) for URLs (Pitfall 2).
- `pipeline/tests/fixtures/feed_cooperativa_sample.xml` — 5 policial items. Use `<guid>` as the canonical URL.
- `pipeline/tests/fixtures/feed_latercera_sample.xml` — 5 items: 2 crime, 3 non-crime. Include `<content:encoded>` to verify it is NOT sent to LLM (D-01).

**RSS 2.0 skeleton** (all feeds follow this structure):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Feed Name</title>
    <link>https://outlet.cl</link>
    <item>
      <title>Robo en Santiago deja un herido</title>
      <link>https://outlet.cl/article/123</link>
      <guid isPermaLink="true">https://outlet.cl/article/123</guid>
      <description>Descripción del incidente...</description>
      <pubDate>Fri, 13 Jun 2026 12:00:00 +0000</pubDate>
    </item>
    ...
  </channel>
</rss>
```

---

### `pipeline/requirements.txt` (modify — add feedparser)

**Analog:** existing `pipeline/requirements.txt`

**Single line to add:**
```
feedparser==6.0.11
```
No other new dependencies. All other libraries (`openai`, `tenacity`, `pydantic`, `python-dotenv`, `requests`) are already present.

---

## Shared Patterns

### Atomic Write
**Source:** `pipeline/shared/atomic_write.py` lines 13–35
**Apply to:** `pipeline/news/store.py`, `pipeline/scripts/build_centroids.py`
```python
from pipeline.shared.atomic_write import atomic_write_json
# Signature:
def atomic_write_json(path: pathlib.Path, data: dict | list, compact: bool = False) -> None
# Usage:
atomic_write_json(pathlib.Path("data/incidents/current.json"), incidents_file_dict)
```
Never use `open()` + `write()` directly for output files.

### Pydantic v2 Schema Gate (All-or-Nothing)
**Source:** `pipeline/shared/schema.py` lines 138–162
**Apply to:** `pipeline/news/schema.py`, `pipeline/news/store.py`
```python
# Validate BEFORE atomic write — if ValidationError, preserve last-good file
try:
    validated = IncidentsFile.model_validate(payload)
except ValidationError as exc:
    logger.error("Schema validation failed — aborting write: %s", exc)
    return  # last-good current.json preserved
atomic_write_json(output_path, payload)
```

### Logging Pattern
**Source:** `pipeline/scrape_cead.py` lines 31–35
**Apply to:** All `pipeline/news/` modules and `pipeline/scrape_news.py`
```python
import logging
logger = logging.getLogger(__name__)
# In scrape_news.py only:
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
```
Module-level loggers only; `basicConfig` exclusively in the orchestrator entry point.

### Per-Feed Fallback (D-04)
**Source:** `pipeline/scrape_cead.py` lines 362–398 (batch loop try/except)
**Apply to:** `pipeline/news/feeds.py`
```python
for name, url in FEEDS.items():
    try:
        entries = fetch_feed(name, url)
        ...
    except Exception as exc:
        logger.warning("[%s] Feed failed, skipping: %s", name, exc)
        continue  # one feed failure never blocks others
```

### FAMILY_KEYS Constant
**Source:** `pipeline/shared/schema.py` lines 22–30
**Apply to:** `pipeline/news/schema.py` (import, not redefine), `pipeline/news/classifier.py` (for system prompt)
```python
from pipeline.shared.schema import FAMILY_KEYS
# FAMILY_KEYS = ["vida", "robos_violentos", "vif", "drogas", "armas", "propiedad", "incivilidades"]
```

### Repo-Root Path Pattern
**Source:** `pipeline/scrape_cead.py` lines 40–41; `pipeline/scripts/fetch_ine_population.py` lines 24–25
**Apply to:** All new `pipeline/news/` modules and scripts
```python
_REPO_ROOT = pathlib.Path(__file__).parent.parent  # from pipeline/news/
_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent  # from pipeline/scripts/
```
Always use `pathlib.Path(__file__).parents[N]` — never `os.getcwd()`.

### Pytest Fixture for Missing Files
**Source:** `pipeline/tests/conftest.py` lines 18–20
**Apply to:** All new test files that use XML fixture files
```python
if not fixture_path.exists():
    pytest.skip("fixture not present — create it first")
```

---

## No Analog Found

All new files have analogs in the existing codebase. No files require falling back to RESEARCH.md-only patterns.

| File | Note |
|------|------|
| `pipeline/news/classifier.py` (DeepSeek call) | Partial analog only (cead/client.py for retry style); the actual openai SDK call has no codebase precedent — use RESEARCH.md §DeepSeek Classification verbatim |
| `pipeline/tests/fixtures/feed_*.xml` | No XML fixture precedent; use RSS 2.0 skeleton from RESEARCH.md §Feed Structure Notes |

---

## Metadata

**Analog search scope:** `pipeline/` (all subdirectories)
**Files read:** 9 source files + 2 test files + CONTEXT.md + RESEARCH.md + IncidentPinLayer.ts
**Pattern extraction date:** 2026-06-13
