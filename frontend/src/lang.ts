// Interface language. Turkish is the default (the app is written for farmers in
// Türkiye); English is a switch for international users and judges. The choice is
// kept in local storage; `?lang=en` in the address opens the app in English.
export type Lang = 'tr' | 'en'

const KEY = 'etugen-lang'

function initial(): Lang {
  try {
    const q = new URLSearchParams(window.location.search).get('lang')
    if (q === 'en' || q === 'tr') {
      localStorage.setItem(KEY, q)
      return q
    }
    return localStorage.getItem(KEY) === 'en' ? 'en' : 'tr'
  } catch {
    return 'tr'
  }
}

export const LANG: Lang = initial()

/** Switch language: texts are chosen once at start, so the page reloads. */
export function setLang(l: Lang): void {
  try {
    localStorage.setItem(KEY, l)
  } catch {
    /* private window: only the URL parameter works there */
  }
  const url = new URL(window.location.href)
  url.searchParams.set('lang', l)
  window.location.replace(url.toString())
}

/** A crop or place name object from the API ({ en, tr }) in the interface language. */
export function nameIn(n: { en?: string; tr?: string } | Record<string, string>): string {
  const v = n as Record<string, string | undefined>
  return v[LANG] ?? v.tr ?? v.en ?? ''
}
