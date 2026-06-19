/**
 * IncidentsList.tsx — Incident event rows inside the ResultPanel.
 *
 * T-03-02-01: External links use rel="noopener noreferrer"; never dangerouslySetInnerHTML.
 * Empty state: em-dash (section heading is always shown by parent).
 */

export interface Incident {
  id: string;
  title_es: string;
  title_en: string;
  date: string;
  outlet: string;
  url: string;
  slug?: string;
  cut?: string;
}

interface Props {
  incidents: Incident[] | null | undefined;
  lang: 'en' | 'es';
}

export function IncidentsList({ incidents, lang }: Props) {
  if (!incidents || incidents.length === 0) {
    return <p className="panel-muted" style={{ margin: 0, color: 'var(--muted)', fontSize: 16 }}>—</p>;
  }

  return (
    <div className="incidents-list">
      {incidents.map((e) => (
        <div className="event-row" key={e.id}>
          <div className="event-title">
            {lang === 'es' ? e.title_es : e.title_en}
          </div>
          <div className="event-meta">
            {e.date} · {e.outlet}
          </div>
          {/* T-03-02-01: rel="noopener noreferrer" on all external links */}
          <a
            href={e.url}
            target="_blank"
            rel="noopener noreferrer"
            className="event-source"
          >
            {lang === 'es' ? 'Fuente' : 'Source'}: {e.outlet}
          </a>
          {/* T-16-11: React JSX auto-escapes slug; only render when slug is present */}
          {e.slug && (
            <a
              href={lang === 'es' ? '/es/comuna/' + e.slug + '/' : '/commune/' + e.slug + '/'}
              className="event-commune-link"
            >
              {lang === 'es' ? 'Ver comuna' : 'View commune'}
            </a>
          )}
        </div>
      ))}
    </div>
  );
}
