/**
 * Toast.tsx — Ephemeral map notification with 3000ms auto-dismiss.
 *
 * UI-SPEC: padding 10px 20px (not 8px); background var(--ink); color #fff.
 * Accessibility: role="status" + aria-live="polite".
 */
import { useEffect } from 'react';

interface Props {
  msg: string;
  onDismiss: () => void;
}

export function Toast({ msg, onDismiss }: Props) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 3000);
    return () => clearTimeout(t);
  }, [msg, onDismiss]);

  return (
    <div className="toast" role="status" aria-live="polite">
      {msg}
    </div>
  );
}
