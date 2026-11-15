import { useState } from 'react'
import { terms } from '../learn'
import { LANG } from '../lang'

// "?" button that opens a short plain-language explanation under the text.
export function Info({ term }: { term: string }) {
  const [open, setOpen] = useState(false)
  const tm = terms[term]
  if (!tm) return null
  return (
    <>
      <button
        type="button"
        className="info-btn"
        aria-expanded={open}
        aria-label={`${tm.title}: bu ne demek?`}
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          setOpen(!open)
        }}
      >
        ?
      </button>
      {open && (
        <span className="info-pop" role="note">
          <strong>{tm.title}:</strong> {tm.text}
        </span>
      )}
    </>
  )
}

// All terms in one place, at the end of the page.
export function Glossary() {
  return (
    <details className="card glossary">
      <summary className="form-summary">📖 {LANG === 'en' ? 'What does it mean? Terms' : 'Bu ne demek? Terimler'}</summary>
      <dl>
        {Object.entries(terms).map(([k, tm]) => (
          <div key={k}>
            <dt>{tm.title}</dt>
            <dd>{tm.text}</dd>
          </div>
        ))}
      </dl>
    </details>
  )
}
