# Plan: Konya’da POWER yağış fazlası (iyileştirme listesi madde 6)

Durum: **onaylandı 2026-11-14 (K1-a, K2 %30, K3-a) ve uygulandı.** Sonuç: METHOD.md
"POWER rain check (CHIRPS)". K3-a: Punjab’da 2001’den beri eksiksiz ayı olan istasyon yok.

## 1. Sorun

Uygulama yağış için varsayılan olarak NASA POWER kullanıyor. Konya noktasında
(Çumra, 37,60 / 32,75) POWER yılda **560 mm**, uydu yağışı IMERG **453 mm**
diyor (2001–2024). Fark çoğunlukla Kasım–Şubat’ta. METHOD.md şimdiye kadar
"istasyon verisi olmadan hangisi doğru bilemeyiz" diyordu.

## 2. Yeni bulgular (2026-11-14)

| Kaynak | Ne | Lisans | Konya, yıllık ort. 2001–2024 |
|---|---|---|---|
| NASA POWER `PRECTOTCORR` | MERRA-2 düzeltilmiş, ~0,5° | NASA, serbest | 560 mm |
| NASA GPM IMERG V07 aylık | uydu + yer ölçümü, 0,1° | NASA, serbest | 453 mm |
| **CHIRPS v2.0 günlük** (`UCSB-CHG/CHIRPS/DAILY`, Earth Engine) | uydu (kızılötesi) + istasyon, 0,05° | **kamu malı** (STAC: "public domain", telif hakkından feragat) | **309 mm** |
| **NOAA GHCN-Daily, KONYA istasyonu** `TUM00017244` (37,98 / 32,56; noktaya 45 km) | yağmur ölçer | NOAA, serbest erişim (yalnız tanı için; depoya konmaz, koşullar uygulamada ayrıca doğrulanacak) | kayıt boşluklu: 2001–2024’te yalnız **59 ay eksiksiz** |

İstasyonun eksiksiz olduğu 59 ayda (aynı aylar, toplam):

| Kaynak | İstasyona oranı | Aylık korelasyon |
|---|---|---|
| POWER | **1,63** | 0,80 |
| IMERG | 1,39 | 0,89 |
| CHIRPS | **0,98** | 0,78 |

Ay ay (bu ayların ortalaması, mm): Aralık’ta istasyon 45, POWER 104, IMERG 80,
CHIRPS 50; Ocak’ta 54 / 97 / 72 / 42. Yaz aylarında kaynaklar yakın.

**Yorum (dikkatli):**
- POWER Konya ovasında kışın açıkça fazla görünüyor; IMERG de fazla ama daha az.
- CHIRPS istasyonla uyumlu. Ancak CHIRPS istasyon verilerini kullanır; Konya
  istasyonu içinde olabilir, yani tam **bağımsız değil**.
- Yağmur ölçerler karı eksik ölçer; kışın gerçek yağış istasyondan biraz fazla
  olabilir. Bu, farkın bir kısmını açıklayabilir ama %60’ı açıklamaz.
- İstasyon şehirde, nokta Çumra’da (45 km). Her ikisi de aynı ovada.

## 3. Tahmini etki (geçici betik; POWER günlük yağışı aylık CHIRPS toplamına ölçeklenerek, IMERG seçeneğiyle aynı kural)

| Nokta (yağmurla) | Ölçek çarpanı (ortanca) | Örnek ürünler, en iyi pencere puanı POWER → CHIRPS |
|---|---|---|
| Konya | **0,59** | kışlık buğday 0,38 → 0,33; arpa 0,48 → 0,41; mercimek 0,25 → 0,22 (sıralama aynı) |
| Punjab | 0,96 | küçük (±0,03) |
| Nakuru | 0,93 | küçük (−0,06 … +0,04) |

Etki Konya’da beklenenden küçük: yağışın çoğu kışın, bitki su tüketiminin düşük
olduğu dönemde düşüyor. Nadas yılında toprağa biriken su ise kış yağışından
geldiği için daha çok azalır (ayrıca ölçülecek).

## 4. Kararlar (onayınız gerekiyor)

**K1 — Varsayılan yağış kaynağı.**
- **K1-a (önerim):** POWER varsayılan kalır (NASA verisi, günlük, her yerde).
  CHIRPS **üçüncü seçenek** olarak eklenir (`precip_source=chirps`, IMERG ile
  aynı aylık ölçekleme kuralı). POWER’ın CHIRPS’ten %30’dan fazla ıslak olduğu
  noktalarda kartta uyarı çıkar: "Bu bölgede NASA POWER yağışı fazla olabilir;
  CHIRPS ile deneyin".
- K1-b: CHIRPS varsayılan olur (50° K – 50° G arası), dışında POWER.
- K1-c: Yalnız belgelenir, kod değişmez.

**K2 — Uyarı eşiği.** %30 (bugünkü "büyük fark" eşiğiyle aynı, **varsayım**). Değiştirmek ister misiniz?

**K3 — İstasyon kontrolü.** GHCN-Daily yalnız belgedeki doğrulamada kullanılır
(uygulamaya ve depoya girmez). Punjab’da yakın istasyonlar var (Jagraon 12 km,
Ludhiana 29 km); aynı kontrol orada da yapılsın mı?
- **K3-a (önerim):** Evet, Punjab’ı da ekleyelim (Nakuru’ya en yakın istasyon 125 km, anlamsız).
- K3-b: Yalnız Konya.

## 5. Onaydan sonra (K1-a, K2 %30, K3-a varsayımıyla)

1. `app/sources/gee.py`: CHIRPS aylık toplam katmanı (sunucu tarafında, tek istek); demo önbelleğine `gee:chirps` ile eklenir.
2. `app/harmonize/rainfall.py`: ölçekleme kuralı genel hale getirilir (IMERG ve CHIRPS).
3. API: `precip_source=power|imerg|chirps`; POWER/CHIRPS oranı ve uyarı yanıtta.
4. Arayüz: yağış kaynağı seçicisine CHIRPS, Türkçe uyarı metni.
5. Testler: ölçekleme, uyarı eşiği, demo önbelleği, API parametresi.
6. Belgeler: DATA_SOURCES (CHIRPS + GHCN-D sonuçları), CREDITS (CHIRPS), METHOD ("POWER vs IMERG vs CHIRPS" bölümü, Konya yorumu), kılavuz.

## 6. Ayrıca not

- Rotasyon araması 50 üründe bazı iyi rotasyonları kaçırıyor ve istek 10–28 s
  sürüyor (METHOD "Known limitations"). Bu ayrı bir iş; yağış konusundan bağımsız.
