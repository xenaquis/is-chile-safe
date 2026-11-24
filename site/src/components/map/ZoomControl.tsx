/**
 * ZoomControl.tsx — Desktop +/− zoom buttons.
 * Hidden on mobile via map.css (< 640px).
 */
import type { RefObject } from 'react';
import type L from 'leaflet';

interface Props {
  mapRef: RefObject<L.Map | null>;
  lang?: 'en' | 'es';
}

export function ZoomControl({ mapRef, lang = 'en' }: Props) {
  return (
    <div className="zoom-ctl">
      <button
        onClick={() => mapRef.current?.zoomIn()}
        aria-label={lang === 'es' ? 'Acercar' : 'Zoom in'}
      >
        +
      </button>
      <button
        onClick={() => mapRef.current?.zoomOut()}
        aria-label={lang === 'es' ? 'Alejar' : 'Zoom out'}
      >
        −
      </button>
    </div>
  );
}
