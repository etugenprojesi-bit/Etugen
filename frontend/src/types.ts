// Shape of GET /api/analyze (backend/app/api/analyze.py).

export type Irrigation = 'none' | 'limited' | 'full'
export type PrecipSource = 'power' | 'imerg' | 'chirps'

// Rainfall source + scenario sliders (stage 5), shared by all requests.
export interface Variant {
  precipSource: PrecipSource
  deltaT: number
  deltaP: number
  exploreSowing: boolean
}

export interface LocalCalendar {
  system: 'rainfed' | 'irrigated'
  planting: string
  maturity: string
  data_source: string
  window_days: number
  fallback_from?: 'rainfed' | 'irrigated' | null
  gap_filled?: boolean
}

export interface VariantInfo {
  precip_source: PrecipSource
  delta_t_c: number
  delta_p_pct: number
  scenario_active: boolean
  note?: string
  imerg_rescale?: {
    months_total: number
    months_rescaled: number
    months_without_imerg: number
    months_without_imerg_range: string | null
    months_imerg_rain_without_power_rain: number
    imerg_rain_not_placed_mm: number
    factor_median: number | null
    annual_mean_mm: { power: number; used: number }
    years: string
  }
  chirps_rescale?: {
    source: string
    months_rescaled: number
    months_without_source: number
    months_without_source_range: string | null
    factor_median: number | null
    annual_mean_mm: { power: number; used: number }
    years: string
  }
}

// POWER vs CHIRPS mean annual rain at the point (plan_konya_yagis.md).
export interface RainCheck {
  status: 'ok' | 'missing'
  error?: string
  years?: string
  power_mm?: number
  chirps_mm?: number
  ratio?: number | null
  limit?: number
  power_may_be_too_wet?: boolean
}

export interface Item {
  code: string
  text: string
  params: Record<string, unknown>
}

export interface Confidence {
  level: 'low' | 'medium' | 'unknown'
  needs_local_validation: boolean
  reasons: Item[]
  questions: Item[]
}

export interface BestWindow {
  sowing: string
  harvest_median: string
  season_days_median: number
  season_months: number[]
  n_seasons: number
  matured_share: number
  score_median: number
  score_p20: number
  fail_rate: number
  temperature_score_median: number
  water_score_median: number
  duration_factor_median: number
  light_factor_median: number
  etc_mm_median: number
  precip_mm_median: number
  rain_deficit_mm_median: number
  frost_days_median: number
  lethal_days_median: number | null
  heat_days_median: number | null
}

export type CropStatus = 'evaluated' | 'not_suitable_by_model' | 'insufficient_data' | 'perennial_not_evaluated'

export interface CropResult {
  id: string
  name: { en: string; tr: string }
  scientific: string
  family: string
  group: string
  nitrogen_fixing: boolean
  status: CropStatus
  confidence: Confidence
  best_window?: BestWindow
  best_window_outside_calendar?: BestWindow | null
  local_calendar?: LocalCalendar | null
  calendar_rule?: boolean
  calendar_conflict?: boolean
  good_sowing_dates?: string[]
  evidence?: Record<string, string>
  method?: string[]
  reason?: { code: string; text: string }
  missing?: string[]
  baseline?: { status: CropStatus; score_median: number | null; sowing: string | null }
}

export interface MonthClimate {
  month: number
  tmean_c: number
  tmax_c: number
  tmin_c: number
  precip_mm: number
  et0_mm: number
  water_balance_mm: number
  frost_days: number
  frost_probability: number
  hot_days: number
  heavy_rain_days: number | null
  soil_wetness_root_model: number
}

export interface Trend {
  slope_per_decade: number | null
  unit: string
  p_value: number
  significant_5pct: boolean
  n_years: number
}

export interface DataSource {
  id: string
  name: string
  api_version: string | null
  resolution: string
  period: string
  origin: 'network' | 'cache' | 'demo_cache'
  is_cached: boolean
  is_demo_cache: boolean
  missing_days: number
}

// Shape of POST /api/rotations (backend/app/api/rotations.py).

export type PriorityKey = 'water' | 'soil' | 'erosion' | 'nitrogen' | 'income' | 'forage'

export interface RotationRequest {
  lat: number
  lon: number
  irrigation: Irrigation
  precip_source: PrecipSource
  delta_t: number
  delta_p: number
  explore_sowing: boolean
  priorities: Record<PriorityKey, number>
  constraints: { excluded_crops: string[]; equipment_limits: string[]; market_crops: string[] }
  current_rotation: string[][] | null
  explain: 'template' | 'llm'
  lang: 'tr' | 'en'
}

export interface RotationSlot {
  crop_id: string
  name: { en: string; tr: string }
  family: string
  group: string
  nitrogen_fixing: boolean
  sowing: string
  harvest: string
  season_days: number
  months: number[]
  score_median: number
  score_p20: number
  fail_rate: number
  rain_deficit_mm: number
  score_median_without_stored_water: number
  irrigation_schedule?: null | {
    mid_season_start: string
    mid_season_end: string
    mid_season_days: number
    etc_mm_per_day: number
    rain_mm_per_day: number
    taw_mm: number
    p: number
    depth_mm: number
    interval_days: number
  }
  stored_soil_water: null | {
    n_fallow_years: number
    stored_mm_median: number
    stored_mm_p20: number
    stored_mm_p80: number
    storage_efficiency_median: number | null
    gap_days_median: number
    gap_rain_mm_median: number
    deep_percolation_mm_median: number
  }
}

export interface Subscore {
  value: number | null
  kind: string
  weight: number
  [detail: string]: unknown
}

export interface RotationCard {
  id: string
  kind: 'current' | 'reference' | 'recommended'
  years: RotationSlot[][]
  missing_slots: { year: number; crop_id: string; status: string }[]
  total: number
  subscores: Record<string, Subscore>
  unknown_subscores: string[]
  irrigation_need_mm_per_year: number | null
  rule_violations: { code: string; crops: string[] }[]
  fallow_periods: { year: number; start_month: number; months: number }[]
  why: Item[]
  benefits: Item[]
  risks: Item[]
  data_gaps: Item[]
  opportunities: Item[]
  confidence: { level: 'low' | 'medium' | 'unknown'; needs_local_validation: boolean }
  questions: Item[]
  evidence: string[]
}

export interface RotationResponse {
  cards: RotationCard[]
  n_recommended: number
  usable_crops: string[]
  min_crop_score: number
  excluded_by_constraints: string[]
  not_used_first_cut_only?: string[]
  slope?: {
    status: string
    flat_terrain?: boolean
    slope_pct_median?: number
    fall?: { downhill_azimuth_deg: number; contour_rows_azimuth_deg: number; plane_slope_pct: number } | null
  }
  erosion_ignored_flat_terrain?: boolean
  explanation: null | { mode: 'template'; reason: string } | { mode: 'llm'; model: string; texts: Record<string, string>; note: string }
  disclaimer: string
  timing_s: number
}

export interface Analysis {
  query: {
    lat: number
    lon: number
    irrigation: Irrigation
    precip_source: PrecipSource
    delta_t: number
    delta_p: number
    explore_sowing: boolean
  }
  analysis_point: { lat: number; lon: number; elevation_m: number; note: string }
  disclaimer: string
  variant: VariantInfo
  data_sources: DataSource[]
  climate: {
    annual: {
      tmean_c: number
      precip_mm: number
      et0_mm: number
      aridity_index_p_over_et0: number
      frost_days: number
      hot_days: number
    }
    monthly: { years: number; heavy_rain_threshold_mm: number | null; months: MonthClimate[] }
    trends: Record<string, Trend>
    rain_check?: RainCheck
  }
  crops: CropResult[]
  timing_s: number
}

// Shape of GET /api/satellite (backend/app/api/satellite.py), stage 3.

export interface TrendStat {
  slope_mm_per_decade: number | null
  p_value: number
  significant_5pct: boolean
  n_years: number
}

export interface PrecipComparison {
  status: 'ok' | 'insufficient_overlap' | 'missing'
  period?: string
  common_full_years?: number
  annual_mean_mm?: { power: number; imerg: number }
  power_relative_difference?: number | null
  verdict?: 'agree' | 'moderate_difference' | 'large_difference' | 'imerg_zero'
  correlation?: { annual: number; monthly: number }
  trend?: { power: TrendStat; imerg: TrendStat; same_direction_and_significance: boolean }
  difference_series?: {
    trend: TrendStat
    change_point: {
      p_value: number
      significant_5pct: boolean
      step: null | {
        last_year_before: number
        mean_diff_before_mm: number
        mean_diff_after_mm: number
        ratio_before: number
        ratio_after: number
      }
    }
    homogeneous: boolean
  }
  power_trend_confirmed_by_imerg?: boolean | null
  annual?: { year: number; power_mm: number; imerg_mm: number }[]
}

export interface SlopeInfo {
  status: 'ok' | 'missing'
  slope_deg_median?: number
  slope_pct_median?: number
  slope_deg_p90?: number | null
  rusle_s?: number
  relative_s?: number
  flat_terrain?: boolean
  source?: string
  error?: string
}

export interface PatternResult {
  status: 'ok' | 'missing_ndvi'
  n_years?: number
  zscore?: { threshold: number; anomalous_years: number[] }
  kmeans?: {
    status: 'ok' | 'no_clear_structure' | 'too_few_years'
    k?: number
    silhouette?: number
    clusters?: { cluster: number; years: number[]; mean_curve: number[]; peak_month: number; n_peaks: number }[]
    regime_shift?: null | { last_year_before: number; p_value: number }
  }
  isolation_forest?: { anomalous_years: number[] }
  analogs?: {
    status: string
    target_year?: number
    target_analogs?: { year: number; distance: number; ndvi_integral: number }[]
    target_ndvi_integral?: number
    loo?: { mae_analog: number; mae_climatology: number; skill: number | null }
  }
  agreement?: { both: number[]; only_zscore: number[]; only_isolation_forest: number[]; jaccard: number | null }
  flagged_year_context?: { year: number; found_by: string[]; z_ndvi_integral: number; z_precip: number; z_tmean: number }[]
  notes?: string[]
}

export interface SatelliteSource {
  id: string
  name: string
  origin: string
  layers?: Record<string, { dataset: string; footprint: string; available: boolean }>
  errors?: Record<string, string>
}

export interface SmapMerge {
  overlap_days: number
  offset_006_minus_005: number | null
  r: number | null
  days_006: number
  days_from_005: number
  first: string | null
  last: string | null
}

export interface Satellite {
  analysis_point: { lat: number; lon: number }
  data_sources: SatelliteSource[]
  labels: Record<string, string>
  slope: SlopeInfo
  monthly_climatology: Record<string, number | null>[]
  precipitation_comparison: PrecipComparison
  soil_moisture: { status: 'ok' | 'missing'; merge?: SmapMerge; correlation_with_model?: number | null }
  patterns: PatternResult
  timing_s: number
}

// Shape of GET /api/risk (backend/app/api/risk.py), stage 5.

export interface RiskLayer {
  id: string
  label: string
  unit: string
  kind: 'count' | 'amount' | 'anomaly'
  type: string
  source: string
  observation: boolean
  scenario_applies: boolean
  higher_is_worse: boolean
  threshold: { value: number | null; unit: string; source: string } | null
  assumption: boolean
  climatology: (number | null)[]
  climatology_years: number[]
  values: (number | null)[][]
  risk_z: (number | null)[][]
  annual: (number | null)[]
  annual_risk_z: (number | null)[]
  annual_baseline_mean: number | null
  annual_how: 'sum' | 'mean'
}

export interface RiskResponse {
  analysis_point: { lat: number; lon: number }
  variant: VariantInfo
  crop: { id: string; name: { en: string; tr: string } } | null
  crop_options: { id: string; name: { en: string; tr: string }; t_heat: number | null; lethal_min: number | null }[]
  data_sources: { id: string; origin: string; errors?: Record<string, string> }[]
  years: number[]
  layers: RiskLayer[]
  missing_layers: string[]
  risk_z_flag: number
  min_years: number
  z_cap: number
  notes: string[]
}
