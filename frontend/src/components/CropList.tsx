import { dateLabel, num, pct, questionText, reasonText, t, tk } from '../i18n'
import { evidenceText } from '../learn'
import type { CropResult } from '../types'
import { Info } from './Learn'
import { nameIn } from '../lang'

export function CropList({ crops }: { crops: CropResult[] }) {
  const evaluated = crops.filter((c) => c.status === 'evaluated')
  const unsuitable = crops.filter((c) => c.status === 'not_suitable_by_model')
  const insufficient = crops.filter((c) => c.status === 'insufficient_data')
  const perennial = crops.filter((c) => c.status === 'perennial_not_evaluated')

  return (
    <section>
      <h2 className="section-title">{t.cropsTitle}</h2>
      <p className="muted small">
        {t.cropsIntro} <Info term="score" /> <Info term="confidence" />
      </p>
      {evaluated.map((c) => (
        <CropCard key={c.id} c={c} />
      ))}

      {unsuitable.length > 0 && (
        <details className="card group">
          <summary>
            {t.notSuitableTitle} ({unsuitable.length})
          </summary>
          <p className="muted small">{t.notSuitableNote}</p>
          {unsuitable.map((c) => (
            <div key={c.id} className="mini">
              <strong>{nameIn(c.name)}</strong>
              <ConfidenceDetails c={c} />
            </div>
          ))}
        </details>
      )}

      {insufficient.length > 0 && (
        <details className="card group">
          <summary>
            {t.insufficientTitle} ({insufficient.length})
          </summary>
          <p className="muted small">{t.insufficientNote}</p>
          <ul className="plain small">
            {insufficient.map((c) => (
              <li key={c.id}>
                <strong>{nameIn(c.name)}</strong> — {(c.missing ?? []).map((m) => t.missingFields[m] ?? m).join(', ')}
              </li>
            ))}
          </ul>
        </details>
      )}

      {perennial.length > 0 && (
        <p className="muted small">
          {t.perennialTitle}: {perennial.map((c) => nameIn(c.name)).join(', ')}
        </p>
      )}
    </section>
  )
}

function CropCard({ c }: { c: CropResult }) {
  const w = c.best_window!
  const lvl = c.confidence.level
  return (
    <details className="card crop">
      <summary>
        <div className="crop-head">
          <div>
            <strong>{nameIn(c.name)}</strong>
            {c.nitrogen_fixing && <span className="badge n">{t.nitrogenFixing}</span>}
            <div className="muted small">
              {t.sowing} {dateLabel(w.sowing)} → {t.harvest} ~{dateLabel(w.harvest_median)} · {w.season_days_median} {t.days}
            </div>
            {c.local_calendar && (
              <div className="muted small">
                {tk.localCalendar(dateLabel(c.local_calendar.planting), dateLabel(c.local_calendar.maturity))}
                {c.local_calendar.fallback_from === 'irrigated' ? ` · ${tk.calendarRainfedFallback}` : ''}
                {c.local_calendar.gap_filled ? ` · ${tk.calendarGapFilled}` : ''}
                {c.calendar_rule ? '' : ` · ${c.calendar_conflict ? tk.calendarConflict : tk.calendarIgnored}`}
              </div>
            )}
            {c.calendar_rule && c.best_window_outside_calendar && (
              <div className="small warn">
                {tk.outsideCalendar(dateLabel(c.best_window_outside_calendar.sowing), pct(c.best_window_outside_calendar.score_median))}
              </div>
            )}
          </div>
          <span className={`badge conf-${lvl}`}>
            {t.confidence}: {t.confidenceLevels[lvl]}
          </span>
        </div>
        <ScoreBar median={w.score_median} p20={w.score_p20} />
        <div className="row wrap small">
          <span>
            {t.score}: <strong>{pct(w.score_median)}</strong> ({t.badYear} {pct(w.score_p20)}) <Info term="bad_year" />
          </span>
          {c.baseline && c.baseline.score_median !== null && (
            <span className={w.score_median >= c.baseline.score_median ? 'delta up' : 'delta down'}>
              {tk.vsBaseline} {pct(c.baseline.score_median)} ({w.score_median >= c.baseline.score_median ? '+' : '−'}
              {Math.round(Math.abs(w.score_median - c.baseline.score_median) * 100)} puan)
            </span>
          )}
          <span>
            {t.rainDeficit}: <strong>{num(w.rain_deficit_mm_median)} mm</strong>
          </span>
          {c.confidence.needs_local_validation && <span className="badge warn">{t.needsLocal}</span>}
        </div>
      </summary>

      <div className="crop-body">
        <h4>{t.subscores}</h4>
        <ul className="plain small">
          <li>
            {t.temperature}: {pct(w.temperature_score_median)} · {t.water}: {pct(w.water_score_median)} · {t.duration}:{' '}
            {pct(w.duration_factor_median)} · {t.light}: {pct(w.light_factor_median)}
          </li>
          <li>
            {t.waterNeed}: {num(w.etc_mm_median)} mm · {t.seasonRain}: {num(w.precip_mm_median)} mm · {t.failRate}:{' '}
            {pct(w.fail_rate)}
          </li>
          <li>
            {t.frostDays}: {num(w.frost_days_median)}
            {w.heat_days_median !== null && ` · ${t.heatDays}: ${num(w.heat_days_median)}`}
          </li>
          {c.good_sowing_dates && (
            <li>
              {t.goodSowing}: {c.good_sowing_dates.map(dateLabel).join(', ')}
            </li>
          )}
        </ul>
        <ConfidenceDetails c={c} />
        {c.evidence && (
          <>
            <h4>{t.evidence}</h4>
            <ul className="plain small muted">
              {Object.entries(c.evidence).map(([k, e]) => (
                <li key={k}>
                  {t.evidenceLabels[k] ?? k}: {evidenceText(k, e)}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </details>
  )
}

function ConfidenceDetails({ c }: { c: CropResult }) {
  return (
    <>
      <h4>{t.whyConfidence}</h4>
      <ul className="plain small">
        {c.confidence.reasons.map((r) => (
          <li key={r.code}>{reasonText(r)}</li>
        ))}
      </ul>
      <h4>❓ {t.askExpert}</h4>
      <ul className="questions small">
        {c.confidence.questions.map((q) => (
          <li key={q.code}>{questionText(q)}</li>
        ))}
      </ul>
    </>
  )
}

function ScoreBar({ median, p20 }: { median: number; p20: number }) {
  return (
    <div className="scorebar" aria-hidden="true">
      <div className="median" style={{ width: `${median * 100}%` }} />
      <div className="p20" style={{ width: `${p20 * 100}%` }} />
    </div>
  )
}
