/**
 * IncidentPinLayer.ts — NEWS layer: fetch incidents/current.json + mount divIcon pins.
 *
 * MAPV2: the original fetchAndMountIncidents (fetch + mount fused) is split so
 * MapIsland can hold the incidents in state and re-mount a FILTERED subset of
 * pins when the crime-family or day filter changes:
 *
 *   fetchIncidents(lang, onToast)          → Promise<IncidentsFile | null>
 *   mountIncidentPins(map, incidents, lang) → L.LayerGroup
 *   fetchAndMountIncidents(map, lang, onToast) — kept for compatibility.
 *
 * Pins are cheap DOM markers; re-mounting the pin LayerGroup on filter change
 * is fine — D-12 (never re-mount) applies to the polygon choropleth only.
 *
 * D-15: absent file → graceful empty state via toast; NO console error.
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
// fetchIncidents — data only (MAPV2 split)
// ---------------------------------------------------------------------------

export async function fetchIncidents(
  lang: 'en' | 'es',
  onToast: (msg: string) => void
): Promise<IncidentsFile | null> {
  try {
    const res = await fetch('/data/incidents/current.json');
    if (!res.ok) {
      // 404 = Phase 5 not yet deployed — graceful empty state (D-15)
      onToast(
        lang === 'es' ? 'Capa de noticias próximamente' : 'News layer coming soon'
      );
      return null;
    }
    return (await res.json()) as IncidentsFile;
  } catch {
    // Network error — same graceful path, no console error
    onToast(
      lang === 'es' ? 'Capa de noticias próximamente' : 'News layer coming soon'
    );
    return null;
  }
}

// ---------------------------------------------------------------------------
// mountIncidentPins — mount a (possibly filtered) incident subset
// ---------------------------------------------------------------------------

export function mountIncidentPins(
  map: L.Map,
  incidents: Incident[],
  lang: 'en' | 'es'
): L.LayerGroup {
  const layer = L.layerGroup();

  // Locale-aware commune URL prefix (Pitfall 5)
  const communeBase = lang === 'es' ? '/es/comuna/' : '/commune/';

  for (const incident of incidents) {
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
    // T-25-04-XSS: title already escaped via escHtml above; reuse for aria-label/title
    L.marker([incident.lat, incident.lng], {
      icon: L.divIcon({
        className: '',
        html: `<div class="ev-dot" role="img" aria-label="${title}"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      }),
      title: title,
    } as L.MarkerOptions)
      .bindPopup(popupHtml, { closeButton: false, offset: [0, -4] })
      .addTo(layer);
  }

  return layer.addTo(map);
}

// ---------------------------------------------------------------------------
// fetchAndMountIncidents — original fused API, kept for compatibility
// ---------------------------------------------------------------------------

export async function fetchAndMountIncidents(
  map: L.Map,
  lang: 'en' | 'es',
  onToast: (msg: string) => void
): Promise<L.LayerGroup | null> {
  const data = await fetchIncidents(lang, onToast);
  if (!data) return null;
  return mountIncidentPins(map, data.incidents, lang);
}
