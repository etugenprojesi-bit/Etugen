// Stage 6: plain-Turkish texts for things the API sends in English, and the
// learning layer ("Bu ne demek?"). The UI is Turkish only, for farmers.
// Explanations are general and qualitative; numbers only where docs/METHOD.md has them.

import { num } from './i18n'
import { LANG } from './lang'

// --- learning layer -------------------------------------------------------------

export interface Term {
  title: string
  text: string
}

const termsTR: Record<string, Term> = {
  et0: {
    title: 'Buharlaşma ihtiyacı (ET0)',
    text: 'Havanın topraktan ve bitkiden ne kadar su çektiği. Sıcak, güneşli, rüzgârlı ve kuru günlerde artar. Kısa, sulanan bir çim için hesaplanır; her ürünün ihtiyacı bunun bir katıdır.',
  },
  water_balance: {
    title: 'Su dengesi',
    text: 'Yağış eksi buharlaşma ihtiyacı. Eksi ise o ay yağış yetmiyor demektir: bitki topraktaki suyu kullanır ya da sulama gerekir.',
  },
  aridity: {
    title: 'Yağış / buharlaşma oranı',
    text: 'Yıllık yağışın yıllık buharlaşma ihtiyacına oranı. 1’den ne kadar küçükse bölge o kadar kurak.',
  },
  frost: {
    title: 'Don günü',
    text: 'Gece en düşük sıcaklığın 0 °C’nin altına indiği gün. Çiçek açmış ya da yeni çıkmış bitkiye zarar verebilir.',
  },
  lethal_cold: {
    title: 'Öldürücü soğuk',
    text: 'Bitkinin kışın ölebileceği sıcaklık; makalelerden alınmıştır. Hesaptaki sıcaklık havadır, toprak yüzeyi değil: kar örtüsü bitkiyi korur.',
  },
  hot: {
    title: 'Sıcak gün',
    text: 'Gündüz en yüksek sıcaklığın bitkiye zarar vermeye başladığı eşiği geçtiği gün. Özellikle çiçeklenmede verimi düşürür.',
  },
  heavy_rain: {
    title: 'Şiddetli yağış günü',
    text: 'Bu yerin en kuvvetli yağışlı günlerinin %5’i. Böyle günlerde çıplak toprak kolay aşınır, tarla su basabilir.',
  },
  ndvi: {
    title: 'Bitki örtüsü (NDVI)',
    text: 'Uydunun ölçtüğü yeşillik. 0’a yakın: çıplak toprak; 1’e yaklaştıkça sık ve sağlıklı bitki. Bir yılın eğrisi, ekim ve hasat zamanını gösterir.',
  },
  smap: {
    title: 'Toprak nemi (SMAP)',
    text: 'NASA’nın SMAP uydusunun ölçtüğü üst ~5 cm toprağın nemi. Yaklaşık 9 km’lik alanın ortalamasıdır, tarlanızın tam değeri değildir.',
  },
  soil_model: {
    title: 'Kök bölgesi nemi (model)',
    text: 'Bilgisayar modelinin hesapladığı kök bölgesi nemi. Uydu ölçümü değildir; yalnız iniş-çıkışları karşılaştırın.',
  },
  rain_sources: {
    title: 'POWER, IMERG ve CHIRPS yağışı',
    text: 'POWER ve IMERG NASA verisidir. POWER ~50 km’lik bir hücrenin model-ölçüm karışımı; IMERG uydu ve yağış istasyonlarından, ~11 km. CHIRPS (kamu malı) uydu ölçümünü yer istasyonlarıyla birleştirir, ~5 km. Konya’da istasyon ölçümünün tam olduğu aylarda POWER istasyondan %63, IMERG %39 fazla; CHIRPS istasyonla neredeyse aynı. Bu yüzden POWER’ın CHIRPS’ten %30’dan fazla ıslak olduğu yerlerde uyarı gösterilir.',
  },
  score: {
    title: 'Puan',
    text: 'Ürünün bu yerde, o ekim tarihinde, son 25 yılın iklimiyle ne kadar iyi yetiştiği (0–100). Sıcaklık, su, sezon süresi ve güneş ışığından hesaplanır. Verim tahmini değildir.',
  },
  bad_year: {
    title: 'Kötü yıl',
    text: 'Her 5 yıldan en kötü 1’inde beklenen puan. Ortalama iyi ama kötü yıl düşükse ürün risklidir.',
  },
  confidence: {
    title: 'Güven',
    text: 'Sonuca ne kadar güvenilebileceği. İklim verisi ~50 km’lik hücreden geldiği için “yüksek” hiç verilmez. “Düşük” ise sonucu mutlaka yerel bir uzmana sorun.',
  },
  rotation: {
    title: 'Ürün rotasyonu (münavebe)',
    text: 'Aynı tarlada yıllar içinde farklı ürünlerin sırayla ekilmesi. Hastalık ve zararlı döngüsünü kırar, toprağı korur, gübre ihtiyacını azaltabilir.',
  },
  legume: {
    title: 'Baklagil ve azot',
    text: 'Mercimek, nohut, fasulye, yonca gibi baklagiller havadaki azotu toprağa bağlar. Ardından ekilen tahıl daha az azotlu gübreyle yetişebilir.',
  },
  cover_crop: {
    title: 'Örtü bitkisi',
    text: 'İki ana ürün arasında boş kalan toprağa ekilen bitki. Toprağı yağmur ve rüzgâra karşı korur. Bu uygulama örtü bitkilerini henüz hesaplamıyor.',
  },
  fallow: {
    title: 'Nadas',
    text: 'Tarlanın bir yıl ekilmeden bırakılması. Kurak yerlerde toprakta su biriktirmek için yapılır. Uygulama biriken suyu FAO-56 yöntemiyle ve toprak haritasıyla tahmin eder ve sonraki ürünün su puanına ekler; bu bir model hesabıdır, ölçüm değildir.',
  },
  erosion: {
    title: 'Erozyon',
    text: 'Toprağın yağmur ve rüzgârla taşınması. Eğim arttıkça ve toprak çıplak kaldıkça artar.',
  },
  risk_colour: {
    title: 'Kırmızı ve mavi',
    text: 'Her ay, aynı ayın 25 yıllık ortalamasıyla karşılaştırılır. Kırmızı: o ay normalden daha riskli (ör. daha çok don, daha az yağış). Mavi: normalden iyi. Renk ne kadar koyuysa fark o kadar büyük.',
  },
  scenario: {
    title: 'Senaryo',
    text: '“Hava 2 derece daha sıcak olsaydı ne olurdu?” sorusunu sınar. Geçmiş 25 yılın her gününe aynı farkı ekler. Gelecek tahmini değildir.',
  },
}

// --- API text in plain Turkish --------------------------------------------------

const literatureTR: Record<string, string> = {
  zhao2019: 'Zhao vd. 2019 (SIMPLE bitki modeli)',
  luo2011: 'Luo 2011',
  sadras2021: 'Sadras vd. 2021',
  maldaner2018: 'Maldaner vd. 2018',
  costa2005: 'Costa vd. 2005',
  chauhan2023: 'Chauhan vd. 2023',
  boonsprins1993: 'Boons-Prins vd. 1993 (WOFOST bitki modeli)',
  ecocrop: 'FAO ECOCROP (genel aralıklar; lisansı belirtilmemiş)',
}

export function evidenceText(key: string, value: string): string {
  if (LANG === 'en') return evidenceTextEN(key, value)
  switch (key) {
    case 'climate':
      return 'NASA POWER günlük iklim verisi, 25 yıl (~50 km’lik hücre)'
    case 'water_use':
      return 'FAO-56 bitki katsayıları (yerel nem ve rüzgâra göre düzeltilmiş) × buharlaşma ihtiyacı'
    case 'stages':
      return `FAO-56 Tablo 11 (${value.replace(/^FAO-56 Table 11 row:\s*/, '')})`
    case 'temperature': {
      const m = value.match(/^(\w+) \(verified against original: (True|False)\)/)
      if (!m) return value
      return `${literatureTR[m[1]] ?? m[1]}${m[2] === 'True' ? '' : ' — asıl makaleyle henüz karşılaştırılmadı'}`
    }
    case 'season_length':
      return value.startsWith('thermal') ? 'Sıcaklık toplamına göre (derece-gün)' : 'FAO-56’daki sabit sezon süresi'
    default:
      return value
  }
}

const rotationEvidenceTR: Record<string, string> = {
  'NASA POWER daily 25 years (~0.5° grid): temperature, rain, ET0 (FAO-56)':
    'NASA POWER günlük iklim verisi, 25 yıl (~50 km): sıcaklık, yağış, buharlaşma ihtiyacı (FAO-56)',
  'FAO-56 Tables 11, 12, 22: stages, Kc, root depth': 'FAO-56 Tablo 11, 12, 22: gelişme evreleri, bitki katsayısı, kök derinliği',
  'Crop temperature response: literature (see crop_sources)': 'Ürünlerin sıcaklık sınırları: bilimsel makaleler',
  'Rules: family sequence, legume-cereal, cover in heavy-rain months (docs/METHOD.md)':
    'Kurallar: aynı aileden ürün art arda gelmez, baklagilden sonra tahıl, şiddetli yağış aylarında toprak örtülü',
}

export const powerSource = LANG === 'en' ? 'NASA POWER daily climate data' : 'NASA POWER günlük iklim verisi'
export const powerResolution = LANG === 'en' ? '~50 km cell' : '~50 km’lik hücre'

// Risk thresholds and sources, by layer id.
export function riskSourceText(id: string, threshold: number | null, assumption: boolean, cropName: string | null): string {
  if (LANG === 'en') return riskSourceTextEN(id, threshold, assumption, cropName)
  switch (id) {
    case 'frost_days':
      return 'En düşük sıcaklık 0 °C altında.'
    case 'lethal_cold_days':
      return `En düşük sıcaklık ${num(threshold, 1)} °C altında (${cropName ?? 'ürün'} için; kaynak: Luo 2011).`
    case 'hot_days':
      return assumption
        ? `En yüksek sıcaklık ${num(threshold)} °C üstünde (genel eşik, varsayım). Ürün seçerseniz ürüne özel eşik kullanılır.`
        : `En yüksek sıcaklık ${num(threshold)} °C üstünde (${cropName ?? 'ürün'} için; kaynak: Zhao vd. 2019).`
    case 'heavy_rain_days':
      return `Günlük yağış ${num(threshold)} mm üstünde (bu yerin en kuvvetli yağışlı günlerinin %5’i).`
    case 'water_balance_mm':
      return 'Aylık yağış eksi buharlaşma ihtiyacı (NASA POWER, FAO-56).'
    case 'smap_sm':
      return 'NASA SMAP uydusu, ~9 km; 2015’ten beri. Uydu ölçümü olduğu için senaryo değiştirmez.'
    case 'ndvi':
      return 'NASA MODIS uydusu, 1 km. Uydu ölçümü olduğu için senaryo değiştirmez.'
    default:
      return ''
  }
}

// An oriented anomaly in words instead of standard deviations.
export function riskWords(z: number | null): string {
  if (LANG === 'en') return riskWordsEN(z)
  if (z === null) return 'karşılaştırma yok'
  if (z >= 2) return 'normalden çok daha riskli'
  if (z >= 1) return 'normalden riskli'
  if (z > -1) return 'normale yakın'
  if (z > -2) return 'normalden iyi'
  return 'normalden çok daha iyi'
}

const layerNamesTR: Record<string, string> = {
  ndvi: 'Bitki örtüsü (MODIS)',
  smap: 'Toprak nemi (SMAP)',
  imerg: 'Yağış (GPM IMERG)',
  slope: 'Eğim (NASADEM)',
}

// ---- English (lang.ts) ----------------------------------------------------------

const termsEN: Record<string, Term> = {
  et0: {
    title: 'Evaporation demand (ET0)',
    text: 'How much water the air draws from soil and plants. It rises on hot, sunny, windy and dry days. It is calculated for short, watered grass; each crop needs a multiple of it.',
  },
  water_balance: {
    title: 'Water balance',
    text: 'Rain minus evaporation demand. If it is negative, rain is not enough that month: the crop uses soil water or needs irrigation.',
  },
  aridity: {
    title: 'Rain / evaporation ratio',
    text: 'Annual rain divided by annual evaporation demand. The further below 1, the drier the area.',
  },
  frost: {
    title: 'Frost day',
    text: 'A day when the night-time minimum falls below 0 °C. It can harm flowering or newly emerged plants.',
  },
  lethal_cold: {
    title: 'Killing cold',
    text: 'The temperature at which the crop can die in winter, taken from papers. The calculation uses air temperature, not the soil surface: snow cover protects plants.',
  },
  hot: {
    title: 'Hot day',
    text: 'A day when the daytime maximum passes the threshold at which heat starts to harm the crop. It lowers yields especially at flowering.',
  },
  heavy_rain: {
    title: 'Heavy-rain day',
    text: 'The 5 % heaviest rain days of this place. On such days bare soil washes away easily and fields can flood.',
  },
  ndvi: {
    title: 'Vegetation (NDVI)',
    text: 'Greenness measured by satellite. Near 0: bare soil; towards 1: dense, healthy plants. A year’s curve shows sowing and harvest time.',
  },
  smap: {
    title: 'Soil moisture (SMAP)',
    text: 'Moisture of the top ~5 cm of soil measured by NASA’s SMAP satellite. It is the average of about 9 km, not the exact value of your field.',
  },
  soil_model: {
    title: 'Root-zone wetness (model)',
    text: 'Root-zone wetness calculated by a computer model. It is not a satellite measurement; compare only the ups and downs.',
  },
  rain_sources: {
    title: 'POWER, IMERG and CHIRPS rainfall',
    text: 'POWER and IMERG are NASA data. POWER mixes model and measurements over a ~50 km cell; IMERG comes from satellites and rain gauges, ~11 km. CHIRPS (public domain) combines satellite data with ground stations, ~5 km. At Konya, in months with complete station records, POWER is 63 % and IMERG 39 % above the station; CHIRPS is almost the same. So a warning appears where POWER is more than 30 % wetter than CHIRPS.',
  },
  score: {
    title: 'Score',
    text: 'How well the crop grows here, at that sowing date, with the climate of the last 25 years (0–100). It comes from temperature, water, season length and sunlight. It is not a yield forecast.',
  },
  bad_year: {
    title: 'Bad year',
    text: 'The score expected in the worst 1 of every 5 years. If the average is good but the bad year is low, the crop is risky.',
  },
  confidence: {
    title: 'Confidence',
    text: 'How far the result can be trusted. Because climate data come from a ~50 km cell, “high” is never given. If it says “low”, always ask a local expert.',
  },
  rotation: {
    title: 'Crop rotation',
    text: 'Growing different crops one after another on the same field over the years. It breaks disease and pest cycles, protects the soil and can reduce fertiliser needs.',
  },
  legume: {
    title: 'Legumes and nitrogen',
    text: 'Legumes such as lentil, chickpea, bean and alfalfa fix nitrogen from the air into the soil. A cereal sown after them can grow with less nitrogen fertiliser.',
  },
  cover_crop: {
    title: 'Cover crop',
    text: 'A plant sown on soil left empty between two main crops. It protects the soil from rain and wind. This app does not calculate cover crops yet.',
  },
  fallow: {
    title: 'Fallow',
    text: 'Leaving the field unsown for a year. In dry areas it is done to store water in the soil. The app estimates the stored water with the FAO-56 method and a soil map and adds it to the next crop’s water score; this is a model calculation, not a measurement.',
  },
  erosion: {
    title: 'Erosion',
    text: 'Soil carried away by rain and wind. It increases with slope and when the soil stays bare.',
  },
  risk_colour: {
    title: 'Red and blue',
    text: 'Each month is compared with the 25-year mean of the same month. Red: riskier than normal (e.g. more frost, less rain). Blue: better than normal. The darker the colour, the bigger the difference.',
  },
  scenario: {
    title: 'Scenario',
    text: 'Tests the question “what if the weather were 2 degrees warmer?”. It adds the same change to every day of the past 25 years. It is not a forecast.',
  },
}

const literatureEN: Record<string, string> = {
  zhao2019: 'Zhao et al. 2019 (SIMPLE crop model)',
  luo2011: 'Luo 2011',
  sadras2021: 'Sadras et al. 2021',
  maldaner2018: 'Maldaner et al. 2018',
  costa2005: 'Costa et al. 2005',
  chauhan2023: 'Chauhan et al. 2023',
  boonsprins1993: 'Boons-Prins et al. 1993 (WOFOST crop model)',
  ecocrop: 'FAO ECOCROP (general ranges; no licence stated)',
}

function evidenceTextEN(key: string, value: string): string {
  switch (key) {
    case 'climate':
      return 'NASA POWER daily climate data, 25 years (~50 km cell)'
    case 'water_use':
      return 'FAO-56 crop coefficients (adjusted to local humidity and wind) × evaporation demand'
    case 'stages':
      return `FAO-56 Table 11 (${value.replace(/^FAO-56 Table 11 row:\s*/, '')})`
    case 'temperature': {
      const m = value.match(/^(\w+) \(verified against original: (True|False)\)/)
      if (!m) return value
      return `${literatureEN[m[1]] ?? m[1]}${m[2] === 'True' ? '' : ' — not yet checked against the original paper'}`
    }
    case 'season_length':
      return value.startsWith('thermal') ? 'From the temperature sum (degree-days)' : 'Fixed season length from FAO-56'
    default:
      return value
  }
}

function riskSourceTextEN(id: string, threshold: number | null, assumption: boolean, cropName: string | null): string {
  switch (id) {
    case 'frost_days':
      return 'Minimum temperature below 0 °C.'
    case 'lethal_cold_days':
      return `Minimum temperature below ${num(threshold, 1)} °C (for ${cropName ?? 'the crop'}; source: Luo 2011).`
    case 'hot_days':
      return assumption
        ? `Maximum temperature above ${num(threshold)} °C (general threshold, assumption). Choose a crop to use its own threshold.`
        : `Maximum temperature above ${num(threshold)} °C (for ${cropName ?? 'the crop'}; source: Zhao et al. 2019).`
    case 'heavy_rain_days':
      return `Daily rain above ${num(threshold)} mm (the 5 % heaviest rain days of this place).`
    case 'water_balance_mm':
      return 'Monthly rain minus evaporation demand (NASA POWER, FAO-56).'
    case 'smap_sm':
      return 'NASA SMAP satellite, ~9 km; since 2015. A satellite measurement, so the scenario does not change it.'
    case 'ndvi':
      return 'NASA MODIS satellite, 1 km. A satellite measurement, so the scenario does not change it.'
    default:
      return ''
  }
}

function riskWordsEN(z: number | null): string {
  if (z === null) return 'no comparison'
  if (z >= 2) return 'much riskier than normal'
  if (z >= 1) return 'riskier than normal'
  if (z > -1) return 'close to normal'
  if (z > -2) return 'better than normal'
  return 'much better than normal'
}

const rotationEvidenceEN: Record<string, string> = {
  'NASA POWER daily 25 years (~0.5° grid): temperature, rain, ET0 (FAO-56)':
    'NASA POWER daily climate data, 25 years (~50 km): temperature, rain, evaporation demand (FAO-56)',
  'FAO-56 Tables 11, 12, 22: stages, Kc, root depth': 'FAO-56 Tables 11, 12, 22: growth stages, crop coefficient, root depth',
  'Crop temperature response: literature (see crop_sources)': 'Crop temperature limits: scientific papers',
  'Rules: family sequence, legume-cereal, cover in heavy-rain months (docs/METHOD.md)':
    'Rules: no two crops of the same family in a row, cereal after legume, soil covered in heavy-rain months',
}

const layerNamesEN: Record<string, string> = {
  ndvi: 'Vegetation (MODIS)',
  smap: 'Soil moisture (SMAP)',
  imerg: 'Rainfall (GPM IMERG)',
  slope: 'Slope (NASADEM)',
}

export const terms = LANG === 'en' ? termsEN : termsTR
export const rotationEvidence = LANG === 'en' ? rotationEvidenceEN : rotationEvidenceTR
export const layerNames = LANG === 'en' ? layerNamesEN : layerNamesTR
