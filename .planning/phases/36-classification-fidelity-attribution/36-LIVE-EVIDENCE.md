# Phase 36 — Live evidence (36-09)

## Task 2 — ship

gate_sha: 0c3cf03
- pytest 876 passed / 1 skipped / 2 xfailed (exit 0); validators 18/18; vitest 192/192; astro check 0 errors / 0 warnings; lint-workflows 0; check-secret-hygiene 0; check_hotfix_regression --data PASS; `git status data/` clean.

pre_push_review: fresh opus, GO-WITH-FIXES.
- F-1 (major): a blank title crashed the whole run. Fixed in 91b1e80 (empty_title reject, live + backfill, 2 tests + negative control); pytest 878/1/2.
- F-2 (minor): the owner-retitled card 514872e1d06db7f2 carries the "Automatically generated headline" label because it has no title_src. Accepted: it leaves the 30-day window on ~2026-10-03, and editing data/ is not allowed.
- F-3 / F-4 (efficiency / pre-existing canonicalisation): → deferred-live.
- F-5: ship-time drop-list re-check (below).
- F-6: health-gate (d) false-alarm risk on quiet runs; watched in Task 3.

ship_drop_list_reviewed: 58/58. The ship-time list after `git pull --rebase --autostash` equals the 58 pairs of 36-DEDUP-REVIEW.md, with 0 new pairs; 514872e1d06db7f2 is not a DROP.
no_active_news_run_at_push: yes (02:46Z).
ship_sha: 91b1e801a57b9d887f4524b6324e1dd59a55f96b
deploy: deploy-on-code 36212726095 success. T0 2026-09-26T02:46:11Z; prod data-build-now 2026-09-26T02:46:48.274Z ≥ T0 (G-51 fingerprint).

prod_checks (curled 2026-09-26 ~02:48Z):

| Check | Result |
|---|---|
| /news/ EN cards | 787 |
| Machine-translated | 0 |
| Original Spanish | 0 |
| Automatically generated | 787 (sum 787 = cards) |
| Served current.json rows without title_src | 787 (== AG, G-36) |
| /es/noticias/ cards | 787 |
| /methodology/ id="news-headlines" | 1 |
| /es/metodologia/ id="titulares-noticias" | 1 |
| check_hotfix_regression --html (news + noticias, with --current) | PASS |

S0: 36-S0-IDS.txt = 787 ids from `git show 91b1e80:data/incidents/current.json`.

## Task 3 — live runs (pending)

first_post_ship_run: 36214289804 drops=0 mode=full
- scheduled 2026-09-26T03:16Z, headSha 91b1e80 (= ship_sha); conclusion success.
- Health gate success; deploy success.
- classified=7, attempted 14, accepted 7, api_errors 0, failovers 0, expired 0, budget_exhausted false.
- fidelity: editorial_filtered 0, title_en_fallbacks 0.
- gnews_decode: candidates 6, decoded 6, failed 0, skipped_budget 0.
- BioBio warning lines: 0.

pruned_existing_reconciled: 58/58 in reviewed pairs. 109 S0 ids are missing from current.json after the run: 51 moved to archive (window aging) and 58 pruned, all 58 DROP ids from 36-DEDUP-REVIEW.md; 0 unreviewed pruned ids. 514872e1d06db7f2 is still present.

- After the run: current.json has 684 incidents; 6 live-added, 6/6 with title_src, 0 news.google.com url, 1 via_url.
- validate_news_dedup: PASS, 0 drops over 684.

validators: 19/19 (#19 news-dedup.mjs registered after first_post_ship_run drops=0; `npm run build && npm run validate` → 19/19).
