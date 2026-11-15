# Plan: nadas ve örtü bitkileri (onaylandı 2026-11-12: K1-A, K2 evet, K3-b)

Durum: **N1–N4 uygulandı** (bkz. docs/METHOD.md "Soil water between crops"). Kaynakların ayrıntısı:
`docs/DATA_SOURCES.md` bölüm 3b (SoilGrids su tutma) ve bölüm 7 (nadas ve
örtü bitkisi). Prob betiği: `scripts/probe/probe_soilgrids_water.py`.

## 1. Bugün ne eksik?

- Rotasyon motoru nadas yılını sadece "üretim yok" sayıyor. Nadasta toprakta
  biriken su bir sonraki ürüne geçmiyor (kartta `fallow_not_modelled`).
- Su puanı 10 günlük bloklarla hesaplanıyor ve **toprakta hiç su
  depolanmıyor**: bir blokta fazla yağan yağmur kaybolur. (METHOD.md "Known
  limitations": soil water storage between 10-day blocks.)
- Örtü bitkileri (çavdar, fiğ, hardal, facelya) yalnızca "boş dönemde düşünün"
  önerisi; Kc ve sıcaklık değerleri yok.

## 2. Nadas: ne fizik, ne kural?

**Fizik (FAO-56, kaynaklı):**

1. Hasattan sonraki ekime kadar olan **her ara dönemde** (nadas yılı da sadece
   uzun bir ara dönemdir) günlük toprak su dengesi:
   - Üst katman (Ze = 0,10 m): çıplak toprak buharlaşması, FAO-56 bölüm 7
     denklem 71–79 (Ke, Kr, TEW, REW, De).
   - Kök bölgesi: FAO-56 bölüm 8 denklem 85–88 (Dr, derin sızma).
   - FAO-56 bölüm 11 ekim dışı çıplak toprak için tam olarak bunu söylüyor:
     Kcb = 0, Kc min = 0, üst katman + kök bölgesi günlük dengesi.
   - Kc max = 1,20 (denklem 72, bitki boyu h = 0; FAO-56 Örnek 31 de 1,20 kullanır).
2. Toprak suyu tutma kapasitesi **SoilGrids**'ten (ISRIC, CC BY 4.0):
   - TAW = 1000 (θFC − θWP) × kök derinliği (denklem 82). Kök derinliği:
     sonraki ürünün FAO-56 Tablo 22 değeri (zaten `crops.yaml`'da).
   - TEW = 1000 (θFC − 0,5 θWP) × 0,10 m (denklem 73), üst 15 cm'den.
3. Ekimde depolanan su S (mm) sonraki ürünün su puanına girer (bkz. karar K1).

**Etiketli varsayımlar (arayüzde ve METHOD.md'de "varsayım" diye yazılacak):**

| Varsayım | Neden | Etkisi |
|---|---|---|
| θFC = 33 kPa, θWP = 1500 kPa'daki su | SoilGrids katmanları bu emişlerde; FAO-56 kPa vermiyor | 10 kPa ile Konya'da depolama 119 → 168 mm (hassasiyet testi) |
| REW = 9 mm (8–11 aralığı) | Üç demo nokta da "killi tın"; FAO-56 Tablo 19'da bu sınıf yok, komşu sınıflar 8–12 mm | Konya'da ≤ 1 mm fark |
| Hasatta kök bölgesi boş (Dr = TAW) | Ölçüm yok; temkinli seçim. Janssen 1972 de ekim–hasat arası nem farkını "depolanan su" saydı | 15 aylık nadasta etkisi küçük (kış profili dolduruyor); test edilecek |
| Yüzey akış yok (RO = 0) | Janssen 1972 düz tarlalarda akışın çok az olduğunu yazıyor | Eğimli tarlada depolamayı abartır → NASADEM eğimi yüksekse uyarı |
| Nadas yabancı otsuz, anız/malç örtüsü hesaba katılmıyor | Örtü oranı bilinmiyor (FAO-56: her %10 örtü TEW'i %5 azaltır) | Yabancı ot depolamayı azaltır, anız artırır — kartta soru olarak |
| Donmuş toprak / kar ayrıca ele alınmıyor | FAO-56 bölüm 11: o koşullarda ET0 sınırlı geçerli | Kışın ET0 zaten düşük; sınırlama olarak yazılır |
| Kökler sezon başından itibaren tüm depoya ulaşır | Kök büyümesi modellenmiyor | Depolamanın faydasını biraz abartabilir |

**Makullük kontrolü (model girdisi değil):** Janssen (1972), Konya Havzası
buğday–nadas: nadas verimliliği (depolanan / nadas yağışı) **%14–33**.

**Konya deneme hesabı** (POWER 2001–2025, 23 yıl, buğday kök derinliği 1,5 m):

| Durum | Ara dönem yağışı | Ekimde depolanan su | Verimlilik |
|---|---|---|---|
| Buğday → buğday (3,5 ay yaz arası) | 39 mm | 0 mm | %0 |
| Buğday → nadas → buğday (15,5 ay) | 617 mm | **119 mm** | **%19** (yılların çoğu %16–23) |

Sonuç Janssen aralığında. **Uyumsuzluk:** model her kış profili doldurup kök
bölgesinin altına ~120 mm sızdırıyor, Janssen ise derin sızma görmemiş. En
olası neden: POWER yağışı burada fazla (IMERG'den %24 fazla; Janssen'in
istasyonları yılda 260–350 mm). Uygulamada IMERG seçeneğiyle de çalıştırılıp
iki sonuç yan yana gösterilecek.

Su puanına etkisi (deneme): buğdayın su çarpanı nadassız 0,45 → nadastan sonra
~0,74. Bu, sezon puanını kabaca 0,38'den ~0,6'ya çıkarır (tahmini; motorla
hesaplanmadı, uygulama aşamasında ölçülecek).

Not: modelin Konya'da seçtiği buğday ekim penceresi 1 Eylül – ~19 Mayıs; yerel
uygulama Ekim ekimi / Temmuz hasadı (Janssen). Bu ayrı, bilinen bir sınırlama
(vernalizasyon yok).

## 3. Örtü bitkileri

| Bitki | Bulunan kaynak | Karar önerisi |
|---|---|---|
| Çavdar | Kc orta 1,00 / son 0,35, Kcb 0,95 / 0,30 (Pereira ve ark. 2021, Tablo 13 s. 28) — ama makale bu değerlerin "atıfsız malzemeye dayandığını" yazıyor (s. 26) ve tane çavdarı için. Kök 0,6–1,2 m, boy 0,9 m (Tablo 15 s. 30). Taban sıcaklık −4,5 °C (Pessotto ve ark. 2023 özeti; yaprak çıkışına göre; tablolar bot kontrolü yüzünden okunamadı) | **Düşük kanıt** etiketiyle modellenebilir (karar K3) |
| Fiğ | Kc kaynağı yok (FAO-56'da ve Pereira 2021'de yok) | **Modellenmez**, veri boşluğu |
| Hardal (beyaz hardal) | Pereira 2021'de sadece Hint hardalı (başka tür) | **Modellenmez** |
| Facelya | Hiçbir şey bulunamadı | **Modellenmez** |

Örtü bitkisi için olgunlaşma süresi (t_sum) gerekmez: ara dönemde yetişip
sürülür. Gereken: suyu ne kadar kullandığı (Kcb eğrisi) ve ne zaman
büyüyebildiği (taban sıcaklık). Aynı ara dönem su dengesi kullanılır; tek
fark Kcb = 0 yerine örtü bitkisinin Kcb'si.

**Alt puanlar: çift sayım olmadan.** Örtü bitkisi hasat edilmez, bu yüzden:

| Alt puan | Örtü bitkisinin etkisi |
|---|---|
| Su | Kendi tüketimi su puanına **eklenmez**; yalnızca sonraki ürünün ekimdeki depolanan suyunu azaltır (fizik). Kartta ayrıca: "örtü bitkisi X mm su kullandı" |
| Erozyon | Kurulduktan sonraki aylar örtülü sayılır; ekildiği ay çıplak sayılır (varsayım) |
| Toprak sağlığı (vekil) | Canlı kök ayları payına girer; kök derinliği ortalamasına girmez (ana ürünlerin ortalaması seyrelmesin) |
| Azot | Çavdar baklagil değil → etkisi yok. İleride fiğ modellenirse yalnız "tahıldan önce baklagil" terimine girer, "baklagil yılı" payına girmez |
| Üretim, kötü yıl, gelir, yem, çeşitlilik | Etkisi yok |
| Kural | Örtü bitkisi aile sırasına girer: çavdar (buğdaygil) buğdaydan hemen önce gelirse "aynı aile arka arkaya" kuralı bozulur |

Literatür yönü (makullük): kurak bölgelerde nadasta örtü bitkisi buğday
ekiminde toprak suyunu ortalama %16,3 azaltıyor (Adil ve ark. 2022,
meta-analiz, CC BY). Model de su açısından aynı yönü göstermeli.

## 4. Senin kararın gereken noktalar

- **K1 — Sezon içi su puanı.**
  - (A, önerilen, şimdi) 10 günlük blok yöntemi aynı kalır; ekimdeki depolanan
    su S açıkları kapatan bir "havuz" olur. Nadas/ara dönemde su birikmezse
    bugünkü bütün puanlar **aynen kalır**.
  - (B, sonra) Her ürün için günlük FAO-56 kök bölgesi dengesi (denklem 84–86).
    Daha doğru ama **bütün su puanları değişir** (Konya buğday 0,45 → 0,64,
    nadassız bile). Ayrı bir aşama olarak önerilir.
- **K2 — Ara dönem dengesi her geçişte mi?** Önerim evet: nadas özel durum
  olmasın, her hasat → ekim arası aynı fizikle hesaplansın (buğday→buğday
  yaz arası zaten ~0 mm veriyor).
- **K3 — Çavdar örtü bitkisi.** (a) Düşük kanıt etiketiyle modelle; sezon
  aşamaları için kaynak olmadığından kışlık buğdayın FAO-56 Tablo 11 aşama
  oranları **vekil** olarak kullanılır (etiketli). (b) Şimdilik modelleme,
  sadece altyapıyı (Kcb'li ara dönem) kur. Önerim: (b), sonra Pessotto 2023
  PDF'i okunabilirse (a).
- **K4 — Pessotto 2023 PDF'i.** Sitesi otomatik erişimi engelliyor. İstersen
  tarayıcında https://doi.org/10.1002/agg2.20393 adresini açıp PDF'i
  İndirilenler klasörüne kaydet ve bana dosya adını yaz; fiğ ve
  çavdar tablolarını oradan okurum. (Lisans CC BY 4.0, repoya eklenmez.)

## 5. Uygulama aşamaları (onaydan sonra)

1. **N1 SoilGrids su verisi backend'e:** `app/sources/soilgrids.py`
   (mevcut WCS yöntemi, yeni bağımlılık yok), önbellek, 3 demo nokta için
   `demo_cache`. CREDITS.md'ye Turek ve ark. 2023 su tutma katmanları.
2. **N2 FAO-56 ara dönem modülü:** `app/water/fao56_soil.py` (TAW, TEW, Ke/Kr,
   günlük De ve Dr dengesi). Testler aşağıda.
3. **N3 Motor bağlantısı:** uygunluk motoru her pencere ve yıl için 10 günlük
   ETc/yağış dizilerini saklar; rotasyon puanlanırken her geçiş için S
   hesaplanır (önbellekli), sonraki ürünün su ve sezon puanı yeniden toplanır.
4. **N4 Kart ve arayüz:** `fallow_not_modelled` yerine nadas sonucu; METHOD.md.
5. **N5 (K3'e göre) örtü bitkisi.**

Her aşama sonunda durup gösteririm (CLAUDE.md).

## 6. Testler

- **FAO-56 Örnek 31** (çıplak tın toprak, 10 gün, TEW 20, REW 9, ET0 4,5):
  gün gün De, Kr, Ke, E değerleri tablodaki gibi çıkmalı (ör. 1. gün E 4,73 mm,
  3. gün Kr 0,96, 10. gün sonu De 19,88 mm).
- Denklem 72 (h = 0 → 1,20), 73, 82 sayısal kontroller; SoilGrids birim çevirimi.
- Kütle dengesi: yağış = buharlaşma + derin sızma + depo değişimi (her gün).
- Sınırlar: 0 ≤ De ≤ TEW, 0 ≤ Dr ≤ TAW.
- Yağmursuz ara dönemde S = 0 → bugünkü puanlar birebir aynı (K1-A).
- Konya regresyonu: nadas verimliliği %10–35 aralığında; POWER ve IMERG ile.
- Hassasiyet: REW 8/11, 33/10 kPa, kök 1,5/1,8 m sonuçları raporlanır.

## 7. Arayüzde ne görünür?

- Nadas yılı olan rotasyon kartında: "Nadas yılında toprakta yaklaşık
  **120 mm** su birikir (yağışın %19'u). Bu su sonraki buğdaya kalır.
  *Model hesabı (FAO-56 + SoilGrids), ölçüm değil.* Konya'da ölçülen:
  %14–33 (Janssen 1972)."
- Kötü yıl / iyi yıl aralığı (yıllara göre p20–p80).
- Varsayım rozetleri: "yabancı ot yok sayıldı", "yüzey akışı yok sayıldı",
  "toprak verisi 250 m harita, tarlanın kendisi değil".
- Yerel uzmana soru: "Nadasta anız bırakıyor musunuz, ne zaman sürüyorsunuz?",
  "Nadasta yabancı ot kontrolü nasıl?"
- Örtü bitkisi: modellenmeyenler için bugünkü gibi "yerel olarak seçin" +
  neden modellenmediği ("su tüketimi için kaynak yok").

## 8. Veri boşluğu olarak kalanlar

- Fiğ, hardal, facelya, karabuğday: Kc ve sıcaklık kaynağı yok.
- Örtü bitkilerinin azot katkısı ve organik madde etkisi.
- Nadasta yabancı ot, anız örtüsü, toprak işleme zamanı (sadece soru).
- Kar ve donmuş toprak; yüzey akışı (eğimli tarlalar).
- Tarla ölçeğinde toprak (SoilGrids 250 m); gerçek hasat anındaki toprak nemi.
- POWER yağışının Konya'da fazla olması (aşama 3 bulgusu) bu sonucu da etkiler.
