# Pitfalls Research

**Domain:** Bilingual crime-data visualization + programmatic SEO platform (Chile Safety Map)
**Researched:** 2026-06-12
**Confidence:** HIGH

---

## Critical Pitfalls

### Pitfall 1: Programmatic Thin Content — Google Deindexes Template Pages

**What goes wrong:**
346 commune pages + 16 region pages get generated, each swapping only the place name into an identical template. Google classifies the entire program as "scaled content abuse" and deindexes 80-98% of pages within 3 months. Organic traffic never materializes despite correct technical SEO.

**Why it happens:**
Developers assume that having real data (CEAD crime rates) is sufficient differentiation. It is not. Google's scaled content abuse policy (hardened in March 2024) targets pages where "template content exceeds unique content" — even if the injected data is factually accurate. The threshold that triggers penalties is less than 30% unique elements per page and under 300 words of substantive content.

**How to avoid:**
Each commune page must have multiple data dimensions that are unique to that commune — not just swapped values but genuinely different narrative context. Minimum per page: (1) actual crime rate vs. national/regional average with qualitative framing, (2) trend direction (rising/falling/stable with year span), (3) which crime types dominate relative to peers, (4) regional context sentence, (5) nearest comparable commune for calibration. Aim for 500+ words with 30-40% content that is impossible to replicate by name-swapping. Deploy in staged batches of 10-20 pages first, verify Google Search Console indexing before launching all 346.

**Warning signs:**
- Google Search Console shows hundreds of pages in "Discovered — currently not indexed" state weeks after launch
- Pages getting crawled but not indexed despite correct sitemaps
- Zero impressions in GSC for commune-level pages after 60 days

**Phase to address:**
Template design phase (before generating any pages). Define content schema with 5+ unique data dimensions per commune before writing the Astro template.

---

### Pitfall 2: CEAD Endpoint Silently Changes — Scraper Fails Quietly

**What goes wrong:**
The CEAD PHP endpoints (`get_estadisticas_delictuales.php`, `get_estadisticas_delictuales_mapa.php`) are undocumented, unofficial, and subject to change without notice. An endpoint parameter is renamed, a response key changes, or the HTML table structure is reorganized. The GitHub Actions cron job runs, produces no error (HTTP 200), commits stale/empty JSON, and the site silently serves months-old data or zeros — with no alert.

**Why it happens:**
PHP endpoints that drive a government dashboard are maintained for the dashboard, not for external consumers. There is no SLA, no versioning, and no changelog. "Silent 200" failures are the norm — the server returns a page but the data shape is wrong. Without schema validation after extraction, the pipeline passes.

**How to avoid:**
After every CEAD scrape, run schema validation before committing: assert expected keys exist, row count is within historical range (e.g., not zero, not 10x previous), numeric values fall within plausible bounds (rates between 0 and 5000 per 100k). Commit only if validation passes; otherwise fail the GitHub Actions job loudly (non-zero exit), post a GitHub issue or send an email alert via Actions, and keep the previous good JSON intact. Store raw responses alongside processed JSON so you can re-parse after a schema fix without re-scraping. Version your scraper selectors separately from business logic.

**Warning signs:**
- Any scraper run that produces a JSON file significantly smaller than the previous run
- National totals that drop to zero or spike 10x
- Commune count in output differs from the known 346

**Phase to address:**
CEAD scraper phase. Bake validation in from the first working version; retrofitting it later is dangerous.

---

### Pitfall 3: GitHub Actions Cron Creates Infinite Rebuild Loop

**What goes wrong:**
The workflow runs on schedule, fetches new news data, commits JSON to the repo, and Cloudflare Pages (configured with Git integration) triggers a full rebuild on every commit. Every few hours the pipeline commits, which triggers a rebuild, which consumes Cloudflare Pages free-tier build credits (500 builds/month cap, 20-minute timeout per build). The site burns through its monthly builds in days. Worse: if a secondary workflow triggers on push events, an infinite loop is possible.

**Why it happens:**
The default Cloudflare Pages + GitHub integration is "rebuild on any push to main." Developers set up data-commit workflows without disabling this default, not realizing that data commits are indistinguishable from code commits to the Pages integration.

**How to avoid:**
Disable Cloudflare Pages Git integration for automatic rebuilds. Instead, use Wrangler CLI (`wrangler pages deploy ./dist`) called explicitly from within the GitHub Actions workflow, only after data has been fetched and validated. This gives full control over when a build fires. For the CEAD scraper (quarterly), trigger a rebuild. For news RSS (every few hours), consider whether a rebuild is necessary every run or only when new unique incidents are found. Use a `[skip ci]` commit message convention for data-only commits if the Git integration must remain enabled. Set `paths-ignore` in workflow triggers to prevent push-triggered workflows from re-running when the workflow itself commits data.

**Warning signs:**
- Cloudflare Pages dashboard shows builds firing every few hours
- Build count approaching 400+ in the first week of the month
- GitHub Actions run history shows push-triggered runs immediately after cron runs

**Phase to address:**
CI/CD setup phase. Configure the deployment strategy before enabling any cron jobs.

---

### Pitfall 4: LLM Hallucinates Commune Names in News Extraction

**What goes wrong:**
DeepSeek v4 extracts a crime incident from a news article and assigns it to a commune that is mentioned in the article tangentially (e.g., a criminal was from Maipú but the incident happened in Pudahuel) or invents a plausible-sounding commune that does not exist. The incident pin appears on the map at the wrong location. At scale, over weeks, a significant fraction of incident pins are geographically wrong. If a pin is placed in a specific commune for a serious crime that did not occur there, it constitutes factual inaccuracy that could harm that location's reputation.

**Why it happens:**
News articles about crime routinely mention multiple places (where the suspect lives, where they were arrested, where the crime occurred, where the victim is from). LLMs, including strong models, conflate these roles at a measurable error rate. The research literature documents "county-state confusion," toponym ambiguity (same name in multiple regions), and entity-role confusion as leading causes of location extraction errors. At temperature > 0.1, format drift also introduces inconsistent commune name spellings that fail to match your canonical commune list.

**How to avoid:**
(1) Require DeepSeek to output the commune from a closed canonical list — include the full 346-commune list in the prompt as valid values, making it a classification task rather than open-ended extraction. (2) Set temperature to 0.0 for all structured extraction calls. (3) Use a two-step pipeline: first extract the event description in free text, then classify commune from that description against the closed list. (4) Add a confidence score field; discard or flag as "location uncertain" if confidence is below threshold. (5) Validate that the extracted commune name exactly matches your canonical list before committing — reject incidents that fail validation rather than guessing. (6) On the front-end, display incidents as "reported in [commune] area" with a link to the source article, making the original source verifiable.

**Warning signs:**
- Incidents appearing in communes with no plausible news coverage
- Same incident appearing with different commune assignments across two sources
- Commune names in output JSON that are not in your 346-commune canonical list

**Phase to address:**
News pipeline design phase. The closed-list constraint and canonical validation must be designed in before the first LLM call, not added after discovering wrong pins.

---

### Pitfall 5: Frequency vs. Rate — Ranking Communes by Absolute Crime Count

**What goes wrong:**
The ranking displays communes sorted by total crime incidents. Santiago (commune), San Bernardo, Maipú, and Puente Alto appear at the top of every ranking because they have the largest populations. Small coastal tourist communes with high per-capita rates appear safe. The ranking is statistically meaningless but looks authoritative. Users make decisions based on it. Media coverage cites it. The project's credibility is damaged when a criminologist or journalist points out the methodological error.

**Why it happens:**
Absolute counts are easier to sort and more intuitive to display. Developers use `ORDER BY frecuencia DESC` without thinking through the population normalization step. CEAD provides both frequency and rate columns — it is easy to accidentally use the wrong one.

**How to avoid:**
The canonical metric for all rankings, choropleth coloring, and comparisons must be the rate per 100,000 inhabitants, not the absolute frequency. This is CEAD's own standard and the FBI/international standard. Add a data contract test: if the top-10 communes in any ranking include more than 3 of the 10 most-populous communes in Chile and no adjustment has been made, fail the data pipeline. On the front-end, always display the rate prominently and include a tooltip or footnote explaining what it means. For very small communes (population < 5,000), flag that rates are volatile (one extra incident can shift the rate dramatically) and avoid presenting them in national top-10 rankings without a minimum population filter.

**Warning signs:**
- Santiago, Maipú, Pudahuel consistently in positions 1-5 of the "most dangerous" ranking
- Any commune with population under 2,000 appearing in a national ranking
- The choropleth coloring high-density urban cores uniformly darker than rural areas regardless of year

**Phase to address:**
Data processing and display phase. Encode the per-100k requirement as a constant in the data pipeline, not a display-layer decision.

---

### Pitfall 6: Hreflang Misconfiguration Silently Kills Bilingual Indexing

**What goes wrong:**
hreflang tags are missing the reciprocal return link (page A references page B but B does not reference A), or the language codes are wrong (`es-CL` used for all Spanish pages when the target audience is primarily Chile, but the English pages use `en` instead of `en-US` or `en`), or the canonical tag on Spanish pages points to the English equivalent. Google ignores all hreflang tags on the affected pages. Spanish and English versions of the same page compete against each other, split link equity, and neither ranks well. A study found 67% of multilingual sites have broken hreflang.

**Why it happens:**
Astro's i18n support generates pages, but hreflang requires each page to declare its own language and all its alternates — including itself. When templates are written quickly, the self-referential tag is often omitted, or the alternate URL patterns are wrong (e.g., `/en/commune/santiago` vs `/commune/santiago` depending on the routing strategy chosen).

**How to avoid:**
(1) Use `es` and `en` language codes (not `es-CL` and `en-US` unless you are specifically targeting those regions exclusively — for a Chile-focused site with English for international tourists, `es` and `en` are correct). (2) Every page must have: a self-referential hreflang, hreflang pointing to the alternate language, and a canonical pointing to itself (not the alternate). (3) Include hreflang in both the `<head>` and the XML sitemap — they must be in sync. (4) Write a build-time test that crawls the generated output and verifies: every hreflang has a reciprocal, all URLs in hreflang tags resolve to actual pages, canonical does not conflict with hreflang. (5) Run an hreflang checker after every significant template change.

**Warning signs:**
- Google Search Console showing the English version indexed in Spanish search results
- Both language versions appearing for the same query (splitting impressions)
- Sitemap hreflang count not matching `<head>` hreflang count in a page audit

**Phase to address:**
Astro i18n setup phase. Validate hreflang correctness on 5 sample pages before generating all 700+ bilingual pages.

---

### Pitfall 7: Leaflet GeoJSON Rendering Causes Mobile Map Unusability

**What goes wrong:**
The full commune GeoJSON (the project's existing `geo-data.js` is ~222 KB) is loaded and rendered as a choropleth. On desktop this works. On mid-range Android phones (the primary device of Chilean domestic users), initial render takes 8-15 seconds and hover/click interactions freeze the UI. The map — the core product — is unusable for a significant portion of the target audience.

**Why it happens:**
Leaflet renders SVG paths for every polygon. With 346 communes, each potentially having complex coastline/border geometries, the SVG node count is high. React-Leaflet adds re-render overhead: if the style function or `onEachFeature` callback is not memoized, every hover event re-renders the entire GeoJSON layer. The 222 KB file size also means a noticeable network delay on mobile connections.

**How to avoid:**
(1) Simplify GeoJSON geometry: use `mapshaper` or `toposjon` to reduce precision — the existing 222 KB file can typically be reduced to 80-100 KB with no perceptible visual difference at choropleth zoom levels. (2) Wrap the Leaflet GeoJSON style function and `onEachFeature` in `useCallback()` and memoize the GeoJSON component with `useMemo()` to prevent re-renders on hover. (3) Implement two-level loading: load region polygons (16 shapes) first for immediate render, then load commune polygons lazily when the user zooms in or selects a region. (4) Serve GeoJSON from Cloudflare's CDN with appropriate cache headers, not from the same bundle as the application. (5) Test on a mid-range Android device at 3G speeds before declaring the map feature complete.

**Warning signs:**
- Chrome DevTools performance profile shows GeoJSON layer repaint on every mouse move
- First contentful paint of the map exceeds 5 seconds on throttled 3G
- GeoJSON file > 150 KB in the production bundle

**Phase to address:**
Map component phase. Geometry simplification must happen before the Astro island is built, not as a performance optimization later.

---

### Pitfall 8: News Deduplication Failure — Same Incident Appears Multiple Times

**What goes wrong:**
Emol, BioBío, Cooperativa, T13, and 24Horas all cover the same robbery. The RSS pipeline creates five separate incident records. The map shows five pins clustered at the same location for one event. Over time, high-profile incidents accumulate dozens of duplicate pins. The "recent incidents" layer becomes noise rather than signal, and the cluster counts on the map mislead users about incident frequency.

**Why it happens:**
Simple deduplication by URL catches only identical links. News agencies publish the same story under different URLs, often with slight headline variations. Cross-source deduplication requires semantic similarity — which adds latency and cost if done naively.

**How to avoid:**
Implement a two-pass deduplication strategy. Pass 1 (cheap, synchronous): normalize and hash the title after stripping dates, crime keywords, and comune names — reject if the hash was seen in the last 72 hours. Pass 2 (LLM-assisted, for near-duplicates that pass hash check): include a deduplication step in the same DeepSeek prompt that classifies a new incident, asking the model to assess whether the event matches any of the last 10 incidents for the same commune on the same day. Maintain a rolling incident store (JSON file) with canonical incident IDs, source URLs, and a "covered by" array for cross-source duplicates. Display only one pin per canonical incident, linking all sources in the popup.

**Warning signs:**
- More than 2 pins in the same commune on the same day for a high-profile event
- The incident JSON file growing faster than the average daily crime news volume would suggest
- Users reporting "I see the same story multiple times"

**Phase to address:**
News pipeline phase, specifically in the DeepSeek prompt design and the incident store schema.

---

### Pitfall 9: AdSense Rejection for Sensitive Crime Content

**What goes wrong:**
The site is built, indexed, and traffic begins to arrive. The AdSense application is rejected under the "Sensitive Events" or "Inappropriate content" policy — specifically the clause covering content that depicts "violence" or "shocking accounts." Crime statistics sites occupy a gray zone: the data itself is government statistics, but the topic is crime, and the framing matters enormously for AdSense reviewers.

**Why it happens:**
AdSense policy distinguishes between news/statistics journalism (generally acceptable) and sensationalistic crime content (rejected). Sites that use emotionally charged language, show crime incident pins prominently on the homepage without context, or lack clear editorial framing risk automated or manual rejection. A domain like "ischilesafe.com" with pins labeled "assault," "robbery," "homicide" without a methodology page or clear data-journalism framing can trigger the Sensitive Events policy.

**How to avoid:**
(1) Apply for AdSense only after the methodology page is live, explaining that all data comes from official Chilean government sources (CEAD / Ministerio de Seguridad Pública). (2) Frame the site explicitly as a "data journalism and public safety research tool," not a crime tracker. (3) Avoid graphic crime incident descriptions — the news pin popup should show "incidente de [tipo de delito] reportado" with a link to the source, not a detailed description. (4) Ensure all required legal pages exist before applying: Privacy Policy, Terms of Use, About, Methodology, Contact. (5) Make sure the homepage prominently features the statistical/choropleth map with official data framing rather than the incident pins — lead with data, not events. (6) If rejected, request manual review with the methodology page URL; AdSense allows reconsideration, and data/statistics sites typically pass manual review when they have clear editorial framing.

**Warning signs:**
- Homepage copy uses words like "danger," "violence," "crime hotspot" without statistical framing
- Incident pins are the most visually prominent element on the homepage
- Missing About/Methodology pages at time of AdSense application

**Phase to address:**
Content and editorial design phase (pre-launch). Write the methodology page and editorial framing guidelines before applying for AdSense.

---

### Pitfall 10: Territorial Stigmatization — Legal and Reputational Risk

**What goes wrong:**
A commune (e.g., La Pintana or El Bosque) appears prominently labeled as "most dangerous" in a headline, social media share, or Google snippet. Residents, community organizations, or local governments object publicly or legally. Under Chilean law, defamation can be committed via internet publication. Even if the data is accurate, presenting it in a reductive or absolutist way that damages a community's reputation creates both reputational risk for the project and potential legal exposure.

**Why it happens:**
Developers treat this as a data accuracy problem ("the data is correct, we're fine") rather than an editorial responsibility problem. The academic literature on crime maps documents how spatial stigmatization causes real harm to communities — property values, business investment, tourism — and generates backlash against the platforms that publish the maps.

**How to avoid:**
(1) Never use absolute superlatives — no "most dangerous," "most unsafe," "crime-ridden." Use "highest reported incidence rate" with a timeframe. (2) Every ranking or comparative page must include a caveat about underreporting, the distinction between reported and actual crime, and the limitations of comparisons (this is also what differentiates the site from thin content). (3) Disable social media og:title and og:description on commune pages from auto-generating "Is [X] dangerous?" framings — write them manually. (4) The PROJECT.md already lists the required editorial vocabulary — enforce it at the template level so it cannot be bypassed accidentally. (5) Consult Chilean data protection law (Ley 19.628 and its 2022/2024 updates) regarding publication of data that identifies or impacts communities.

**Warning signs:**
- Any generated og:title containing "dangerous," "safe," "peligrosa," or "segura" as an absolute
- Social media previews of commune pages that look like crime sensationalism
- Ranking page titles that read like tabloid headlines

**Phase to address:**
Editorial guidelines phase (before template writing). Define a content style guide that all programmatic templates must follow, with automated checks in the build pipeline.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Commit raw CEAD HTML alongside processed JSON | Skip building a re-parse mechanism | Storage bloat in git repo (hundreds of MB over years) | Acceptable in MVP if you store only the final trimester per year |
| Single monolithic GeoJSON with all communes | Simpler initial map code | Unmaintainable performance on mobile, hard to do region-level lazy loading | Never for production — simplify geometry before shipping |
| Hardcode DeepSeek prompt in the scraper script | Faster to write | Cannot A/B test prompts, cannot version or audit prompt changes without code deploys | MVP only, with a TODO to externalize |
| No incident expiration / TTL in the news JSON | Simpler pipeline | Incident store grows unbounded; old incidents stay on map forever | Never — set a 30-day rolling window from day one |
| Generate all 700+ pages in one Astro build pass | Simpler build config | Out-of-memory errors if data JSON is loaded all at once into build context | Never — use per-page lazy reads from disk |
| Apply AdSense before methodology page is ready | Slightly faster to market | High rejection risk, 30-day waiting period between reapplications | Never |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| CEAD PHP endpoints | Sending requests without delays, triggering rate limiting or IP blocks on a government server | Use `time.sleep(2-5)` between requests, randomize user-agent, avoid hammering during Chilean business hours |
| CEAD `descarga=true` Excel endpoint | Assuming the Excel format matches the JSON endpoint structure | Parse and validate both independently; they have different column naming conventions |
| DeepSeek API | Using the same prompt for both classification and deduplication in a single call | Separate concerns: one prompt for extraction/classification, one for deduplication — easier to debug and iterate |
| Cloudflare Pages + GitHub Actions | Using GitHub's push event to trigger Pages builds when the workflow commits data | Disable Pages Git integration; deploy explicitly via Wrangler CLI in the workflow |
| Astro i18n + hreflang | Letting Astro generate hreflang automatically without verifying reciprocal links | Write a build-time validation script that checks every generated page's hreflang consistency |
| Leaflet + React islands | Importing Leaflet in a non-`client:only` Astro island (Leaflet requires `window`) | Always use `client:only="react"` for Leaflet islands; Leaflet cannot run during SSR |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading full commune GeoJSON (~222 KB) on mobile | Map takes 8-15s to render; interactions freeze | Simplify geometry to <100 KB; lazy-load communes on zoom | Any mid-range Android phone on 3G |
| React-Leaflet re-renders GeoJSON on every hover | CPU spike, janky hover highlighting | Memoize style function with `useCallback`; wrap GeoJSON in `useMemo` | With 50+ polygon choropleth, any device |
| Astro loading all 346 commune JSON files into memory at build time | `JavaScript heap out of memory` during `astro build` | Use `getStaticPaths` with per-route lazy file reads, not a single global import | Sites > 100 programmatic pages |
| Committing cumulative incident JSON that grows unbounded | Git repo grows to GB over months; clone time degrades CI | Enforce 30-day TTL on incidents; trim before committing | After ~6 months of daily commits |
| GitHub Actions cron running every 2 hours for RSS even when no new articles | 500 free build minutes/month consumed; no value added | Check for new articles before triggering a rebuild; only rebuild when new unique incidents are found | Immediately on high-frequency cron setup |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing DeepSeek API key in the workflow YAML directly | Key exposed in public repo; unauthorized API usage and billing | Store in GitHub Actions Secrets; access via `${{ secrets.DEEPSEEK_API_KEY }}` |
| No input validation on the commune query parameter if any server-side logic is added later | Injection risk if the project ever adds a server component | Validate all commune identifiers against the canonical list before use |
| Publishing LLM-extracted incident data without source attribution | Defamation liability if an incident is incorrectly assigned to a location | Every incident pin must link to the original source article; never publish LLM-generated summaries without a source link |
| Scraping CEAD without rate limiting | Server overload, IP ban, or being seen as a DoS attack on government infrastructure | Minimum 2-second delay between requests; only run full scrapes during off-peak hours (midnight CL time) |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing absolute crime counts in the commune panel without per-100k rates | Users incorrectly conclude large cities are dramatically more dangerous than small communes | Always display rate per 100k as the primary metric; show absolute count as secondary with a tooltip explaining the difference |
| Incident pins visible at country zoom level | Map looks covered in dots; the choropleth (the main value) is obscured | Hide individual incident pins below zoom level 10; show cluster counts only; reveal individual pins at commune zoom |
| English-only error states on a bilingual site | Spanish-first users see error messages in English, breaking trust | All UI states (loading, error, no data, empty) must be translated in both languages from day one |
| Ranking page with no "minimum population" filter | A commune of 3,000 people with one murder rates as the most dangerous in Chile at 33 per 100k | Apply a minimum population threshold (e.g., 10,000 residents) for national rankings; explain the filter |
| Choropleth with a linear color scale on skewed data | One outlier commune makes all others look identical (white/pale) | Use quantile or logarithmic color scale; CEAD data is heavily right-skewed |

---

## "Looks Done But Isn't" Checklist

- [ ] **hreflang:** Verify every page has a self-referential tag AND a reciprocal tag on the alternate language version — run the hreflang checker, not just visual inspection
- [ ] **CEAD scraper validation:** Confirm the scraper fails loudly (non-zero exit, no commit) when the data shape is wrong — test by intentionally breaking a parser assertion
- [ ] **Choropleth color scale:** Verify the scale uses quantile/log distribution, not linear — inspect whether rural communes with low absolute counts appear meaningfully differentiated
- [ ] **Cloudflare Pages rebuild loop:** Confirm data-commit actions do NOT trigger automatic Pages rebuilds — check the Pages dashboard build history after the first cron run
- [ ] **Incident deduplication:** Manually verify that the same incident from two different RSS sources appears as one pin, not two
- [ ] **Mobile map performance:** Test the choropleth on a real mid-range Android device (not Chrome DevTools emulation) before launch
- [ ] **Methodology page live before AdSense:** Confirm `/methodology/` (EN) and `/es/metodologia/` (ES) are indexed before submitting the AdSense application
- [ ] **Rate metric used in rankings:** Run a query against the ranking data — if the top-5 includes Santiago, Maipú, and Puente Alto in every category, you are ranking by frequency not rate

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Google deindexes programmatic pages for thin content | HIGH (weeks of recovery time) | Add content depth to template, request removal of affected URLs from GSC, resubmit sitemap, wait 4-8 weeks for re-evaluation |
| CEAD scraper serves stale data silently | MEDIUM | Re-run scraper with validation, restore previous good JSON from git history, audit all scraped fields against current CEAD UI |
| Cloudflare Pages build credit exhausted | LOW | Upgrade to paid plan ($20/mo) or pause rebuilds until next billing cycle; switch to Wrangler CLI deploy immediately |
| LLM assigns incidents to wrong communes at scale | HIGH (trust/reputation damage) | Add confidence filtering, mark all existing incidents as "unverified," re-process with corrected prompt, display "source" links prominently |
| AdSense rejected | MEDIUM | Revise editorial framing, ensure methodology page is live, wait 30 days, reapply with manual review request |
| CEAD endpoint permanently changes or disappears | HIGH | Contact CEAD directly (spd-cead@minsegpublica.gob.cl); check datos.gob.cl for official dataset exports; fall back to Excel download endpoint; document that data is frozen at last successful scrape |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Thin content penalty on programmatic pages | Template design (pre-generation) | Deploy 10 sample pages, verify GSC indexes them within 4 weeks |
| CEAD endpoint schema drift / silent failure | Scraper implementation | Intentionally break a field, confirm pipeline fails loudly and does not commit |
| GitHub Actions infinite rebuild loop | CI/CD setup | Check Cloudflare Pages dashboard after first cron run — build count should not increment |
| LLM commune hallucination | News pipeline design | Manual audit of 50 extracted incidents against source articles |
| Frequency vs. rate ranking error | Data processing layer | Query the ranking output — top-5 must not be dominated by largest-population communes |
| hreflang misconfiguration | Astro i18n setup | Run hreflang checker tool on all generated pages before full deployment |
| Leaflet GeoJSON mobile performance | Map component implementation | Test on real mid-range Android at 3G before declaring done |
| News incident deduplication failure | RSS pipeline design | Publish a breaking national story, verify it appears as one pin from 5 sources |
| AdSense rejection for sensitive content | Editorial guidelines + methodology page | Methodology page live and indexed; homepage framing review before applying |
| Territorial stigmatization / legal risk | Editorial guidelines | Automated build check for forbidden superlative language in og:title and meta descriptions |

---

## Sources

- [The Hidden Dangers of Programmatic SEO — AirOps](https://www.airops.com/blog/hidden-dangers-of-programmatic-seo)
- [Programmatic SEO Traffic Cliff Guide — Passionfruit](https://www.getpassionfruit.com/blog/programmatic-seo-traffic-cliff-guide)
- [Programmatic SEO Mistakes: 9 Reasons Your Pages Aren't Ranking — SEOmatic](https://seomatic.ai/blog/programmatic-seo-mistakes)
- [Common Hreflang Mistakes — Search Engine Journal](https://www.searchenginejournal.com/ask-an-seo-what-are-the-most-common-hreflang-mistakes/556455/)
- [Beyond the Surface: Uncovering Implicit Locations with LLMs — arXiv](https://arxiv.org/pdf/2502.14660)
- [Missing the Community for the Dots: Newspaper Crime Maps and Territorial Stigma — Springer](https://link.springer.com/article/10.1007/s10612-023-09720-w)
- [How to Render Huge GeoJSON Datasets on a Map — Medium](https://danw1ld.medium.com/how-to-render-huge-geojson-datasets-on-a-map-part-2-be1edf555034)
- [React Leaflet Map Performance Issues — tmsvr.com](https://tmsvr.com/react-leaflet-map-performance-issues/)
- [Scheduled Builds for Cloudflare Deployments with GitHub Actions — Medium](https://medium.com/medialesson/scheduled-builds-for-cloudflare-deployments-with-github-actions-93341a112432)
- [Cloudflare Pages Limits — Official Docs](https://developers.cloudflare.com/pages/platform/limits)
- [AdSense Program Policies — Google](https://support.google.com/adsense/answer/48182?hl=en)
- [Understanding Crime Rates — PlainCrime](https://plaincrime.com/guides/understanding-crime-rates)
- [More crime in cities? On the scaling laws of crime — arXiv](https://arxiv.org/pdf/2012.15368)
- [Get Reliable JSON from LLMs — GenAI Unplugged](https://genaiunplugged.substack.com/p/structured-outputs-json-prompts-guide)
- [Criminal Defamation Laws in South America — CPJ](https://cpj.org/reports/2016/03/south-america/)
- [Tutorial R datos delincuencia Chile (CEAD) — GitHub](https://github.com/bastianolea/tutorial_r_datos_delincuencia)
- [Articles deduplication — Newscatcher API](https://www.newscatcherapi.com/docs/news-api/guides-and-concepts/articles-deduplication)
- [Scaling Astro to 10,000+ Pages — Astro Blog](https://astro.build/blog/experimental-static-build/)

---
*Pitfalls research for: bilingual crime-data visualization + programmatic SEO platform (Chile Safety Map / ischilesafe.com)*
*Researched: 2026-06-12*
