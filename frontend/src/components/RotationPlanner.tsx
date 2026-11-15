import { useEffect, useMemo, useRef, useState } from 'react'
import { ApiError, fetchRotations } from '../api'
import { t, tr } from '../i18n'
import type { Analysis, PriorityKey, RotationResponse } from '../types'
import { Info } from './Learn'
import { RotationCards } from './RotationCards'
import { LANG, nameIn } from '../lang'

const PRIORITY_KEYS: PriorityKey[] = ['water', 'soil', 'erosion', 'nitrogen', 'income', 'forage']
const EQUIPMENT = ['no_root_harvester', 'no_paddy']
const YEARS = 3

type Result = { kind: 'idle' } | { kind: 'loading' } | { kind: 'error'; message: string } | { kind: 'done'; data: RotationResponse }

export function RotationPlanner({ a }: { a: Analysis }) {
  const crops = useMemo(() => a.crops.filter((c) => c.status !== 'perennial_not_evaluated'), [a])
  const nameOf = useMemo(() => {
    const m = new Map(a.crops.map((c) => [c.id, nameIn(c.name)]))
    return (id: string) => m.get(id) ?? id
  }, [a])
  const [priorities, setPriorities] = useState<Record<PriorityKey, number>>(
    Object.fromEntries(PRIORITY_KEYS.map((k) => [k, 3])) as Record<PriorityKey, number>,
  )
  const [equipment, setEquipment] = useState<string[]>([])
  const [market, setMarket] = useState<string[]>([])
  const [excluded, setExcluded] = useState<string[]>([])
  const [knowsCurrent, setKnowsCurrent] = useState(false)
  const [current, setCurrent] = useState<string[][]>(Array.from({ length: YEARS }, () => ['', '']))
  const [llm, setLlm] = useState(false)
  const [result, setResult] = useState<Result>({ kind: 'idle' })

  // Rainfall source or scenario changed (new analysis): re-run a comparison already shown.
  const firstAnalysis = useRef(a)
  useEffect(() => {
    if (a === firstAnalysis.current) return
    firstAnalysis.current = a
    if (result.kind === 'done') void compare()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [a])

  const toggle = (list: string[], set: (v: string[]) => void, id: string) =>
    set(list.includes(id) ? list.filter((x) => x !== id) : [...list, id])

  async function compare() {
    setResult({ kind: 'loading' })
    const rotation = current.map((y) => y.filter(Boolean)).filter((y) => y.length > 0)
    try {
      const data = await fetchRotations({
        lat: a.query.lat,
        lon: a.query.lon,
        irrigation: a.query.irrigation,
        precip_source: a.query.precip_source,
        delta_t: a.query.delta_t,
        delta_p: a.query.delta_p,
        explore_sowing: a.query.explore_sowing,
        priorities,
        constraints: { excluded_crops: excluded, equipment_limits: equipment, market_crops: market },
        current_rotation: knowsCurrent && rotation.length ? rotation : null,
        explain: llm ? 'llm' : 'template',
        lang: LANG,
      })
      setResult({ kind: 'done', data })
    } catch (e) {
      const status = e instanceof ApiError ? e.status : -1
      setResult({ kind: 'error', message: status === 422 ? t.errors.invalid : status === 0 || status >= 500 ? t.errors.network : t.errors.other })
    }
  }

  return (
    <section className="planner">
      <h2 className="section-title">
        🔄 {tr.plannerTitle} <Info term="rotation" />
      </h2>
      <p className="muted small">
        {tr.plannerIntro} <Info term="legume" /> <Info term="cover_crop" /> <Info term="fallow" />
      </p>

      <details className="card" open>
        <summary className="form-summary">{tr.priorities}</summary>
        <div className="sliders">
          {PRIORITY_KEYS.map((k) => (
            <label key={k} className="slider">
              <span>{tr.priorityNames[k]}</span>
              <input
                type="range"
                min={0}
                max={5}
                step={1}
                value={priorities[k]}
                onChange={(e) => setPriorities({ ...priorities, [k]: Number(e.target.value) })}
              />
              <output>{priorities[k]}</output>
            </label>
          ))}
        </div>
      </details>

      <details className="card">
        <summary className="form-summary">{tr.constraints}</summary>
        <h4>{tr.equipment}</h4>
        {EQUIPMENT.map((eq) => (
          <label key={eq} className="check">
            <input type="checkbox" checked={equipment.includes(eq)} onChange={() => toggle(equipment, setEquipment, eq)} />
            {tr.equipmentOptions[eq]}
          </label>
        ))}
        <h4>{tr.marketCrops}</h4>
        <ChipPicker crops={crops} selected={market} onToggle={(id) => toggle(market, setMarket, id)} />
        <h4>{tr.excludedCrops}</h4>
        <ChipPicker crops={crops} selected={excluded} onToggle={(id) => toggle(excluded, setExcluded, id)} danger />
      </details>

      <details className="card">
        <summary className="form-summary">{tr.currentRotation}</summary>
        <label className="check">
          <input type="checkbox" checked={!knowsCurrent} onChange={() => setKnowsCurrent(!knowsCurrent)} />
          {tr.dontKnow}
        </label>
        {knowsCurrent &&
          current.map((pair, y) => (
            <div key={y} className="row wrap year-row">
              <strong className="small">
                {tr.year} {y + 1}
              </strong>
              {pair.map((val, i) => (
                <select
                  key={i}
                  value={val}
                  aria-label={`${tr.year} ${y + 1} ${i === 0 ? '' : tr.secondCrop}`}
                  onChange={(e) => {
                    const next = current.map((p) => [...p])
                    next[y][i] = e.target.value
                    setCurrent(next)
                  }}
                >
                  <option value="">{i === 0 ? tr.none : tr.secondCrop}</option>
                  {crops.map((c) => (
                    <option key={c.id} value={c.id}>
                      {nameIn(c.name)}
                    </option>
                  ))}
                </select>
              ))}
            </div>
          ))}
      </details>

      <label className="check small">
        <input type="checkbox" checked={llm} onChange={() => setLlm(!llm)} />
        {tr.llmExplain}
      </label>
      <button type="button" className="btn primary wide" onClick={compare} disabled={result.kind === 'loading'}>
        {result.kind === 'loading' ? tr.comparing : tr.compare}
      </button>
      <p className="muted small">{tr.privacyNote}</p>

      {result.kind === 'error' && <div className="card error">⛔ {result.message}</div>}
      {result.kind === 'done' && <RotationCards data={result.data} nameOf={nameOf} />}
    </section>
  )
}

function ChipPicker({
  crops,
  selected,
  onToggle,
  danger,
}: {
  crops: Analysis['crops']
  selected: string[]
  onToggle: (id: string) => void
  danger?: boolean
}) {
  return (
    <div className="chip-picker">
      {crops.map((c) => (
        <button
          key={c.id}
          type="button"
          aria-pressed={selected.includes(c.id)}
          className={`btn chip small ${selected.includes(c.id) ? (danger ? 'chip-danger' : 'chip-on') : ''}`}
          onClick={() => onToggle(c.id)}
        >
          {nameIn(c.name)}
        </button>
      ))}
    </div>
  )
}
