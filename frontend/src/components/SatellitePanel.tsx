import { useState } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ApiError, fetchSatellite } from '../api'
import { num, t, ts } from '../i18n'
import { layerNames } from '../learn'
import { Info } from './Learn'
import type { PatternResult, PrecipComparison, Satellite, SlopeInfo } from '../types'
import { LANG } from '../lang'

type State = { kind: 'idle' } | { kind: 'loading' } | { kind: 'error'; message: string } | { kind: 'done'; data: Satellite }

function errorText(e: unknown): string {
  if (e instanceof ApiError) {
    const d = e.detail as { source?: string; error?: string } | null
    if (d?.error) return `${ts.error}: ${LANG === 'en' ? 'Earth Engine cannot be reached right now.' : 'Earth Engine’e şu an ulaşılamıyor.'}`
    if (e.status === 0 || e.status >= 500) return t.errors.network
  }
  return ts.error
}

export function SatellitePanel({ lat, lon }: { lat: number; lon: number }) {
  const [state, setState] = useState<State>({ kind: 'idle' })

  const load = () => {
    setState({ kind: 'loading' })
    fetchSatellite(lat, lon)
      .then((data) => setState({ kind: 'done', data }))
      .catch((e) => setState({ kind: 'error', message: errorText(e) }))
  }

  return (
    <section className="card">
      <h2>🛰️ {ts.title}</h2>
      <p className="muted small">{ts.intro}</p>
      {state.kind === 'idle' && (
        <button type="button" className="btn primary wide" onClick={load}>
          {ts.load}
        </button>
      )}
      {state.kind === 'loading' && (
        <div className="loading small">
          <span className="spinner" aria-hidden="true" /> {ts.loading}
        </div>
      )}
      {state.kind === 'error' && (
        <div className="error small">
          ⛔ {state.message}{' '}
          <button type="button" className="btn" onClick={load}>
            ↻
          </button>
        </div>
      )}
      {state.kind === 'done' && <SatelliteBody s={state.data} />}
    </section>
  )
}

function SatelliteBody({ s }: { s: Satellite }) {
  const ee = s.data_sources.find((d) => d.id === 'earth_engine')
  const errors = Object.entries(ee?.errors ?? {})
  const homogeneous = s.precipitation_comparison.difference_series?.homogeneous
  return (
    <>
      {ee && (
        <div className="row wrap small">
          <span className={`badge ${ee.origin === 'earth_engine' ? 'ok' : 'cached'}`}>{ts.origin[ee.origin] ?? ee.origin}</span>
          {Object.entries(ee.layers ?? {}).map(([k, l]) => (
            <span key={k} className="muted" title={`${l.dataset} · ${l.footprint}`}>
              {l.available ? '✓' : '✗'} {layerNames[k] ?? l.dataset}
            </span>
          ))}
        </div>
      )}
      {errors.length > 0 && (
        <ul className="warn small">
          {errors.map(([k, v]) => (
            <li key={k}>
              {k}: {v}
            </li>
          ))}
        </ul>
      )}
      <PrecipBlock p={s.precipitation_comparison} />
      <MonthlyBlock s={s} />
      <SlopeBlock slope={s.slope} />
      <PatternsBlock p={s.patterns} precipInhomogeneous={homogeneous === false} />
    </>
  )
}

function trendLabel(tr: { slope_mm_per_decade: number | null; significant_5pct: boolean }): string {
  if (tr.slope_mm_per_decade === null) return '—'
  const v = tr.slope_mm_per_decade
  return `${v > 0 ? '+' : ''}${num(v)} mm ${t.perDecade}${tr.significant_5pct ? '' : ` (${ts.notSignificant})`}`
}

function PrecipBlock({ p }: { p: PrecipComparison }) {
  if (p.status !== 'ok' || !p.annual_mean_mm || !p.trend || !p.difference_series) return null
  const step = p.difference_series.change_point.step
  const data = (p.annual ?? []).map((a) => ({ year: a.year, power: a.power_mm, imerg: a.imerg_mm }))
  return (
    <>
      <h3>
        {ts.precipTitle} <Info term="rain_sources" />
      </h3>
      <p className="small">{ts.verdict[p.verdict ?? ''] ?? ''}</p>
      <dl className="stats">
        <div>
          <dt>{ts.annualMean} ({p.period?.replace('..', ' – ')})</dt>
          <dd>
            POWER {num(p.annual_mean_mm.power)} mm · IMERG {num(p.annual_mean_mm.imerg)} mm
          </dd>
          {p.power_relative_difference != null && <dd className="muted small">{ts.relDiff(p.power_relative_difference)}</dd>}
        </div>
        <div>
          <dt>{ts.correlation}</dt>
          <dd>{num(p.correlation?.annual, 2)}</dd>
        </div>
        <div>
          <dt>{ts.trend}</dt>
          <dd className="small">POWER {trendLabel(p.trend.power)}</dd>
          <dd className="small">IMERG {trendLabel(p.trend.imerg)}</dd>
        </div>
      </dl>
      {p.power_trend_confirmed_by_imerg === false && (
        <p className="warn small">
          ⚠️{' '}
          {step ? ts.trendNotConfirmed(step.last_year_before, step.ratio_before, step.ratio_after) : ts.trendNotConfirmedNoStep}
        </p>
      )}
      {p.difference_series.homogeneous && <p className="muted small">{ts.homogeneous}</p>}
      <div className="chart">
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: -8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" vertical={false} />
            <XAxis dataKey="year" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} unit=" mm" width={64} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line dataKey="power" name="NASA POWER" stroke="var(--temp)" strokeWidth={2} dot={false} />
            <Line dataKey="imerg" name="GPM IMERG" stroke="var(--rain)" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="muted small">{ts.footprintNote}</p>
    </>
  )
}

function MonthlyBlock({ s }: { s: Satellite }) {
  const data = s.monthly_climatology.map((m) => ({
    name: t.months[Number(m.month) - 1],
    label: t.monthNames[Number(m.month) - 1],
    ndvi: m.ndvi,
    smap: m.smap_sm,
    gwet: m.power_gwetroot_model,
  }))
  const merge = s.soil_moisture.merge
  return (
    <>
      <h3>
        {ts.monthlyTitle} <Info term="ndvi" /> <Info term="smap" /> <Info term="soil_model" />
      </h3>
      <div className="chart">
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: -12 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} />
            <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} />
            <Tooltip labelFormatter={(_, p) => p?.[0]?.payload?.label ?? ''} formatter={(v) => num(v, 3)} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line dataKey="ndvi" name={ts.ndvi} stroke="var(--brand)" strokeWidth={2} dot={false} />
            <Line dataKey="smap" name={ts.smap} stroke="var(--rain)" strokeWidth={2} dot={false} />
            <Line dataKey="gwet" name={ts.gwet} stroke="var(--muted)" strokeDasharray="5 4" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {merge && <p className="muted small">{ts.smapMerge(merge)}</p>}
      <p className="muted small">{ts.smapVsModel}</p>
    </>
  )
}

function SlopeBlock({ slope }: { slope: SlopeInfo }) {
  return (
    <>
      <h3>{ts.slopeTitle}</h3>
      <p className="small">
        {slope.status === 'ok' && slope.slope_pct_median != null && slope.relative_s != null
          ? ts.slopeText(slope.slope_pct_median, slope.relative_s)
          : ts.slopeMissing}
        {slope.flat_terrain ? ` ${ts.slopeFlat}` : ''}
      </p>
    </>
  )
}

function Years({ ys }: { ys: number[] | undefined }) {
  return <>{ys && ys.length ? ys.join(', ') : ts.none}</>
}

function PatternsBlock({ p, precipInhomogeneous }: { p: PatternResult; precipInhomogeneous: boolean }) {
  if (p.status !== 'ok') return null
  const km = p.kmeans
  const an = p.analogs
  const ctx = new Map((p.flagged_year_context ?? []).map((c) => [c.year, c]))
  return (
    <>
      <h3>{ts.patternsTitle}</h3>
      <p className="muted small">{ts.patternsIntro(p.n_years ?? 0)}</p>

      <h4>{ts.methodZ}</h4>
      <p className="small">
        {ts.methodZText(p.zscore?.threshold ?? 1.5)} <strong><Years ys={p.zscore?.anomalous_years} /></strong>
      </p>

      <h4>{ts.methodIF}</h4>
      <p className="small">
        {ts.methodIFText} <strong><Years ys={p.isolation_forest?.anomalous_years} /></strong>
      </p>

      {p.agreement && (
        <>
          <h4>{ts.agreement}</h4>
          <ul className="small">
            {(
              [
                [ts.both, p.agreement.both],
                [ts.onlyZ, p.agreement.only_zscore],
                [ts.onlyIF, p.agreement.only_isolation_forest],
              ] as [string, number[]][]
            ).map(([label, ys]) => (
              <li key={label}>
                {label}:{' '}
                {ys.length === 0
                  ? ts.none
                  : ys.map((y, i) => {
                      const c = ctx.get(y)
                      return (
                        <span key={y} title={c ? ts.yearCtx(c.z_ndvi_integral, c.z_precip, c.z_tmean) : undefined}>
                          {i > 0 && ', '}
                          {y}
                          {c && <span className="muted"> ({ts.yearCtx(c.z_ndvi_integral, c.z_precip, c.z_tmean)})</span>}
                        </span>
                      )
                    })}
              </li>
            ))}
          </ul>
        </>
      )}

      {km && (
        <>
          <h4>{ts.methodKM}</h4>
          <p className="small">
            {ts.kmStatus[km.status] ?? km.status}
            {km.silhouette != null && ` (k = ${km.k}, siluet ${num(km.silhouette, 2)})`}
          </p>
          <ul className="small">
            {(km.clusters ?? []).map((c) => (
              <li key={c.cluster}>
                {ts.cluster(c.years.length, c.peak_month, c.n_peaks)}: <span className="muted">{c.years.join(', ')}</span>
              </li>
            ))}
          </ul>
          {km.regime_shift && <p className="warn small">⚠️ {ts.regimeShift(km.regime_shift.last_year_before)}</p>}
        </>
      )}

      {an?.status === 'ok' && an.target_year != null && (
        <>
          <h4>{ts.methodAN}</h4>
          <p className="small">{ts.analogText(an.target_year, (an.target_analogs ?? []).map((a) => a.year).join(', '))}</p>
          {an.loo?.skill != null && <p className="small">{ts.analogSkill(an.loo.skill)}</p>}
        </>
      )}
      {precipInhomogeneous && <p className="warn small">{ts.precipNotHomogeneous}</p>}
    </>
  )
}
