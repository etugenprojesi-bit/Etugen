# Plan: model sezonlarını uydu (MODIS) ile doğrulama — iyileştirme listesi madde 5

Durum: **onaylandı 2026-11-12 (K1-a, K2-a, K3-a, K4-a) ve uygulandı.** Son
sonuçlar: METHOD.md "Season validation (MODIS)". Not: uygulamada model ekimi
yağmurla yapıldı (sezon uzunluğu sulamaya bağlı değil); Punjab buğdayı farkı
MCD12Q2 ile −20 gün, NDVI ile −25 gün çıktı (bu taslaktaki −26 ön sonuçtu).

## 1. Amaç

Model her ürün için "ekim → olgunluk" sezonunu sıcaklık toplamından hesaplıyor.
Bunun gerçeğe ne kadar uyduğunu bilmiyoruz. Uydu, tarlanın ne zaman yeşerip ne
zaman kuruduğunu 25 yıldır görüyor. Plan: model sezonunu uydu sezonuyla
karşılaştırıp farkı **göstermek** (puanları değiştirmeden). Bu bir doğrulamadır,
modeli uyduya "uydurmak" (kalibrasyon) değil.

## 2. Veri

| Veri | Ne verir | Durum |
|---|---|---|
| **MODIS MCD12Q2 v6.1** (NASA LP DAAC, DOI [10.5067/MODIS/MCD12Q2.061](https://doi.org/10.5067/MODIS/MCD12Q2.061)), Earth Engine `MODIS/061/MCD12Q2` | Her yıl için en fazla 2 bitki döngüsü: yarı-yeşerme (EVI2 genliğinin %50’si, `MidGreenup`), zirve (`Peak`), yarı-kuruma (`MidGreendown`), kalite kodu. 500 m, 2001–2025. | ✅ canlı prob 2026-11-12: 3 noktada 25 yıl, 0,6–2 s/nokta. Yeni veri seti → CREDITS’e eklenecek. |
| MODIS MOD13Q1 NDVI (zaten var, demo önbelleğinde) | 16 günlük NDVI, 1 km ortalama. Aynı %50 kuralını kendimiz uygularsak çapraz kontrol. | ✅ mevcut |

Eşik tanımları (15/50/90 %) bizim seçimimiz değil, MCD12Q2 ürün tanımı (STAC
bant açıklamaları). Biz yalnız %50 noktalarını ve zirveyi kullanırız.

## 3. Karşılaştırma kuralı (öneri)

1. Ekim tarihi = GGCMI yerel ekim günü (en yakın 1/16 tarihi). Böylece
   "pencere seçimi" değil, **sezon uzunluğu** sınanır.
2. Her yıl model sezonu hesaplanır (ekim, orta dönem, olgunluk).
3. O yılın uydu döngüsü: zirvesi model sezonu içinde (ekim … olgunluk + 45 gün)
   kalan döngü (**varsayım**, etiketlenir). Yoksa o yıl "eşleşmedi".
4. Ölçüler: (model olgunluk − uydu yarı-kuruma) ve (model orta dönem − uydu
   zirve) için ortanca, çeyrekler arası aralık, yıllar arası Spearman korelasyonu,
   eşleşen yıl sayısı.
5. Not: uydu yarı-kuruma ≠ fizyolojik olum; birkaç haftalık **sabit** bir fark
   beklenir. Önemli olan: fark çok büyük mü, yıllar arası iniş-çıkış tutuyor mu.

## 4. Ön sonuçlar (geçici betik, demo önbelleği, NDVI %50 kuralı)

| Nokta / ürün | Model olgunluk − uydu yarı-kuruma | Model orta dönem − uydu zirve | Yıllar arası uyum | Yorum |
|---|---|---|---|---|
| Punjab çeltik (tam sulama, ekim 07-01) | **−4 gün** (−10…+3) | −3 gün | 0,30 | ✔ çok iyi |
| Punjab buğday (tam sulama, ekim 11-01) | **−26 gün** (−29…−20) | −10 gün | **0,67** | Model ~4 hafta erken olgunlaştırıyor (GGCMI olum 04-16, uydu kuruma ~04-04, model ~03-09). Yazlık çeşit parametresi + vernalizasyon/gün uzunluğu yok. Yıllar arası zamanlama tutuyor. |
| Nakuru buğday / arpa (kısa yağmurlar, ekim Eyl–Eki) | −3 / 0 gün | +39 / +10 gün | ~0 | ✔ ortalama uyumlu; ama MCD12Q2 bu döngüyü 25 yılın yalnız 4’ünde görüyor |
| Nakuru mısır (GGCMI ekimi Ekim) | +93 gün | +71 gün | ~0 | ✘ model sezonu gözlenen döngüden çok uzun. Ya bu pikseldeki Ekim–Ocak döngüsü mısır değil, ya yüksek rakım çeşidi farklı. **Sonuçsuz.** Bölgenin ana döngüsü uzun yağmurlarda: yarı-yeşerme ~05-01, zirve ~06-09, yarı-kuruma ~07-28 (MCD12Q2). |
| Konya (Çumra) kışlık buğday / arpa | — | — | — | ✘ Bu 500 m–1 km pikselde tek döngü var, zirvesi **Ağustos başı** (sulu yazlık ürünler). Kışlık tahıl bu pikselde doğrulanamaz. |

MCD12Q2 ile kendi NDVI hesabımız tutarlı: Punjab yarı-kuruma buğday 89. gün
(NDVI: 94.), çeltik 288. gün (NDVI: 290.).

**Ana bulgu:** Model, Punjab çeltiğinde uydu ile neredeyse aynı; Punjab
buğdayını ~4 hafta erken bitiriyor (bilinen kısıt, şimdi sayıyla gösterildi).
Konya ve Nakuru’da 1 km’lik piksel karışık olduğu için doğrulama sınırlı.

## 5. Kararlar (onayınız gerekiyor)

**K1 — Veri.**
- **K1-a (önerim):** MCD12Q2 ana kaynak (NASA’nın hazır fenoloji ürünü, eşikler
  ürünün kendi tanımı), MOD13Q1 NDVI çapraz kontrol. Earth Engine katmanı +
  demo önbelleği yeniden üretilir (küçük ek, ~1 s/nokta).
- K1-b: Yalnız mevcut MOD13Q1 NDVI, %50 kuralını biz uygularız (yeni veri yok).

**K2 — Nerede gösterilir?**
- **K2-a (önerim):** Önce yalnız belge + betik + testler: `scripts/validate_seasons.py`
  demo noktaları için tabloyu üretir, METHOD.md’ye "Doğrulama" bölümü girer.
  Arayüz değişmez.
- K2-b: Ayrıca ürün kartına bir satır: "Uydu: bu bölgede bitki örtüsü genelde
  X tarihinde kuruyor; model Y diyor" + karışık piksel uyarısı.
- K2-c: K2-b + fark 30 günden büyükse güven bir kademe düşer.

**K3 — Punjab buğdayı bulgusuyla ne yapalım?**
- **K3-a (önerim):** Şimdi değiştirmeyiz, belgeye yazarız. Ayrı bir adımda
  Güney Asya buğday çeşitleri için kaynaklı t_sum aranır (madde 4 gibi).
- K3-b: t_sum’u uyduya göre ayarlamak — **önermem** (kaynaksız uydurma olur).

**K4 — Konya.**
- **K4-a (önerim):** "Bu pikselde kışlık tahıl doğrulanamaz" diye yazılır.
- K4-b: Tarla ölçeğinde (30 m) HLS verisi eklenir — daha ağır, sonra.

## 6. Onaydan sonra (K1-a, K2-a, K3-a, K4-a varsayımıyla)

1. `app/sources/gee.py`: MCD12Q2 katmanı (nokta pikseli, 2001–son yıl,
   bantlar yukarıdaki gibi); `scripts/build_demo_cache.py gee` ile 3 noktanın
   önbelleği yenilenir.
2. `app/validation/seasons.py`: döngü eşleştirme ve ölçüler (saf fonksiyonlar).
3. `scripts/validate_seasons.py`: demo noktaları için tablo (çevrimdışı).
4. Testler: tarih dönüşümü (1970’ten gün sayısı), %50 geçişleri yapay eğride,
   döngü eşleştirme (çift döngülü yıl, eşleşmeyen yıl), ölçüler, önbellek okuma.
5. Belgeler: DATA_SOURCES §4 (MCD12Q2 + prob sonucu), CREDITS (MCD12Q2),
   METHOD (doğrulama bölümü ve tablo, Known limitations’a Punjab buğdayı),
   kılavuz (bir cümle: "uydu ile karşılaştırma").

## 7. Açık noktalar

- Nakuru: GGCMI mısır ekimini Ekim gösteriyor, uydu ana döngüyü Mayıs–Temmuz’da
  görüyor. Takvim ya da piksel sorunu olabilir; doğrulama bunu ancak işaret edebilir.
- Punjab’daki şüpheli GGCMI sulu arpa takvimi (Haziran ekimi): uyduda o
  dönemde ayrı bir arpa döngüsü yok (yaz döngüsü çeltik).
