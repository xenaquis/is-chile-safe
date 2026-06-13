---
phase: 04-editorial-pages-adsense
verified: 2026-06-13T14:55:00Z
status: human_needed
score: 6/6 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Browse the 10 EN editorial pages and 10 ES editorial pages in a browser and confirm each contains substantive, editorially sober prose (800-1500 words, single H1, logical H2 sections, no placeholder copy)"
    expected: "All 20 editorial pages read as authoritative, well-structured content about Chilean crime data — not lorem ipsum or scaffolding skeletons"
    why_human: "Word count and structure assertions are automated; prose quality, editorial tone, and whether content genuinely answers the page topic require human judgment"
  - test: "Submit the methodology page and the legal pages (Privacy Policy, Terms, About, Contact) to Google Search Console (URL Inspection → Request Indexing)"
    expected: "GSC confirms the pages are crawlable and queued for indexing; no robots or canonical issues reported"
    why_human: "GSC submission is an external action that cannot be verified programmatically from the build. ROADMAP Success Criterion 1 states pages are 'submitted to Google Search Console' — this is deferred until Phase 6 per CONTEXT D-09 for the flag-flip, but GSC submission of the editorial and legal pages is a Phase 4 criterion. Human must confirm submission status."
  - test: "Visually inspect the site footer on both the EN home (/) and ES home (/es/) to confirm all four legal links are rendered with correct locale labels and working href paths"
    expected: "EN footer shows 'Privacy Policy / Terms of Use / About / Contact' linking to the correct slugs; ES footer shows 'Política de Privacidad / Términos de Uso / Acerca de / Contacto'"
    why_human: "Automated tests verified the href values in HTML; human visual check confirms labels and rendering fidelity in the browser"
  - test: "Open /is-chile-safe/ and /es/delitos-por-comunas/ and confirm the FAQBlock renders the Q+A items with visible text, logical questions, and correct sober-language editorial tone"
    expected: "FAQ items expand as static open list (no JS accordion), answers cite CEAD year and data, no absolute-safety claims"
    why_human: "FAQPage JSON-LD and markup presence is verified; editorial quality of FAQ answers requires human review"
deferred:
  - truth: "AdSense code is integrated and serving ads after the first indexing wave is confirmed (ROADMAP Success Criterion 5)"
    addressed_in: "Phase 6"
    evidence: "CONTEXT D-09: ADSENSE_ENABLED defaults OFF; flag-flip deferred to Phase 6 after first GSC indexing wave. ROADMAP Phase 6 goal: 'site live on ischilesafe.com with automated pipelines'. GSC submission timing also Phase 6 per CONTEXT deferred ideas."
---

# Phase 4: Editorial Pages + AdSense Verification Report

**Phase Goal:** Authoritative editorial and legal pages are live and indexed; the site qualifies for and has AdSense integrated
**Verified:** 2026-06-13T14:55:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | All 10 EN and 10 ES priority editorial pages are accessible and contain substantive content | VERIFIED | Build produces all 20 pages confirmed in dist/; structure.mjs "Phase-4 PASS — all 28 editorial/legal pages present"; hreflang.mjs 100/100 pages pass |
| 2 | The methodology page explains CEAD sources, rate calculation, subregistro caveat, and comparison criteria | VERIFIED | dist/methodology/index.html: CEAD present, rate-per-100k present, subregistro present; ~1441 words |
| 3 | Legal pages (Privacy Policy, Terms, About, Contact) are live and linked from the footer in both locales | VERIFIED | All 8 legal pages in dist/; footer verified in dist/index.html and dist/es/index.html for all 8 legal links; no ad-slot markup on any legal page |
| 4 | The Astro build fails with a clear error if any page contains forbidden language | VERIFIED | forbidden-language.mjs registered as validator #9 in all.mjs; 100 pages scanned, 0 violations; FORBIDDEN_TERMS array with word-boundary lookahead/lookbehind (not \b), accent-normalised via NFD; allow-list for CEAD-attributed superlatives |
| 5 | AdSense code is built and gated (MON-01 build-time integration) — no ad markup in dist/ with flag unset | VERIFIED | AdSlot.astro uses exact `ADSENSE_ENABLED === 'true'` gate; BaseLayout.astro has gated loader; recursive dist/ scan: ZERO pagead2/adsbygoogle occurrences; legal pages have zero ad-slot markup |
| 6 | FAQ editorial pages emit FAQPage JSON-LD | VERIFIED | dist/is-chile-safe/ and dist/is-santiago-safe/ both contain FAQPage JSON-LD; DataCallout markup present on /is-santiago-safe/ |

**Score:** 6/6 truths verified

### Deferred Items

Items not yet met but explicitly addressed in later milestone phases.

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | AdSense serving ads after first indexing wave (ROADMAP SC #5) | Phase 6 | CONTEXT D-09: flag-flip + GSC submission deferred to Phase 6. Phase 6 goal: site live on ischilesafe.com. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `site/scripts/validate/forbidden-language.mjs` | Post-build dist/ scanner for forbidden terms (EDIT-05) | VERIFIED | Exists; FORBIDDEN_TERMS array; NFD accent-normalisation; lookahead/lookbehind boundaries; ALLOW_LIST; 80+ lines |
| `site/scripts/validate/all.mjs` | 9-validator registry including forbidden-language.mjs | VERIFIED | VALIDATORS array has 9 entries; header comment lists all 9; forbidden-language is #9 |
| `site/scripts/validate/structure.mjs` | EDIT-01/02/04 dist/ slug assertions | VERIFIED | PHASE4_DIST_PAGES array; sentinel gate (methodology/index.html); all 28 slugs from REQUIREMENTS.md |
| `site/src/components/AdSlot.astro` | CLS-safe ad slot, env-gated | VERIFIED | Exact string compare `ADSENSE_ENABLED === 'true'`; reserved 90px/50px dimensions; placeholder when disabled; position prop (not slot — CR fix applied) |
| `site/src/components/CookieConsent.astro` | Consent banner, localStorage gate | VERIFIED | Exists; banner ids present; csm_consent localStorage key |
| `site/src/layouts/BaseLayout.astro` | Gated async AdSense loader in head | VERIFIED | `adsenseEnabled && adsenseClient` gate; pagead2 loader conditional; JSON-LD `</` escape fix (CR-01) |
| `site/src/components/PageFooter.astro` | Footer legal-page links (EDIT-04) | VERIFIED | Second nav row with locale-correct links to all 4 legal pages in EN and ES |
| `site/src/config/i18n.ts` | Footer + cookie + callout EN/ES strings | VERIFIED (inferred) | PageFooter imports t.footer_privacy/terms/about/contact; build succeeds with no TypeScript errors |
| `site/src/layouts/EditorialLayout.astro` | Editorial wrapper with AdSlot + CookieConsent gated | VERIFIED | Wraps BaseLayout; AdSlot position="bottom" rendered; CookieConsent gated on adsenseEnabled; .editorial-prose 720px |
| `site/src/layouts/LegalLayout.astro` | Legal wrapper, no ads, no consent | VERIFIED | Wraps BaseLayout; NO AdSlot import; NO CookieConsent reference; .editorial-prose 720px |
| `site/src/components/DataCallout.astro` | Sourced data callout box | VERIFIED | Exists; callout-source class confirmed |
| `site/src/components/FAQBlock.astro` | Static FAQ Q+A list | VERIFIED | Exists; no client: directive; FAQPage JSON-LD present in built pages that use it |
| `site/src/components/ContactForm.astro` | Static mailto contact form | VERIFIED | Exists; `mailto:xenaquis@gmail.com`; 3+ required attributes confirmed |
| `site/src/pages/is-chile-safe.astro` | EDIT-01 EN FAQ editorial page | VERIFIED | File exists; FAQPage JSON-LD in dist; loads loadNationalAverage() |
| `site/src/pages/is-santiago-safe.astro` | EDIT-01 EN FAQ editorial page with data callouts | VERIFIED | File exists; FAQPage JSON-LD; DataCallout markup in dist |
| `site/src/pages/privacy-policy.astro` | EDIT-04 EN privacy policy disclosing AdSense | VERIFIED | File exists; uses LegalLayout; dist HTML mentions AdSense/advertising + cookies |
| `site/src/pages/contact.astro` | EDIT-04 EN contact page with mailto form | VERIFIED | File exists; ContactForm component imported; mailto: in dist/contact/index.html |
| `site/src/pages/es/politica-privacidad.astro` | EDIT-04 ES privacy policy | VERIFIED | File exists; dist page present |

All 10 EN editorial slugs (EDIT-01): `/` `/chile-crime-map/` `/is-chile-safe/` `/santiago-safety-map/` `/is-santiago-safe/` `/valparaiso-safety/` `/vina-del-mar-safety/` `/concepcion-safety/` `/safest-cities-in-chile/` `/methodology/` — all confirmed in dist/.

All 10 ES editorial slugs (EDIT-02): `/es/` `/es/mapa-delito-chile/` `/es/delitos-por-comuna/` `/es/delitos-por-region/` `/es/comunas-mas-seguras-chile/` `/es/mapa-seguridad-santiago/` `/es/seguridad-valparaiso/` `/es/seguridad-vina-del-mar/` `/es/seguridad-concepcion/` `/es/metodologia/` — all confirmed in dist/.

Legal pages (EDIT-04): `/privacy-policy/` `/terms/` `/about/` `/contact/` `/es/politica-privacidad/` `/es/terminos/` `/es/acerca-de/` `/es/contacto/` — all confirmed in dist/. Note: two slugs are intentionally unpaired per design (is-santiago-safe has no ES pair; es/delitos-por-region has no EN pair); self-referencing hreflang passes hreflang.mjs.

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `all.mjs` VALIDATORS | `forbidden-language.mjs` | array entry at position 9 | WIRED | Confirmed in VALIDATORS array; runs in spawnSync loop |
| `EditorialLayout.astro` | `AdSlot.astro` | AdSlot position="bottom" in template | WIRED | Import + usage confirmed in source |
| `EditorialLayout.astro` | `BaseLayout.astro` | wraps BaseLayout, passes jsonLd | WIRED | Confirmed in source |
| `BaseLayout.astro` | `import.meta.env.ADSENSE_ENABLED` | build-time env gate | WIRED | `adsenseEnabled && adsenseClient` gate in head |
| `PageFooter.astro` | `i18n.ts` footer_* keys | t.footer_privacy/terms/about/contact | WIRED | Import + four keys used; build succeeds |
| `contact.astro` | `ContactForm.astro` | component embed | WIRED | mailto: present in dist/contact/index.html |
| `privacy-policy.astro` | `LegalLayout.astro` | layout wrap | WIRED | Confirmed in source; no ad markup in dist |
| `is-chile-safe.astro` | FAQPage JSON-LD | BaseLayout jsonLd prop | WIRED | FAQPage in dist/is-chile-safe/index.html |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `is-chile-safe.astro` | `nationalAvg` | `loadNationalAverage()` from lib/data.ts | Yes — reads from CEAD JSON files | FLOWING |
| `is-santiago-safe.astro` | commune data | `loadCommune('13101')` from lib/data.ts | Yes — reads from data/cead/comunas/13101.json | FLOWING |
| `methodology.astro` | (static prose) | N/A — static content | N/A | N/A (static editorial) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Build produces all 100 pages cleanly | `npm run build` | 100 page(s) built in 16.94s, no errors | PASS |
| 9/9 validators pass including forbidden-language (#9) | `node scripts/validate/all.mjs` | 9/9 PASS, "All validators passed." | PASS |
| No ad markup in dist/ when ADSENSE_ENABLED unset | Node scan of all dist/ HTML | ZERO pagead2/adsbygoogle occurrences | PASS |
| All 8 footer legal links present on EN/ES home | Node check of dist/index.html + dist/es/index.html | All 8 links present | PASS |
| Methodology mentions CEAD, rate per 100k, subregistro | Node check of dist/methodology/index.html | All 3 present; ~1441 word-tokens | PASS |
| Privacy policy discloses AdSense/cookies | Node check of dist/privacy-policy/index.html | AdSense/advertising and cookies mentioned | PASS |
| No ad-slot markup on any of 8 legal pages | Node scan of all 8 legal dist/ pages | All 8 clean | PASS |
| FAQPage JSON-LD on question-style pages | Node check of dist/is-chile-safe/ + dist/is-santiago-safe/ | FAQPage present on both | PASS |
| structure.mjs reports all 28 Phase-4 pages present | structure validator output | "Phase-4 PASS — all 28 editorial/legal pages present" | PASS |
| hreflang correct on 100 pages | hreflang.mjs | 100/100 PASS including editorial/legal pages | PASS |

### Probe Execution

No explicit probes declared in PLAN files. The 9-validator suite (`node scripts/validate/all.mjs`) functions as the phase probe. Result: 9/9 PASS (evidence above).

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|---------------|-------------|--------|----------|
| EDIT-01 | 04-04, 04-05 | 10 EN editorial pages at specified slugs | SATISFIED | All 10 slugs in dist/; structure.mjs asserts them |
| EDIT-02 | 04-06 | 10 ES editorial pages at specified slugs | SATISFIED | All 10 slugs in dist/; structure.mjs asserts them |
| EDIT-03 | 04-05, 04-06 | Methodology page documents CEAD sources, rate calc, subregistro, comparison criteria | SATISFIED | dist/methodology/index.html verified: CEAD, rate/100k, subregistro, ~1441 words |
| EDIT-04 | 04-07 | Legal pages: Privacy Policy, Terms, About, Contact in EN+ES; linked from footer | SATISFIED | All 8 legal pages in dist/; footer links verified on EN+ES home pages |
| EDIT-05 | 04-01 | Build fails with clear error on forbidden language | SATISFIED | forbidden-language.mjs as validator #9; 100 pages scanned, 0 violations in live build |
| MON-01 | 04-02, 04-07 | AdSense integrated (gated OFF by default; activation after indexing wave) | SATISFIED (build-time) | AdSlot + CookieConsent + gated loader built and wired; zero ad markup in dist/ with flag unset; activation deferred to Phase 6 per D-09 |

All 6 required Phase 4 requirements are accounted for. No orphaned requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/components/ContactForm.astro` | 1-3 | `<!-- Phase-4 MVP: mailto link. Replace with a form service endpoint in v2. -->` | Info | Intentional documented tradeoff per D-14; contact via mailto is the accepted MVP mechanism; no unreferenced debt marker |

No TBD/FIXME/XXX markers found in Phase 4 files. The mailto comment is a documented design decision (D-14), not unresolved debt.

### Human Verification Required

#### 1. Editorial Prose Quality

**Test:** Browse all 20 editorial pages (10 EN + 10 ES) and confirm each contains substantive, editorially sober prose — 800-1500 words, single H1, logical H2 sections, no placeholder copy
**Expected:** Pages read as authoritative content about Chilean crime data, answering the page's title question with sourced CEAD callouts and appropriate caveats; no absolute-safety claims in natural language that would evade the automated gate
**Why human:** Word count is automated; editorial quality, completeness of coverage, and genuine topic relevance require human judgment

#### 2. GSC Submission of Editorial and Legal Pages

**Test:** Submit the methodology page and all legal pages to Google Search Console via URL Inspection → Request Indexing; confirm editorial pages are crawlable
**Expected:** GSC reports pages are crawlable with no robots.txt blocking or canonical issues; indexing request accepted
**Why human:** External action against Google's Search Console; cannot be verified programmatically. ROADMAP Success Criterion 1 specifies pages are "submitted to Google Search Console" — this is a human action required before phase can be fully signed off

#### 3. Footer Legal Links Visual Rendering

**Test:** Open the site in a browser at both `/` (EN) and `/es/` (ES) and visually confirm the footer's legal nav row displays all four links with correct locale-appropriate labels and working href navigation
**Expected:** EN footer: "Privacy Policy | Terms of Use | About | Contact"; ES footer: "Política de Privacidad | Términos de Uso | Acerca de | Contacto"; links navigate to the correct pages
**Why human:** Automated tests verified href values; human confirms visual rendering, label text from i18n strings, and browser navigation behavior

#### 4. FAQ Quality and Sober Language Check

**Test:** Open `/is-chile-safe/` and `/es/delitos-por-region/` (or `/is-santiago-safe/`) and read the FAQ block answers
**Expected:** FAQ answers cite specific CEAD data with year references, use comparative language ("higher/lower reported rates") rather than absolute safety claims, and read naturally as editorial content
**Why human:** The forbidden-language gate catches defined terms; subtle editorial quality and whether the copy achieves the intended authoritative-yet-sober tone requires human review

### Gaps Summary

No automated gaps found. All 6/6 must-have truths are VERIFIED by codebase evidence and live build output.

Status is `human_needed` because ROADMAP Success Criterion 1 (GSC submission) requires a human external action, and editorial prose quality requires human judgment to confirm the pages are genuinely authoritative rather than mechanically generated skeletons.

The deferred item (AdSense serving live ads, ROADMAP SC #5) is explicitly scoped to Phase 6 per CONTEXT D-09 and is not a gap for Phase 4 sign-off.

---

_Verified: 2026-06-13T14:55:00Z_
_Verifier: Claude (gsd-verifier)_
