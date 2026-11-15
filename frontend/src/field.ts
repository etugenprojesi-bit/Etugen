// Field outline helpers. The corners never leave the browser (docs/PRIVACY.md): only the
// centre is used as the analysis point, like a single tap on the map.
import type { Corner } from './components/MapView'
import { LANG } from './lang'

const M_PER_DEG_LAT = 110_574 // WGS84 mean, adequate for field-sized areas

/** Corners in metres east / north of the centroid (local equirectangular projection). */
export function toLocal(corners: Corner[]): { x: number; y: number }[] {
  const c = centroid(corners)
  const kx = 111_320 * Math.cos((c.lat * Math.PI) / 180)
  return corners.map((p) => ({ x: (p.lon - c.lon) * kx, y: (p.lat - c.lat) * M_PER_DEG_LAT }))
}

export function centroid(corners: Corner[]): Corner {
  const n = corners.length
  return {
    lat: corners.reduce((s, p) => s + p.lat, 0) / n,
    lon: corners.reduce((s, p) => s + p.lon, 0) / n,
  }
}

/** Polygon area in decares (1 da = 1000 m²), shoelace formula on the local projection. */
export function areaDecare(corners: Corner[]): number {
  if (corners.length < 3) return 0
  const p = toLocal(corners)
  let a = 0
  for (let i = 0; i < p.length; i++) {
    const j = (i + 1) % p.length
    a += p[i].x * p[j].y - p[j].x * p[i].y
  }
  return Math.abs(a) / 2 / 1000
}

const DIRS = LANG === 'en'
  ? ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west']
  : ['kuzey', 'kuzeydoğu', 'doğu', 'güneydoğu', 'güney', 'güneybatı', 'batı', 'kuzeybatı']

/** Compass word for an azimuth (degrees clockwise from north). */
export function compass(az: number): string {
  return DIRS[Math.round((((az % 360) + 360) % 360) / 45) % 8]
}

/** Row direction (0-180°) as "A–B", e.g. 139° -> "kuzeybatı–güneydoğu". */
export function rowAxis(az: number): string {
  const a = compass(az + 180)
  const b = compass(az)
  const [x, y] = a < b ? [a, b] : [b, a]
  return LANG === 'en' ? `${x} to ${y}` : `${x}–${y}`
}
