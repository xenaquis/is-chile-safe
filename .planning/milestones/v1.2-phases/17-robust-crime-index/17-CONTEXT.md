# Phase 17: Data Quality, Source Traceability & Methodology - Context

**Gathered:** 2026-06-18 · **Re-scoped:** 2026-06-18 (FOCUSED — see Scope Note)
**Status:** Wave 0 research COMPLETE (ran 2026-06-18 from local CL egress) —
see 17-WAVE0-RESEARCH-A.md (S1/S4) + 17-WAVE0-RESEARCH-B.md (S2/S3/S5). Discuss artifact
pre-staged for autonomous run. Ready to plan.
**Milestone:** v1.2 (data-correctness hardening before milestone close)

> ## ⚠️ SCOPE NOTE (read first — autonomous run)
> This phase was RE-SCOPED with the user on 2026-06-18 to a **focused
> data-quality + source-traceability + methodology** pass. The original
> ambitious plan (exposure-adjusted **composite index**, homicide metric
> switch in the UI, `featured_rates`→7-metric **schema migration**,
> index-driven choropleth) is **DEFERRED to a future phase (proposed Phase 18,
> "Composite Crime Index")** and is **OUT OF SCOPE here**. Do NOT change the
> displayed metric, the map choropleth metric, or the data schema in this phase.
> Wave 0 already validated the sources for that future work; this phase makes
> the *current* site correct, explicit, and traceable to the right sources, and
> commits reproducible static snapshots of the new sources for later use.

<domain>
## Phase Boundary

Make every quantitative figure on the site **verifiably correct** and
**traceable to its authoritative source**, and rewrite the methodology so the
source of every number is explicit and clickable — without re-architecting the
metric. Motivation (confirmed against live repo data `data/cead/comunas/*.json`
and Wave 0):

- **Traceability gap.** `methodology.astro` cites the CEAD host as
  `cead.ministeriointerior.gob.cl`, but the scraper actually uses
  `cead.minsegpublica.gob.cl` (`pipeline/cead/client.py`). The cited source is
  wrong — the headline "source of truth" claim is itself untraceable. Fix.
- **Single-source today, multi-source reality.** The site presents only CEAD,
  but Wave 0 confirmed the *correct* authoritative sources for homicide (SPD VHC,
  comuna-level), secuestro (Fiscalía/Ministerio Público, regional), and an
  exposure proxy (SII empresas/trabajadores por comuna). These must be named,
  attributed, and (as static snapshots) made reproducible — even though the
  displayed metric does not change yet.
- **Known data-quality artifacts to verify, not silently carry:**
  - Floating-population denominator (Providencia property rate 4,423 vs
    Coyhaique 1,018) — mathematically valid, must be *explained* in methodology.
  - Small-count + partial-year (San Joaquín homicide 2025=1 vs ~10/yr average) —
    the partial-year guard exists for sparklines but the headline can bypass it;
    verify every surfaced figure flags partial years.
  - Drug scope (CEAD "Drogas" = Ley 20.000 grupo 401 only; consumption under
    Incivilidades grupo 702) — already audited (quick-260616-klv); ensure the
    methodology states it.
- **CEAD measure semantics now known (Wave 0 S4):** `tipoVal` 1=denuncias,
  2=detenciones, 3=aprehendidos, additive; casos policiales = `1,2` (what the
  site shows). Methodology must state this precisely.

## In Scope

1. **Data-quality verification (DQ-01).** Cross-check each surfaced
   metric/series against its authoritative source using the Wave 0 facts and
   the offline CEAD cache; re-verify the four anomalies (Providencia,
   Lo Barnechea, San Joaquín, Recoleta); range/sanity checks; confirm
   partial-year flags are present on every surfaced figure. Produce a
   traceable `17-DATA-QUALITY.md` report (pass/fail per check, with evidence).
2. **Source registry + correct attribution (DQ-02).** One canonical
   `data/SOURCES.md` (or `.planning` registry) listing, per data class, the
   authoritative source, exact endpoint/URL, vintage/coverage, licence, and the
   measure semantics — CEAD (multi-measure, casos policiales), SPD homicide
   (VHC xlsx, comuna), SII exposure (PUB_COMU.xlsb), Fiscalía secuestro
   (regional). Fix the wrong CEAD host everywhere it appears.
3. **Methodology rewrite, bilingual, clickable sources (DQ-03).** Rewrite
   `site/src/pages/methodology.astro` + `site/src/pages/es/metodologia.astro`:
   correct CEAD host; state casos-policiales (`tipoVal=1,2`) semantics;
   document partial-year handling, low-count caveat, drug scope, and the
   floating-population denominator caveat; name SPD/SII/Fiscalía as the
   authoritative sources for the figures they back; add a **clickable link to
   every cited source**. Bilingual parity; legal-safe tone (never label a
   territory "dangerous/safe" in absolute terms; always attribute).
4. **Reproducible static source snapshots (DQ-04).** Commit small, normalized,
   versioned snapshots of the new sources (homicides per comuna/year from SPD;
   empresas+trabajadores per comuna/year from SII; secuestro per región/year
   from Fiscalía) under `data/`, each with a reproducible fetch/normalize script
   in `pipeline/` and source attribution. Reference-only — NOT wired to the UI
   metric, NOT migrating the CEAD schema.

## Out of Scope (DEFERRED to proposed Phase 18 — Composite Crime Index)

- Exposure-adjusted **composite index** + the SII denominator formula.
- **Homicide metric switch** to SPD in the map/panel (display change).
- `featured_rates` → 7-metric **schema migration** (lesiones 103/104/105,
  secuestro metric, dropping the `vida` aggregate).
- Index-driven choropleth, dual index+count display, multi-measure aggregation
  in the displayed number.
- News-layer work (that is **Phase 16**, runs AFTER this phase).
</domain>

<decisions>
## Decisions (locked with user 2026-06-18)

- **D-SCOPE:** focused data-quality/traceability/methodology pass; composite
  index + schema migration deferred to Phase 18. No displayed-metric change.
- **D-ORDER:** this phase (17) runs BEFORE Phase 16 (news) so the source
  registry + methodology are authoritative before news adds its own attribution.
- **D-SOURCES (from Wave 0, authoritative):**
  - Homicide truth = SPD VHC (`prevenciondehomicidios.cl`, comuna-level,
    2018–2025). CEAD grupo 101 mixes homicidio+femicidio and ignores
    `subgrupo[]` → cite SPD as the authoritative homicide source.
  - Secuestro = Fiscalía/Ministerio Público (regional granularity only;
    absent from CEAD taxonomy entirely). Region-level attribution.
  - Exposure proxy = SII `PUB_COMU.xlsb` (trabajadores dependientes / FTE per
    comuna, 2005–2024) — snapshot now for Phase 18; document the HQ/domicile
    caveat.
  - CEAD remains the source for the displayed incidence rates (casos
    policiales, `tipoVal=1,2`, `medida=2`), host = `cead.minsegpublica.gob.cl`.
- **D-VERIFY:** use **BrowserOS** to visually verify the rewritten methodology
  pages (EN+ES) render with working clickable source links, and that sampled
  commune/ranking figures still cite source+year correctly.
</decisions>

<unknowns>
## Wave 0 — research spikes — COMPLETE

All Wave 0 spikes ran 2026-06-18 from local Chilean egress (the cloud sandbox
403s on every CL gov host). Results in 17-WAVE0-RESEARCH-A.md (S1/S4) and
17-WAVE0-RESEARCH-B.md (S2/S3/S5). Confirmed: CEAD grupo/subgrupo catalog
(17-CEAD-CATALOG.json), tipoVal additivity + semantics, SPD comuna-level
homicide dataset, SII comuna exposure dataset, Fiscalía secuestro (regional).
No open research blockers for the focused scope. (Open for Phase 18 only:
S5b — comuna-level secuestro from the Fiscalía BED app.)
</unknowns>

<approach>
## Proposed wave structure

- **Wave 1 — Verify:** build `17-DATA-QUALITY.md` — automated/offline checks of
  each surfaced metric vs source (use `pipeline/cache/` + Wave 0 facts);
  re-verify the 4 anomalies; partial-year + range sanity. (No code change to
  displayed data; this is the evidence base.)
- **Wave 2 — Source snapshots + registry:** reproducible fetch/normalize
  scripts for SPD/SII/Fiscalía → small normalized JSON snapshots in `data/` +
  attribution; write the canonical source registry (`data/SOURCES.md`).
- **Wave 3 — Methodology rewrite (EN+ES):** correct host, multi-source naming,
  clickable source links, all caveats; bilingual parity; legal-tone check
  (reuse validator #9 forbidden-language gate).
- **Wave 4 — Verify + gate:** chained build+validate (OneDrive desync — one
  command); BrowserOS visual check of both methodology pages + sampled figures;
  `17-VERIFICATION.md`.

## Cross-cutting risks
1. **Legal tone** (highest) — methodology must never assert absolute safety;
   always attribute. Reuse the forbidden-language validator.
2. **Bilingual drift** — EN/ES methodology must stay in parity.
3. **OneDrive build desync** — always chain build+validate in one command
   (see memory: onedrive-build-artifacts-desync).
4. **Snapshot size** — commit normalized JSON, not the raw multi-MB xlsx/xlsb.
</approach>
