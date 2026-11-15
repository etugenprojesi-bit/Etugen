// English interface texts: the same shape as the Turkish ones in i18n.ts (type Dict).
// Plain words, for farmers and international readers.

import type { Dict } from './i18n'
import { dateLabel, num, pct, yearsLabel } from './i18n'

const MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const t: Dict['t'] = {
  appName: 'Etügen',
  tagline: 'Crop-rotation decision support with NASA data',
  tapHint: 'Tap your field on the map',
  useMyLocation: 'Use my location',
  locating: 'Finding your location…',
  locationFailed:
    'Could not get your location. The browser did not allow it or the connection is not secure (location needs HTTPS). You can choose on the map instead.',
  demoPoints: 'Example points',
  irrigation: 'Irrigation',
  irrigationOptions: { none: 'None', limited: 'Limited', full: 'Yes' },
  irrigationHelp: {
    none: 'Rain only',
    limited: 'Assumption: half of the rain deficit is covered',
    full: 'No water limit',
  },
  analyze: 'Analyse',
  loading: 'Fetching 25 years of daily climate data from NASA POWER and calculating…',
  errors: {
    network: 'Could not reach the server. Check your internet connection or the backend server.',
    source: 'NASA POWER data could not be fetched and there is no saved data for this point. No result can be shown.',
    invalid: 'Invalid coordinates or parameters.',
    other: 'An unexpected error occurred.',
  },
  disclaimer:
    'This tool supports decisions; it does not replace the farmer’s judgement or local expertise. Check every result marked “Needs local check” with an agronomist.',
  dataOrigin: {
    network: 'Live data',
    cache: 'Cached data (real data fetched earlier)',
    demo_cache: 'Cached data — no network, saved demo data in use',
  },
  analysisPoint: 'Analysis point',
  roundedNote: 'Coordinates rounded to 0.05°',
  elevation: 'Elevation',
  profileTitle: 'Area profile',
  annual: {
    tmean: 'Mean temperature',
    precip: 'Annual rainfall',
    et0: 'Evaporation demand (ET0)',
    aridity: 'Rainfall / ET0',
    frost: 'Frost days (year)',
    hot: 'Hot days >35 °C (year)',
  },
  aridityClass: (ai: number) =>
    ai < 0.05 ? 'hyper-arid' : ai < 0.2 ? 'arid' : ai < 0.5 ? 'semi-arid' : ai < 0.65 ? 'dry sub-humid' : 'humid',
  trendsTitle: '25-year trends',
  trendNames: {
    tmean: 'Temperature',
    precip: 'Rainfall',
    et0: 'ET0',
    frost_days: 'Frost days',
    hot_days: 'Hot days',
    soil_wetness_root_model: 'Root-zone wetness (model)',
  } as Record<string, string>,
  perDecade: '/ 10 years',
  noSignificantTrend: 'No significant trend',
  trendNote: 'Mann-Kendall test, only p < 0.05 shown. Soil wetness comes from the MERRA-2 model, not from SMAP observations.',
  monthlyTitle: 'Monthly climate',
  precip: 'Rainfall (mm)',
  et0: 'ET0 (mm)',
  tmean: 'Temperature (°C)',
  calendarTitle: 'Calendar',
  calendarRows: { frost: 'Frost risk', water: 'Water balance', hot: 'Hot days' },
  calendarLegend: 'Darker = higher risk / deficit. ● good sowing month, ▬ season',
  cropsTitle: 'Crops',
  cropsIntro:
    'Sorted by the best sowing window. The dark part of the bar is the score expected even in a bad year (worst 20 %), the light part a normal year.',
  calendarNoCrops: 'No crop scores above 20 % here; the calendar shows only the climate rows.',
  units: { '°C': '°C', mm: 'mm', days: 'days', '0-1': '' } as Record<string, string>,
  evidenceLabels: {
    climate: 'Climate',
    water_use: 'Water use',
    stages: 'Growth stages',
    temperature: 'Temperature parameters',
    season_length: 'Season length',
  } as Record<string, string>,
  sowing: 'Sowing',
  harvest: 'Harvest',
  days: 'days',
  score: 'Score',
  badYear: 'bad year',
  failRate: 'Failed years',
  rainDeficit: 'Rain deficit',
  seasonRain: 'Season rainfall',
  waterNeed: 'Water need (ETc)',
  goodSowing: 'Good sowing dates',
  subscores: 'Sub-scores',
  temperature: 'Temperature',
  water: 'Water',
  duration: 'Season length',
  light: 'Sunlight',
  frostDays: 'Frost days in season',
  heatDays: 'Heat-stress days in season',
  confidence: 'Confidence',
  confidenceLevels: { low: 'Low', medium: 'Medium', unknown: 'Unknown' } as Record<string, string>,
  needsLocal: 'Needs local check',
  whyConfidence: 'What affects confidence',
  askExpert: 'Questions for a local expert',
  evidence: 'Evidence',
  nitrogenFixing: 'Fixes nitrogen',
  notSuitableTitle: 'Not suitable by the model',
  notSuitableNote: 'This is a model result, not a final verdict. Compare with local experience.',
  insufficientTitle: 'Missing data',
  insufficientNote: 'No sourced parameters for these crops yet; the model does not guess.',
  perennialTitle: 'Perennial (not evaluated in rotations)',
  missingFields: {
    temperature_limits: 'temperature limits',
    heat_thresholds: 'heat-stress thresholds',
    season_stages: 'season stages',
    fao56_kc: 'FAO-56 crop coefficient',
    climate_record_too_short: 'enough climate record',
  } as Record<string, string>,
  months: ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'],
  monthNames: MONTHS_SHORT,
  newAnalysis: 'Choose another point',
  source: 'Data source',
  seconds: 's',
}

const reasonTexts: Dict['reasonTexts'] = {
  coarse_climate_grid: () => 'Climate data come from a ~50 km grid (NASA POWER); conditions in the field can differ.',
  unverified_transcription: () =>
    'Temperature parameters were transcribed second-hand and not yet checked against the original paper.',
  no_heat_threshold: () => 'Heat-stress thresholds for this crop are unknown.',
  fixed_season_length: () => 'Season length is a fixed FAO-56 reference value, not adjusted to local temperature.',
  ecocrop_general_ranges: () =>
    'Temperature limits are general ranges from FAO ECOCROP (no variety or regional differences; no licence stated, FAO asked).',
  analogy_assumption: () => 'Some values of this crop are not in FAO-56; they come from a similar crop (assumption).',
  regional_variant: (p) =>
    `Season length is adjusted to this region’s varieties (${p.name}): derived from sowing-to-maturity days observed in a 2023-24 trial at Punjab Agricultural University (one season, one site).`,
  calendar_conflict: (p) =>
    `The model cannot grow this crop around the usual local sowing day (${dateLabel(String(p.planting))}, GGCMI), so the best time outside the local calendar is shown. Check with local knowledge.`,
  high_variability: (p) => `Results vary a lot from year to year (normal year ${pct(p.median)}, bad year ${pct(p.p20)}).`,
  frequent_failure: (p) => `The season often fails (share of failed years: ${pct(p.fail_rate)}).`,
  model_unsuitable: (p) =>
    ({
      does_not_mature:
        'The crop does not mature within its typical season (too cool, or the model’s reference variety does not fit local varieties).',
      temperature: 'Temperatures limit the crop in every sowing window.',
      water: 'Rain does not meet the crop’s water need in any sowing window.',
    })[String(p.limiting_factor)] ?? '',
  missing_parameters: (p) =>
    'Missing parameters: ' + ((p.missing as string[]) ?? []).map((m) => t.missingFields[m] ?? m).join(', '),
}

const questionTexts: Dict['questionTexts'] = {
  irrigation_available: (p) =>
    `Is irrigation water available in the dry part of the season? The model estimates a rain deficit of about ${num(p.deficit)} mm.`,
  frost_damage: (p) =>
    `Frost occurs on ~${num(p.days)} days in a typical season. Do local varieties of this crop survive frost at that stage?`,
  heat_at_flowering: (p) =>
    `There are ~${num(p.days)} days above ${num(p.t)} °C in the season. Does heat at flowering reduce yields locally?`,
  local_variety: (p) => `Which local varieties are used? Does their season match the model’s ${num(p.days)} days?`,
  local_experience: () => 'Is this crop grown in the area? When is it sown and harvested?',
  short_season_variety: () =>
    'Are there local varieties with a shorter season? The model’s thermal time comes from a single reference variety.',
}

const tr: Dict['tr'] = {
  plannerTitle: 'Plan a rotation',
  plannerIntro:
    'Enter your priorities and limits; your current rotation (if you know it) and the 3 best alternatives are compared side by side.',
  priorities: 'Priorities (0 = not important, 5 = very important)',
  priorityNames: {
    water: 'Saving water',
    soil: 'Soil structure / organic matter',
    erosion: 'Less erosion',
    nitrogen: 'Less nitrogen / fertiliser',
    income: 'Extra income / market',
    forage: 'Animal feed',
  } as Record<string, string>,
  constraints: 'Limits',
  equipment: 'Equipment',
  equipmentOptions: {
    no_root_harvester: 'I have no root/tuber harvester',
    no_paddy: 'I cannot flood fields (paddy rice)',
  } as Record<string, string>,
  marketCrops: 'Crops with a market (for the income score; if you choose none, income stays “unknown”)',
  excludedCrops: 'Crops I do not want to grow',
  currentRotation: 'My current rotation',
  dontKnow: 'I don’t know',
  year: 'Year',
  secondCrop: '+ second crop (same year)',
  none: '—',
  llmExplain: 'Simplify the explanation with AI (if the server has an API key; no location is sent)',
  compare: 'Compare rotations',
  comparing: 'Calculating rotations…',
  privacyNote: 'These inputs are used only for this calculation and are not stored on the server.',
  kinds: { current: 'Current rotation', reference: 'Reference: one crop', recommended: 'Option' } as Record<string, string>,
  total: 'Total score',
  fallow: 'Fallow',
  storedWater: (mm: number) => `~${num(mm)} mm water in the soil at sowing (model)`,
  cycleYears: (n: number) => `${n}-year cycle`,
  irrigationNeed: 'Water not covered by rain',
  perYear: 'mm/year',
  subscoreNames: {
    suitability: 'Yield suitability',
    climate_risk: 'Bad-year resilience',
    water: 'Water',
    soil: 'Soil health (proxy)',
    erosion: 'Erosion protection',
    nitrogen: 'Nitrogen',
    income: 'Income (your input)',
    forage: 'Animal feed',
    diversity: 'Family diversity',
  } as Record<string, string>,
  unknownValue: 'unknown',
  why: 'Why',
  benefits: 'Possible benefits',
  risks: 'Risks',
  dataGaps: 'Data gaps',
  opportunities: 'Opportunities',
  evidenceTitle: 'Evidence and method',
  explanationTitle: 'Summary',
  llmNote: 'Simplified with AI; the numbers come from the card’s data.',
  noRecommendation: 'No rotation follows the rules. Try relaxing the limits or changing the irrigation option.',
  usableCrops: (n: number, min: number) => `${n} crops could be used in the model (score at least ${Math.round(min * 100)} %).`,
  firstCutOnly: (names: string) =>
    `${names} are not in the recommendations: for these cut forage crops only the first cut can be calculated, so how many months they occupy the field is unknown.`,
}

const rotationTexts: Dict['rotationTexts'] = {
  is_current: () => 'The rotation you entered, scored with the same rules.',
  is_reference: () =>
    'For comparison: the single best crop every year (monoculture). Enter your current rotation to compare with it instead.',
  legume_before_cereal: () => 'Legume before cereal: less nitrogen fertiliser may be needed.',
  pest_break: () => 'Different plant families in a row break pest and disease cycles.',
  roots_structure: () => 'Deep roots and long-living roots support soil structure and water infiltration (proxy).',
  cover_in_rainy_months: () => 'The soil is covered in most heavy-rain months.',
  double_cropping: () => 'Two crops in one year: the season is fully used.',
  market_crops: () => 'Most crops are ones you marked as having a market.',
  fallow_break: () => 'A fallow year breaks the cereal sequence and the pest cycle.',
  same_family_consecutive: (p, name) =>
    `Rule broken: crops of the same family in a row (${(p.crops as string[]).map(name).join(' → ')}).`,
  same_crop_consecutive_years: (p, name) => `Rule broken: ${(p.crops as string[]).map(name).join(', ')} in consecutive years.`,
  seasons_overlap: (p, name) => `The seasons of the two crops in the same year overlap (${(p.crops as string[]).map(name).join(' + ')}).`,
  water_deficit: (p) => `Rain covers only a small part of the crops’ water need (~${num(p.irrigation_need_mm_per_year)} mm deficit per year).`,
  frequent_failure: (p) => `At least one crop often fails (share of failed years: ${pct(p.max_fail_rate)}).`,
  bare_soil: (p) =>
    `${yearsLabel(p.years)} the field is empty from ${t.monthNames[Number(p.start_month) - 1]} for ${num(p.months)} months (bare soil).`,
  soil_proxy: () => 'The soil-health score is a proxy (root depth, months with living roots); data on crops’ organic-matter input are not available yet.',
  no_market_data: () => 'No market/price data: mark the crops that have a market to get an income score.',
  no_slope: () => 'No slope data: the erosion score assumes a 9 % slope.',
  slope_is_area: (p) => `The slope (${num(p.slope_pct, 1)} %) is the median of the surrounding ~5 km cell (NASADEM), not of your field.`,
  unmodelled_current_crops: (p, name) =>
    `Some crops in your rotation cannot be modelled yet: ${(p.crops as string[]).map(name).join(', ')}.`,
  fallow_not_modelled: () =>
    'Soil data could not be fetched, so the water stored during fallow is not calculated; the fallow year counts as “no production”.',
  fallow_stores_water: (p, name) =>
    `In the fallow year about ${num(p.stored_mm_median)} mm of water is stored in the soil (${pct(p.storage_efficiency_median)} of the fallow-period rain; ` +
    `${num(p.stored_mm_p20)}–${num(p.stored_mm_p80)} mm in most years). This water carries over to the next ${name(String(p.crop_id))}: ` +
    `score ${pct(p.score_median_with)} instead of ${pct(p.score_median_without)}. A model calculation (FAO-56), not a measurement.`,
  soil_water_model: () =>
    'The water stored in the soil between crops is a model calculation (FAO-56, SoilGrids 250 m soil map). ' +
    'Assumptions: dry soil at harvest, no runoff, weeds and stubble ignored.',
  cover_crop_window: (p, name) =>
    `${yearsLabel(p.years)} a ${num(p.months)}-month gap from ${t.monthNames[Number(p.start_month) - 1]}: a chance for a cover or catch crop (` +
    `such as ${(p.candidates as string[]).map(name).join(', ')}; not modelled yet, choose locally).`,
  cover_crop_local: (p) =>
    `Which cover crop can grow in the ${num(p.months)}-month empty period starting in ${t.monthNames[Number(p.start_month) - 1]}?`,
  drainage: () => 'Does this field have drainage or waterlogging problems?',
  fallow_management: () => 'Do you leave stubble during fallow? How do you control weeds, and when do you plough?',
}

const ts: Dict['ts'] = {
  title: 'Satellite data',
  intro:
    'NDVI (MODIS), soil moisture (SMAP), rainfall (GPM IMERG) and slope (NASADEM) are fetched for this point from Earth Engine and brought to the same monthly step as NASA POWER.',
  load: 'Load satellite data',
  loading: 'Fetching satellite time series from Earth Engine… At a new point the first time can take 1–3 minutes.',
  error: 'Satellite data could not be fetched',
  origin: {
    earth_engine: 'Live data (Earth Engine)',
    cache: 'Cached data (real data fetched earlier)',
    demo_cache: 'Cached data — Earth Engine not reachable, saved demo data in use',
    network: 'Live data',
    none: 'No data',
  } as Record<string, string>,
  precipTitle: 'Rainfall: NASA POWER and GPM IMERG',
  verdict: {
    agree: 'The two sources agree on the annual mean (difference under 15 %).',
    moderate_difference: 'Moderate difference between the two sources (15–30 %).',
    large_difference: 'Large difference between the two sources (over 30 %): interpret results with care.',
    imerg_zero: 'IMERG rainfall is zero; no comparison possible.',
  } as Record<string, string>,
  annualMean: 'Annual mean',
  relDiff: (rel: number) => `POWER is ${Math.round(Math.abs(rel) * 100)} % ${rel >= 0 ? 'higher' : 'lower'} than IMERG`,
  correlation: 'Year-to-year agreement (r)',
  trend: 'Rainfall trend',
  notSignificant: 'not significant',
  trendNotConfirmed: (y: number, a: number, b: number) =>
    `The rainfall trend in POWER is not confirmed by IMERG. The difference between the sources jumps after ${y} (POWER/IMERG ratio ${num(a, 2)} → ${num(b, 2)}). The trend most likely comes from data processing; do not read it as climate change.`,
  trendNotConfirmedNoStep: 'The rainfall trend in POWER is not confirmed by IMERG (the difference between the sources changes over time).',
  homogeneous: 'The difference between the sources is stable over time (no break).',
  footprintNote: 'POWER is a ~50 km cell average, IMERG ~11 km; neither is a field measurement. Only years complete in both sources are compared.',
  monthlyTitle: 'Monthly means: vegetation and soil moisture',
  ndvi: 'NDVI (MODIS)',
  smap: 'Soil moisture — SMAP observation (m³/m³)',
  gwet: 'Root-zone wetness — MERRA-2 model (0–1)',
  smapMerge: (m: { days_006: number; days_from_005: number; offset_006_minus_005: number | null; r: number | null }) =>
    `SMAP 006 main series (${num(m.days_006)} days); ${num(m.days_from_005)} missing days filled from version 005` +
    (m.offset_006_minus_005 === null
      ? ' (little overlap, no offset correction).'
      : ` (offset ${num(m.offset_006_minus_005, 3)} m³/m³${m.r === null ? '' : `, r = ${num(m.r, 3)}`}).`),
  smapVsModel:
    'SMAP measures the top ~5 cm; the POWER value is a model for the root zone. Compare the ups and downs, not the values.',
  slopeTitle: 'Slope and erosion',
  slopeText: (pctv: number, rel: number) =>
    `Median slope in the surrounding ~5 km cell: ${num(pctv, 1)} %. The RUSLE slope factor is ${num(rel, 2)} times that of the standard 9 % plot. The erosion score of the rotation cards uses this factor.`,
  slopeMissing: 'No slope data; the erosion score assumes a 9 % slope.',
  slopeFlat:
    'This is a flat plain: the elevation data come in 1 m steps and cannot measure small slopes, so the slope is taken from the elevation range of the cell (assumption).',
  patternsTitle: 'Finding patterns: three approaches compared',
  patternsIntro: (n: number) =>
    `${n} years of NDVI curves and climate summaries. The sample is small: flagged years are questions to ask, not findings.`,
  methodZ: 'A · z-score / threshold (classical statistics)',
  methodZText: (thr: number) => `Years whose NDVI total or peak is more than ${num(thr, 1)} standard deviations from the mean:`,
  methodIF: 'B · Isolation Forest (machine learning)',
  methodIFText: 'Years found “unusual” from the shape of the NDVI curve together with the climate:',
  methodKM: 'B · k-means NDVI clustering (machine learning)',
  kmStatus: {
    ok: 'Clear cluster structure',
    no_clear_structure: 'No clear cluster structure (low silhouette); clusters are weak',
    too_few_years: 'Not enough years',
  } as Record<string, string>,
  cluster: (n: number, peak: number, peaks: number) =>
    `${n} years · peak ${t.monthNames[peak - 1]} · ${peaks === 2 ? 'two seasons' : peaks === 1 ? 'one season' : `${peaks} peaks`}`,
  regimeShift: (y: number) =>
    `Clusters split by time: the seasonal pattern changed after ${y}. Did the crop pattern or irrigation change? Check locally.`,
  methodAN: 'C · Analogue years (classical statistics)',
  analogText: (y: number, years: string) => `Years whose climate is most like ${y}: ${years}.`,
  analogSkill: (s: number) =>
    s > 0.1
      ? `Years with a similar climate predict NDVI ${Math.round(s * 100)} % better than the long-term mean (leave-one-out test).`
      : 'Years with a similar climate do not predict NDVI better than the long-term mean: here management (irrigation, crop choice) may matter more than climate.',
  agreement: 'Agreement of A and B',
  both: 'Both',
  onlyZ: 'z-score only',
  onlyIF: 'Isolation Forest only',
  none: 'none',
  yearCtx: (z: number, p: number, tm: number) => `NDVI z ${num(z, 1)} · rainfall z ${num(p, 1)} · temperature z ${num(tm, 1)}`,
  precipNotHomogeneous: 'Note: POWER rainfall is not homogeneous at this point; methods using climate (Isolation Forest, analogue years) are affected.',
}

const tk: Dict['tk'] = {
  scenarioTitle: 'Rainfall source and scenario',
  precipSource: 'Rainfall data',
  precipOptions: { power: 'NASA POWER', imerg: 'GPM IMERG', chirps: 'CHIRPS' } as Record<string, string>,
  precipHelp: {
    power: 'Default: NASA POWER daily rainfall (~50 km cell).',
    imerg:
      'Each month’s POWER daily rain is scaled to that month’s IMERG total (the daily pattern stays from POWER). Months without IMERG keep POWER.',
    chirps:
      'Each month’s POWER daily rain is scaled to that month’s CHIRPS total (the daily pattern stays from POWER). CHIRPS combines satellite data with ground stations (~5 km).',
  } as Record<string, string>,
  deltaT: 'Temperature change',
  deltaP: 'Rainfall change',
  exploreSowing: 'Also try other sowing times',
  exploreSowingHelp:
    'Normally the best sowing time is chosen within 45 days before or after the usual local sowing day (GGCMI crop calendar). ' +
    'If you tick this, the model tries the whole year; useful for asking how sowing time could shift with a changing climate.',
  localCalendar: (plant: string, mature: string) => `Usual here: sowing ${plant}, harvest ~${mature} (GGCMI)`,
  calendarIgnored: 'whole year tried',
  calendarRainfedFallback: 'no record for irrigated farming, rainfed calendar used',
  calendarGapFilled: 'no observation in this cell, estimated calendar',
  calendarConflict: 'the model cannot grow it at this date, whole year tried',
  outsideCalendar: (sow: string, score: string) =>
    `The model gives a higher score to sowing on ${sow} (${score}), but this date is outside the usual local sowing time.`,
  apply: 'Apply',
  reset: 'Reset',
  pending: 'Changes not applied yet.',
  scenarioNote:
    'A scenario is a sensitivity test, not a climate forecast: the same temperature change is added to every day of the observed 25 years and rainfall is changed by the same share; humidity, wind and sunshine stay the same, ET0 is recalculated.',
  bannerScenario: (dt: number, dp: number) =>
    `Scenario: ${dt > 0 ? '+' : ''}${num(dt, 1)} °C, rainfall ${dp > 0 ? '+' : ''}${num(dp)} %`,
  bannerImerg: (used: number, power: number) => `Rainfall: scaled to IMERG (${num(used)} mm per year; POWER ${num(power)} mm)`,
  bannerChirps: (used: number, power: number) => `Rainfall: scaled to CHIRPS (${num(used)} mm per year; POWER ${num(power)} mm)`,
  rainTooWet: (power: number, chirps: number) =>
    `NASA POWER rainfall may be too high here: ${num(power)} mm per year, while station-blended CHIRPS gives ${num(chirps)} mm. ` +
    'Rainfed results may be optimistic; try CHIRPS under “Rainfall source”.',
  rainTooWetShort: 'POWER rainfall may be too high here',
  imergGaps: (n: number, range: string | null) => `${n} months without IMERG data${range ? ` (${range.replace('..', ' – ')})` : ''}; POWER used in these months.`,
  vsBaseline: 'without scenario',
  riskTitle: 'Risk layers',
  riskIntro:
    'Each month is compared with the 25-year mean of the same calendar month. Red: the month is riskier than normal; blue: less risky. Values are the time series of the analysis point, not a map.',
  riskLoad: 'Load risk layers',
  riskLoading: 'Calculating risk layers… At a new point satellite data can take 1–3 minutes the first time.',
  riskError: 'Risk layers could not be fetched',
  cropFor: 'Crop for thresholds',
  generic: 'General (no crop chosen)',
  year: 'Year',
  annualCol: 'Year',
  normal: 'normal',
  layers: {
    frost_days: 'Frost days',
    lethal_cold_days: 'Killing-cold days',
    hot_days: 'Hot days',
    heavy_rain_days: 'Heavy-rain days',
    water_balance_mm: 'Water balance',
    smap_sm: 'Soil moisture (satellite)',
    ndvi: 'Vegetation (NDVI)',
  } as Record<string, string>,
  units: { days: 'days', mm: 'mm', 'm³/m³': 'm³/m³', NDVI: '' } as Record<string, string>,
  notes: {
    scenario_applies_to_climate_only:
      'The scenario applies to the climate layers only. SMAP and NDVI are observations and are shown as they are.',
    generic_heat_threshold: 'No crop chosen: the general 35 °C threshold is used for hot days (assumption). Choose a crop to use its sourced threshold.',
    lethal_cold_is_air_temperature:
      'Killing cold: 2 m air temperature of a ~50 km cell, not the temperature at the plant’s crown; snow cover protects plants.',
  } as Record<string, string>,
  missingLayer: (ids: string) => `Missing layer: ${ids}. Satellite data could not be fetched.`,
  compareTitle: 'Compare layers',
  compareIntro: 'See two layers side by side on the same scale. The 0 line is normal; above is riskier than normal, below is better.',
  layerA: 'Layer A',
  layerB: 'Layer B',
  chartYear: (y: number) => `${y} — months`,
  chartAll: 'All years — annual',
  riskAxis: 'risk',
  noData: 'no data',
  legendWorse: 'riskier than normal',
  legendBetter: 'better than normal',
}

const tu: Dict['tu'] = {
  tabs: { field: 'Field', summary: 'Summary', rotation: 'Rotation', details: 'Details' },
  help: 'How to use',
  close: 'Close',
  pickTitle: 'Choose your field',
  pickHint: 'Drag the map with your finger. Bring the cross in the middle over your field, then press the yellow “Choose this point” button. Tapping the map brings that spot to the middle.',
  pickHere: 'Choose this point',
  searchLabel: 'Search a place',
  searchPlaceholder: 'Village, district, 37.6, 32.75 or a map link',
  search: 'Search',
  searching: 'Searching…',
  noResults: 'Nothing found. Try another spelling or a province/district name.',
  searchFailed: 'Search failed (maybe no internet). You can choose on the map or type coordinates.',
  searchNote: 'To search a place name, the name you type is sent to OpenStreetMap; your location is not sent. Coordinates or map links you paste are sent nowhere.',
  shortLink:
    'Short share links do not contain the location. Open the link in the browser, copy the long address from the address bar and paste it here.',
  linkWithoutCoords: 'No location found in this link. Type the village name or choose on the map.',
  tkgmTitle: 'Find it by your land-registry block/parcel number (Türkiye)',
  tkgmSteps: [
    'Open the “Parcel Query” site of the Turkish Land Registry (TKGM) with the button below.',
    'Enter province, district, village, block and parcel number. The site shows your parcel on a map.',
    'Come back here. Type the village name in the box above and search, or paste the location link from TKGM into the box.',
    'Find your parcel on the satellite map, bring the cross over it and press “Choose this point”.',
  ],
  tkgmOpen: 'Open TKGM Parcel Query',
  tkgmNote:
    'TKGM’s own site opens in a new tab. What you type there does not come to this app, and this app sends nothing to TKGM.',
  coordOutOfRange: 'Invalid coordinates: latitude must be −90…90, longitude −180…180.',
  orDivider: 'or',
  examples: 'Example fields',
  mapSatellite: 'Satellite',
  mapStreet: 'Map',
  satelliteNote: 'The satellite image is from 2016 (Sentinel-2); your field may look different today.',
  irrigationQuestion: 'Can you irrigate your field?',
  irrigationOptions: { none: 'No', limited: 'A little', full: 'Yes' },
  irrigationHelp: {
    none: 'Only rain water is counted.',
    limited: 'Assumption: you can irrigate half of the water that rain does not provide.',
    full: 'Water is assumed not to be a problem.',
  },
  chosenPlace: 'Chosen place',
  changeField: 'Change',
  noField: 'First choose your field in the “Field” section.',
  loading: 'Looking at 25 years of NASA weather data…',
  bestTitle: 'What grows best on this field',
  bestIntro: 'Based on the weather of the last 25 years. The score is not a yield forecast; it is for comparing crops with each other.',
  outOf: '/ 100',
  badYearShort: 'In a bad year',
  sowShort: 'Sowing',
  harvestShort: 'Harvest',
  goodMonths: 'Good sowing months',
  askLocal: 'Needs local check: ask an expert',
  questionsTitle: 'Ask an agronomist',
  noCrops:
    'The model found no suitable crop here. This is not a final verdict: compare with local experience; all crops are under “Details”.',
  risksTitle: 'What to watch',
  risksIntro: 'Monthly means of the last 25 years. Coloured boxes show risky months.',
  riskFrost: 'Frost',
  riskFrostText: 'In these months there is frost in at least 1 of every 2 years.',
  riskHot: 'Extreme heat',
  riskHotText: 'In these months at least 1 day per month on average goes above 35 °C.',
  riskDry: 'Not enough rain',
  riskDryText: 'In these months rain is less than the water the air draws from the soil. The crop uses soil water or needs irrigation.',
  riskNone: 'none',
  next: 'Next step',
  goRotation: 'Which crop in which year? — Rotation',
  goDetails: 'All crops, risk table and satellite data — Details',
  detailsIntro:
    'Expert view: the technical details of the calculations. Press the “?” next to a term to read what it means.',
  detailsSections: {
    data: 'Data source and location',
    scenario: 'Rainfall source and scenario',
    climate: 'Climate of the area',
    crops: 'All crops',
    risk: 'Risk table by month',
    satellite: 'Satellite data',
  },
  helpSteps: [
    ['Choose your field', 'Drag the map, bring the cross over your field and press “Choose this point”. You can also type a village name or press “Use my location”.'],
    ['Say if you irrigate', 'If you can irrigate your field, choose “Yes” or “A little”. The results change with it.'],
    ['Read the summary', 'The “Summary” shows the crops that grow best here, when to sow them and the months to watch.'],
    ['Plan your rotation', 'In “Rotation” you can compare which crop to grow in which year.'],
    ['Ask an expert', 'This app helps; the decision is yours. Ask an agronomist or the local agriculture office about results marked “Ask an expert”.'],
  ] as [string, string][],
  helpScores:
    'Score: out of 100. A higher score means the crop fits the weather here better. The “bad year” score is the score expected in the worst of every 5 years.',
  helpOffline: 'Without internet, your last results stay on your phone for 7 days.',
  helpGuide: 'Detailed user guide (Turkish): docs/KULLANIM_KILAVUZU.md (project documents).',
}

const te: Dict['te'] = {
  chooseTitle: 'How do you want to use the app?',
  chooseIntro: 'You can change this at any time with the button at the top.',
  easyName: 'Easy mode',
  easyText: 'Just tell me what to do: what to sow, when to sow it, how much water it needs.',
  expertName: 'Expert mode',
  expertText: 'Let me choose priorities and limits and look at all the charts.',
  switchToExpert: 'Expert',
  switchToEasy: 'Easy',
  planTab: 'My plan',
  planTitle: 'Recommended plan for your field',
  planIntro: (years: number) =>
    `A ${years}-year cycle: after year ${years}, go back to year 1. Below is what to sow each year and when.`,
  computing: 'Preparing your plan… (can take half a minute)',
  noPlan: 'No plan that follows the rules was found for this place. You can look at the details in expert mode.',
  option: (i: number, n: number) => `Option ${i} of ${n}`,
  otherOption: 'Show another option',
  year: (i: number) => `Year ${i}`,
  fallowYear: 'Fallow: do not sow the field this year, let the soil store rain water.',
  sow: (date: string) => `Sowing: around ${date}`,
  harvest: (date: string) => `Harvest: about ${date}`,
  prepare: 'Prepare the soil before sowing, at the usual time in your area.',
  waterOkRain: 'Water: rain is usually enough in a normal year.',
  waterNeedNone: (mm: number) =>
    `Water: in a normal year rain falls about ${mm} mm short (~${mm} tonnes of water per decare). Without irrigation the yield may drop.`,
  waterNeedIrr: (mm: number) =>
    `Water: about ${mm} mm of irrigation water is needed over the season (~${mm} tonnes per decare). More in dry years.`,
  stored: (mm: number) => `About ${mm} mm of water is stored in the soil in the empty period before; it helps the crop.`,
  forage: 'Can be used as animal feed.',
  legume: 'Leaves nitrogen in the soil: the next crop may need less nitrogen fertiliser.',
  idleTitle: 'Months the field is empty',
  monthNames: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
  idle: (from: string, months: number) => `${months} months from ${from}`,
  idleAdvice:
    'The field is empty in these months. If you like, you can let your animals graze the stubble, or sow a cover crop such as vetch so the soil is not bare. The app does not calculate how much grazing this gives; ask experienced farmers in your village or the agriculture office how many animals can graze.',
  flat: 'Your land is flat: little risk of rain washing the soil away (erosion), so the plan does not count it.',
  scoreLine: (p: number) => `Suitability score of this plan: ${p}/100`,
  lowConfidence: 'This plan is a model calculation; ask a local agronomist before you use it.',
  why: 'Why this plan?',
  moreDetails: 'Switch to expert mode for a detailed comparison.',
}

const tf: Dict['tf'] = {
  title: 'Mark the corners of your field (optional)',
  intro: 'If you mark the corners, the area of your field is calculated and the plan tells you how many tonnes of water your whole field needs.',
  drawingHint: 'Tap the corners of your field on the map one after another (at least 3). Then press “Done”.',
  start: 'Mark the corners',
  edit: 'Edit the corners',
  undo: 'Remove last corner',
  clear: 'Clear',
  done: 'Done, this is my field',
  area: (da: number) => `Area: about ${num(da, da < 10 ? 1 : 0)} decares`,
  privacy: 'The corners stay on your phone and are sent nowhere.',
  irrigation: (lead: string, from: string, to: string, days: number, mm: number) =>
    `${lead} (${from} – ${to}, the period of highest water need): if it does not rain, every ${days} days, about ${mm} mm each time (~${mm} tonnes per decare).`,
  irrigationOnce: (lead: string, from: string, to: string, mm: number) =>
    `${lead} (${from} – ${to}, the period of highest water need): if this period stays dry, one irrigation of about ${mm} mm (~${mm} tonnes per decare) is enough.`,
  irrigationLead: 'Irrigation',
  irrigationLeadIfPossible: 'If you can irrigate',
  irrigationRainy: 'Rain is usually enough in this period; irrigate at the interval above in weeks without rain.',
  wholeField: (tons: number) => `For your whole field: about ${num(tons)} tonnes.`,
  seasonWholeField: (tons: number) => `Over the season, about ${num(tons)} tonnes of extra water for your field.`,
  rowsTitle: 'Which direction should the rows run?',
  rowsContour: (axis: string, down: string) =>
    `The land slopes down towards the ${down}. Sow the rows across the slope, that is ${axis} (the lines in the drawing): rain carries less soil away and more water soaks in.`,
  rowsFlat: 'Your land is flat: rain does not wash the soil away, so sow the rows in whatever direction is easiest for you.',
  rowsUnknown: 'The direction of the slope is unknown; no row-direction advice.',
  rowsNote: 'The slope direction comes from the general slope of the surrounding ~5 km (NASA NASADEM); if your own field slopes differently, follow your field.',
  sketchNorth: 'N',
  sketchTitle: 'Your field (north is up)',
}

export const EN: Dict = { t, tr, ts, tk, tu, te, tf, reasonTexts, questionTexts, rotationTexts }
