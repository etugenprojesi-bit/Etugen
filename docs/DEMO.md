# Demo — 2-minute script

The app is in Turkish (it is made for farmers in Türkiye); the words in
quotes are the Turkish labels on screen. Everything below works **offline**
for the three demo points: the backend falls back to `demo_cache/` (real API
responses saved on 2026-11-11) and the app labels it "Önbellek verisi".

Start: backend (`backend/.venv/Scripts/python -m uvicorn app.main:app --app-dir backend --port 8000`)
and frontend (`cd frontend && npm run dev`), open `http://localhost:5173`,
phone width (or a phone on the same Wi-Fi).

| Time | Do | Say |
|---|---|---|
| 0:00 | Show the satellite field picker ("Tarla" tab: crosshair + "Bu noktayı seç", place search) | "Etügen helps a farmer explore which crops and rotations fit their field, using 25 years of NASA data. It supports, it does not replace, local experts." |
| 0:10 | Tap example field **Konya** (opens the "Özet" tab with the yellow disclaimer) | "One tap: NASA POWER daily climate for 25 years, evapotranspiration from FAO-56 physics, and every crop tested for every sowing date in every year." |
| 0:25 | "Özet": top 3 crops, sowing/harvest, frost/heat/dry months; then "Ayrıntılar" → "Tüm ürünler", open **winter wheat**, tap a "?" | "Each score shows its evidence, a bad-year value, a confidence level and questions for a local expert. The '?' buttons explain every term in plain Turkish." |
| 0:40 | "Ayrıntılar" → "Aylara göre risk tablosu" → "Risk katmanlarını yükle" → year slider to **2025** | "Risk layers: frost, heat, heavy rain, water balance, and NASA SMAP soil moisture and MODIS NDVI from Earth Engine. Red = worse than normal for that month. 2025 was Konya's driest soil-moisture year in the SMAP record." |
| 0:55 | Layer compare: water balance vs NDVI | "Any two layers side by side on one scale, by month and over all years." |
| 1:05 | "Ayrıntılar" → "Yağış kaynağı ve senaryo": choose **GPM IMERG** | "Two NASA rainfall sources disagree here: POWER is about 24 % wetter than GPM IMERG. The farmer can see results with either." |
| 1:15 | Slider **+2 °C**, "Uygula" | "A sensitivity test, not a forecast: every crop and rotation is recomputed. Each crop shows the change against today's climate." |
| 1:30 | "Ekim sırası" tab → "Rotasyonları karşılaştır" | "Rotations are scored with transparent rules (water, soil, erosion from NASADEM slope, nitrogen from legumes) and compared with the best single-crop monoculture (or the farmer's own rotation)." |
| 1:45 | "Ayrıntılar" → "Uydu verileri" → patterns | "Classical statistics and machine learning side by side on the same data: k-means found Konya's growing season shifted after 2015, which a simple z-score misses." |
| 1:55 | Footer "Gizlilik" | "No accounts, no tracking; the server keeps only 5 km-rounded points. Open source, Apache-2.0." |

Offline rehearsal: start the `backend-offline` configuration in `.claude/launch.json` (dead proxy, empty cache: only `demo_cache/`). Risk layers and rotations then take ~45 s because the Earth Engine attempt times out first.

Backup if the network is down during the demo: everything above works from
the demo cache. Other points need the network (NASA POWER, Earth Engine)
and show an explicit error if a source is unreachable.
