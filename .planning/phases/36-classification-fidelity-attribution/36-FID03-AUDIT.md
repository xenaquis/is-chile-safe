---
phase: 36-classification-fidelity-attribution
plan: 08
status: Task 2 complete (replay + spend). Task 3 (blind audit + score) pending.
---

# 36-FID03-AUDIT.md — FID-03 out-of-sample audit (Phase 36 classifier)

## Task 2 — Select + replay-classify the 14-day pool

### Step 1-2: population (G-32/G-42/R-09)

as_of: 2026-09-26T01:11:57Z

Exclusion inputs (scratchpad, session-local): `v3-exclude-ids.txt` (32 v3
`source_id` values from 36-GOLDEN-V3.md), `v3-siblings.txt` (the 32 v3 raw
stored titles, one per line, used for the sibling ratio check).

```
as_of: 2026-09-26T01:11:57Z
window_days: 14
pool: 1380
by_stage: {"classifier_none": 1210, "commune_null": 1, "low_confidence": 169}
pool_by_epoch: outage=1210 live=170
sibling_exclusions: 13
```

13 sibling exclusions (ratio >= 0.60 over `dedup.normalize_title`), all
matched against the 3 v3 vida/homicide-adjacent headlines (Renca carabinero
crime, Colina volantín robbery-homicide, Fiestas Patrias balance) plus one
against the Pitrufquén death_no_crime headline:

| id | ratio | matched v3 headline (truncated) |
|---|---|---|
| 37419d21d3a013ff | 0.6224 | "Crimen de carabinero en Renca..." |
| a38630929ec688fd | 0.6224 | "Crimen de carabinero en Renca..." |
| 1323a8d861ee21bc | 0.6306 | "...robo y homicidio de un hombre...en Colina..." |
| a4f4e3157c03f74c | 0.6224 | "Crimen de carabinero en Renca..." |
| ae32fb5892c5830b | 0.6316 | "...robo y homicidio de un hombre...en Colina..." |
| 508983345ce5acb8 | 0.6425 | "...robo y homicidio de un hombre...en Colina..." |
| f97e2a7d99dcbd3e | 0.6008 | "...robo y homicidio de un hombre...en Colina..." |
| cb6fb95b0ae1ab32 | 0.6129 | "...robo y homicidio de un hombre...en Colina..." |
| 3b5385a04dd2da97 | 0.6316 | "Balance final de Fiestas Patrias..." |
| 8069a024228460fb | 0.6220 | "Balance final de Fiestas Patrias..." |
| 361cdb81361abd41 | 0.6347 | "Balance final de Fiestas Patrias..." |
| a010897e8fd57431 | 0.8548 | "PDI descarta homicidio tras hallar cadáver..." |
| 8856ad25a1520f59 | 0.8235 | "Balance final de Fiestas Patrias..." |

Pool file (scratchpad, not committed): `fid03-pool.json` (1380 rows).

### Step 3: spend precheck

Estimate: 1380 x $0.00025 = $0.345. `--spend-cap min(0.90, 5.00 - phase-36
spend so far)` = min(0.90, 5.00 - 0.171) = **0.90** (G-45). Estimate well
under the cap.

### Step 4: classify run

Cache: `fid03-cache.jsonl` (scratchpad, JSONL, one line per attempt, outside
data/). Run in 5 chunks (a system memory-pressure reaper killed the first
foreground invocation at 303/1380 rows; the orchestrator resumed with 4
further foreground chunks, no background monitors, each below its timeout).
Every row got exactly one classify call (no API_ERROR retries, no
redispatch): `303 + 265 + 345 + 301 + 166 = 1380` calls, matching
`cached_final=1380 uncached=0` on the final chunk (exit=0).

`classifier_blob_iter1: dcc33ead6c517787f9fde2858b06571702421f3c` (== the
36-06 shipped prompt blob at `pipeline/news/classifier.py`, confirmed via
`git hash-object`).

**Deviation (tooling defect, not fixed — reported per orchestrator
instruction):** `backfill_classifier_outage.SpendMeter.persist()` overwrites
`--spend-ledger` on every call rather than accumulating across separate
invocations of the same cache/cap. Because the classify run had to be split
into 5 process invocations (memory-pressure kill + resume), the ledger file
only ever reflects the *last* invocation's own total, not the cumulative
spend across all 5. This is in `pipeline/backfill_classifier_outage.py`
(shared with `backfill_classifier_outage.py --classify` and reused
as-is by `fid03_audit.py --classify`), not in `fid03_audit.py` itself, so it
is out of this plan's file scope and was not fixed here. Cumulative spend
below was computed by hand-summing the 5 per-invocation ledger snapshots
(`fid03-spend-chunk1.json`, `fid03-spend-chunk2.json`, `fid03-spend-chunk3.json`,
`fid03-spend.json` covering chunk 4, and the initial partial-run ledger
covering chunk 0/303 rows).

Per-chunk spend (USD, each ledger's own `total_usd`):

| chunk | rows classified | spend_usd |
|---|---|---|
| 0 (killed at 303/1380, partial) | 303 | 0.058800 |
| 1 | 265 | 0.043902 |
| 2 | 345 | 0.039619 |
| 3 | 301 | 0.037942 |
| 4 (final, cached_final=1380) | 166 | 0.020434 |
| **total** | **1380** | **0.200697** |

```
spend_usd: 0.2006
```

Phase-36 cumulative after 36-08: 0.171 (36-02 + 36-06) + 0.2006 = **0.3716**,
well under the USD 5 phase cap.

### Step 5: outcomes, would-publish, family distribution, vida share

```
outcome_split: {"ok": 622, "not_crime": 757, "parse_error": 1}
would_publish: 622
```

All 622 `ok` rows resolved to a would-publish item (commune resolvable,
centroid found, not editorial_filter) — zero drop at that stage.

Would-publish family distribution (n=622):

| family | n | share |
|---|---|---|
| vida | 318 | 51.13% |
| propiedad | 102 | 16.40% |
| robos_violentos | 57 | 9.16% |
| drogas | 42 | 6.75% |
| armas | 41 | 6.59% |
| incivilidades | 39 | 6.27% |
| sexuales | 16 | 2.57% |
| vif | 7 | 1.13% |

vida share of the would-publish pool: **51.13%** (318/622) — next to the
references V-07 (51%, pre-Granite) and G-18 (51.4%), and next to
`data/incidents/current.json`'s **execution-time** share, measured
2026-09-26 (787 incidents total, 511 vida = **64.93%**; NOT the stale 71.4%
figure from 36-RESEARCH.md). The would-publish pool's vida share (51.13%) is
materially lower than current.json's live share (64.93%), consistent with
the FID-02 finding that the Phase-36 category-level prompt reduces vida's
role as a catch-all outside the golden set too.

`pool_by_epoch: outage=1210 live=170` (recorded in Step 2 above; unchanged by
classification — this is a population-composition line, not an outcome
line).

### Step 6: back-off

Would-publish count (622) >= 50 on the first pass — **no back-off needed**.

```
as_of_final: 2026-09-26T01:11:57Z
```

## Task 3 — pending

--sample 50 --seed 3608 with --blind-out to follow.
