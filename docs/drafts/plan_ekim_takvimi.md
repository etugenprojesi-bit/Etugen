# Plan: ekim takvimi (kışlık buğday ve diğer ürünler) — onaylandı 2026-11-12 (K1-a, K2 evet, K3 sonra)

Durum: **A seçeneği uygulandı** (docs/METHOD.md "Local sowing calendar"). Kaynaklar: `docs/DATA_SOURCES.md`
bölüm 8. Prob betiği: `scripts/probe/probe_ggcmi_calendar.py`.

## 1. Sorun ne?

Konya'da model kışlık buğdayı **1 Eylül'de ekip 19 Mayıs'ta** hasat ediyor.
Yerel uygulama Ekim ekimi, Temmuz hasadı.

Teşhis: gün-derece hesabı doğru. Modelin 16 Ekim penceresi zaten 2 Temmuz'da
bitiyor (260 gün). Model Eylül'ü seçiyor çünkü erken ekim yaz kuraklığından
kaçıyor (su puanı 0,45'e karşı 0,36). Bunu gerçekte engelleyen üç şey modelde
yok:

1. **Vernalizasyon** (kış soğuğu ihtiyacı) ve **gün uzunluğu**: erken ekilen
   buğday da ilkbahar gelmeden başaklanmaz, yani erken olgunlaşmaz.
2. **Ekim için toprak nemi**: Konya'da Eylül kuru, tohum çimlenmez.
3. Sıcakta hastalık, göllenme gibi modellenmemiş yerel kısıtlar.

Sorun yalnız Konya'da değil. Yerel takvimle karşılaştırınca (aşağıda) Pencap'ta
model buğdayı **Temmuz'da (musonda)** ekiyor; yerelde Kasım. Patates ve kuru
fasulyede de benzer kaymalar var. Önceden bulduğumuz "Pencap'ta mercimek
musonda" hatasıyla aynı kök neden.

## 2. Bulunan kaynaklar

**GGCMI ürün takvimi** (Jägermeyr ve ark. 2021, Zenodo, **CC BY 4.0**):
dünyanın her 0,5° hücresinde 18 ürün için yağışa dayalı ve sulu ekim ve
olgunlaşma günü. Kaynakları: ulusal istatistikler, SAGE, MIRCA2000 vb. Ölçüme
dayalı yerel takvim; tüm dosyalar sıkıştırınca ~1 MB.

| Nokta | Ürün | Modelin seçtiği | Yerel takvim (GGCMI) |
|---|---|---|---|
| Konya | kışlık buğday | 1 Eyl → 19 May | 21 Eki → 9 Tem |
| Pencap | kışlık buğday | 16 Tem → 25 Eyl | 4 Kas → 16 Nis |
| Nakuru | mısır | 16 Mar → 24 Eyl | 12 Eki → 9 Oca |

29 ürün/nokta çiftinin 15'inde ekim günü 45 günden az farklı, 14'ünde daha
fazla. Not: Nakuru'da iki yağmur mevsimi var, GGCMI ise her ürün için tek
mevsim veriyor; oradaki fark her zaman model hatası değil.

**DSSAT CERES-Wheat** (açık kaynak, BSD-3): vernalizasyon ve gün uzunluğu
formülleri ve çeşit parametreleri koddan okundu.

**Önemli bulgu:** modelimizin "kışlık buğday" değerleri Yecora Rojo
çeşidinden geliyor; DSSAT'e göre bu bir **yazlık tip** buğday (vernalizasyon
ihtiyacı çok düşük). Gerçek bir kışlık çeşit için tutarlı parametre seti henüz
kaynaklı değil.

**Ekim için toprak nemi kuralı:** açık kaynakta genel bir eşik bulunamadı.

## 3. Seçenekler

**A. GGCMI'yi "yerel takvim" olarak eklemek (önerilen, şimdi).**
- Her ürün kartında: "Bu bölgede yaygın ekim: 21 Ekim, hasat 9 Temmuz
  (GGCMI)". Yağışa dayalı ya da sulu takvim, seçilen sulamaya göre.
- **Kural (karar K1):** GGCMI'de takvimi olan ürünlerde "en iyi pencere",
  yerel ekim gününün ±45 günü içindeki pencereler arasından seçilir. Diğer
  pencereler silinmez, "yerel takvim dışında" etiketiyle gösterilir.
  - ±45 gün bir **varsayım** (etiketli). GGCMI çok yıllık ortalama veriyor,
    gerçek ekim yıldan yıla kayar.
- Rotasyon motoru yalnız bu pencereleri kullanır, böylece musonda buğday gibi
  öneriler çıkmaz.
- "Farklı ekim zamanlarını da dene" düğmesi kuralı kapatır. İklim
  senaryosunda yeni ekim zamanı aramak bu proje için önemli ("Field Shift").
- Doğrulama: her noktada model–takvim farkı API'de raporlanır. Bu, madde 5
  (uydu doğrulaması) için de temel olur.

**B. CERES-Wheat vernalizasyon ve gün uzunluğu (sonra).** Fiziksel olarak
daha doğru ama kışlık bir çeşit için tutarlı parametre seti gerekiyor.
Bulamazsak SIMPLE (gün-derece) ve CERES (gelişme) parametrelerini
karıştırmış oluruz. Ayrı bir araştırma aşaması öneriyorum.

**C. Ekim nemi kuralı:** kaynak yok, şimdilik yapılmaz. Soru olarak kalır
("Ekimi ilk yağmurdan sonra mı yapıyorsunuz?").

## 4. Senin kararın gereken noktalar

- **K1 — Takvim kuralı:**
  - (a) Önerilen: ±45 gün içinden seç, diğerlerini etiketle, düğmeyle kapatılabilsin.
  - (b) Sadece göster, seçimi değiştirme.
- **K2 — Yeni bağımlılık `h5py`** (BSD-3 lisanslı, yalnız bir kez veri
  dönüştürmek için). GGCMI dosyaları HDF5 biçiminde. Önerim:
  `scripts/build_crop_calendar.py` h5py ile 36 dosyayı tek bir
  `data/ggcmi_crop_calendar.npz` (~1 MB, CC BY 4.0, kaynak gösterilerek)
  dosyasına çevirir. Uygulama çalışırken h5py gerekmez, sadece numpy.
  h5py yalnız `requirements-probe.txt`'e girer. CREDITS ve DEPENDENCIES
  aynı commit'te güncellenir.
- **K3 — B seçeneği** (vernalizasyon) ayrı bir aşama olarak sonra mı?

## 5. Uygulama adımları (onaydan sonra)

1. Dönüştürme betiği + `data/ggcmi_crop_calendar.npz` + ürün kodu eşlemesi
   (`crops.yaml` id → GGCMI kodu, ör. `winter_wheat` → `wwh`). Yalnız
   eşleşen 18 ürün; çavdar örtü bitkisi olarak modellenmediği için kullanılmaz.
2. `app/suitability/calendar.py`: en yakın 0,5° hücre, yağışa dayalı/sulu seçim.
3. Uygunluk motoru: pencerelere `in_local_calendar`; en iyi pencere kuralı (K1).
4. Rotasyon: yalnız takvim içi pencereler (düğme kapalıysa).
5. Arayüz: ürün kartında yerel takvim satırı, takvim dışı etiketi, düğme;
   METHOD.md, CREDITS.md, DATA_SOURCES.md.
6. Testler: hücre seçimi (sınırlar, −180/180), yılın sonunu aşan pencereler
   (Kasım ekimi → Nisan hasadı), K1 kuralı, Konya buğdayı 1–31 Ekim arasında
   seçiliyor mu, Pencap buğdayı Ekim–Aralık arasında mı.

## 6. Beklenen etki (tahmin, ölçülmedi)

- Konya kışlık buğday 16 Ekim'e kayar: puan 0,38 → ~0,31. Daha gerçekçi
  ama daha düşük; nadas sonrası puan da buna göre değişir.
- Pencap buğdayı Kasım'a kayar; yağışa dayalı puanı düşük çıkar (~0,18).
  Gerçekte Pencap buğdayı sulanıyor, bu doğru bir uyarı olur.
- Bazı öneriler değişebilir; demo sayıları METHOD.md'de güncellenir.
