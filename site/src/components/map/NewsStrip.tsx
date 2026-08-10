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

interface Props {
  lang: 'en' | 'es';
  /** Family-filtered incidents (NOT day-filtered — the bars need all days). */
  incidents: Incident[];
  windowDays: number;
  /** Label of the inherited scope, e.g. "Robos violentos" or "todos los tipos". */
  scopeLabel: string;
  day: string | null;
  onDayChange: (day: string | null) => void;
  /** MPX-C4: max date across the UNFILTERED incidents file, passed down from
   *  MapIsland. The timeline anchor must not shrink to the filtered
   *  subset's own most-recent date — that silently truncates the window. */
  anchor: string;
}

/** YYYY-MM-DD → short local label like "11 jul" / "Jul 11". */
function dayLabel(d: string, lang: 'en' | 'es'): string {
  const date = new Date(d + 'T00:00:00');
  return date.toLocaleDateString(lang === 'es' ? 'es-CL' : 'en-US', { day: 'numeric', month: 'short' });
}

function shiftDays(d: string, n: number): string {
  const t = new Date(d + 'T00:00:00Z');
  t.setUTCDate(t.getUTCDate() + n);
  return t.toISOString().slice(0, 10);
}

export function NewsStrip({ lang, incidents, windowDays, scopeLabel, day, onDayChange, anchor }: Props) {
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

  // MPX-C4: anchor comes from the UNFILTERED incidents file (prop), not the
  // family-filtered `incidents` this strip receives — otherwise a filter
  // with no recent hits silently shifts the whole window backward.
  //
  // MPX-C2: the day range spans min→max of the actual incident dates
  // (window_days is display text only) — a 30-day window can legitimately
  // contain 31 distinct calendar dates, and truncating by count drops the
  // oldest day while the header count still includes it.
  const days: string[] = [];
  if (anchor) {
    let minDate = anchor;
    for (const i of incidents) if (i.date < minDate) minDate = i.date;
    const windowStart = shiftDays(anchor, -(windowDays - 1));
    if (windowStart < minDate) minDate = windowStart;
    for (let d = minDate; d <= anchor; d = shiftDays(d, 1)) {
      days.push(d);
    }
  }
  const counts: Record<string, number> = {};
  for (const i of incidents) counts[i.date] = (counts[i.date] ?? 0) + 1;
  const max = Math.max(1, ...days.map((d) => counts[d] ?? 0));

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
        {days.map((d) => {
          const n = counts[d] ?? 0;
          const active = day === d;
          return (
            <button
              key={d}
              type="button"
              className={`news-strip-bar${active ? ' active' : ''}`}
              aria-pressed={active}
              aria-label={`${dayLabel(d, lang)}: ${n} ${v2.news_strip_incidents}`}
              onClick={() => onDayChange(active ? null : d)}
              style={{ opacity: day === null || active ? 1 : 0.3 }}
            >
              <span aria-hidden="true" style={{ height: `${Math.max(6, Math.round((n / max) * 100))}%` }} />
            </button>
          );
        })}
      </div>
    </div>
  );
}
