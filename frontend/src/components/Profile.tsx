import type { ReactNode } from 'react'
import { num, t, tk } from '../i18n'
import { powerResolution, powerSource } from '../learn'
import { Info } from './Learn'
import type { Analysis } from '../types'
import { LANG } from '../lang'

export function DataBanner({ a }: { a: Analysis }) {
  const src = a.data_sources[0]
  return (
    <section className="card banner">
      <p className="disclaimer">⚠️ {t.disclaimer}</p>
      <div className="row wrap small">
        <span className={`badge ${src.origin === 'network' ? 'ok' : 'cached'}`}>{t.dataOrigin[src.origin]}</span>
        <span className="muted">
          {t.source}: {powerSource} ({src.period.replace('..', ' – ')}, {powerResolution})
        </span>
      </div>
      {a.variant.scenario_active && (
        <p className="small">
          <span className="badge warn">{tk.bannerScenario(a.variant.delta_t_c, a.variant.delta_p_pct)}</span>
        </p>
      )}
      {a.variant.imerg_rescale && (
        <p className="small">
          <span className="badge ok">{tk.bannerImerg(a.variant.imerg_rescale.annual_mean_mm.used, a.variant.imerg_rescale.annual_mean_mm.power)}</span>{' '}
          {a.variant.imerg_rescale.months_without_imerg > 0 && (
            <span className="muted">{tk.imergGaps(a.variant.imerg_rescale.months_without_imerg, a.variant.imerg_rescale.months_without_imerg_range)}</span>
          )}
        </p>
      )}
      {a.variant.chirps_rescale && (
        <p className="small">
          <span className="badge ok">{tk.bannerChirps(a.variant.chirps_rescale.annual_mean_mm.used, a.variant.chirps_rescale.annual_mean_mm.power)}</span>
        </p>
      )}
      {a.query.precip_source === 'power' && a.climate.rain_check?.power_may_be_too_wet && (
        <p className="small">
          <span className="badge warn">⚠️ {tk.rainTooWet(a.climate.rain_check.power_mm ?? 0, a.climate.rain_check.chirps_mm ?? 0)}</span>
        </p>
      )}
      <p className="muted small">
        {t.analysisPoint}: {num(a.analysis_point.lat, 2)}°, {num(a.analysis_point.lon, 2)}° · {t.elevation}{' '}
        {num(a.analysis_point.elevation_m)} m · {t.roundedNote}
        {src.missing_days > 0 && ` · ${src.missing_days} ${LANG === 'en' ? 'missing days' : 'eksik gün'}`}
      </p>
    </section>
  )
}

// Short version for the summary: disclaimer, data origin and active options stay visible.
export function DataStrip({ a }: { a: Analysis }) {
  const src = a.data_sources[0]
  return (
    <div className="data-strip">
      <p className="disclaimer">⚠️ {t.disclaimer}</p>
      <div className="row wrap small">
        <span className={`badge ${src.origin === 'network' ? 'ok' : 'cached'}`}>{t.dataOrigin[src.origin]}</span>
        {a.variant.scenario_active && <span className="badge warn">{tk.bannerScenario(a.variant.delta_t_c, a.variant.delta_p_pct)}</span>}
        {a.variant.imerg_rescale && <span className="badge ok">{tk.precipOptions.imerg}</span>}
        {a.variant.chirps_rescale && <span className="badge ok">{tk.precipOptions.chirps}</span>}
        {a.query.precip_source === 'power' && a.climate.rain_check?.power_may_be_too_wet && (
          <span className="badge warn">⚠️ {tk.rainTooWetShort}</span>
        )}
      </div>
    </div>
  )
}

export function ProfileCard({ a }: { a: Analysis }) {
  const y = a.climate.annual
  const trends = Object.entries(a.climate.trends).filter(([, tr]) => tr.significant_5pct && tr.slope_per_decade !== null)
  return (
    <section className="card">
      <h2>{t.profileTitle}</h2>
      <dl className="stats">
        <Stat label={t.annual.tmean} value={`${num(y.tmean_c, 1)} °C`} />
        <Stat label={t.annual.precip} value={`${num(y.precip_mm)} mm`} />
        <Stat label={<>{t.annual.et0} <Info term="et0" /></>} value={`${num(y.et0_mm)} mm`} />
        <Stat
          label={<>{t.annual.aridity} <Info term="aridity" /></>}
          value={`${num(y.aridity_index_p_over_et0, 2)}`}
          sub={t.aridityClass(y.aridity_index_p_over_et0)}
        />
        <Stat label={<>{t.annual.frost} <Info term="frost" /></>} value={num(y.frost_days)} />
        <Stat label={<>{t.annual.hot} <Info term="hot" /></>} value={num(y.hot_days)} />
      </dl>
      <h3>{t.trendsTitle}</h3>
      {trends.length === 0 ? (
        <p className="muted small">{t.noSignificantTrend}</p>
      ) : (
        <ul className="chips">
          {trends.map(([k, tr]) => {
            const s = tr.slope_per_decade as number
            return (
              <li key={k} className={`chip-static ${s > 0 ? 'up' : 'down'}`}>
                {t.trendNames[k] ?? k} {s > 0 ? '▲' : '▼'} {s > 0 ? '+' : ''}
                {num(s, Math.abs(s) < 1 ? 2 : 0)} {t.units[tr.unit] ?? tr.unit} {t.perDecade}
              </li>
            )
          })}
        </ul>
      )}
      <p className="muted small">{t.trendNote}</p>
    </section>
  )
}

function Stat({ label, value, sub }: { label: ReactNode; value: string; sub?: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>
        {value}
        {sub && <span className="muted small"> {sub}</span>}
      </dd>
    </div>
  )
}
