/**
 * UserLocationMarker.ts — Geolocation + ray-cast point-in-polygon.
 *
 * Exports:
 *   locate(map, geoFeatures, userRef, onSelectCut, onToast, lang) — triggers
 *     browser Geolocation API; on success runs PiP to find user's commune CUT;
 *     places a .user-dot L.divIcon marker; calls onSelectCut + onToast.
 *     Degrades gracefully: out-of-Chile → simulate Santiago; permission
 *     denied → denied toast; API unavailable → simulate silently.
 *
 *   pointInPolygon(lat, lng, features) — O(features × rings) ray-cast;
 *     handles Polygon + MultiPolygon; returns CUT string or null.
 *
 * D-14: true PiP (not centroid-distance).
 * D-16: user-dot is DOM-based L.marker (not canvas renderer).
 * Pitfall 7: uses L.divIcon to avoid default marker-icon.png 404.
 *
 * GeoJSON coordinate convention: rings are [lng, lat] arrays.
 * Chile bounding box: lat (-56.5, -17), lng (-76.5, -66).
 */

import L from 'leaflet';
import type { MutableRefObject } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Lang = 'en' | 'es';

// ---------------------------------------------------------------------------
// Point-in-Polygon (ray-cast, Polygon + MultiPolygon)
// ---------------------------------------------------------------------------

/**
 * ringContains — ray-cast algorithm for a single ring.
 * Ring coords are [lng, lat]. pt is [lng, lat].
 */
function ringContains(ring: number[][], pt: [number, number]): boolean {
  const [x, y] = pt;
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i]!;
    const [xj, yj] = ring[j]!;
    const intersect =
      yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

/**
 * containsPoint — dispatch Polygon vs MultiPolygon.
 * Returns true if pt is inside any ring (outer ring only — ignoring holes
 * is acceptable for commune-level PiP at this scale).
 */
function containsPoint(
  geometry: GeoJSON.Geometry,
  pt: [number, number]
): boolean {
  if (geometry.type === 'Polygon') {
    // geometry.coordinates[0] is the outer ring
    return ringContains(geometry.coordinates[0] as number[][], pt);
  }
  if (geometry.type === 'MultiPolygon') {
    return geometry.coordinates.some((poly) =>
      ringContains(poly[0] as number[][], pt)
    );
  }
  return false;
}

/**
 * pointInPolygon — find CUT of the feature containing (lat, lng).
 * Returns null if no feature contains the point.
 */
export function pointInPolygon(
  lat: number,
  lng: number,
  features: GeoJSON.Feature[]
): string | null {
  const pt: [number, number] = [lng, lat]; // GeoJSON coords are [lng, lat]
  for (const f of features) {
    if (!f.geometry) continue;
    if (containsPoint(f.geometry, pt)) {
      return (f.properties as { id: string }).id;
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// Chile bounding box guard
// ---------------------------------------------------------------------------

function insideChile(lat: number, lng: number): boolean {
  return lat > -56.5 && lat < -17 && lng > -76.5 && lng < -66;
}

// ---------------------------------------------------------------------------
// locate — main export
// ---------------------------------------------------------------------------

/**
 * locate — trigger Geolocation API, place user-dot, highlight commune.
 *
 * Flow:
 *  1. navigator.geolocation present → getCurrentPosition (timeout 5000 ms)
 *     a. success, inside Chile → PiP → onSelectCut(cut) + success toast
 *     b. success, outside Chile → simulate Santiago + approximate toast
 *     c. error (denied / timeout) → denied toast, no crash
 *  2. geolocation unavailable → simulate Santiago silently
 */
export function locate(
  map: L.Map,
  geoFeatures: GeoJSON.Feature[],
  userRef: MutableRefObject<L.Marker | null>,
  onSelectCut: (cut: string) => void,
  onToast: (msg: string) => void,
  lang: Lang
): void {
  function placeMarker(lat: number, lng: number): void {
    // Remove previous user-dot (if any)
    if (userRef.current) {
      userRef.current.remove();
      userRef.current = null;
    }
    // D-16: DOM-based L.marker with L.divIcon (Pitfall 7 — no default marker icon)
    userRef.current = L.marker([lat, lng], {
      icon: L.divIcon({
        className: '',
        html: '<div class="user-dot"></div>',
        iconSize: [18, 18],
        iconAnchor: [9, 9],
      }),
    })
      .bindTooltip(lang === 'es' ? 'Mi ubicación' : 'My location', {
        direction: 'top',
        offset: [0, -10],
      })
      .addTo(map);
  }

  function finish(lat: number, lng: number, simulated: boolean): void {
    placeMarker(lat, lng);

    // D-14: PiP to find commune
    const cut = pointInPolygon(lat, lng, geoFeatures);
    if (cut) {
      onSelectCut(cut);
    }

    // flyTo zoom 12
    map.flyTo([lat, lng], 12, { duration: 0.8 });

    // Toast copy per UI-SPEC
    if (simulated) {
      onToast(
        lang === 'es'
          ? 'Ubicación aproximada: Santiago'
          : 'Approx. location: Santiago'
      );
    } else {
      // Use commune CUT as name placeholder; ResultPanel will show the real name
      const nameHint = cut ?? 'tu zona';
      onToast(
        lang === 'es'
          ? `Tu comuna: ${nameHint}`
          : `Your commune: ${nameHint}`
      );
    }
  }

  const simulate = (): void => finish(-33.44, -70.65, true);

  if (typeof navigator !== 'undefined' && navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude: la, longitude: lo } = position.coords;
        if (insideChile(la, lo)) {
          finish(la, lo, false);
        } else {
          simulate();
        }
      },
      () => {
        // Permission denied or position unavailable — graceful toast, no crash
        onToast(
          lang === 'es'
            ? 'No se pudo obtener tu ubicación'
            : 'Location access denied'
        );
      },
      { timeout: 5000 }
    );
  } else {
    // Geolocation API unavailable — simulate silently
    simulate();
  }
}
