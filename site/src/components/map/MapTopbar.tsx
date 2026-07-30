/**
 * MapTopbar.tsx — Composes SearchBox + NewsToggle + EntryPointsRail + FilterSheet
 * in the map topbar overlay.
 * Position: absolute top, z-index 800, full width below the page header.
 */
import React from 'react';
import { SearchBox, type CommuneIndexEntry } from './SearchBox';
import { NewsToggle } from './NewsToggle';
import { EntryPointsRail } from './EntryPointsRail';
import { FilterSheet } from './FilterSheet';

interface Props {
  lang: 'en' | 'es';
  index: CommuneIndexEntry[];
  year: number;
  onYearChange: (year: number) => void;
  crimeFamily: string | null;
  onFamilyChange: (key: string | null, index: number | null) => void;
  showEvents: boolean;
  onEventsToggle: (v: boolean) => void;
  onSelect: (cut: string) => void;
  onLocate: () => void;
  mode: 'composite' | 'family';
  onModeChange: (mode: 'composite' | 'family') => void;
}

export function MapTopbar({
  lang,
  index,
  year,
  onYearChange,
  crimeFamily,
  onFamilyChange,
  showEvents,
  onEventsToggle,
  onSelect,
  onLocate,
  mode,
  onModeChange,
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
      </div>
      <EntryPointsRail
        lang={lang}
        year={year}
        onYearChange={onYearChange}
        crimeFamily={crimeFamily}
        onFamilyChange={onFamilyChange}
        mode={mode}
        onModeChange={onModeChange}
      />
      <FilterSheet
        lang={lang}
        year={year}
        onYearChange={onYearChange}
        crimeFamily={crimeFamily}
        onFamilyChange={onFamilyChange}
        mode={mode}
        onModeChange={onModeChange}
      />
    </div>
  );
}
