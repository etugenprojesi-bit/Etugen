import { dateLabel, questionText, t, tu } from '../i18n'
import type { Analysis, CropResult, MonthClimate } from '../types'
import { Info } from './Learn'
import { LANG, nameIn } from '../lang'

const TOP_N = 3

// Display rules for the plain "what to watch" list (not model parameters; also
// written in docs/KULLANIM_KILAVUZU.md):
// - frost month: frost in at least half of the years (frost_probability ≥ 0.5);
// - hot month: on average at least 1 day above 35 °C (the generic hot-day rule, docs/METHOD.md);
// - dry month: monthly water balance (rain − ET0) below 0.
const FROST_SHARE = 0.5
const HOT_DAYS = 1

export function Summary({ a, onGo }: { a: Analysis; onGo: (tab: 'rotation' | 'details') => void }) {
  const top = a.crops.filter((c) => c.status === 'evaluated' && c.best_window).slice(0, TOP_N)
  const months = a.climate.monthly.months

  return (
    <div className="summary">
      <section>
        <h2 className="section-title">🌾 {tu.bestTitle}</h2>
        <p className="muted small lead">
          {tu.bestIntro} <Info term="score" />
        </p>
        {top.length === 0 && <div className="card">{tu.noCrops}</div>}
        <ol className="best-list">
          {top.map((c, i) => (
            <BestCrop key={c.id} c={c} rank={i + 1} />
          ))}
        </ol>
      </section>

      <section>
        <h2 className="section-title">⚠️ {tu.risksTitle}</h2>
        <p className="muted small lead">{tu.risksIntro}</p>
        <div className="card risks">
          <RiskRow icon="❄️" title={tu.riskFrost} text={tu.riskFrostText} kind="frost" months={months} on={(m) => m.frost_probability >= FROST_SHARE} term="frost" />
          <RiskRow icon="☀️" title={tu.riskHot} text={tu.riskHotText} kind="hot" months={months} on={(m) => m.hot_days >= HOT_DAYS} term="hot" />
          <RiskRow icon="💧" title={tu.riskDry} text={tu.riskDryText} kind="dry" months={months} on={(m) => m.water_balance_mm < 0} term="water_balance" />
        </div>
      </section>

      <section className="next">
        <h2 className="section-title">👉 {tu.next}</h2>
        <button type="button" className="btn next-btn" onClick={() => onGo('rotation')}>
          🔄 {tu.goRotation}
        </button>
        <button type="button" className="btn next-btn" onClick={() => onGo('details')}>
          🔬 {tu.goDetails}
        </button>
      </section>
    </div>
  )
}

function BestCrop({ c, rank }: { c: CropResult; rank: number }) {
  const w = c.best_window!
  const score = Math.round(w.score_median * 100)
  const bad = Math.round(w.score_p20 * 100)
  const season = new Set(w.season_months)
  const goodMonths = [...new Set((c.good_sowing_dates ?? [w.sowing]).map((d) => Number(d.slice(0, 2))))].sort((x, y) => x - y)
  const sowMonths = new Set(goodMonths)
  return (
    <li className="card best">
      <div className="best-head">
        <span className="rank" aria-hidden="true">
          {rank}
        </span>
        <div className="best-name">
          <strong>{nameIn(c.name)}</strong>
          {c.nitrogen_fixing && <span className="badge n">🫘 {t.nitrogenFixing}</span>}
        </div>
        <div className="score" aria-label={LANG === 'en' ? `Score: ${score} out of 100` : `Puan: 100 üzerinden ${score}`}>
          <span className="score-num">{score}</span>
          <span className="score-of">{tu.outOf}</span>
        </div>
      </div>
      <div className="meter" aria-hidden="true">
        <span className="meter-normal" style={{ width: `${score}%` }} />
        <span className="meter-bad" style={{ width: `${bad}%` }} />
      </div>
      <p className="small muted bad-line">
        {tu.badYearShort}: {bad} {tu.outOf} <Info term="bad_year" />
      </p>

      <div className="dates">
        <div>
          <span className="date-label">🌱 {tu.sowShort}</span>
          <strong>{dateLabel(w.sowing)}</strong>
        </div>
        <div>
          <span className="date-label">🌾 {tu.harvestShort}</span>
          <strong>~{dateLabel(w.harvest_median)}</strong>
        </div>
      </div>

      <div className="season-strip" role="img" aria-label={`${tu.goodMonths}: ${goodMonths.map((m) => t.monthNames[m - 1]).join(', ')}`}>
        {t.months.map((m, i) => (
          <span key={i} className={`${season.has(i + 1) ? 'in' : ''} ${sowMonths.has(i + 1) ? 'sow' : ''}`}>
            {m}
          </span>
        ))}
      </div>
      <p className="small muted legend">
        <span className="key sow" /> {tu.goodMonths} <span className="key in" /> Tarlada
      </p>

      {c.confidence.needs_local_validation && <p className="badge warn big-badge">👨‍🌾 {tu.askLocal}</p>}
      {c.confidence.questions.length > 0 && (
        <details className="questions-box">
          <summary>❓ {tu.questionsTitle}</summary>
          <ul className="questions small">
            {c.confidence.questions.map((q) => (
              <li key={q.code}>{questionText(q)}</li>
            ))}
          </ul>
        </details>
      )}
    </li>
  )
}

function monthRuns(on: boolean[]): string {
  if (on.every(Boolean)) return LANG === 'en' ? 'all year' : 'bütün yıl'
  // Start after an "off" month so runs that wrap around the new year stay together.
  const start = on.findIndex((v, i) => !v && on[(i + 1) % 12])
  const runs: [number, number][] = []
  for (let k = 1; k <= 12; k++) {
    const i = (start + k) % 12
    if (!on[i]) continue
    const last = runs[runs.length - 1]
    if (last && (last[1] + 1) % 12 === i) last[1] = i
    else runs.push([i, i])
  }
  return runs.map(([a, b]) => (a === b ? t.monthNames[a] : `${t.monthNames[a]}–${t.monthNames[b]}`)).join(', ')
}

function RiskRow(p: {
  icon: string
  title: string
  text: string
  kind: string
  term: string
  months: MonthClimate[]
  on: (m: MonthClimate) => boolean
}) {
  const on = Array.from({ length: 12 }, (_, i) => {
    const m = p.months.find((x) => x.month === i + 1)
    return m ? p.on(m) : false
  })
  const any = on.some(Boolean)
  return (
    <div className={`risk ${any ? '' : 'none'}`}>
      <div className="risk-top">
        <span className="risk-icon" aria-hidden="true">
          {p.icon}
        </span>
        <div>
          <strong>{p.title}</strong>
          <span className="risk-when">{any ? monthRuns(on) : tu.riskNone}</span>
        </div>
        <Info term={p.term} />
      </div>
      <div className={`risk-strip ${p.kind}`} aria-hidden="true">
        {t.months.map((m, i) => (
          <span key={i} className={on[i] ? 'on' : ''}>
            {m}
          </span>
        ))}
      </div>
      {any && <p className="small muted">{p.text}</p>}
    </div>
  )
}
