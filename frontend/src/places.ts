import { LANG } from './lang'
// Demo fields and typed/pasted location parsing for the field picker.
// Everything here runs in the browser; nothing is sent anywhere.

export const DEMO_POINTS = [
  { key: 'konya', label: 'Konya', lat: 37.6, lon: 32.75 },
  { key: 'punjab', label: LANG === 'en' ? 'Punjab' : 'Pencap', lat: 30.8, lon: 75.6 },
  { key: 'nakuru', label: 'Nakuru', lat: -0.25, lon: 36.15 },
]

// TKGM's public parcel query web site. Only linked (opened in a new tab): its
// terms forbid using its web services without permission (docs/DATA_SOURCES.md).
export const TKGM_PARSEL_URL = 'https://parselsorgu.tkgm.gov.tr/'

const NUM = '(-?\\d{1,3}\\.\\d+)'
const SEP = '\\s*(?:,|%2C)\\s*'

// Coordinates inside common map links, e.g.
//   https://www.google.com/maps/@37.6,32.75,15z
//   https://www.google.com/maps?q=37.6,32.75 · .../dir/?api=1&destination=37.6,32.75
//   https://www.openstreetmap.org/#map=15/37.6/32.75 · ?mlat=37.6&mlon=32.75
//   geo:37.6,32.75
const LINK_PATTERNS: RegExp[] = [
  new RegExp(`@${NUM}${SEP}${NUM}`),
  new RegExp(`[?&](?:q|query|ll|sll|destination|daddr|center)=(?:loc:)?${NUM}${SEP}${NUM}`, 'i'),
  new RegExp(`geo:${NUM}${SEP}${NUM}`, 'i'),
  new RegExp(`map=\\d+(?:\\.\\d+)?/${NUM}/${NUM}`),
  new RegExp(`mlat=${NUM}&mlon=${NUM}`),
]

// Short share links (maps.app.goo.gl, goo.gl/maps) hide the coordinates.
export function isShortMapLink(text: string): boolean {
  return /(maps\.app\.goo\.gl|goo\.gl\/maps)/i.test(text)
}

// "37.60, 32.75", "37.6 32.75", "37,60 32,75", "37,60; 32,75", or a map link → lat, lon.
export function parseCoords(text: string): { lat: number; lon: number } | null {
  const s = text.trim()
  const m = s.match(/^(-?\d{1,3}(?:[.,]\d+)?)\s*(?:[;,]\s*|\s+)(-?\d{1,3}(?:[.,]\d+)?)$/)
  if (m) return pair(m[1].replace(',', '.'), m[2].replace(',', '.'))
  for (const re of LINK_PATTERNS) {
    const l = s.match(re)
    if (l) return pair(l[1], l[2])
  }
  return null
}

function pair(a: string, b: string): { lat: number; lon: number } | null {
  const lat = Number(a)
  const lon = Number(b)
  return Number.isFinite(lat) && Number.isFinite(lon) ? { lat, lon } : null
}
