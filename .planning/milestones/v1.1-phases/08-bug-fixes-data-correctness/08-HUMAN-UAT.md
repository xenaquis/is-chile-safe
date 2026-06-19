---
status: partial
phase: 08-bug-fixes-data-correctness
source: [08-VERIFICATION.md]
started: 2026-06-15T09:45:00Z
updated: 2026-06-15T09:45:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Console clean on money pages + map (BUGFIX-01)
test: Open the 11 EN money pages and /map/ in a real browser with DevTools Console open; navigate and interact with the map.
expected: Zero console errors and zero console warnings.
why_human: Client-side Leaflet/React island hydration output cannot be observed by static build grep. Phase 8 adds no new client-side code, but the clean-console claim needs a live browser run to be auditable.
result: [pending]

### 2. CR-01 functional rank cross-check
test: Open /crime/homicide/ and /es/delito/homicidio/; pick one displayed commune and confirm its shown rank (#N) matches national standing, not filtered-list position.
expected: Each commune shows its true national rank (a commune ranked #87 nationally displays #87, not #1). Cross-reference against the commune's data/cead/{CUT}.json national_rank field.
why_human: CR-01 fix is code-verified (nationalRank assigned from a pre-filter counter, rendered as row.nationalRank); functional correctness with real rollout data needs a human cross-reference.
result: [pending]

### 3. Mobile hamburger keyboard behavior (WR-02 / WR-03)
test: Open the site at <640px viewport; activate the hamburger menu; attempt to close it with the Escape key; tab through the header.
expected: Menu opens/closes by click/tap; Escape does NOT close the CSS-only menu (WR-03 known limitation, intentionally deferred to Phase 9 under the D-09 zero-JS constraint); no crash/console error; Tab order does not land on the hidden checkbox.
why_human: WR-02 (tabindex / display:none toggle) is code-verified. WR-03 (Escape + focus management) is a known deferred a11y gap requiring observation on a mobile viewport.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
