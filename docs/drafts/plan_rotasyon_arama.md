# Plan: Rotasyon aramasını iyileştirme (kalan iyileştirmeler, madde 1)

Durum: **uygulandı 2026-11-14** (kullanıcı ara onay beklemeden ilerlemeyi istedi;
kararlar aşağıda, varsayımlar işaretli). Sonuç: METHOD.md "Rotation engine" → Search.

## 1. Sorun

`recommend()` yalnızca **ürün puanına** göre sıralanmış en iyi 30 yıl planını
(`PLAN_POOL`) birleştiriyordu. 50 ürünle bu havuzu neredeyse 1,0 puanlı sebze
pencereleri dolduruyor; iyi çift ürün yılları havuza giremiyordu. Nakuru yağışa
dayalı en iyi toplam 0,726 → 0,681'e düşmüştü; havuzu 60'a çıkarmak 0,717 buluyor
ama istek başına ~150 s sürüyordu.

Ölçüm (profil, Nakuru): istek süresinin ~yarısı 50 ürünün uygunluk hesabı, kalanı
arama: aday döngüler için toprak suyu geçişlerinin hesaplanması (havuzdaki tüm plan
çiftleri) ve tam puanlama.

## 2. Seçenekler

| | Yöntem | Artı | Eksi |
|---|---|---|---|
| A | Havuzu büyütmek | basit | süre küpü ile artar (60 → ~150 s) |
| B | Havuzu ürün/aileye göre çeşitlendirmek | ucuz | yine sezgisel bir sıralama; çift ürün yılları kaçabilir |
| C | Dal-sınır (branch and bound) | kesin | oran şeklindeki alt puanlar için sıkı üst sınır zor |
| **D** | **İki aşama: taşınan toprak suyu olmadan vektörel ön-puan (tam puanın kendisi), sonra en iyi adayları tam puanlama** | ön-puan tam puanla aynı formül; çok geniş arama ucuz | toprak suyu çok büyük katkı yaparsa bir döngü kaçabilir |

**Karar: D** (en savunulabilir: sezgisel sıralama yerine gerçek rotasyon puanı kullanılıyor
ve sonuç daha geniş bir aramayla ölçülerek doğrulanıyor).

## 3. Ayrıntılar (varsayım = **V**)

- Taşınan toprak suyu yoksa her alt puan yıl planı toplamlarının oranıdır (+ "baklagil
  sonrası tahıl" için bir çift terimi + aile birleşimi). Böylece tüm döngüler numpy ile
  birlikte puanlanır. Birim test: ön-puan = `score(..., carry=None)` (±0,002 yuvarlama).
- **V1:** Yıl planları kendi ön-puanlarına göre sıralanır, en iyi **150** tanesi
  birleştirilir (`MAX_PLANS`). Gösterge noktalarında 60 bile aynı sonucu verdi; 150 pay bırakır.
- **V2:** Ön-puanı en iyi **300** döngü (`N_CANDIDATES`; aynı ürün kümesinden en çok 3)
  tam puanlanır (taşınan toprak suyu dahil). Toprak suyu yalnız su açığını azaltır, bu yüzden
  ön-puan tam puanın altında kalır (ölçülen fark 0 … +0,113, ortanca +0,011).
- Toprak suyu geçişleri artık yalnız bu 300 adayın kullandığı geçişler için hesaplanır.
- Kurallar (aile, tekrar, nadas) değişmedi; plan uyumluluk matrisi `rule_violations` ile
  birim testte karşılaştırıldı; döngü listesi küçük örnekte kaba kuvvet aramayla birebir aynı.

## 4. Doğrulama

`scripts/bench_rotations.py` (çevrimdışı demo önbelleği, varsayılan öncelikler, 3 koşunun en hızlısı):

| Nokta | Su | En iyi toplam önce → sonra | Arama, s | İstek, s |
|---|---|---|---|---|
| Konya | yağışa dayalı | 0,521 → 0,521 | 0,12 → 0,07 | 3,1 → 3,0 |
| Konya | tam sulama | 0,643 → **0,697** | 5,63 → 0,58 | 8,6 → 3,5 |
| Punjab | yağışa dayalı | 0,639 → 0,639 | 1,09 → 0,33 | 4,1 → 3,3 |
| Punjab | tam sulama | 0,719 → **0,724** | 4,36 → 0,57 | 7,4 → 3,6 |
| Nakuru | yağışa dayalı | 0,681 → **0,727** | 3,23 → 0,62 | 6,3 → 3,7 |
| Nakuru | tam sulama | 0,739 → **0,772** | 2,88 → 0,71 | 5,9 → 3,6 |

Sağlamlık: 3 nokta × 2 sulama × 4 öncelik profili (varsayılan; su 5; azot 5 + yem 5;
toprak 5 + erozyon 5 + su 0) = 24 durumda gösterilen ilk 3 kart, 10 kat geniş aramayla
(tüm yıl planları, 3000 tam puanlı aday) **24/24 aynı**.

## 5. Açık kalan

- İsteğin kalan ~3 s'si 50 ürünün uygunluk hesabı (aramadan bağımsız). Aynı nokta için
  öncelik değiştirildiğinde bu hesap tekrar yapılıyor; istenirse bellek içi önbellek eklenebilir.
