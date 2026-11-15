import { Map as MapLibreMap, Marker, NavigationControl, setWorkerUrl, type GeoJSONSource, type StyleSpecification } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'
import type { Feature } from 'geojson'
import { LANG } from '../lang'

// Defined in vite.config.ts (the worker file is served/emitted there).
declare const __MAPLIBRE_WORKER_PATH__: string
setWorkerUrl(__MAPLIBRE_WORKER_PATH__)

// Street map: OpenFreeMap (free, no API key); attribution comes from the style.
const STREET_STYLE = 'https://tiles.openfreemap.org/styles/liberty'

// Satellite map: EOX Sentinel-2 cloudless 2016 (CC BY 4.0, verified by
// scripts/probe/probe_basemap.py), with road lines and place names from the
// same OpenFreeMap vector tiles on top. See docs/CREDITS.md.
const SATELLITE_STYLE: StyleSpecification = {
  version: 8,
  glyphs: 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf',
  sources: {
    s2: {
      type: 'raster',
      tiles: ['https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg'],
      tileSize: 256,
      maxzoom: 15, // 10 m pixels; deeper zooms are only enlarged
      attribution:
        '<a href="https://s2maps.eu" target="_blank" rel="noopener">Sentinel-2 cloudless 2016</a> by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2016), CC BY 4.0',
    },
    omt: { type: 'vector', url: 'https://tiles.openfreemap.org/planet' },
  },
  layers: [
    { id: 's2', type: 'raster', source: 's2' },
    {
      id: 'roads',
      type: 'line',
      source: 'omt',
      'source-layer': 'transportation',
      filter: ['match', ['get', 'class'], ['motorway', 'trunk', 'primary', 'secondary', 'tertiary'], true, false],
      paint: { 'line-color': '#fff6d5', 'line-opacity': 0.55, 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.5, 14, 2] },
    },
    {
      id: 'places',
      type: 'symbol',
      source: 'omt',
      'source-layer': 'place',
      filter: ['match', ['get', 'class'], ['country', 'state', 'city', 'town', 'village', 'hamlet'], true, false],
      layout: {
        'text-field': ['coalesce', ['get', 'name:tr'], ['get', 'name']],
        'text-font': ['Noto Sans Regular'],
        'text-size': ['match', ['get', 'class'], ['country', 'city'], 15, 'town', 13, 12],
      },
      paint: { 'text-color': '#ffffff', 'text-halo-color': 'rgba(0,0,0,0.75)', 'text-halo-width': 1.4 },
    },
  ],
}

export type Basemap = 'satellite' | 'street'

export interface MapHandle {
  /** Centre of the map view (where the crosshair is). */
  center: () => { lat: number; lon: number } | null
  flyTo: (lat: number, lon: number, zoom?: number) => void
}

export type Corner = { lat: number; lon: number }

interface Props {
  point: { lat: number; lon: number } | null
  basemap: Basemap
  /** Set when the map is shown again after being hidden (MapLibre must re-measure). */
  visible: boolean
  /** Field corners (kept in the browser only, docs/PRIVACY.md). */
  corners?: Corner[]
  /** While drawing, a tap adds a corner instead of moving the map. */
  drawing?: boolean
  onAddCorner?: (c: Corner) => void
}

const FIELD_SRC = 'field'

function fieldGeoJSON(corners: Corner[]) {
  const ring = corners.map((c) => [c.lon, c.lat])
  const features: Feature[] = corners.map((c) => ({
    type: 'Feature',
    properties: {},
    geometry: { type: 'Point', coordinates: [c.lon, c.lat] },
  }))
  if (corners.length >= 2)
    features.push({
      type: 'Feature',
      properties: {},
      geometry:
        corners.length >= 3
          ? { type: 'Polygon', coordinates: [[...ring, ring[0]]] }
          : { type: 'LineString', coordinates: ring },
    })
  return { type: 'FeatureCollection' as const, features }
}

export const MapView = forwardRef<MapHandle, Props>(function MapView(
  { point, basemap, visible, corners = [], drawing = false, onAddCorner },
  ref,
) {
  const container = useRef<HTMLDivElement>(null)
  const drawingRef = useRef(drawing)
  const addRef = useRef(onAddCorner)
  const cornersRef = useRef(corners)
  drawingRef.current = drawing
  addRef.current = onAddCorner
  cornersRef.current = corners
  const map = useRef<MapLibreMap | null>(null)
  const marker = useRef<Marker | null>(null)
  const firstStyle = useRef(basemap)

  useImperativeHandle(ref, () => ({
    center: () => {
      const c = map.current?.getCenter()
      return c ? { lat: c.lat, lon: c.lng } : null
    },
    flyTo: (lat, lon, zoom = 13) => map.current?.flyTo({ center: [lon, lat], zoom, speed: 1.8 }),
  }))

  useEffect(() => {
    if (!container.current) return
    const m = new MapLibreMap({
      container: container.current,
      style: firstStyle.current === 'satellite' ? SATELLITE_STYLE : STREET_STYLE,
      center: [35, 39], // Türkiye
      zoom: 4.6,
      maxZoom: 17,
      attributionControl: { compact: true },
    })
    m.addControl(new NavigationControl({ showCompass: false }), 'top-right')
    // A tap moves that spot under the crosshair; the user then confirms.
    m.on('click', (e) => {
      if (drawingRef.current && addRef.current) addRef.current({ lat: e.lngLat.lat, lon: e.lngLat.lng })
      else m.easeTo({ center: e.lngLat, zoom: Math.max(m.getZoom(), 12) })
    })
    // The field outline lives in its own source; a style change removes it, so add it again.
    const addField = () => {
      if (m.getSource(FIELD_SRC)) return
      m.addSource(FIELD_SRC, { type: 'geojson', data: fieldGeoJSON(cornersRef.current) })
      m.addLayer({ id: 'field-fill', type: 'fill', source: FIELD_SRC, filter: ['==', '$type', 'Polygon'],
        paint: { 'fill-color': '#e9a23b', 'fill-opacity': 0.25 } })
      m.addLayer({ id: 'field-line', type: 'line', source: FIELD_SRC, filter: ['!=', '$type', 'Point'],
        paint: { 'line-color': '#ffd166', 'line-width': 3 } })
      m.addLayer({ id: 'field-corners', type: 'circle', source: FIELD_SRC, filter: ['==', '$type', 'Point'],
        paint: { 'circle-radius': 6, 'circle-color': '#e8572b', 'circle-stroke-color': '#fff', 'circle-stroke-width': 2 } })
    }
    m.on('style.load', addField)
    // The compact attribution starts open on narrow screens and would cover the pick button.
    m.once('load', () => container.current?.querySelector('.maplibregl-ctrl-attrib')?.classList.remove('maplibregl-compact-show'))
    map.current = m
    return () => m.remove()
  }, [])

  useEffect(() => {
    const m = map.current
    if (!m || firstStyle.current === basemap) return
    firstStyle.current = basemap
    m.setStyle(basemap === 'satellite' ? SATELLITE_STYLE : STREET_STYLE)
  }, [basemap])

  useEffect(() => {
    if (visible) map.current?.resize()
  }, [visible])

  useEffect(() => {
    ;(map.current?.getSource(FIELD_SRC) as GeoJSONSource | undefined)?.setData(fieldGeoJSON(corners))
  }, [corners])

  useEffect(() => {
    const m = map.current
    if (!m || !point) return
    if (!marker.current) marker.current = new Marker({ color: '#e8572b' })
    marker.current.setLngLat([point.lon, point.lat]).addTo(m)
  }, [point])

  return (
    <div className="map-wrap">
      <div ref={container} className="map" role="application" aria-label={LANG === 'en' ? 'Map' : 'Harita'} />
      <div className="crosshair" aria-hidden="true" />
    </div>
  )
})
