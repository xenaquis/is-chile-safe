/**
 * cead-vintage.lib.mjs — pure, side-effect-free helpers for cead-vintage.mjs (FRESH-05, validator #17).
 *
 * Deliberately independent of site/src/lib/ceadVintage.ts (facets.mjs precedent): this
 * validator re-derives the expected vintage triple from raw CEAD data JSON so it can
 * detect drift between the site's real rendered output and the data, instead of
 * testing itself against its own production code.
 *
 * No fs. No top-level execution. Safe to import from the vitest spec or from
 * cead-vintage.mjs.
 */

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

/**
 * expectedFromJson(json) — derives { lastUpdated, partialYear, latestCompleteYear }
 * from a raw CEAD data JSON object ({ series: [{year, partial}], last_updated }).
 * Mirrors the shape of site/src/lib/ceadVintage.ts's ceadVintage(), written
 * independently on purpose (see file header).
 */
export function expectedFromJson(json) {
  const lastUpdated =
    json && typeof json.last_updated === 'string' && ISO_DATE_RE.test(json.last_updated) && !Number.isNaN(Date.parse(json.last_updated))
      ? json.last_updated
      : null;

  let partialYear = null;
  let latestCompleteYear = null;
  const series = Array.isArray(json?.series) ? json.series : [];
  for (const entry of series) {
    if (!entry || typeof entry.year !== 'number') continue;
    if (entry.partial === true) {
      if (partialYear === null || entry.year > partialYear) partialYear = entry.year;
    } else {
      if (latestCompleteYear === null || entry.year > latestCompleteYear) latestCompleteYear = entry.year;
    }
  }

  return { lastUpdated, partialYear, latestCompleteYear };
}

/**
 * formatDate(iso, locale) — Intl long-month date, always UTC (near-midnight dates
 * flip under non-UTC system timezones otherwise; see facets.mjs assertion-11).
 */
export function formatDate(iso, locale) {
  const date = new Date(iso);
  const intlLocale = locale === 'es' ? 'es-CL' : 'en-US';
  return date.toLocaleDateString(intlLocale, {
    timeZone: 'UTC',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

const CEAD_VINTAGE_NODE_RE = /<p class="cead-vintage"([^>]*)>([\s\S]*?)<\/p>/g;

function extractAttr(attrString, name) {
  const re = new RegExp(name + '="([^"]*)"');
  const m = re.exec(attrString);
  return m ? m[1] : null;
}

function stripTags(html) {
  return html.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
}

/**
 * checkCeadVintagePage(html, expected, locale, {methodology}) → string[] errors.
 * expected = { lastUpdated, partialYear, latestCompleteYear } (from expectedFromJson).
 */
export function checkCeadVintagePage(html, expected, locale, { methodology = false } = {}) {
  const errors = [];

  const matches = [...html.matchAll(CEAD_VINTAGE_NODE_RE)];
  if (matches.length === 0) {
    errors.push('no .cead-vintage node found');
    return errors;
  }
  if (matches.length > 1) {
    errors.push(`expected exactly 1 .cead-vintage node, found ${matches.length}`);
    return errors;
  }

  const [, attrString, innerHtml] = matches[0];
  const text = stripTags(innerHtml);

  const expectedLastUpdated = expected.lastUpdated ?? '';
  const expectedPartialYear = expected.partialYear === null || expected.partialYear === undefined ? '' : String(expected.partialYear);
  const expectedLatestComplete = expected.latestCompleteYear === null || expected.latestCompleteYear === undefined ? '' : String(expected.latestCompleteYear);

  const gotLastUpdated = extractAttr(attrString, 'data-cead-last-updated') ?? '';
  const gotPartialYear = extractAttr(attrString, 'data-partial-year') ?? '';
  const gotLatestComplete = extractAttr(attrString, 'data-latest-complete-year') ?? '';

  if (gotLastUpdated !== expectedLastUpdated) {
    errors.push(`data-cead-last-updated mismatch: expected "${expectedLastUpdated}", got "${gotLastUpdated}"`);
  }
  if (gotPartialYear !== expectedPartialYear) {
    errors.push(`data-partial-year mismatch: expected "${expectedPartialYear}", got "${gotPartialYear}"`);
  }
  if (gotLatestComplete !== expectedLatestComplete) {
    errors.push(`data-latest-complete-year mismatch: expected "${expectedLatestComplete}", got "${gotLatestComplete}"`);
  }

  // Visible "CEAD data as of <date>" / "Datos CEAD al <date>" prefix + formatted date
  if (expected.lastUpdated) {
    const prefix = locale === 'es' ? 'Datos CEAD al ' : 'CEAD data as of ';
    const formatted = formatDate(expected.lastUpdated, locale);
    if (!text.includes(prefix + formatted)) {
      errors.push(`visible text missing "${prefix}${formatted}" (got: "${text}")`);
    }
  }

  // Partial-year label
  if (expected.partialYear !== null && expected.partialYear !== undefined) {
    const partialLabel = locale === 'es'
      ? `${expected.partialYear} es un año parcial`
      : `${expected.partialYear} is a partial year`;
    if (!text.includes(partialLabel)) {
      errors.push(`visible text missing partial-year label "${partialLabel}"`);
    }
    const completeLabel = locale === 'es'
      ? `último año completo es ${expected.latestCompleteYear}`
      : `latest complete year is ${expected.latestCompleteYear}`;
    if (!text.includes(completeLabel)) {
      errors.push(`visible text missing latest-complete-year label "${completeLabel}"`);
    }
  } else {
    const bannedLabel = locale === 'es' ? 'es un año parcial' : 'is a partial year';
    if (text.includes(bannedLabel)) {
      errors.push(`visible text contains a partial-year label but expected.partialYear is null: "${text}"`);
    }
  }

  // Methodology mode: "(currently N)" / "(actualmente N)" narrative check, against
  // the whole page (the sentence lives outside the .cead-vintage node itself).
  if (methodology && expected.latestCompleteYear !== null && expected.latestCompleteYear !== undefined) {
    const methodologyLabel = locale === 'es'
      ? `(actualmente ${expected.latestCompleteYear})`
      : `(currently ${expected.latestCompleteYear})`;
    if (!html.includes(methodologyLabel)) {
      errors.push(`page missing methodology label "${methodologyLabel}"`);
    }
  }

  // R-05: the node must not deny what the trend chart draws.
  const r05Banned = locale === 'es' ? 'ni las tendencias' : 'or trends';
  if (text.includes(r05Banned)) {
    errors.push(`R-05: .cead-vintage node text contains banned phrase "${r05Banned}"`);
  }

  return errors;
}

/**
 * findBannedPartialLabels(text) — R-02: returns every match of the invented
 * month-cutoff / partial-data phrasing this milestone removed.
 */
export function findBannedPartialLabels(text) {
  const re = /Jan–Jun|ene–jun|\(partial data\)|\(datos parciales\)/g;
  return [...text.matchAll(re)].map((m) => m[0]);
}
