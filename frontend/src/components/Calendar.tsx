import type { ReactNode } from 'react'
import { t } from '../i18n'
import type { CropResult, MonthClimate } from '../types'
import { nameIn } from '../lang'

const MAX_CROPS = 6
const MIN_SCORE = 0.2 // crops scoring lower everywhere would only clutter the calendar

export function CalendarStrip({ months, crops }: { months: MonthClimate[]; crops: CropResult[] }) {
  const maxHot = Math.max(1, ...months.map((m) => m.hot_days))
  const maxBalance = Math.max(1, ...months.map((m) => Math.abs(m.water_balance_mm)))
  const top = crops
    .filter((c) => c.status === 'evaluated' && c.best_window && c.best_window.score_median >= MIN_SCORE)
    .slice(0, MAX_CROPS)

  return (
    <section className="card">
      <h2>{t.calendarTitle}</h2>
      <div className="calendar" role="table">
        <div className="cal-row head" role="row">
          <span className="cal-label" />
          {t.months.map((m, i) => (
            <span key={i} className="cal-cell head" role="columnheader">
              {m}
            </span>
          ))}
        </div>
        <Row label={t.calendarRows.frost}>
          {months.map((m) => (
            <span
              key={m.month}
              className="cal-cell"
              style={{ background: `rgba(70, 130, 220, ${m.frost_probability * 0.85})` }}
              title={`${Math.round(m.frost_probability * 100)}%`}
            />
          ))}
        </Row>
        <Row label={t.calendarRows.water}>
          {months.map((m) => {
            const a = Math.min(1, Math.abs(m.water_balance_mm) / maxBalance) * 0.85
            const color = m.water_balance_mm >= 0 ? `rgba(40, 150, 110, ${a})` : `rgba(220, 120, 40, ${a})`
            return <span key={m.month} className="cal-cell" style={{ background: color }} title={`${m.water_balance_mm} mm`} />
          })}
        </Row>
        <Row label={t.calendarRows.hot}>
          {months.map((m) => (
            <span
              key={m.month}
              className="cal-cell"
              style={{ background: `rgba(210, 60, 50, ${(m.hot_days / maxHot) * 0.85})` }}
              title={`${m.hot_days}`}
            />
          ))}
        </Row>
        {top.map((c) => {
          const season = new Set(c.best_window!.season_months)
          const good = new Set((c.good_sowing_dates ?? []).map((d) => Number(d.slice(0, 2))))
          return (
            <Row key={c.id} label={nameIn(c.name)} crop>
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <span key={m} className={`cal-cell ${season.has(m) ? 'season' : ''}`}>
                  {good.has(m) ? '●' : ''}
                </span>
              ))}
            </Row>
          )
        })}
      </div>
      {top.length === 0 && <p className="muted small">{t.calendarNoCrops}</p>}
      <p className="muted small">{t.calendarLegend}</p>
    </section>
  )
}

function Row({ label, children, crop }: { label: string; children: ReactNode; crop?: boolean }) {
  return (
    <div className={`cal-row ${crop ? 'crop' : ''}`} role="row">
      <span className="cal-label" role="rowheader">
        {label}
      </span>
      {children}
    </div>
  )
}
