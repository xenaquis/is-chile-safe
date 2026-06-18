# Phase 17: Robust Crime Index & Metric Redesign - Context

**Gathered:** 2026-06-18
**Status:** Wave 0 research COMPLETE (ran 2026-06-18 from local CL egress) —
see 17-01-SUMMARY.md (S1/S4) + 17-02-SUMMARY.md (S2/S3/S5). Ready to plan Wave 1.
**Milestone:** proposed v1.3 (v1.2 ends at Phase 16 / News Activation)

<domain>
## Phase Boundary

Rebuild how the map and rankings construct, weight, and validate crime data,
because the current per-resident rate produces **misleading signals**. Confirmed
against live repo data (`data/cead/comunas/*.json`):

- **Denominator / floating-population artifact.** Rate = CEAD police cases per
  100k *resident* population (`medida=2`, `tipoVal=1,2`). Property-crime rate
  2024: **Providencia 4,423** (pop 164k) vs **Coyhaique 1,018** (pop 62k).
  Providencia is a commercial/office hub whose daytime population is ~3–4× its
  residents; crime against that floating mass is divided by the small resident
  base, inflating the rate. The figure is mathematically valid but wrong as a
  personal-risk signal.
- **Small-count + partial-year artifact.** San Joaquín homicide series (counts):
  2020=11, 2021=11, 2022=12, 2024=11, **2025=1**, 2026=2. The "1 case in 2025"
  the user saw is an *unconsolidated* current year being surfaced as a headline,
  not a real drop. The commune averages ~10 homicides/year. `partial`/
  `latestCompleteYear` logic exists for sparklines but the homicide *headline*
  bypasses it.
- **Scope artifact (drugs).** CEAD "Drogas" = Ley 20.000 only (trafficking);
  consumption is filed under Incivilidades. Denuncias undercount drug activity
  that is overwhelmingly police-detected (aprehensiones).

## In Scope

1. **New 7-metric taxonomy** (drop the aggregated `vida`/Life-crimes family):
   a) homicidio  b) lesiones  c) propiedad  d) VIF  e) drogas  f) armas
   g) secuestros. `lesiones` and `secuestros` are NOT scraped today and require
   new CEAD subgroup acquisition (`grupo[]=<id>`).
2. **Homicide source switch → SPD** (`prevenciondehomicidios.cl/cifras-oficiales`),
   the consolidated official figure (Carabineros + PDI + SML + Fiscalía),
   replacing CEAD subgroup-101 denuncias as the homicide source.
3. **Exposure-adjusted composite index** correcting the resident-denominator
   problem using a daytime/economic-activity proxy (candidate: SII firms +
   workers per commune, national coverage).
4. **Multi-measure aggregation** — denuncias + detenciones + aprehendidos
   (`tipoVal` variants), normalized per offence to avoid double-counting.
5. **Statistical robustness** — small-count suppression (no ranking of communes
   below N cases/year), multi-year smoothing (3-yr moving average for homicide),
   and partial-vs-complete-year separation surfaced on EVERY figure, not just
   sparklines.
6. **Frontend** — map choropleth driven by the new index; dual display
   (index + absolute count); methodology rewrite (3 sources); bilingual copy;
   removal of `vida` aggregate from the primary taxonomy.
7. **Validation** — re-check the four anomalies (Providencia, Lo Barnechea,
   San Joaquín, Recoleta) post-redesign; range sanity; per-figure source
   attribution; legal copy (never label a territory "dangerous/safe" absolutely).

## Out of Scope

- News-layer activation (Phase 16).
- Keeping Incivilidades / Robos Violentos as PRIMARY metrics — decision was the
  7 exact metrics. They may remain as scraped data but are demoted from the
  headline taxonomy.
</domain>

<decisions>
## Direction decisions (locked with user 2026-06-18)

- **D-IDX (denominator):** build an **exposure-adjusted index**, not just
  per-resident rate + caveats. Highest robustness; requires an exposure proxy
  (S3). The index MUST be explainable and legally safe — replacing one
  misleading number with an opaque one is failure.
- **D-HOM (homicide source):** **switch to SPD** (prevenciondehomicidios.cl) as
  the homicide source of truth. Cross-reference/fallback to CEAD where SPD
  granularity is missing.
- **D-TAX (taxonomy):** **the 7 exact metrics**; drop the `vida` aggregate.
  `lesiones` + `secuestros` are new acquisition work.
- **D-AGG (measures):** aggregate **denuncias + detenciones + aprehendidos**.
  Hard constraint: normalize per offence — a denuncia and its aprehensión can be
  the same event; summing rates naively double-counts.
</decisions>

<unknowns>
## Wave 0 — Research spikes (BLOCKING, need a live endpoint)

### Network reality (2026-06-18)
From THIS remote execution environment, all four Chilean government hosts return
**HTTP 403** to a plain request (CEAD, SPD/prevenciondehomicidios, SII, INE) —
the egress IP is geofenced/filtered. TCP connects; the gateway rejects. The
production scraper succeeds from **GitHub Actions** (2026 partial data exists in
the repo), so the spikes must run from Actions or a local Chilean/clean egress,
NOT from this sandbox. Spike scripts are committed ready-to-run; see runbook.

### S1 · CEAD subgroup IDs for `lesiones` and `secuestros`
- Mechanism CONFIRMED (Phase 14): subgroup selected via `grupo[]=<id>`;
  `subgrupo[]` is silently ignored. Homicide = `grupo[]=101` under `familia[]=1`.
- UNKNOWN: the `grupo[]` IDs for lesiones (likely under familia 1) and secuestros
  (may live under a family NOT in the current 1–7 set — delitos contra la
  libertad). Must enumerate the CEAD group catalog and probe for non-zero rows.
- Experiment: `pipeline/experiments/test_subgroup_discovery.py`.

### S2 · SPD homicide source (`prevenciondehomicidios.cl`)
- Returns 403 to plain GET; needs the CEAD-style header/cookie warmup pattern.
- UNKNOWN: comunal vs only regional/national granularity; years covered;
  downloadable dataset (CSV/API) vs charts-only; exact source institutions.
- RISK: if SPD homicide is only regional, the commune choropleth cannot use SPD
  directly — fall back to CEAD at commune level, SPD at region/national.
- Action: replicate `make_cead_session()` header approach against SPD; inspect
  page + network calls; document structure. (Spike script TBD after S1 lands.)

### S3 · Exposure proxy (the index denominator)
- Candidate: **SII "empresas y trabajadores por comuna"** — open data, national,
  346 communes; proxy for daytime/economic activity. Alternative: INE Censo
  daytime flows (limited); EOD (Gran Santiago only — rejected, not national).
- UNKNOWN: download format/URL, latest year, normalization choice (workers,
  firms, or a blend; how to combine resident + daytime into one denominator).
- Action: source the dataset, commit a static copy to `data/`, define the
  adjustment formula. Document the formula in plain language for the methodology
  page (explainability is a hard requirement of D-IDX).

### S4 · CEAD measure codes (denuncias / detenciones / aprehendidos)
- Current scraper uses `tipoVal="1,2"` (= casos policiales). UNKNOWN: the exact
  tipoVal codes that isolate denuncias vs detenciones vs aprehendidos, and
  whether they can be requested separately in one call.
- RISK: double-counting (D-AGG constraint). Map which measures are additive per
  offence before designing the index.
- Experiment: folded into `test_subgroup_discovery.py` (tipoVal probe section).
</unknowns>

<approach>
## Proposed wave structure (post-Wave-0)

- **Wave 1 — Pipeline:** extend CEAD client to fetch 3 measures × new subgroups
  + counts (`medida=1`); SPD scraper module; ingest exposure proxy (static).
- **Wave 2 — Index:** composite formula = per-metric normalized scores +
  exposure-adjusted denominator + small-count suppression + 3-yr smoothing;
  compute per comuna/region/national.
- **Wave 3 — Schema:** `featured_rates` → 7 metrics, each
  `{rate, count, index, source, completeYear, partial}`; version bump + migration.
- **Wave 4 — Frontend/map:** index-driven choropleth; dual index+count display;
  partial-year fix everywhere; methodology rewrite (CEAD multi-measure + SPD +
  exposure proxy); bilingual copy; remove `vida` aggregate from taxonomy.
- **Wave 5 — Validation:** re-verify the 4 anomalies; range sanity; source
  attribution; legal-tone audit.

## Cross-cutting risks
1. **Index interpretability / legal safety** (highest) — must be explainable and
   never label territory as absolutely dangerous/safe.
2. **Double-counting** across denuncias/detenciones/aprehendidos.
3. **SPD granularity** possibly regional-only.
4. **Exposure proxy** national availability + normalization defensibility.
</approach>

<notes>
## Adjacent finding — deploy of code-only changes (separate quick)

Cloudflare auto-deploy on push is OFF (DEPLOYMENT.md §4); the only build trigger
is the data-change Deploy Hook. Code-only commits (e.g. the `lu4` dynamic
ranking-table sort, merged to master `b2ad8f8`) never rebuild production. A
`deploy-on-code-push` workflow (ping the hook when `site/**` changes on the
default branch) unblocks this class of change. Tracked separately from Phase 17.
</notes>
