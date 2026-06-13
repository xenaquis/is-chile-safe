---
phase: 01-data-foundation
plan: "01"
subsystem: pipeline
tags: [schema, pydantic, atomic-write, pytest, scaffold]
dependency_graph:
  requires: []
  provides:
    - pipeline.shared.schema (ComunaRecord, RegionRecord, NationalRecord, YearRecord, MapPayload, MapPayloadEntry, MetaIndexEntry, validate_all_communes)
    - pipeline.shared.atomic_write (atomic_write_json)
  affects:
    - All downstream pipeline plans (02-cead-client, 03-parser, 04-normalizer)
tech_stack:
  added:
    - pydantic==2.13.4 (v2 models and field validators)
    - pytest==8.4.2 (test framework)
    - requests==2.34.2
    - beautifulsoup4==4.15.0
    - lxml==6.1.1
    - tenacity==9.1.4
    - python-dotenv==1.2.2
    - openpyxl==3.1.5
  patterns:
    - Pydantic v2 syntax exclusively (model_validate, @field_validator, @classmethod)
    - os.replace() atomic write pattern (POSIX + Windows compatible)
    - pytest fixtures in conftest.py for shared test data
key_files:
  created:
    - pipeline/shared/schema.py
    - pipeline/shared/atomic_write.py
    - pipeline/tests/conftest.py
    - pipeline/tests/test_schema.py
    - pipeline/tests/test_atomic_write.py
    - pipeline/requirements.txt
    - pipeline/pytest.ini
    - pipeline/__init__.py
    - pipeline/shared/__init__.py
    - pipeline/tests/__init__.py
    - pipeline/cache/.gitkeep
    - pipeline/tests/fixtures/.gitkeep
    - .gitignore
  modified: []
decisions:
  - Pydantic v2 syntax exclusively — no v1 @validator or parse_obj anywhere in pipeline
  - PLAUSIBILITY_MAX_RATE=20000 as named constant (tighten in later phase when real data is available)
  - sample_cead_html fixture skips gracefully when fixture file absent — no live data required for Task 2/3 tests
metrics:
  duration: ~20min
  completed: "2026-06-12"
  tasks_completed: 3
  tests_passing: 18
---

# Phase 01 Plan 01: Pipeline Scaffold, Schema, and Atomic Write Summary

**One-liner:** Pydantic v2 data contracts (7 models, 346-count validation gate, plausibility range checks) plus atomic JSON write utility, pytest infrastructure, and pinned Python dependencies.

## What Was Built

Three tasks executed sequentially, all green.

**Task 1 — Package scaffold and dependencies**

Created the full `pipeline/` Python package tree with empty `__init__.py` files at `pipeline/`, `pipeline/shared/`, and `pipeline/tests/`. Wrote `pipeline/requirements.txt` with all 7 pinned production packages plus `pytest==8.*`. Wrote `pipeline/pytest.ini` with `pythonpath = ..` so `from pipeline.shared.schema import ...` resolves from repo root. Created `.gitkeep` files for `pipeline/cache/` and `pipeline/tests/fixtures/`. Created `.gitignore` covering `pipeline/cache/*` (raw CEAD responses never committed), `__pycache__/`, `*.pyc`, `.pytest_cache/`, `*.tmp`, and `.env`.

**Task 2 — Schema models and validation gate (DATA-02, DATA-03)**

Implemented `pipeline/shared/schema.py` with 7 Pydantic v2 models matching the canonical interface contract:
- `YearRecord`, `ComunaRecord` (with `id_must_be_cut` field validator), `RegionRecord`, `NationalRecord`
- `MapPayloadEntry` (with `level_must_be_1_to_5` validator), `MapPayload`, `MetaIndexEntry`

Implemented `validate_all_communes(list[dict]) -> list[ComunaRecord]` as the all-or-nothing D-14 gate: rejects count != 346, runs `model_validate` on each record, then plausibility-checks every `YearRecord` rate (negative or > 20000). Module constants `PLAUSIBILITY_MAX_RATE`, `FAMILY_KEYS`, `FEATURED_FAMILIES` provide single named values for downstream plans.

Wrote `conftest.py` with `sample_commune_dict` and `sample_cead_html` fixtures. Wrote `test_schema.py` with 12 tests covering count gate, structural validation, CUT id validator, and plausibility range checks.

**Task 3 — Atomic write utility (DATA-03)**

Implemented `pipeline/shared/atomic_write.py` with `atomic_write_json(path, data)` using `os.replace()` for crash-safe atomic replacement on both Windows and POSIX. UTF-8 encoding with `ensure_ascii=False` preserves Chilean commune names with accented characters (Ñuñoa, etc.). Wrote `test_atomic_write.py` with 6 tests covering round-trip, parent directory creation, no `.tmp` residue, UTF-8 accent preservation, list input, and overwrite behavior.

## Test Results

```
18 passed in 0.27s
```

All tests green across `test_schema.py` (12) and `test_atomic_write.py` (6).

## Deviations from Plan

None — plan executed exactly as written. The pre-existing pip dependency conflicts (gradio requiring pydantic<2.12, inscriptis requiring lxml<6.1.0) are system-level packages unrelated to this pipeline; they do not affect pipeline functionality or test execution.

## Commits

| Hash | Message |
|------|---------|
| b144c9f | chore(01-01): pipeline scaffold, dependencies, and git-ignore |
| bcfb356 | feat(01-01): Pydantic v2 schema models and all-or-nothing validation gate |
| 58e82b3 | feat(01-01): atomic write utility and tests (DATA-03) |

## Known Stubs

None — no hardcoded empty values flow to UI rendering. `featured_rates: {}` in `sample_commune_dict` is a test fixture value, not a UI stub; it will be populated by the normalizer in Plan 04.

## Threat Flags

None — no new network endpoints, auth paths, or file access patterns introduced beyond what the plan's threat model covers (T-01-01 through T-01-SC all addressed).

## Self-Check

- [x] `pipeline/shared/schema.py` exists and contains `PLAUSIBILITY_MAX_RATE = 20000`
- [x] `pipeline/shared/atomic_write.py` exists and contains `os.replace(`
- [x] `pipeline/tests/conftest.py` exists and contains `def sample_commune_dict`
- [x] `pipeline/requirements.txt` contains `pydantic==2.13.4`
- [x] `pipeline/pytest.ini` contains `[pytest]`
- [x] 18 tests pass

## Self-Check: PASSED
