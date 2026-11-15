import type { Analysis, Irrigation, RiskResponse, RotationRequest, RotationResponse, Satellite, Variant } from './types'

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown, message: string) {
    super(message)
    this.status = status
    this.detail = detail
  }
}

function variantParams(v: Variant): Record<string, string> {
  return {
    precip_source: v.precipSource,
    delta_t: String(v.deltaT),
    delta_p: String(v.deltaP),
    explore_sowing: String(v.exploreSowing),
  }
}

export async function fetchAnalysis(
  lat: number,
  lon: number,
  irrigation: Irrigation,
  variant: Variant,
  signal?: AbortSignal,
): Promise<Analysis> {
  const params = new URLSearchParams({ lat: lat.toFixed(4), lon: lon.toFixed(4), irrigation, ...variantParams(variant) })
  return request(`/api/analyze?${params}`, { signal })
}

export async function fetchRisk(lat: number, lon: number, crop: string, variant: Variant, signal?: AbortSignal): Promise<RiskResponse> {
  const params = new URLSearchParams({ lat: lat.toFixed(4), lon: lon.toFixed(4), ...variantParams(variant) })
  if (crop) params.set('crop', crop)
  return request(`/api/risk?${params}`, { signal })
}

export async function fetchSatellite(lat: number, lon: number, signal?: AbortSignal): Promise<Satellite> {
  const params = new URLSearchParams({ lat: lat.toFixed(4), lon: lon.toFixed(4) })
  return request(`/api/satellite?${params}`, { signal })
}

export async function fetchRotations(body: RotationRequest, signal?: AbortSignal): Promise<RotationResponse> {
  return request('/api/rotations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
}

async function request<T>(url: string, init: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(url, init)
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw e
    throw new ApiError(0, null, 'network')
  }
  if (!res.ok) {
    let detail: unknown = null
    try {
      detail = (await res.json()).detail
    } catch {
      /* body was not JSON */
    }
    throw new ApiError(res.status, detail, `http_${res.status}`)
  }
  return res.json()
}
