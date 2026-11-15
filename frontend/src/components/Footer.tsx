import { LANG } from '../lang'
import { Glossary } from './Learn'

// Short version of docs/PRIVACY.md (Turkish / English), plus the glossary and data credits.
export function Footer() {
  return (
    <footer className="footer">
      <Glossary />
      {LANG === 'en' ? <PrivacyEN /> : <PrivacyTR />}
    </footer>
  )
}

function PrivacyTR() {
  return (
    <>
      <details className="card">
        <summary className="form-summary">🔒 Gizlilik</summary>
        <ul className="plain small">
          <li>Hesap, çerez ve takip yok.</li>
          <li>
            Seçtiğiniz konum yaklaşık 5 km’ye yuvarlanır. Sunucu yalnız yuvarlanmış konumu ve herkese açık veri sonuçlarını
            saklar; sizi tanıtan hiçbir bilgi saklanmaz.
          </li>
          <li>Sulama, öncelikler, kısıtlar ve mevcut rotasyonunuz yalnız o hesap için kullanılır, saklanmaz.</li>
          <li>Sunucu kayıtlarında konum ile IP adresi birlikte yazılmaz.</li>
          <li>Son sonuçlar internetsiz kullanım için 7 gün telefonunuzda tutulur.</li>
          <li>
            Yer adı ararsanız yalnız yazdığınız ad OpenStreetMap’in arama hizmetine (Nominatim) gider. Harita görüntüleri
            OpenFreeMap ve EOX sunucularından yüklenir. TKGM düğmesi yalnız TKGM’nin sitesini açar; bu uygulama oraya bir şey göndermez.
          </li>
          <li>
            Yapay zekâ açıklaması yalnız kutuyu işaretlerseniz kullanılır; konum gönderilmez.
          </li>
        </ul>
      </details>
      <p className="muted small center">
        Veriler: NASA POWER, MODIS, SMAP, GPM IMERG, NASADEM (NASA). Harita © OpenMapTiles, © OpenStreetMap katkıcıları;
        uydu görüntüsü Sentinel-2 cloudless 2016, EOX IT Services GmbH (değiştirilmiş Copernicus Sentinel verisi 2016), CC
        BY 4.0; yer arama Nominatim (OpenStreetMap). Açık kaynak, Apache-2.0.
      </p>
    </>
  )
}

function PrivacyEN() {
  return (
    <>
      <details className="card">
        <summary className="form-summary">🔒 Privacy</summary>
        <ul className="plain small">
          <li>No account, no cookies, no tracking.</li>
          <li>
            The place you choose is rounded to about 5 km. The server keeps only the rounded place and public-data results;
            nothing that identifies you is kept.
          </li>
          <li>Irrigation, priorities, limits and your current rotation are used only for that calculation and are not stored.</li>
          <li>Server logs never record a location together with an IP address.</li>
          <li>Your last results stay on your phone for 7 days for offline use. The field corners never leave your phone.</li>
          <li>
            If you search a place name, only the name you type goes to OpenStreetMap’s search service (Nominatim). Map images
            load from OpenFreeMap and EOX servers. The TKGM button only opens TKGM’s site; this app sends nothing there.
          </li>
          <li>The AI explanation is used only if you tick its box; no location is sent.</li>
        </ul>
      </details>
      <p className="muted small center">
        Data: NASA POWER, MODIS, SMAP, GPM IMERG, NASADEM (NASA). Map © OpenMapTiles, © OpenStreetMap contributors;
        satellite image Sentinel-2 cloudless 2016, EOX IT Services GmbH (contains modified Copernicus Sentinel data 2016), CC
        BY 4.0; place search Nominatim (OpenStreetMap). Open source, Apache-2.0.
      </p>
    </>
  )
}
