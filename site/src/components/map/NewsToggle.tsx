/**
 * NewsToggle.tsx — standalone, always-visible, labeled news-layer toggle
 * (MAPSH-01). Replaces the baseline's offscreen toggle (29-DESIGN-SPEC.md §0,
 * x=1370 at 1296px). Never buried in a filter surface; label is shortened,
 * never hidden, below 640px (spec §7 "shorten, never remove").
 */

import { EN_STRINGS, ES_STRINGS } from '../../config/i18n';

interface Props {
  lang: 'en' | 'es';
  showEvents: boolean;
  onEventsToggle: (show: boolean) => void;
}

export function NewsToggle({ lang, showEvents, onEventsToggle }: Props) {
  const strings = lang === 'es' ? ES_STRINGS : EN_STRINGS;

  return (
    <button
      type="button"
      data-role="news-toggle"
      aria-pressed={showEvents}
      aria-label={strings.map_news_toggle_long}
      className={`news-toggle${showEvents ? ' active' : ''}`}
      onClick={() => onEventsToggle(!showEvents)}
    >
      <span className="ev-dot-mini" aria-hidden="true" />
      <span className="news-toggle-label-long">{strings.map_news_toggle_long}</span>
      <span className="news-toggle-label-short">{strings.map_news_toggle_short}</span>
    </button>
  );
}
