---
id: adsense-consent-mode-phase6
created: 2026-06-13
source: 04-UI-REVIEW.md (Experience Design pillar, 2/4)
resolves_phase: 6
priority: high
---

# Wire AdSense consent signal when activating ADSENSE_ENABLED (Phase 6)

**Context:** Phase 4 built CookieConsent + the gated AdSense (`adsbygoogle`) loader, but the
consent decision is only stored in `localStorage` (`csm_consent`) — it is never forwarded to
Google's ad runtime. The 04-UI-SPEC.md specified `googletag.pubads().setPrivacySettings()`, but
that is the **Google Ad Manager (GPT)** API, not AdSense. The implementation uses **AdSense**
(`adsbygoogle` + `pagead2.googlesyndication.com`).

**What to do in Phase 6 (when flipping `ADSENSE_ENABLED=true`):**
- Use Google **Consent Mode v2** (`gtag('consent', 'default'/'update', {ad_storage, ad_user_data,
  ad_personalization, analytics_storage})`) — the correct AdSense mechanism — instead of the
  GAM `setPrivacySettings()` call from the spec.
- Wire the CookieConsent Accept handler → `gtag('consent','update',{...granted})` and Reject →
  non-personalized / denied, gated on `ADSENSE_ENABLED === 'true'`.
- Verify the consent signal reaches Google (Tag Assistant / Consent Mode debug) before the first
  indexing wave / AdSense approval submission.

**Why deferred:** ad code is inert in Phase 4 (flag OFF); only matters once ads serve. GDPR/AdSense
policy compliance gate for go-live.
