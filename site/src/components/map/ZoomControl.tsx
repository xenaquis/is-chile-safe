/**
 * ZoomControl.tsx — Desktop +/− zoom buttons.
 * Hidden on mobile via map.css (< 640px).
 */
import type { RefObject } from 'react';
import type L from 'leaflet';

interface Props {
  mapRef: RefObject<L.Map | null>;
}

export function ZoomControl({ mapRef }: Props) {
  return (
    <div className="zoom-ctl">
      <button
        onClick={() => mapRef.current?.zoomIn()}
        aria-label="Zoom in"
      >
        +
      </button>
      <button
        onClick={() => mapRef.current?.zoomOut()}
        aria-label="Zoom out"
      >
        −
      </button>
    </div>
  );
}
