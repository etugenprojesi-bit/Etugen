# Data sources

Every entry below was verified by a probe script in `scripts/probe/` on
**2026-11-03**. IDs, versions and coverage dates come from the probe output
(API responses or the official Earth Engine STAC catalog), not from memory.

Status legend: ✅ works · ⏳ waiting for credentials · ⚠️ works with caveats · ❌ not usable

Demo points (all checked as cropland with MODIS MCD12Q1 LC_Type1 2024, ≥22/25
pixels class 12 in a 1 km box):

| key | lat | lon | place |
|---|---|---|---|
| konya | 37.60 | 32.75 | Çumra, Konya plain, Türkiye |
| punjab | 30.80 | 75.60 | Ludhiana district, Punjab, India |
| nakuru | -0.25 | 36.15 | Nakuru County, Kenya |

The first coordinates I tried were city centres; SoilGrids masks urban pixels,
which is why the REST API first returned `null` everywhere.

---

## 1. NASA POWER — daily point API ✅

| | |
|---|---|
| Endpoint | `https://power.larc.nasa.gov/api/temporal/daily/point` (`community=AG`) |
| API version | `v2.10.2` (from response header) |
| Upstream sources (header) | MERRA-2, SYN1deg (CERES), POWER |
| Parameters | `T2M`, `T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `RH2M`, `WS2M`, `ALLSKY_SFC_SW_DWN`, `GWETTOP`, `GWETROOT`; since 2026-11-12 also `T2MDEW` (§9) |
| Spatial resolution | ~0.5° × 0.625° (MERRA-2 grid; solar ~1°) — coarse, point = nearest cell |
| Temporal | daily, local solar time (`time_standard: LST`) |
| Tested range | 2001-01-01 … 2025-12-31: 9131 days, **0 fill values** at all 3 points |
| Fill value | `-999.0` |
| Latency | 1.6–3.5 s per point for 25 years × 9 parameters (~1.3 MB JSON) |
| Extra | response geometry includes cell elevation (m), usable for the FAO-56 psychrometric constant |
| Auth | none |
| Terms | No restrictions on use; the project asks for acknowledgement — see [POWER referencing](https://power.larc.nasa.gov/docs/referencing/) |
| Probe | `scripts/probe/probe_power.py` |

Units (from `/api/system/manager/parameters`): T2M* °C, PRECTOTCORR mm/day
(MERRA-2 bias-corrected), RH2M %, WS2M m/s, ALLSKY_SFC_SW_DWN MJ/m²/day,
GWET* 0–1.

> **GWETTOP / GWETROOT are model output (MERRA-2 land surface model), not SMAP
> observations.** The UI must label them "model-based soil wetness".

## 2. ORNL DAAC MODIS/VIIRS Land Product Subsets REST API ⚠️ (fallback)

| | |
|---|---|
| Endpoint | `https://modis.ornl.gov/rst/api/v1/{product}/{bands|dates|subset}` |
| Service DOI | [10.3334/ORNLDAAC/1557](https://doi.org/10.3334/ORNLDAAC/1557) (Collection 6 web service) |
| Auth | none |
| Limits | max 10 dates per `subset` request (observed) |

| Product | Res. | Cadence | Coverage (Konya point) | Result |
|---|---|---|---|---|
| `MOD13Q1` (NDVI/EVI, C6.1) | 231.66 m cell | 16 days | 612 dates, 2000-02-18 … 2026-09-14 | ✅ 9×9 px for 1 km buffer; **3.3–18.6 s per 10 dates** (varied between runs) |
| `MOD11A2` (LST 8-day) | 926.6 m | 8 days | 1221 dates, 2000-02-18 … 2026-09-22 | ✅ 3×3 px; 3.9 s per 10 dates |
| `MCD12Q1` (land cover) | 500 m | yearly | to 2024 | ✅ used to validate demo points |
| `SPL3SMP_E` (SMAP) | 9 km | daily | — | ❌ "No data available for this location" |
| `GEDI03` | 1 km | one-time | — | ❌ "No data available for this location" |

**Caveat:** a full 25-year NDVI series would be ~60 requests (minutes). Use only
as a fallback for recent seasons; Earth Engine is the primary NDVI path.

## 3. ISRIC SoilGrids v2.0 ✅ (WCS) / ⚠️ (REST)

| | WCS (primary) | REST (backup) |
|---|---|---|
| Endpoint | `https://maps.isric.org/mapserv?map=/map/{prop}.map` (OGC WCS 2.0.1, `COVERAGEID={prop}_{depth}_mean`) | `https://rest.isric.org/soilgrids/v2.0/properties/query` |
| Latency | ~0.5 s per layer; 21 layers in parallel ≈ 2.3 s | **30–60 s per point; one timeout at 60 s** |
| Output | GeoTIFF (int16), reprojected to EPSG:4326, pixel 0.00222° × 0.0025° | JSON |

- Resolution: 250 m. Properties tested: `clay`, `sand`, `silt`, `phh2o`, `soc`,
  `bdod`, `cec` at `0-5cm`, `5-15cm`, `15-30cm`.
- Raw units (mapped units, divide by `d_factor`): clay/sand/silt g/kg (÷10 → %),
  phh2o pH×10, soc dg/kg (÷10 → g/kg), bdod cg/cm³ (÷100 → kg/dm³), cec mmol(c)/kg (÷10 → cmol(c)/kg).
- 0 = nodata (masked: urban, water).
- WCS quirk: windows of ~0.02° came back all-zero; a 0.1° window works, then the
  probe takes the median of valid pixels within 1 km.
- Cross-check WCS vs REST (0–5 cm clay): Punjab 27.2 % vs 27.7 %, Nakuru 36.4 % vs 36.3 %.
- License: **CC BY 4.0** (as stated in the EE catalog entry `ISRIC/SoilGrids250m/v2_0`).
- Probes: `probe_soilgrids_wcs.py`, `probe_soilgrids.py`.
- New dependency for reading GeoTIFFs: `tifffile` (BSD-3-Clause) + `numpy`.

### 3b. SoilGrids water retention (wv0010 / wv0033 / wv1500) ✅ probed 2026-11-11 — used since 2026-11-12 (`app/sources/soilgrids.py`, demo cache for the 3 points)

- Layers: volumetric water content at 10, 33 and 1500 kPa, six depths
  (0–5 … 100–200 cm), `mean`, `Q0.05`, `Q0.5`, `Q0.95` and `uncertainty`
  coverages, same WCS endpoint (`map=/map/wv0033.map`, `COVERAGEID=wv0033_{depth}_mean`).
  Coverage IDs from the live `GetCapabilities` response.
- Source paper: Turek, M.E. et al. (2023), Global mapping of volumetric water
  retention at 100, 330 and 15000 cm suction using the WoSIS database.
  Int. Soil Water Conserv. Res. 11(2):225–239, doi:10.1016/j.iswcr.2022.08.001
  (bibliographic data from the Earth Engine catalog entry; paper not read in full).
- Units (ISRIC SoilGrids FAQ, conversion-factor table): mapped value =
  10⁻³ cm³/cm³ = 0.1 vol% = **1 mm water per m of soil**; ÷1000 → m³/m³.
- Licence: CC BY 4.0 (Earth Engine catalog entry `ISRIC/SoilGrids250m/v2_0`, wv assets).
- **Assumption (labelled):** θFC = water content at 33 kPa, θWP = at 1500 kPa.
  FAO-56 defines field capacity and wilting point physically, not by suction;
  10 kPa is shown as a sensitivity case (it raises TAW by 35–80 %).
- Probe: `scripts/probe/probe_soilgrids_water.py` (24 requests per point, 2–5 s).

Results (median of valid 250 m pixels within 1 km; FAO-56 eq. 82 TAW = 1000 (θFC − θWP) Zr,
eq. 73 TEW = 1000 (θFC − 0.5 θWP) Ze with Ze = 0.10 m):

| Point | θFC / θWP 0–15 cm | TEW mm | TAW 33 kPa, Zr 0.6 / 1.0 / 1.5 / 1.8 m | TAW 10 kPa, same | sand / silt / clay % 0–15 cm |
|---|---|---|---|---|---|
| Konya | 0.299 / 0.192 | 20.3 | 57 / 92 / 138 / 165 | 78 / 125 / 186 / 222 | 20.5 / 47.3 / 32.6 |
| Punjab | 0.267 / 0.143 | 19.5 | 77 / 134 / 211 / 257 | 110 / 183 / 273 / 327 | 38.8 / 33.8 / 27.3 |
| Nakuru | 0.299 / 0.183 | 20.8 | 62 / 104 / 155 / 185 | 117 / 193 / 280 / 333 | 35.1 / 29.2 / 35.9 |

Plausibility: θFC and θWP fall inside the FAO-56 Table 19 ranges for loam /
silty clay loam / clay, and TEW (≈ 20 mm) inside the Table 19 TEW ranges of
the neighbouring classes (16–29 mm). All three points are USDA **clay loam**
by the SoilGrids texture, a class that FAO-56 Table 19 does **not** list, so
REW (readily evaporable water) cannot be read from Table 19 directly (see
section 7).

## 4. Google Earth Engine ✅ (live, verified 2026-11-11)

IDs below were verified against the official STAC catalog
(`probe_gee_catalog.py`,
`https://storage.googleapis.com/earthengine-stac/catalog/catalog.json`) and,
on **2026-11-11**, live with `scripts/probe/probe_gee.py` (Konya point, 2024).

### Live probe results (2026-11-11, Konya 37.60, 32.75)

| Check | Time | Result |
|---|---|---|
| `MODIS/061/MOD13Q1` NDVI 2024, 1 km mean | 0.3 s | 23 composites, mean NDVI 0.382 |
| `NASA/HLS/HLSL30/v002` + `HLSS30` 2024 scenes | 2.5 s | L30: 45, S30: 1775 (S30 counts tiles/granules over the point) |
| `NASA/SMAP/SPL3SMP_E/006` 2024 mean | 16.6 s | soil_moisture_am 0.117 m³/m³, anomaly −0.027 |
| `NASA/GPM_L3/IMERG_MONTHLY_V07` 2024 mean | 1.1 s | 0.0476 mm/h (≈ 418 mm/yr) |
| `NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI` latest | 0.5 s | 238 images; lwe_thickness −23.1 cm ± 7.4 |
| `NASA/NASADEM_HGT/001` slope, 1 km | 1.0 s | 1.74° mean |
| `NASA/ECOSTRESS/L2T_LSTE/V2` 2024 scenes | 0.5 s | 74 |
| `LARSE/GEDI/GEDI04_B_002` MU | 0.4 s | 1.71 Mg/ha |
| `MODIS/061/MOD11A2` LST_Day 2024 mean | 1.1 s | 297.2 K |
| `ISRIC/SoilGrids250m/v2_0` | 0.6 s | 3 images, first `wv0010` (water retention, not texture) |

**Authentication quirk.** `earthengine authenticate` asks for Earth Engine,
Cloud, Drive and Cloud Storage scopes. If the Drive box is left unticked, the
library's token refresh fails with `invalid_scope` and reports "Please
authorize access…". The probe and the backend therefore refresh the stored
token with only `earthengine.readonly` + `cloud-platform.read-only`
(`app/sources/gee.py`); Drive is never used.

### Point time series used by the app (stage 3, `app/sources/gee.py`)

| Layer | Extraction | QA (from STAC band description) |
|---|---|---|
| NDVI | MOD13Q1, mean of 250 m pixels within 1 km, per 16-day composite | `SummaryQA` ≤ 1 (0 good, 1 marginal; 2 snow, 3 cloud rejected) |
| Soil moisture | SPL3SMP_E 005 and 006, `getRegion` at 9 km, one request per year and version (a single request hit "User memory limit exceeded") | `retrieval_qual_flag_am` == 0 ("Pass") |
| Precipitation | IMERG_MONTHLY_V07 at 0.1° | — (`precipitationQualityIndex` not used) |
| Slope | `ee.Terrain.slope(NASADEM elevation)`, mean / p10 / p50 / p90 over the 0.05° analysis cell | — |

Timing (2026-11-11): one point, 2001–2025, all layers — 176 s sequentially;
with layers and SMAP years requested in parallel threads, 25–30 s per point
from the build script and ~13 s through `/api/satellite`. Results are cached
per rounded point.

Demo-point responses are stored in `demo_cache/gee_<lat>_<lon>.json.gz`
(64–69 KiB each, built with `scripts/build_demo_cache.py gee`).

**SMAP versions (observed 2026-11-11, contradicts the catalog text).** The
catalog says 006 starts on 2023-12-04 and that earlier data "will eventually
be reprocessed". Live, **006 already returns data from 2015-03-31**, so the two
versions overlap for 2015-04 … 2023-12. Overlap statistics (both QA-pass):

| Point | Days | mean(006 − 005) m³/m³ | RMSD | r |
|---|---|---|---|---|
| Konya | 1273 | +0.0005 | 0.0042 | 0.996 |
| Punjab | 759 | +0.0065 | 0.0256 | 0.931 |
| Nakuru | 1100 | −0.0188 | 0.0192 | 0.999 |

Merge rule: 006 is primary; days without a passing 006 retrieval are filled
from 005 minus the mean offset (11–36 days per point). See `docs/METHOD.md`.

| Purpose | Dataset ID | Version | Coverage | Resolution | Key bands |
|---|---|---|---|---|---|
| NDVI, phenology | `MODIS/061/MOD13Q1` | 6.1 | 2000-02-18 … 2026-09-30 | 250 m, 16 d | `NDVI`, `SummaryQA`, `DayOfYear` |
| Precipitation (rain check, option) | `UCSB-CHG/CHIRPS/DAILY` | 2.0 final | 1981-01-01 … 2026-09-30, 50°S–50°N | 0.05°, daily | `precipitation` (mm/d) |
| Land surface phenology (validation) | `MODIS/061/MCD12Q2` | 6.1 | 2001 … 2025 (yearly) | 500 m | `MidGreenup_n`, `Peak_n`, `MidGreendown_n`, `EVI_Amplitude_n`, `QA_Overall_n` |
| NDVI (Aqua, offset 8 d) | `MODIS/061/MYD13Q1` | 6.1 | 2002-07-04 … 2026-10-08 | 250 m, 16 d | same |
| Field-scale NDVI | `NASA/HLS/HLSL30/v002` | v002 | 2013-04-11 … 2026-11-01 | 30 m | `B4`,`B5`,`Fmask` |
| Field-scale NDVI | `NASA/HLS/HLSS30/v002` | v002 | 2015-11-28 … 2026-11-01 | 30 m | `B4`,`B8A`,`Fmask` |
| Landsat alternative | `LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2` | C02 | 2013-03-18 / 2021-10-31 … 2026-10/11 | 30 m | — |
| Soil moisture (obs.) | `NASA/SMAP/SPL3SMP_E/005` | 5 | 2015-03-31 … 2023-12-03 | 9 km, daily | `soil_moisture_am`, `soil_moisture_am_anomaly`, `retrieval_qual_flag_am` |
| Soil moisture (obs.) | `NASA/SMAP/SPL3SMP_E/006` | 6 | 2023-12-04 … 2026-10-31 | 9 km, daily | same |
| Soil moisture (L4 model+obs.) | `NASA/SMAP/SPL4SMGP/008` | 8 | 2015-03-31 … 2026-10-31 | 11 km, 3 h | — (007 is deprecated) |
| Precipitation | `NASA/GPM_L3/IMERG_V07` | Release 07 | 1998-01-01 … 2026-11-02 | 0.1° (11 km), 30 min | `precipitation` (mm/h) |
| Precipitation monthly | `NASA/GPM_L3/IMERG_MONTHLY_V07` | Release 07 | 1998-01-01 … 2025-09-01 | 0.1°, monthly | `precipitation` |
| Water storage | `NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI` | RL06.3 | 2002-03-31 … 2024-09-30 | 0.5° (55.66 km) | `lwe_thickness`, `uncertainty` |
| Elevation / slope | `NASA/NASADEM_HGT/001` | 1 | 2000 (SRTM epoch) | 30 m | `elevation` |
| Elevation (alt.) | `USGS/SRTMGL1_003` | 3 | 2000 | 30 m | `elevation` |
| Heat stress LST | `NASA/ECOSTRESS/L2T_LSTE/V2` | V002 | 2018-07-09 … 2026-11-02 | 70 m, irregular | `LST`, `QC`, `cloud` |
| LST fallback | `MODIS/061/MOD11A2` | 6.1 | 2000-02-18 … 2026-10-16 | 1 km, 8 d | `LST_Day_1km`, `QC_Day` |
| Actual ET | `MODIS/061/MOD16A2GF` | 6.1 | 2000-01-01 … 2025-12-27 | 500 m, 8 d | `ET`, `PET` |
| Biomass | `LARSE/GEDI/GEDI04_B_002` | 2 | 2019-04-18 … 2021-08-04 | 1 km gridded | `MU` (AGBD), `SE` |
| Biomass (footprints, monthly raster) | `LARSE/GEDI/GEDI04_A_002_MONTHLY` | 2.1 | 2019-03-25 … 2025-07-01 | 25 m footprints | `agbd`, `l4_quality_flag` |
| Soil (EE fallback) | `ISRIC/SoilGrids250m/v2_0` | — | static | 250 m | `val_0_5cm_mean`, … |

### MODIS MCD12Q2 land surface phenology — probed and used 2026-11-12 (season validation)

Used by `app/validation/seasons.py` (layer `phenology` in `app/sources/gee.py`,
`getRegion` at 500 m, all product years; added to the demo cache with
`scripts/build_demo_cache.py gee:phenology`). `QA_Overall` classes from the
STAC entry: 0 Best, 1 Good, 2 Fair, 3 Poor.

`MODIS/061/MCD12Q2` v6.1, DOI [10.5067/MODIS/MCD12Q2.061](https://doi.org/10.5067/MODIS/MCD12Q2.061),
500 m, yearly, up to two vegetation cycles per year from NBAR-EVI2. Band
definitions from the STAC entry: `MidGreenup_n` / `MidGreendown_n` = first / last
crossing of 50 % of the segment EVI2 amplitude, `Peak_n` = segment maximum,
dates as days since 1970-01-01; `QA_Overall_n`. Probe
`scripts/probe/probe_mcd12q2.py` (`getRegion` at the point pixel, all years):

| Point | Years | Time | Cycles (median) | MidGreenup / Peak / MidGreendown, median day of year |
|---|---|---|---|---|
| Konya | 2001–2025 | 2.0 s | 1 | 168 / 214 / 260 (one summer cycle) |
| Punjab | 2001–2025 | 0.6 s | 2 | cycle 1: 12 / 47 / 89 (wheat season); cycle 2: 202 / 246 / 288 (rice season) |
| Nakuru | 2001–2025 | 0.6 s | 1 | cycle 1: 121 / 160 / 209 (19 years); cycle 2: 300 / 335 / 20 (4 years) |

Cross-check with our own 50 % rule on MOD13Q1 NDVI (1 km mean): Punjab
greendown 94 (wheat) and 290 (rice). Use: validation of model seasons
(`docs/METHOD.md` "Season validation (MODIS)").

Notes from the catalog:
- SMAP E is split across two versions (005 until 2023-12-03, 006 from 2023-12-04) — merge both for a long series. (Live: 006 now starts 2015-03-31; see above.)
- `IMERG_MONTHLY_V07` ends 2025-09 in the catalog; recent months need aggregation of the 30-min product. The app compares POWER and IMERG on complete years only (2001–2024).
- GRACE mascon ends 2024-09-30.
- GEDI covers ~51.6° S … 51.6° N only and is sparse; biomass is context, not a field measurement.
- STAC `license` shows "proprietary" for NASA datasets (catalog placeholder); the
  `gee:terms_of_use` text states NASA data are freely available without
  restriction (citation requested). Earth Engine itself requires a registered
  Cloud project; noncommercial use is free.

### Rainfall cross-check at Konya: CHIRPS and a GHCN-Daily station (probed 2026-11-14; CHIRPS used since 2026-11-14 as rain check and optional rain source)

Plan: `docs/drafts/plan_konya_yagis.md`.

- **CHIRPS v2.0 daily**, Earth Engine `UCSB-CHG/CHIRPS/DAILY`, band `precipitation`
  (mm/d), 0.05°, 50°S–50°N, 1981–. STAC terms: "This dataset is in the public
  domain" (copyright waived by the Climate Hazards Center). Probe
  `scripts/probe/probe_chirps.py` (monthly sums on the server, one request per
  point, 1.7–2.3 s): mean annual 2001–2024 Konya **309 mm**, Punjab 617 mm,
  Nakuru 1141 mm (POWER 560 / 715 / 1260, IMERG 453 / 637 / 1275).
- **NOAA GHCN-Daily** station KONYA `TUM00017244` (37.979, 32.562, 1030 m; 45 km
  from the demo point), file `by_station/TUM00017244.csv.gz` from
  `https://www.ncei.noaa.gov/pub/data/ghcn/daily/`. PRCP 1963–2025 but with gaps:
  only 59 months of 2001–2024 are complete (≥ days − 1 reported, no quality flag).
  Not stored in the repo; reuse terms for non-US stations to be checked before
  any use in the app.
- Same 59 months, totals relative to the station: POWER **1.63**, IMERG 1.39,
  CHIRPS **0.98**; monthly r 0.80 / 0.89 / 0.78. The excess is in Oct–Feb.
  CHIRPS blends station data, so it may include this station (not independent);
  gauges under-catch snow.
- Nearest GHCN-D stations: Punjab JAGRAON `IN018090400` (12 km), LUDHIANA
  `IN018090300` (29 km) — **no PRCP data 2001–2024**; LUDHIANA `IN018091100`
  (33 km) has PRCP 2016–2025 but only ~55–112 days per year and **no complete
  month** (checked 2026-11-14 with `ghcnd-inventory.txt` and the station file),
  so no gauge check is possible at Punjab. Nakuru: ELDORET INTL (124 km).
- In the app: Earth Engine layer `chirps` (`app/sources/gee.py`, monthly sums,
  one request, ~2 s, cached; fetched alone by `load_layer`), added to the demo
  cache with `scripts/build_demo_cache.py gee:chirps`.

## 5. Crop parameters

| Source | Used for | Status |
|---|---|---|
| FAO-56 Table 12 ([x0490e0b](https://www.fao.org/4/X0490E/x0490e0b.htm)) | Kc_ini, Kc_mid, Kc_end, max height | ✅ 30 crops in `data/crops.yaml`; 181 values checked automatically against the extracted table |
| FAO-56 Table 22 ([x0490e0e](https://www.fao.org/4/X0490E/x0490e0e.htm)) | max root depth, depletion fraction p | ✅ same check |
| FAO-56 Tables 12 and 22, extracted to `data/fao56_table12_22.yaml` by `scripts/extract_fao56_table12_22.py` (2026-11-13; 124 + 103 rows) | Kc, height, root depth, p for the 15 vegetables and pulses; cross-check of all existing `fao56` blocks | ✅ all 29 existing rows match the extraction (`tests/test_fao56_tables.py`) |
| FAO-56 Table 11 ([x0490e0b](https://www.fao.org/4/X0490E/x0490e0b.htm)) | stage lengths (days) per region/planting date | ✅ 167 rows in `data/fao56_table11.yaml`, generated by `scripts/extract_fao56_table11.py` (re-runnable) |
| Zhao et al. 2019, SIMPLE crop model, Table 1a ([doi](https://doi.org/10.1016/j.eja.2019.01.009)) | t_base, t_opt, t_heat, t_ext, t_sum for wheat, maize, rice, soybean, dry bean, groundnut, potato, cassava, cotton | ⚠️ in `data/crop_phenology.yaml`; **second-hand transcription** from the GPL-3 NetLogo implementation by Angourakis ([Zenodo 4557347](https://doi.org/10.5281/zenodo.4557347)), checked automatically against that CSV but **not against the paper** (publisher page and HAL blocked automated access) |
| Luo 2011, Climatic Change, Tables 1–2 ([doi](https://doi.org/10.1007/s10584-011-0028-6)) | sorghum t_base/t_opt; wheat and barley lethal minimum | ✅ read from the article PDF |
| Sadras, Rosewarne & Lake 2021, Front. Plant Sci. 12:674327, Table 1 ([doi](https://doi.org/10.3389/fpls.2021.674327)), CC BY 4.0 | lentil t_base 0 (authors' assumption, citing Summerfield et al. 1985) and t_sum 1963–2193 °C·d sowing–maturity (19 varieties) | ✅ read from the publisher PDF |
| Maldaner et al. 2018, Brazilian J. Agric. 93(3):234–249, Tables 1–2 ([doi](https://doi.org/10.37856/bja.v93i3.3173)), open access | sunflower t_base 5.8 °C (estimated) and t_sum 1761 °C·d sowing–maturity, cv. Hélio 358 | ✅ read from the journal PDF |
| Costa et al. 2005, Pesq. Agropec. Bras. 40(12):1171–1177, Tabelas 1–2 ([doi](https://doi.org/10.1590/S0100-204X2005001200003)), CC BY-NC 4.0 — non-commercial licence; the team decided on 2026-11-09 to keep the cited numeric values (non-commercial project, attribution given) | pearl millet t_base 10 °C (authors' assumption, citing Norman et al. 1995) and t_sum 1052–1352 °C·d sowing–maturity (5 genotypes, 2 sowing dates) | ✅ read from the PDF and the SciELO table images |
| Chauhan et al. 2023, Agron. Sustain. Dev. 43:49, section 2 ([doi](https://doi.org/10.1007/s13593-023-00903-x)), CC BY 4.0 | chickpea t_base 0 °C (APSIM development cardinal temperatures 0/30/40 °C) | ✅ read from the publisher PDF; partial (no t_sum, no growth optimum) |
| Boons-Prins et al. 1993, *Crop-specific simulation parameters for yield forecasting across the European Community*, Simulation Reports CABO-TT 32, Appendix C1 and C3 Table C3b ([edepot.wur.nl/308997](https://edepot.wur.nl/308997)), open technical report, no DOI | barley (spring barley, EU15 WOFOST calibration): development table DTSMTB 0→0, 35→35, 45→35; TSUM1 800 + TSUM2 750 °C·d emergence–maturity; sowing–emergence TBASEM 3 °C, TEFFMX 30 °C, TSUMEM 110 °C·d | ✅ read from the report PDF (2026-11-12); added after decision K1-a |
| FAO ECOCROP data sheets ([search form](https://ecocrop.apps.fao.org/ecocrop/srv/en/cropSearchForm)), one `dataSheet?id=` per crop | temperature optimal / absolute range, crop cycle, killing temperature for the 11 crops without literature values (oats, faba bean, dry pea, cowpea, safflower, sesame, flax, sweet potato, sugar beet, chickpea, cereal rye) | ⚠️ **no licence stated; used by user decision 2026-11-12, labelled** (see below); read with `scripts/probe/probe_ecocrop.py` |

Since 2026-11-14, 43 of the 50 crops are evaluable: 15 from literature and
28 from ECOCROP general ranges (11 field crops; 15 vegetables and pulses added
2026-11-13; Sudan grass and berseem clover added 2026-11-14 as cut forage
modelled to the first cut only, not used in recommended rotations). Still
`insufficient_data`: rapeseed, mustard, ryegrass (no season-length source),
buckwheat, vetch and phacelia (no Kc source; vetch and phacelia also not in
ECOCROP); alfalfa is perennial (search log 2026-11-14 below). Lentil, sunflower, millet and barley have
t_base + t_sum but no growth optimum and no heat thresholds (sorghum has
t_opt but no heat thresholds), so their confidence is "low" and hot-season
sowings are not penalised (see the search logs below).
Water limits are no longer needed from literature: water suitability is
computed from FAO-56 Kc × ET0 against rainfall.

### ECOCROP licence check (2026-11-03)

- FAO's [ECOCROP page](https://www.fao.org/land-water/resources/tools/databases/ecocrop/en)
  says the database was **discontinued around 2015** and now lives on the GAEZ
  portal (`gaez.fao.org/pages/ecocrop`). Neither page states a licence or reuse terms.
- The [FAO Database Terms of Use](https://www.fao.org/contact-us/terms/db-terms-of-use)
  (CC BY 4.0 + extra terms) cover "FAO corporate statistical databases"
  (FAOSTAT, AQUASTAT, …); ECOCROP is not listed.
- The only GAEZ v4 licence text found is CC BY-NC-SA 3.0 IGO, on the **documentation**,
  not explicitly on the data.
- [openclim/ecocrop](https://github.com/openclim/ecocrop) redistributes a full
  ECOCROP CSV; its README licence (Open Government Licence) covers the code, and
  it does not state a licence for the FAO data.

**Conclusion: licence unclear → not added to the repo.**

**Update 2026-11-12 (user decision):** the online database
(`ecocrop.apps.fao.org`) still states no licence on any page. The user decided
to use it, labelled, for crops without literature values (plan
`docs/drafts/plan_ecocrop_urun_artirma.md`). Only the few numbers used are
copied by hand into `data/crop_phenology.yaml` (source key `ecocrop`, one data
sheet id per crop); no bulk table is stored. Values read on 2026-11-12:

| Crop | Sheet id | TMIN / TOPMN / TOPMX / TMAX °C | Cycle days | Killing temp. early growth °C |
|---|---|---|---|---|
| Oats (*Avena sativa*) | 481 | 5 / 16 / 20 / 30 | 110–270 | −1 |
| Faba bean (*Vicia faba*) | 2146 | 5 / 18 / 28 / 32 | 100–150 | — |
| Dry pea (*Pisum sativum*) | 1721 | 4 / 10 / 24 / 30 | 60–140 | 0 |
| Cowpea (*Vigna unguiculata*) | 2153 | 15 / 25 / 35 / 40 | 30–240 | −1 |
| Safflower (*Carthamus tinctorius*) | 2514 | 5 / 20 / 32 / 45 | 120–245 | −2 |
| Sesame (*Sesamum indicum*) | 1937 | 10 / 20 / 30 / 40 | 40–180 | — |
| Flax (*Linum usitatissimum*) | 7336 | 5 / 16 / 24 / 30 | 80–180 | −1 |
| Sweet potato (*Ipomoea batatas*) | 1265 | 10 / 18 / 28 / 38 | 80–170 | 5 |
| Sugar beet (*Beta vulgaris*) | 514 | 4 / 15 / 25 / 35 | 160–240 | 0 |
| Chickpea (*Cicer arietinum*) | 2479 | 7 / 15 / 29 / 35 | 90–180 | 0 |
| Cereal rye (*Secale cereale*) | 1929 | 3 / 15 / 20 / 31 | 110–270 | −1 |

Added 2026-11-13 (same probe; vegetables and pulses with FAO-56 rows):

| Crop | Sheet id | TMIN / TOPMN / TOPMX / TMAX °C | Cycle days | Killing temp. early growth °C |
|---|---|---|---|---|
| Tomato (*Lycopersicon esculentum*) | 1379 | 7 / 20 / 27 / 35 | 70–150 | — |
| Onion (*Allium cepa*) | 364 | 4 / 12 / 25 / 30 | 85–175 | — |
| Cabbage (*Brassica oleracea* var. *capitata*) | 554 | 7 / 15 / 24 / 32 | 60–200 | −1 |
| Carrot (*Daucus carota*) | 871 | 3 / 15 / 24 / 30 | 40–150 | 0 |
| Cucumber (*Cucumis sativus*) | 817 | 6 / 18 / 32 / 38 | 40–180 | — |
| Watermelon (*Citrullus lanatus*) | 708 | 15 / 20 / 35 / 40 | 0–0 on the sheet (not stored) | — |
| Melon (*Cucumis melo*) | 815 | 9 / 18 / 30 / 35 | 50–120 | — |
| Sweet pepper (*Capsicum annuum*) | 618 | 8 / 17 / 30 / 35 | 60–180 | — |
| Eggplant (*Solanum melongena*) | 1965 | 9 / 20 / 35 / 40 | 70–120 | — |
| Lettuce (*Lactuca sativa* var. *capitata*) | 1313 | 5 / 12 / 21 / 30 | 35–85 | 0 |
| Spinach (*Spinacia oleracea*) | 1997 | 2 / 13 / 20 / 27 | 40–120 | 0 |
| Pumpkin (*Cucurbita maxima*) | 819 | 9 / 20 / 30 / 38 | 80–140 | — |
| Radish (*Raphanus sativus*) | 1839 | 10 / 12 / 26 / 37 | 50–80 | — |
| Green bean (*Phaseolus vulgaris*) | 1668 | 7 / 16 / 25 / 32 | 50–270 | — |
| Mung bean (*Vigna radiata*) | 2150 | 8 / 21 / 36 / 40 | 50–120 | — |
| Sudan grass (*Sorghum* × *drummondii*) — added 2026-11-14 | 9970 | 12 / 21 / 33 / 38 | 90–120 | −1 |
| Berseem clover (*Trifolium alexandrinum*) — added 2026-11-14 | 10522 | 3 / 16 / 27 / 35 | 90–270 | −2 |

Not found: *Vicia sativa*, *Vicia villosa*, *Phacelia tanacetifolia* and
*Brassica rapa* (no exact match); *Sorghum sudanense* sheet 1988 is empty, but
the sheet of *Sorghum* × *drummondii* (9970, the species in `crops.yaml`) has
values (found 2026-11-14). Read but not used (no season-length or Kc source
to go with them, see the 2026-11-14 log): rapeseed *Brassica napus* 549
(5 / 15 / 25 / 41, 85–340 d), white mustard *Sinapis alba* 9787 (5 / 10 / 25 / 30,
110–180 d), brown mustard *B. juncea* 548 (7 / 15 / 28 / 40, 50–100 d),
buckwheat *Fagopyrum esculentum* 2285 (7 / 17 / 27 / 40, 55–85 d), Italian
ryegrass *Lolium multiflorum* 7389 (2 / 14 / 30 / 38, 90–270 d). Method: ECOCROP model as implemented
in the R package `dismo` (R. J. Hijmans, `R/ecocrop.R`, GPL-3; code not used,
method described in `docs/METHOD.md`).

**Decision (2026-11-03):** temperature / rainfall optimum and absolute limits
and season length come from **peer-reviewed literature**, one citation per
value in `data/crops.yaml`. In parallel the team asks FAO
(copyright@fao.org) about reuse terms for ECOCROP data; draft in
`docs/drafts/fao_ecocrop_licence_request.md`. If FAO confirms an open licence,
ECOCROP can be added later as a cross-check source.

Rules for literature values (stage 1):
- Only sources the team can read in full (open access or the publisher's
  freely accessible version); DOI and the table/page for every value.
- No value is entered from memory; anything not found stays `null`.
- Where sources disagree, the range is stored and confidence is lowered.

### Literature search for crop temperature parameters (2026-11-08)

Searched open-access literature for SIMPLE-type parameters (t_base, t_opt
growth optimum, t_heat/t_ext, t_sum sowing–maturity with its t_base) for the
crops without a `temperature` block. Only values read in an original, freely
accessible paper were added (table above). Not added, and why:

- **Zhao et al. 2019 (SIMPLE) Table 1a** still not verified: the HAL copy is
  behind a bot check (not bypassed); ScienceDirect is paywalled.
- **Barley**: no open paper with one sowing–maturity thermal time; Alzueta et
  al. 2014 (Comput. Electron. Agric. 107:8–19) give photoperiod-dependent
  regressions (Tb 0 to heading, 8.2 °C after heading), not a single t_sum.
- **Rapeseed**: Luz et al. 2012 (Ciência Rural 42:1549) estimate Tb per
  subperiod (−1 to 11 °C), no single base/t_sum. Rapeseed also lacks a
  FAO-56 Table 11 row, so it could not be evaluated anyway.
- **Chickpea**: Jeffrey et al. 2025 (Front. Plant Sci., doi:10.3389/fpls.2024.1496629)
  use base 10 °C capped at 30 °C; their GDD to maturity varies threefold
  between sites, so it is not a usable t_sum.
- **Dry bean, highland cultivars**: no open sowing–maturity thermal time found.
  The SIMPLE common-bean calibration in Agronomy (MDPI) 12:1813 (2022) and the
  Kenyan legume papers on core.ac.uk were blocked (HTTP 403 / bot check).
- **Luo 2011 Table 2** has no further usable values for these crops (barley
  only Tlmin and a pollen-viability threshold).
- **Lentil heat thresholds**: Maphosa et al. 2023 (Plants 12:474) only cite
  general ranges (10–30 °C optimum, >35 °C detrimental) from other papers;
  not added as t_heat.
- Germination/emergence cardinal temperatures (many open papers) were not
  used: they describe seed germination, not crop development or growth.

### Literature search for crop temperature parameters, round 2 (2026-11-12)

Plan and decisions: `docs/drafts/plan_sicaklik_parametreleri.md`, approved
2026-11-12 as K1-a, K2-a, K3-a: **barley added**, faba bean not (no local
calendar and no heat threshold; the model sowed it into the Punjab monsoon).
Loader count before: 14 of 35 crops evaluable; now 15 (10 with heat
thresholds), 20 `insufficient_data`.

**Usable, read in the original:**

- **Boons-Prins, E.R., de Koning, G.H.J., van Diepen, C.A., Penning de Vries,
  F.W.T. (1993).** Crop-specific simulation parameters for yield forecasting
  across the European Community. Simulation Reports CABO-TT 32, CABO-DLO,
  Wageningen. Open PDF <https://edepot.wur.nl/308997> (technical report, no DOI,
  no licence statement; numeric parameters cited). WOFOST calibration for EU15.
  - Spring barley, Appendix C3 Table C3b (p. C III-3): development base 0 °C
    (DTSMTB 0→0, 35→35, 45→35), TSUM1 800 + TSUM2 750 °C·d emergence–maturity;
    sowing–emergence TBASEM 3.0 °C, TSUMEM 110 °C·d. Calibrated on EU crop
    calendars (Table C3a, Appendix C4).
  - Field bean (*Vicia faba*), Appendix G1 (p. G I-1/2) and Appendix G4 caption
    (p. G IV-1, "base temperature of 0 °C"): TBASEM 0, TSUMEM 100, TSUM1 833,
    TSUM2 1351 °C·d; DTSMTB non-linear (0→0, 20→22.5, 25→25, 35→25).
  - No heat-stress thresholds of the SIMPLE type (TMPFTB is a photosynthesis
    temperature factor on daytime temperature, not a Tmax heat factor; not mapped).
- Cross-check: the same numbers are distributed as YAML in
  [ajwdewit/WOFOST_crop_parameters](https://github.com/ajwdewit/WOFOST_crop_parameters)
  (branch `wofost72`, EUPL-1.2, Wageningen Environmental Research). **Discrepancy:**
  `barley.yaml` (Spring_barley_301) has TBASEM 0.0, the report says 3.0 — the
  report is used.

**Found but not recommended:**

- Sugar beet (same report, Appendix E1/E3, Table E3a1): section 3.5 says the
  second phase uses base 0 °C while the data file DTSMTB has base 3 °C (cap
  21 °C); the season ends at a management harvest date, not maturity.
- Cowpea: van Heemst, H.D.J. (1988), Plant data values required for simple crop
  growth simulation models: review and bibliography, Simulation Report CABO-TT 17,
  <https://edepot.wur.nl/218353>, Table 9 (p. 32–33): Tbase1 8 °C, Tsum1
  660 °C·d (Hadley et al. 1983) and Tsum1 740 / Tsum2 630 °C·d (cv. Red Caloona,
  Muchow 1985, base not stated), Tsum2 370 (cv. K 2809). The WOFOST YAML
  (660 + 630) mixes cultivars. Secondary compilation; not used.
- Sweet potato: WOFOST YAML TSUM1 416 / TSUM2 1436 are not in van Heemst
  Table 18 (only days at a given temperature, Agata 1982) → not traceable.
- Rapeseed (Boons-Prins 1993 / WOFOST YAML): temperature sums are counted from
  1 January, not from sowing; no FAO-56 Table 11 row.
- Sorghum and pearl millet SIMPLE heat thresholds: Nzimande, T.N.M. (2021),
  MSc thesis, University of KwaZulu-Natal, Table 3.6 (p. 39–40): Tbase 8,
  Topt 30/32, MaxT 44/48, ExtremeT 50 °C, Tsum 1648/1337 °C·d (local calibration,
  Ukulinga). Not peer-reviewed; maize values there differ from Zhao et al. 2019.

**Searched, nothing usable found:** oats; dry pea (open papers concern fresh
processing-pea harvest, e.g. HortScience 35:611, not dry-seed maturity);
safflower; sesame (bases of 8, 10, 15 °C in different secondary sources);
flax (PMC article behind a reCAPTCHA, not bypassed); Sudan grass; heat
thresholds for lentil and sunflower; Hatfield & Prueger 2015 (Weather Clim.
Extremes 10:4–10, CC BY-NC-ND) has no crop threshold table.

**SIMPLE (Zhao et al. 2019) original:** still not verifiable. Unpaywall and
Semantic Scholar report "closed", no repository copy; HAL is behind a bot
check (not bypassed). Values stay marked as second-hand.

### Punjab wheat season and heat thresholds — source search (2026-11-14)

Plan: `docs/drafts/plan_punjab_bugday_sicak_esik.md`. Nothing added to `data/`.

- **Kaur, H., Kingra, P.K., Singh, L., Kaur, S., Bora, S. (2025).** Phenological and
  yield responses of wheat to sowing dates and varieties in Punjab: an agro-climatic
  index approach. Indian Journal of Agronomy 70(4): 499–502,
  [doi:10.59797/ija.v70.i4.5677](https://doi.org/10.59797/ija.v70.i4.5677); full text
  read from the journal site (no licence statement found; numbers cited only).
  PAU Ludhiana, rabi 2023-24, PBW 826 / PBW 766 / PBW 550. Table 1 (p. 500): days
  sowing → maturity 154 (6 Nov), 146 (24 Nov), 136 (12 Dec); varieties 138–154.
  Accumulated GDD to maturity 1773.7 / 1691.9 / 1652.6 °C·d, but the base
  temperature is **not stated** (methods give GDD = (Tmax + Tmin)/2 − Tbase only),
  so these sums are not usable as t_sum. With POWER at the Punjab demo point, the
  observed seasons hold 2639 / 2564 / 2482 °C·d above 0 °C; our winter wheat
  (2200 °C·d) matures 16 / 13 / 9 days earlier. **Used since 2026-11-14** (user
  decision) as a derived regional t_sum [2482, 2639] for wheat in Indian Punjab,
  source key `kaur2025` (METHOD "Regional cultivar variants").
- Other PAU sowing-date studies found (Journal of Agrometeorology 2024, J. Sci. Ind. Res.
  2024, Indian J. Agron. 2025 vol. 70(4) "sowing regimes"): full texts not retrieved
  (servers did not respond); one snippet states Tbase 5 °C (Slafer & Savin 1991).
- **Heat thresholds (sorghum, millet, lentil, sunflower, barley):** searched again for
  SIMPLE-type growth thresholds (T_heat, T_extreme) in peer-reviewed open papers; only
  the Nzimande (2021) MSc thesis (already rejected, round 2) and model comparisons
  without calibrated values were found. Development / pollen thresholds are not mapped.

### Crops still without data — source search (2026-11-14)

Plan and decisions: `docs/drafts/plan_veri_eksik_urunler.md` (K1–K5).

- **ECOCROP** (`scripts/probe/probe_ecocrop.py`, table above): values found for
  Sudan grass (*Sorghum* × *drummondii*; the sheet of *S. sudanense* is empty),
  berseem, rapeseed, white and brown mustard, buckwheat and Italian ryegrass;
  none for vetch (*V. sativa*, *V. villosa*) or phacelia.
- **Pereira, L.S., Paredes, P., Hunsaker, D.J., López-Urrea, R., Mohammadi Shad, Z.
  (2021).** Standard single and basal crop coefficients for field crops. Updates and
  advances to the FAO56 crop water requirements method. Agricultural Water Management
  243, 106466, [doi:10.1016/j.agwat.2020.106466](https://doi.org/10.1016/j.agwat.2020.106466);
  read in the open repository copy (Universidade de Lisboa). Table 12 (p. 27) gives
  updated Kc mid / end for canola 1.10 / 0.35 and mustard (*Brassica juncea*)
  1.15 / 0.40; Table 15 (p. 30) mustard root depth 0.50–1.10 m, height 1.5–2.0 m,
  p 0.55. **No stage lengths:** the authors state that stage durations were out of
  scope and advise against FAO-56's indicative durations (section 1, p. 4–5); no Kc ini
  is tabulated. Not used: our mustard is the cover crop *Sinapis alba*, not *B. juncea*,
  and no season length exists for either; no buckwheat, vetch, phacelia, ryegrass or
  clover rows (the pseudo-cereals covered are amaranth and quinoa only).
- **FAO-56 Table 11** has no row for rapeseed/canola, mustard, buckwheat, ryegrass,
  berseem, vetch or phacelia. The nearest rows were judged unsuitable for rapeseed
  ("Crucifers" = vegetable brassicas harvested green; the local winter rapeseed
  overwinters, which a fixed-length season cannot represent) and ryegrass (only
  warm-season "Sudan" / "Bermuda" grass hay rows; "Grass Pasture" has no length).
  For berseem the alfalfa first cutting cycle is used as a labelled analogy (K2).

## 6. Base maps and place search (stage 7) ✅

Verified 2026-11-11 with `scripts/probe/probe_basemap.py`.

| | Satellite base map | Place search |
|---|---|---|
| Service | EOX WMTS, layer `s2cloudless_3857` | OpenStreetMap Nominatim `/search` |
| Endpoint | `https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg` (capabilities: `.../WMTSCapabilities.xml`) | `https://nominatim.openstreetmap.org/search?format=jsonv2` |
| What it is | Layer title "Sentinel-2 cloudless layer for 2016 by EOX - 3857": a cloud-free Sentinel-2 mosaic, 10 m pixels | Geocoder over OpenStreetMap data |
| Licence (from the service itself) | Layer abstract: "EOxCloudless … (Contains modified Copernicus Sentinel data 2016) released under … CC BY 4.0". Later years (2017+) carry other licences (CC BY-NC-SA) and are **not used** | Response field `licence`: "Data © OpenStreetMap contributors, ODbL 1.0" |
| Probe result | JPEG tiles at z10/13/15/17 for all 3 demo points, HTTP 200, 0.07–0.22 s; z15 shows field boundaries at Konya | "Çumra, Konya" → 2 results near 37.57, 32.78 (~16 s on the first request) |
| Limits | Imagery is from 2016; native detail ends near z15 (the app sets `maxzoom: 15` and enlarges beyond) | Usage policy: no autocomplete, ≤ 1 request/s, attribution; the app searches only on submit and waits ≥ 1.1 s between searches |
| Privacy | Tile requests reveal the map area being viewed to EOX | Only the typed text is sent (see `docs/PRIVACY.md`) |

### TKGM parcel query (ada/parsel) — not used ❌ (checked 2026-11-11)

Türkiye's cadastre (Tapu ve Kadastro Genel Müdürlüğü) offers a public web app,
[parselsorgu.tkgm.gov.tr](https://parselsorgu.tkgm.gov.tr/), backed by
`cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/` ("TKGM Parsel Sorgu Servisi"). There is
no public API documentation. Its terms of use
([Kullanım Koşulları V-1.0](https://parselsorgu.tkgm.gov.tr/app/documents/parsel-sorgu-kullanim-kosullari-v.1.0.pdf), read in full) say:

- item 3: the web services the app needs may **not** be accessed, directly or
  indirectly, **without permission from TKGM**;
- item 4: results are for information only, not for official use, and
  commercial use is forbidden;
- item 12: all rights reserved.

So calling the parcel service from Etügen would break item 3. MEGSİS
WMS/WFS services exist for partner institutions (TKGM MEGSİS page), with no
public sign-up found. Decision: not integrated unless TKGM gives written
permission. The field picker only links to the TKGM web site (new tab) and
explains how to find the same parcel on the satellite map; pasted map links
(Google Maps, OpenStreetMap, `geo:`) are parsed in the browser (`frontend/src/places.ts`).

## 7. Fallow and cover crops — source search (2026-11-11)

Goal: carry water stored in a fallow period into the next crop's water score,
and check whether cover crops can be modelled. Plan approved 2026-11-12
(`docs/drafts/plan_nadas_ortu_bitkisi.md`, K1-A, K2, K3-b); implemented, see
METHOD.md "Soil water between crops". Cover crops remain unmodelled.

### Methods (FAO-56, read in the original HTML and equation images)

| Item | Where in FAO-56 (Allen et al. 1998) | Checked how |
|---|---|---|
| Dual Kc: Ke = Kr (Kc max − Kcb) ≤ few Kc max (eq. 71); TEW (eq. 73); Kr = (TEW − De)/(TEW − REW) (eq. 74); few (eq. 75); topsoil balance De (eq. 77, 78); DPe (eq. 79); Kc max (eq. 72) | ch. 7, [x0490e0c](https://www.fao.org/4/X0490E/x0490e0c.htm) | text + equation GIFs `x0490e2q/2r/2u/2v` read |
| Table 19: θFC, θWP, REW, TEW (Ze = 0.10 m) for 9 USDA texture classes | ch. 7 | extracted from the HTML table; note: the "Silty clay" θFC cell is printed "0-30 - 0.42" (typo for 0.30) |
| Example 31: 10-day evaporation from bare loam after rain (TEW 20, REW 9, Kc max 1.20, ETo 4.5) | ch. 7 | day-by-day table extracted → planned unit test |
| TAW (eq. 82), RAW (eq. 83), Ks (eq. 84), root-zone balance Dr (eq. 85, 86), initial depletion (eq. 87), deep percolation (eq. 88) | ch. 8, [x0490e0e](https://www.fao.org/4/X0490E/x0490e0e.htm) | text + GIF `x0490e2w` read |
| **Non-growing periods, bare soil:** "the values for Kcb and for Kc min in Equations 71 and 76 should be set equal to zero" and a daily balance of topsoil and root zone is used; mulch: reduce TEW by 5 % per 10 % cover; frozen/snow: ETo of limited value | ch. 11, [x0490e0h](https://www.fao.org/4/X0490E/x0490e0h.htm) | text read |
| Vegetation without tabulated Kc: Kcb mid from LAI (eq. 97) or ground cover (eq. 98); Kcb full from height, Kcb,h = 1.0 + 0.1 h (eq. 101), climate adjustment (eq. 100) | ch. 9, [x0490e0f](https://www.fao.org/4/X0490E/x0490e0f.htm) | text read; eq. 98–100 are images, not yet read |

With h = 0 (bare soil) eq. 72 gives Kc max = max(1.2, Kcb + 0.05) = 1.20, the
value used in Example 31.

**Texture class gap.** SoilGrids puts all three demo points in USDA clay loam
(Konya at the border with silty clay loam, sand 20.5 %). Table 19 has no clay
loam row. TEW can be computed from SoilGrids θ with eq. 73 (no class needed);
REW only exists per class (neighbouring classes loam 8–10, silty clay loam
8–11, clay 8–12 mm). Proposed: REW = 9 mm as a **labelled assumption** with
8 and 11 mm as sensitivity bounds (Konya: stored water changes by ≤ 1 mm).

### Plausibility reference (not a model input)

- **Janssen, B.H. (1972).** The significance of the fallow year in the
  dry-farming system of the Great Konya Basin, Turkey. Neth. J. Agric. Sci.
  20:247–260. Read in full (WUR open journal archive,
  [PDF](https://library.wur.nl/ojs/index.php/njas/article/download/17273/16687)).
  - p. 248–249: winter wheat–fallow; the fallow usually lasts **15 months**
    (harvest July → sowing October of the next year); land kept under stubble
    until spring ploughing.
  - p. 250: in fallow fields "moisture loss during summer was mainly
    restricted to the upper 20 cm" (supports the FAO-56 two-layer model in
    which bare-soil evaporation comes from the top layer only); p. 251: no deep
    percolation on the trial fields; runoff very small on flat fields.
  - p. 257: fallow efficiency (stored / fallow rainfall) in the Basin
    **14–33 %** (citing Janssen 1970b); 10–30 % in older literature (p. 249).
  - p. 258, Table 4: stored-moisture levels 0–120 mm used in the calculation.
  - p. 258: the Basin is an area "where precipitation varies between 260 and 350 mm" — much less
    than POWER (≈ 560 mm) or IMERG (≈ 450 mm) at our point (stage 3).
- Adil, M. et al. (2022). Effects of fallow management practices on soil water,
  crop yield and water use efficiency in winter wheat monoculture system: a
  meta-analysis. Front. Plant Sci. 13:825309, doi:10.3389/fpls.2022.825309,
  CC BY. Relative effects only: no-till +42.5 % PSE vs conventional tillage;
  **cover cropping in the fallow lowered soil water at wheat planting by
  16.3 %** (Results, mulching section). Used only as a direction check for
  cover crops in dry areas.
- Nielsen & Vigil (2010), Agron. J. (PSE 20 % conventional / 35 % no-till,
  Colorado): seen only in a search snippet, paper not accessible → not cited.

**Konya scratch check (2026-11-11, not committed code).** FAO-56 bare-soil
balance (Kcb = 0, Kc max 1.20, few = 1, RO = 0, TEW 20.3, REW 9, TAW from
SoilGrids over the wheat root zone, profile assumed empty at harvest), POWER
2001–2025, model winter-wheat window (sowing 09-01, harvest ≈ 05-19), 23 years:

| Case | Rain in gap (median) | Stored at sowing | Storage efficiency (p20–p80) | Deep percolation |
|---|---|---|---|---|
| Wheat → wheat (3.5-month summer gap) | 39 mm | 0 mm | 0 % | 0 |
| Wheat → fallow → wheat (15.5 months), Zr 1.5 m | 617 mm | 119 mm | **19 %** (16–23 %) | 123 mm |
| same, Zr 1.8 m | 617 mm | 147 mm | 23 % (20–28 %) | 95 mm |
| same, θFC at 10 kPa, Zr 1.5 m | 617 mm | 168 mm | 26 % (22–30 %) | 74 mm |

Efficiency falls inside Janssen's 14–33 %. **Discrepancy:** the model fills the
profile to field capacity every winter and drains ~100 mm below the root zone,
while Janssen observed no deep percolation. Most likely cause: POWER rainfall
is too high here (stage 3: +24 % vs IMERG; Janssen's stations 260–350 mm).
The IMERG option must be part of the implementation check.

### Cover crops

| Crop | Kc / Kcb | Height, root depth | Temperature | Verdict |
|---|---|---|---|---|
| Cereal rye (*Secale cereale*) | Pereira et al. 2021, Agric. Water Manage. 243:106466, doi:10.1016/j.agwat.2020.106466, **Table 13** p. 28: updated standard Kc mid 1.00, Kc end 0.35; Kcb mid 0.95, Kcb end 0.30. Text p. 26: rye values "added on the basis of non-cited material" (no observed data, all "n/r"). Read in the author copy (repositorio.ulisboa.pt); © Elsevier, numbers cited as facts | Same paper **Table 15** p. 30: Zr 0.60–1.20 m, h 0.90 m, p 0.55 (indicative) | Pessotto et al. 2023, Agrosyst. Geosci. Environ. 6(3):e20393, doi:10.1002/agg2.20393, CC BY: abstract gives base −4.5 °C and optimum 24.8 °C, fitted on **leaf appearance** over 21 days in growth chambers (development, not biomass growth). Full text blocked by bot checks (Wiley, uark ScholarWorks) — tables not read | **Possible, low evidence**: Kc is grain rye, not a terminated cover crop; no stage lengths (FAO-56 Table 11 has no rye) |
| Common vetch (*Vicia sativa*) | none found (not in FAO-56 Tables 12/17, not in Pereira 2021) | none | Pessotto 2023 tables (not readable, see above) | **Stays unmodelled** |
| White mustard (*Sinapis alba*) | Pereira 2021 has only Indian mustard *Brassica juncea* (another species) → not transferable | — | — | **Stays unmodelled** |
| Phacelia | nothing found | — | — | **Stays unmodelled** |


## 8. Sowing calendar: observed crop calendar and wheat development — source search (2026-11-12)

Problem: at Konya the model's best winter-wheat window is sowing 09-01 →
harvest ≈ 05-19, while local practice is October → July. Diagnosis
(POWER 2001–2025, rainfed): thermal time is not the cause — the model's 10-16
window already ends ≈ 07-02 after 260 days. The model prefers September
because an earlier season escapes the summer drought (water score 0.45 vs
0.36), and nothing penalises it: no vernalisation, no photoperiod, no
sowing-moisture rule. Plan `docs/drafts/plan_ekim_takvimi.md` approved
2026-11-12 (K1-a, h5py for the conversion only, vernalisation later); the GGCMI
calendar is used since then, see METHOD.md "Local sowing calendar".

### GGCMI Phase 3 crop calendar ✅ (used: `data/ggcmi_crop_calendar.npz`, 1.1 MB, 17 crops × rainfed/irrigated)

- Ray, D., Jägermeyr, J., Minoli, S., Siebert, S., Müller, C. (2021). GGCMI Phase 3
  crop calendar. Zenodo, doi:10.5281/zenodo.5062513, **CC BY 4.0** (from the
  Zenodo API). Method: Jägermeyr et al. (2021), Nature Food 2:873–885,
  doi:10.1038/s43016-021-00400-y.
- Content: planting and maturity day of year for 18 crops, rainfed and
  irrigated, 0.5° grid, static multi-year average; merged from MIRCA2000,
  SAGE (Sacks et al. 2010), Iizumi et al. 2019, RiceAtlas, national statistics
  (layer `data_source_used`); cells outside cropland are extrapolated. Separate
  winter and spring wheat calendars. 36 files of 50–145 KiB, NetCDF-4/HDF5.
- Probe: `scripts/probe/probe_ggcmi_calendar.py` checks the record, licence and
  files. Values were read once with h5py in a throw-away environment (not a
  project dependency); all 36 grids compress to 965 KiB as uint16 `.npz`.
- Nearest 0.5° cell to the demo points: Konya 37.75, 32.75; Punjab 30.75, 75.75;
  Nakuru −0.25, 36.25.

Model best window vs GGCMI rainfed calendar (selected crops; POWER, rainfed):

| Point | Crop | Model best (sow → harvest, score) | GGCMI (plant → maturity, source) | Model at the GGCMI date |
|---|---|---|---|---|
| Konya | winter wheat | 09-01 → 05-19, 0.38 | 10-21 → 07-09 (SAGE) | 10-16 → 07-02, 0.31 |
| Konya | spring wheat | 08-16 → 04-16, 0.38 | 03-31 → 07-25 (SAGE) | 04-01 → 08-05, 0.14 |
| Konya | soybean | 05-01 → 10-19 | 05-04 → 09-21 | same window |
| Punjab | winter wheat | **07-16 → 09-25**, 0.31 | 11-04 → 04-16 (India statistics) | 11-01 → 03-09, 0.18 |
| Punjab | rice | 07-01 → 10-14 | 06-29 → 11-26 (RiceAtlas) | same window |
| Punjab | potato | 07-01 → 09-30 | 02-09 → 05-12 | 02-16 → 06-02, 0.07 |
| Nakuru | maize | 03-16 → 09-24 | 10-12 → 01-09 (Dimou et al.) | 10-16 → 04-16, 0.35 |
| Nakuru | millet | 05-16 → 10-12 | 04-10 → 08-08 | 04-16 → 09-07, 0.78 |

Of the 29 crop/point pairs with both a model window and a calendar, 15 differ
by ≤ 45 days in sowing and 14 by more; the largest errors are cool-season crops
sown into a hot or monsoon season (Punjab wheat, potato, dry bean), the same
cause as the earlier lentil finding (no heat/vernalisation limits). Nakuru has
two rainy seasons, while GGCMI gives one season per crop and cell, so a
difference there is not necessarily a model error.

### GGCMI data source codes (checked 2026-11-14)

`data_source_used` per cell, counted over the 0.5° grid (259 200 cells) in
`data/ggcmi_crop_calendar.npz`: 1 MIRCA2000, 2 SAGE, 3 Iizumi et al. 2019,
4 RiceAtlas, 5 Dimou et al. 2018, 6 ChinaCropPhen, 7 India agricultural
statistics, 8 Brazil CONAB, 9 Australia ABARES; **0 = no named source**. All
rainfed grids have 0 in 191 780 cells (ocean and non-cropland; the Zenodo
record says cells outside cultivated areas are "spatially extrapolated and
original data gap-filled", method in Jägermeyr et al. 2021). The irrigated
grids of sugar beet (all cells), sunflower, cassava, potato, groundnut, pea,
rapeseed, cotton, millet, barley and sorghum have a named source in only
0–6 % of all cells (every rainfed grid: 26 %), so most irrigated values of these crops are gap-filled. At
the Punjab cell (30.75, 75.75): irrigated barley 06-01 → 10-24 and sugar beet
04-01 → 09-30 have source 0; rainfed barley 11-01 (MIRCA2000), rainfed sugar beet
06-01 (MIRCA2000) and dry pea 06-11 → 11-11 (India agricultural statistics,
rainfed and irrigated) have named sources. Rule: METHOD.md "Local sowing calendar".

### Wheat vernalisation and photoperiod: DSSAT CERES-Wheat (open source)

- DSSAT-CSM, github.com/DSSAT/dssat-csm-os, **BSD-3-Clause** (GitHub API).
  Read in `Plant/CERES-Wheat_Barley/CER_Growth.for`, `CER_Integrate.for` and
  `Data/Genotype/WHCER048.CUL/.ECO/.SPE` (branch `develop`, 2026-11-12):
  - development units DU = TT × VF × DF (CER_Growth.for, "Developmental units");
  - vernalisation: CUMVD += TFV − VDLOST, TFV = trapezoid of mean temperature
    with TRVRN = −5, 0, 7, 15 °C (SPE file); VDLOST = 0.5 (Tmax − 30) while
    CUMVD < 10 and Tmax > 30; VF = (1 − VEFF) + VEFF × min(1, CUMVD / P1V)
    (CER_Integrate.for);
  - photoperiod: DF = 1 − (P1D / 10000) (P1DT − daylength)², P1DT = 20 h,
    sensitive until growth stage 2 (PPEND, SPE file);
  - cultivars (CUL file): P1V vernalising days, P1D sensitivity, e.g. NEWTON
    (US winter wheat) P1V 48.45, P1D 73.5, VEFF 1.0; Yecora Rojo (AZWH18)
    P1V 10, P1D 40, VEFF 0.6.
- **Finding:** our `winter_wheat` uses SIMPLE parameters of cultivar Yecora
  Rojo (Zhao et al. 2019), which DSSAT lists with P1V = 10, i.e. a spring-type
  wheat. A true winter wheat needs a winter cultivar with consistent thermal
  time and vernalisation parameters; none is sourced yet.
- Wang & Engel (1998) and Streck et al. (2003) wheat development models: papers
  not accessible (paywalled), not used.

### Sowing-moisture rule

No open source with a general numeric threshold was found (searched
2026-11-12). A search snippet of a durum-wheat sowing-date study (Field Crops
Research 2020, not read) describes the Mediterranean window as opening with the
first significant rain after summer, without one number. Not adopted.

## 9. Kc climate adjustment (FAO-56 eq. 62 / 65) — sources and humidity data (2026-11-12)

Goal: adjust the FAO-56 Table 12 Kc_mid and Kc_end (valid for RHmin ≈ 45 %,
u2 ≈ 2 m/s) to the local climate. Plan: `docs/drafts/plan_kc_iklim_duzeltmesi.md`
(approved 2026-11-12: K1-a dew point, K2-a midpoint). Implemented, see
METHOD.md "Kc climate adjustment". The POWER demo cache was rebuilt with
`T2MDEW` (API v2.10.3); all other parameter values are identical to the old files.

### Methods (FAO-56, read in the original HTML and equation images)

| Item | Where in FAO-56 (Allen et al. 1998) | Checked how |
|---|---|---|
| Kc_mid = Kc_mid(Tab) + [0.04 (u2 − 2) − 0.004 (RHmin − 45)] (h/3)^0.3 (eq. 62); valid for 1 ≤ u2 ≤ 6 m/s, 20 ≤ RHmin ≤ 80 %, 0.1 < h < 10 m; "the limits ... should be observed"; u2 and RHmin are means over the mid-season stage | ch. 6, [x0490e0b](https://www.fao.org/4/X0490E/x0490e0b.htm) | text + GIF `x0490e2d` read |
| Kc_end: same form (eq. 65) with late-season means of u2 and RHmin; **only applied when Kc_end(Tab) exceeds 0.45**, no adjustment below | ch. 6 | text + GIF `x0490e2i` read |
| RHmin = 100 e°(Tdew) / e°(Tmax) (eq. 63); without dewpoint: Tdew ≈ Tmin (eq. 64), with Tmin − 2 °C in arid / semi-arid climates (footnote, Annex 6 eq. 6-6) | ch. 6; Annex 6 [x0490e0n](https://www.fao.org/4/X0490E/x0490e0n.htm) | text + GIFs `x0490e2e`, `x0490e2f` read |
| ea = e°(Tdew) (eq. 14); eq. 19 (ea from RHmean) "is less desirable than are Equations 17 or 18"; Example 5: eq. 19 gives 1.78 kPa vs 1.70 kPa from eq. 17 | ch. 3, [x0490e07](https://www.fao.org/4/X0490E/x0490e07.htm) | text read |
| Averaging: daily RHmin from Tmax and Tdew, then the mean of daily u2 and RHmin over the mid-season stage (spreadsheet columns AO/AP, footnotes 1 and 12) | Annex 8, [x0490e0p](https://www.fao.org/4/X0490E/x0490e0p.htm) | text read |
| **Example 27** (unit test): maize, Kc_mid(Tab) 1.20, h = 2 m; Taipei u2 1.3, RHmin 75 → **1.07**; Mocha u2 4.6, RHmin 44 → **1.30** | ch. 6 | GIFs `x0490e2g`, `x0490e2h` read; recomputed: 1.069, 1.296 |
| Box 14 (wheat, h = 1 m, climate classes of Tables 15/16): values read off Fig. 32 and rounded; not all reproduce eq. 62 exactly (e.g. "1.15 + 0.00 = 1.17"), so only a loose check | ch. 6 | text read |

### NASA POWER humidity parameters ✅ (probe `scripts/probe/probe_power_humidity.py`, 2026-11-12, API v2.10.3)

| Parameter (daily, `community=AG`) | Offered? | Units / definition (parameter manager) |
|---|---|---|
| `T2MDEW` | ✅ | °C, "Dew/Frost Point at 2 Meters" |
| `QV2M` | ✅ | g/kg, specific humidity at 2 m |
| `RH2M` (already used) | ✅ | %, daily mean RH |
| `WS2M` (already used) | ✅ | m/s, "The average of wind speed at 2 meters" |
| `WS2M_MAX`, `WS2M_MIN` | ✅ | m/s, hourly max / min |
| `RH2M_MIN`, `RH2M_MAX` | ❌ HTTP 422 | — (no daily RHmin in POWER) |

2001-01-01 … 2025-12-31, all three demo points: 9131 days, **0 fill values**
for T2M_MAX, T2M_MIN, RH2M, T2MDEW, QV2M, WS2M.

Mean RHmin (%) over 2001–2025 from three estimates
(A: ea from RH2M with eq. 19, RHmin = 100 ea / e°(Tmax); B: eq. 63 with T2MDEW;
C: eq. 64 with Tmin, no −2 °C):

| Point | A (RH2M) | B (T2MDEW) | C (Tmin) | mean daily abs(A − B) | mean u2 (m/s) |
|---|---|---|---|---|---|
| Konya | 46.2 | 40.1 | 44.7 | 6.2 | 2.21 |
| Punjab | 33.9 | 29.4 | 45.8 | 4.5 | 1.62 |
| Nakuru | 52.0 | 45.1 | 47.1 | 6.9 | 2.04 |

A is higher than B by 4–7 points at every point and month, as expected from
FAO-56 Example 5 (eq. 19 overestimates ea; POWER RH2M is also a mean of hourly
values, not (RHmax + RHmin)/2). C is far too humid in dry months (Punjab May:
C 42.6 vs B 15.4), which is why FAO-56 asks for Tmin − 2 °C in arid climates.
