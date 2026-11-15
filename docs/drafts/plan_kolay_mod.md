# Plan: Kolay mod (çiftçi için doğrudan plan) — aşama 7'nin devamı

Durum: **uygulandı 2026-11-14.** Kullanıcı isteği: "Ne ekeceğimizi sormasın, otomatik olsun;
'bu rotasyonu yap, şu kadar sula, şu zaman ek' desin. Mevcut mod da kalsın, başta hangisi
olacağını seçelim. Eğimi olmayan yerde erozyon saçma. Hayvan otlatmayı da söylesin."

## Kararlar

- **K1 – Başlangıçta mod seçimi:** İlk açılışta iki büyük düğme: *Kolay mod* (bana ne yapacağımı
  söyle) ve *Uzman mod* (ayarları ben seçeyim; bugünkü ekranlar). Seçim tarayıcıda saklanır,
  üst çubuktan her an değiştirilebilir.
- **K2 – Kolay modda soru yok:** Tarla seçilip "sulayabiliyor musunuz?" yanıtlandıktan sonra
  rotasyon, varsayılan önceliklerle (hepsi 3) **otomatik** hesaplanır. Ekranda 1. öneri bir
  "plan" olarak yazılır; "Başka seçenek" ile 2. ve 3. öneri görülebilir.
- **K3 – Plan satırları (yalnız modelin hesapladığı sayılar):**
  - Ekim: modelin en iyi ekim tarihi ("16 Kasım civarı"); hasat: ortanca hasat tarihi.
  - Su: sezonun yağmur açığı (mm, 25 yılın ortancası). 1 mm = dekar başına 1 ton su (birim
    çevirisi). Sulama sayısı/aralığı **yazılmaz** (modelde yok).
  - Nadas yılı: "ekmeyin"; sonraki ürüne kalan su (model) yazılır.
  - Toprak hazırlığı (sürüm): tarih **yazılmaz** (modelde yok); "ekimden önce, yerel uygulamaya
    göre" denir.
- **K4 – Hayvan otlatma:** Otlatma modellenmiyor. Tarlanın boş kaldığı aylar (modelden) gösterilir
  ve "bu aylarda anızı otlatabilir veya örtü bitkisi ekebilirsiniz; yerel uzmana danışın" diye
  **seçenek** olarak yazılır (sayı yok). Yem bitkisi olan ürünlerde "hayvan yemi" notu.
- **K5 – Düz arazide erozyon:** Eğim kuralı arazinin düz olduğunu söylüyorsa (`flat_terrain`), erozyon
  önceliğinin ağırlığı sunucuda 0 yapılır (su erozyonu eğimle oluşur; RUSLE eğim katsayısı orada
  ~0,05) ve kartlar/ayarlar "Arazi düz: erozyon riski düşük" der. Rüzgâr erozyonu modellenmiyor.
