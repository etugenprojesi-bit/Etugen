import { useEffect, useMemo, useState } from 'react'
import { ApiError, fetchRotations } from '../api'
import { areaDecare, compass, rowAxis, toLocal } from '../field'
import { dateLabel, rotationText, t, te, tf } from '../i18n'
import type { Corner } from './MapView'
import type { Analysis, PriorityKey, RotationCard, RotationResponse, RotationSlot } from '../types'
import { LANG, nameIn } from '../lang'

// Kolay mod (docs/drafts/plan_kolay_mod.md): the rotation is computed automatically with
// default priorities and written as a plan. Only model numbers are shown; nothing is invented.
const DEFAULT_PRIORITIES: Record<PriorityKey, number> = { water: 3, soil: 3, erosion: 3, nitrogen: 3, income: 3, forage: 3 }
const ENOUGH_RAIN_MM = 10 // display rule: deficits below this are shown as "rain is enough"
const MIN_IDLE_MONTHS = 2 // same as the cover-crop gap rule of the rotation cards

type Result = { kind: 'loading' } | { kind: 'error'; message: string } | { kind: 'done'; data: RotationResponse }

export function EasyPlan({ a, corners, onExpert }: { a: Analysis; corners: Corner[]; onExpert: () => void }) {
  const area = areaDecare(corners)
  const [result, setResult] = useState<Result>({ kind: 'loading' })
  const [choice, setChoice] = useState(0)

  useEffect(() => {
    const ctrl = new AbortController()
    setResult({ kind: 'loading' })
    setChoice(0)
    fetchRotations(
      {
        lat: a.query.lat,
        lon: a.query.lon,
        irrigation: a.query.irrigation,
        precip_source: a.query.precip_source,
        delta_t: a.query.delta_t,
        delta_p: a.query.delta_p,
        explore_sowing: a.query.explore_sowing,
        priorities: DEFAULT_PRIORITIES,
        constraints: { excluded_crops: [], equipment_limits: [], market_crops: [] },
        current_rotation: null,
        explain: 'template',
        lang: LANG,
      },
      ctrl.signal,
    )
      .then((data) => setResult({ kind: 'done', data }))
      .catch((e) => {
        if ((e as Error).name === 'AbortError') return
        const status = e instanceof ApiError ? e.status : -1
        setResult({ kind: 'error', message: status === 0 || status >= 500 ? t.errors.network : t.errors.other })
      })
    return () => ctrl.abort()
  }, [a])

  const plans = useMemo(
    () => (result.kind === 'done' ? result.data.cards.filter((c) => c.kind === 'recommended') : []),
    [result],
  )

  if (result.kind === 'loading')
    return (
      <div className="card loading">
        <span className="spinner" aria-hidden="true" /> {te.computing}
      </div>
    )
  if (result.kind === 'error') return <div className="card error">⛔ {result.message}</div>

  const plan = plans[choice]
  return (
    <section className="easy-plan">
      <h2 className="section-title">🗓️ {te.planTitle}</h2>
      {!plan ? (
        <div className="card">{te.noPlan}</div>
      ) : (
        <>
          <p className="muted small lead">{te.planIntro(plan.years.length)}</p>
          {plans.length > 1 && (
            <div className="row wrap plan-switch">
              <span className="small muted">{te.option(choice + 1, plans.length)}</span>
              <button type="button" className="btn small" onClick={() => setChoice((choice + 1) % plans.length)}>
                🔁 {te.otherOption}
              </button>
            </div>
          )}
          <Plan c={plan} irrigation={a.query.irrigation} area={area} />
          <Rows slope={result.data.slope} corners={corners} />
          {result.data.erosion_ignored_flat_terrain && <p className="small">⛰️ {te.flat}</p>}
        </>
      )}
      <p className="disclaimer card">⚠️ {te.lowConfidence}</p>
      <button type="button" className="btn wide" onClick={onExpert}>
        🔬 {te.moreDetails}
      </button>
    </section>
  )
}

function Plan({ c, irrigation, area }: { c: RotationCard; irrigation: Analysis['query']['irrigation']; area: number }) {
  const idle = c.fallow_periods.filter((g) => g.months >= MIN_IDLE_MONTHS && g.months < 12 * c.years.length)
  const why = [...c.benefits, ...c.why.filter((w) => w.code.startsWith('strong_'))].slice(0, 3)
  const names = new Map(c.years.flat().map((s) => [s.crop_id, nameIn(s.name)]))
  const nameOf = (id: string) => names.get(id) ?? id
  return (
    <>
      <ol className="plan-years">
        {c.years.map((y, i) => (
          <li key={i} className="card plan-year">
            <h3>{te.year(i + 1)}</h3>
            {y.length === 0 ? (
              <p>🟫 {te.fallowYear}</p>
            ) : (
              y.map((s) => <PlanCrop key={s.crop_id + s.sowing} s={s} irrigation={irrigation} area={area} />)
            )}
          </li>
        ))}
      </ol>

      {idle.length > 0 && (
        <div className="card">
          <h3>🐑 {te.idleTitle}</h3>
          <ul className="plain-list small">
            {idle.map((g, k) => (
              <li key={k}>
                {te.year(g.year)}: {te.idle(te.monthNames[g.start_month - 1], g.months)}
              </li>
            ))}
          </ul>
          <p className="small">{te.idleAdvice}</p>
        </div>
      )}

      {why.length > 0 && (
        <details className="card small">
          <summary>{te.why}</summary>
          <ul className="plain-list">
            {why.map((w, k) => (
              <li key={k}>{rotationText(w, nameOf)}</li>
            ))}
          </ul>
          <p className="muted">{te.scoreLine(Math.round(c.total * 100))}</p>
        </details>
      )}
    </>
  )
}

function PlanCrop({ s, irrigation, area }: { s: RotationSlot; irrigation: Analysis['query']['irrigation']; area: number }) {
  const mm = Math.round(s.rain_deficit_mm)
  const stored = s.stored_soil_water?.stored_mm_median ?? 0
  const sc = s.irrigation_schedule
  return (
    <div className="plan-crop">
      <strong className="plan-crop-name">🌱 {nameIn(s.name)}</strong>
      <ul className="plain-list small">
        <li>📅 {te.sow(dateLabel(s.sowing))}</li>
        <li>🌾 {te.harvest(dateLabel(s.harvest))}</li>
        <li>🚜 {te.prepare}</li>
        <li>
          💧{' '}
          {mm < ENOUGH_RAIN_MM ? te.waterOkRain : irrigation === 'none' ? te.waterNeedNone(mm) : te.waterNeedIrr(mm)}
        </li>
        {mm >= ENOUGH_RAIN_MM && area > 0 && <li>🧮 {tf.seasonWholeField(mm * area)}</li>}
        {sc && mm >= ENOUGH_RAIN_MM && (
          <li>
            🚿 {irrigationText(sc, irrigation)}
            {area > 0 && ` ${tf.wholeField(sc.depth_mm * area)}`}
            {sc.rain_mm_per_day >= sc.etc_mm_per_day && ` ${tf.irrigationRainy}`}
          </li>
        )}
        {stored >= ENOUGH_RAIN_MM && <li>🪣 {te.stored(Math.round(stored))}</li>}
        {s.group === 'forage' && <li>🐄 {te.forage}</li>}
        {s.nitrogen_fixing && <li>🫘 {te.legume}</li>}
      </ul>
    </div>
  )
}

function Rows({ slope, corners }: { slope: RotationResponse['slope']; corners: Corner[] }) {
  const fall = slope?.fall ?? null
  const text = fall
    ? tf.rowsContour(rowAxis(fall.contour_rows_azimuth_deg), compass(fall.downhill_azimuth_deg))
    : slope?.flat_terrain
      ? tf.rowsFlat
      : tf.rowsUnknown
  return (
    <div className="card">
      <h3>🧭 {tf.rowsTitle}</h3>
      {(fall || corners.length >= 3) && <Sketch corners={corners} rowsAz={fall?.contour_rows_azimuth_deg} downAz={fall?.downhill_azimuth_deg} />}
      <p className="small">{text}</p>
      {fall && <p className="muted small">{tf.rowsNote}</p>}
    </div>
  )
}

/** Field outline (north up) with row lines across the slope and a downhill arrow. */
function Sketch({ corners, rowsAz, downAz }: { corners: Corner[]; rowsAz?: number; downAz?: number }) {
  const S = 220
  const pts = corners.length >= 3 ? toLocal(corners) : null
  const ext = pts ? Math.max(...pts.map((p) => Math.max(Math.abs(p.x), Math.abs(p.y)))) || 1 : 1
  const k = (S / 2 - 20) / ext
  const poly = pts
    ? pts.map((p) => `${S / 2 + p.x * k},${S / 2 - p.y * k}`).join(' ')
    : `${S / 2 - 70},${S / 2 - 60} ${S / 2 + 70},${S / 2 - 60} ${S / 2 + 70},${S / 2 + 60} ${S / 2 - 70},${S / 2 + 60}`
  const lines: string[] = []
  if (rowsAz !== undefined) {
    const r = (rowsAz * Math.PI) / 180
    const ux = Math.sin(r), uy = -Math.cos(r) // row direction on screen
    const nx = -uy, ny = ux // spacing direction
    for (let i = -10; i <= 10; i++) {
      const cx = S / 2 + nx * i * 12, cy = S / 2 + ny * i * 12
      lines.push(`M${cx - ux * S},${cy - uy * S} L${cx + ux * S},${cy + uy * S}`)
    }
  }
  const d = downAz !== undefined ? (downAz * Math.PI) / 180 : null
  return (
    <svg className="field-sketch" viewBox={`0 0 ${S} ${S}`} role="img" aria-label={tf.sketchTitle}>
      <defs>
        <clipPath id="field-clip">
          <polygon points={poly} />
        </clipPath>
        <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#4f8fd6" />
        </marker>
      </defs>
      <polygon points={poly} fill="#e2efe3" stroke="#22603a" strokeWidth="2" strokeDasharray={pts ? undefined : '6 4'} />
      <g clipPath="url(#field-clip)">
        {lines.map((l, i) => (
          <path key={i} d={l} stroke="#7a5a2b" strokeWidth="2" />
        ))}
      </g>
      {d !== null && (
        <line x1={S / 2 - Math.sin(d) * 40} y1={S / 2 + Math.cos(d) * 40} x2={S / 2 + Math.sin(d) * 40} y2={S / 2 - Math.cos(d) * 40}
          stroke="#4f8fd6" strokeWidth="4" markerEnd="url(#arrow)" />
      )}
      <text x={S - 16} y={18} fontSize="14" fontWeight="700" fill="#1d2a20">{tf.sketchNorth}</text>
      <path d={`M${S - 12},${24} L${S - 12},${44}`} stroke="#1d2a20" strokeWidth="2" />
    </svg>
  )
}

function irrigationText(sc: NonNullable<RotationSlot['irrigation_schedule']>, irrigation: Analysis['query']['irrigation']) {
  const lead = irrigation === 'none' ? tf.irrigationLeadIfPossible : tf.irrigationLead
  const from = dateLabel(sc.mid_season_start)
  const to = dateLabel(sc.mid_season_end)
  return sc.interval_days >= sc.mid_season_days
    ? tf.irrigationOnce(lead, from, to, sc.depth_mm)
    : tf.irrigation(lead, from, to, sc.interval_days, sc.depth_mm)
}
