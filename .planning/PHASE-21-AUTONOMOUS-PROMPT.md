# Phase 21 — Autonomous run (paste after /clear)

## ▶ Copy-paste this exact line after `/clear`:

```
/gsd-autonomous --only 21
```

That's it. Everything below is already prepared so the run is well-scoped.

---

## What's already set up (so the autonomous run doesn't go off-rails)

- **CONTEXT pre-seeded:** `.planning/phases/21-commune-comparator-a-vs-b-seo/21-CONTEXT.md` — locks the critical guardrails (curated ~3,400-pair allowlist NOT full cartesian, build <18k files, ≥5 uniqueness blocks + ≥300 words per pair, accent-insensitive autocomplete, static pre-render, EN/ES parity, build on Phase 18 `comparator_table.json`). Because CONTEXT exists, the autonomous flow **skips discuss** and goes straight to UI-spec → plan → execute.
- **Prereqs green:** Phase 18 outputs (`comparator_table.json` + `composite_index`) present; CMP-01..07 in REQUIREMENTS; config `skip_discuss` + `ui_phase` on.
- **Phase 21 is `--only`**, so it runs just the comparator phase (UI-spec → plan → execute → code-review → ui-review) and skips milestone lifecycle.

## What `/gsd-autonomous --only 21` will do
1. Auto-detect Phase 21, see CONTEXT exists → skip discuss.
2. Generate UI-SPEC (frontend phase: comparator island + A-vs-B pages).
3. Research + plan (it's research-flagged — the planner will compute the real priority-pair count from commune data BEFORE getStaticPaths, per the CONTEXT).
4. Execute the plans, code-review, ui-review.
5. Pause only for genuine blockers / a gap-found decision.

## If you'd rather it ask you scoping questions instead of auto-deciding
Use this instead (runs discuss interactively, then plan+execute in background):
```
/gsd-autonomous --only 21 --interactive
```

## Added scope (2026-06-20)
The CONTEXT now also includes a user-directed deliverable: **show the homicide rate per 100k on the static commune pages (EN+ES)** — currently missing (they only show the broad "Life crimes" family; the dedicated homicide figure lived only in the map panel). Phase 21 will add it to commune pages + the comparator.

## Heads-up
- Phase 21 is the biggest remaining phase (interactive comparator island + ~6,800 bilingual A-vs-B SEO pages). Expect a long run with several subagents.
- The build-size assertion (<18k files) and the thin-content assertion are the two hard gates — if the planner can't satisfy them it will surface a decision rather than ship thin pages.
