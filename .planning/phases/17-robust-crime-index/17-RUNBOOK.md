# Phase 17 — Wave 0 Spike Runbook (run locally)

The discovery spike CANNOT run from the Claude remote sandbox: every Chilean
government host (CEAD, SPD, SII, INE) returns HTTP 403 to that egress IP. Run it
from a local machine on a clean/Chilean egress — the same context where
`pipeline/scrape_cead.py` works.

## S1 + S4 — CEAD subgroup + tipoVal discovery

```bash
# from repo root
python -m venv .venv && source .venv/bin/activate        # first time only
pip install -r pipeline/requirements.txt                 # first time only

python pipeline/experiments/test_subgroup_discovery.py | tee pipeline/cache/s1_s4_output.txt
```

What to read in the output:

- **S1a (group catalog):** does any attempt dump a JSON list of grupos for
  familia 1? If so, copy the real IDs for *lesiones* and look for *secuestro*.
- **S1b (probe):** lines flagged `<-- HAS DATA` are real subgroups. Homicide=101
  should show data. Find which 1xx ID is **lesiones**. If no candidate is
  **secuestros**, it lives outside familia 1–7 — extend `CANDIDATE_GRUPOS` in
  the script with IDs from the catalog dump and re-run.
- **S4 (tipoVal):** compare counts for `'1'` vs `'2'` vs `'1,2'`. If
  `'1,2' == '1' + '2'`, the measures are additive → the index must normalize per
  offence (the D-AGG double-counting constraint).

Captured HTML/text fixtures land in `pipeline/cache/` (git-ignored).

## After running

Record the confirmed values in `17-WAVE0-RESEARCH-A.md` (template stub below), then
ping me with the output and we close S1/S4 and move to S2 (SPD) + S3 (SII proxy).

Fill in:
- `lesiones`  → `grupo[] = ____`  (familia 1)
- `secuestros`→ `familia[] = ____  grupo[] = ____`
- `tipoVal` mapping → denuncias=`__`  detenciones=`__`  aprehendidos=`__`
- additive? yes / no
