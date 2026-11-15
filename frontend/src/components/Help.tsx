import { useEffect, useRef } from 'react'
import { t, tu } from '../i18n'

// "Nasıl kullanılır?" — a short in-app guide (the long one is docs/KULLANIM_KILAVUZU.md).
export function HelpDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (open && !d.open) d.showModal()
    if (!open && d.open) d.close()
  }, [open])

  return (
    <dialog ref={ref} className="help" onClose={onClose} aria-labelledby="help-title">
      <div className="help-head">
        <h2 id="help-title">❓ {tu.help}</h2>
        <button type="button" className="btn" onClick={onClose}>
          ✕ {tu.close}
        </button>
      </div>
      <ol className="help-steps">
        {tu.helpSteps.map(([title, text]) => (
          <li key={title}>
            <strong>{title}</strong>
            <span>{text}</span>
          </li>
        ))}
      </ol>
      <p className="small">{tu.helpScores}</p>
      <p className="disclaimer">⚠️ {t.disclaimer}</p>
      <p className="muted small">{tu.helpOffline}</p>
      <p className="muted small">{tu.helpGuide}</p>
    </dialog>
  )
}
