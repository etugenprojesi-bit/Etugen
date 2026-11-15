# Plan: eksik ürün sıcaklık parametreleri (iyileştirme listesi madde 4)

Durum: **onaylandı 2026-11-12 (K1-a, K2-a, K3-a, K4) ve uygulandı** — arpa
eklendi, bakla eklenmedi. Gerçek etki: METHOD.md "WOFOST thermal time". Arama kaydı:
`docs/DATA_SOURCES.md` §5, "Literature search … round 2 (2026-11-12)".

## 1. Bugün durum ne? (yükleyici çalıştırılarak sayıldı)

35 ürünün **14’ü** değerlendirilebiliyor (METHOD.md’deki "11 of 35" ve
kılavuzdaki "35 üründen yalnız 11’i" eski):

| Durum | Ürünler |
|---|---|
| Tam (t_base, t_sum/t_opt, ısı eşikleri) — 10 | kışlık ve yazlık buğday, mısır, çeltik, kuru fasulye, soya, yer fıstığı, pamuk, patates, manyok |
| Değerlendiriliyor ama **ısı eşiği yok** (güven "düşük") — 4 | sorgum, darı, mercimek, ayçiçeği |
| "Veri eksik" (sıcaklık sınırı yok) — 21 | arpa, yulaf, bakla, kuru bezelye, börülce, aspir, susam, keten, tatlı patates, şeker pancarı, sudan otu · ayrıca FAO-56 Tablo 11 satırı da olmayanlar: nohut (yalnız t_base var), kolza, yonca, İskenderiye üçgülü, çim, çavdar, fiğ, hardal, facelya, karabuğday |

Son 10 üründe sezon tablosu da yok; sıcaklık bulunsa bile şu an
değerlendirilemezler. Bu yüzden asıl hedef ilk 11 ürün + 4 ürünün ısı eşiği.

## 2. Ne bulundu?

### Kullanılabilir (orijinal kaynakta okundu)

Kaynak: **Boons-Prins, de Koning, van Diepen, Penning de Vries (1993).**
*Crop-specific simulation parameters for yield forecasting across the European
Community.* Simulation Reports CABO-TT 32, Wageningen. Açık PDF:
<https://edepot.wur.nl/308997> (DOI yok; WUR kalıcı bağlantısı). Bu, WOFOST
modelinin AB için kalibre edilmiş parametreleridir. Aynı sayılar WUR’un
[WOFOST_crop_parameters](https://github.com/ajwdewit/WOFOST_crop_parameters)
deposunda **EUPL-1.2** (OSI onaylı) lisansla da dağıtılıyor.

| Ürün | Değer | Yer (rapor) | Not |
|---|---|---|---|
| **Arpa** (yazlık arpa, AB15) | gelişme tabanı 0 °C (DTSMTB: 0 → 0, 35 → 35, üstü 35’te sabit) | Ek C3, Tablo C3b (s. C III-3) | |
| | çıkış–çiçeklenme 800 + çiçeklenme–olgunluk 750 = **1550 °C·gün** | aynı | kalibrasyon: AB ekim/çiçek/olum takvimleri (Ek C3 Tablo C3a, Ek C4) |
| | ekim–çıkış: taban 3 °C, 110 °C·gün | aynı | ⚠️ WUR deposundaki YAML burada **0 °C** yazıyor; rapor **3 °C**. Raporu esas alırız. |
| **Bakla** (field bean, AB15) | taban 0 °C; ekim–çıkış 100 + çıkış–çiçek 833 + çiçek–olum 1351 = **2284 °C·gün** | Ek G1 (s. G I-1/2), Ek G4 başlığı (s. G IV-1: "base temperature of 0 °C") | DTSMTB doğrusal değil: 0 → 0, 20 → 22,5, 25 → 25, üstü 25’te sabit |

İkisinde de **ısı eşiği (t_heat/t_ext) yok** → güven "düşük", sıcak sezon
ekimleri cezalandırılmaz (mercimek ve ayçiçeğindeki durumla aynı).

### Bulundu ama önermiyorum

| Ürün | Neden |
|---|---|
| Şeker pancarı | Raporda çelişki: metin "2. evre taban 0 °C" diyor, veri dosyası 3 °C; ayrıca sezon sonu fizyolojik olum değil **hasat tarihi** (işletme kararı). |
| Börülce | van Heemst 1988 (CABO-TT 17, edepot.wur.nl/218353) Tablo 9 farklı çeşitlerin değerlerini veriyor (660/740 ve 370/630 °C·gün); Muchow 1985 toplamlarının taban sıcaklığı yazmıyor; WUR YAML iki farklı çeşidi karıştırmış. |
| Tatlı patates | WUR YAML’daki sayılar (416/1436) van Heemst Tablo 18’de yok (orada yalnız gün sayıları var) → izlenemiyor. |
| Kolza | Sıcaklık toplamları "1 Ocak’tan başlayarak" tahmin edilmiş (ekimden değil); FAO-56 Tablo 11 satırı da yok. |
| Sorgum/darı ısı eşikleri | Tek kaynak bir yüksek lisans tezi (Nzimande 2021, UKZN, Tablo 3.6 — SIMPLE yerel kalibrasyon: sorgum 44/50 °C, darı 48/50 °C); hakemli değil, mısır değerleri Zhao 2019’dan da farklı. |

### Bulunamadı

Yulaf, kuru bezelye (bulunan çalışmalar *taze/konserve* bezelye hasadı),
aspir, susam (taban 8–15 °C arası çelişkili), keten (PMC makalesi bot
kontrolünün arkasında), sudan otu; mercimek ve ayçiçeği için ısı eşikleri.
**SIMPLE orijinali (Zhao 2019)** hâlâ kapalı: Unpaywall "closed, depo kopyası
yok", HAL bot kontrolü (aşılmadı). SIMPLE değerleri ikinci el kalmaya devam ediyor.
FAO ECOCROP kullanılmadı (kural).

## 3. Demo noktalarında tahmini etki

Geçici bir betikle, çevrimdışı (demo_cache), **yaklaşık** girişle (K2-b:
arpa t_base 0 / 1660 °C·gün, bakla 0 / 2284 °C·gün) hesaplandı:

| Nokta | Arpa (en iyi pencere) | Bakla (en iyi pencere) | Rotasyonlar |
|---|---|---|---|
| Konya, yağmurla | 10-01 → 05-21, puan 0,48 (buğday 0,38); GGCMI takvimi 11-01 → 06-23 ✔ | 09-01 → 05-23, 0,41 | İlk öneri **arpa → bakla** (0,55; önce buğday → mercimek 0,51) |
| Konya, tam sulama | 01-01, 0,84 | **07-01 → 10-12, 1,00** ⚠️ yaz ortası | lentil → arpa+bakla → buğday (0,645) |
| Punjab, yağmurla | 11-16, 0,24 (su yetmiyor) | **06-16 → 08-24 (muson), 0,78** ⚠️ | 3 önerinin hepsi **muson baklası** ile başlıyor ⚠️ |
| Punjab, tam sulama | 07-16, 54 gün ⚠️ (GGCMI sulu arpa takvimi burada Haziran; kaynak "unknown") | 08-16, 1,00 ⚠️ | bakla 01-01 + sorgum çift ürün |
| Nakuru, yağmurla | 10-01 → 12-29 (90 gün); GGCMI 10-12 → 01-23 ✔ | 05-01, 0,77 | millet → mercimek ilk sırada kalıyor; bakla+arpa 2. |

Özet: **arpa makul** (GGCMI takvimi pencereyi sınırlıyor, Konya ve Nakuru’da
takvimle uyumlu). **Bakla sorunlu**: GGCMI takviminde yok ve ısı eşiği yok, bu
yüzden sıcak mevsime (Punjab musonu, Konya yazı) ekiliyor ve Punjab
önerilerinin hepsine giriyor. Bu tarımsal olarak yanlış (bakla Punjab’da kış
ürünüdür), ama kaynaksız bir sıcaklık sınırı koyamayız.

## 4. Kararlar (sizin onayınız gerekiyor)

**K1 — Kaynak türü.** Boons-Prins 1993 hakemli dergi değil, açık bir teknik
rapor (DOI yok). Kabul edelim mi?
- **K1-a (önerim):** Evet, yalnız orijinal raporda okunan değerler; DATA_SOURCES
  ve CREDITS’e "teknik rapor, WUR edepot" diye yazılır.
- K1-b: Hayır, yalnız hakemli makale → bu turda hiçbir ürün eklenmez.

**K2 — Gün-derece hesabı.** WOFOST günlük katkıyı bir tabloyla sınırlıyor
(arpa 35 °C’de, bakla 25 °C’de sabit) ve ekim–çıkış evresini ayrı tabanla sayıyor.
- **K2-a (önerim):** Motora iki isteğe bağlı alan: `dev_rate_table` (parça
  parça doğrusal günlük katkı) ve `emergence: {t_base, t_sum}`. Kaynağa sadık;
  mevcut ürünlerin sonucu **değişmez** (alan yoksa eski formül). ~40 satır + test.
- K2-b: Kod değişmeden t_base 0 + toplam (1660 / 2284). Yaklaşıktır; bakla için
  15 °C’de günlük katkıyı ~%11 az (sezon uzun), 30 °C’de ~%17 fazla (sezon kısa) sayar. "Varsayım" diye etiketlenir.

**K3 — Bakla ne olsun?**
- **K3-a (önerim):** Bu turda **yalnız arpa** eklenir. Bakla "veri eksik"
  kalır, notunda "gelişme verisi var, sıcaklık stresi eşiği yok" yazar.
- K3-b: Bakla da eklenir, düşük güvenle; sıcak sezon önerileri riskini kabul ederiz.
- K3-c: Bakla eklenir ama rotasyon önerilerine girmez (yalnız ürün kartında görünür).

**K4 — Sayı düzeltmesi.** METHOD.md "11 of 35" ve KULLANIM_KILAVUZU.md
"35 üründen yalnız 11’i" → gerçek sayı (bugün 14; K3-a ile 15). Ayrıca
"10’unda ısı eşikleri de var" bilgisi eklenir.

## 5. Onaydan sonra yapılacaklar (K1-a, K2-a, K3-a varsayımıyla)

1. `data/crop_phenology.yaml`: kaynak `boonsprins1993` (atıf, URL, sayfa,
   `verified_against_original: true`) ve arpa bloğu: t_base 0, t_sum 1550,
   dev_rate_table [[0,0],[35,35],[45,35]], emergence {t_base 3, t_sum 110}; notta
   "yazlık arpa AB kalibrasyonu, vernalizasyon yok, ısı eşiği yok".
2. `crops.py` / `engine.py`: iki isteğe bağlı alan (K2-a).
3. Testler: tablo enterpolasyonu ve üst sınır; çıkış evresi ayrı tabanla;
   alan yoksa eski sonuç aynen (mevcut 140 test); arpa artık `evaluated`,
   güven "low"; yükleyici sayımı (15 değerlendirilebilir).
4. Belgeler: DATA_SOURCES §5 tablosu, METHOD (yöntem + sayı + etki), kılavuz
   (sayı), CREDITS (Boons-Prins 1993 raporu; WUR YAML’ı yalnız karşılaştırma
   için kullanıldı, EUPL-1.2).
5. Demo önbelleği değişmez (yalnız veri dosyası değişiyor).

## 6. Açık sorular / sonraki adımlar

- Punjab’da GGCMI **sulu arpa** takvimi Haziran ekimi diyor (veri kaynağı
  "unknown"). Takvim hatası olabilir; madde 5 (MODIS NDVI doğrulaması) ile bakılabilir.
- Mercimek, ayçiçeği, sorgum, darı ve bakla için ısı eşiği bulmak ayrı bir
  arama gerektiriyor (ör. çiçeklenmede kritik sıcaklık deneyleri); bulunursa
  SIMPLE’ın Tmax tabanlı ısı faktörüne nasıl çevrileceği ayrıca karar ister.
- FAO’dan ECOCROP yanıtı gelirse çapraz kontrol kaynağı olarak eklenebilir.
