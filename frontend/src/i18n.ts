// All user-facing text lives here: Turkish (default, plain words for farmers) and
// English (`i18n.en.ts`, the same shape, checked by the compiler). Backend reasons and
// questions carry a stable `code`; unknown codes fall back to the English API text.

import { EN } from './i18n.en'
import { LANG } from './lang'
import type { Item } from './types'

const tTR = {
  appName: 'Etügen',
  tagline: 'NASA verileriyle ürün rotasyonu karar desteği',
  tapHint: 'Haritada tarlanıza dokunun',
  useMyLocation: 'Konumumu kullan',
  locating: 'Konum alınıyor…',
  locationFailed:
    'Konum alınamadı. Tarayıcı izin vermedi ya da bağlantı güvenli değil (konum için HTTPS gerekir). Haritaya dokunarak seçebilirsiniz.',
  demoPoints: 'Örnek noktalar',
  irrigation: 'Sulama',
  irrigationOptions: { none: 'Yok', limited: 'Sınırlı', full: 'Var' },
  irrigationHelp: {
    none: 'Sadece yağış',
    limited: 'Varsayım: yağış açığının yarısı karşılanır',
    full: 'Su kısıtı yok',
  },
  analyze: 'Analiz et',
  loading: 'NASA POWER’dan 25 yıllık günlük iklim verisi alınıyor ve hesaplanıyor…',
  errors: {
    network: 'Sunucuya ulaşılamadı. İnternet bağlantınızı ya da arka uç sunucusunu kontrol edin.',
    source: 'NASA POWER verisi alınamadı ve bu nokta için kayıtlı veri yok. Sonuç gösterilemiyor.',
    invalid: 'Geçersiz koordinat veya parametre.',
    other: 'Beklenmeyen bir hata oluştu.',
  },
  disclaimer:
    'Bu araç destek amaçlıdır; çiftçinin yargısının ve yerel uzmanlığın yerine geçmez. “Yerel doğrulama gerekli” işaretli her sonucu bir ziraat uzmanıyla kontrol edin.',
  dataOrigin: {
    network: 'Canlı veri',
    cache: 'Önbellek verisi (daha önce çekilmiş gerçek veri)',
    demo_cache: 'Önbellek verisi — ağ yok, kayıtlı demo verisi kullanılıyor',
  },
  analysisPoint: 'Analiz noktası',
  roundedNote: 'Koordinatlar 0,05°’ye yuvarlandı',
  elevation: 'Rakım',
  profileTitle: 'Bölge profili',
  annual: {
    tmean: 'Ortalama sıcaklık',
    precip: 'Yıllık yağış',
    et0: 'Buharlaşma ihtiyacı (ET0)',
    aridity: 'Yağış / ET0',
    frost: 'Don günü (yıl)',
    hot: 'Sıcak gün >35 °C (yıl)',
  },
  aridityClass: (ai: number): string =>
    ai < 0.05 ? 'aşırı kurak' : ai < 0.2 ? 'kurak' : ai < 0.5 ? 'yarı kurak' : ai < 0.65 ? 'yarı nemli-kuru' : 'nemli',
  trendsTitle: '25 yıllık eğilimler',
  trendNames: {
    tmean: 'Sıcaklık',
    precip: 'Yağış',
    et0: 'ET0',
    frost_days: 'Don günleri',
    hot_days: 'Sıcak günler',
    soil_wetness_root_model: 'Kök bölgesi nemi (model)',
  } as Record<string, string>,
  perDecade: '/ 10 yıl',
  noSignificantTrend: 'Anlamlı eğilim yok',
  trendNote: 'Mann-Kendall testi, p < 0,05 olanlar gösteriliyor. Toprak nemi MERRA-2 modelinden gelir, SMAP gözlemi değildir.',
  monthlyTitle: 'Aylık iklim',
  precip: 'Yağış (mm)',
  et0: 'ET0 (mm)',
  tmean: 'Sıcaklık (°C)',
  calendarTitle: 'Takvim',
  calendarRows: { frost: 'Don riski', water: 'Su dengesi', hot: 'Sıcak günler' },
  calendarLegend: 'Koyu renk = daha yüksek risk / açık. ● iyi ekim ayı, ▬ sezon',
  cropsTitle: 'Ürünler',
  cropsIntro:
    'En iyi ekim dönemine göre sıralı. Çubuğun koyu kısmı kötü bir yılda (en kötü %20) bile beklenen puan, açık kısmı normal yıl.',
  calendarNoCrops: 'Bu noktada puanı %20’nin üstünde olan ürün yok; takvimde yalnızca iklim satırları gösteriliyor.',
  units: { '°C': '°C', mm: 'mm', days: 'gün', '0-1': '' } as Record<string, string>,
  evidenceLabels: {
    climate: 'İklim',
    water_use: 'Su kullanımı',
    stages: 'Gelişme evreleri',
    temperature: 'Sıcaklık parametreleri',
    season_length: 'Sezon süresi',
  } as Record<string, string>,
  sowing: 'Ekim',
  harvest: 'Hasat',
  days: 'gün',
  score: 'Puan',
  badYear: 'kötü yıl',
  failRate: 'Başarısız yıl',
  rainDeficit: 'Yağış açığı',
  seasonRain: 'Sezon yağışı',
  waterNeed: 'Su ihtiyacı (ETc)',
  goodSowing: 'İyi ekim tarihleri',
  subscores: 'Alt puanlar',
  temperature: 'Sıcaklık',
  water: 'Su',
  duration: 'Sezon süresi',
  light: 'Güneş ışığı',
  frostDays: 'Sezonda don günü',
  heatDays: 'Sezonda sıcak stres günü',
  confidence: 'Güven',
  confidenceLevels: { low: 'Düşük', medium: 'Orta', unknown: 'Bilinmiyor' } as Record<string, string>,
  needsLocal: 'Yerel doğrulama gerekli',
  whyConfidence: 'Güveni etkileyenler',
  askExpert: 'Yerel uzmana sorulacaklar',
  evidence: 'Kanıt',
  nitrogenFixing: 'Azot bağlar',
  notSuitableTitle: 'Model uygun bulmadı',
  notSuitableNote: 'Bu bir model sonucudur, kesin yargı değildir. Yerel deneyimle karşılaştırın.',
  insufficientTitle: 'Veri eksik',
  insufficientNote: 'Bu ürünler için kaynaklı parametre henüz yok; model tahmin yürütmüyor.',
  perennialTitle: 'Çok yıllık (rotasyon aşamasında değerlendirilecek)',
  missingFields: {
    temperature_limits: 'sıcaklık sınırları',
    heat_thresholds: 'sıcak stresi eşikleri',
    season_stages: 'sezon evreleri',
    fao56_kc: 'FAO-56 bitki katsayısı',
    climate_record_too_short: 'yeterli iklim kaydı',
  } as Record<string, string>,
  months: ['O', 'Ş', 'M', 'N', 'M', 'H', 'T', 'A', 'E', 'E', 'K', 'A'],
  monthNames: ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'],
  newAnalysis: 'Başka nokta seç',
  source: 'Veri kaynağı',
  seconds: 'sn',
}

const reasonTextsTR: Record<string, (p: Record<string, unknown>) => string> = {
  coarse_climate_grid: () => 'İklim verisi ~50 km’lik ızgaradan geliyor (NASA POWER); tarladaki koşullar farklı olabilir.',
  unverified_transcription: () =>
    'Sıcaklık parametreleri ikinci elden aktarıldı; orijinal makaleyle henüz karşılaştırılmadı.',
  no_heat_threshold: () => 'Bu ürün için sıcak stresi eşikleri bilinmiyor.',
  fixed_season_length: () => 'Sezon süresi sabit FAO-56 referans değeri; yerel sıcaklığa göre ayarlanmadı.',
  ecocrop_general_ranges: () =>
    'Sıcaklık sınırları FAO ECOCROP’un genel aralıkları (çeşit ve bölge farkı yok; lisansı belirtilmemiş, FAO’ya soruldu).',
  analogy_assumption: () =>
    'Bu ürünün bazı değerleri FAO-56’da yok; benzer bir üründen alındı (varsayım).',
  regional_variant: (p) =>
    `Sezon uzunluğu bu bölgenin çeşitlerine göre ayarlandı (${p.name_tr}): Pencap Tarım Üniversitesi’nin 2023-24 deneyinde gözlenen ekim–olgunlaşma günlerinden türetildi (tek sezon, tek yer).`,
  calendar_conflict: (p) =>
    `Bölgede yaygın ekim zamanında (${dateLabel(String(p.planting))}, GGCMI) model bu ürünü yetiştiremiyor; bu yüzden yerel takvimin dışındaki en iyi zaman gösteriliyor. Yerel bilgiyle kontrol edin.`,
  high_variability: (p) => `Sonuçlar yıldan yıla çok değişiyor (normal yıl ${pct(p.median)}, kötü yıl ${pct(p.p20)}).`,
  frequent_failure: (p) => `Sezon sık başarısız oluyor (başarısız yıl oranı: ${pct(p.fail_rate)}).`,
  model_unsuitable: (p) =>
    ({
      does_not_mature:
        'Ürün tipik sezon süresi içinde olgunlaşmıyor (çok serin ya da modeldeki referans çeşit yerel çeşitlere uymuyor).',
      temperature: 'Sıcaklıklar her ekim döneminde ürünü sınırlıyor.',
      water: 'Yağış hiçbir ekim döneminde ürünün su ihtiyacını karşılamıyor.',
    })[String(p.limiting_factor)] ?? '',
  missing_parameters: (p) =>
    'Eksik parametreler: ' + ((p.missing as string[]) ?? []).map((m) => t.missingFields[m] ?? m).join(', '),
}

const questionTextsTR: Record<string, (p: Record<string, unknown>) => string> = {
  irrigation_available: (p) =>
    `Sezonun kurak döneminde sulama suyu var mı? Model yaklaşık ${num(p.deficit)} mm yağış açığı hesaplıyor.`,
  frost_damage: (p) =>
    `Tipik bir sezonda ~${num(p.days)} gün don oluyor. Bu ürünün yerel çeşitleri o dönemde dona dayanıyor mu?`,
  heat_at_flowering: (p) =>
    `Sezonda ${num(p.t)} °C üstü ~${num(p.days)} sıcak gün var. Çiçeklenme döneminde sıcak verimi düşürüyor mu?`,
  local_variety: (p) => `Hangi yerel çeşitler kullanılıyor? Sezonları modeldeki ${num(p.days)} günle uyuşuyor mu?`,
  local_experience: () => 'Bu ürün yörede yetiştiriliyor mu? Ne zaman ekilip hasat ediliyor?',
  short_season_variety: () =>
    'Daha kısa sezonlu yerel çeşitler var mı? Modeldeki ısı toplamı tek bir referans çeşitten geliyor.',
}

const trTR = {
  plannerTitle: 'Rotasyon planla',
  plannerIntro:
    'Önceliklerinizi ve kısıtlarınızı girin; mevcut rotasyonunuz (biliyorsanız) ve en iyi 3 alternatif yan yana karşılaştırılır.',
  priorities: 'Öncelikler (0 = önemsiz, 5 = çok önemli)',
  priorityNames: {
    water: 'Su tasarrufu',
    soil: 'Toprak yapısı / organik madde',
    erosion: 'Erozyonu azaltma',
    nitrogen: 'Azot / gübre azaltma',
    income: 'Ek gelir / pazar',
    forage: 'Hayvan yemi',
  } as Record<string, string>,
  constraints: 'Kısıtlar',
  equipment: 'Ekipman',
  equipmentOptions: {
    no_root_harvester: 'Kök/yumru hasat makinem yok',
    no_paddy: 'Çeltik (su basma) imkânım yok',
  } as Record<string, string>,
  marketCrops: 'Pazarı olan ürünler (gelir puanı için; seçmezseniz gelir “bilinmiyor” kalır)',
  excludedCrops: 'Yetiştirmek istemediğim ürünler',
  currentRotation: 'Mevcut rotasyonum',
  dontKnow: 'Bilmiyorum',
  year: 'Yıl',
  secondCrop: '+ ikinci ürün (aynı yıl)',
  none: '—',
  llmExplain: 'Açıklamayı yapay zekâyla sadeleştir (sunucuda API anahtarı varsa; konum gönderilmez)',
  compare: 'Rotasyonları karşılaştır',
  comparing: 'Rotasyonlar hesaplanıyor…',
  privacyNote: 'Bu bilgiler yalnızca bu hesaplama için kullanılır, sunucuda saklanmaz.',
  kinds: { current: 'Mevcut rotasyon', reference: 'Referans: tek ürün', recommended: 'Öneri' } as Record<string, string>,
  total: 'Toplam puan',
  fallow: 'Nadas',
  storedWater: (mm: number) => `ekimde toprakta ~${num(mm)} mm su (model)`,
  cycleYears: (n: number) => `${n} yıllık döngü`,
  irrigationNeed: 'Yağışla karşılanmayan su',
  perYear: 'mm/yıl',
  subscoreNames: {
    suitability: 'Verim uygunluğu',
    climate_risk: 'Kötü yıl dayanımı',
    water: 'Su',
    soil: 'Toprak sağlığı (vekil)',
    erosion: 'Erozyon koruması',
    nitrogen: 'Azot',
    income: 'Gelir (sizin girdiniz)',
    forage: 'Hayvan yemi',
    diversity: 'Familya çeşitliliği',
  } as Record<string, string>,
  unknownValue: 'bilinmiyor',
  why: 'Neden',
  benefits: 'Olası faydalar',
  risks: 'Riskler',
  dataGaps: 'Bilgi eksiklikleri',
  opportunities: 'Fırsatlar',
  evidenceTitle: 'Kanıt ve yöntem',
  explanationTitle: 'Özet',
  llmNote: 'Yapay zekâ ile sadeleştirildi; sayılar karttaki verilerden gelir.',
  noRecommendation:
    'Kurallara uyan bir rotasyon bulunamadı. Kısıtları gevşetmeyi ya da sulama seçeneğini değiştirmeyi deneyin.',
  usableCrops: (n: number, min: number) => `Modelde ${n} ürün kullanılabildi (puanı en az %${Math.round(min * 100)}).`,
  firstCutOnly: (names: string) =>
    `${names} önerilerde yok: bu biçilen yem bitkilerinde yalnız ilk biçim hesaplanabiliyor, tarlada kaç ay kalacağı bilinmiyor.`,
}

const rotationTextsTR: Record<string, (p: Record<string, unknown>, name: (id: string) => string) => string> = {
  is_current: () => 'Girdiğiniz rotasyon, aynı kurallarla puanlandı.',
  is_reference: () =>
    'Karşılaştırma için: her yıl en uygun tek ürün (monokültür). Mevcut rotasyonunuzu girerseniz onunla karşılaştırılır.',
  legume_before_cereal: () => 'Tahıldan önce baklagil: azotlu gübre ihtiyacı azalabilir.',
  pest_break: () => 'Ardışık farklı bitki familyaları zararlı ve hastalık döngüsünü kırar.',
  roots_structure: () => 'Derin kökler ve uzun süre canlı kök, toprak yapısını ve suyun toprağa işlemesini destekler (vekil gösterge).',
  cover_in_rainy_months: () => 'Şiddetli yağışlı ayların çoğunda toprak örtülü.',
  double_cropping: () => 'Aynı yılda iki ürün: sezon tam kullanılıyor.',
  market_crops: () => 'Ürünlerin çoğu pazarı olduğunu belirttiğiniz ürünler.',
  fallow_break: () => 'Nadas yılı tahıl dizisini ve zararlı döngüsünü kırar.',
  same_family_consecutive: (p, name) =>
    `Kural ihlali: aynı familyadan ürünler art arda (${(p.crops as string[]).map(name).join(' → ')}).`,
  same_crop_consecutive_years: (p, name) => `Kural ihlali: ${(p.crops as string[]).map(name).join(', ')} art arda yıllarda.`,
  seasons_overlap: (p, name) => `Aynı yıldaki iki ürünün sezonu çakışıyor (${(p.crops as string[]).map(name).join(' + ')}).`,
  water_deficit: (p) => `Yağış, ürünlerin su ihtiyacının küçük bir kısmını karşılıyor (yılda ~${num(p.irrigation_need_mm_per_year)} mm açık).`,
  frequent_failure: (p) => `En az bir ürün sık başarısız oluyor (başarısız yıl oranı: ${pct(p.max_fail_rate)}).`,
  bare_soil: (p) =>
    `${yearsLabel(p.years)} tarla ${t.monthNames[Number(p.start_month) - 1]} ayından itibaren ${num(p.months)} ay boş (çıplak toprak).`,
  soil_proxy: () => 'Toprak sağlığı puanı vekil göstergedir (kök derinliği, canlı kök süresi); ürünlerin organik madde katkısı verisi henüz yok.',
  no_market_data: () => 'Pazar/fiyat verisi yok: gelir puanı için pazarı olan ürünleri işaretleyin.',
  no_slope: () => 'Eğim verisi alınamadı: erozyon puanı %9 eğim varsayıyor.',
  slope_is_area: (p) => `Eğim (%${num(p.slope_pct, 1)}) tarlanızın değil, çevredeki ~5 km’lik hücrenin ortancası (NASADEM).`,
  unmodelled_current_crops: (p, name) =>
    `Rotasyonunuzdaki bazı ürünler henüz modellenemiyor: ${(p.crops as string[]).map(name).join(', ')}.`,
  fallow_not_modelled: () =>
    'Toprak verisi alınamadığı için nadasta biriken su hesaplanamadı; nadas yılı “üretim yok” sayılıyor.',
  fallow_stores_water: (p, name) =>
    `Nadas yılında toprakta yaklaşık ${num(p.stored_mm_median)} mm su birikir (nadas dönemi yağışının ${pct(p.storage_efficiency_median)} kadarı; ` +
    `yılların çoğunda ${num(p.stored_mm_p20)}–${num(p.stored_mm_p80)} mm). Bu su sonraki ${name(String(p.crop_id))} ekimine kalır: ` +
    `puanı ${pct(p.score_median_without)} yerine ${pct(p.score_median_with)}. Model hesabı (FAO-56), ölçüm değil.`,
  soil_water_model: () =>
    'Ürünler arası dönemde toprakta biriken su bir model hesabıdır (FAO-56, SoilGrids 250 m toprak haritası). ' +
    'Varsayımlar: hasatta toprak kuru, yüzey akışı yok, yabancı ot ve anız yok sayıldı.',
  cover_crop_window: (p, name) =>
    `${yearsLabel(p.years)} ${t.monthNames[Number(p.start_month) - 1]} ayından itibaren ${num(p.months)} aylık boşluk: örtü/ara ürün fırsatı (` +
    `${(p.candidates as string[]).map(name).join(', ')} gibi; bunlar henüz modellenmiyor, yerel seçim gerekli).`,
  cover_crop_local: (p) =>
    `${t.monthNames[Number(p.start_month) - 1]} ayından başlayan ${num(p.months)} aylık boş dönemde hangi örtü bitkisi yetişebilir?`,
  drainage: () => 'Bu tarlada drenaj ya da su göllenmesi sorunu var mı?',
  fallow_management: () => 'Nadasta anız bırakıyor musunuz? Yabancı otla nasıl mücadele ediyorsunuz, toprağı ne zaman sürüyorsunuz?',
}

export function yearsLabel(years: unknown): string {
  const ys = (years as number[] | undefined) ?? []
  if (LANG === 'en') return ys.length > 1 ? `In years ${ys.join(', ')}` : ys.length === 1 ? `In year ${ys[0]}` : ''
  return ys.length > 1 ? `${ys.join(', ')}. yıllarda` : ys.length === 1 ? `${ys[0]}. yılda` : ''
}

export function rotationText(item: Item, name: (id: string) => string): string {
  if (item.code.startsWith('strong_')) {
    const key = item.code.slice(7)
    return LANG === 'en'
      ? `Strong point: ${tr.subscoreNames[key] ?? key} (${pct(item.params.value)}).`
      : `Güçlü yanı: ${tr.subscoreNames[key] ?? key} (${pct(item.params.value)}).`
  }
  return rotationTexts[item.code]?.(item.params, name) ?? questionTexts[item.code]?.(item.params) ?? item.text
}

export function reasonText(item: Item): string {
  return reasonTexts[item.code]?.(item.params) || item.text
}

export function questionText(item: Item): string {
  return questionTexts[item.code]?.(item.params) || item.text
}

export function pct(v: unknown): string {
  return LANG === 'en' ? `${Math.round(Number(v) * 100)}%` : `%${Math.round(Number(v) * 100)}`
}

export function num(v: unknown, digits = 0): string {
  return Number(v).toLocaleString(LANG === 'en' ? 'en-GB' : 'tr-TR', { maximumFractionDigits: digits })
}

// Stage 3: satellite panel.
const tsTR = {
  title: 'Uydu verileri',
  intro:
    'NDVI (MODIS), toprak nemi (SMAP), yağış (GPM IMERG) ve eğim (NASADEM) bu nokta için Earth Engine’den alınır ve NASA POWER ile aynı aylık adıma getirilir.',
  load: 'Uydu verilerini yükle',
  loading: 'Earth Engine’den uydu zaman serileri alınıyor… Yeni bir noktada ilk seferde 1–3 dakika sürebilir.',
  error: 'Uydu verileri alınamadı',
  origin: {
    earth_engine: 'Canlı veri (Earth Engine)',
    cache: 'Önbellek verisi (daha önce çekilmiş gerçek veri)',
    demo_cache: 'Önbellek verisi — Earth Engine’e ulaşılamadı, kayıtlı demo verisi kullanılıyor',
    network: 'Canlı veri',
    none: 'Veri yok',
  } as Record<string, string>,
  precipTitle: 'Yağış: NASA POWER ve GPM IMERG',
  verdict: {
    agree: 'İki kaynak yıllık ortalamada uyumlu (fark %15’ten az).',
    moderate_difference: 'İki kaynak arasında orta düzeyde fark var (%15–30).',
    large_difference: 'İki kaynak arasında büyük fark var (%30’dan fazla): sonuçları dikkatle yorumlayın.',
    imerg_zero: 'IMERG yağışı sıfır; karşılaştırma yapılamadı.',
  } as Record<string, string>,
  annualMean: 'Yıllık ortalama',
  relDiff: (rel: number) => `POWER, IMERG’den %${Math.round(Math.abs(rel) * 100)} ${rel >= 0 ? 'fazla' : 'az'}`,
  correlation: 'Yıldan yıla uyum (r)',
  trend: 'Yağış eğilimi',
  notSignificant: 'anlamlı değil',
  trendNotConfirmed: (y: number, a: number, b: number) =>
    `POWER’daki yağış eğilimi IMERG ile doğrulanmadı. İki kaynağın farkı ${y} sonrasında sıçrıyor (POWER/IMERG oranı ${num(a, 2)} → ${num(b, 2)}). Eğilim büyük olasılıkla veri işlemeden kaynaklanıyor; iklim değişimi olarak yorumlamayın.`,
  trendNotConfirmedNoStep: 'POWER’daki yağış eğilimi IMERG ile doğrulanmadı (iki kaynağın farkı zamanla değişiyor).',
  homogeneous: 'İki kaynağın farkı zaman içinde sabit (kırılma yok).',
  footprintNote: 'POWER ~50 km’lik, IMERG ~11 km’lik hücre ortalamasıdır; ikisi de tarla ölçümü değildir. Karşılaştırma yalnız iki kaynağın da tam olduğu yıllarda yapılır.',
  monthlyTitle: 'Aylık ortalamalar: bitki örtüsü ve toprak nemi',
  ndvi: 'NDVI (MODIS)',
  smap: 'Toprak nemi — SMAP gözlemi (m³/m³)',
  gwet: 'Kök bölgesi nemi — MERRA-2 modeli (0–1)',
  smapMerge: (m: { days_006: number; days_from_005: number; offset_006_minus_005: number | null; r: number | null }) =>
    `SMAP 006 ana seri (${num(m.days_006)} gün); ${num(m.days_from_005)} boş gün 005 sürümüyle dolduruldu` +
    (m.offset_006_minus_005 === null
      ? ' (örtüşme az, ofset düzeltmesi yapılamadı).'
      : ` (ofset ${num(m.offset_006_minus_005, 3)} m³/m³${m.r === null ? '' : `, r = ${num(m.r, 3)}`}).`),
  smapVsModel:
    'SMAP üst ~5 cm’yi ölçer; POWER’daki değer modeldir ve kök bölgesini temsil eder. Değerleri değil, iniş-çıkışları karşılaştırın.',
  slopeTitle: 'Eğim ve erozyon',
  slopeText: (pctv: number, rel: number) =>
    `Çevredeki ~5 km’lik hücrede ortanca eğim %${num(pctv, 1)}. RUSLE eğim faktörü %9 eğimli standart parselin ${num(rel, 2)} katı. Rotasyon kartlarındaki erozyon puanı bu katsayıyı kullanır.`,
  slopeMissing: 'Eğim verisi yok; erozyon puanı %9 eğim varsayıyor.',
  slopeFlat:
    'Burası düz ova: yükseklik verisi metre adımlı olduğu için küçük eğimleri ölçemez; eğim, hücredeki yükseklik farkından hesaplandı (varsayım).',
  patternsTitle: 'Örüntü bulma: üç yaklaşımın karşılaştırması',
  patternsIntro: (n: number) =>
    `${n} yıllık NDVI eğrileri ve iklim özetleri. Örneklem küçük: işaretlenen yıllar kesin bulgu değil, sorulacak sorulardır.`,
  methodZ: 'A · z-skor / eşik (klasik istatistik)',
  methodZText: (thr: number) => `NDVI toplamı veya zirvesi ortalamadan ${num(thr, 1)} standart sapmadan fazla sapan yıllar:`,
  methodIF: 'B · Isolation Forest (makine öğrenmesi)',
  methodIFText: 'NDVI eğrisinin şekli ve iklimle birlikte “alışılmadık” bulunan yıllar:',
  methodKM: 'B · k-means NDVI kümeleme (makine öğrenmesi)',
  kmStatus: {
    ok: 'Belirgin küme yapısı var',
    no_clear_structure: 'Belirgin küme yapısı yok (siluet düşük); kümeler zayıf',
    too_few_years: 'Yeterli yıl yok',
  } as Record<string, string>,
  cluster: (n: number, peak: number, peaks: number) =>
    `${n} yıl · zirve ${t.monthNames[peak - 1]} · ${peaks === 2 ? 'iki sezon' : peaks === 1 ? 'tek sezon' : `${peaks} zirve`}`,
  regimeShift: (y: number) =>
    `Kümeler zamana göre ayrılıyor: ${y} sonrasında sezon deseni değişmiş. Ürün deseni veya sulama değişti mi? Yerelde kontrol edin.`,
  methodAN: 'C · Analog yıllar (klasik istatistik)',
  analogText: (y: number, years: string) => `${y} yılının iklimine en çok benzeyen yıllar: ${years}.`,
  analogSkill: (s: number) =>
    s > 0.1
      ? `Benzer iklimli yıllar NDVI’yi uzun dönem ortalamasından %${Math.round(s * 100)} daha iyi tahmin ediyor (birini dışarıda bırakma testi).`
      : 'Benzer iklimli yıllar NDVI’yi uzun dönem ortalamasından daha iyi tahmin etmiyor: burada bitki örtüsünü iklimden çok yönetim (sulama, ürün seçimi) belirliyor olabilir.',
  agreement: 'A ile B’nin uyumu',
  both: 'İkisi de',
  onlyZ: 'Yalnız z-skor',
  onlyIF: 'Yalnız Isolation Forest',
  none: 'yok',
  yearCtx: (z: number, p: number, tm: number) => `NDVI z ${num(z, 1)} · yağış z ${num(p, 1)} · sıcaklık z ${num(tm, 1)}`,
  precipNotHomogeneous: 'Not: bu noktada POWER yağışı homojen değil; iklim kullanan yöntemler (Isolation Forest, analog yıllar) bundan etkilenir.',
}

export function dateLabel(mmdd: string): string {
  const [m, d] = mmdd.split('-').map(Number)
  return LANG === 'en' ? `${t.monthNames[m - 1]} ${d}` : `${d} ${t.monthNames[m - 1]}`
}

// Stage 5: rainfall source, scenario sliders, risk layers.
const tkTR = {
  scenarioTitle: 'Yağış kaynağı ve senaryo',
  precipSource: 'Yağış verisi',
  precipOptions: { power: 'NASA POWER', imerg: 'GPM IMERG', chirps: 'CHIRPS' } as Record<string, string>,
  precipHelp: {
    power: 'Varsayılan: NASA POWER günlük yağışı (~50 km hücre).',
    imerg:
      'Her ayın POWER günlük yağışı, o ayın IMERG toplamına ölçeklenir (gün deseni POWER’dan). IMERG’in olmadığı aylar POWER kalır.',
    chirps:
      'Her ayın POWER günlük yağışı, o ayın CHIRPS toplamına ölçeklenir (gün deseni POWER’dan). CHIRPS uydu ölçümünü yer istasyonlarıyla birleştirir (~5 km).',
  } as Record<string, string>,
  deltaT: 'Sıcaklık değişimi',
  deltaP: 'Yağış değişimi',
  exploreSowing: 'Farklı ekim zamanlarını da dene',
  exploreSowingHelp:
    'Normalde en iyi ekim zamanı, bölgede yaygın ekim gününün 45 gün öncesi ile sonrası arasından seçilir (GGCMI ürün takvimi). ' +
    'İşaretlerseniz model bütün yılı dener; bu, iklim değişince ekim zamanı nasıl kayabilir sorusu için yararlıdır.',
  localCalendar: (plant: string, mature: string) => `Bu bölgede yaygın: ekim ${plant}, hasat ~${mature} (GGCMI)`,
  calendarIgnored: 'bütün yıl denendi',
  calendarRainfedFallback: 'sulu tarım için kayıt yok, kuru tarım takvimi',
  calendarGapFilled: 'bu hücrede gözlem yok, tahmini takvim',
  calendarConflict: 'model bu tarihte yetiştiremiyor, bütün yıl denendi',
  outsideCalendar: (sow: string, score: string) =>
    `Model ${sow} ekimine daha yüksek puan veriyor (${score}), ama bu tarih bölgedeki ekim zamanının dışında.`,
  apply: 'Uygula',
  reset: 'Sıfırla',
  pending: 'Değişiklikler henüz uygulanmadı.',
  scenarioNote:
    'Senaryo bir duyarlılık testidir, iklim tahmini değildir: gözlenen 25 yılın her gününe aynı sıcaklık farkı eklenir ve yağış aynı oranda değiştirilir; nem, rüzgâr ve güneşlenme değişmez, ET0 yeniden hesaplanır.',
  bannerScenario: (dt: number, dp: number) =>
    `Senaryo: ${dt > 0 ? '+' : ''}${num(dt, 1)} °C, yağış ${dp > 0 ? '+' : ''}${num(dp)} %`,
  bannerImerg: (used: number, power: number) => `Yağış: IMERG’e ölçeklendi (yıllık ${num(used)} mm; POWER ${num(power)} mm)`,
  bannerChirps: (used: number, power: number) => `Yağış: CHIRPS’e ölçeklendi (yıllık ${num(used)} mm; POWER ${num(power)} mm)`,
  rainTooWet: (power: number, chirps: number) =>
    `Bu bölgede NASA POWER yağışı fazla olabilir: yılda ${num(power)} mm, istasyonlarla birleştirilmiş CHIRPS ${num(chirps)} mm. ` +
    'Yağmurla tarım sonuçları iyimser olabilir; “Yağış kaynağı” ayarından CHIRPS ile deneyin.',
  rainTooWetShort: 'POWER yağışı burada fazla olabilir',
  imergGaps: (n: number, range: string | null) => `${n} ay IMERG verisi yok${range ? ` (${range.replace('..', ' – ')})` : ''}; bu aylarda POWER kullanıldı.`,
  vsBaseline: 'senaryosuz',
  riskTitle: 'Risk katmanları',
  riskIntro:
    'Her ay, aynı takvim ayının 25 yıllık ortalamasıyla karşılaştırılır. Kırmızı: o ay risk normalden yüksek; mavi: normalden düşük. Değerler analiz noktasının zaman serisidir, harita değildir.',
  riskLoad: 'Risk katmanlarını yükle',
  riskLoading: 'Risk katmanları hesaplanıyor… Uydu verisi yeni bir noktada ilk seferde 1–3 dakika sürebilir.',
  riskError: 'Risk katmanları alınamadı',
  cropFor: 'Eşikler için ürün',
  generic: 'Genel (ürün seçilmedi)',
  year: 'Yıl',
  annualCol: 'Yıl',
  normal: 'normal',
  layers: {
    frost_days: 'Don günü',
    lethal_cold_days: 'Öldürücü soğuk günü',
    hot_days: 'Sıcak gün',
    heavy_rain_days: 'Şiddetli yağış günü',
    water_balance_mm: 'Su dengesi',
    smap_sm: 'Toprak nemi (uydu)',
    ndvi: 'Bitki örtüsü (NDVI)',
  } as Record<string, string>,
  units: { days: 'gün', mm: 'mm', 'm³/m³': 'm³/m³', NDVI: '' } as Record<string, string>,
  notes: {
    scenario_applies_to_climate_only:
      'Senaryo yalnız iklim katmanlarına uygulanır. SMAP ve NDVI gözlemdir; olduğu gibi gösterilir.',
    generic_heat_threshold: 'Ürün seçilmedi: sıcak gün için genel 35 °C eşiği kullanılıyor (varsayım). Ürün seçerseniz kaynaklı eşik kullanılır.',
    lethal_cold_is_air_temperature:
      'Öldürücü soğuk: ~50 km hücrede 2 m hava sıcaklığıdır, bitkinin kök boğazı sıcaklığı değildir; kar örtüsü bitkiyi korur.',
  } as Record<string, string>,
  missingLayer: (ids: string) => `Eksik katman: ${ids}. Uydu verisi alınamadı.`,
  compareTitle: 'Katman karşılaştırma',
  compareIntro: 'İki katmanı aynı ölçekte yan yana görün. 0 çizgisi normal; yukarısı normalden riskli, aşağısı normalden iyi.',
  layerA: 'Katman A',
  layerB: 'Katman B',
  chartYear: (y: number) => `${y} — aylar`,
  chartAll: 'Tüm yıllar — yıllık',
  riskAxis: 'risk',
  noData: 'veri yok',
  legendWorse: 'normalden riskli',
  legendBetter: 'normalden iyi',
}

// Simple farmer view (bottom tabs, field picker, summary, help).
const tuTR = {
  tabs: { field: 'Tarla', summary: 'Özet', rotation: 'Ekim sırası', details: 'Ayrıntılar' },
  help: 'Nasıl kullanılır?',
  close: 'Kapat',
  pickTitle: 'Tarlanızı seçin',
  pickHint: 'Haritayı parmağınızla kaydırın. Ortadaki artı işaretini tarlanızın üstüne getirin, sonra sarı “Bu noktayı seç” düğmesine basın. Haritaya dokunursanız o yer ortaya gelir.',
  pickHere: 'Bu noktayı seç',
  searchLabel: 'Yer ara',
  searchPlaceholder: 'Köy, ilçe, 37.6, 32.75 ya da harita linki',
  search: 'Ara',
  searching: 'Aranıyor…',
  noResults: 'Bulunamadı. Başka bir yazımla ya da il/ilçe adıyla deneyin.',
  searchFailed: 'Arama yapılamadı (internet yok olabilir). Haritadan seçebilir ya da koordinat yazabilirsiniz.',
  searchNote: 'Yer adı aramak için yazdığınız ad OpenStreetMap’e gönderilir; konumunuz gönderilmez. Koordinat ya da harita bağlantısı yapıştırırsanız hiçbir yere gönderilmez.',
  shortLink:
    'Kısa paylaşım bağlantılarında konum yazmaz. Bağlantıyı tarayıcıda açın, adres çubuğundaki uzun adresi kopyalayıp buraya yapıştırın.',
  linkWithoutCoords: 'Bu bağlantıda konum bulunamadı. Köy/mahalle adını yazın ya da haritadan seçin.',
  tkgmTitle: 'Tapudaki ada/parsel numaranızla bulun',
  tkgmSteps: [
    'Aşağıdaki düğmeyle Tapu ve Kadastro’nun (TKGM) “Parsel Sorgu” sitesini açın.',
    'İl, ilçe, mahalle/köy, ada ve parsel numaranızı girin. Site parselinizi haritada gösterir.',
    'Buraya dönün. Mahalle/köy adını yukarıdaki kutuya yazıp arayın; ya da TKGM’den aldığınız konum bağlantısını kutuya yapıştırın.',
    'Uydu haritasında parselinizi bulun, artı işaretini üstüne getirip “Bu noktayı seç”e basın.',
  ],
  tkgmOpen: 'TKGM Parsel Sorgu’yu aç',
  tkgmNote:
    'TKGM’nin kendi sitesi yeni sekmede açılır. Oraya yazdıklarınız bu uygulamaya gelmez, bu uygulama da TKGM’ye bir şey göndermez.',
  coordOutOfRange: 'Koordinat geçersiz: enlem −90…90, boylam −180…180 olmalı.',
  orDivider: 'ya da',
  examples: 'Örnek tarlalar',
  mapSatellite: 'Uydu',
  mapStreet: 'Harita',
  satelliteNote: 'Uydu görüntüsü 2016 yılına aittir (Sentinel-2); tarlanızın bugünkü hâli farklı olabilir.',
  irrigationQuestion: 'Tarlanızı sulayabiliyor musunuz?',
  irrigationOptions: { none: 'Hayır', limited: 'Biraz', full: 'Evet' },
  irrigationHelp: {
    none: 'Sadece yağmur suyu hesaba katılır.',
    limited: 'Varsayım: yağmurun yetmediği suyun yarısını sulayabiliyorsunuz.',
    full: 'Su sorunu yok sayılır.',
  },
  chosenPlace: 'Seçilen yer',
  changeField: 'Değiştir',
  noField: 'Önce “Tarla” bölümünden tarlanızı seçin.',
  loading: '25 yıllık NASA hava verisi inceleniyor…',
  bestTitle: 'Bu tarlada en iyi yetişebilecekler',
  bestIntro: 'Son 25 yılın havasına göre. Puan bir verim tahmini değildir; ürünleri birbiriyle karşılaştırmak içindir.',
  outOf: '/ 100',
  badYearShort: 'Kötü yılda',
  sowShort: 'Ekim',
  harvestShort: 'Hasat',
  goodMonths: 'Uygun ekim ayları',
  askLocal: 'Yerel doğrulama gerekli: uzmana danışın',
  questionsTitle: 'Ziraat uzmanına sorun',
  noCrops:
    'Model bu noktada uygun ürün bulamadı. Bu kesin bir yargı değildir: yerel deneyimle karşılaştırın, “Ayrıntılar”da tüm ürünleri görebilirsiniz.',
  risksTitle: 'Dikkat edilecekler',
  risksIntro: 'Son 25 yılın aylık ortalamaları. Renkli kutular riskli ayları gösterir.',
  riskFrost: 'Don',
  riskFrostText: 'Bu aylarda her 2 yıldan en az 1’inde don oluyor.',
  riskHot: 'Aşırı sıcak',
  riskHotText: 'Bu aylarda ortalama ayda en az 1 gün 35 °C’yi geçiyor.',
  riskDry: 'Yağmur yetmiyor',
  riskDryText: 'Bu aylarda yağmur, havanın topraktan çektiği sudan az. Bitki ya topraktaki suyu kullanır ya da sulama gerekir.',
  riskNone: 'yok',
  next: 'Sonraki adım',
  goRotation: 'Hangi ürünü hangi yıl ekeyim? — Ekim sırası',
  goDetails: 'Tüm ürünler, risk tablosu ve uydu verisi — Ayrıntılar',
  detailsIntro:
    'Uzman görünümü: hesapların teknik ayrıntıları. Terimlerin yanındaki “?” düğmesine basarak ne demek olduğunu okuyabilirsiniz.',
  detailsSections: {
    data: 'Veri kaynağı ve konum',
    scenario: 'Yağış kaynağı ve senaryo',
    climate: 'Bölgenin iklimi',
    crops: 'Tüm ürünler',
    risk: 'Aylara göre risk tablosu',
    satellite: 'Uydu verileri',
  },
  helpSteps: [
    ['Tarlanızı seçin', 'Haritayı kaydırıp artı işaretini tarlanıza getirin ve “Bu noktayı seç”e basın. Köy adı da yazabilir ya da “Konumumu kullan”a basabilirsiniz.'],
    ['Sulamayı söyleyin', 'Tarlanızı sulayabiliyorsanız “Evet” ya da “Biraz” seçin. Sonuçlar buna göre değişir.'],
    ['Özeti okuyun', '“Özet” bölümünde bu yerde en iyi yetişebilecek ürünler, ne zaman ekileceği ve dikkat edilecek aylar var.'],
    ['Ekim sırasını planlayın', '“Ekim sırası” bölümünde hangi yıl hangi ürünü ekeceğinizi karşılaştırabilirsiniz.'],
    ['Uzmana danışın', 'Bu uygulama yardımcıdır, karar sizindir. “Uzmana danışın” yazan sonuçları ziraat mühendisine ya da il/ilçe tarım müdürlüğüne sorun.'],
  ] as [string, string][],
  helpScores:
    'Puan: 100 üzerinden. Yüksek puan, ürünün bu yerin havasına daha iyi uyduğunu gösterir. “Kötü yılda” puanı, her 5 yılın en kötüsünde beklenen puandır.',
  helpOffline: 'İnternet yoksa son baktığınız sonuçlar 7 gün telefonunuzda kalır.',
  helpGuide: 'Ayrıntılı kullanım kılavuzu: docs/KULLANIM_KILAVUZU.md (proje belgeleri).',
}

// ---- Kolay mod (docs/drafts/plan_kolay_mod.md)
const teTR = {
  chooseTitle: 'Uygulamayı nasıl kullanmak istersiniz?',
  chooseIntro: 'İstediğiniz zaman üstteki düğmeyle değiştirebilirsiniz.',
  easyName: 'Kolay mod',
  easyText: 'Bana doğrudan ne yapacağımı söyle: ne ekeyim, ne zaman ekeyim, ne kadar su gerekir.',
  expertName: 'Uzman mod',
  expertText: 'Öncelikleri, kısıtları ve tüm grafikleri ben seçip inceleyeyim.',
  switchToExpert: 'Uzman',
  switchToEasy: 'Kolay',
  planTab: 'Planım',
  planTitle: 'Tarlanız için önerilen plan',
  planIntro: (years: number) =>
    `${years} yıllık bir döngü: ${years}. yıldan sonra 1. yıla dönün. Her yıl ne ekeceğiniz ve ne zaman ekeceğiniz aşağıda.`,
  computing: 'Planınız hazırlanıyor… (yarım dakika sürebilir)',
  noPlan: 'Bu yer için kurallara uyan bir plan bulunamadı. Uzman modda ayrıntılara bakabilirsiniz.',
  option: (i: number, n: number) => `Seçenek ${i} / ${n}`,
  otherOption: 'Başka seçenek göster',
  year: (i: number) => `${i}. yıl`,
  fallowYear: 'Nadas: bu yıl tarlayı ekmeyin, toprak yağmur suyunu biriktirsin.',
  sow: (date: string) => `Ekim: ${date} civarı`,
  harvest: (date: string) => `Hasat: yaklaşık ${date}`,
  prepare: 'Toprağı ekimden önce, bölgenizdeki alışılmış zamanda hazırlayın.',
  waterOkRain: 'Su: yağmur normal bir yılda genelde yeter.',
  waterNeedNone: (mm: number) =>
    `Su: yağmur normal bir yılda yaklaşık ${mm} mm eksik kalır (dekar başına ~${mm} ton su). Sulayamıyorsanız verim düşebilir.`,
  waterNeedIrr: (mm: number) =>
    `Su: sezon boyunca yaklaşık ${mm} mm sulama suyu gerekir (dekar başına ~${mm} ton). Kurak yıllarda daha fazla.`,
  stored: (mm: number) => `Önceki boş dönemde toprakta yaklaşık ${mm} mm su birikir; bu su ürüne yardım eder.`,
  forage: 'Hayvan yemi olarak kullanılabilir.',
  legume: 'Toprağa azot bırakır: sonraki ürüne daha az azotlu gübre gerekebilir.',
  idleTitle: 'Tarlanın boş kaldığı aylar',
  monthNames: ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'],
  idle: (from: string, months: number) => `${from} ayından başlayarak ${months} ay`,
  idleAdvice:
    'Bu aylarda tarla boş kalır. İsterseniz anızı hayvanlarınıza otlatabilir ya da toprak çıplak kalmasın diye fiğ gibi bir örtü bitkisi ekebilirsiniz. Uygulama bunun ne kadar ot vereceğini hesaplamıyor; kaç hayvan otlatabileceğinizi köyünüzdeki tecrübeli çiftçilere veya tarım müdürlüğüne sorun.',
  flat: 'Araziniz düz: yağmurla toprak taşınması (erozyon) riski düşük, plan bunu dikkate almadı.',
  scoreLine: (p: number) => `Bu planın uygunluk puanı: ${p}/100`,
  lowConfidence: 'Bu plan bir model hesabıdır; uygulamadan önce yerel bir ziraat mühendisine danışın.',
  why: 'Neden bu plan?',
  moreDetails: 'Ayrıntılı karşılaştırma için uzman moda geçin.',
}

// ---- Tarla köşeleri, sulama aralığı, sıra yönü (docs/drafts/plan_kolay_mod.md, devamı)
const tfTR = {
  title: 'Tarlanızın köşelerini işaretleyin (isteğe bağlı)',
  intro: 'Köşeleri işaretlerseniz tarlanızın alanı hesaplanır ve plan size tarlanızın tamamı için kaç ton su gerektiğini söyler.',
  drawingHint: 'Haritada tarlanızın köşelerine sırayla dokunun (en az 3). Bitince “Tamam”a basın.',
  start: 'Köşeleri işaretle',
  edit: 'Köşeleri düzenle',
  undo: 'Son köşeyi sil',
  clear: 'Temizle',
  done: 'Tamam, bu tarla',
  area: (da: number) => `Alan: yaklaşık ${num(da, da < 10 ? 1 : 0)} dekar`,
  privacy: 'Köşeler yalnız telefonunuzda kalır, hiçbir yere gönderilmez.',
  irrigation: (lead: string, from: string, to: string, days: number, mm: number) =>
    `${lead} (${from} – ${to}, en çok su isteyen dönem): yağmur yağmazsa her ${days} günde bir, her seferinde yaklaşık ${mm} mm (dekar başına ~${mm} ton).`,
  irrigationOnce: (lead: string, from: string, to: string, mm: number) =>
    `${lead} (${from} – ${to}, en çok su isteyen dönem): bu dönem yağmursuz geçerse bir kez yaklaşık ${mm} mm (dekar başına ~${mm} ton) yeter.`,
  irrigationLead: 'Sulama',
  irrigationLeadIfPossible: 'Sulayabilirseniz',
  irrigationRainy: 'Bu dönemde yağmur genelde yeter; yağmursuz geçen haftalarda yukarıdaki aralıkla sulayın.',
  wholeField: (tons: number) => `Tarlanızın tamamı için: yaklaşık ${num(tons)} ton.`,
  seasonWholeField: (tons: number) => `Tüm sezonda tarlanız için yaklaşık ${num(tons)} ton ek su.`,
  rowsTitle: 'Sıraları hangi yönde ekmeli?',
  rowsContour: (axis: string, down: string) =>
    `Arazi ${down} yönüne doğru alçalıyor. Sıraları eğime dik, yani ${axis} yönünde ekin (çizimdeki çizgiler): yağmur suyu toprağı daha az taşır ve daha çok su toprağa işler.`,
  rowsFlat: 'Araziniz düz: yağmur toprağı taşımaz, sıraları size en kolay gelen yönde ekebilirsiniz.',
  rowsUnknown: 'Arazinin eğim yönü bilinmiyor; sıra yönü önerisi yok.',
  rowsNote: 'Eğim yönü çevredeki ~5 km’lik alanın genel eğiminden (NASA NASADEM) hesaplandı; tarlanızın kendi eğimi farklıysa ona göre ekin.',
  sketchNorth: 'K',
  sketchTitle: 'Tarlanız (yukarısı kuzey)',
}

// ---- language selection (lang.ts)
export type Dict = {
  t: typeof tTR
  tr: typeof trTR
  ts: typeof tsTR
  tk: typeof tkTR
  tu: typeof tuTR
  te: typeof teTR
  tf: typeof tfTR
  reasonTexts: typeof reasonTextsTR
  questionTexts: typeof questionTextsTR
  rotationTexts: typeof rotationTextsTR
}
const D: Dict =
  LANG === 'en'
    ? EN
    : { t: tTR, tr: trTR, ts: tsTR, tk: tkTR, tu: tuTR, te: teTR, tf: tfTR,
        reasonTexts: reasonTextsTR, questionTexts: questionTextsTR, rotationTexts: rotationTextsTR }
export const t = D.t
export const tr = D.tr
export const ts = D.ts
export const tk = D.tk
export const tu = D.tu
export const te = D.te
export const tf = D.tf
const reasonTexts = D.reasonTexts
const questionTexts = D.questionTexts
const rotationTexts = D.rotationTexts
