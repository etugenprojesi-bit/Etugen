# Etügen — Kullanım Kılavuzu

Bu kılavuz çiftçiler içindir. Etügen, tarlanızın bulunduğu yerin son
25 yıllık hava kaydına (NASA verileri) bakarak şu sorulara yardım eder:

- Bu yerde hangi ürünler daha iyi yetişebilir?
- Ne zaman ekmek uygun olur?
- Hangi aylarda don, aşırı sıcak ya da kuraklık riski var?
- Ürünleri yıllara nasıl sıralayabilirim (ekim sırası, münavebe)?

> **Önemli:** Bu uygulama yardımcıdır. Kararı siz verirsiniz. Uygulama
> çiftçinin bilgisinin ve yerel ziraat uzmanının yerine geçmez. “Yerel
> doğrulama gerekli” yazan her sonucu bir ziraat mühendisine ya da il/ilçe
> tarım müdürlüğüne sorun.

---

## 1. Uygulamayı açın

Telefonunuzun tarayıcısında uygulamanın adresini açın. İlk açılışta iki seçenek çıkar:

- **🧑‍🌾 Kolay mod:** Size soru sormadan doğrudan bir plan verir. Tarlanızı seçip
  "sulayabiliyor musunuz?" sorusunu yanıtlarsınız; **🗓️ Planım** sekmesinde her yıl ne
  ekeceğiniz, ekim ve hasat tarihi, yağmurun ne kadar su eksik bıraktığı (mm; 1 mm = dekar
  başına 1 ton su) ve tarlanın boş kaldığı aylar yazar. "Başka seçenek göster" ile diğer
  iki planı görebilirsiniz. Boş aylarda anızı otlatmak veya örtü bitkisi ekmek bir
  **öneri seçeneğidir**, hesaplanmadı; sulama sayısı ve toprak işleme tarihi de
  hesaplanmadığı için yazılmaz.
- **🔬 Uzman mod:** Aşağıdaki dört sekmeli görünüm; öncelikleri ve kısıtları siz seçersiniz.

Kolay modda ayrıca:
- **📐 Tarlanın köşeleri (isteğe bağlı):** Tarla sekmesinde "Köşeleri işaretle"ye basıp
  haritada köşelere sırayla dokunun. Alan (dekar) hesaplanır; plan su ihtiyacını tarlanızın
  tamamı için ton olarak da yazar. Köşeler telefonunuzdan çıkmaz.
- **🚿 Sulama aralığı:** Her ürün için en çok su istediği dönemde, yağmur yağmazsa kaç günde
  bir ve her seferinde kaç mm sulanacağı (FAO-56 yöntemi; toprağın tutabildiği suya göre).
- **🧭 Sıra yönü:** Araziniz eğimliyse sıraları eğime dik ekmeniz önerilir ve çizimde gösterilir
  (yağmur toprağı daha az taşır). Düz arazide yön fark etmez; size kolay gelen yönde ekin.

Modu üstteki düğmeyle istediğiniz zaman değiştirebilirsiniz. Üstteki **EN** düğmesi uygulamayı İngilizceye çevirir, **TR** geri Türkçeye alır. Araziniz düzse erozyon
önceliği kullanılmaz (yağmurla toprak taşınması eğimle olur).

Uzman modda ekranın altında dört düğme vardır:

| Düğme | Ne işe yarar |
|---|---|
| 📍 **Tarla** | Tarlanızı haritada seçersiniz |
| 🌾 **Özet** | Kısa cevap: hangi ürün, ne zaman, hangi aylar riskli |
| 🔄 **Ekim sırası** | Hangi yıl hangi ürünü ekeceğinizi karşılaştırırsınız |
| 🔬 **Ayrıntılar** | Uzmanlar için teknik bilgiler |

Üstteki **“❓ Nasıl kullanılır?”** düğmesi kısa yardımı açar.

## 2. Tarlanızı seçin (📍 Tarla)

Dört yolu var, hangisi kolayınıza gelirse:

1. **Haritadan seçin.** Harita açılışta **uydu görüntüsü** olarak gelir;
   tarlaları, yolları ve köy adlarını görürsünüz. Haritayı parmağınızla
   kaydırın, iki parmakla büyütün. Ortadaki **artı (+) işaretini** tarlanızın
   üstüne getirin ve sarı **“✔ Bu noktayı seç”** düğmesine basın. Haritada
   bir yere dokunursanız o yer ortaya gelir.
2. **Yer adı yazın.** Üstteki kutuya köy ya da ilçe adını yazıp **“Ara”**ya
   basın (ör. “Çumra, Konya”). Çıkan listeden doğru yeri seçin; harita oraya
   gider. Sonra artı işaretini tarlanıza getirip seçin.
   Koordinat biliyorsanız kutuya doğrudan yazabilirsiniz: `37.60, 32.75`.
   Bir harita bağlantısı da yapıştırabilirsiniz (ör. Google Haritalar ya da
   OpenStreetMap adresi); uygulama içindeki konumu okur. Kısa paylaşım
   bağlantıları (`maps.app.goo.gl/...`) konum içermez: önce tarayıcıda açın,
   adres çubuğundaki uzun adresi yapıştırın.
3. **Konumumu kullan.** Tarladaysanız bu düğmeye basın. Telefon konum izni
   ister. Harita bulunduğunuz yere gider; doğruysa “Bu noktayı seç”e basın.

4. **Tapudaki ada/parsel numarasıyla.** “📜 Tapudaki ada/parsel numaranızla
   bulun” kutusunu açın ve **“TKGM Parsel Sorgu’yu aç”**a basın. Tapu ve
   Kadastro’nun kendi sitesi yeni sekmede açılır. Orada il, ilçe, mahalle/köy,
   ada ve parsel numaranızı girin; parseliniz haritada görünür. Sonra bu
   uygulamaya dönün: mahalle/köy adını arayın (ya da oradan aldığınız konum
   bağlantısını yapıştırın), uydu haritasında aynı parseli bulup artı işaretini
   üstüne getirin.
   Etügen TKGM’ye bağlanmaz ve parsel bilgilerinizi görmez. TKGM’nin
   kullanım koşulları, servislerine izinsiz erişimi yasaklar; bu yüzden ada/parsel
   numarası doğrudan bu uygulamaya yazılamaz.

**Örnek tarlalar** (Konya, Pencap, Nakuru) denemek içindir; NASA sunucularına
ulaşılamasa da kayıtlı gerçek veriyle çalışır.

Notlar:

- Uydu görüntüsü **2016 yılına** aittir (Sentinel-2). Tarlanızın bugünkü hâli
  farklı olabilir; yalnız yeri bulmak için kullanın. İsterseniz sol üstteki
  **“Harita”** düğmesiyle sokak haritasına geçebilirsiniz.
- Hesap tam tarlanız için değil, çevresindeki **yaklaşık 50 km’lik bir alanın**
  hava verisi için yapılır. Yakındaki iki tarla aynı sonucu alabilir.

### Sulama sorusu

“**Tarlanızı sulayabiliyor musunuz?**” sorusuna cevap verin:

| Seçim | Anlamı |
|---|---|
| 🌧️ Hayır | Sadece yağmur suyu hesaba katılır |
| 💧 Biraz | Varsayım: yağmurun yetmediği suyun yarısını sulayabildiğiniz kabul edilir |
| 🚿 Evet | Su sorunu yok sayılır |

Bu seçimi sonra “Özet” ekranında da değiştirebilirsiniz; sonuçlar yeniden
hesaplanır.

## 3. Özeti okuyun (🌾 Özet)

En üstte sarı uyarı kutusu ve verinin nereden geldiği yazar. **“Önbellek
verisi”** yazıyorsa sonuç, daha önce NASA’dan alınmış ve kaydedilmiş gerçek
veriden gelir (ör. internet yoksa).

### “Bu tarlada en iyi yetişebilecekler”

En yüksek puanlı **3 ürün** gösterilir. Her kartta:

- **Puan (100 üzerinden):** Ürünün bu yerin son 25 yıllık havasına ne kadar
  uyduğu. Sıcaklık, su, yetişme süresi ve güneş ışığından hesaplanır.
  **Bu bir verim tahmini değildir**; ürünleri birbiriyle karşılaştırmak içindir.
  Düşük puan, “bu ürün burada hiç olmaz” demek değildir.
- **Çubuk:** Açık yeşil kısım normal bir yıldaki puan, koyu yeşil kısım
  **kötü yıldaki** puandır.
- **Kötü yılda:** Her 5 yılın en kötüsünde beklenen puan. Normal puan iyi ama
  kötü yıl puanı çok düşükse, o ürün risklidir (bazı yıllar elde bir şey
  kalmayabilir).
- **Ekim / Hasat:** En iyi ekim tarihi ve ortalama hasat zamanı.
- **Ay şeridi:** Koyu yeşil kutular uygun ekim ayları, açık yeşil kutular
  ürünün tarlada kaldığı aylardır.
- **🫘 Azot bağlar:** Baklagiller (mercimek, fasulye, soya gibi) havadaki azotu
  toprağa bağlar; ardından ekilen tahıl daha az gübreyle yetişebilir.
- **“Yerel doğrulama gerekli: uzmana danışın”:** Sonucun güveni düşük.
  **“❓ Ziraat uzmanına sorun”** kısmına basınca uzmana sorulacak hazır
  sorular çıkar (ör. “Bu ürünün yerel çeşitleri dona dayanıyor mu?”).

Neden güven hiç “yüksek” değil? Çünkü hava verisi yaklaşık 50 km’lik bir
alanın ortalamasıdır; tarlanızın kendisi ölçülmez.

### “Dikkat edilecekler” (risk renkleri)

Son 25 yılın aylık ortalamalarına göre üç risk gösterilir. Renkli kutular o
riskin olduğu aylardır:

| Satır | Renkli ay ne demek? |
|---|---|
| ❄️ **Don** (mavi) | O ay her 2 yıldan en az 1’inde gece sıcaklığı 0 °C’nin altına iniyor |
| ☀️ **Aşırı sıcak** (kırmızı) | O ay ortalama en az 1 gün en yüksek sıcaklık 35 °C’yi geçiyor |
| 💧 **Yağmur yetmiyor** (turuncu) | O ay yağmur, havanın topraktan ve bitkiden çektiği sudan az; bitki topraktaki suyu kullanır ya da sulama gerekir |

Bu eşikler (“2 yılda 1”, “ayda 1 gün”) sadeleştirilmiş gösterim içindir. Tam
sayılar “Ayrıntılar” bölümündedir.

## 4. Ekim sırasını planlayın (🔄 Ekim sırası)

Aynı tarlaya her yıl aynı ürünü ekmek yerine ürünleri sırayla ekmek
(münavebe) hastalık ve zararlıları azaltır, toprağı korur.

1. **Öncelikler:** Sizin için neyin önemli olduğunu 0 (önemsiz) ile 5 (çok
   önemli) arasında seçin: su tasarrufu, toprak yapısı, erozyon, azot/gübre,
   ek gelir, hayvan yemi.
2. **Kısıtlar:** Makineniz yoksa (ör. kök/yumru hasat makinesi), istemediğiniz
   ürünler, pazarı olan ürünler.
   Uygulama **fiyat bilmez**: pazarı olan ürünleri siz işaretlemezseniz gelir
   puanı “bilinmiyor” kalır.
3. **Mevcut ekim sıranız** (biliyorsanız): Yıl yıl girin; uygulama onu da aynı
   kurallarla puanlar.
4. **“Rotasyonları karşılaştır”**a basın. Kartları yana kaydırarak
   karşılaştırın. Her kartta toplam puan, nedenleri, olası faydalar, riskler,
   bilgi eksiklikleri ve uzmana sorulacaklar yazar.

Kurallar: aynı bitki ailesinden iki ürün art arda gelmez, aynı ürün art arda
iki yıl ekilmez, baklagilden sonra tahıl ekmek artı puan alır, şiddetli
yağışlı aylarda toprağın örtülü olması erozyonu azaltır.

## 5. Ayrıntılar (🔬 uzman görünümü)

Bu bölüm ziraat uzmanları ve meraklılar içindir. Her terimin yanındaki **“?”**
düğmesine basınca ne demek olduğu sade Türkçeyle açılır. Sayfanın en altında
**“📖 Bu ne demek? Terimler”** listesi de vardır.

- **Yağış kaynağı ve senaryo:** Üç yağış verisi arasında seçim: NASA POWER
  (varsayılan), NASA GPM IMERG ve CHIRPS (uydu + yer istasyonları). POWER’ın
  CHIRPS’ten %30’dan fazla yağış gösterdiği yerlerde (ör. Konya ovası) sarı bir
  uyarı çıkar; orada yağmurla tarım sonuçları iyimser olabilir. Ayrıca ve “hava 2 derece daha sıcak olsaydı?” gibi denemeler.
  Senaryo bir **duyarlılık testidir, gelecek tahmini değildir.** Senaryo açıksa
  “Özet”te sarı bir etiket görünür.
- **Veri kaynağı ve konum:** Hangi veri, hangi yıllar, yuvarlanmış konum ve
  rakım.
- **Bölgenin iklimi:** Yıllık ortalamalar, 25 yıllık eğilimler, aylık grafik
  ve takvim.
- **Tüm ürünler:** Bütün ürünlerin puanları, alt puanları, kanıtları ve
  neden “uygun bulunmadığı” ya da “verisi eksik” olduğu.
- **Aylara göre risk tablosu:** Her yılın her ayı o ayın 25 yıllık
  ortalamasıyla karşılaştırılır. **Kırmızı:** o ay normalden riskli (ör. daha
  çok don, daha az yağmur). **Mavi:** normalden iyi. Renk ne kadar koyuysa fark
  o kadar büyük. Bir kutuya basınca değerini görürsünüz.
- **Uydu verileri:** Bitki örtüsü (yeşillik), uydudan ölçülen toprak nemi,
  iki yağış kaynağının karşılaştırması ve eğim. Burada işaretlenen “alışılmadık
  yıllar” kesin bulgu değil, sorulacak sorulardır.

## 6. Aracın sınırları

Uygulamanın bilmediği ya da hesaplamadığı şeyler:

- **Tarlanın kendisi ölçülmez.** Hava verisi yaklaşık 50 km’lik bir alanın
  ortalamasıdır; özellikle yağmur tarlanızda farklı olabilir. Konya’da iki
  NASA yağış verisi birbirinden yaklaşık %24 farklıdır; hangisinin doğru olduğu
  istasyon ölçümü olmadan bilinemez.
- **Her ürün için tek bir referans çeşit** kullanılır. Yerel çeşitleriniz daha
  kısa ya da uzun sürede olgunlaşabilir. Uydu ile karşılaştırınca (NASA MODIS,
  25 yıl): Punjab’da çeltiğin sezonu uyduyla birkaç gün içinde tutuyor; buğdayı
  ise model yaklaşık 3 hafta erken bitiriyor.
- **Hesaba katılmayanlar:** toprak türü ve topraktaki su birikimi, don
  yüzünden bitkinin ölmesi (don günleri gösterilir ve soruya çevrilir),
  kışlık buğdayın soğuklama ihtiyacı ve gün uzunluğu, ekim zamanındaki toprak
  nemi, su göllenmesi, hastalık ve zararlılar, gübre.
- **Fiyat ve pazar bilgisi yoktur.** Gelir yalnız sizin işaretlediğiniz
  ürünlere göre hesaplanır.
- **50 üründen 43’ü** değerlendirilebiliyor: 15’inin sıcaklık sınırları
  bilimsel kaynaklardan, 28’inin (yulaf, bakla, bezelye, börülce, aspir, susam,
  keten, tatlı patates, şeker pancarı, nohut, çavdar, domates, soğan, lahana,
  havuç, hıyar, karpuz, kavun, biber, patlıcan, marul, ıspanak, bal kabağı, turp,
  taze fasulye, maş fasulyesi, Sudan otu ve İskenderiye üçgülü) FAO ECOCROP’un genel aralıklarından gelir.
  Sudan otu ve İskenderiye üçgülü (berseem) için yalnız ekimden ilk biçime kadar
  hesap yapılır; sonraki biçimler hesaplanmadığı için bu iki yem bitkisi ürün
  listesinde görünür ama rotasyon önerilerinde kullanılmaz. ECOCROP ürünlerinde çeşit ve bölge farkı yoktur, güven
  her zaman “düşük” görünür. Literatür değeri olan 15 ürünün 10’unda aşırı sıcak eşiği de vardır (arpa, sorgum,
  darı, mercimek ve ayçiçeğinde yoktur, bu yüzden sıcak mevsim ekimleri
  cezalandırılmaz ve güven “düşük” görünür). Kaynağı olmayan ürünler için uygulama tahmin yürütmez, “veri
  eksik” yazar.
- **Toprak sağlığı puanı** dolaylı bir göstergedir (kök derinliği, toprakta
  canlı kökün kaldığı süre).
- **Eğim,** tarlanızın değil, çevredeki yaklaşık 5 km’lik alanın ortancasıdır.
- **Senaryo** bir duyarlılık testidir, iklim tahmini değildir.
- **Nadas yılında ve iki ürün arasında toprakta biriken su** bir model
  hesabıdır (FAO-56 yöntemi ve 250 m’lik toprak haritası), ölçüm değildir.
  Hasatta toprağın kuru olduğu, yüzey akışı, yabancı ot ve anız olmadığı
  varsayılır. Konya’da sonuç, bölgede ölçülmüş değerlerle (%14–33) uyumludur.
- **Ekim zamanı:** en iyi ekim zamanı, bölgenizde yaygın ekim gününün 45 gün
  öncesi ile sonrası arasından seçilir (GGCMI ürün takvimi, çok yıllık
  ortalama). “Farklı ekim zamanlarını da dene” kutusu bu sınırı kaldırır.
  Takvimde sulu tarım için kayıt yoksa kuru tarım takvimi kullanılır. Model
  ürünü bölgedeki ekim zamanında hiç yetiştiremiyorsa (örneğin Punjab’da
  Haziran’da bezelye) bütün yıl denenir; ürün kartı bunu “güven düşük”
  nedeni olarak yazar, yerel bilgiyle kontrol edin.
- **Pencap (Hindistan) buğdayı:** Bu bölgede buğdayın sezon uzunluğu, Pencap
  Tarım Üniversitesi’nin bir sezonluk deneyinde gözlenen çeşitlere göre
  ayarlanır; başka yerlerde tek bir referans çeşit kullanılır.
- **Örtü bitkileri** henüz hesaplanmaz.

## 7. Ne zaman uzmana danışmalısınız?

Şu durumlarda kararı vermeden önce bir ziraat mühendisine, il/ilçe tarım
müdürlüğüne ya da deneyimli komşu çiftçilere danışın:

- Kartta **“Yerel doğrulama gerekli”** yazıyorsa.
- **Kötü yıl puanı** normal puandan çok düşükse.
- Uygulamanın önerdiği ürün yörenizde **hiç yetiştirilmiyorsa** ya da sizin
  bildiğiniz ekim zamanı uygulamanınkinden çok farklıysa.
- **Don, aşırı sıcak** ya da **kuraklık** ayları ürünün tarlada olduğu aylara
  denk geliyorsa.
- Yeni bir ürüne geçmeyi, sulama yatırımını ya da büyük bir masrafı
  düşünüyorsanız.
- Toprağınızda tuzluluk, su göllenmesi, hastalık gibi uygulamanın bilmediği
  bir sorun varsa.

Uygulamanın “❓ Ziraat uzmanına sorun” listesindeki soruları yanınızda
götürebilirsiniz.

## 8. İnternet ve gizlilik

- İnternet yoksa son baktığınız sonuçlar **7 gün** telefonunuzda kalır.
  Örnek tarlalar (Konya, Pencap, Nakuru) NASA sunucularına ulaşılamasa da
  kayıtlı gerçek veriyle çalışır.
- Hesap açmanız gerekmez; çerez ve takip yoktur.
- Seçtiğiniz konum yaklaşık **5 km’ye yuvarlanır**. Sunucu yalnız yuvarlanmış
  konumu ve herkese açık veri sonuçlarını saklar.
- Sulama, öncelikler ve ekim sıranız yalnız o hesap için kullanılır,
  saklanmaz.
- **Yer adı ararsanız** yalnız yazdığınız ad OpenStreetMap’in arama hizmetine
  gönderilir; konumunuz gönderilmez. Koordinat yazarsanız hiçbir yere
  gönderilmez.
- Ayrıntılar için uygulamanın altındaki **“🔒 Gizlilik”** bölümüne ve
  [`docs/PRIVACY.md`](PRIVACY.md) dosyasına bakın.

## 9. Verilerin kaynağı

- Hava: NASA POWER (günlük, 25 yıl), buharlaşma ihtiyacı FAO-56 yöntemiyle.
- Uydu: NASA MODIS (bitki örtüsü), SMAP (toprak nemi), GPM IMERG (yağış),
  NASADEM (eğim); CHIRPS (yağış, uydu + istasyon, kamu malı).
- Harita: OpenStreetMap katkıcıları (OpenFreeMap); uydu görüntüsü Sentinel-2
  cloudless 2016, EOX IT Services GmbH (CC BY 4.0).
- Yöntemin tamamı: [`docs/METHOD.md`](METHOD.md). Tüm kaynaklar ve lisanslar:
  [`docs/CREDITS.md`](CREDITS.md).
