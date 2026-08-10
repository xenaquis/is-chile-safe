/**
 * MapTopbar.tsx — Composes SearchBox + NewsToggle + StateSummary + LayerRail
 * + FilterSheet in the map topbar overlay.
 * MAPV2: EntryPointsRail (3 closed <details>) is replaced by LayerRail (one
 * always-visible chip row + year select). Mode is now implied by the chosen
 * layer, so the mode props collapse into onLayerChange.
 * Position: absolute top, z-index 800, full width below the page header.
 */
import React from 'react';
import { SearchBox, type CommuneIndexEntry } from './SearchBox';
import { NewsToggle } from './NewsToggle';
import { LayerRail, StateSummary } from './LayerRail';
import { FilterSheet } from './FilterSheet';
import type { LayerDef } from '../../lib/mapFilterDefs';

interface Props {
  lang: 'en' | 'es';
  index: CommuneIndexEntry[];
  year: number;
  onYearChange: (year: number) => void;
  mode: 'composite' | 'family';
  crimeFamily: string | null;
  onLayerChange: (def: LayerDef) => void;
  showEvents: boolean;
  onEventsToggle: (v: boolean) => void;
  onSelect: (cut: string) => void;
  onLocate: () => void;
}

export function MapTopbar({
  lang,
  index,
  year,
  onYearChange,
  mode,
  crimeFamily,
  onLayerChange,
  showEvents,
  onEventsToggle,
  onSelect,
  onLocate,
}: Props) {
  return (
    <div className="map-topbar">
      <div className="map-topbar-row1">
        <SearchBox
          index={index}
          lang={lang}
          onSelect={onSelect}
          onLocate={onLocate}
        />
        <NewsToggle lang={lang} showEvents={showEvents} onEventsToggle={onEventsToggle} />
        <StateSummary lang={lang} year={year} crimeFamily={crimeFamily} mode={mode} />
      </div>
      <LayerRail
        lang={lang}
        year={year}
        onYearChange={onYearChange}
        mode={mode}
        crimeFamily={crimeFamily}
        onLayerChange={onLayerChange}
      />
      <FilterSheet
        lang={lang}
        year={year}
        onYearChange={onYearChange}
        mode={mode}
        crimeFamily={crimeFamily}
        onLayerChange={onLayerChange}
      />
    </div>
  );
}
