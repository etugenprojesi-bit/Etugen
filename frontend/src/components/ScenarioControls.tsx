import { useState } from 'react'
import { num, tk } from '../i18n'
import type { PrecipSource, Variant } from '../types'
import { Info } from './Learn'

// Slider limits mirror backend/app/features/scenario.py (assumption: demo UI limits).
const T_RANGE = { min: -2, max: 4, step: 0.5 }
const P_RANGE = { min: -30, max: 30, step: 5 }

interface Props {
  value: Variant
  onChange: (v: Variant) => void
}

export function ScenarioControls({ value, onChange }: Props) {
  const [dt, setDt] = useState(value.deltaT)
  const [dp, setDp] = useState(value.deltaP)
  const dirty = dt !== value.deltaT || dp !== value.deltaP

  return (
    <details className="card scenario">
      <summary className="form-summary">⚙️ {tk.scenarioTitle}</summary>

      <fieldset className="segmented" style={{ marginTop: '0.6rem' }}>
        <legend>{tk.precipSource}</legend>
        {(['power', 'imerg', 'chirps'] as PrecipSource[]).map((v) => (
          <label key={v} className={value.precipSource === v ? 'on' : ''}>
            <input
              type="radio"
              name="precip_source"
              value={v}
              checked={value.precipSource === v}
              onChange={() => onChange({ ...value, precipSource: v })}
            />
            {tk.precipOptions[v]}
          </label>
        ))}
      </fieldset>
      <p className="muted small">
        {tk.precipHelp[value.precipSource]} <Info term="rain_sources" />
      </p>

      <label className="check small">
        <input
          type="checkbox"
          checked={value.exploreSowing}
          onChange={(e) => onChange({ ...value, exploreSowing: e.target.checked })}
        />{' '}
        {tk.exploreSowing}
      </label>
      <p className="muted small">{tk.exploreSowingHelp}</p>

      <div className="sliders">
        <label className="slider">
          <span>{tk.deltaT}</span>
          <input type="range" {...T_RANGE} value={dt} onChange={(e) => setDt(Number(e.target.value))} />
          <output>
            {dt > 0 ? '+' : ''}
            {num(dt, 1)} °C
          </output>
        </label>
        <label className="slider">
          <span>{tk.deltaP}</span>
          <input type="range" {...P_RANGE} value={dp} onChange={(e) => setDp(Number(e.target.value))} />
          <output>
            {dp > 0 ? '+' : ''}
            {num(dp)} %
          </output>
        </label>
      </div>
      <div className="row wrap" style={{ marginTop: '0.5rem' }}>
        <button type="button" className="btn primary" disabled={!dirty} onClick={() => onChange({ ...value, deltaT: dt, deltaP: dp })}>
          {tk.apply}
        </button>
        <button
          type="button"
          className="btn"
          disabled={dt === 0 && dp === 0 && value.deltaT === 0 && value.deltaP === 0}
          onClick={() => {
            setDt(0)
            setDp(0)
            onChange({ ...value, deltaT: 0, deltaP: 0 })
          }}
        >
          {tk.reset}
        </button>
        {dirty && <span className="warn small">{tk.pending}</span>}
      </div>
      <p className="muted small">
        {tk.scenarioNote} <Info term="scenario" />
      </p>
    </details>
  )
}
