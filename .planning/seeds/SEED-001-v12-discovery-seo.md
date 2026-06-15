---
id: SEED-001
title: v1.2 — Discovery, comparators & programmatic SEO
planted_during: Phase 9 discussion (v1.1)
planted_date: 2026-06-15
trigger_when: opening milestone v1.2, or when planning rankings / comparators / programmatic SEO pages
status: planted
---

# SEED-001: v1.2 — Discovery, Comparators & Programmatic SEO

Captured while discussing Phase 9 (map comprehension). These are discovery/SEO
**features** — deliberately deferred out of v1.1's polish scope. User chose:
new milestone **v1.2**, rollout **hybrid**, comprehension first (= Phase 9).

## When to Surface

- Opening milestone v1.2 (`/gsd:new-milestone`).
- Planning any "safest/least-safe cities" ranking, commune comparator, or A-vs-B page.
- Designing programmatic SEO expansion beyond the current rollout pages.

## Scope ideas

- **Rankings by crime family** — which city/commune has the most/least of crime type X; national, by region, by family. (User reiterated this twice.)
- **Interactive commune comparator** — side-by-side 2–3 communes: rate, rank, trend per family; "compare with national/regional average"; commune search.
- **A-vs-B comparison pages** — programmatic long-tail ("Providencia o Ñuñoa?").
- **"Safest communes" editorial + structured rankings** — top-N pages with real prose + Dataset/FAQ/BreadcrumbList schema.
- **Ranking pages by (region × crime family)** — programmatic grid.
- **Internal linking** — rankings ↔ communes ↔ regions ↔ comparators.

## Why This Matters

This is the primary organic-traffic engine: long-tail comparison/ranking queries
are high-intent and abundant for Chilean place + crime terms. The data (CEAD per
commune/family) already exists — the gap is presentation + indexable pages.

## Locked constraints (carry into v1.2)

- **Rollout = hybrid:** national rankings may *display* all communes (data exists),
  but only link to a page for the top-N / rollout set — never 404 to non-rollout
  communes (Phase 8 F-005 contract).
- Never absolute "peligroso/seguro"; always CEAD + year attribution.
- Avoid thin content (Google deindexing risk) — every programmatic page needs real,
  differentiated prose.
- Static / SEO-indexable; no critical content client-only.

## Prerequisite

Close v1.1 first (Phase 9 + Phase 8 human UAT), then `/gsd:complete-milestone`
before `/gsd:new-milestone` for v1.2 — avoids the destructive phase-dir clear on
an open milestone.
