/**
 * FilterSheet.tsx — mobile (<=480px) filter entry point (MAPSH-02/03).
 * A FAB (`data-role="filter-entry"`) opens a native `<dialog>` bottom sheet
 * via `showModal()` — never the `open` attribute, since only `showModal()`
 * gives native focus containment, Escape and a backdrop (spec section 5).
 * The three FilterFields dimensions render flat inside the dialog body — no
 * <details> wrapper, since the dialog itself already provides disclosure.
 *
 * `aria-expanded` on the FAB is set via `setAttribute` at THREE sites: the
 * FAB click handler ('true'), the close-button click handler ('false'), and
 * the dialog's native 'close' event ('false') — which also fires on Escape
 * and backdrop dismissal. Relying on the close event alone was iteration 1's
 * defect (it never fired in that build); relying on click alone would repeat
 * the failure in the opposite direction on Escape/backdrop close. Both paths
 * are wired independently.
 */

import { useEffect, useRef } from 'react';
import { EN_STRINGS, ES_STRINGS } from '../../config/i18n';
import { YearField, FamilyField, ModeField } from './FilterFields';

interface Props {
  lang: 'en' | 'es';
  year: number;
  onYearChange: (year: number) => void;
  crimeFamily: string | null;
  onFamilyChange: (key: string | null, index: number | null) => void;
  mode: 'composite' | 'family';
  onModeChange: (mode: 'composite' | 'family') => void;
}

export function FilterSheet({
  lang,
  year,
  onYearChange,
  crimeFamily,
  onFamilyChange,
  mode,
  onModeChange,
}: Props) {
  const strings = lang === 'es' ? ES_STRINGS : EN_STRINGS;
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

    function handleCloseClick() {
      dialog!.close();
      fab!.setAttribute('aria-expanded', 'false');
      fab!.focus();
    }

    function handleDialogClose() {
      fab!.setAttribute('aria-expanded', 'false');
      // Spec §6: closing returns focus to the invoking control. Measured in a real
      // browser: after a native Escape dismissal focus lands on <body>, not on the
      // FAB — the close-button path restores it explicitly, this path did not.
      fab!.focus();
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
      <button
        type="button"
        ref={fabRef}
        data-role="filter-entry"
        className="filter-fab"
        aria-label={strings.map_filters_fab}
        aria-haspopup="dialog"
        aria-expanded="false"
      >
        {strings.map_filters_fab}
      </button>
      <dialog
        id="filter-sheet"
        ref={dialogRef}
        aria-labelledby="filter-sheet-title"
        className="filter-sheet"
      >
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
            <div className="filter-sheet-field-label">{strings.map_entry_year}</div>
            <YearField lang={lang} year={year} onYearChange={onYearChange} />
          </div>
          <div>
            <div className="filter-sheet-field-label">{strings.map_entry_family}</div>
            <FamilyField lang={lang} crimeFamily={crimeFamily} onFamilyChange={onFamilyChange} />
          </div>
          <div>
            <div className="filter-sheet-field-label">{strings.map_entry_mode}</div>
            <ModeField lang={lang} mode={mode} onModeChange={onModeChange} />
          </div>
        </div>
      </dialog>
    </>
  );
}
