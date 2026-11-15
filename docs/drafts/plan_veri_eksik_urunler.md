# Plan: Hâlâ "veri eksik" olan 9 ürün (kalan iyileştirmeler, madde 2)

Durum: **uygulandı 2026-11-14** (kullanıcı ara onay beklemeden ilerlemeyi istedi; kararlar
aşağıda, varsayımlar işaretli). Sonuç: METHOD.md "ECOCROP crops" → Cut forage;
DATA_SOURCES.md §5 "Crops still without data — source search (2026-11-14)".

## 1. Durum

Değerlendirilemeyen 9 ürün: kolza, hardal, karabuğday, çim (Lolium), berseem (İskenderiye
üçgülü), fiğ, facelya, Sudan otu, yonca. Bir ürünün değerlendirilmesi için gerekenler:
FAO-56 Kc (su), sıcaklık sınırları, mevsim/dönem uzunlukları.

## 2. Araştırma (ayrıntı: DATA_SOURCES §5)

| Ürün | Kc | Sıcaklık | Dönem uzunluğu |
|---|---|---|---|
| Sudan otu | FAO-56 ✔ | **ECOCROP 9970** (*Sorghum × drummondii* = crops.yaml'daki tür) ✔ — *S. sudanense* sayfası boştu | FAO-56 "Sudan, 1. biçim" ✔ |
| Berseem | FAO-56 ✔ | ECOCROP 10522 ✔ | FAO-56'da yok → yonca 1. biçim benzetmesi |
| Kolza | FAO-56 ✔ (Pereira 2021 güncel değer) | ECOCROP 549 ✔ | **yok** |
| Hardal (*Sinapis alba*) | yok (Pereira 2021 yalnız *B. juncea*) | ECOCROP 9787 ✔ | **yok** |
| Çim (*L. multiflorum*) | FAO-56 ✔ | ECOCROP 7389 ✔ | **yok** (yalnız sıcak mevsim otu satırları) |
| Karabuğday | **yok** | ECOCROP 2285 ✔ | **yok** |
| Fiğ, facelya | **yok** | **yok** (ECOCROP'ta yok) | **yok** |
| Yonca | FAO-56 ✔ | — | çok yıllık; motor tek yıllık mevsim modelliyor |

Pereira ve ark. 2021 (FAO-56 güncellemesi, açık kopya) dönem uzunluğu vermiyor; yazarlar
FAO-56'nın gösterge sürelerini kullanmamayı öneriyor.

## 3. Kararlar (varsayım = **V**)

- **K1 – Sudan otu eklenir.** ECOCROP 9970 + FAO-56 "Sudan, 1. biçim" (75 gün).
  **V:** yalnız ekimden ilk biçime kadar modellenir, sonraki biçimler modellenmez (etiketli).
- **K2 – Berseem eklenir.** ECOCROP 10522 + **benzetme V:** FAO-56'da berseem satırı yok;
  yonca 1. biçim satırı (iki satırın medyanı → 60 gün) kullanılır. İkisi de biçilen yem
  baklagili (Fabaceae), FAO-56 Tablo 12'de ikisi de "biçim etkileri ortalaması" ile verilir.
  Nohut/çavdar örneğindeki gibi etiketli.
- **K3 – Bu iki yem bitkisi rotasyon önerilerinde kullanılmaz** (`first_cut_only`).
  Sebep (ölçüldü): yalnız ilk biçim hesaplanınca 60–75 günlük, ucuz, yem + azot puanı veren
  ürün gibi görünüyorlar ve 6 demo durumunun 6'sında da önerilere giriyorlardı (ör. Konya
  kuru: arpa → berseem 0,629; berseem'in kendi puanı 0,24). Tarlada gerçekte kaç ay kaldıkları
  (kaç biçim) bilinmiyor. Ürün listesinde görünürler; rotasyon sayfası adlarını ve nedenini yazar.
  Kullanıcının kendi rotasyonunda yazarsa o rotasyon yine puanlanır.
- **K4 – Kolza, hardal, çim eklenmez:** dönem uzunluğu için kaynak yok. En yakın FAO-56
  satırları uygun değil ("Crucifers" yeşil hasat edilen sebzeler; yerel kışlık kolza kışı
  tarlada geçirir ve sabit uzunlukta bir mevsimle gösterilemez; çim için yalnız sıcak mevsim
  otu satırları var). Hardalda ayrıca Kc yalnız başka türe (*B. juncea*) ait.
- **K5 – Karabuğday, fiğ, facelya eklenmez:** Kc kaynağı yok (fiğ, facelya ECOCROP'ta da yok).
  Bunlar örtü bitkisi olarak zaten ayrı bir modeli bekliyor (önceki karar K3-b).
- Yonca: çok yıllık bir stand modeli mimari değişiklik gerektirir; yapılmadı (kullanıcıya soru).

## 4. Sonuç

- Değerlendirilebilir ürün 41 → **43**; önerilen rotasyonlar demo noktalarında **değişmedi**.
- İlk biçim için en iyi pencereler: Punjab tam sulama berseem 10-16 ve Sudan otu 09-01 (1,00);
  Punjab kuru Sudan otu 07-01 (0,73, muson); Nakuru kuru berseem 07-01 (0,87).

## 5. Açık sorular (kullanıcı)

- Çok-biçimli yem bitkileri ve yonca için biçim sayısı / tarlada kalma süresi yerel bilgiyle
  (kullanıcı girdisi) verilebilir mi? O zaman rotasyonlarda kullanılabilirler.
