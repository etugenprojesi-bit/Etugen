# Plan: Punjab buğdayının erken olgunlaşması ve eksik sıcak stresi eşikleri (kalan iyileştirmeler, madde 3)

Durum: **K1-a kullanıcı tarafından seçildi ve uygulandı (2026-11-14).** Pencap'ta (kutu + GGCMI
kaynağı Hindistan istatistikleri) kışlık ve ilkbahar buğdayı t_sum 2482–2639 °C·gün kullanır.
MODIS farkı −20 → −4 gün. Eşikler için uygun kaynak bulunamadı (K2).

## 1. Punjab buğdayı

**Sorun:** MODIS karşılaştırmasında Punjab'da kışlık buğday (GGCMI ekimi 11-01) uydu
yeşil-kaybından ~20 gün önce olgunlaşıyor. Parametreler tek bir ilkbahar tipi çeşitten
(Yecora Rojo, SIMPLE, t_sum 2200 °C·gün, taban 0 °C) geliyor.

**Kaynak (tam metin okundu):** Kaur, H., Kingra, P.K., Singh, L., Kaur, S., Bora, S. (2025).
Phenological and yield responses of wheat to sowing dates and varieties in Punjab: an
agro-climatic index approach. *Indian Journal of Agronomy* 70(4): 499–502.
doi:10.59797/ija.v70.i4.5677. PAU Ludhiana, rabi 2023-24, çeşitler PBW 826, PBW 766, PBW 550.
Tablo 1 (s. 500): ekimden olgunluğa gün: 6 Kasım **154**, 24 Kasım **146**, 12 Aralık **136**;
çeşitler 138–154 gün. Aynı tabloda GDD (6 Kasım 1773,7 °C·gün) var ama **taban sıcaklığı
yazılmamış** → kurallarımıza göre t_sum olarak kullanılamaz (t_sum yalnız kendi tabanıyla saklanır).

**Karşılaştırma (POWER, Punjab demo noktası, aynı sezon 2023-24):**

| Ekim | Gözlenen olgunluk | Model (2200 °C·gün, taban 0) | Fark | POWER taban-0 toplamı gözlenen sezonda |
|---|---|---|---|---|
| 6 Kasım | 154 gün (7 Nisan) | 138 gün (22 Mart) | −16 gün | 2639 °C·gün |
| 24 Kasım | 146 gün (17 Nisan) | 133 gün (4 Nisan) | −13 gün | 2564 °C·gün |
| 12 Aralık | 136 gün (25 Nisan) | 127 gün (16 Nisan) | −9 gün | 2482 °C·gün |

Yani bağımsız bir saha gözlemi MODIS bulgusunu doğruluyor: Punjab çeşitleri modeldekinden
~2 hafta uzun. Tek sezon, tek istasyon; POWER hücresi Ludhiana'ya ~25 km.

**K1 – Seçenekler (kullanıcının kararı; mimari değişiklik):**
- **a) Bölgeye özgü çeşit (önerim):** `crop_phenology.yaml`'da bir ürüne bölgeye bağlı ek parametre
  seti (ör. GGCMI takviminin kaynağı "India agricultural statistics" olan hücreler veya bir enlem-boylam
  kutusu). Punjab buğdayının t_sum'u, gözlenen sezon uzunluklarından POWER ile türetilir
  (taban 0: 2482–2639 °C·gün; **V:** tek sezon, türetilmiş değer, etiketli).
- b) Hiçbir şey değiştirmemek, yalnız kartta "yerel çeşitler daha uzun olabilir" uyarısı (şu anki durum).
- c) winter_wheat t_sum'unu her yerde artırmak — **önerilmez**: Konya ve Nakuru'yu doğrulamasız değiştirir.

## 2. Sıcak stresi eşikleri (sorgum, darı, mercimek, ayçiçeği, arpa)

SIMPLE türü eşik (t_heat: büyümenin sıcakla azalmaya başladığı Tmax; t_ext: büyümenin durduğu
Tmax) için hakemli, açık, DOI'li kaynak aranıp bulunamadı:
- SIMPLE'ın kendi tablosu (Zhao ve ark. 2019) bu beş ürünü içermiyor.
- Sorgum/darı SIMPLE değerleri yalnız bir yüksek lisans tezinde (Nzimande 2021, hakemsiz) — önceki
  turda da reddedildi.
- Literatürdeki "maksimum gelişme sıcaklığı" ve polen canlılığı eşikleri (ör. Luo 2011, Hatfield ve
  ark. 2011) gelişme/üreme eşikleri; SIMPLE'ın büyüme eşiğine eşlenmesi varsayım olur, kurallarımız
  (yalnız `note`'a yazılır) buna izin vermiyor.

**K2:** Eşikler `null` kalır; bu ürünlerin güveni "düşük" ve sıcak mevsim ekimleri cezalandırılmaz
(METHOD "Known limitations"). Yerel takvim kuralı bu boşluğu kısmen kapatıyor.
