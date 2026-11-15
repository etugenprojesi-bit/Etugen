# Credits and attributions

Every data set, API, library, base map and AI tool used by this project. Updated
in the same commit as any new dependency. "Used for" says where in the project.

## NASA data

| Name | Provider | Link | License / terms | Used for |
|---|---|---|---|---|
| POWER daily API (v2.10.2) | NASA Langley Research Center, POWER Project | https://power.larc.nasa.gov/ | No restrictions; acknowledgement requested | Daily climate (T, P, RH, wind, radiation), ET0, model soil wetness |
| MODIS Land Product Subsets web service (C6) | NASA ORNL DAAC | https://doi.org/10.3334/ORNLDAAC/1557 | Open, EOSDIS data use & citation guidance | NDVI / LST fallback; demo-point land-cover check |
| MOD13Q1 / MYD13Q1 v6.1 | NASA LP DAAC | https://doi.org/10.5067/MODIS/MOD13Q1.061 | No restrictions on use (LP DAAC) | NDVI seasonal curves, pattern finding (stage 3; MOD13Q1 via Earth Engine); NDVI anomaly risk layer (stage 5) |
| MCD12Q2 v6.1 Land Cover Dynamics (phenology) | NASA LP DAAC | https://doi.org/10.5067/MODIS/MCD12Q2.061 | No restrictions on use (LP DAAC) | Validation of model season timing (green-up, peak, green-down), via Earth Engine |
| MOD11A2 v6.1 | NASA LP DAAC | https://doi.org/10.5067/MODIS/MOD11A2.061 | No restrictions (LP DAAC) | LST / heat stress fallback (planned) |
| MCD12Q1 v6.1 | NASA LP DAAC | https://doi.org/10.5067/MODIS/MCD12Q1.061 | No restrictions (LP DAAC) | Checking demo points are cropland |
| MOD16A2GF v6.1 | NASA LP DAAC | https://doi.org/10.5067/MODIS/MOD16A2GF.061 | No restrictions (LP DAAC) | Actual ET (planned) |
| HLS L30 / S30 v002 | NASA LP DAAC | https://www.earthdata.nasa.gov/data/projects/hls | NASA open data policy | Field-scale NDVI (planned) |
| SMAP SPL3SMP_E v005/v006, SPL4SMGP v008 | NASA NSIDC DAAC | https://nsidc.org/data/smap | Public domain (NASA ESDS policy) | Observed surface soil moisture, 005 + 006 merged (stage 3; SPL4SMGP planned); soil-moisture anomaly risk layer (stage 5) |
| CHIRPS v2.0 (Climate Hazards Center InfraRed Precipitation with Station data) | Climate Hazards Center, UC Santa Barbara | https://www.chc.ucsb.edu/data/chirps | Public domain (copyright waived, per the Earth Engine catalog terms) | POWER rain check (warning) and optional rainfall source, via Earth Engine `UCSB-CHG/CHIRPS/DAILY` |
| GHCN-Daily (rain gauge KONYA `TUM00017244`) | NOAA NCEI | https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily | Freely accessible; used only for a documented cross-check, not stored or shown in the app | Check of POWER / IMERG / CHIRPS rainfall at Konya |
| GPM IMERG V07 | NASA GES DISC | https://gpm.nasa.gov/data/imerg | Freely available | Monthly precipitation, cross-check of POWER rainfall (stage 3); optional rainfall source for the water balance (stage 5); extreme events planned |
| GRACE/GRACE-FO JPL Mascon RL06.3 (CRI) | NASA JPL | https://grace.jpl.nasa.gov/ | Freely available; acknowledgement requested | Long-term water-storage trend (planned) |
| NASADEM v001 / SRTMGL1 v003 | NASA JPL / LP DAAC | https://doi.org/10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001 | NASA open data | Slope for the erosion sub-score (stage 3, NASADEM) |
| ECOSTRESS L2T LSTE V2 | NASA JPL / LP DAAC | https://ecostress.jpl.nasa.gov/ | Freely accessible; citation requested | Heat stress (planned) |
| GEDI L4B v2 / L4A v2.1 | NASA ORNL DAAC / Univ. of Maryland | https://gedi.umd.edu/ | Public domain | Biomass context (planned) |

## Other data

| Name | Provider | Link | License | Used for |
|---|---|---|---|---|
| SoilGrids v2.0 (WCS + REST) | ISRIC – World Soil Information | https://www.isric.org/explore/soilgrids | CC BY 4.0 | Texture, pH, organic carbon, bulk density, CEC |
| SoilGrids v2.0 water retention (wv0033, wv1500; Turek et al. 2023, doi:10.1016/j.iswcr.2022.08.001) | ISRIC – World Soil Information | https://www.isric.org/explore/soilgrids | CC BY 4.0 | Total available / evaporable soil water (TAW, TEW) for the soil water between crops (fallow) |
| FAO-56 ch. 7, 8, 11 (eq. 71–88), Table 19, Examples 31 and 35 | FAO (Allen et al. 1998) | https://www.fao.org/4/X0490E/x0490e0c.htm | © FAO publication; equations and numbers cited with source | Bare-soil / root-zone daily water balance between crops; unit tests |
| GGCMI Phase 3 crop calendar (Ray, Jägermeyr, Minoli, Siebert, Müller 2021; method Jägermeyr et al. 2021, Nature Food 2:873–885) | GGCMI / AgMIP | https://doi.org/10.5281/zenodo.5062513 | CC BY 4.0 | Local sowing calendar: planting / maturity day per 0.5° cell (`data/ggcmi_crop_calendar.npz`, values unchanged) |
| Fallow efficiency in the Great Konya Basin | Janssen 1972, Neth. J. Agric. Sci. 20:247–260 | https://library.wur.nl/ojs/index.php/njas/article/download/17273/16687 | Journal article; numeric values cited | Plausibility check only (14–33 %), not a model input |
| FAO-56 Tables 12 & 22 | FAO (Allen et al. 1998) | https://www.fao.org/4/X0490E/x0490e00.htm | © FAO publication; numeric parameters cited with source | Crop coefficients, root depth, depletion fraction in `data/crops.yaml` |
| FAO ECOCROP data sheets | FAO | https://ecocrop.apps.fao.org/ecocrop/srv/en/cropSearchForm | **No licence stated**; used by user decision 2026-11-12, labelled; reuse terms requested from FAO (see DATA_SOURCES.md §5) | Temperature ranges of 28 crops without literature values (11 field crops, 15 vegetables and pulses added 2026-11-13, Sudan grass and berseem clover added 2026-11-14) |
| ECOCROP model method (`dismo::ecocrop`) | R. J. Hijmans, R package dismo | https://github.com/rspatial/dismo/blob/master/R/ecocrop.R | GPL-3 (code not used; method described) | Temperature trapezoid, worst-month rule |
| FAO-56 Table 11 | FAO (Allen et al. 1998) | https://www.fao.org/4/X0490E/x0490e0b.htm | © FAO publication; numeric parameters cited with source | Crop stage lengths (`data/fao56_table11.yaml`) |
| SIMPLE crop model parameters (Table 1a) | Zhao et al. 2019, European Journal of Agronomy | https://doi.org/10.1016/j.eja.2019.01.009 | Journal article; numeric parameters cited | Crop temperature response and thermal time |
| SIMPLE crop model, NetLogo implementation (parameter CSV) | A. Angourakis | https://doi.org/10.5281/zenodo.4557347 | GPL-3.0 (code not used; only the transcribed numbers, cited) | Source of the transcribed Table 1a values |
| Temperature thresholds review | Luo 2011, Climatic Change | https://doi.org/10.1007/s10584-011-0028-6 | Journal article; numeric values cited | Sorghum temperatures, wheat/barley lethal minimum (also the lethal-cold risk layer, stage 5) |
| OpenStreetMap data (via OpenMapTiles / OpenFreeMap) | OpenStreetMap contributors | https://www.openstreetmap.org/copyright | ODbL 1.0; attribution shown on the map | Base map; road lines and place names on the satellite map (stage 7) |
| Sentinel-2 cloudless 2016 (EOxCloudless, WMTS layer `s2cloudless_3857`) | EOX IT Services GmbH (contains modified Copernicus Sentinel data 2016) | https://s2maps.eu / https://cloudless.eox.at | CC BY 4.0 (stated in the layer abstract; later years are CC BY-NC-SA, not used); attribution shown on the map | Satellite base map for picking a field (stage 7) |
| Nominatim place search | OpenStreetMap Foundation; data © OpenStreetMap contributors | https://nominatim.org / https://operations.osmfoundation.org/policies/nominatim/ | ODbL 1.0 data; usage policy: no autocomplete, ≤ 1 request/s, attribution | Searching a village or district name in the field picker (stage 7) |
| Lentil phenology (Table 1) | Sadras, Rosewarne & Lake 2021, Frontiers in Plant Science | https://doi.org/10.3389/fpls.2021.674327 | CC BY 4.0 | Lentil base temperature and thermal time |
| Sunflower base temperature and thermal time (Tables 1–2) | Maldaner et al. 2018, Brazilian Journal of Agriculture | https://doi.org/10.37856/bja.v93i3.3173 | Open access journal; numeric values cited | Sunflower base temperature and thermal time |
| Pearl millet thermal units (Tabelas 1–2) | Costa et al. 2005, Pesquisa Agropecuária Brasileira | https://doi.org/10.1590/S0100-204X2005001200003 | CC BY-NC 4.0; only a few numeric values used, with attribution; kept by team decision 2026-11-09 (project is non-commercial) | Millet base temperature and thermal time |
| Chickpea phenology model description | Chauhan et al. 2023, Agronomy for Sustainable Development | https://doi.org/10.1007/s13593-023-00903-x | CC BY 4.0 | Chickpea base temperature |
| WOFOST crop-specific parameters (Appendix C1, C3 Table C3b) | Boons-Prins, de Koning, van Diepen & Penning de Vries 1993, Simulation Reports CABO-TT 32, Wageningen | https://edepot.wur.nl/308997 | Openly available technical report, no licence stated; only numeric parameters cited | Barley thermal time (development table, emergence phase) |
| Wheat phenology at PAU Ludhiana (Table 1, days sowing to maturity) | Kaur, Kingra, Singh, Kaur & Bora 2025, Indian Journal of Agronomy 70(4):499–502, doi:10.59797/ija.v70.i4.5677 | https://pub.isa-india.in/index.php/ija/article/view/7016 | Freely accessible journal article, no licence stated; only numeric values cited | Regional thermal time of wheat in Indian Punjab (derived with NASA POWER) |
| WOFOST crop parameter files (cross-check only) | Wageningen Environmental Research (A. de Wit), WOFOST_crop_parameters | https://github.com/ajwdewit/WOFOST_crop_parameters | EUPL-1.2 (not redistributed; values taken from the 1993 report) | Cross-check of the barley values (one discrepancy, TBASEM) |
| RUSLE slope steepness factor S, eq. 4-4/4-5 (McCool et al. 1987) | Renard et al. 1997, USDA Agriculture Handbook 703, ch. 4 p. 107 | https://www.ars.usda.gov/Research/docs.htm?docid=6028 | US Government work (public domain) | Slope factor in the erosion sub-score |
| Radiation-use efficiency principle | Monteith 1977, Phil. Trans. R. Soc. B 281:277–294 | https://doi.org/10.1098/rstb.1977.0140 | Journal article; method cited | Light factor in the suitability score (stage 5) |
| Warming effect on global crop yields | Zhao C. et al. 2017, PNAS 114(35):9326–9331 | https://doi.org/10.1073/pnas.1701762114 | Journal article; result cited | Plausibility check of the scenario sliders (stage 5) |
| Pettitt change-point test | Pettitt 1979, Applied Statistics 28(2):126–135 | https://doi.org/10.2307/2346729 | Journal article; method cited | Homogeneity check of POWER vs IMERG rainfall; NDVI regime shifts |
| Plants of the World Online | Royal Botanic Gardens, Kew | https://powo.science.kew.org/ | Reference (families to verify) | Crop botanical families |

## Platforms and services

| Name | Provider | Link | Terms | Used for |
|---|---|---|---|---|
| Earth Engine | Google | https://earthengine.google.com/ | Noncommercial use with registered Cloud project | Server-side extraction of NDVI, SMAP, IMERG and NASADEM point series (stage 3) |
| OpenFreeMap (public tile instance, style "liberty") | OpenFreeMap project | https://openfreemap.org/ | Free, no key, no usage limits; software MIT; attribution required ("© OpenMapTiles", "Data from OpenStreetMap"), shown by MapLibre | Base map tiles |
| Earth Engine public STAC catalog | Google | https://storage.googleapis.com/earthengine-stac/catalog/catalog.json | Public | Verifying dataset IDs |
| Anthropic API (optional) | Anthropic | https://docs.anthropic.com/ | Commercial API terms | Optional plain-language rewording of rotation cards (stage 4, default model `claude-opus-5-5`, set by `ANTHROPIC_MODEL`); the app works fully without it |

## Software (direct dependencies)

| Name | Version | License | Used for |
|---|---|---|---|
| Python | 3.14 | PSF-2.0 | Backend, probes |
| httpx | 0.28.1 | BSD-3-Clause | HTTP client |
| PyYAML | 6.0.3 | MIT | Reading `crops.yaml` |
| earthengine-api | 1.7.51 | Apache-2.0 | Earth Engine client |
| numpy | 2.5.4 | BSD-3-Clause (+ bundled 0BSD, MIT, Zlib, CC0-1.0) | Numerics |
| tifffile | 2026.10.15 | BSD-3-Clause | Reading SoilGrids WCS GeoTIFFs |
| h5py | 3.16.0 | BSD-3-Clause | One-off conversion of the GGCMI crop calendar (NetCDF-4/HDF5) in `scripts/build_crop_calendar.py`; not needed at runtime |
| FastAPI | 0.162.0 | MIT | Backend web API |
| Starlette | 1.10.0 | BSD-3-Clause | FastAPI's web framework layer |
| Uvicorn | 0.54.0 | BSD-3-Clause | ASGI server |
| pandas | 3.1.0 | BSD-3-Clause | Time-series handling |
| pydantic | 2.14.2 | MIT | Request validation (via FastAPI) |
| pytest | 9.2.0 | MIT | Unit tests |
| pytest-asyncio | 1.4.1.post1 | Apache-2.0 | Async tests |
| anthropic (Python SDK) | 2.6.0 | Apache-2.0 | Optional LLM explanations |
| httpx2 | 2.16.0 | BSD-3-Clause | HTTP layer of the anthropic SDK |
| scikit-learn | 1.9.1 | BSD-3-Clause | k-means clustering of NDVI curves, Isolation Forest (stage 3 pattern comparison) |
| SciPy | 1.18.1 | BSD-3-Clause | Installed with scikit-learn (not used directly) |
| joblib, threadpoolctl, cloudpickle | 1.6.0, 3.8.0, 3.1.2 | BSD-3-Clause | Installed with scikit-learn (not used directly) |
| narwhals | 2.28.0 | MIT | Installed with scikit-learn (not used directly) |

### Frontend (direct dependencies, `frontend/package.json`)

| Name | Version | License | Used for |
|---|---|---|---|
| React, React DOM | 19.3.1 | MIT | User interface |
| MapLibre GL JS | 6.17.0 | BSD-3-Clause | Interactive map |
| Recharts | 3.10.1 | MIT | Monthly climate chart |
| Vite | 8.3.6 | MIT | Dev server and build |
| @vitejs/plugin-react | 6.2.1 | MIT | React support for Vite |
| vite-plugin-pwa (uses Workbox 7.4.1, MIT) | 2.0.0 | MIT | Installable app: manifest + service worker |
| TypeScript | 7.0.2 | Apache-2.0 | Type checking |
| oxlint | 1.92.0 | MIT | Linting (template default) |

App icons are generated by `scripts/make_icons.py` (own work, Apache-2.0).

All direct and transitive dependencies with their licences: [`DEPENDENCIES.md`](DEPENDENCIES.md),
generated by `scripts/list_dependencies.py` (stage 6). All licences found are OSI-approved or
free-content licences (MIT, BSD, Apache-2.0, ISC, PSF-2.0, MPL-2.0, BlueOak-1.0.0, MIT-0, 0BSD,
Zlib, CC0-1.0, and CC-BY-4.0 for the browser-support data `caniuse-lite`, a build tool not shipped).

## AI tools

| Name | Provider | Used for |
|---|---|---|
| Claude (Claude Code) | Anthropic | Coding assistant for writing code, probes and docs, reviewed by the team |
