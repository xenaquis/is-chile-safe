/**
 * NewsStrip.tsx — MAPV2: context strip for the news layer.
 *
 * The old news layer was a bare on/off toggle. This strip (shown only while
 * the layer is on and data is loaded) gives it three things the toggle
 * never had:
 *   1. a COUNT — how many press incidents are on the map right now,
 *   2. a SCOPE — the strip inherits the active crime-family filter, so the
 *      pins and the choropleth always answer the same question,
 *   3. a TIMELINE — one bar per day over the scrape window; clicking a day
 *      filters the pins to that day (click again or use the chip to clear).
 *
 * Receives incidents ALREADY family-filtered by MapIsland (single source of
 * filtering truth); day filtering is owned here via day/onDayChange.
 */
import { mapV2Strings } from '../../config/mapV2Strings';
import type { Incident } from './IncidentPinLayer';
import type { StripDay } from '../../lib/newsStripDays';

interface Props {
  lang: 'en' | 'es';
  /** Family-filtered incidents (NOT day-filtered — the bars need all days). */
  incidents: Incident[];
  windowDays: number;
  /** Label of the inherited scope, e.g. "Robos violentos" or "todos los tipos". */
  scopeLabel: string;
  day: string | null;
  onDayChange: (day: string | null) => void;
  /** R2/F35-R1-06 (G-22(b)): the coverage-clipped day range, computed by
   *  MapIsland via computeStripDays over the UNFILTERED incidents file. Gap
   *  days come from here, never re-derived from the family-filtered
   *  `incidents` this component receives. */
  days: StripDay[];
}

/** YYYY-MM-DD → short local label like "11 jul" / "Jul 11". */
function dayLabel(d: string, lang: 'en' | 'es'): string {
  const date = new Date(d + 'T00:00:00');
  return date.toLocaleDateString(lang === 'es' ? 'es-CL' : 'en-US', { day: 'numeric', month: 'short' });
}

export function NewsStrip({ lang, incidents, windowDays, scopeLabel, day, onDayChange, days }: Props) {
  const v2 = mapV2Strings(lang);
  if (incidents.length === 0 && day === null) {
    return (
      <div className="news-strip" role="region" aria-label={v2.news_strip_incidents}>
        <div className="news-strip-head">
          <span className="ev-dot-mini" aria-hidden="true" />
          <strong>0 {v2.news_strip_incidents}</strong>
          <span className="news-strip-scope">{scopeLabel}</span>
        </div>
      </div>
    );
  }

  // R2/F35-R1-06 (G-22(b)): `days` is the coverage-clipped range from
  // computeStripDays (MapIsland), computed over the UNFILTERED incidents
  // file. Bar counts still come from the family-filtered `incidents` this
  // component receives — the range and the counts are deliberately two
  // different sources (range = coverage, counts = active scope).
  const counts: Record<string, number> = {};
  for (const i of incidents) counts[i.date] = (counts[i.date] ?? 0) + 1;
  const max = Math.max(1, ...days.map((d) => counts[d.date] ?? 0));

  return (
    <div className="news-strip" role="region" aria-label={v2.news_strip_incidents}>
      <div className="news-strip-head">
        <span className="ev-dot-mini" aria-hidden="true" />
        <strong>
          {incidents.length} {v2.news_strip_incidents}
        </strong>
        <span className="news-strip-scope">
          {scopeLabel} · {v2.news_strip_days.replace('{n}', String(windowDays))}
        </span>
        {day !== null && (
          <button
            type="button"
            className="news-strip-clear"
            onClick={() => onDayChange(null)}
            aria-label={v2.news_strip_clear_day}
          >
            {dayLabel(day, lang)} ×
          </button>
        )}
      </div>
      <span id="news-strip-day-hint" className="sr-only">{v2.news_strip_day_hint}</span>
      <div className="news-strip-bars" aria-describedby="news-strip-day-hint">
        {days.map(({ date: d, gap }) => {
          const n = counts[d] ?? 0;
          const active = day === d;
          return (
            <button
              key={d}
              type="button"
              className={`news-strip-bar${active ? ' active' : ''}${gap ? ' gap' : ''}`}
              aria-pressed={active}
              aria-label={gap ? `${dayLabel(d, lang)}: ${v2.news_strip_gap}` : `${dayLabel(d, lang)}: ${n} ${v2.news_strip_incidents}`}
              onClick={() => onDayChange(active ? null : d)}
              style={{ opacity: day === null || active ? 1 : 0.3 }}
            >
              <span aria-hidden="true" style={{ height: gap ? '10%' : `${Math.max(6, Math.round((n / max) * 100))}%` }} />
            </button>
          );
        })}
      </div>
    </div>
  );
}
