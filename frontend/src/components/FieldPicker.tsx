import { useRef, useState, type FormEvent } from 'react'
import { areaDecare, centroid } from '../field'
import { t, tf, tu } from '../i18n'
import type { Irrigation } from '../types'
import { DEMO_POINTS, isShortMapLink, parseCoords, TKGM_PARSEL_URL } from '../places'
import { MapView, type Basemap, type Corner, type MapHandle } from './MapView'
import { LANG } from '../lang'

// OpenStreetMap place search. Usage policy: searches only on submit (no
// autocomplete), at most one request per second. See docs/PRIVACY.md.
const NOMINATIM = 'https://nominatim.openstreetmap.org/search'

interface Place {
  name: string
  lat: number
  lon: number
}

type Search = { kind: 'idle' } | { kind: 'busy' } | { kind: 'error'; message: string } | { kind: 'done'; places: Place[] }

interface Props {
  point: { lat: number; lon: number } | null
  visible: boolean
  irrigation: Irrigation
  onIrrigation: (v: Irrigation) => void
  onPick: (lat: number, lon: number) => void
  corners: Corner[]
  onCorners: (c: Corner[]) => void
}

export function FieldPicker({ point, visible, irrigation, onIrrigation, onPick, corners, onCorners }: Props) {
  const [drawing, setDrawing] = useState(false)
  const mapRef = useRef<MapHandle>(null)
  const [basemap, setBasemap] = useState<Basemap>('satellite')
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState<Search>({ kind: 'idle' })
  const [locating, setLocating] = useState(false)
  const [geoError, setGeoError] = useState(false)
  const lastSearch = useRef(0)

  function pick(lat: number, lon: number) {
    mapRef.current?.flyTo(lat, lon)
    onPick(lat, lon)
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    const q = query.trim()
    if (!q) return
    const c = parseCoords(q)
    if (c) {
      if (Math.abs(c.lat) > 90 || Math.abs(c.lon) > 180) {
        setSearch({ kind: 'error', message: tu.coordOutOfRange })
        return
      }
      setSearch({ kind: 'idle' })
      mapRef.current?.flyTo(c.lat, c.lon)
      return
    }
    // A pasted link is never sent to the place search.
    if (/^(https?|geo):|:\/\/|www\./i.test(q)) {
      setSearch({ kind: 'error', message: isShortMapLink(q) ? tu.shortLink : tu.linkWithoutCoords })
      return
    }
    const wait = 1100 - (Date.now() - lastSearch.current)
    if (wait > 0) await new Promise((r) => setTimeout(r, wait))
    lastSearch.current = Date.now()
    setSearch({ kind: 'busy' })
    try {
      const params = new URLSearchParams({ q, format: 'jsonv2', limit: '5', 'accept-language': 'tr' })
      const r = await fetch(`${NOMINATIM}?${params}`)
      if (!r.ok) throw new Error(String(r.status))
      const rows = (await r.json()) as { display_name: string; lat: string; lon: string }[]
      setSearch({ kind: 'done', places: rows.map((p) => ({ name: p.display_name, lat: Number(p.lat), lon: Number(p.lon) })) })
    } catch {
      setSearch({ kind: 'error', message: tu.searchFailed })
    }
  }

  function useMyLocation() {
    setGeoError(false)
    if (!('geolocation' in navigator) || !window.isSecureContext) {
      setGeoError(true)
      return
    }
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false)
        // Show the spot first; the farmer confirms it is the right field.
        mapRef.current?.flyTo(pos.coords.latitude, pos.coords.longitude, 15)
      },
      () => {
        setLocating(false)
        setGeoError(true)
      },
      { enableHighAccuracy: true, timeout: 15000 },
    )
  }

  return (
    <section className="picker" aria-label={tu.pickTitle}>
      <div className="step-head">
        <span className="step-no">1</span>
        <h2>{tu.pickTitle}</h2>
      </div>

      <form className="search" role="search" onSubmit={submit}>
        <label className="sr-only" htmlFor="place-q">
          {tu.searchLabel}
        </label>
        <input
          id="place-q"
          type="search"
          inputMode="search"
          enterKeyHint="search"
          autoComplete="off"
          placeholder={tu.searchPlaceholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" className="btn primary" disabled={search.kind === 'busy'}>
          {search.kind === 'busy' ? tu.searching : `🔍 ${tu.search}`}
        </button>
      </form>
      {search.kind === 'error' && <p className="warn small">{search.message}</p>}
      {search.kind === 'done' && (
        <ul className="places">
          {search.places.length === 0 && <li className="muted small">{tu.noResults}</li>}
          {search.places.map((p) => (
            <li key={`${p.lat},${p.lon}`}>
              <button
                type="button"
                className="place"
                onClick={() => {
                  mapRef.current?.flyTo(p.lat, p.lon, 14)
                  setSearch({ kind: 'idle' })
                }}
              >
                📍 {p.name}
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="map-card">
        <MapView
          ref={mapRef}
          point={point}
          basemap={basemap}
          visible={visible}
          corners={corners}
          drawing={drawing}
          onAddCorner={(c) => onCorners([...corners, c])}
        />
        <div className="basemap-toggle" role="group" aria-label={LANG === 'en' ? 'Map type' : 'Harita türü'}>
          {(['satellite', 'street'] as Basemap[]).map((b) => (
            <button key={b} type="button" className={basemap === b ? 'on' : ''} aria-pressed={basemap === b} onClick={() => setBasemap(b)}>
              {b === 'satellite' ? `🛰️ ${tu.mapSatellite}` : `🗺️ ${tu.mapStreet}`}
            </button>
          ))}
        </div>
        <button
          type="button"
          className="btn pick-btn"
          onClick={() => {
            const c = mapRef.current?.center()
            if (c) onPick(c.lat, c.lon)
          }}
        >
          ✔ {tu.pickHere}
        </button>
      </div>
      <p className="muted small">{tu.pickHint}</p>

      <div className="card corners">
        <strong>📐 {tf.title}</strong>
        <p className="small muted">{drawing ? tf.drawingHint : tf.intro}</p>
        <div className="row wrap">
          {!drawing ? (
            <button type="button" className="btn" onClick={() => setDrawing(true)}>
              ✏️ {corners.length ? tf.edit : tf.start}
            </button>
          ) : (
            <>
              <button type="button" className="btn small" disabled={!corners.length} onClick={() => onCorners(corners.slice(0, -1))}>
                ↩️ {tf.undo}
              </button>
              <button type="button" className="btn small" disabled={!corners.length} onClick={() => onCorners([])}>
                🗑️ {tf.clear}
              </button>
              <button
                type="button"
                className="btn primary"
                disabled={corners.length < 3}
                onClick={() => {
                  setDrawing(false)
                  const c = centroid(corners)
                  onPick(c.lat, c.lon)
                }}
              >
                ✔ {tf.done}
              </button>
            </>
          )}
        </div>
        {corners.length >= 3 && <p className="small">{tf.area(areaDecare(corners))}</p>}
        <p className="muted small">🔒 {tf.privacy}</p>
      </div>
      {basemap === 'satellite' && <p className="muted small">{tu.satelliteNote}</p>}

      <div className="row wrap">
        <button type="button" className="btn big" onClick={useMyLocation} disabled={locating}>
          {locating ? t.locating : `📍 ${t.useMyLocation}`}
        </button>
      </div>
      {geoError && <p className="warn small">{t.locationFailed}</p>}
      <div className="row wrap">
        <span className="muted small">{tu.examples}:</span>
        {DEMO_POINTS.map((p) => (
          <button key={p.key} type="button" className="btn chip" onClick={() => pick(p.lat, p.lon)}>
            {p.label}
          </button>
        ))}
      </div>
      <p className="muted small">{tu.searchNote}</p>

      <details className="card tkgm">
        <summary>📜 {tu.tkgmTitle}</summary>
        <ol className="tkgm-steps small">
          {tu.tkgmSteps.map((x) => (
            <li key={x}>{x}</li>
          ))}
        </ol>
        <a className="btn primary tkgm-link" href={TKGM_PARSEL_URL} target="_blank" rel="noopener noreferrer">
          {tu.tkgmOpen} ↗
        </a>
        <p className="muted small">{tu.tkgmNote}</p>
      </details>

      <div className="step-head">
        <span className="step-no">2</span>
        <h2>{tu.irrigationQuestion}</h2>
      </div>
      <IrrigationChoice value={irrigation} onChange={onIrrigation} />
    </section>
  )
}

export function IrrigationChoice({ value, onChange, compact }: { value: Irrigation; onChange: (v: Irrigation) => void; compact?: boolean }) {
  return (
    <div className={compact ? 'irrigation compact' : 'irrigation'}>
      {compact && <span className="irr-title">💧 {tu.irrigationQuestion}</span>}
      <div className="choice" role="radiogroup" aria-label={tu.irrigationQuestion}>
        {(['none', 'limited', 'full'] as Irrigation[]).map((v) => (
          <button key={v} type="button" role="radio" aria-checked={value === v} className={value === v ? 'on' : ''} onClick={() => onChange(v)}>
            {v === 'none' ? '🌧️' : v === 'limited' ? '💧' : '🚿'} {tu.irrigationOptions[v]}
          </button>
        ))}
      </div>
      <p className="muted small">{tu.irrigationHelp[value]}</p>
    </div>
  )
}
