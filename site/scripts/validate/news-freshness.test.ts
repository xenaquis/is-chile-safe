import { describe, it, expect } from 'vitest';
import {
  checkNewsPage,
  checkCommuneSection,
  formatLongDate,
  COVERAGE_GAPS as LIB_COVERAGE_GAPS,
} from './news-freshness.lib.mjs';
import { COVERAGE_GAPS as TS_COVERAGE_GAPS } from '../../src/lib/newsCoverageGaps';

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

function addDays(dateStr: string, days: number): string {
  const ms = Date.parse(dateStr + 'T00:00:00Z') + days * 86400000;
  return new Date(ms).toISOString().slice(0, 10);
}

function dateRange(from: string, to: string): string[] {
  const out: string[] = [];
  for (let d = from; d <= to; d = addDays(d, 1)) out.push(d);
  return out;
}

function buildBar(date: string, gap: boolean): string {
  return `<button type="button" class="day-bar" data-day="${date}"${gap ? ' data-gap="true"' : ''} aria-pressed="false" style="--h:10%"><span class="day-bar-fill"></span><span class="news-sr">x</span></button>`;
}

function buildNewsHtml(opts: {
  latest: string;
  buildNow: string;
  locale: 'en' | 'es';
  includeNotice?: boolean;
  bars?: string;
  captions?: string;
  extra?: string;
  latestAttrOverride?: string;
}): string {
  const { latest, buildNow, locale, includeNotice = false, bars = '', captions = '', extra = '', latestAttrOverride } = opts;
  const latestText = locale === 'es'
    ? `Último incidente: ${formatLongDate(latest, 'es')}`
    : `Latest incident: ${formatLongDate(latest, 'en')}`;
  const latestAttr = latestAttrOverride ?? latest;
  return `
    <section>
      <h1>News</h1>
      <p class="freshness" data-latest-incident="${latestAttr}" data-build-now="${buildNow}">
        <time datetime="${latest}">${latestText}</time>
      </p>
      ${includeNotice ? `<p class="news-stale-notice" role="status" data-stale-hours="48">stale text</p>` : ''}
    </section>
    ${extra}
    <div class="day-histogram">
      <div class="day-bars">${bars}</div>
      ${captions}
    </div>
  `;
}

const FROZEN_PAYLOAD = { incidents: [{ date: '2026-09-04' }] }; // no last_new_incident_at

// ---------------------------------------------------------------------------
// checkNewsPage
// ---------------------------------------------------------------------------

describe('checkNewsPage', () => {
  const buildNow = '2026-09-23T12:00:00.000Z';

  it('frozen fixture (stale, notice present, EN) returns []', () => {
    const html = buildNewsHtml({ latest: '2026-09-04', buildNow, locale: 'en', includeNotice: true });
    expect(checkNewsPage(html, FROZEN_PAYLOAD, 'en')).toEqual([]);
  });

  it('same HTML without the notice returns "stale notice expected"', () => {
    const html = buildNewsHtml({ latest: '2026-09-04', buildNow, locale: 'en', includeNotice: false });
    const errors = checkNewsPage(html, FROZEN_PAYLOAD, 'en');
    expect(errors.some((e) => e.includes('stale notice expected'))).toBe(true);
  });

  it('fresh payload with the notice present returns "stale notice not expected"', () => {
    const freshPayload = {
      incidents: [{ date: '2026-09-04' }],
      last_new_incident_at: new Date(Date.parse(buildNow) - 3600000).toISOString(),
    };
    const html = buildNewsHtml({ latest: '2026-09-04', buildNow, locale: 'en', includeNotice: true });
    const errors = checkNewsPage(html, freshPayload, 'en');
    expect(errors.some((e) => e.includes('stale notice not expected'))).toBe(true);
  });

  it('wrong data-latest-incident returns an error', () => {
    const html = buildNewsHtml({
      latest: '2026-09-04',
      buildNow,
      locale: 'en',
      includeNotice: true,
      latestAttrOverride: '2026-09-01',
    });
    const errors = checkNewsPage(html, FROZEN_PAYLOAD, 'en');
    expect(errors.some((e) => e.includes('data-latest-incident mismatch'))).toBe(true);
  });

  it('a build-time ">Updated " text node returns an error', () => {
    const html = buildNewsHtml({
      latest: '2026-09-04',
      buildNow,
      locale: 'en',
      includeNotice: true,
      extra: '<p>Updated September 4, 2026</p>',
    });
    const errors = checkNewsPage(html, FROZEN_PAYLOAD, 'en');
    expect(errors.some((e) => e.includes('Updated'))).toBe(true);
  });

  it('ES variant with "Último incidente: 4 de septiembre de 2026" returns []', () => {
    const html = buildNewsHtml({ latest: '2026-09-04', buildNow, locale: 'es', includeNotice: true });
    expect(html).toContain('Último incidente: 4 de septiembre de 2026');
    expect(checkNewsPage(html, FROZEN_PAYLOAD, 'es')).toEqual([]);
  });

  it('payload last_new_incident_at 25h in the future expects NO notice', () => {
    const futurePayload = {
      incidents: [{ date: '2026-09-04' }],
      last_new_incident_at: new Date(Date.parse(buildNow) + 25 * 3600000).toISOString(),
    };
    const htmlNoNotice = buildNewsHtml({ latest: '2026-09-04', buildNow, locale: 'en', includeNotice: false });
    expect(checkNewsPage(htmlNoNotice, futurePayload, 'en')).toEqual([]);

    const htmlWithNotice = buildNewsHtml({ latest: '2026-09-04', buildNow, locale: 'en', includeNotice: true });
    const errors = checkNewsPage(htmlWithNotice, futurePayload, 'en');
    expect(errors.some((e) => e.includes('stale notice not expected'))).toBe(true);
  });

  describe('R1/R-01 per-bar gap check', () => {
    const realDates = [...dateRange('2026-08-24', '2026-09-04'), ...dateRange('2026-09-23', '2026-09-25')];
    const payload = { incidents: realDates.map((date) => ({ date })), last_new_incident_at: '2026-09-25T01:00:00.000Z' };
    const allDays = dateRange('2026-08-24', '2026-09-25');
    const gapDays = new Set(dateRange('2026-09-05', '2026-09-22'));

    function buildBars(dropGapOn?: string): string {
      return allDays.map((d) => buildBar(d, gapDays.has(d) && d !== dropGapOn)).join('');
    }

    it('payload with real dates on either side of the gap and correctly flagged bars gives []', () => {
      const html = buildNewsHtml({ latest: '2026-09-25', buildNow: '2026-09-25T06:00:00.000Z', locale: 'en', includeNotice: false, bars: buildBars() });
      expect(checkNewsPage(html, payload, 'en')).toEqual([]);
    });

    it('dropping data-gap from the 09-10 bar gives an error naming 2026-09-10', () => {
      const html = buildNewsHtml({ latest: '2026-09-25', buildNow: '2026-09-25T06:00:00.000Z', locale: 'en', includeNotice: false, bars: buildBars('2026-09-10') });
      const errors = checkNewsPage(html, payload, 'en');
      expect(errors.some((e) => e.includes('2026-09-10'))).toBe(true);
    });

    it('a real 09-10 incident with data-gap still on 09-10 gives an error', () => {
      const payloadWithReal = { incidents: [...payload.incidents, { date: '2026-09-10' }], last_new_incident_at: payload.last_new_incident_at };
      const html = buildNewsHtml({ latest: '2026-09-25', buildNow: '2026-09-25T06:00:00.000Z', locale: 'en', includeNotice: false, bars: buildBars() });
      const errors = checkNewsPage(html, payloadWithReal, 'en');
      expect(errors.some((e) => e.includes('2026-09-10'))).toBe(true);
    });
  });

  describe('R2/F35-R1-04 gap-caption spans', () => {
    // Real incidents on 09-04, 09-22, 09-23; gap days 09-05..09-21.
    const realDates = ['2026-09-04', '2026-09-22', '2026-09-23'];
    const payload = { incidents: realDates.map((date) => ({ date })), last_new_incident_at: '2026-09-23T01:00:00.000Z' };
    const allDays = dateRange('2026-09-04', '2026-09-23');
    const gapDays = new Set(dateRange('2026-09-05', '2026-09-21'));
    const bars = allDays.map((d) => buildBar(d, gapDays.has(d))).join('');

    it('a single caption ending 2026-09-21 with matching visible text gives []', () => {
      const captionText = `No incidents were collected from ${formatLongDate('2026-09-05', 'en')} to ${formatLongDate('2026-09-21', 'en')} because of an outage.`;
      const captions = `<p class="day-gap-caption" data-gap-from="2026-09-05" data-gap-to="2026-09-21">${captionText}</p>`;
      const html = buildNewsHtml({ latest: '2026-09-23', buildNow: '2026-09-23T06:00:00.000Z', locale: 'en', includeNotice: false, bars, captions });
      expect(checkNewsPage(html, payload, 'en')).toEqual([]);
    });

    it('a caption ending 2026-09-22 (a real-incident day, not a gap bucket) gives an error', () => {
      const captionText = `No incidents were collected from ${formatLongDate('2026-09-05', 'en')} to ${formatLongDate('2026-09-22', 'en')} because of an outage.`;
      const captions = `<p class="day-gap-caption" data-gap-from="2026-09-05" data-gap-to="2026-09-22">${captionText}</p>`;
      const html = buildNewsHtml({ latest: '2026-09-23', buildNow: '2026-09-23T06:00:00.000Z', locale: 'en', includeNotice: false, bars, captions });
      const errors = checkNewsPage(html, payload, 'en');
      expect(errors.some((e) => e.includes('2026-09-22'))).toBe(true);
    });

    it('a caption whose dates are not gap buckets at all gives an error', () => {
      const captionText = `No incidents were collected from ${formatLongDate('2026-09-04', 'en')} to ${formatLongDate('2026-09-04', 'en')} because of an outage.`;
      const captions = `<p class="day-gap-caption" data-gap-from="2026-09-04" data-gap-to="2026-09-04">${captionText}</p>`;
      const html = buildNewsHtml({ latest: '2026-09-23', buildNow: '2026-09-23T06:00:00.000Z', locale: 'en', includeNotice: false, bars, captions });
      const errors = checkNewsPage(html, payload, 'en');
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  it('COVERAGE_GAPS literal copy deep-equals the TS export', () => {
    expect(LIB_COVERAGE_GAPS).toEqual(TS_COVERAGE_GAPS);
  });
});

// ---------------------------------------------------------------------------
// checkCommuneSection
// ---------------------------------------------------------------------------

function buildCommuneHtml(opts: {
  buildNow: string;
  newest: string;
  stale: string;
  heading: string;
  locale?: 'en' | 'es';
  attrsOutOfOrder?: boolean;
  extraBefore?: string;
}): string {
  const { buildNow, newest, stale, heading, attrsOutOfOrder = false, extraBefore = '' } = opts;
  const sectionOpen = attrsOutOfOrder
    ? `<section data-build-now="${buildNow}" data-astro-cid-z class="cnews-section" data-news-stale="${stale}">`
    : `<section class="cnews-section" data-news-stale="${stale}" data-build-now="${buildNow}">`;
  const headingTag = attrsOutOfOrder
    ? `<h2 data-astro-cid-w class="section-heading">${heading}</h2>`
    : `<h2 class="section-heading">${heading}</h2>`;
  return `
    ${extraBefore}
    ${sectionOpen}
      ${headingTag}
      <ul class="cnews-list"><li><time datetime="${newest}">x</time></li></ul>
    </section>
  `;
}

describe('checkCommuneSection', () => {
  it('build-now 2026-09-23T12:00Z, newest 2026-09-04, stale=true + stale heading gives []', () => {
    const html = buildCommuneHtml({
      buildNow: '2026-09-23T12:00:00.000Z',
      newest: '2026-09-04',
      stale: 'true',
      heading: 'Earlier Incidents in the News',
    });
    expect(checkCommuneSection(html, 'en')).toEqual([]);
  });

  it('same newest date with data-news-stale="false" gives an error', () => {
    const html = buildCommuneHtml({
      buildNow: '2026-09-23T12:00:00.000Z',
      newest: '2026-09-04',
      stale: 'false',
      heading: 'Recent Incidents in the News',
    });
    const errors = checkCommuneSection(html, 'en');
    expect(errors.length).toBeGreaterThan(0);
  });

  it('newest 2026-09-20 with stale="false" and the normal heading gives []', () => {
    const html = buildCommuneHtml({
      buildNow: '2026-09-23T12:00:00.000Z',
      newest: '2026-09-20',
      stale: 'false',
      heading: 'Recent Incidents in the News',
    });
    expect(checkCommuneSection(html, 'en')).toEqual([]);
  });

  it('ES headings are handled (stale)', () => {
    const html = buildCommuneHtml({
      buildNow: '2026-09-23T12:00:00.000Z',
      newest: '2026-09-04',
      stale: 'true',
      heading: 'Incidentes Anteriores en la Prensa',
    });
    expect(checkCommuneSection(html, 'es')).toEqual([]);
  });

  it('ES headings are handled (fresh)', () => {
    const html = buildCommuneHtml({
      buildNow: '2026-09-23T12:00:00.000Z',
      newest: '2026-09-20',
      stale: 'false',
      heading: 'Incidentes Recientes en la Prensa',
    });
    expect(checkCommuneSection(html, 'es')).toEqual([]);
  });

  it('HTML without a cnews-section gives []', () => {
    expect(checkCommuneSection('<p>no section here</p>', 'en')).toEqual([]);
  });

  it('R-08: cead-vintage + two other h2.section-heading nodes before a fresh section, attrs out of order, gives []', () => {
    const html = buildCommuneHtml({
      buildNow: '2026-09-23T12:00:00.000Z',
      newest: '2026-09-20',
      stale: 'false',
      heading: 'Recent Incidents in the News',
      attrsOutOfOrder: true,
      extraBefore: `
        <p class="cead-vintage" data-astro-cid-x><time datetime="2026-06-16">June 16, 2026</time></p>
        <h2 class="section-heading" data-astro-cid-y>Other</h2>
        <h2 class="section-heading" data-astro-cid-y>Other</h2>
      `,
    });
    expect(checkCommuneSection(html, 'en')).toEqual([]);
  });

  it('R-07: newest item dated tomorrow UTC expects a NON-stale section, gives []', () => {
    const html = buildCommuneHtml({
      buildNow: '2026-09-23T23:30:00.000Z',
      newest: '2026-09-24',
      stale: 'false',
      heading: 'Recent Incidents in the News',
    });
    expect(checkCommuneSection(html, 'en')).toEqual([]);
  });

  it('the old "(none in the last 7 days)" heading gives an error', () => {
    const html = buildCommuneHtml({
      buildNow: '2026-09-23T12:00:00.000Z',
      newest: '2026-09-04',
      stale: 'true',
      heading: '(none in the last 7 days)',
    });
    const errors = checkCommuneSection(html, 'en');
    expect(errors.length).toBeGreaterThan(0);
  });
});
