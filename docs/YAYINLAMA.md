# Uygulamayı yayına alma (hakemlerin tıklayacağı adres)

Sonuç: `https://<kullanıcı-adı>-etugen.hf.space` gibi herkese açık bir adres.
Ücretsiz, kredi kartı gerekmez. Arayüz ve sunucu aynı adreste çalışır.

Sıra önemli: **A → B → C → D**. Earth Engine (C) isteğe bağlıdır; atlanırsa uygulama yine
çalışır, yalnız üç örnek tarla dışında uydu katmanları (eğim, NDVI, toprak nemi) “veri yok” der.

---

## A. Kodu GitHub’da herkese açın

1. <https://github.com> → giriş yapın (hesap yoksa açın) → sağ üstte **+ › New repository**.
2. Ad: `etugen` · **Public** seçin · başka kutu işaretlemeyin · **Create repository**.
3. Bilgisayarda, proje klasöründe (`C:\Users\ycane\Desktop\NasaSpace`) bir terminal açın ve
   GitHub’ın sayfada gösterdiği adresle (sizin kullanıcı adınızla) şunları çalıştırın:

```bash
git remote add origin https://github.com/KULLANICI-ADINIZ/etugen.git
```

```bash
git push -u origin main
```

   İlk seferde tarayıcıda GitHub girişi istenir; onaylayın.
   Yalnız `main` dalını gönderin (yukarıdaki komut). `git push --all` kullanmayın: yerel yedek
   dallarda (`backup/...`, `claude/...`) eski e-posta adresi hâlâ duruyor.
4. Kontrol: GitHub sayfasında `.env` dosyası **görünmemeli** (gizli bilgiler orada). Görünürse
   hemen durun ve haber verin.

## B. Hugging Face Space açın

1. <https://huggingface.co/join> → hesap açın.
2. <https://huggingface.co/new-space> →
   - Space name: `etugen`
   - License: `apache-2.0`
   - **SDK: Docker** → **Blank**
   - Hardware: **CPU basic (free)** · Visibility: **Public** → **Create Space**.
3. Space sayfasında **Files › Add file › Upload files** ile projedeki şu iki dosyayı yükleyin
   (var olan `README.md`’nin yerine geçsin):
   - `deploy/huggingface/Dockerfile`
   - `deploy/huggingface/README.md`
4. Yükledikten sonra **Dockerfile**’ı Space’te açın (✏️ Edit) ve tek satırı değiştirin:
   `ARG REPO=https://github.com/YOUR-USER/YOUR-REPO.git` →
   `ARG REPO=https://github.com/KULLANICI-ADINIZ/etugen.git` → **Commit**.
5. Space kendiliğinden derlenir (**Building**, 5–10 dakika). **Running** olunca **App**
   sekmesinde uygulama açılır. Adres: sağ üstte **⋮ › Embed this Space › Direct URL**.

## C. (İsteğe bağlı) Earth Engine için servis hesabı

Bunun için yeni açacağınız ayrı bir Google hesabını kullanın.

1. O hesapla <https://console.cloud.google.com> → üstte proje seçici → **New project** → bir ad
   verin → oluşturun. **Proje kimliğini (Project ID)** not edin.
2. <https://code.earthengine.google.com/register> → **Use with a Cloud project** →
   **Unpaid usage › Academia & research** (ya da uygun kar amacı gütmeyen seçenek) → az önce
   açtığınız projeyi seçin → kaydı tamamlayın.
3. Cloud Console’da **APIs & Services › Library** → “Earth Engine API” → **Enable**.
4. **IAM & Admin › Service Accounts › Create service account** → ad: `toprak-demo` → **Create**
   → rol olarak **Earth Engine Resource Viewer** ve **Service Usage Consumer** ekleyin → **Done**.
5. Oluşan hesaba tıklayın → **Keys › Add key › Create new key › JSON** → bir `.json` dosyası iner.
   Bu dosya bir şifre gibidir: kimseyle paylaşmayın, GitHub’a koymayın, bana da göndermeyin.

## D. Gizli bilgileri Space’e girin

Space → **Settings › Variables and secrets › New secret**:

| Ad | Değer |
|---|---|
| `EE_PROJECT` | C1’deki Project ID |
| `EE_SERVICE_ACCOUNT_JSON` | C5’te inen `.json` dosyasının **tüm içeriği** (Not Defteri’yle açıp kopyalayın) |

Kaydedince Space yeniden başlar. C’yi atladıysanız bu adımı da atlayın.

## Deneme

1. Adresi telefonda ve bilgisayarda gizli pencerede açın.
2. “Kolay mod” → örnek tarla **Konya** → plan gelmeli (ilk istek 10–30 sn sürebilir).
3. İngilizce: adresin sonuna `?lang=en` ekleyin. Hakemlere bu bağlantıyı verin.
4. Ücretsiz Space bir süre kullanılmazsa uyur; ilk açılış bir dakika kadar sürebilir.

## Kod değişince

GitHub’a yeni commit gönderdikten sonra Space’te **Settings › Factory rebuild** deyin.

## Gizlilik notu

Uygulama sunucuda yuvarlanmış konum dışında bir şey saklamaz (docs/PRIVACY.md). Barındırma
hizmetinin (Hugging Face) kendi sunucu kayıtları onların gizlilik politikasına tabidir.
