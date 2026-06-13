/**
 * MapTopbar.tsx — Composes SearchBox + FiltersRow in the map topbar overlay.
 * Position: absolute top, z-index 800, full width below the page header.
 */
import { SearchBox, type CommuneIndexEntry } from './SearchBox';
import { FiltersRow } from './FiltersRow';

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
      </div>
      <FiltersRow
        lang={lang}
        year={year}
        onYearChange={onYearChange}
        crimeFamily={crimeFamily}
        onFamilyChange={onFamilyChange}
        showEvents={showEvents}
        onEventsToggle={onEventsToggle}
      />
    </div>
  );
}
