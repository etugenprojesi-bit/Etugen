# Plan: Punjab'daki GGCMI takvim tuhaflıkları (kalan iyileştirmeler, madde 4)

Durum: **uygulandı 2026-11-14** (kullanıcı ara onay beklemeden ilerlemeyi istedi; kararlar
aşağıda, varsayımlar işaretli). Sonuç: METHOD.md "Local sowing calendar (GGCMI) — rule";
DATA_SOURCES.md §8 "GGCMI data source codes".

## 1. Sorun

Punjab'da (30,80 / 75,60) GGCMI takvimi kuru bezelyeyi Haziran'da, sulu arpayı Haziran'da,
sulu şeker pancarını Nisan'da (±45 gün → Şubat–Mayıs) ekiyor. Bu pencerelerde model puanı 0;
takvim dışındaki Kasım/Ekim pencereleri 1,00 / 0,81. Takvim kuralı yüzünden bu ürünler önerilere
hiç giremiyordu.

## 2. Bulgular (hücre değerleri `data/ggcmi_crop_calendar.npz`)

- GGCMI her hücre için veri kaynağını yazıyor (`data_source_used`): 1–9 adlı kaynaklar
  (MIRCA2000, SAGE, Hindistan tarım istatistikleri …), **0 = adlı kaynak yok** (boşluk doldurma /
  dışdeğerleme; Zenodo kaydı: ekili alan dışındaki hücreler dışdeğerlenir, boşluklar doldurulur).
- Punjab: sulu arpa (06-01) ve sulu şeker pancarı (04-01) **kaynak 0**. Sulu şeker pancarı
  takviminin dünyada hiçbir hücresinde adlı kaynak yok. Kuru arpa 11-01 (MIRCA2000) gözleme dayalı.
- Kuru bezelye 06-11 ve kuru şeker pancarı 06-01 ise adlı kaynaklı (Hindistan istatistikleri,
  MIRCA2000) ama modelin iklim verisiyle bu yaz pencerelerinde ürün hiç yetişmiyor.

## 3. Kararlar (varsayım = **V**)

- **K1 – Kaynak kuralı:** İstenen sistem (kuru/sulu) hücrede boşluk-doldurulmuşsa (kaynak 0) ve
  diğer sistemin adlı kaynağı varsa, diğer sistemin takvimi kullanılır (`fallback_from`, arayüzde
  "sulu tarım için kayıt yok, kuru tarım takvimi"). **V:** sulu tarım, kayıt yoksa kuru tarımla aynı
  mevsimde yapılır (mevcut "sınırlı sulama kuru takvimi izler" varsayımıyla tutarlı). Başka
  seçenek yoksa boşluk-doldurulmuş değer yine kullanılır ve "tahmini takvim" diye etiketlenir.
- **K2 – Çelişki kuralı:** Ürün bir pencerede yetişebiliyor ama yerel ekim gününün ±45 gününde
  **hiçbir** pencere 0'dan büyük puan alamıyorsa, takvim o ürün için uygulanmaz (`calendar_conflict`).
  Kart güveni "düşük" yapar ve nedenini yazar. Gerekçe: takvim, modelde olmayan kısıtları (soğuklama,
  gün uzunluğu …) getirmek için var; takvim penceresi tümüyle başarısızsa ya takvim ya model yanlış,
  hangisi bilinemez; ürünü sessizce 0 göstermek yerine en iyi pencereyi uyarıyla göstermek daha açık.
- Takvimi hiç olmayan veya hiçbir pencerede yetişemeyen ürünlerde değişiklik yok.

## 4. Sonuç (demo noktaları)

- Punjab: sulu arpa takvimi 11-01'e döndü (en iyi 12-01, 1,00); kuru bezelye 11-16 (kuru 0,23,
  tam sulama 1,00).
- **Çözülmeyen:** sulu şeker pancarı artık kuru MIRCA2000 hücresini (06-01) izliyor; orada model
  0,33 (07-16) bulduğu için çelişki kuralı devreye girmiyor; daha iyi takvim dışı pencere
  (10-16, 0,81) yalnız gösteriliyor. Adlı kaynaklı bir değeri keyfî bir eşikle atmak istemedim.
- Rotasyonlar: yalnız tam sulamalı Punjab (0,724 → 0,736; sorgum + mercimek → pamuk + kuru bezelye)
  ve Nakuru (0,772 → 0,776) değişti.
- Yan etki: Nakuru soya (kuru 02-16, sulu 01-01) ve çeltik (10-01) GGCMI mevsimi dışında
  değerlendirilir hâle geldi; güven "düşük", kart nedenini yazar.

## 5. Açık

- Hindistan istatistiklerindeki Haziran bezelyesinin neyi temsil ettiği (yeşil bezelye? başka
  bir baklagil?) bilinmiyor; yerel bilgiyle kontrol edilmeli.
