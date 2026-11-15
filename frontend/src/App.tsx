import { useEffect, useRef, useState, type ReactNode } from 'react'
import { ApiError, fetchAnalysis } from './api'
import { CalendarStrip } from './components/Calendar'
import { CropList } from './components/CropList'
import { FieldPicker, IrrigationChoice } from './components/FieldPicker'
import { Footer } from './components/Footer'
import { HelpDialog } from './components/Help'
import { MonthlyChart } from './components/MonthlyChart'
import { EasyPlan } from './components/EasyPlan'
import type { Corner } from './components/MapView'
import { ModeChooser, type Mode } from './components/ModeChooser'
import { DataBanner, DataStrip, ProfileCard } from './components/Profile'
import { RiskPanel } from './components/RiskPanel'
import { RotationPlanner } from './components/RotationPlanner'
import { SatellitePanel } from './components/SatellitePanel'
import { ScenarioControls } from './components/ScenarioControls'
import { Summary } from './components/Summary'
import { num, t, te, tu } from './i18n'
import type { Analysis, Irrigation, Variant } from './types'
import { LANG, setLang } from './lang'

type State =
  | { kind: 'idle' }
  | { kind: 'loading'; prev?: Analysis }
  | { kind: 'error'; message: string }
  | { kind: 'done'; data: Analysis }

type Tab = 'field' | 'summary' | 'rotation' | 'details' | 'plan'
const EXPERT_TABS: { id: Tab; icon: string }[] = [
  { id: 'field', icon: '📍' },
  { id: 'summary', icon: '🌾' },
  { id: 'rotation', icon: '🔄' },
  { id: 'details', icon: '🔬' },
]
// Kolay mod (docs/drafts/plan_kolay_mod.md): field, the automatic plan, the plain summary.
const EASY_TABS: { id: Tab; icon: string }[] = [
  { id: 'field', icon: '📍' },
  { id: 'plan', icon: '🗓️' },
  { id: 'summary', icon: '🌾' },
]
const MODE_KEY = 'etugen-mode'

function loadMode(): Mode | null {
  try {
    const v = localStorage.getItem(MODE_KEY)
    return v === 'easy' || v === 'expert' ? v : null
  } catch {
    return null
  }
}

function errorMessage(e: unknown): string {
  if (e instanceof ApiError) {
    const fromPower = (e.detail as { source?: string } | null)?.source === 'nasa_power'
    if (e.status === 502 && fromPower) return t.errors.source
    if (e.status === 422) return t.errors.invalid
    // No response, or a proxy/gateway error without our backend's detail: server unreachable.
    if (e.status === 0 || e.status >= 500) return t.errors.network
  }
  return t.errors.other
}

export default function App() {
  const [point, setPoint] = useState<{ lat: number; lon: number } | null>(null)
  const [irrigation, setIrrigation] = useState<Irrigation>('none')
  const [variant, setVariant] = useState<Variant>({ precipSource: 'power', deltaT: 0, deltaP: 0, exploreSowing: false })
  const [state, setState] = useState<State>({ kind: 'idle' })
  const [tab, setTab] = useState<Tab>('field')
  const [help, setHelp] = useState(false)
  const [corners, setCorners] = useState<Corner[]>([])
  const [mode, setMode] = useState<Mode | null>(loadMode)
  const TABS = mode === 'easy' ? EASY_TABS : EXPERT_TABS

  function chooseMode(m: Mode) {
    setMode(m)
    try {
      localStorage.setItem(MODE_KEY, m)
    } catch {
      /* private window: the choice lasts for this visit only */
    }
    if (m === 'easy' && (tab === 'rotation' || tab === 'details')) setTab(point ? 'plan' : 'field')
    if (m === 'expert' && tab === 'plan') setTab('rotation')
  }
  const shownPoint = useRef<{ lat: number; lon: number } | null>(null)

  useEffect(() => {
    if (!point) return
    const ctrl = new AbortController()
    const samePoint = shownPoint.current === point
    // Same point, new irrigation / rainfall source / scenario: keep the old results visible
    // (and the risk and rotation panels mounted) while recalculating.
    setState((s) => ({ kind: 'loading', prev: samePoint && s.kind === 'done' ? s.data : undefined }))
    fetchAnalysis(point.lat, point.lon, irrigation, variant, ctrl.signal)
      .then((data) => {
        setState({ kind: 'done', data })
        shownPoint.current = point
      })
      .catch((e) => {
        if ((e as Error).name !== 'AbortError') setState({ kind: 'error', message: errorMessage(e) })
      })
    return () => ctrl.abort()
  }, [point, irrigation, variant])

  function go(next: Tab) {
    setTab(next)
    window.scrollTo({ top: 0 })
  }

  function pick(lat: number, lon: number) {
    setPoint({ lat, lon })
    go(mode === 'easy' ? 'plan' : 'summary')
  }

  const data = state.kind === 'done' ? state.data : state.kind === 'loading' ? state.prev : undefined
  const status = (
    <>
      {state.kind === 'loading' && (
        <div className="card loading">
          <span className="spinner" aria-hidden="true" /> {tu.loading}
        </div>
      )}
      {state.kind === 'error' && <div className="card error">⛔ {state.message}</div>}
    </>
  )

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <span className="logo" aria-hidden="true">
            🧭
          </span>
          <div>
            <h1>{t.appName}</h1>
            <p className="tagline">{t.tagline}</p>
          </div>
        </div>
        <div className="row top-actions">
          {mode && (
            <button type="button" className="btn small mode-btn" onClick={() => chooseMode(mode === 'easy' ? 'expert' : 'easy')}>
              {mode === 'easy' ? `🔬 ${te.switchToExpert}` : `🧑‍🌾 ${te.switchToEasy}`}
            </button>
          )}
          <button
            type="button"
            className="btn small mode-btn lang-btn"
            lang={LANG === 'tr' ? 'en' : 'tr'}
            aria-label={LANG === 'tr' ? 'English' : 'Türkçe'}
            onClick={() => setLang(LANG === 'tr' ? 'en' : 'tr')}
          >
            {LANG === 'tr' ? 'EN' : 'TR'}
          </button>
          <button type="button" className="btn help-btn" aria-label={tu.help} onClick={() => setHelp(true)}>
            ❓ <span>{tu.help}</span>
          </button>
        </div>
      </header>

      <main className="content">
        {mode === null && <ModeChooser onChoose={chooseMode} />}
        <div hidden={mode === null || tab !== 'field'}>
          <FieldPicker
            point={point}
            visible={tab === 'field'}
            irrigation={irrigation}
            onIrrigation={setIrrigation}
            onPick={pick}
            corners={corners}
            onCorners={setCorners}
          />
        </div>

        {tab !== 'field' && (
          <div className="place-bar">
            {point ? (
              <>
                <span>
                  📍 {tu.chosenPlace}: <strong>{num(point.lat, 2)}°, {num(point.lon, 2)}°</strong>
                </span>
                <button type="button" className="btn small" onClick={() => go('field')}>
                  {tu.changeField}
                </button>
              </>
            ) : (
              <span>{tu.noField}</span>
            )}
          </div>
        )}

        <div hidden={tab !== 'summary'} aria-live="polite">
          {data && <DataStrip a={data} />}
          {point && <IrrigationChoice compact value={irrigation} onChange={setIrrigation} />}
          {status}
          {data && <Summary a={data} onGo={(x) => (mode === 'easy' ? (x === 'rotation' ? go('plan') : (chooseMode('expert'), go(x))) : go(x))} />}
        </div>

        {mode === 'easy' && (
          <div hidden={tab !== 'plan'}>
            {point && <IrrigationChoice compact value={irrigation} onChange={setIrrigation} />}
            {status}
            {data && (
              <EasyPlan
                a={data}
                corners={corners}
                onExpert={() => {
                  chooseMode('expert')
                  go('rotation')
                }}
              />
            )}
          </div>
        )}

        <div hidden={tab !== 'rotation'}>
          {status}
          {data && <RotationPlanner key={`${data.query.lat},${data.query.lon},${data.query.irrigation}`} a={data} />}
        </div>

        <div hidden={tab !== 'details'} className="details-tab">
          {status}
          {data && (
            <>
              <p className="muted small lead">{tu.detailsIntro}</p>
              <ScenarioControls value={variant} onChange={setVariant} />
              <Acc title={`📄 ${tu.detailsSections.data}`}>
                <DataBanner a={data} />
              </Acc>
              <Acc title={`🌦️ ${tu.detailsSections.climate}`}>
                <ProfileCard a={data} />
                <MonthlyChart months={data.climate.monthly.months} />
                <CalendarStrip months={data.climate.monthly.months} crops={data.crops} />
              </Acc>
              <Acc title={`🌾 ${tu.detailsSections.crops}`}>
                <CropList crops={data.crops} />
              </Acc>
              <Acc title={`⚠️ ${tu.detailsSections.risk}`} hideInnerTitle>
                <RiskPanel key={`risk-${data.query.lat},${data.query.lon}`} lat={data.query.lat} lon={data.query.lon} variant={variant} />
              </Acc>
              <Acc title={`🛰️ ${tu.detailsSections.satellite}`} hideInnerTitle>
                <SatellitePanel key={`sat-${data.query.lat},${data.query.lon}`} lat={data.query.lat} lon={data.query.lon} />
              </Acc>
            </>
          )}
        </div>
      </main>

      <Footer />

      <nav className="tabbar" aria-label={LANG === 'en' ? 'Sections' : 'Bölümler'} hidden={mode === null}>
        {TABS.map((x) => (
          <button
            key={x.id}
            type="button"
            className={tab === x.id ? 'on' : ''}
            aria-current={tab === x.id ? 'page' : undefined}
            disabled={x.id !== 'field' && !point}
            onClick={() => go(x.id)}
          >
            <span className="tab-icon" aria-hidden="true">
              {x.icon}
            </span>
            {x.id === 'plan' ? te.planTab : tu.tabs[x.id as Exclude<Tab, 'plan'>]}
          </button>
        ))}
      </nav>

      <HelpDialog open={help} onClose={() => setHelp(false)} />
    </div>
  )
}

function Acc({ title, children, hideInnerTitle }: { title: string; children: ReactNode; hideInnerTitle?: boolean }) {
  return (
    <details className={`card acc ${hideInnerTitle ? 'hide-inner-title' : ''}`}>
      <summary>{title}</summary>
      <div className="acc-body">{children}</div>
    </details>
  )
}
