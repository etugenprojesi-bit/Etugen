import { te } from '../i18n'

export type Mode = 'easy' | 'expert'

export function ModeChooser({ onChoose }: { onChoose: (m: Mode) => void }) {
  return (
    <section className="mode-chooser">
      <h2 className="section-title">{te.chooseTitle}</h2>
      <p className="muted small lead">{te.chooseIntro}</p>
      <button type="button" className="card mode-option" onClick={() => onChoose('easy')}>
        <span className="mode-icon" aria-hidden="true">🧑‍🌾</span>
        <span>
          <strong>{te.easyName}</strong>
          <span className="small">{te.easyText}</span>
        </span>
      </button>
      <button type="button" className="card mode-option" onClick={() => onChoose('expert')}>
        <span className="mode-icon" aria-hidden="true">🔬</span>
        <span>
          <strong>{te.expertName}</strong>
          <span className="small">{te.expertText}</span>
        </span>
      </button>
    </section>
  )
}
