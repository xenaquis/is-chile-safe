---
phase: 36
plan: 07
artifact: gnews decode measurement (FID-04, V-10 fix step 3)
measured: 2026-09-25
script: pipeline/experiments/measure_gnews_decode.py
seed: 3607
---

# 36-07 Task 1 — Google-News decode success rate (n=50)

Measured BEFORE the ingest wiring (V-10 fix step 3). Read-only on data/ (git diff -- data/ empty), no LLM calls. The only network targets were news.google.com (the article GET and the hardcoded batchexecute POST, T-gf7-04). No publisher URL was fetched.

## Method

- **Population:** incidents in data/incidents/current.json at HEAD a00058a whose `url` host is news.google.com. There are 435 distinct URLs (V-10 measured 426 on 2026-09-24; the cron has added more since).
- **Sample:** `random.Random(3607).sample(sorted(urls), 50)`.
- **Per URL:**
  - First `gnews_decoder._try_old_format(url)` (offline).
  - If that is not usable, `decode_gnews_url(url, session=requests.Session()` with `User-Agent = fulltext.USER_AGENT`, `timeout=10)`.
  - `fulltext.REQUEST_DELAY` = 1.5 s between URLs.
- **Usable:** the result is non-empty, `store.is_safe_url` accepts it (http/https), and its host is not news.google.com.

## Result

| outcome | count |
|---|---|
| old_format (offline token) | 0 |
| new_format (GET + batchexecute) | 50 |
| failed | 0 |
| **total** | **50** |

success_rate: 50/50

- **Wall time:** 79.8 s for 50 URLs, including 49 × 1.5 s courtesy sleeps. Decode time per URL: median 0.12 s, max 0.24 s.
- **Checks:** all 50 decoded URLs have a host different from news.google.com and pass `is_safe_url`.
- **Hosts:** 38 distinct publisher hosts. The top ones are miradiols.cl 4, soychile.cl 4, then adnradio.cl, antofagasta.tv, g5noticias.cl, biobiochile.cl, radiopaulina.cl and t.co with 2 each.
- **Observation (not a gate):** 2/50 decode to `t.co` (a Twitter/X shortener). For those items Google News itself indexed a shortener. They are valid http(s) URLs, so they count as decoded; a publisher-grade URL would need a redirect fetch, which this pipeline never does (T-36-18).
- **Old-format count:** 0 of the current Google links carry an old-format token. This is consistent with the gate arbiter's measurement of 0/426 decodes without a session (BF-03). Every decode needs the network path.

Measured from a residential IP; the Actions runner rate is measured live in 36-09 from the run summary.

## Live decode floor (G-37 as amended by G-44)

X/50 = 1.00 ≥ 0.50, so F = min(0.70, 1.00 − 0.20) = min(0.70, 0.80) = 0.70.

live_decode_floor: 0.70

36-09 gates FID-04 on two conditions:
- **(a)** live decode rate = Σdecoded / Σ(decoded + failed) over the run summaries' `gnews_decode`, with Σ attempts ≥ 20, must be ≥ 0.70.
- **(b)** news.google.com share of live-added `url` ≤ 43 % (n ≥ 20). This is the secondary condition.

If Google blocks decoding from runner IPs, (a) fails and FID-04 is PARTIAL per G-35(6), with both rates recorded.
