---
phase: 36-classification-fidelity-attribution
plan: 08
status: Task 3 complete. FID-03 = FAILED/Partial (37/50, vida 19/25). 36-09 ships
  iteration 2 (FID-02 PASS, improves on live G-18). Owner question recorded
  for deferred-live.
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

## Task 3 — Blind 50-item audit + mechanical decision + G-33

### Step 1: sample

`--sample 50 --seed 3608` from the 622-item would-publish pool (Task 2).
`--blind-out` (pass-1 reviewer file, `fid03-blind.json`, scratchpad): decoded
every news.google.com URL with `decode_gnews_url(url, session=requests.Session()`
(User-Agent = `fulltext.USER_AGENT`), 1.5 s between decode calls (G-43/BF-03).

```
publisher_url_decoded: 29/29
```

All 29 Google-News rows in the sample decoded to a usable non-Google
publisher URL; the other 21 rows carried their own outlet URL.

### Step 2-3: blind two-pass audit (fresh opus reviewer) + score

Pass 1 (title/description/url/publisher_url/outlet only, frozen before pass 2):
`fid03-pass1.json` (scratchpad). Pass 2 + q3/basis verdicts: `fid03-verdicts.json`
(scratchpad, 50 items).

```
agreement: 37/50
agreement_by_basis: source=37/49 headline_only=0/1
vida_precision: 19/25
publisher_url_decoded: 29/29
**Decision**: FAILED
```

Wilson 95% interval for 37/50 = 0.74: **[0.6045, 0.8413]**.

vida share of the would-publish pool (Task 2): **51.13%** (318/622), vs
V-07 (51%), G-18 (51.4%), and `current.json`'s execution-time share (64.93%,
2026-09-26).

Informational only, not gated (NB-01):

```
sample_by_epoch: outage=50 live=0
agreement_by_epoch: outage=37/50
```

Every one of the 50 sampled would-publish items happened to be drawn from
the outage-era stage (`classifier_none`); the live-era stages
(`low_confidence`/`commune_null`/`resolver_fail`) contributed 170/1380 to the
pool but 0 to this seed's sample, so `agreement_by_epoch` has no `live` row.

### Per-item verdicts (id, q1, pass-1 family, predicted_family, q3, basis, commune)

| id | q1 | pass-1 family | predicted_family | q3 | basis | commune |
|---|---|---|---|---|---|---|
| ada54741b94f346b | T | incivilidades | vida | F | source | Copiapó |
| 513cf06471c18d14 | T | vida | vida | T | source | Villarrica |
| 9cc7927193ebd716 | T | vida | vida | T | source | Villarrica |
| 2410d3f0c79bec40 | T | vida | vida | T | source | San Clemente |
| 122588999e864284 | T | vida | vida | T | source | Pitrufquén |
| 4aab48612f1a0076 | F | - | incivilidades | F | source | - |
| 8f733e6178cad355 | T | sexuales | sexuales | T | source | San Gregorio |
| 6f6de561a9daf593 | T | vif | vif | T | source | Valparaíso |
| b2be36c516b11de5 | T | vida | vida | T | source | Renca |
| 7f5e1556ee940a1a | F | - | incivilidades | F | source | - |
| bca5a29492c87553 | T | vida | vida | T | source | Limache |
| 84863646f1b7770c | T | propiedad | propiedad | T | source | Puerto Montt |
| e2b7c21c949cb633 | T | robos_violentos | vida | F | source | Santiago |
| a37146a50219cb46 | T | incivilidades | incivilidades | T | source | Valparaíso |
| e3e413c0fc4bf11d | T | robos_violentos | robos_violentos | T | source | Santa Bárbara |
| 9cc624285ab1d13d | T | vida | armas | F | source | Iquique |
| 5d003b5a80fe22ed | T | vida | vida | T | source | Quilicura |
| e52e6efbf6e9ebaa | F | - | vida | F | source | - |
| b6a367097ea9f7fe | T | vida | vida | T | source | Renca |
| c231d23c42a80b6b | T | incivilidades | incivilidades | T | source | San Bernardo |
| b5602749bb1399ea | T | sexuales | sexuales | T | source | Coquimbo |
| 30c59c9b646f9501 | T | vida | vida | T | source | Tomé |
| bf7244684028d6c3 | T | vida | vida | T | source | La Serena |
| 005404cacc326dd1 | T | propiedad | propiedad | T | source | Antofagasta |
| 052aca6214c05714 | T | vida | vida | T | source | Vicuña |
| 1a262ff906e43016 | T | robos_violentos | robos_violentos | T | source | Talca |
| 0a1230100e633948 | T | propiedad | propiedad | T | source | Santiago |
| 0638a95af967e449 | T | vida | vida | T | source | Maipú |
| 920e33c81d88b61d | T | vida | vida | T | source | La Granja |
| 8e0b40a0c2565036 | T | drogas | drogas | T | source | Calama |
| 618e18df3fbcc186 | T | vida | armas | F | source | Iquique |
| f2f2572c7b83e04a | F | - | vida | F | source | - |
| a733cb72fbe98ae8 | T | incivilidades | incivilidades | T | source | La Pintana |
| b9ffd5bfad203e72 | T | robos_violentos | robos_violentos | T | source | Puerto Montt |
| 4ff09aaae6b39205 | F | - | vida | F | headline_only | - |
| c8beba4543c0df79 | T | propiedad | propiedad | T | source | La Serena |
| 367d9da33e8cfb98 | T | drogas | drogas | T | source | Los Vilos |
| 2e805f358affb263 | T | vida | vida | T | source | Iquique |
| 5636151a9ca9cd5f | T | drogas | drogas | T | source | Alto Hospicio |
| 4024ecf88081284a | T | vida | vida | T | source | Calama |
| e1b1e7306c300d30 | T | vida | vida | T | source | Quillota |
| fbac2cdeca736073 | T | drogas | drogas | T | source | Vicuña |
| 52f94d3697770c0a | T | vif | incivilidades | F | source | Monte Patria |
| 089a55faa420633c | T | vida | vida | T | source | Limache |
| cdf78cced7e62190 | T | vida | vida | T | source | Santiago |
| 8335c4ec003d2927 | T | vif | incivilidades | F | source | Monte Patria |
| 207d2f3e3019fb60 | T | vida | vida | T | source | La Granja |
| 6ce9e3ecc4c99384 | F | - | armas | F | source | - |
| 7d591a52e4d61c1d | T | propiedad | propiedad | T | source | Estación Central |
| b98ecc41f65151b2 | F | - | vida | F | source | - |

### Failure categories (auditor notes)

**q1 false, 7 (all disagreements — none are family mismatches, they are
whole-item "not a discrete crime incident" calls):**

- `4aab48612f1a0076` — court orders prison transfer of an already-recaptured
  juvenile homicide convict (penitentiary procedure, not a new incident).
- `7f5e1556ee940a1a` — municipal official's commentary about a tiktoker's
  expulsion (statement, not a crime case).
- `e52e6efbf6e9ebaa` — government pensions granted to the Bruma fishermen's
  relatives (policy/aid news).
- `f2f2572c7b83e04a` — neighbours' protest against a 2008 case's statute of
  limitations (protest, not a new incident).
- `4ff09aaae6b39205` — elderly man's body found in Pitrufquén, no alleged
  crime stated (headline_only basis, publisher 403).
- `6ce9e3ecc4c99384` — mayor requesting police/military support after
  reported gunfire (institutional request, not a specific case).
- `b98ecc41f65151b2` — drunk-driving crash injuring eight, counted as an
  accident per the category-level non-crime rubric (traffic accidents are
  non-crime even with a detained driver).

q2 false: 0. q4 true (title_en changes/adds facts): 0 — every sampled
title_en was a faithful translation, no kinship-guard fallback fired.

**6 family disagreements (all q1=true, q3=false):**

- `ada54741b94f346b` — vida vs incivilidades: official charged with
  facilitating a homicide convict's escape; the offence is evasion, not the
  (prior) homicide.
- `e2b7c21c949cb633` — vida vs robos_violentos: person forced into a car
  while carrying cash (kidnapping for gain reads as violent robbery, not a
  vida case).
- `9cc624285ab1d13d`, `618e18df3fbcc186` — armas vs vida: two Iquique
  shootings with wounded victims; the model calls them armas (weapons
  offence), the reviewer reads vida (attempted homicide) as the lead charge.
- `52f94d3697770c0a`, `8335c4ec003d2927` — incivilidades vs vif: armed
  threat + phone theft against an ex-cohabitant in breach of a restraining
  order (Monte Patria); the model calls incivilidades, the reviewer reads
  vif (intimate-partner context). These two ids are duplicate reports of the
  **same** underlying case (also true of `513cf06471c18d14`/`9cc7927193ebd716`,
  the Villarrica double killing — both correctly agreed as vida).

### Step 3: extra iteration (BF-07) — evaluated on golden v3 first, reverted

36-06 iteration 3 (commit `e5f866e`) added category-level edits targeting
exactly these failure classes (procedural/statement non-crime, routine death
inquiry, shooting=vida / partner-threat=vif / kidnapping-for-gain=robos_violentos
/ evasion=incivilidades). Per the plan's declared order (BF-07: assert the
re-classification cache's blob equals the prompt that ships, and per G-38's
FID-02 gate), iteration 3 was evaluated on golden_set_v3 **first**: it
**FAILED FID-02** (not_crime 18/24 = 0.75, below the 20/24 iteration-2
result and below the FID-02 gate). Because a prompt that fails FID-02 cannot
ship, iteration 3 was **reverted** (`git revert e5f866e` → commit `c0c58b9`;
`pipeline/news/classifier.py` blob back to `dcc33ead6c517787f9fde2858b06571702421f3c`,
confirmed via `git hash-object`). The seed-3609 re-audit of Task 3's decision
rule ("at most ONE extra category-level prompt iteration... re-run FID-02
and this audit with seed 3609") is **NOT run**, because it would audit a
prompt that cannot ship — auditing it would not change the decision.

### Final decision

**FID-03 = FAILED/Partial** with numbers (37/50 agreement, min 43; vida
precision 19/25, min ceil(0.85*25)=22). 36-09 ships classifier.py at
iteration 2 (blob `dcc33ead6c517787f9fde2858b06571702421f3c`) regardless,
because FID-02 passed on that iteration (20/24) and it improves materially
on the live G-18 prompt's q1 (43/50 here — counting only the 43 items where
q1=true — vs G-18's measured 40/50).

Owner question, recorded for the deferred-live list:

> FID-03 failed (37/50; vida precision 19/25; non-crime procedural/institutional
> news and vida/armas/vif boundaries). Options: accept, extend the golden set
> with these classes and iterate under a new pre-declared rule, or evaluate
> another model.

### G-33 (2026-09-26, orchestrator)

**G-33** — FID-03 outcome: FAILED/Partial (agreement 37/50 vs the declared
≥43/50 gate; vida precision 19/25 vs the declared ≥ceil(0.85·25)=22 gate).
The single permitted extra iteration (36-06 iteration 3, commit `e5f866e`,
targeting exactly the observed failure classes) was evaluated on
golden_set_v3 first per FID-02/G-38 and failed there (18/24), so it was
reverted rather than re-audited at seed 3609 (auditing a prompt that cannot
ship would not change the decision). 36-09 ships classifier.py iteration 2
(blob `dcc33ead6c517787f9fde2858b06571702421f3c`) because FID-02 passed on
it and it improves on the live G-18 prompt (q1 43/50 vs 40/50); FID-03's
failure is recorded, not gating, per the plan's own "36-09 may still ship if
FID-02 passed" rule. Granite-era re-classification (2026-07-27..09-04)
stays **NO** in this milestone — the owner default (directive "Re-classify
Granite-era published incidents") is applied unchanged by this audit's
outcome, and the FID-03 failure is added to the deferred-live list as the
owner question above (accept / extend golden set + new pre-declared rule /
evaluate another model).
