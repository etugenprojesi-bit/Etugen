import { useEffect, useMemo, useState } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ApiError, fetchRisk } from '../api'
import { num, t, tk, ts } from '../i18n'
import { riskSourceText, riskWords } from '../learn'
import type { RiskLayer, RiskResponse, Variant } from '../types'
import { Info } from './Learn'
import { LANG, nameIn } from '../lang'

const LAYER_TERM: Record<string, string> = {
  frost_days: 'frost',
  lethal_cold_days: 'lethal_cold',
  hot_days: 'hot',
  heavy_rain_days: 'heavy_rain',
  water_balance_mm: 'water_balance',
  smap_sm: 'smap',
  ndvi: 'ndvi',
}

type State = { kind: 'idle' } | { kind: 'loading'; prev?: RiskResponse } | { kind: 'error'; message: string } | { kind: 'done'; data: RiskResponse }

const COLOR_A = '#7b3fa0'
const COLOR_B = '#d07d10'

function errorText(e: unknown): string {
  if (e instanceof ApiError) {
    const d = e.detail as { error?: string } | string | null
    // Earth Engine / data-source failure: say so in Turkish, without the technical English message.
    if (d && typeof d === 'object' && d.error) return `${tk.riskError}: ${LANG === 'en' ? 'satellite data are not available right now.' : 'uydu verisi şu an alınamıyor.'}`
    if (e.status === 0 || e.status >= 500) return t.errors.network
  }
  return tk.riskError
}

// Diverging colour for an oriented anomaly: red = worse than normal, blue = better.
function zColor(z: number | null): string {
  if (z === null) return 'transparent'
  const a = Math.min(Math.abs(z) / 2.5, 1) * 0.85
  return z > 0 ? `rgba(192, 57, 43, ${a.toFixed(2)})` : `rgba(47, 110, 186, ${a.toFixed(2)})`
}

function fmt(l: RiskLayer, v: number | null): string {
  if (v === null) return '—'
  const d = l.unit === 'm³/m³' || l.unit === 'NDVI' ? 3 : 0
  return num(v, d)
}

function unitOf(l: RiskLayer): string {
  return tk.units[l.unit] ?? l.unit
}

export function RiskPanel({ lat, lon, variant }: { lat: number; lon: number; variant: Variant }) {
  const [state, setState] = useState<State>({ kind: 'idle' })
  const [started, setStarted] = useState(false)
  const [crop, setCrop] = useState('')

  useEffect(() => {
    if (!started) return
    const ctrl = new AbortController()
    setState((s) => ({ kind: 'loading', prev: s.kind === 'done' ? s.data : s.kind === 'loading' ? s.prev : undefined }))
    fetchRisk(lat, lon, crop, variant, ctrl.signal)
      .then((data) => setState({ kind: 'done', data }))
      .catch((e) => {
        if ((e as Error).name !== 'AbortError') setState({ kind: 'error', message: errorText(e) })
      })
    return () => ctrl.abort()
  }, [started, lat, lon, crop, variant])

  const data = state.kind === 'done' ? state.data : state.kind === 'loading' ? state.prev : undefined

  return (
    <section className="card">
      <h2>⚠️ {tk.riskTitle}</h2>
      <p className="muted small">{tk.riskIntro}</p>
      {!started && (
        <button type="button" className="btn primary wide" onClick={() => setStarted(true)}>
          {tk.riskLoad}
        </button>
      )}
      {state.kind === 'loading' && (
        <div className="loading small">
          <span className="spinner" aria-hidden="true" /> {tk.riskLoading}
        </div>
      )}
      {state.kind === 'error' && (
        <div className="error small">
          ⛔ {state.message}{' '}
          <button type="button" className="btn" onClick={() => { setStarted(false); setTimeout(() => setStarted(true)) }}>
            ↻
          </button>
        </div>
      )}
      {data && <RiskBody r={data} crop={crop} onCrop={setCrop} />}
    </section>
  )
}

function RiskBody({ r, crop, onCrop }: { r: RiskResponse; crop: string; onCrop: (id: string) => void }) {
  const years = r.years
  const [yi, setYi] = useState(years.length - 1)
  const [cell, setCell] = useState<{ layer: string; month: number } | null>(null)
  const ids = r.layers.map((l) => l.id)
  const [a, setA] = useState(ids.includes('water_balance_mm') ? 'water_balance_mm' : ids[0])
  const [b, setB] = useState(ids.includes('ndvi') ? 'ndvi' : ids[1] ?? ids[0])
  const year = years[Math.min(yi, years.length - 1)]
  const sat = r.data_sources.find((d) => d.id === 'earth_engine')

  return (
    <>
      {sat && (
        <div className="row wrap small">
          <span className={`badge ${sat.origin === 'earth_engine' ? 'ok' : 'cached'}`}>{ts.origin[sat.origin] ?? sat.origin}</span>
        </div>
      )}
      {r.missing_layers.length > 0 && <p className="warn small">{tk.missingLayer(r.missing_layers.map((m) => tk.layers[m] ?? m).join(', '))}</p>}

      <label className="field small">
        <span>{tk.cropFor}</span>
        <select value={crop} onChange={(e) => onCrop(e.target.value)}>
          <option value="">{tk.generic}</option>
          {r.crop_options.map((c) => (
            <option key={c.id} value={c.id}>
              {nameIn(c.name)}
            </option>
          ))}
        </select>
      </label>

      <div className="year-slider">
        <button type="button" className="btn small" aria-label={LANG === 'en' ? 'previous year' : 'önceki yıl'} disabled={yi <= 0} onClick={() => setYi(yi - 1)}>
          ◀
        </button>
        <input
          type="range"
          min={0}
          max={years.length - 1}
          value={yi}
          aria-label={tk.year}
          onChange={(e) => setYi(Number(e.target.value))}
        />
        <button type="button" className="btn small" aria-label={LANG === 'en' ? 'next year' : 'sonraki yıl'} disabled={yi >= years.length - 1} onClick={() => setYi(yi + 1)}>
          ▶
        </button>
        <strong className="year-label">{year}</strong>
      </div>

      <RiskGrid r={r} yi={yi} cell={cell} onCell={setCell} />
      <CellDetail r={r} yi={yi} cell={cell} />

      <div className="legend-row small muted">
        <span className="swatch" style={{ background: zColor(2) }} /> {tk.legendWorse}
        <span className="swatch" style={{ background: zColor(-2) }} /> {tk.legendBetter} <Info term="risk_colour" />
      </div>

      <ul className="plain small thresholds">
        {r.layers.map((l) => (
          <li key={l.id}>
            <strong>{tk.layers[l.id] ?? l.label}</strong> <Info term={LAYER_TERM[l.id] ?? ''} />{' '}
            <span className="muted">{riskSourceText(l.id, l.threshold?.value ?? null, l.assumption, (r.crop ? nameIn(r.crop.name) : null))}</span>
          </li>
        ))}
      </ul>
      {r.notes.filter((n) => n !== 'generic_heat_threshold').map((n) => (
        <p key={n} className="warn small">
          {tk.notes[n] ?? n}
        </p>
      ))}

      <h3>{tk.compareTitle}</h3>
      <p className="muted small">{tk.compareIntro}</p>
      <div className="row wrap">
        <LayerSelect label={tk.layerA} color={COLOR_A} value={a} onChange={setA} layers={r.layers} />
        <LayerSelect label={tk.layerB} color={COLOR_B} value={b} onChange={setB} layers={r.layers} />
      </div>
      <CompareCharts r={r} yi={yi} a={a} b={b} />
    </>
  )
}

function LayerSelect(p: { label: string; color: string; value: string; onChange: (v: string) => void; layers: RiskLayer[] }) {
  return (
    <label className="field small">
      <span style={{ color: p.color, fontWeight: 600 }}>{p.label}</span>
      <select value={p.value} onChange={(e) => p.onChange(e.target.value)}>
        {p.layers.map((l) => (
          <option key={l.id} value={l.id}>
            {tk.layers[l.id] ?? l.label}
          </option>
        ))}
      </select>
    </label>
  )
}

function RiskGrid({ r, yi, cell, onCell }: { r: RiskResponse; yi: number; cell: { layer: string; month: number } | null; onCell: (c: { layer: string; month: number } | null) => void }) {
  return (
    <div className="risk-grid" role="table">
      <div className="risk-row head" role="row">
        <span />
        {t.monthNames.map((m) => (
          <span key={m} className="risk-cell head">
            {m.slice(0, 1)}
          </span>
        ))}
        <span className="risk-cell head">{tk.annualCol}</span>
      </div>
      {r.layers.map((l) => {
        const vals = l.values[yi]
        const zs = l.risk_z[yi]
        return (
          <div key={l.id} className="risk-row" role="row">
            <span className="risk-label" title={l.label}>
              {tk.layers[l.id] ?? l.label}
            </span>
            {vals.map((v, m) => {
              const on = cell?.layer === l.id && cell.month === m
              return (
                <button
                  key={m}
                  type="button"
                  className={`risk-cell${v === null ? ' empty' : ''}${on ? ' on' : ''}`}
                  style={{ background: zColor(zs[m]) }}
                  onClick={() => onCell(on ? null : { layer: l.id, month: m })}
                  aria-label={`${tk.layers[l.id] ?? l.label}, ${t.monthNames[m]}: ${fmt(l, v)}`}
                >
                  {l.kind === 'count' && v !== null ? fmt(l, v) : ''}
                </button>
              )
            })}
            <span className="risk-cell annual" style={{ background: zColor(l.annual_risk_z[yi]) }} title={`${tk.normal}: ${fmt(l, l.annual_baseline_mean)}`}>
              {fmt(l, l.annual[yi])}
            </span>
          </div>
        )
      })}
    </div>
  )
}

function CellDetail({ r, yi, cell }: { r: RiskResponse; yi: number; cell: { layer: string; month: number } | null }) {
  if (!cell) return null
  const l = r.layers.find((x) => x.id === cell.layer)
  if (!l) return null
  const v = l.values[yi][cell.month]
  const z = l.risk_z[yi][cell.month]
  const u = unitOf(l)
  return (
    <p className="cell-detail small">
      <strong>
        {t.monthNames[cell.month]} {r.years[yi]} · {tk.layers[l.id] ?? l.label}
      </strong>
      : {v === null ? tk.noData : `${fmt(l, v)} ${u}`} · {tk.normal} {fmt(l, l.climatology[cell.month])} {u}
      {` · ${riskWords(z)}`}
    </p>
  )
}

function CompareCharts({ r, yi, a, b }: { r: RiskResponse; yi: number; a: string; b: string }) {
  const la = r.layers.find((l) => l.id === a)
  const lb = r.layers.find((l) => l.id === b)
  const nameA = la ? tk.layers[la.id] ?? la.label : ''
  const nameB = lb ? tk.layers[lb.id] ?? lb.label : ''
  const monthly = useMemo(
    () => t.monthNames.map((m, i) => ({ m: m.slice(0, 3), A: la?.risk_z[yi][i] ?? null, B: lb?.risk_z[yi][i] ?? null })),
    [la, lb, yi],
  )
  const annual = useMemo(
    () => r.years.map((y, i) => ({ y, A: la?.annual_risk_z[i] ?? null, B: lb?.annual_risk_z[i] ?? null })),
    [r.years, la, lb],
  )
  const dom: [number, number] = [-r.z_cap, r.z_cap]
  return (
    <div className="compare">
      <figure>
        <figcaption className="small">{tk.chartYear(r.years[yi])}</figcaption>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={monthly} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid stroke="var(--grid)" />
            <XAxis dataKey="m" fontSize={10} interval={1} />
            <YAxis domain={dom} fontSize={10} ticks={[-3, -2, -1, 0, 1, 2, 3]} />
            <ReferenceLine y={0} stroke="var(--muted)" />
            <Tooltip formatter={(v) => (v === null || v === undefined ? tk.noData : num(v, 2))} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Line dataKey="A" name={nameA} stroke={COLOR_A} strokeWidth={2} dot={{ r: 2 }} connectNulls={false} isAnimationActive={false} />
            <Line dataKey="B" name={nameB} stroke={COLOR_B} strokeWidth={2} dot={{ r: 2 }} connectNulls={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </figure>
      <figure>
        <figcaption className="small">{tk.chartAll}</figcaption>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={annual} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid stroke="var(--grid)" />
            <XAxis dataKey="y" fontSize={10} />
            <YAxis domain={dom} fontSize={10} ticks={[-3, -2, -1, 0, 1, 2, 3]} />
            <ReferenceLine y={0} stroke="var(--muted)" />
            <ReferenceLine x={r.years[yi]} stroke="var(--text)" strokeDasharray="3 3" />
            <Tooltip formatter={(v) => (v === null || v === undefined ? tk.noData : num(v, 2))} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Line dataKey="A" name={nameA} stroke={COLOR_A} strokeWidth={2} dot={{ r: 2 }} isAnimationActive={false} />
            <Line dataKey="B" name={nameB} stroke={COLOR_B} strokeWidth={2} dot={{ r: 2 }} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </figure>
    </div>
  )
}
