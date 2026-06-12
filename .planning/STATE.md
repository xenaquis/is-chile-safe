# STATE — Chile Safety Map (ischilesafe.com)

_Last updated: 2026-06-12_

## Project Reference

**Core value**: Un mapa nacional interactivo con datos delictivos oficiales reales por comuna, servido en páginas estáticas bilingües que Google indexa — si el mapa con datos CEAD reales y las páginas SEO funcionan, el resto puede esperar.

**Current focus**: Phase 1 — Data Foundation

## Current Position

**Phase**: 1 — Data Foundation
**Plan**: Not started
**Status**: Not started
**Progress**: ░░░░░░░░░░ 0% (0/6 phases complete)

## Performance Metrics

| Metric | Value |
|--------|-------|
| Phases complete | 0/6 |
| Requirements mapped | 32/32 |
| Plans created | 0 |
| Plans complete | 0 |

## Accumulated Context

### Key Decisions
- Astro 6.4.x + React islands for pre-rendered static HTML (SEO indexability mandatory)
- JSON in repo as data store — no backend/DB; GitHub Actions cron commits trigger Cloudflare Pages via Deploy Hook only (never Git auto-build)
- DeepSeek v4-flash for RSS classification; `deepseek-chat` deprecated 2026-07-24 — never commit that model ID
- Commune canonical list (346 items) must be fixed in prompt at temperature 0.0 to prevent LLM geolocation hallucination
- Rate per 100,000 inhabitants is the single canonical metric; raw counts must never appear in rankings
- Programmatic pages deploy in batches of 10–20 first; GSC indexing confirmed before generating all 346

### Critical Pitfalls to Avoid
- Thin programmatic content → Google deindexing (recovery 4–8 weeks)
- GitHub Actions → Cloudflare Pages infinite rebuild loop (burns 500 free builds/month)
- LLM assigning incidents to wrong communes (use closed-list classification)
- Frequency vs. rate ranking error (bake `rate_per_100k` into schema from day 1)
- CEAD endpoint silently returning wrong data (validate 346-commune count + key presence after every scrape)

### Research Flags for Planning
- Phase 1: Live CEAD endpoint validation needed — confirm exact POST parameter names and current response field names before implementation
- Phase 5: RSS feed URLs for T13, 24Horas, Meganoticias, SoyChile unconfirmed — design per-feed graceful fallback

### Todos
- (none yet — populated during planning)

### Blockers
- (none)

## Session Continuity

**Last session**: 2026-06-12 — Project initialized; roadmap created
**Next action**: `/gsd:plan-phase 1` — Plan Phase 1: Data Foundation
**Resume prompt**: Start Phase 1 planning. CEAD scraper (DATA-01..04). Run live endpoint validation before writing pipeline code — confirm POST parameters and response schema. See `.planning/research/STACK.md` and `.planning/research/ARCHITECTURE.md` for implementation patterns.
