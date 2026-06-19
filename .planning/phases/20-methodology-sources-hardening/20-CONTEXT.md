# Phase 20: Methodology & Sources Hardening - Context

**Gathered:** 2026-06-19
**Status:** Ready for planning
**Mode:** Seeded from v1.3-METHODOLOGY-SPEC.md (the build target) + review findings

<domain>
## Phase Boundary

Make every quantitative figure on the site explained + sourced+linked + caveated, EN/ES parity, with CI guards to keep it that way. The build target is `.planning/v1.3-METHODOLOGY-SPEC.md` (figure registry F1–F12+F15, expanded SOURCES.md spec, completeness checklist).

Requirements: MTH-01..04, SRC-01..05 (9 total). **Definition of done:** zero displayed figure without a `data/SOURCES.md` registry entry or labeled editorial-parameter note.
</domain>

<decisions>
## Implementation Decisions (locked)

- **Already done in Phase 19 — do NOT redo:** F2/TD-01 (methodology unweighted-mean wording), F7 trend `#trend-formula` anchor (MC-06 was in P19 SEO/i18n? verify — if not anchored, do it here), F10 drogas scope on commune FamilyBreakdownBars (MC-09). Re-confirm these landed; only act if missing.
- **Sources scope (DECISIONS b):** Add INE, ENUSC, Subsecretaría de Prevención del Delito (SPD parent) as FIRST-CLASS source classes. SII / Fiscalía-secuestro / SPD-VHC stay STUBS (deferred to Phase 18) — do not promote.
- **Editorial parameters** (5% trend threshold, 3-year window, 10k low-pop exclusion) are documented as EDITORIAL with rationale — not invented external sources.
- **No new displayed metric/index** (reserved for Phase 18). This phase is explanation + sourcing only — no data recompute, no schema change.
- **Editorial guardrail:** do NOT invent figures or URLs. If an official URL is uncertain, mark `[verify URL]` rather than fabricate. Legal-safe tone throughout.

### Claude's Discretion
Exact methodology H2 sub-section wording, where each caveat renders (inline vs MethodologyCaveat component), CI validator implementation (extend existing validators in site/ + a pipeline spot-check).
</decisions>

<code_context>
## Figure registry → work (from v1.3-METHODOLOGY-SPEC.md Part 1)

- **F3 (MTH-01):** per-family `familyNationalMean` at `crime-ranking/[crime].astro:137-141` + es — add inline caveat "unweighted commune mean" + explain in methodology.
- **F4 (MTH-01):** per-region breakdown mean at `crime-ranking/[crime].astro:143-165` + es — caveat + methodology sentence.
- **F5:** national/regional time-series ARE population-weighted (correct) — make the weighting distinction explicit vs F2 to avoid confusion (methodology trend/series section).
- **F6 (MTH-02):** LevelChip 1–5 at `commune/[slug].astro:82-86` + es — add methodology "Incidence level classification" sub-section (relative 5-tier from build-time non-low-pop distribution; not a safety verdict).
- **F8:** choropleth 5-class scale — cross-reference F6 in methodology "Map".
- **F7 (MTH-03 + SC-05):** trend 3-yr window + 5% threshold — ensure `#trend-formula` anchor exists + linked; document 5%/3-yr as editorial in SOURCES.md.
- **F9 (SC-06):** <10k low-pop exclusion at methodology:292-294 — add SOURCES.md provenance note (editorial + INE small-area convention).
- **F10 (MTH-03):** drogas = Ley 20.000 grupo 401 — ensure scope note renders on commune FamilyBreakdownBars (verify P19 didn't already; see cead-drug-family-taxonomy memory).
- **F11 (SRC-02/SC-03):** ENUSC cited at methodology:214 / metodologia:217 — add `## ENUSC` to SOURCES.md + inline citation link.

## Expanded SOURCES.md (Part 2) — new classes to author
- **INE (SRC-01/SC-01,SC-02):** population/projections; per-100k denominator + <10k rule; official URL + measure semantics + vintage + fetch script (`pipeline/scripts/fetch_ine_population.py`) + third-party-mirror caveat (`bastianolea/censo_proyecciones_poblacion` is a MIRROR — document official INE backing).
- **ENUSC (SRC-02/SC-03):** cifra-negra/underreporting; URL, publisher (SPD/MinInterior), measure semantics, vintage, licence.
- **SPD parent (SRC-03/SC-04,SC-07):** Subsecretaría de Prevención del Delito = parent of CEAD + taxonomy authority; portal seguridadpublica.gov.cl; CEAD grupo/subgrupo taxonomy provenance (ajax_2.php seleccion=9). Chain of authority.
- **Editorial parameters (SRC-04/SC-05,SC-06):** 5% trend threshold, 3-yr window, 10k exclusion — labeled editorial note.

## CI guards (MTH-04 + SRC-05)
- Forbidden-language validator (already exists as forbidden-language.mjs — verify it's gated; extend if needed) — no non-attributed absolute "safe/dangerous"/"seguro/peligroso".
- INE population spot-check: compare ≥5 commune populations vs official INE (pipeline test or validator).
- methodology.astro ↔ es/metodologia.astro structural H2 parity (7 H2 each per spec Part 3).

## Canonical References
- `.planning/v1.3-METHODOLOGY-SPEC.md` (THE build target — figure registry + SOURCES spec + checklist)
- `.planning/v1.3-REVIEW-FINDINGS.md` (MC/SC finding detail + file:line)
- `data/SOURCES.md` (current registry to expand)
- Memories: `cead-drug-family-taxonomy`, `crime-rates-already-per-100k`, `i18n-localized-slug-pitfall`, `onedrive-build-artifacts-desync`.
</code_context>

<specifics>
## Hard constraints (execution)
- OneDrive build desync: ALWAYS chain `cd site && npm run build && npm run validate` in ONE command.
- Crime rates are ALREADY per-100k denuncia rates — never rescale (memory crime-rates-already-per-100k).
- Legal-safe tone; EN/ES parity (7 H2 each in methodology); static-JSON store; no new metric.
- Verify: build green + 12/12 (13/13 if new validator) validators + pipeline pytest green; figure registry shows zero orphans.
</specifics>

<deferred>
## Deferred Ideas
- SII / Fiscalía-secuestro / SPD-VHC first-class promotion + F13/F14 → Phase 18.
- Composite index / new metrics → Phase 18.
</deferred>
