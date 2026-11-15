import { dateLabel, num, pct, questionText, rotationText, t, tr, te } from '../i18n'
import { rotationEvidence } from '../learn'
import type { Item, RotationCard, RotationResponse, RotationSlot } from '../types'
import { LANG, nameIn } from '../lang'

// Soil water stored before sowing (fallow / gap), shown when it is worth mentioning (>= 10 mm).
function storedLabel(s: RotationSlot): string {
  const w = s.stored_soil_water
  return w && w.stored_mm_median >= 10 ? ` · 💧 ${tr.storedWater(w.stored_mm_median)}` : ''
}

const COLORS = ['#7fb77e', '#e3b04b', '#6fa8dc', '#c27ba0', '#e07b5f', '#9e9ac8']
const SUBSCORE_ORDER = ['suitability', 'climate_risk', 'water', 'soil', 'erosion', 'nitrogen', 'income', 'forage', 'diversity']

export function RotationCards({ data, nameOf }: { data: RotationResponse; nameOf: (id: string) => string }) {
  const llmTexts = data.explanation?.mode === 'llm' ? data.explanation.texts : null
  let n = 0
  return (
    <>
      <p className="muted small">
        {tr.usableCrops(data.usable_crops.length, data.min_crop_score)}
        {data.n_recommended === 0 && ` ${tr.noRecommendation}`}
        {data.not_used_first_cut_only?.length
          ? ` ${tr.firstCutOnly(data.not_used_first_cut_only.map(nameOf).join(', '))}`
          : null}
        {data.erosion_ignored_flat_terrain ? ` ⛰️ ${te.flat}` : null}
      </p>
      <div className="rotation-scroller" role="list">
        {data.cards.map((c) => {
          const label = c.kind === 'recommended' ? `${tr.kinds.recommended} ${++n}` : tr.kinds[c.kind]
          return <Card key={c.id} c={c} label={label} nameOf={nameOf} llmText={llmTexts?.[c.id]} hideErosion={data.erosion_ignored_flat_terrain} />
        })}
      </div>
      {llmTexts && <p className="muted small">🤖 {tr.llmNote}</p>}
      <p className="disclaimer card">⚠️ {t.disclaimer}</p>
    </>
  )
}

function Card({
  c,
  label,
  nameOf,
  llmText,
  hideErosion,
}: {
  c: RotationCard
  label: string
  nameOf: (id: string) => string
  llmText?: string
  hideErosion?: boolean
}) {
  const colors = new Map<string, string>()
  c.years.flat().forEach((s) => colors.has(s.crop_id) || colors.set(s.crop_id, COLORS[colors.size % COLORS.length]))
  const text = (i: Item) => rotationText(i, nameOf)
  const firstStrength = c.benefits[0] ?? c.why.find((w) => w.code.startsWith('strong_'))
  const firstRisk = c.risks[0] ?? c.data_gaps[0]

  return (
    <article className={`card rotation ${c.kind}`} role="listitem">
      <header className="rot-head">
        <div>
          <span className={`badge kind-${c.kind}`}>{label}</span>
          <span className="muted small"> · {tr.cycleYears(c.years.length)}</span>
        </div>
        <span className={`badge conf-${c.confidence.level}`}>
          {t.confidence}: {t.confidenceLevels[c.confidence.level]}
        </span>
      </header>

      <div className="rot-total">
        <span className="small">{tr.total}</span>
        <div className="scorebar">
          <div className="p20" style={{ width: `${c.total * 100}%` }} />
        </div>
        <strong>{pct(c.total)}</strong>
      </div>
      {c.confidence.needs_local_validation && <span className="badge warn">{t.needsLocal}</span>}

      <div className="rot-years">
        {c.years.map((y, i) => (
          <div key={i} className="rot-year">
            <div className="rot-year-label small">
              <strong>
                {tr.year} {i + 1}:
              </strong>{' '}
              {y.length === 0
                ? c.missing_slots.some((m) => m.year === i + 1)
                  ? c.missing_slots.filter((m) => m.year === i + 1).map((m) => `${nameOf(m.crop_id)} (?)`).join(' + ')
                  : `🟫 ${tr.fallow}`
                : y.map((s) => `${nameIn(s.name)} (${dateLabel(s.sowing)} → ${dateLabel(s.harvest)})` + storedLabel(s)).join(' + ')}
            </div>
            <div className="month-strip" aria-hidden="true">
              {Array.from({ length: 12 }, (_, m) => {
                const s = y.find((sl) => sl.months.includes(m + 1))
                return (
                  <span key={m} style={{ background: s ? colors.get(s.crop_id) : undefined }} title={s ? nameIn(s.name) : undefined}>
                    {t.months[m]}
                  </span>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      <p className="rot-summary small">
        {llmText ??
          [
            `${label}: ${c.years.map((y) => (y.length ? y.map((s) => nameIn(s.name)).join(' + ') : tr.fallow)).join(' → ')}.`,
            firstStrength && text(firstStrength),
            firstRisk && text(firstRisk),
            LANG === 'en' ? 'Check with a local expert.' : 'Yerel bir uzmanla kontrol edin.',
          ]
            .filter(Boolean)
            .join(' ')}
      </p>

      {c.irrigation_need_mm_per_year !== null && (
        <p className="small">
          💧 {tr.irrigationNeed}: <strong>{num(c.irrigation_need_mm_per_year)} {tr.perYear}</strong>
        </p>
      )}

      <ul className="subscores small">
        {SUBSCORE_ORDER.filter((k) => c.subscores[k] && !(hideErosion && k === 'erosion')).map((k) => {
          const s = c.subscores[k]
          return (
            <li key={k}>
              <span className="sub-name">
                {tr.subscoreNames[k] ?? k}
                {s.weight === 0 && ' (0)'}
              </span>
              {s.value === null ? (
                <span className="muted">{tr.unknownValue}</span>
              ) : (
                <>
                  <span className="mini-bar">
                    <span style={{ width: `${s.value * 100}%` }} />
                  </span>
                  <span className="sub-val">{pct(s.value)}</span>
                </>
              )}
            </li>
          )
        })}
      </ul>

      <Section title={tr.why} items={c.why} render={text} />
      <Section title={tr.benefits} items={c.benefits} render={text} />
      <Section title={tr.risks} items={c.risks} render={text} warn />
      <Section title={tr.dataGaps} items={c.data_gaps} render={text} />
      <Section title={tr.opportunities} items={c.opportunities} render={text} />
      <Section
        title={`❓ ${t.askExpert}`}
        items={c.questions}
        render={(q) => {
          const crop = q.params.crop_id ? `${nameOf(String(q.params.crop_id))}: ` : ''
          return crop + (questionText(q) !== q.text ? questionText(q) : text(q))
        }}
      />
      <details className="small">
        <summary>{tr.evidenceTitle}</summary>
        <ul className="plain muted">
          {c.evidence.map((e) => (
            <li key={e}>{rotationEvidence[e] ?? e}</li>
          ))}
        </ul>
      </details>
    </article>
  )
}

function Section({ title, items, render, warn }: { title: string; items: Item[]; render: (i: Item) => string; warn?: boolean }) {
  if (!items.length) return null
  return (
    <>
      <h4>{title}</h4>
      <ul className={`small ${warn ? 'risk-list' : 'plain-list'}`}>
        {items.map((i, k) => (
          <li key={`${i.code}-${k}`}>{render(i)}</li>
        ))}
      </ul>
    </>
  )
}
