/**
 * FilterSheet.tsx — mobile (<=480px) filter entry point (MAPSH-02/03).
 * MAPV2: the sheet body now shows TWO dimensions (Capa + Año) instead of
 * three — LayerField replaces FamilyField + ModeField. All the dialog
 * mechanics below are ported verbatim from the original file:
 *
 * A FAB (`data-role="filter-entry"`) opens a native `<dialog>` bottom sheet
 * via `showModal()` — never the `open` attribute (focus containment, Escape,
 * backdrop). `aria-expanded` on the FAB is owned by THREE imperative
 * setAttribute sites (FAB click / close click / native 'close' event) and is
 * intentionally NOT set in JSX (M-02). Light dismiss on backdrop click is
 * manual (M-03). Focus is returned to the FAB only if visible (L-02).
 */

import { useEffect, useRef } from 'react';
import { EN_STRINGS, ES_STRINGS } from '../../config/i18n';
import { YearField, LayerField } from './FilterFields';
import { mapV2Strings } from '../../config/mapV2Strings';
import type { LayerDef } from '../../lib/mapFilterDefs';

interface Props {
  lang: 'en' | 'es';
  year: number;
  onYearChange: (year: number) => void;
  mode: 'composite' | 'family';
  crimeFamily: string | null;
  onLayerChange: (def: LayerDef) => void;
}

export function FilterSheet({
  lang,
  year,
  onYearChange,
  mode,
  crimeFamily,
  onLayerChange,
}: Props) {
  const strings = lang === 'es' ? ES_STRINGS : EN_STRINGS;
  const v2 = mapV2Strings(lang);
  const fabRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const closeBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const fab = fabRef.current;
    const dialog = dialogRef.current;
    const closeBtn = closeBtnRef.current;
    if (!fab || !dialog || !closeBtn) return;

    function handleFabClick() {
      dialog!.showModal();
      fab!.setAttribute('aria-expanded', 'true');
    }

    // L-02: guard against focusing a hidden FAB — .filter-fab is display:none
    // above 480px, so a viewport widen while the sheet is open must not call
    // .focus() on a non-rendered element.
    function focusFabIfVisible() {
      if (fab!.offsetParent !== null) {
        fab!.focus();
      }
    }

    function handleCloseClick() {
      dialog!.close();
      fab!.setAttribute('aria-expanded', 'false');
      focusFabIfVisible();
    }

    function handleDialogClose() {
      fab!.setAttribute('aria-expanded', 'false');
      focusFabIfVisible();
    }

    fab.addEventListener('click', handleFabClick);
    closeBtn.addEventListener('click', handleCloseClick);
    dialog.addEventListener('close', handleDialogClose);

    return () => {
      fab.removeEventListener('click', handleFabClick);
      closeBtn.removeEventListener('click', handleCloseClick);
      dialog.removeEventListener('close', handleDialogClose);
    };
  }, []);

  return (
    <>
      {/* M-02: aria-expanded intentionally NOT set here in JSX — owned by the
          imperative setAttribute() calls above so there is exactly one writer. */}
      <button
        type="button"
        ref={fabRef}
        data-role="filter-entry"
        className="filter-fab"
        aria-label={strings.map_filters_fab}
        aria-haspopup="dialog"
      >
        {strings.map_filters_fab}
      </button>
      <dialog
        id="filter-sheet"
        ref={dialogRef}
        aria-labelledby="filter-sheet-title"
        className="filter-sheet"
        onClick={(e) => {
          // M-03: light dismiss — a click landing on the <dialog> element
          // itself (the ::backdrop) closes the sheet.
          if (e.target === dialogRef.current) {
            dialogRef.current?.close();
          }
        }}
      >
        <div className="filter-sheet-inner">
        <div className="filter-sheet-header">
          <h2 id="filter-sheet-title">{strings.map_filters_fab}</h2>
          <button
            type="button"
            ref={closeBtnRef}
            className="filter-sheet-close"
            aria-label={lang === 'es' ? 'Cerrar' : 'Close'}
          >
            &times;
          </button>
        </div>
        <div className="filter-sheet-body">
          <div>
            <div className="filter-sheet-field-label">{v2.layer_group}</div>
            <LayerField lang={lang} mode={mode} crimeFamily={crimeFamily} onLayerChange={onLayerChange} />
          </div>
          <div>
            <div className="filter-sheet-field-label">{strings.map_entry_year}</div>
            <YearField lang={lang} year={year} onYearChange={onYearChange} />
          </div>
        </div>
        </div>
      </dialog>
    </>
  );
}
