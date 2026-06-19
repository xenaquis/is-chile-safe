---
phase: 17-robust-crime-index
reviewed: 2026-06-18T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - pipeline/scripts/verify_data_quality.py
  - pipeline/snapshots/fetch_spd_homicide.py
  - pipeline/snapshots/fetch_sii_exposure.py
  - pipeline/snapshots/fetch_fiscalia_secuestro.py
  - pipeline/snapshots/__init__.py
findings:
  critical: 0
  warning: 4
  info: 3
  total: 7
status: issues_found
---

# Phase 17: Code Review Report

**Reviewed:** 2026-06-18
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Four Python scripts (three snapshot fetchers and one offline QA harness) were reviewed. All scripts correctly write only under `data/snapshots/` or `.planning/` — none touch `data/cead/`, `featured_rates`, `by_family`, or any displayed-metric path. No secrets or raw xlsx/xlsb files are committed. The `CACHE_ONLY=1` offline path is correctly wired in the two network-capable scripts (`fetch_spd_homicide.py`, `fetch_sii_exposure.py`). `fetch_fiscalia_secuestro.py` is correctly static-only (no download path at all). Atomic writes via `atomic_write_json` (os.replace) are used consistently.

Four warnings were found: one logic bug in `_rederive_rate` that silently returns the wrong year's value under partial cache, one runtime crash risk from unchecked population-zero division in the QA harness, one unhandled exception path in the SII fetcher during integer coercion, and one missing record-count guard in `fetch_fiscalia_secuestro.py` (though low-impact since the data is static). Three informational items are also noted.

---

## Warnings

### WR-01: Silent wrong-year fallback in `_rederive_rate` returns first available value regardless of year

**File:** `pipeline/scripts/verify_data_quality.py:85-88`

**Issue:** When the requested year key is absent from `row["values"]`, the fallback at lines 85-88 iterates over all keys and returns the value of the very first one it encounters, ignoring year entirely. This means a check expecting a 2024 rate could silently receive a 2020 rate, causing false-PASS or misdirected FAIL results in checks 5 and 6.

```python
# Current — returns arbitrary year's value
for k, v in row["values"].items():
    return parse_cead_float(v)
return None
```

**Fix:** Remove the silent fallback; return `None` if the specific year is absent, which correctly triggers a DOCUMENTED outcome rather than a wrong-year comparison:

```python
val = row["values"].get(str(year))
if val is None:
    return None
return parse_cead_float(val)
```

---

### WR-02: Division-by-zero crash when `population == 0` in checks 7 and 8

**File:** `pipeline/scripts/verify_data_quality.py:493-495, 548-549`

**Issue:** In `check_7_san_joaquin_homicidios` and `check_8_recoleta_homicidios_2024`, the PASS branch constructs an f-string that always evaluates `count * 100000 / pop`, even when the earlier guard `if count_2024 is not None and pop and rate_2024 is not None` skips the arithmetic check. If `pop == 0` and all three values are truthy (count=0 would be falsy, but count could be 0 which is also falsy — the real risk is `pop=0` with a non-zero count), the f-string in the return statement will raise `ZeroDivisionError` and crash the harness for that check.

More precisely: the condition `if count_2024 is not None and pop and rate_2024 is not None` correctly gates the error-check, but the unconditional f-string in the `return CheckResult(... evidence=...)` block recomputes `count_2024 * 100000 / pop` without any guard. If `pop` is falsy (0 or None from JSON), the earlier if-block is skipped but the return statement still crashes.

**Fix:** Guard the f-string division, or extract the computed rate before the return:

```python
derived_str = (
    f"{count_2024 * 100000 / pop:.4f}" if pop else "N/A (pop=0)"
)
```

---

### WR-03: Unhandled `ValueError` / `OverflowError` when coercing NaN empresas/trabajadores to `int` in `fetch_sii_exposure.py`

**File:** `pipeline/snapshots/fetch_sii_exposure.py:172-180`

**Issue:** The per-row coercion uses `pd.notna(row[col_empresas])` as a guard before calling `int(row[col_empresas])`. However, if pyxlsb returns a float like `1e20` for a cell with an extreme value (malformed or merged header rows that survived the dropna), `int()` will succeed but silently produce a nonsensical count. More critically, if the column contains a string after `pd.to_numeric(..., errors="coerce")` set it to NaN and the dropna on `col_year` (line 153) did not remove it, a subsequent row iteration could still expose a non-numeric value in `col_empresas`/`col_trabajadores`. The `pd.notna` guard handles NaN but not other non-numeric remnants.

This is low probability but can silently write corrupt records rather than raising loudly.

**Fix:** Wrap the per-record int coercions in a try/except and skip the offending row with a warning:

```python
try:
    emp = int(row[col_empresas]) if pd.notna(row[col_empresas]) else None
    trab = int(row[col_trabajadores]) if pd.notna(row[col_trabajadores]) else None
except (ValueError, OverflowError) as exc:
    log.warning("Skipping row with bad numeric value: %s", exc)
    continue
records.append({"cut": cut, "name": canonical, "year": int(row[col_year]),
                "empresas": emp, "trabajadores": trab})
```

---

### WR-04: `fetch_fiscalia_secuestro.py` has no record-count guard before writing output

**File:** `pipeline/snapshots/fetch_fiscalia_secuestro.py:63-83`

**Issue:** The two network-capable scripts each enforce a `MIN_RECORDS` guard before calling `atomic_write_json`. The fiscalia script skips this because data is static, but the same pattern should apply for consistency and future-proofing. If `KNOWN_RECORDS` were accidentally emptied (e.g., during a merge conflict resolution), the script would silently write an empty `records: []` snapshot with no error.

**Fix:** Add a minimal guard:

```python
if not KNOWN_RECORDS:
    raise RuntimeError("KNOWN_RECORDS is empty — refusing to overwrite snapshot.")
```

---

## Info

### IN-01: `assert` used as a runtime guard at module import time in `verify_data_quality.py`

**File:** `pipeline/scripts/verify_data_quality.py:33`

**Issue:** `assert REPO_ROOT.is_dir()` is stripped when Python runs with `-O` (optimized mode). Although no CI job currently uses `-O`, assertions are not the right mechanism for runtime invariant checks in production scripts.

**Fix:** Replace with an explicit `if` / `raise`:

```python
if not REPO_ROOT.is_dir():
    raise RuntimeError(f"REPO_ROOT not found: {REPO_ROOT}")
```

---

### IN-02: `_rederive_count` in `verify_data_quality.py` is dead code

**File:** `pipeline/scripts/verify_data_quality.py:93-104`

**Issue:** The function `_rederive_count` is defined but never called anywhere in the file. Its body explicitly returns `None` unconditionally. It adds noise and may mislead future maintainers into thinking count re-derivation from cache is implemented.

**Fix:** Remove the function entirely, or replace with a `# TODO:` comment at the call site explaining why count re-derivation was deferred.

---

### IN-03: `fetch_spd_homicide.py` logs unmatched names twice (redundant warning)

**File:** `pipeline/snapshots/fetch_spd_homicide.py:143-148, 178-179`

**Issue:** Unmatched commune names are logged at line 143-148 (inside the main loop guard) and again at line 178-179 (after the record-count guard). The second call emits an identical `log.warning` with the same data. This doubles the noise in CI logs without adding information.

**Fix:** Remove the duplicate `log.warning` block at lines 178-179; the first warning (line 143) already fires with the full sorted list.

---

_Reviewed: 2026-06-18_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
