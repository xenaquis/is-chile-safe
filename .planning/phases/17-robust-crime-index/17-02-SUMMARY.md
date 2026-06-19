---
phase: 17-robust-crime-index
plan: "02"
subsystem: pipeline/snapshots
tags: [data-quality, snapshots, spd, sii, fiscalia, reference-only]
dependency_graph:
  requires: []
  provides: [data/snapshots/spd_homicide.json, data/snapshots/sii_exposure.json, data/snapshots/fiscalia_secuestro.json]
  affects: []
tech_stack:
  added: [pipeline/snapshots package]
  patterns: [CACHE_ONLY=1 offline path, atomic_write_json, make_slug CUT join, try/except parse guard, record count guard]
key_files:
  created:
    - pipeline/snapshots/__init__.py
    - pipeline/snapshots/fetch_spd_homicide.py
    - pipeline/snapshots/fetch_sii_exposure.py
    - pipeline/snapshots/fetch_fiscalia_secuestro.py
    - data/snapshots/spd_homicide.json
    - data/snapshots/sii_exposure.json
    - data/snapshots/fiscalia_secuestro.json
    - data/snapshots/ATTRIBUTION.md
  modified: []
decisions:
  - "CUT join via make_slug on data/cead/meta/index.json (not catalog.json which has no commune list)"
  - "SII columns accessed by position index (0,1,4,6) not by name — pyxlsb encoding of column headers is inconsistent across environments"
  - "Fiscalia script embeds static series (PDF-only source); no network download path"
  - "Unmatched SPD names (Calera, Marchihue) and SII names (Aisen, Coihaique, Paihuano, Titil, Trehuaco) are logged as warnings — some are genuine non-CEAD communes, others are encoding artifacts to investigate in Phase 18"
metrics:
  duration: "20m"
  completed: "2026-06-18"
  tasks: 2
  files: 8
---

# Phase 17 Plan 02: Snapshot Scripts (SPD + SII + Fiscalia) Summary

Three reproducible fetch/normalize snapshot scripts and their normalized JSON outputs committed under `data/snapshots/` as reference-only artifacts for the Phase 18 composite crime index — plus an attribution file. No displayed metric touched; CEAD schema unchanged.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | SPD homicide + SII exposure snapshot scripts | 038eec3 | pipeline/snapshots/__init__.py, fetch_spd_homicide.py, fetch_sii_exposure.py, data/snapshots/spd_homicide.json, data/snapshots/sii_exposure.json |
| 2 | Fiscalia secuestro snapshot + attribution file | ffb5a47 | pipeline/snapshots/fetch_fiscalia_secuestro.py, data/snapshots/fiscalia_secuestro.json, data/snapshots/ATTRIBUTION.md |

## Snapshot Output Summary

| Snapshot | Records | Vintage | Granularity |
|----------|---------|---------|-------------|
| spd_homicide.json | 1534 | 2018-2025 | commune + year |
| sii_exposure.json | 6820 | 2005-2024 | commune + year |
| fiscalia_secuestro.json | 5 | 2023-2024 | regional (fiscalia regions) |

## Verification Results

- `CACHE_ONLY=1 python pipeline/snapshots/fetch_spd_homicide.py` — 1534 records, all have `cut/name/year/homicides`
- `CACHE_ONLY=1 python pipeline/snapshots/fetch_sii_exposure.py` — 6820 records, all have `cut/name/year/empresas/trabajadores`; `Sin Informacion` bucket (20 rows) dropped
- `python pipeline/snapshots/fetch_fiscalia_secuestro.py` — 5 records with `region/year/secuestros`
- `git status` shows no `.xlsx` or `.xlsb` staged
- No file under `data/cead/` or `site/` was modified

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Notes

- The plan references `data/cead/meta/catalog.json` as the CUT join source, but that file only contains the crime family taxonomy (no commune names). The actual commune name→CUT mapping is in `data/cead/meta/index.json` (346 entries, `{cut, name, slug, ...}`). Used `index.json` for the join — this is the correct file.
- SII column access by positional index (0=year, 1=commune, 4=empresas, 6=trabajadores) rather than by name, because pyxlsb column name encoding is environment-dependent (confirmed garbled characters on Windows cp1252). The underlying data values are unaffected.
- SPD unmatched names: `Calera` (maps to either `La Calera` or `Calera de Tango` — ambiguous), `Marchihue` (small commune not in CEAD 346). Both logged as warnings; no silent drop.
- SII unmatched names: `Aisen`, `Coihaique`, `Paihuano`, `Titil`, `Trehuaco` — not in index.json (CEAD 346 does not include these communes). Logged as warnings.

## Known Stubs

None — these are data pipeline scripts with no UI surface.

## Threat Flags

None — no new network endpoints or auth paths introduced. xlsx/xlsb parsing is wrapped in try/except per T-17-01; raw files not committed per T-17-02.

## Self-Check: PASSED

- pipeline/snapshots/__init__.py: EXISTS
- pipeline/snapshots/fetch_spd_homicide.py: EXISTS
- pipeline/snapshots/fetch_sii_exposure.py: EXISTS
- pipeline/snapshots/fetch_fiscalia_secuestro.py: EXISTS
- data/snapshots/spd_homicide.json: EXISTS (1534 records)
- data/snapshots/sii_exposure.json: EXISTS (6820 records)
- data/snapshots/fiscalia_secuestro.json: EXISTS (5 records)
- data/snapshots/ATTRIBUTION.md: EXISTS
- Commits 038eec3, ffb5a47: VERIFIED
