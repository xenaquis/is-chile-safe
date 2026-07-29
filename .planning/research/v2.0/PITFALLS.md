# Pitfalls Research — v2.0 Composite Index, Comparators & Launch

**Domain:** Bilingual crime-data visualization + programmatic SEO platform (Chile Safety Map)
**Milestone:** v2.0 — Composite Crime Index, Commune Comparator, A-vs-B SEO Pages, Go-live
**Researched:** 2026-06-19
**Confidence:** HIGH (project-specific; derived from existing codebase state, PROJECT.md, STATE.md, and prior v1.x lessons)
**Scope:** NEW features only. v1.0 pitfalls are in the archived 2026-06-12 PITFALLS.md.

---

## Critical Pitfalls

### Pitfall CI-1: Composite Index Implies an Absolute Safety Verdict

**What goes wrong:**
The index is designed to replace the raw `featured_rates` headline figure with something more informative. However, any composite that outputs a single number per commune will be rendered by users — and by Google snippets, social shares, and screen readers — as "Santiago scores 42 / La Pintana scores 78, therefore La Pintana is dangerous." The CI forbidden-language validator added in P20 checks rendered HTML for vocabulary like "seguro/peligroso/safe/dangerous." A composite index page will pass that check if the word "index" is used but still communicate an absolute verdict through ranking position, color, and relative superlatives ("bottom 10 communes").

**Why it happens:**
Any single-number output that can be sorted becomes a de-facto ranking, and rankings invite superlatives. The problem is not the word "dangerous" — it is the information architecture. A choropleth colored from green to red, a ranking table sorted from best to worst, and a comparator that says "Commune A is safer than Commune B" all communicate an absolute verdict without using the forbidden words.

**How to avoid:**
- Frame the index as "composite reported-crime burden" or "índice de carga delictiva reportada" — never "safety score" or "seguridad relativa".
- Every page that displays the index must include a mandatory caveat block (EN/ES) stating: underreporting rates vary; the index reflects denuncias not actual crime; small-denominator communes have high volatility.
- The choropleth color scale legend must be labeled "reported crime burden (relative)" not "danger level" or "safety".
- The ranking derived from the index must be titled "Communes by reported crime burden" not "safest/most dangerous communes."
- Extend the forbidden-language CI validator to also flag: "safest," "most dangerous," "crime-free," "sin delitos," "más segura," "más peligrosa" when they appear without a qualifying "reported" or "según registros."
- Add the index methodology to the existing `/methodology/` page (EN/ES) before deploying any index-driven page.

**Warning signs:**
- Any og:description or `<title>` that reads like "[Commune] ranks #1 safest in Chile"
- The choropleth legend uses green/red without explicit "relative to national reported rate" labeling
- The comparator page says "A is safer than B" without "according to reported denuncias"

**Phase to address:**
Phase 18 (Composite Index) — editorial framing must be locked in the schema design step, before any template is written. Extend the P20 CI validator in the same phase.

---

### Pitfall CI-2: Normalization Choice Silently Misleads — Min-Max vs. Z-Score vs. Percentile

**What goes wrong:**
The composite index must normalize across 7 metrics with different units and ranges (per-100k rates, raw homicide counts, SII exposure ratios). Choosing min-max normalization causes a single extreme outlier commune (Sierra Gorda, Juan Fernández — known to reach 43,369 per-100k) to compress all other communes into a narrow band near zero. The choropleth looks uniform; all but the most extreme commune appear equally "safe." Choosing z-score without winsorization causes the same outlier to distort the mean and standard deviation, inflating z-scores for mid-range communes. Neither failure is obvious from looking at the output without comparing to known ground truth.

**Why it happens:**
Min-max is the most commonly documented normalization method and is easiest to implement. Developers apply it without checking whether the input distribution is approximately uniform or heavily skewed. CEAD per-100k rates are right-skewed (known from prior PLAUSIBILITY_MAX_RATE work — micro-communes can reach 43,369). Applying min-max to a right-skewed distribution compresses 95% of communes into the bottom 20% of the output range.

**How to avoid:**
- Use percentile rank normalization (rank each commune 0–100 within the distribution) as the primary approach — it is outlier-resistant by construction and maps naturally to choropleth quintiles.
- Or use z-score with winsorization: cap input values at the 95th percentile before computing mean/std. Document the winsorization threshold in `data/SOURCES.md` and the methodology page.
- Run a distribution check after normalization: if more than 70% of communes have a normalized score below 0.25 (for min-max) or below -0.5 z, the normalization is distorted by outliers.
- Add a pytest assertion: `assert index_scores.describe()['25%'] > index_scores.mean() * 0.3` (i.e., the 25th percentile is not near zero).
- Display the raw underlying metrics alongside the index in the commune panel — do not hide the inputs that produced the score.

**Warning signs:**
- Choropleth shows nearly all communes in the lowest color band with one or two extreme outliers
- The 25th percentile of the index is less than 5% of the maximum value
- Santiago (a high-crime large city) and a micro-commune have the same index score

**Phase to address:**
Phase 18 (Composite Index) — normalization function must be validated with distribution checks before any visual is built on top of it.

---

### Pitfall CI-3: SII Exposure Proxy Distorts Small-Commune and Tourist-Commune Scores

**What goes wrong:**
The SII exposure proxy (empresas + trabajadores dependientes per commune) was chosen because it approximates the daytime/functional population better than INE residential population for crime-rate adjustment. However, SII records firms by their fiscal domicile (HQ), not by the location where workers or customers are actually present. A large forestry company headquartered in Los Ángeles employs workers in remote logging communes — those worker counts do not appear in those communes' SII data. Conversely, a commune like Las Condes has a disproportionately high SII count because many national companies register their legal address there. The exposure-adjusted index will rank Las Condes as lower-crime-burden than its raw rate suggests (the denominator is inflated by HQ registrations), and will rank forestry communes higher than they should be.

**Why it happens:**
This is a known caveat documented in Phase 17 Wave-0 decisions: "SII `PUB_COMU.xlsb` (empresas + trabajadores dependientes per commune; needs `pyxlsb`; comuna = firm domicile/HQ caveat)." It is easy to wire the data correctly and still produce misleading outputs because the caveat is methodological, not computational.

**How to avoid:**
- The methodology page must explain the SII HQ-domicile limitation explicitly, in both languages, with an example (e.g., "companies with offices in multiple communes are registered at their fiscal address, which may differ from their operational location").
- Cap the SII adjustment factor: if `sii_workers / ine_population > N` (e.g., 5.0), flag the commune and use the INE population as denominator instead. Document the cap threshold.
- Display a "high-denominator adjustment" warning badge on commune pages where the SII figure deviates more than 3x from INE population.
- Do not present the SII-adjusted index as more accurate than the INE-based rate — frame it as "adjusted for estimated economic activity" and show both the adjusted and unadjusted rates.
- Add a pytest: assert no commune's `sii_workers` exceeds `ine_population * 10` (catches obviously wrong joins or data errors).

**Warning signs:**
- Las Condes or Providencia show dramatically lower index scores than their raw crime rates suggest
- A forestry or mining commune shows a very high index score that contradicts local knowledge
- The exposure ratio for any commune exceeds 10x its residential population

**Phase to address:**
Phase 18 (Composite Index) — the SII join and cap logic must be implemented and validated in the pipeline before the index is computed.

---

### Pitfall CI-4: CEAD tipoVal Double-Count Inflates the Composite Metric

**What goes wrong:**
The CEAD `tipoVal` parameter is additive: `1=denuncias, 2=detenciones, 3=aprehendidos`. If the index pipeline requests `tipoVal=1,2` (cases policiales, as documented in Phase 17 Wave-0), it gets denuncias + detenciones summed. If a new scraper pass for the composite index accidentally requests all three values or fails to specify the filter, it gets triple-counted figures. This inflates every input metric, which inflates the index, which produces a misleading choropleth. The error is invisible unless the developer compares against the previously validated `featured_rates` values.

**Why it happens:**
The CEAD API does not document the `tipoVal` parameter. The correct value (`1,2`) was established in Phase 17 Wave-0 and stored as a key decision. A new pipeline pass written by someone who did not read STATE.md will default to the API's behavior, which may return all measures summed.

**How to avoid:**
- Centralize the `tipoVal` constant in a single configuration file (`pipeline/config.py` or similar) — never embed it in multiple scraper call sites.
- Add a validation assertion after every CEAD fetch for the index: compare the fetched national total against the `featured_rates` national total already in `data/` — they must agree within 5%. If they diverge, fail loudly.
- Add a comment in the CEAD client module: `# tipoVal=1,2 = denuncias+detenciones (casos policiales). DO NOT use tipoVal=3 (aprehendidos) or omit tipoVal — both double-count.`

**Warning signs:**
- Index input values are approximately 3x the corresponding `featured_rates` values
- National totals from the new scrape differ from Phase 17-validated totals by more than 10%

**Phase to address:**
Phase 18 (Composite Index) — pipeline plan step must include a cross-check assertion against existing validated data.

---

### Pitfall CI-5: Spurious Precision — Index Score Displayed to Two Decimal Places

**What goes wrong:**
The index is computed from 7 metrics, each with its own uncertainty (CEAD underreporting, SII HQ-domicile caveat, SPD VHC annual lag, INE population projections). Displaying the result as "63.47" implies a precision that does not exist. Users anchor on the second decimal place when comparing communes ("A is 63.47, B is 63.51, so B is slightly more dangerous"). The comparator page's A-vs-B display amplifies this — a difference of 0.04 index points is presented as meaningful when it is well within the measurement uncertainty.

**Why it happens:**
Floating-point arithmetic naturally produces many decimal places. Developers display them because "more precision looks more scientific."

**How to avoid:**
- Round the index to one significant digit or display it as a percentile rank (integer 1–100) on all public-facing pages.
- If a raw score must be shown, display it as an integer or to one decimal place maximum.
- The comparator must include a "margin of uncertainty" statement: "Index scores within 5 points should be considered equivalent given data limitations."
- Never display the index to more than one decimal place in any generated page template, og:description, or JSON-LD property.

**Warning signs:**
- Any rendered page showing index values like "47.823" or "12.67"
- The comparator page highlighting a difference of less than 2 index points as meaningful

**Phase to address:**
Phase 18 (Composite Index) — lock the display precision in the data schema (store as rounded integer in the output JSON) so templates cannot over-display it.

---

### Pitfall CI-6: Schema Migration Breaks Existing Validators and Map Payload

**What goes wrong:**
`featured_rates` currently holds 6 fields consumed by: (1) the commune panel React component, (2) the choropleth color logic, (3) the commune page Astro template, (4) the figure-registry validator, and (5) the pytest pipeline assertions. Migrating to a 7-metric schema renames, reorders, or adds fields. Any consumer that accesses `featured_rates` by index position (array) rather than by key (object) will silently read the wrong metric. The choropleth may color by the wrong dimension. The figure-registry validator may accept orphan figures from the old schema. The commune panel may display zeros or undefined.

**Why it happens:**
The existing STATE.md notes: "ResultPanel converts series.by_family RECORD to catalog-indexed ARRAY for PanelFamilyBars (commune JSON uses record; map-payload uses array — never confuse them)." The dual record/array representation is a known source of confusion. Adding new fields to `featured_rates` while it is still array-indexed in the map payload is the specific risk.

**How to avoid:**
- Make `featured_rates` a named-key object (not an array) in the new 7-metric schema. If the map payload currently uses array indexing, migrate the map payload to named-key access in the same phase.
- Add a TypeScript type definition for the new schema and run `@astrojs/check` in CI — type errors will catch consumers that break.
- Write a migration validator: before the Phase 18 build goes live, run the existing 12 frontend validators + all pytest against the new schema. All must pass before proceeding.
- Add a backward-compatibility shim: during the transition, keep the old `featured_rates` fields present alongside the new ones (deprecated but present), removing them only after all consumers are verified.
- The figure-registry validator must be updated to know about the 7 new metric keys — do not deploy new figures until the registry is updated.

**Warning signs:**
- Choropleth coloring does not change when switching between metric types after the migration
- Any commune panel field shows "undefined" or "NaN" after the schema change
- Pytest assertions that check specific `featured_rates` values by index pass but are testing the wrong field

**Phase to address:**
Phase 18 (Composite Index) — migration plan must enumerate all 5+ consumers of `featured_rates` and verify each one explicitly.

---

### Pitfall CI-7: SPD VHC Homicide Count Creates Annual-Lag Inconsistency with CEAD Data

**What goes wrong:**
The composite index switches homicide input from CEAD grupo 101 (denuncias) to SPD VHC xlsx (actual homicide counts, 2018–2025). SPD VHC data has an annual lag — the 2025 file may not be complete or published until mid-2026. CEAD data is available quarterly. If the index combines SPD VHC 2024 homicide counts with CEAD 2025 Q1 rates for other crime types, it produces a temporally inconsistent index. Users (and the methodology page) will see "2025 data" but the homicide component is actually 2024.

**Why it happens:**
Data sources update on different schedules. Developers wire the latest available file from each source without checking temporal alignment.

**How to avoid:**
- The index must use the same reference year for all components. The reference year is the latest year where ALL components are available.
- Add a pipeline assertion: `assert spd_year == cead_year == sii_year`, fail if any source is from a different year than the others.
- The methodology page must display the reference year for each component separately (e.g., "homicide: SPD VHC 2024; other crime: CEAD 2025 Q1; exposure: SII 2024").
- If a more recent CEAD year is available than SPD VHC, offer both: the index for the aligned year, and a separate "CEAD current" display that does not include homicide from SPD.

**Warning signs:**
- The index JSON metadata shows different `data_year` values for different components
- The methodology page says "2025 data" but the SPD VHC file in `data/snapshots/` is dated 2024

**Phase to address:**
Phase 18 (Composite Index) — the pipeline plan must include explicit year-alignment logic and assertions.

---

### Pitfall CI-8: Micro-Commune Outlier Dominates Choropleth Color Scale

**What goes wrong:**
Sierra Gorda (pop. ~2,000, mining commune) has a confirmed per-100k rate reaching 43,369 — more than 10x the next-highest commune. When the choropleth color scale is computed from this distribution, Sierra Gorda gets the darkest color and every other commune clusters in the lower three quintiles. The map communicates almost no information about the other 345 communes. This was noted in existing STATE.md but applies equally to the composite index — any weighted combination that includes a high-weight metric from a skewed distribution will exhibit the same behavior.

**Why it happens:**
The color scale is typically computed as a linear or quantile split across all values. When one value is 10x the next, even quantile splits may place the extreme outlier alone in the top quintile, making the map look like a single dark dot on an otherwise uniform background.

**How to avoid:**
- Use a percentile-rank color scale (already partially addressed in CI-2): map the index percentile to color, not the raw index value.
- Or winsorize: cap the top 1% of values at the 99th percentile for display purposes (display the actual value in the tooltip, use the winsorized value for color).
- Add a choropleth preview step in the pipeline: generate a histogram of index values and flag if any single bin contains > 5% of all communes AND is more than 3 standard deviations from the mean.
- The existing `PLAUSIBILITY_MAX_RATE = 100000` constant should be mirrored as a choropleth winsorization cap constant — keep them in sync.

**Warning signs:**
- The choropleth preview shows one commune in the darkest color and all others in the lightest two colors
- The 90th percentile of index scores is less than 20% of the maximum value

**Phase to address:**
Phase 18 (Composite Index) — choropleth scale logic must be tested with the actual index distribution before the map island is updated.

---

## Comparator / A-vs-B SEO Pitfalls

### Pitfall SEO-1: Combinatorial Page Explosion Exceeds the 20,000 Cloudflare File Limit

**What goes wrong:**
346 communes × 345 pairings = 119,370 possible A-vs-B pairs. Even if only one direction is generated (A < B alphabetically), that is ~59,000 pages. The current build produces 792 pages and sits safely under the 20,000-file free-tier limit. Adding 59,000 A-vs-B pages blows the limit by 3x and also blows any realistic Astro build time (20-minute CI timeout).

**Why it happens:**
"Programmatic SEO" naturally suggests generating every possible combination. The Cloudflare limit is a hard wall, not a soft guideline.

**How to avoid:**
- Limit A-vs-B pages to high-intent pairs only: the ~50 most-searched commune pairs (determined by GSC data once the site is live, or seeded from population × tourism priority in the short term), plus cross-region pairs for the 16 regional capitals, plus any pair explicitly linked from an editorial page. This gives ~200–500 pages, well within limits.
- Use a curated `data/comparator-pairs.json` file that explicitly lists which pairs to generate. Do not generate all permutations.
- Add a build-time assertion: `assert total_pages < 18000` (leaving headroom for future pages). Fail the build if exceeded.
- The sitemap must only include generated pairs — do not auto-generate sitemap entries for all possible pairs.

**Warning signs:**
- `getStaticPaths` for A-vs-B returns more than 2,000 entries
- Astro build time exceeds 15 minutes
- Cloudflare Pages deploy fails with "too many files" error

**Phase to address:**
Comparator/A-vs-B phase (Phase 21 or equivalent) — the pair-selection strategy must be defined before any `getStaticPaths` is written.

---

### Pitfall SEO-2: A-vs-B Pages Are Thin Content — Symmetric Template With Swapped Names

**What goes wrong:**
"Santiago vs Providencia" and "Providencia vs Santiago" are the same page with names swapped. "Santiago vs Providencia" and "Santiago vs Ñuñoa" are the same template with only one name changed. If the template generates a page that says "Santiago has a crime burden of X; Providencia has Y; Santiago is higher/lower" without any additional context, Google classifies the page as thin content and deindexes it. At 500 pairs, even a 10% deindex rate creates 50 orphan URLs that waste crawl budget.

**Why it happens:**
A-vs-B pages are inherently comparative templates. The challenge is making each pair unique enough to justify a separate URL.

**How to avoid:**
Each A-vs-B page must include at minimum:
1. The index comparison with the underlying metric breakdown (not just the headline score).
2. A narrative sentence for each commune that is generated from its data (e.g., "Santiago's rate is driven primarily by property crime (X%), while homicide rates are below the national average").
3. Regional context: which region each commune is in, and how each compares to its regional average.
4. A "who should care" framing: tourist, resident, or investor — and what each metric means for that use case.
5. A link to each commune's dedicated page (hub-and-spoke cross-linking from Phase 12 is the model).

Minimum target: 400 words of substantive, non-swappable content per page.

**Warning signs:**
- A-vs-B template generates fewer than 300 words of unique content per pair
- The only unique element on the page is the commune names and numbers
- Google Search Console shows "Discovered — not indexed" for >20% of A-vs-B pages within 60 days of launch

**Phase to address:**
Comparator/A-vs-B phase — content schema must be defined before the template is written. Define the 5+ data dimensions per pair that make each page unique.

---

### Pitfall SEO-3: A-vs-B hreflang Reciprocity Breaks at Scale

**What goes wrong:**
For each A-vs-B pair, there must be: `/compare/santiago-vs-providencia/` (EN) and `/es/comparar/santiago-vs-providencia/` (ES), each with hreflang tags pointing to the other, and each pointing to itself as the canonical. At 500 pairs × 2 languages = 1,000 pages, a single template error in the hreflang logic silently breaks all 1,000 pages. The existing hreflang pitfall (from v1.0 PITFALLS.md) is amplified by the volume.

**Why it happens:**
Astro's `getRelativeLocaleUrl` does not translate slugs (documented in memory `i18n-localized-slug-pitfall`). The A-vs-B slug must be constructed consistently in both the EN and ES templates and must exactly match the URL that the other language version generates.

**How to avoid:**
- The A-vs-B slug must use commune CUT codes (e.g., `/compare/13110-vs-13119/`), not commune names. This avoids transliteration and accent issues across languages. The page title displays the commune names; the URL uses stable CUTs.
- Or: use the canonical commune slug as established in the existing site (the same slug used in commune pages) and hardcode the ES equivalent rather than deriving it via `getRelativeLocaleUrl`.
- Write a build-time validator: for every A-vs-B page generated, assert that the corresponding ES/EN counterpart also exists in the output, and that their hreflang tags are reciprocal.
- Run this validator as part of the existing `npm run validate` suite.

**Warning signs:**
- Google Search Console shows EN A-vs-B pages appearing in ES search results (or vice versa)
- The hreflang checker finds non-reciprocal tags in A-vs-B pages
- ES comparator pages have different URL patterns than what EN pages reference in their hreflang

**Phase to address:**
Comparator/A-vs-B phase — slug strategy must be decided before template generation. The hreflang validator must be extended to cover A-vs-B pages.

---

### Pitfall SEO-4: Comparator Pages Are Orphaned — No Internal Links Pointing to Them

**What goes wrong:**
A-vs-B pages are generated and indexed but receive no PageRank from the rest of the site because no other page links to them. Google treats them as orphan pages (no incoming internal links) and either deindexes them or assigns very low crawl priority. The sitemap alone is insufficient to drive indexing for hundreds of new programmatic pages.

**Why it happens:**
Developers generate pages and add them to the sitemap without thinking through the internal linking structure. The commune pages (from Phase 11/12 hub-and-spoke) are the natural source of internal links, but they need to be updated to link to "Compare [X] with..." pages.

**How to avoid:**
- Each commune page must include a "Compare with nearby communes" section linking to the 3–5 most-searched A-vs-B pairs involving that commune.
- The home page or a dedicated `/compare/` index page must link to the 10–20 most popular A-vs-B pairs (bootstrapped from population + tourism priority, updated from GSC data once live).
- Editorial priority pages ("Is Santiago safe?") must link to the "Santiago vs Providencia" or "Santiago vs Vitacura" comparator pages where relevant.
- Add a build-time assertion: every generated A-vs-B page must be linked from at least one other page in the build output.

**Warning signs:**
- GSC shows A-vs-B pages in "Discovered — not indexed" state despite sitemap inclusion
- The A-vs-B pages have zero internal links in a site crawl (Screaming Frog or equivalent)
- Organic traffic to A-vs-B pages is zero 60 days after launch

**Phase to address:**
Comparator/A-vs-B phase — internal linking strategy must be designed as part of the page schema, not added after.

---

## Go-Live Pitfalls

### Pitfall GL-1: CF_DEPLOY_HOOK_URL Secret Unset — Site Remains Stale Indefinitely

**What goes wrong:**
This is the known blocker documented in STATE.md and memory `prod-deploy-hook-secret-gap`. The `CF_DEPLOY_HOOK_URL` GitHub Actions secret is unset. The `deploy-on-code.yml` workflow (added in quick-260618-x95) has `exit 0` when the secret is empty — a safe dry-run guard. But if the secret is never set, every code push to `site/**` silently succeeds in CI while the live site remains stale. The v2.0 composite index, A-vs-B pages, and go-live work will never appear in production.

**Why it happens:**
The secret requires a manual step in the Cloudflare dashboard (CF → Pages project → Settings → Deploy Hooks → Create hook → copy URL). It cannot be automated. It is easy to defer and forget.

**How to avoid:**
- Make setting the `CF_DEPLOY_HOOK_URL` secret step 1 of the go-live phase, before any code is merged to master.
- After setting the secret, do a test push of a trivial change and verify the Cloudflare Pages dashboard shows a new build triggered.
- Add a workflow that posts a GitHub issue or comment if `CF_DEPLOY_HOOK_URL` is empty — this surfaces the missing secret rather than silently passing.
- The go-live phase checklist must include: `[ ] CF deploy hook URL set in repo secrets`, `[ ] test push triggered a Cloudflare build`, `[ ] build completed and live URL updated`.

**Warning signs:**
- `deploy-on-code.yml` runs show "Deploy skipped: CF_DEPLOY_HOOK_URL not set" in the logs
- The Cloudflare Pages dashboard shows no new builds after a code push to `site/**`
- The live site URL still shows v1.2 content after v2.0 is merged to master

**Phase to address:**
Go-live track (Phase 21 or equivalent) — this is step 1, not a cleanup task.

---

### Pitfall GL-2: GitHub Actions Rebuild Loop After CF_DEPLOY_HOOK_URL Is Set

**What goes wrong:**
Once `CF_DEPLOY_HOOK_URL` is set and `deploy-on-code.yml` fires on push to `site/**`, there is a risk of a feedback loop: (1) news cron runs, commits to `data/**`, (2) if a second workflow is triggered by the push to `data/**` and that workflow touches `site/**`, it triggers a deploy, (3) the deploy does not itself push to the repo, so no loop there — BUT if `scrape-news.yml` runs on `push` to master (not just on `schedule`), any commit from it could cascade. The architecture is designed to avoid this (data commits do not trigger deploys), but adding new workflows for the composite index pipeline could accidentally reintroduce the loop.

**Why it happens:**
The anti-rebuild-loop architecture is documented but not enforced by code. A new pipeline workflow written for Phase 18 (index computation) might use `on: push` instead of `on: schedule` or `on: workflow_dispatch`.

**How to avoid:**
- All data-pipeline workflows (CEAD scraper, news scraper, index computation) must use `on: schedule` or `on: workflow_dispatch` only — never `on: push`.
- The `deploy-on-code.yml` workflow must only trigger on `paths: ['site/**']` — data changes in `data/**` must not trigger it.
- After the first news cron run post-go-live, manually inspect the Cloudflare Pages build count. If builds are incrementing on every data commit, the loop has been reintroduced.
- Add a pipeline test: the news scraper CI run must not produce a push to any path that matches `deploy-on-code.yml`'s path filter.

**Warning signs:**
- Cloudflare Pages dashboard shows builds firing every 2-6 hours (news cron frequency)
- Build count exceeds 100 in the first week after go-live
- `deploy-on-code.yml` run history shows runs triggered by the news scraper commit

**Phase to address:**
Go-live track — verify anti-loop architecture before enabling the deploy hook.

---

### Pitfall GL-3: AdSense Consent Mode Not Wired Before ADSENSE_ENABLED Flip

**What goes wrong:**
`ADSENSE_ENABLED` is currently gated (false). Flipping it to true without wiring AdSense Consent Mode violates the EU/GDPR consent requirements that Google enforces since 2024 for AdSense publishers. Google may: (a) disable ad serving on the site, (b) flag the account for policy violation, or (c) require remediation before re-enabling. The site's Spanish-language audience is primarily Chilean (not EU), but the English-language audience includes EU tourists researching Chile travel. The site uses Cloudflare CDN which serves globally — EU users will land on the site.

**Why it happens:**
Consent Mode is a separate implementation from the AdSense ad tag. Developers enable AdSense and assume consent mode is handled automatically. It is not — it requires explicit implementation of the Google Consent Mode v2 API (gtag consent commands) or a CMP (Consent Management Platform).

**How to avoid:**
- Before flipping `ADSENSE_ENABLED`, implement the minimum Consent Mode v2: add `gtag('consent', 'default', {...})` calls with `ad_storage: 'denied'` as the default, and a minimal cookie banner that sets consent to 'granted' on user acceptance.
- The cookie banner must appear for all users (not just EU-detected users) to avoid geolocation detection complexity.
- Use Google's free Consent Mode integration without a third-party CMP for this budget level — it is sufficient for the traffic volume expected at launch.
- Add a pre-AdSense checklist item: `[ ] Consent Mode v2 implemented and tested`, `[ ] cookie banner visible on desktop + mobile`, `[ ] ad-storage denied by default until consent granted`.
- Test with the Google Tag Assistant: verify that `ad_storage: denied` fires on page load before consent, and `granted` fires after.

**Warning signs:**
- AdSense account shows a "Consent Mode not implemented" warning in the AdSense dashboard
- No cookie consent banner appears when accessing the site from an incognito window
- `gtag('consent', ...)` calls are absent from the page source

**Phase to address:**
Go-live track — Consent Mode must be implemented before `ADSENSE_ENABLED` is set to true in any environment. This was flagged as `adsense-consent-mode-phase6` in STATE.md deferred items.

---

### Pitfall GL-4: Google Search Console Not Submitted for New Index/Comparator Pages

**What goes wrong:**
The v2.0 index and A-vs-B pages are added to the sitemap, built, and deployed. But GSC is not notified of the new sitemap version. Google's crawler discovers the new pages only when it next recrawls the site (which may take 4–8 weeks for new URL patterns). The A-vs-B pages in particular may be slow to be discovered because they are not yet linked from well-crawled pages (see Pitfall SEO-4).

**Why it happens:**
Sitemap submission to GSC is a manual step that developers skip because "it's in the sitemap, Google will find it." That is true — eventually. For a site still building its crawl budget and PageRank, manual submission accelerates indexing by weeks.

**How to avoid:**
- After deploying v2.0, submit the updated sitemap to GSC using the "Sitemaps" tool (both the root sitemap and the ES sitemap if separate).
- Use the "URL Inspection" tool to request indexing for 5–10 representative A-vs-B pairs within the first week of launch.
- Monitor GSC "Coverage" for the new A-vs-B URL pattern weekly for the first 4 weeks.

**Warning signs:**
- GSC shows 0 indexed A-vs-B pages 30 days after launch
- The sitemap in GSC still shows the old (pre-v2.0) page count
- "URL Inspection" shows A-vs-B pages as "not indexed" with reason "Discovered — currently not indexed"

**Phase to address:**
Go-live track, immediately after first v2.0 deploy to production.

---

### Pitfall GL-5: OneDrive Build Desync Corrupts the v2.0 Validation Run

**What goes wrong:**
This is the documented `OneDrive build artifacts desync` pitfall (memory `onedrive-build-artifacts-desync`). The repo lives inside OneDrive. When `npm run build` and `npm run validate` are run as separate commands, OneDrive syncs `dist/` between the two commands and the validate step reads a partially synced or empty `dist/`. This causes false validator failures, which may cause the developer to skip validation or mark it as "flaky." A new v2.0 schema bug (e.g., broken `featured_rates` migration) is then deployed to production without being caught.

**Why it happens:**
The build produces many files quickly. OneDrive's real-time sync tries to upload them simultaneously. On slower connections, the sync may interfere with the validate process reading from `dist/`.

**How to avoid:**
- Always chain build + validate in ONE command: `cd site && npm run build && npm run validate`. This is in STATE.md under Critical Pitfalls but must be re-documented in any v2.0 plan that adds new validators.
- Any new validator added in Phase 18 (figure-registry update, schema migration check) must be added to the same `npm run validate` chain — not as a separate script to be run independently.
- In CI (GitHub Actions), the build and validate are not affected by OneDrive (Actions runs in a Linux container) — but local development and local testing are affected.

**Warning signs:**
- Validator reports "file not found" for files that were just built
- Running `npm run validate` after `npm run build` in a separate terminal window shows different results than running them together
- The composite index validation fails locally but passes in CI

**Phase to address:**
Phase 18 (Composite Index) and Comparator phase — all new validators must be integrated into the chain from the start. Never document a new validator as a standalone command.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Storing index as a float in the commune JSON | Simple to compute | Template accidentally displays spurious precision (e.g., 47.8234) | Never — store as rounded integer from day 1 |
| Generating all 346×346 A-vs-B pairs | No pair-selection logic to maintain | Exceeds 20K Cloudflare file limit; thin content penalty; build timeout | Never |
| Using the index without a mandatory caveat block | Cleaner UI | Violates editorial/legal constraint; violates v1.3 figure-attribution requirement | Never |
| Skipping temporal alignment check for SPD/CEAD/SII | Faster pipeline | Index uses data from different years, silently misleading | Never — one-line assertion is trivial to add |
| Not updating figure-registry when adding 7 new metrics | Saves time during Phase 18 | figure-registry validator allows orphan figures; next PR adds unattributed figures | Never — update registry in the same commit that adds the metrics |
| Deploying AdSense before Consent Mode | Faster monetization | Policy violation, ad serving suspended | Never |
| Min-max normalization without distribution check | Simplest math | Outlier communes compress all others; misleading choropleth | Never for this data — use percentile rank or z-score + winsorization |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| SII PUB_COMU.xlsb (exposure proxy) | Using raw `trabajadores` count as population substitute without the HQ-domicile caveat | Cap at 10x INE population; display both adjusted and unadjusted rates; add HQ caveat to methodology |
| SPD VHC xlsx (homicide truth) | Joining on commune name string instead of CUT code | Use CUT as join key; the SPD file has commune names with accent/capitalization variations |
| Cloudflare Pages (CF_DEPLOY_HOOK_URL) | Setting the secret but not testing the first deploy | After setting, push a trivial change and verify CF dashboard shows a new triggered build before merging real work |
| Google AdSense + Consent Mode v2 | Enabling AdSense ad tag without defaulting `ad_storage: denied` | Implement `gtag('consent', 'default', {ad_storage: 'denied'})` before the AdSense tag; add a consent banner |
| Astro getStaticPaths (A-vs-B) | Returning all 346×345 pairs without filtering | Use a curated `comparator-pairs.json` allowlist; assert `paths.length < 2000` in the function |
| Astro i18n + A-vs-B slugs | Using commune name strings in URLs (causes accent/encoding issues and untranslatable ES slugs) | Use CUT codes in URL slugs (e.g., `/compare/13110-vs-13119/`); display names in page content |
| figure-registry validator | Adding new index metrics to pages without registering them in figure-registry | Update figure-registry.mjs in the same PR that adds the new metric to any template |

---

## "Looks Done But Isn't" Checklist

- [ ] **Composite index editorial framing:** Every page displaying the index has a mandatory caveat block (underreporting, SII HQ-domicile, small-denominator volatility) — verify it renders in both EN and ES
- [ ] **Forbidden-language CI validator extended:** Validator also catches "safest," "más segura," "most dangerous," "más peligrosa" as absolute (not just "safe/dangerous") — run on generated composite index pages
- [ ] **Normalization distribution check:** Assert that the 25th percentile of index scores is >10% of the maximum — if not, outlier distortion is present
- [ ] **SII exposure cap:** Assert no commune has `sii_workers > ine_population * 10` — catches wrong joins or missing HQ-domicile filter
- [ ] **tipoVal assertion:** Cross-check new CEAD fetches against existing `featured_rates` national totals — agree within 5%
- [ ] **Schema migration complete:** All 5+ consumers of `featured_rates` (commune panel, choropleth, Astro template, figure-registry, pytest) updated and verified with the new 7-metric schema
- [ ] **A-vs-B page count:** `getStaticPaths` returns fewer than 2,000 entries; build produces fewer than 18,000 total files
- [ ] **A-vs-B hreflang reciprocity:** Every EN A-vs-B page has a corresponding ES page, and both hreflang to each other — run hreflang validator on a 10% sample
- [ ] **A-vs-B internal links:** Every generated A-vs-B page is linked from at least one other page in the build output
- [ ] **CF_DEPLOY_HOOK_URL verified:** After setting the secret, a test push triggered a Cloudflare build — confirm in CF dashboard before merging v2.0
- [ ] **Rebuild loop check:** After first news cron run post-go-live, confirm CF build count did NOT increment from the data commit
- [ ] **AdSense Consent Mode:** `gtag('consent', 'default', {ad_storage: 'denied'})` fires before AdSense tag on first page load — verify in Network tab and Tag Assistant
- [ ] **SPD/CEAD/SII year alignment:** Pipeline assertion confirms all three sources use the same reference year before index is computed
- [ ] **Index precision:** No rendered page shows the index to more than 1 decimal place — grep the built HTML for patterns like `\d+\.\d{2,}`

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Index implies absolute safety verdict — editorial blowback | HIGH (reputational; requires methodology rewrite + re-crawl) | Add mandatory caveat blocks; rename index to "reported crime burden"; request GSC re-crawl; update og:descriptions |
| Min-max normalization outlier distortion — choropleth useless | MEDIUM (data pipeline fix + rebuild) | Switch to percentile rank; recompute index; rebuild; redeploy; takes 1-2 days |
| SII HQ-domicile distortion discovered after launch | MEDIUM (methodology update + partial recompute) | Add cap + caveat; recompute affected communes; update methodology page; publish correction note |
| Schema migration breaks commune panel — live site shows undefined | HIGH (user-facing; immediate rollback needed) | Revert `featured_rates` to previous schema in git; redeploy; fix migration; re-deploy |
| A-vs-B pages deindexed for thin content | HIGH (4-8 week recovery) | Add content depth to template; remove thin pages from sitemap; request removal in GSC; wait for re-evaluation |
| A-vs-B page count exceeds Cloudflare limit | MEDIUM (build fails; no user impact yet) | Reduce pair allowlist to <18,000 total files; rebuild; redeploy |
| CF_DEPLOY_HOOK_URL never set — site stale post-merge | LOW (ops task) | Set secret in GitHub repo settings; trigger manual CF deploy from dashboard; takes <1 hour |
| AdSense disabled for missing Consent Mode | MEDIUM (monetization loss during remediation) | Implement Consent Mode v2; submit for policy review; 1-2 week remediation cycle |
| Rebuild loop burns Cloudflare build quota | LOW (ops; no user impact) | Identify triggering workflow; change trigger to `schedule` or `workflow_dispatch`; remaining quota resets at month boundary |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| CI-1: Index implies absolute verdict | Phase 18 (Composite Index) — editorial framing step | Forbidden-language CI validator run on all index pages |
| CI-2: Normalization outlier distortion | Phase 18 — normalization validation step | pytest: 25th percentile > 10% of max; choropleth preview |
| CI-3: SII HQ-domicile distortion | Phase 18 — SII join + cap logic | pytest: no commune `sii_workers > ine_population * 10`; methodology caveat present |
| CI-4: CEAD tipoVal double-count | Phase 18 — pipeline plan | Cross-check assertion vs existing `featured_rates` national total |
| CI-5: Spurious precision | Phase 18 — schema design | grep built HTML for `\d+\.\d{2,}` in index display contexts |
| CI-6: Schema migration breaks consumers | Phase 18 — migration checklist | All 5 consumers verified; TypeScript types pass `@astrojs/check`; all 12 validators green |
| CI-7: SPD/CEAD/SII temporal misalignment | Phase 18 — pipeline assertions | pytest: `spd_year == cead_year == sii_year` assertion passes |
| CI-8: Micro-commune choropleth distortion | Phase 18 — color scale logic | Choropleth preview: distribution check; >3 color bands visible for >80% of communes |
| SEO-1: A-vs-B page count explosion | Comparator phase — pair selection design | `getStaticPaths.length < 2000`; total build files < 18,000 |
| SEO-2: A-vs-B thin content | Comparator phase — content schema design | 400+ words of non-swappable content per pair; 10-page GSC indexing test |
| SEO-3: A-vs-B hreflang reciprocity | Comparator phase — slug strategy + validator extension | Hreflang validator run on 10% sample of generated A-vs-B pages |
| SEO-4: A-vs-B orphan pages | Comparator phase — internal linking design | Site crawl: every A-vs-B page has ≥1 incoming internal link |
| GL-1: CF_DEPLOY_HOOK_URL unset | Go-live track — step 1 | CF dashboard shows triggered build after test push |
| GL-2: Rebuild loop reintroduced | Go-live track — workflow audit | CF build count does not increment on data-only commits |
| GL-3: AdSense Consent Mode missing | Go-live track — pre-AdSense checklist | Tag Assistant: `ad_storage: denied` on page load before consent |
| GL-4: GSC not submitted for new pages | Go-live track — post-deploy | GSC sitemap shows updated page count; representative A-vs-B URLs requested for indexing |
| GL-5: OneDrive build desync | Phase 18 + Comparator phase — validator integration | All validators run inside single chained command; no standalone validator scripts documented |

---

## Sources

- `.planning/PROJECT.md` — v2.0 milestone context, editorial constraints, key decisions, SEED-001 locked constraints
- `.planning/STATE.md` — Phase 17 Wave-0 decisions (tipoVal, SII HQ caveat, SPD VHC source), Critical Pitfalls to Avoid, deploy-hook gap, OneDrive desync, localized-slug pitfall
- `CLAUDE.md` — Cloudflare Pages 20K file limit, What NOT to Use, forbidden-language constraint
- Memory `prod-deploy-hook-secret-gap` — CF_DEPLOY_HOOK_URL gap history
- Memory `onedrive-build-artifacts-desync` — build+validate chaining requirement
- Memory `i18n-localized-slug-pitfall` — getRelativeLocaleUrl does not translate ES slugs
- Memory `astro-script-no-expr-interpolation` — Astro template data-passing constraints
- Prior v1.0 PITFALLS.md (2026-06-12) — thin content, hreflang, rebuild loop, editorial stigmatization (foundational; apply to v2.0 by extension)
- Google AdSense Consent Mode v2 requirements (2024 enforcement) — ad_storage default denied requirement

---
*Pitfalls research for: v2.0 Composite Index, Commune Comparator, A-vs-B SEO, Go-live — Chile Safety Map*
*Researched: 2026-06-19*
