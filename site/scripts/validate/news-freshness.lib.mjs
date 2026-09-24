/**
 * news-freshness.lib.mjs — pure, side-effect-free helpers for
 * news-freshness.mjs (validator #18, FRESH-01/FRESH-02/FRESH-03).
 *
 * Imports the single G-05 rule from src/lib/newsEvidence.mjs — this module
 * does NOT re-derive the freshness rule, only the page-consistency checks
 * around it (does the served HTML agree with what the shared helper says
 * about the payload the build consumed?).
 *
 * No fs. No top-level execution. Safe to import from the vitest spec or from
 * news-freshness.mjs.
 */

import {
  latestIncidentDate,
  computeEvidence,
  evidenceVerdict,
  MAX_AGE_HOURS,
  COMMUNE_NEWS_STALE_HOURS,
} from '../../src/lib/newsEvidence.mjs';

// Literal copy of site/src/lib/newsCoverageGaps.ts's COVERAGE_GAPS. Kept as a
// literal (not an import) because that source is TypeScript and this
// validator runs as plain .mjs under Node — see news-freshness.test.ts for
// the deep-equal parity assertion against the TS export (the vitest side can
// import both).
export const COVERAGE_GAPS = [
  { from: '2026-09-05', to: '2026-09-22', source: 'G-18 classifier outage' },
];

// Heading literals duplicated here with a comment naming the i18n keys they
// mirror (same precedent as the FORBIDDEN_TERMS copy in
// CommuneNewsSection.astro:76-88). Source: site/src/config/i18n.ts
// commune_news_heading / commune_news_heading_stale.
const COMMUNE_HEADING = {
  en: 'Recent Incidents in the News',
  es: 'Incidentes Recientes en la Prensa',
};
const COMMUNE_HEADING_STALE = {
  en: 'Earlier Incidents in the News',
  es: 'Incidentes Anteriores en la Prensa',
};
// R2/F35-R1-05: the old zero-quantifier heading this milestone removed. Any
// page still carrying it is a regression, regardless of the data-news-stale
// verdict.
const BANNED_STALE_HEADING_SUBSTRING = {
  en: 'none in the last 7 days',
  es: 'ninguno en los últimos 7 días',
};

const DAY_MS = 24 * 60 * 60 * 1000;

/**
 * formatLongDate(dateStr, locale) — 'YYYY-MM-DD' -> Intl long-month date,
 * always UTC (a near-midnight date otherwise flips under a non-UTC system
 * timezone — facets.mjs assertion-11 precedent).
 */
export function formatLongDate(dateStr, locale) {
  const date = new Date(dateStr + 'T00:00:00Z');
  const intlLocale = locale === 'es' ? 'es-CL' : 'en-US';
  return date.toLocaleDateString(intlLocale, {
    timeZone: 'UTC',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

/**
 * addDaysStr — UTC string-only day arithmetic, ported from
 * newsDayFacets.ts's addDays.
 */
function addDaysStr(dateStr, days) {
  const ms = Date.parse(dateStr + 'T00:00:00Z') + days * DAY_MS;
  return new Date(ms).toISOString().slice(0, 10);
}

function extractAttr(attrString, name) {
  const re = new RegExp(name + '="([^"]*)"');
  const m = re.exec(attrString || '');
  return m ? m[1] : null;
}

function stripTags(html) {
  return html.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
}

// ---------------------------------------------------------------------------
// checkNewsPage
// ---------------------------------------------------------------------------

const FRESHNESS_P_RE = /<p\b(?=[^>]*\bclass="freshness")([^>]*)>([\s\S]*?)<\/p>/;
const STALE_NOTICE_RE = /<p\b(?=[^>]*\bclass="news-stale-notice")[^>]*>/;
const DAY_BAR_RE = /<button\b(?=[^>]*\bclass="day-bar")([^>]*)>/g;
const GAP_CAPTION_RE = /<p\b(?=[^>]*\bclass="day-gap-caption")([^>]*)>([\s\S]*?)<\/p>/g;

/**
 * checkNewsPage(html, payload, locale) → string[] errors.
 *
 * - Verifies the `.freshness` node's data-latest-incident + build-now-derived
 *   stale expectation against the shared G-05 helper.
 * - Verifies the visible "Latest incident: {date}" / "Último incidente:
 *   {date}" text.
 * - Verifies the presence/absence of `.news-stale-notice` mirrors 35-04
 *   exactly (R1/R-07): notice iff verdict is 'stale' or 'none'; 'future' is
 *   NOT stale.
 * - R1/R-01: for every `.day-bar[data-day]`, expected gap = the date falls in
 *   a declared COVERAGE_GAPS range AND no payload incident has that date;
 *   compares that to the bar's own data-gap="true" presence.
 * - R2/F35-R1-04: for every `.day-gap-caption[data-gap-from][data-gap-to]`,
 *   every date in the span must be a `.day-bar[data-gap="true"]`, the span
 *   must be maximal (the day before `from` and the day after `to` are not
 *   gap bars among the bars present), and the visible text must name both
 *   dates in the locale's long format.
 */
export function checkNewsPage(html, payload, locale) {
  const errors = [];

  const freshMatch = FRESHNESS_P_RE.exec(html);
  if (!freshMatch) {
    errors.push('no p.freshness node found');
    return errors;
  }
  const [, attrString, innerHtml] = freshMatch;

  if (/>Updated /.test(html) || />Actualizado /.test(html)) {
    errors.push('found a build-time "Updated"/"Actualizado" stamp text node — G-20(1) removed this');
  }

  const expectedLatest = latestIncidentDate(payload) ?? '';
  const gotLatest = extractAttr(attrString, 'data-latest-incident') ?? '';
  if (gotLatest !== expectedLatest) {
    errors.push(`data-latest-incident mismatch: expected "${expectedLatest}", got "${gotLatest}"`);
  }

  const buildNowStr = extractAttr(attrString, 'data-build-now');
  const buildNowMs = buildNowStr ? Date.parse(buildNowStr) : NaN;
  if (buildNowStr === null || Number.isNaN(buildNowMs)) {
    errors.push('p.freshness is missing a parseable data-build-now attribute');
    return errors;
  }

  const evidence = computeEvidence(payload);
  const verdict = evidenceVerdict(evidence, buildNowMs, MAX_AGE_HOURS);
  const expectStale = verdict === 'stale' || verdict === 'none';

  const noticePresent = STALE_NOTICE_RE.test(html);
  if (expectStale && !noticePresent) {
    errors.push(`stale notice expected (verdict "${verdict}") but .news-stale-notice is absent`);
  }
  if (!expectStale && noticePresent) {
    errors.push(`stale notice not expected (verdict "${verdict}") but .news-stale-notice is present`);
  }

  if (expectedLatest) {
    const expectedText = locale === 'es'
      ? `Último incidente: ${formatLongDate(expectedLatest, 'es')}`
      : `Latest incident: ${formatLongDate(expectedLatest, 'en')}`;
    const text = stripTags(innerHtml);
    if (!text.includes(expectedText)) {
      errors.push(`p.freshness visible text missing "${expectedText}" (got: "${text}")`);
    }
  }

  // R1/R-01: per-bar gap check against the FULL payload (not the page's
  // 30-day window) — a gap day is only a gap if no incident anywhere in the
  // payload was published that day.
  const payloadDates = new Set(
    (Array.isArray(payload?.incidents) ? payload.incidents : [])
      .map((inc) => (inc && typeof inc.date === 'string' ? inc.date : null))
      .filter((d) => d !== null)
  );

  const bars = new Map(); // date -> gap boolean
  let barMatch;
  DAY_BAR_RE.lastIndex = 0;
  while ((barMatch = DAY_BAR_RE.exec(html)) !== null) {
    const barAttrs = barMatch[1];
    const date = extractAttr(barAttrs, 'data-day');
    if (!date) continue;
    const gotGap = /\bdata-gap="true"/.test(barAttrs);
    bars.set(date, gotGap);
    const expectedGap = COVERAGE_GAPS.some((g) => g.from <= date && date <= g.to) && !payloadDates.has(date);
    if (expectedGap !== gotGap) {
      errors.push(
        `day-bar ${date}: expected data-gap="${expectedGap}" but got "${gotGap}"`
      );
    }
  }

  // R2/F35-R1-04: contiguous-span gap captions.
  let capMatch;
  GAP_CAPTION_RE.lastIndex = 0;
  while ((capMatch = GAP_CAPTION_RE.exec(html)) !== null) {
    const [, capAttrs, capInner] = capMatch;
    const from = extractAttr(capAttrs, 'data-gap-from');
    const to = extractAttr(capAttrs, 'data-gap-to');
    if (!from || !to) {
      errors.push('day-gap-caption missing data-gap-from/data-gap-to');
      continue;
    }

    let allGap = true;
    for (let d = from; d <= to; d = addDaysStr(d, 1)) {
      if (bars.get(d) !== true) {
        allGap = false;
        errors.push(`day-gap-caption ${from}..${to}: ${d} is not a data-gap="true" bar`);
      }
      if (d === to) break; // guard against an inverted/degenerate range looping forever
    }

    const before = addDaysStr(from, -1);
    const after = addDaysStr(to, 1);
    if (bars.has(before) && bars.get(before) === true) {
      errors.push(`day-gap-caption ${from}..${to}: not maximal — ${before} (before "from") is also a gap bar`);
    }
    if (bars.has(after) && bars.get(after) === true) {
      errors.push(`day-gap-caption ${from}..${to}: not maximal — ${after} (after "to") is also a gap bar`);
    }

    if (allGap) {
      const text = stripTags(capInner);
      const fromLabel = formatLongDate(from, locale);
      const toLabel = formatLongDate(to, locale);
      if (!text.includes(fromLabel) || !text.includes(toLabel)) {
        errors.push(`day-gap-caption ${from}..${to}: visible text missing "${fromLabel}"/"${toLabel}" (got: "${text}")`);
      }
    }
  }

  return errors;
}

// ---------------------------------------------------------------------------
// checkCommuneSection
// ---------------------------------------------------------------------------

// R-08: tolerate any attribute order and Astro's injected data-astro-cid-*
// attributes — the class check is a lookahead, not a fixed position.
const CNEWS_SECTION_RE = /<section\b(?=[^>]*\bclass="cnews-section")([^>]*)>([\s\S]*?)<\/section>/;
const SECTION_HEADING_RE = /<h2\b(?=[^>]*\bclass="section-heading")[^>]*>([\s\S]*?)<\/h2>/;
const FIRST_TIME_RE = /<time\s+datetime="([^"]*)"/;

/**
 * checkCommuneSection(html, locale) → string[] errors.
 *
 * Extracts ONLY the substring from `<section class="cnews-section" …>` to
 * its matching `</section>` (R1/R-08) — the CEAD `<time>` and the other
 * h2.section-heading nodes elsewhere on a commune page are never inspected.
 * Returns [] when no cnews-section is present (a commune with 0 safe items
 * renders nothing).
 */
export function checkCommuneSection(html, locale) {
  const errors = [];

  const sectionMatch = CNEWS_SECTION_RE.exec(html);
  if (!sectionMatch) return errors;

  const [, attrString, inner] = sectionMatch;

  const buildNowStr = extractAttr(attrString, 'data-build-now');
  const buildNowMs = buildNowStr ? Date.parse(buildNowStr) : NaN;
  if (buildNowStr === null || Number.isNaN(buildNowMs)) {
    errors.push('cnews-section is missing a parseable data-build-now attribute');
    return errors;
  }

  const gotStale = extractAttr(attrString, 'data-news-stale');
  if (gotStale !== 'true' && gotStale !== 'false') {
    errors.push(`cnews-section data-news-stale must be "true" or "false", got "${gotStale}"`);
    return errors;
  }

  const timeMatch = FIRST_TIME_RE.exec(inner);
  const newestDate = timeMatch ? timeMatch[1] : null;
  if (!newestDate) {
    errors.push('cnews-section has no <time datetime="…"> to determine the newest listed item');
    return errors;
  }

  const verdict = evidenceVerdict(
    computeEvidence({ incidents: [{ date: newestDate }] }),
    buildNowMs,
    COMMUNE_NEWS_STALE_HOURS
  );
  const expectedStale = verdict === 'stale';
  const expectStaleAttr = expectedStale ? 'true' : 'false';
  if (gotStale !== expectStaleAttr) {
    errors.push(
      `cnews-section data-news-stale mismatch for newest item ${newestDate} (verdict "${verdict}"): expected "${expectStaleAttr}", got "${gotStale}"`
    );
  }

  const headingMatch = SECTION_HEADING_RE.exec(inner);
  if (!headingMatch) {
    errors.push('cnews-section has no h2.section-heading');
    return errors;
  }
  const headingText = stripTags(headingMatch[1]);
  const expectedHeading = expectedStale ? COMMUNE_HEADING_STALE[locale] : COMMUNE_HEADING[locale];
  if (headingText !== expectedHeading) {
    errors.push(`cnews-section heading mismatch: expected "${expectedHeading}", got "${headingText}"`);
  }
  if (headingText.includes(BANNED_STALE_HEADING_SUBSTRING[locale])) {
    errors.push(`cnews-section heading contains the banned zero-quantifier phrase "${BANNED_STALE_HEADING_SUBSTRING[locale]}" (R2/F35-R1-05)`);
  }

  return errors;
}
