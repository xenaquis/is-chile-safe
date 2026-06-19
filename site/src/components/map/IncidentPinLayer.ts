/**
 * IncidentPinLayer.ts — NEWS layer: fetch incidents/current.json + mount divIcon pins.
 *
 * Exports:
 *   fetchAndMountIncidents(map, lang, onToast) → Promise<L.LayerGroup | null>
 *     Fetches /data/incidents/current.json.
 *     - If absent / 404 / network error → "coming soon" toast, returns null, NO console error.
 *     - If present → builds L.layerGroup of .ev-dot L.divIcon markers with
 *       localized popup (title, date, outlet, source link).
 *
 * incidents/current.json schema (defined here for Phase 5 to produce):
 * {
 *   generated: string;          // ISO-8601 timestamp of when file was built
 *   window_days: number;        // how many days back incidents were scraped
 *   incidents: Array<{
 *     id: string;               // unique incident ID
 *     cut: string;              // commune CUT code
 *     lat: number;              // approx. latitude (commune centroid from CEAD catalog)
 *     lng: number;              // approx. longitude
 *     title_es: string;         // incident headline in Spanish
 *     title_en: string;         // incident headline in English
 *     date: string;             // YYYY-MM-DD
 *     outlet: string;           // news outlet name (e.g. "BioBio Chile")
 *     url: string;              // source article URL
 *     family: string;           // crime family key (vida, propiedad, etc.)
 *   }>;
 * }
 *
 * D-15: absent file → graceful empty state; NO console.error.
 * D-16: pins are DOM-based L.marker (not canvas renderer).
 * Pitfall 7: uses L.divIcon (.ev-dot) — not default marker icon.
 * Security (T-03-03-02): incident strings are HTML-escaped before popup interpolation.
 * Security (T-03-03-03): source links use rel="noopener noreferrer".
 */

import L from 'leaflet';

// ---------------------------------------------------------------------------
// Types (incidents/current.json schema — Phase 5 contract)
// ---------------------------------------------------------------------------

export interface Incident {
  id: string;
  cut: string;
  lat: number;
  lng: number;
  title_es: string;
  title_en: string;
  date: string;
  outlet: string;
  url: string;
  family: string;
  slug?: string;
}

export interface IncidentsFile {
  generated: string;
  window_days: number;
  incidents: Incident[];
}

// ---------------------------------------------------------------------------
// HTML escaping (T-03-03-02 — escape before bindPopup interpolation)
// ---------------------------------------------------------------------------

function escHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Escape a URL: only allow http/https schemes to prevent javascript: injection.
 */
function safeUrl(url: string): string {
  try {
    const u = new URL(url);
    if (u.protocol === 'http:' || u.protocol === 'https:') {
      return escHtml(url);
    }
  } catch {
    // malformed URL — return empty
  }
  return '#';
}

// ---------------------------------------------------------------------------
// fetchAndMountIncidents — main export
// ---------------------------------------------------------------------------

export async function fetchAndMountIncidents(
  map: L.Map,
  lang: 'en' | 'es',
  onToast: (msg: string) => void
): Promise<L.LayerGroup | null> {
  let data: IncidentsFile;

  try {
    const res = await fetch('/data/incidents/current.json');
    if (!res.ok) {
      // 404 = Phase 5 not yet deployed — graceful empty state (D-15)
      onToast(
        lang === 'es' ? 'Capa de noticias próximamente' : 'News layer coming soon'
      );
      return null;
    }
    data = (await res.json()) as IncidentsFile;
  } catch {
    // Network error — same graceful path, no console error
    onToast(
      lang === 'es' ? 'Capa de noticias próximamente' : 'News layer coming soon'
    );
    return null;
  }

  // Build layer group of .ev-dot divIcon markers
  const layer = L.layerGroup();

  // Locale-aware commune URL prefix (Pitfall 5)
  const communeBase = lang === 'es' ? '/es/comuna/' : '/commune/';

  for (const incident of data.incidents) {
    const title = escHtml(lang === 'es' ? incident.title_es : incident.title_en);
    const outlet = escHtml(incident.outlet);
    const date = escHtml(incident.date);
    const url = safeUrl(incident.url);

    const sourceLabel = lang === 'es' ? 'Fuente' : 'Source';
    const approxLabel = lang === 'es' ? 'Ubicación aproximada' : 'Approx. location';
    const communeLabel = lang === 'es' ? 'Ver comuna' : 'View commune';

    // T-16-10: escHtml applied to slug for defense-in-depth
    const communeLink = incident.slug
      ? `<a href="${communeBase}${escHtml(incident.slug)}/">${communeLabel}</a>`
      : '';

    // Popup HTML — all strings escaped above (T-03-03-02)
    const popupHtml = `<div class="ev-pop">
  <div class="ev-badges">
    <span class="ev-badge">CEAD</span>
    <span class="ev-badge">${approxLabel}</span>
  </div>
  <strong>${title}</strong>
  <div class="ev-meta">${date} · ${outlet}</div>
  <div class="ev-meta">
    <a href="${url}" target="_blank" rel="noopener noreferrer">${sourceLabel}: ${outlet}</a>
  </div>${communeLink ? `\n  <div class="ev-meta">${communeLink}</div>` : ''}
</div>`;

    // D-16: DOM-based L.marker; Pitfall 7: L.divIcon (.ev-dot)
    L.marker([incident.lat, incident.lng], {
      icon: L.divIcon({
        className: '',
        html: '<div class="ev-dot"></div>',
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      }),
    })
      .bindPopup(popupHtml, { closeButton: false, offset: [0, -4] })
      .addTo(layer);
  }

  return layer.addTo(map);
}
