# Plan: FAO ECOCROP ile ürün sayısını artırma

Durum: **onaylandı 2026-11-12 (K1-a … K5-a) ve ilk adım (11 ürün) uygulandı.** Gerçek etki:
METHOD.md "ECOCROP crops". Yeni 15 ürün (D) 2026-11-13’te eklendi (kullanıcı: "1’i yap, bitince main’e aktar").

Kullanıcı kararı (2026-11-12): hem eksik 20 ürün kapatılsın hem yeni ürün
eklensin; FAO ECOCROP **etiketlenerek** kullanılsın (lisans belirtilmemiş,
FAO’ya soruldu). Bu karar CLAUDE.md’deki "ECOCROP kullanılmaz" kuralını
değiştirir; CLAUDE.md ve DATA_SOURCES §5 buna göre güncellenecek.

## 1. ECOCROP ne veriyor? (site 2026-11-12’de okundu)

Kaynak: <https://ecocrop.apps.fao.org/ecocrop/srv/en/cropSearchForm>
(2568 bitki). Ürün sayfası: `.../dataSheet?id=<no>`. Sayfalarda **lisans,
telif ya da kullanım koşulu yazmıyor**.

Her ürün için: uygun sıcaklık aralığı (TOPMN–TOPMX), dayanılabilir aralık
(TMIN–TMAX), yağış aralıkları, iki don öldürme sıcaklığı (dinlenme / erken
büyüme), sezon uzunluğu (en kısa–en uzun gün), gün uzunluğu tepkisi.

Yöntem kaynağı: ECOCROP modeli, R paketi `dismo` (Hijmans), dosya
`R/ecocrop.R` (GPL-3; **kod kullanılmaz**, yalnız yöntem tarif edilir):
aylık ortalama sıcaklık yamuk fonksiyonuyla (TMIN, TOPMN, TOPMX, TMAX) 0–1
puan alır, sezon puanı sezon içindeki ayların **en düşüğü**dür; sezon süresi
(en kısa + en uzun)/2; don kuralı: aylık ortalama en düşük − 5 °C ≤ öldürme
sıcaklığı ise 0.

## 2. Hangi ürünler kazanılır?

**A. Hemen değerlendirilebilir olacak 9 ürün** (FAO-56 sezon tablosu ve bitki
katsayısı zaten var, ECOCROP değeri var):

| Ürün | ECOCROP id | Uygun / dayanılabilir sıcaklık (°C) | Sezon (gün) |
|---|---|---|---|
| Yulaf | 481 | 16–20 / 5–30 | 110–270 |
| Bakla | 2146 | 18–28 / 5–32 | 100–150 |
| Kuru bezelye | 1721 | 10–24 / 4–30 | 60–140 |
| Börülce | 2153 | 25–35 / 15–40 | 30–240 |
| Aspir | 2514 | 20–32 / 5–45 | 120–245 |
| Susam | 1937 | 20–30 / 10–40 | 40–180 |
| Keten | 7336 | 16–24 / 5–30 | 80–180 |
| Tatlı patates | 1265 | 18–28 / 10–38 | 80–170 |
| Şeker pancarı | 514 | 15–25 / 4–35 | 160–240 |

**B. Benzer ürün varsayımıyla kazanılabilecek 2 ürün** (FAO-56 Tablo 11 satırı
yok; K3): nohut (2479; 15–29 / 7–35) → evre oranları "Lentil" satırından;
çavdar (1929; 15–20 / 3–31) → "Barley/Oats/Wheat" satırı ve arpa Kc’si.

**C. Bu yolla kazanılamayanlar:** fiğ ve facelya (ECOCROP’ta yok), sudan otu
(ECOCROP sayfası boş), yonca (çok yıllık, ayrı konu), kolza, hardal,
karabuğday, çim, İskenderiye üçgülü (FAO-56 sezon tablosu yok ve yakın bir
benzer satır önermiyorum).

**D. Yeni ürünler (ilk grup, 15)** — FAO-56 Tablo 11 + 12 + 22 satırı ve
ECOCROP değeri olanlar: domates (1379), kuru soğan (364), lahana (*B. oleracea*
var. *capitata*, id bulunacak), havuç (871), hıyar (817), karpuz (708), kavun
(815), biber (618), patlıcan (1965), marul (1313, var. *capitata*), ıspanak
(1997), bal kabağı (819), turp (1839), taze fasulye (1668), maş fasulyesi
(2150; FAO-56 "Green gram" satırı). Çok yıllıklar (bağ, meyve bahçesi, şeker
kamışı) bu grupta yok.

**Sayılar:** bugün 35 üründen 15’i → A ile **24/35** → A+B ile **26/35** →
yeni ürünlerle **41/50**.

## 3. Modelde nasıl kullanılır? (öneri)

ECOCROP verisi olan ve literatür değeri olmayan ürünler için ayrı, basit bir yol:

| Adım | Tanım | Tür |
|---|---|---|
| Sezon uzunluğu | FAO-56 Tablo 11 (bugünkü kural, ortanca satır) | veri |
| Sıcaklık puanı | 30 günlük yürüyen ortalama sıcaklık → ECOCROP yamuğu (TMIN, TOPMN, TOPMX, TMAX); sezon puanı = K1’e göre | yöntem (dismo) |
| Su puanı | bugünkü FAO-56 Kc × ET0 yöntemi (ECOCROP yağış aralığı kullanılmaz, çift sayım olmasın) | fizik |
| Don | K2’ye göre | — |
| Güven | her zaman "düşük", gerekçe "FAO ECOCROP — lisans belirtilmemiş, genel aralıklar" | kural |

Literatür değeri olan ürünler (buğday, mısır, arpa…) **değişmez**; ECOCROP
onlar için yalnız çapraz kontrol olarak belgede gösterilir.

## 4. Ön sonuç (geçici betik, demo önbelleği; yaklaşık: günlük yamuk, sezon ortalaması)

| Nokta | Öne çıkanlar (en iyi pencere, puan) | Dikkat |
|---|---|---|
| Konya, yağmurla | hepsi düşük (0,08–0,23): su yetmiyor | — |
| Konya, tam sulama | bakla 06-16 (1,00), susam, tatlı patates, keten, aspir ~0,93–0,99 | **yaz ortası ekimler**: ECOCROP aralıkları geniş, Konya yazı "uygun" görünüyor |
| Punjab, yağmurla | börülce 06-16 (0,74), susam 06-16 (0,60), aspir (0,56) — muson ürünleri ✔ | bakla yine muson (0,25, düşük puanla) |
| Punjab, tam sulama | yulaf 11-01 (0,87), bakla 10-01 (0,91), keten 11-01 (0,92) — kış ✔ | bezelye GGCMI takvimi Temmuz diyor (0,14) — takvim şüpheli |
| Nakuru, yağmurla | yulaf, bakla, bezelye, keten, şeker pancarı ~0,73–0,79 (uzun yağmurlar) | — |

ECOCROP’un üst sınırı sayesinde Punjab’da sulu bakla artık kışa gidiyor (önceki
sorun kısmen çözülüyor). K1-a (aylık en düşük) seçilirse puanlar bu tablodan
**düşük** çıkar.

## 5. Kararlar (onayınız gerekiyor)

**K1 — Sezon sıcaklık puanı.**
- **K1-a (önerim):** ECOCROP yöntemine sadık: 30 günlük ortalamalar, sezonun
  **en kötü** ayı (dismo). Daha katı; yöntemle birebir.
- K1-b: Günlük puanların sezon ortalaması (diğer ürünlerle aynı mantık, daha yumuşak).

**K2 — Don öldürme sıcaklığı.**
- **K2-a (önerim):** Bugünkü gibi yalnız "don riski" olarak raporlanır, puana girmez.
- K2-b: dismo kuralı (aylık en düşük − 5 °C ≤ öldürme sıcaklığı → 0).

**K3 — Sezon tablosu olmayan nohut ve çavdar.**
- **K3-a (önerim):** Benzer ürün varsayımıyla eklensin (nohut ← mercimek
  evreleri; çavdar ← arpa/yulaf/buğday evreleri ve arpa Kc’si), "varsayım"
  diye etiketlenir.
- K3-b: Eklenmesin.

**K4 — Literatür değeri eksik olanlarda ECOCROP ısı sınırı kullanılsın mı?**
(sorgum, darı, mercimek, ayçiçeği, arpa için t_heat yok)
- **K4-a (önerim):** Hayır. ECOCROP sınırları ortalama sıcaklık için, bizim
  ısı eşiği günlük en yüksek sıcaklık için; karıştırmak yanlış olur.
- K4-b: Evet, "yaklaşık" etiketiyle.

**K5 — Yeni ürünler.**
- **K5-a (önerim):** Önce 9 + 2 ürün (A+B) yapılır ve onaylanır; yeni 15 ürün
  ikinci adım (FAO-56 Tablo 12 ve 22 için yeniden çalıştırılabilir çıkarma
  betiği gerekiyor; bitki adları ve Türkçe karşılıkları eklenir).
- K5-b: Hepsi tek seferde.

## 6. Onaydan sonra (K1-a, K2-a, K3-a, K4-a, K5-a varsayımıyla)

1. `scripts/probe/probe_ecocrop.py`: ürün listesi için dataSheet sayfalarını
   okur, değerleri yazdırır (toplu veri depoya **konmaz**).
2. `data/crop_phenology.yaml`: kaynak `ecocrop` (URL, okuma tarihi, "lisans
   belirtilmemiş"), her ürüne `ecocrop: {id, url, temp: [TMIN, TOPMN, TOPMX,
   TMAX], cycle: [min, max], kill: {...}}`.
3. `crops.py` / `engine.py`: ECOCROP yolu (yukarıdaki tablo); `evaluable()`
   ECOCROP bloğunu da kabul eder; güven "düşük" + gerekçe.
4. Testler: yamuk sınırları, 30 günlük ortalama, sezonun en kötü ayı, ECOCROP
   ürünü değerlendirilebilir, literatür ürünleri değişmedi (mevcut 160 test),
   ürün sayısı 26.
5. Belgeler: CLAUDE.md kuralı, DATA_SOURCES §5 (ECOCROP: kullanım kararı,
   lisans durumu, okunan sayfalar), CREDITS, METHOD (yöntem + etki), kılavuz
   (sayı ve "genel aralık" uyarısı), arayüzde kaynak adı (`learn.ts`).
6. Demo noktalarında rotasyon etkisi ölçülür ve raporlanır.

## 7. Riskler

- ECOCROP aralıkları **genel** (çeşit ve bölge farkı yok), bu yüzden bazı
  sonuçlar fazla iyimser olabilir (Konya’da yaz ortası bakla). Güven hep "düşük".
- FAO lisans konusunda olumsuz yanıt verirse ECOCROP değerleri kaldırılır;
  bu yüzden hepsi tek bir kaynak anahtarına (`ecocrop`) bağlanır.
