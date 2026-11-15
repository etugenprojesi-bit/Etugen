# Plan: bitki katsayısını (Kc) yerel iklime göre düzeltme — onaylandı 2026-11-12 (K1-a, K2-a)

Durum: **uygulandı** (docs/METHOD.md "Kc climate adjustment"). Rotasyon etkisi
orada: Konya ve Pencap'ta öneriler aynı; Nakuru'da "darı → mercimek" birinci sıraya çıktı.

İyileştirme listesindeki 3. adım. Kaynaklar: `docs/DATA_SOURCES.md` bölüm 9.
Prob betiği: `scripts/probe/probe_power_humidity.py`.

## 1. Sorun ne?

Bitkinin su tüketimini ETc = Kc × ET0 ile hesaplıyoruz. Kc değerlerini
FAO-56 Tablo 12'den alıyoruz. Bu tablo "orta nemli" bir iklim için yazılmış:
öğleden sonraki en düşük bağıl nem (RHmin) ≈ %45, rüzgâr (u2) ≈ 2 m/s.

- Kurak ve rüzgârlı yerde bitki daha çok su harcar → Kc daha yüksek olmalı.
- Nemli ve sakin yerde daha az harcar → Kc daha düşük olmalı.

Şu an bu düzeltme yok (METHOD.md "Known limitations" bunu açıkça yazıyor).
`data/crops.yaml` başlığı da "kodda düzeltilmeli" diyor.

## 2. Kaynak: FAO-56 6. bölüm (orijinal HTML ve denklem resimleri okundu)

| Ne | Denklem | Not |
|---|---|---|
| Orta dönem Kc | Kc_mid = Kc_mid(Tablo) + [0,04 (u2 − 2) − 0,004 (RHmin − 45)] (h/3)^0,3 (**denk. 62**) | u2 ve RHmin: **orta dönemin** ortalaması; h = bitki boyu (m) |
| Son Kc | Aynı formül (**denk. 65**), **son dönemin** ortalamasıyla | **Yalnız Kc_end(Tablo) > 0,45 ise** uygulanır (yeşil hasat edilen ürünler). Kuruyarak hasat edilen ürünlerde (buğday 0,25–0,40) düzeltme yok |
| Geçerlilik sınırları | 1 ≤ u2 ≤ 6 m/s; %20 ≤ RHmin ≤ %80; 0,1 < h < 10 m | FAO: "sınırlara uyulmalı" |
| RHmin | RHmin = 100 · e°(Tçiğ) / e°(Tmax) (**denk. 63**) | Çiğ noktası yoksa Tçiğ ≈ Tmin (denk. 64), kurak iklimde Tmin − 2 °C |
| Ortalama alma | Her gün RHmin hesaplanır, sonra dönem boyunca ortalaması alınır | FAO-56 Ek 8 tablosu böyle yapıyor |

Bitki boyu h zaten `data/crops.yaml` içinde var (`max_height_m`, FAO-56 Tablo 12).

## 3. RHmin nereden gelecek? (prob sonucu)

NASA POWER günlük **en düşük** nemi vermiyor (RH2M_MIN yok, HTTP 422). Ama
**çiğ noktası** (`T2MDEW`) veriyor. 25 yıl, 3 noktada hiç boş gün yok.
Üç yolu karşılaştırdım (25 yılın ortalama RHmin'i, %):

| Nokta | A: günlük ortalama nemden (RH2M) | B: çiğ noktasından (T2MDEW, denk. 63) | C: Tmin'den (denk. 64) |
|---|---|---|---|
| Konya | 46,2 | 40,1 | 44,7 |
| Pencap | 33,9 | 29,4 | 45,8 |
| Nakuru | 52,0 | 45,1 | 47,1 |

- **A** yeni veri gerektirmez ama her yerde 4–7 puan fazla nemli çıkıyor.
  FAO-56 de bu yolun (denk. 19) havadaki nemi fazla tahmin ettiğini yazıyor (Örnek 5).
- **B** FAO-56'nın tercih ettiği yol (denk. 63). POWER'a bir parametre eklemek gerekir.
- **C** kurak aylarda çok yanlış (Pencap Mayıs: %43 yerine %15). Kullanmıyoruz.

Rüzgâr: zaten çektiğimiz `WS2M` (2 m'de günlük ortalama rüzgâr) doğrudan u2'dir.

## 4. Ne değişecek? (onaydan sonra)

1. `power.py`: parametre listesine `T2MDEW` eklenir (yalnız K1 = B seçilirse).
   Önbellek anahtarı parametre listesini içerdiği için bir kez yeniden indirilir.
   `demo_cache/` içindeki 3 POWER dosyası internetle yeniden oluşturulur.
2. Yeni küçük modül `app/features/kc_climate.py`: denk. 62/65, denk. 63, sınırlar.
3. `Crop` sınıfına `max_height_m` eklenir (aralıksa orta değer, mevcut kural).
4. `ClimateArrays` günlük RHmin ve u2 taşır.
5. `engine.season_rows`: her yıl ve her ekim tarihi için orta ve son dönemin
   gerçek günleri bulunur, o günlerin RHmin ve u2 ortalamasıyla Kc_mid ve Kc_end
   düzeltilir. Kc_ini değişmez (o, ıslanma sıklığına bağlı; ayrı konu).
6. Senaryo kaydırıcıları: ET0 hesabındaki kabulle aynı olsun diye "nem sabit"
   kalır, yani RHmin gözlenen iklimden alınır (sıcaklık artınca değişmez).
7. `docs/METHOD.md` (yeni bölüm + "Known limitations" güncellenir), kart ve
   kaynak listesindeki "FAO-56 Kc (Table 12)" metni "yerel neme ve rüzgâra göre
   düzeltildi (FAO-56 denk. 62/65)" olur. Arayüzde yeni bir düğme yok.

Nadas su hesabı etkilenmez: çıplak toprakta h = 0 olduğu için denk. 72'deki
düzeltme terimi sıfır olur.

## 5. Kabuller (kartta ve METHOD.md'de etiketli olacak)

- Dönem ortalaması sınırların dışına çıkarsa sınıra çekilir (ör. u2 = 0,8 → 1,0).
- Bitki boyu h tek bir değer: FAO-56 Tablo 12'deki boy, orta ve son dönem için aynı.
  (FAO: "genelde orta dönem için tek bir h kullanılır".)
- Tablo değeri aralıksa (mısır Kc_end 0,35–0,60) orta değer kullanılır (bugünkü kural) —
  0,45 sınırı bu orta değere uygulanır (bkz. K2).
- Dönem sınırları, mevcut Kc eğrisindeki FAO-56 Tablo 11 oranlarıyla bulunur.
- POWER ~50 km'lik bir hücre; tarla nemini değil bölge nemini verir.

## 6. Testler

- **FAO-56 Örnek 27** (kesin test): mısır, Kc_mid 1,20, h = 2 m.
  Taipei (u2 1,3, RHmin 75) → **1,07**; Mocha (u2 4,6, RHmin 44) → **1,30**.
- Kc_end ≤ 0,45 ise değişmez; > 0,45 ise denk. 65 uygulanır.
- RHmin = 45 ve u2 = 2 iken Kc tablo değerine eşit kalır.
- Sınırlar: u2 = 0,5 ile 1,0 aynı sonucu verir; h < 0,1 m ise düzeltme yok.
- Denk. 63: Tçiğ = Tmax ise RHmin = %100.
- Dönem ortalaması: yapay bir iklimde orta dönem günlerinin doğru seçildiği.
- (Box 14 buğday tablosu grafikten okunmuş, yuvarlanmış; yalnız gevşek kontrol.)

## 7. Beklenen etki (deneme betiği, yağmur POWER, susuz, yerel takvim açık)

Kc_mid değişimi en iyi ekim penceresinde, 25 yılın ortancası. B = önerilen yol.

| Nokta | Kc_mid değişimi (B) | Mevsim su ihtiyacı (ETc) | En iyi pencere puanı |
|---|---|---|---|
| Konya (kurak, yaz) | buğday +0,01, mısır +0,10, ayçiçeği +0,08 | buğday 476 → 477 mm, mısır 873 → 947 mm (+%8) | en fazla −0,007 (ayçiçeği 0,113 → 0,106) |
| Pencap (musonda nemli) | muson ürünleri −0,01…−0,04, kış buğdayı +0,05 | mısır 370 → 360, sorgum 511 → 493 mm | en fazla +0,010 (sorgum 0,600 → 0,610) |
| Nakuru (nemli, sakin) | 0…−0,04 (mısır +0,02) | ayçiçeği 391 → 379 mm | en fazla +0,013 (darı 0,798 → 0,811) |

- En iyi ekim tarihi, değerlendirilebilen 32 ürün/nokta çiftinin yalnız birinde değişiyor
  (Nakuru patates 16 Nis → 1 May; ikisi zaten neredeyse eşit puanlı).
- A yolu aynı yönde ama daha "nemli": Kc'ler 0,01–0,02 daha düşük.
- Yani: su ihtiyacı (mm) kurak yazda gözle görülür artıyor, sıralamalar
  neredeyse aynı kalıyor. Bu beklenen bir sonuç: FAO-56 da denk. 62'nin
  nem ve rüzgâra "çok duyarlı olmadığını" yazıyor.
- Rotasyon önerileri ayrıca kontrol edilmedi; puan farkları ≤ 0,02 olduğu için
  küçük değişim bekleniyor. Uygulama sırasında ölçülüp METHOD.md'ye yazılacak.

## 8. Karar vermeniz gerekenler

**K1 — RHmin kaynağı**
- **a) Çiğ noktası T2MDEW (önerilen):** FAO-56'nın tercih ettiği yol, daha doğru.
  Bedeli: POWER'a 1 parametre, demo önbelleğini yeniden indirmek (internet gerekir).
- b) Mevcut RH2M: yeni veri yok, ama Kc'yi biraz düşük (≈0,01–0,02) hesaplar.

**K2 — Aralıklı Kc_end (mısır, börülce 0,35–0,60)**
- **a) Orta değer 0,475 ile devam (önerilen):** bugünkü kuralla tutarlı; 0,45'i aştığı için düzeltilir.
- b) Tane hasadı için alt değer 0,35: düzeltme yapılmaz ama tüm uygulamada
  mısırın su ihtiyacı değişir (ayrı bir karar olur).

**K3 — Sonraya bırakılan:** ET0 hesabında da çiğ noktasını kullanmak (denk. 14,
FAO'nun tercih ettiği). Bu tüm ET0 değerlerini artırır ve her sonucu
değiştirir; ayrı bir adım olarak, K1 = a seçilirse önerilir. Şimdi yapılmayacak.
