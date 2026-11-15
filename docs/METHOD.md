# Method

What each part of the analysis does, and whether it is **physics**, a
**rule**, **classical statistics** or **machine learning**. Every API result
carries a `method` list with the same tags. Machine learning is used only in
the stage 3 pattern comparison (k-means, Isolation Forest), next to classical
alternatives on the same data.

## Stage 1 pipeline

```
lat/lon ──► round to 0.05° ──► NASA POWER daily, 25 complete years (~0.5° grid)
                                   │   (SQLite cache → network → demo_cache fallback)
                                   ▼
                      daily ET0 (FAO-56 Penman-Monteith)            [physics]
                                   │
           ┌───────────────────────┴───────────────────────┐
           ▼                                               ▼
   climate profile                                 crop suitability
   monthly normals, P−ET0, frost/hot days,         24 sowing dates × 25 years × crop
   heavy-rain days (R95p)              [stat]      thermal-time season length   [rule]
   Mann-Kendall + Sen's slope trends   [stat]      heat factor, cold days       [rule]
                                                   Kc(t) × ET0 water use        [physics]
                                                   10-day rain deficit          [rule]
                                                   median / bad year / failure rate [stat]
                                                   confidence + local questions [rule]
```

## Climate profile

| Feature | Definition | Type |
|---|---|---|
| ET0 | FAO-56 eq. 6, daily, G = 0; ea from mean RH (eq. 19) because POWER gives daily mean RH only; Rs/Rso ≤ 1 | physics |
| Monthly normals | mean over years of monthly mean T / monthly sums of P and ET0 | stat |
| Water balance | monthly P − ET0 | physics |
| Frost day | Tmin < 0 °C; frost probability = share of years with ≥ 1 frost day in that month | rule |
| Hot day | Tmax > 35 °C (generic; crop-specific heat thresholds are used in suitability) | rule |
| Heavy-rain day | P above the 95th percentile of wet days (P ≥ 1 mm) of the whole record (ETCCDI R95p style) | stat |
| Trends | annual values; Mann-Kendall test (tie-corrected variance, two-sided p) and Sen's slope, reported per decade | stat |
| Soil wetness | POWER `GWETROOT` — **MERRA-2 model output, not SMAP observations** | model |

Unit tests reproduce FAO-56 Example 18 (ET0 = 3.88 mm/day) step by step.

## Crop suitability and sowing windows

For each crop, each sowing date (1st and 16th of every month) and each year:

1. **Season length.** Thermal time from the SIMPLE crop model (Zhao et al.
   2019): the season ends when Σ max(0, Tmean − t_base) reaches t_sum. Crops
   without t_sum use the FAO-56 Table 11 length (median-length row). Crops
   sourced from WOFOST (barley) use the source's own development rules, see
   "WOFOST thermal time" below.
2. **Season limits (assumptions).** A season fails if it would last longer than
   1.25 × the longest FAO-56 Table 11 season for that crop (e.g. a summer crop
   that would have to overwinter), and is never longer than 365 days.
3. **Temperature score.** Season mean of [Tmean > t_base] × the SIMPLE heat
   factor (1 below t_heat, linear to 0 at t_ext, on daily Tmax). Days below
   t_base count as lost days. For crops without t_sum the SIMPLE growth factor
   (0 at t_base, linear to 1 at t_opt) replaces [Tmean > t_base].
4. **Duration factor (assumption).** min(1, days / (0.75 × shortest FAO-56
   season)). Very short, heat-accelerated seasons yield less.
5. **Water score.** ETc = Kc(t) × ET0, with the FAO-56 Kc curve built from
   Table 12 coefficients and Table 11 stage proportions; Kc_mid and Kc_end
   are adjusted to the local wind and RHmin (FAO-56 eq. 62/65, see "Kc climate
   adjustment" below). Rainfed deficit = Σ
   over 10-day blocks of max(0, ETc − P). Score = 1 − deficit / ETc.
   Irrigation: `full` = no deficit; `limited` = **assumption** that half the
   deficit is covered.
6. **Season score** = temperature × water × duration × light. The light factor
   (added in stage 5) is min(1, season solar radiation / median for that
   sowing date in the baseline climate); see "Light factor" under stage 5.
7. **Over years:** median score, bad-year score (20th percentile) and failure
   rate (score < 0.4 or not matured). Best window = highest median;
   "good sowing dates" = within 0.05 of the best median and at least 90 % of
   it (so uniformly poor results do not mark every month as good).
8. If no sowing date works, the status is `not_suitable_by_model` with the
   limiting factor. This is a model result to check locally, not a verdict.

### Local sowing calendar (GGCMI) — rule

Decided 2026-11-12 (plan `docs/drafts/plan_ekim_takvimi.md`, K1-a). Code:
`app/suitability/calendar.py`; data `data/ggcmi_crop_calendar.npz` built by
`scripts/build_crop_calendar.py` from the GGCMI Phase 3 crop calendar
(Zenodo doi:10.5281/zenodo.5062513, CC BY 4.0; `docs/DATA_SOURCES.md` §8).

| Step | Definition | Type |
|---|---|---|
| Local calendar | Observed planting / maturity day of year of the crop at the nearest 0.5° cell; rainfed calendar, irrigated calendar only with `full` irrigation (**assumption**: "limited" follows the rainfed calendar) | observation |
| Window label | `in_local_calendar` = sowing date within **±45 days** of the local planting day (**assumption**: GGCMI is a multi-year average, sowing moves between years) | rule |
| Best window | Chosen among the labelled windows; the best window outside them is reported as `best_window_outside_calendar` | rule |
| Rotations | Only labelled windows become rotation slots; the current rotation prefers them | rule |
| Switch | `explore_sowing=true` (UI: "Farklı ekim zamanlarını da dene") ignores the calendar, e.g. to look for new sowing dates under a scenario | user input |
| Source rule (2026-11-14, K1) | GGCMI marks each cell's data source (`data_source_used`); 0 = no named source (gap-filled / extrapolated). If the requested system (rainfed or irrigated) is gap-filled at the cell and the other system has a named source, the other system's calendar is used (`fallback_from`); otherwise the value is used and labelled `gap_filled` | rule |
| Conflict rule (2026-11-14, K2) | If the crop can grow in some window but **every** window within ±45 days of the local planting day has median score 0, the calendar is not applied for this crop (`calendar_conflict`, confidence "low" with reason `calendar_conflict`) | rule |

Why: the model has no vernalisation, photoperiod, sowing-moisture, heat-disease
or waterlogging limits, so it sometimes sows a crop when no farmer would (wheat
in the Punjab monsoon). The calendar brings in these unmodelled constraints as
observed practice. Crops without a GGCMI calendar (lentil, chickpea, faba bean,
oats, forage and cover crops) keep the free choice.

Effect at the demo points (POWER, rainfed): Punjab winter wheat 07-16 → 11-16
(score 0.31 → 0.19; Punjab wheat is irrigated in practice), Nakuru maize
03-16 → 09-01 (0.74 → 0.42), Konya winter wheat 09-01 → 09-16 (0.38 → 0.38;
the local planting day is 10-21, so 09-16 is still within ±45 days). In some
cells every in-calendar window scores 0 (Nakuru rice and soybean): the model and
the local calendar disagree, and the card says so.

**GGCMI oddities at Punjab (decided 2026-11-14, plan `docs/drafts/plan_ggcmi_takvim.md`).**
Irrigated barley planted 06-01 and irrigated sugar beet 04-01 come from cells
with no named source (the irrigated sugar-beet calendar has no named source in
any cell worldwide; irrigated sunflower, cassava, potato, groundnut, rapeseed
and cotton have one in < 3 % of the cells). With the source rule they use the
observed rainfed cell (barley 11-01 MIRCA2000, best window 12-01). Dry pea
06-11 does have a named source (India agricultural statistics), but the model
cannot grow it in any of those summer windows, so the conflict rule lets the
best window be chosen freely (11-16). **Still odd:** irrigated sugar beet now
follows the rainfed MIRCA2000 cell (06-01), where the model reaches 0.33
(07-16), so the conflict rule does not apply and the better out-of-calendar
window (10-16, 0.81) is only reported, not used. Effect on the demo rotations: only
Punjab and Nakuru with full irrigation change (0.724 → 0.736, cotton + dry pea
after sorghum + lentil; 0.772 → 0.776). The conflict rule also unlocks Nakuru
soybean (02-16 rainfed, 01-01 irrigated) and rice (10-01), sown outside the
GGCMI season; their cards are "low" confidence and say why. Not changed: the
gap-filled values are still used where no observed alternative exists
(labelled in the crop list).

### Regional cultivar variants (Punjab wheat)

Decided 2026-11-14 by the user (plan `docs/drafts/plan_punjab_bugday_sicak_esik.md`,
K1-a). Code: `crops.localize`; data: `regional` blocks in `data/crop_phenology.yaml`.

| Step | Definition | Type |
|---|---|---|
| Region | Point inside a box around Indian Punjab (lat 29.5–32.6, lon 73.8–77.0; **assumption**) **and** its GGCMI winter-wheat cell sourced from "India agricultural statistics" (this excludes the Pakistani cells in the box) | rule |
| Variant | winter and spring wheat: t_sum 2482–2639 °C·d (mean 2560), base 0 °C; all other parameters from the base cultivar (Yecora Rojo, SIMPLE) | data (derived) |
| Derivation (**assumption**, labelled) | Kaur et al. 2025, Table 1: 154 / 146 / 136 days sowing → maturity for 6 Nov / 24 Nov / 12 Dec 2023 at PAU Ludhiana (three PBW cultivars); Σ max(0, Tmean) over those seasons from NASA POWER at the same 0.5° GGCMI cell. One season, one site | physics + observation |
| Report | crop entry `cultivar_variant`; confidence reason `regional_variant` | — |

Effect: MODIS check at Punjab, winter wheat (11-01) maturity − green-down −20 → **−4 d**;
spring wheat (12-01) +6 → +18 d, consistent with the field harvest dates (17–25 April).
Rotations: Punjab unchanged at #1 (0.639 rainfed, 0.736 irrigated).

### WOFOST thermal time (barley)

Decided 2026-11-12 (plan `docs/drafts/plan_sicaklik_parametreleri.md`, K1-a,
K2-a, K3-a). Code: `engine.daily_thermal_time`, `crops.Emergence`; data
`data/crop_phenology.yaml`. Source: Boons-Prins et al. 1993 (WOFOST EU
calibration, open report, `docs/DATA_SOURCES.md` §5).

| Step | Definition | Type |
|---|---|---|
| Sowing → emergence | Σ min(max(0, Tmean − TBASEM), TEFFMX − TBASEM) reaches TSUMEM (barley 3 °C, 30 °C, 110 °C·d) | data |
| Emergence → maturity | Σ DTSMTB(Tmean) reaches TSUM1 + TSUM2; DTSMTB is the source's piecewise-linear table, held constant beyond its ends (barley 0 → 0, 35 → 35, 45 → 35 °C·d; 800 + 750 = 1550 °C·d) | data |
| Other crops | unchanged: Σ max(0, Tmean − t_base) from sowing | — |

Barley has **no heat-stress thresholds** (confidence "low", hot-season sowings
not penalised) and is a spring-barley calibration without vernalisation; the
GGCMI local calendar limits its sowing windows. Faba bean has parameters in the
same report but stays `insufficient_data` (decision K3-a): it has no GGCMI
calendar and no heat threshold, and the model sowed it into the Punjab monsoon.

**Effect at the demo points** (POWER, local calendar, best window):

| Point | Barley best window | Rotations |
|---|---|---|
| Konya, rainfed | 10-01 → 05-24 (236 d), score 0.48, bad year 0.38 (GGCMI: 11-01 → 06-23) | new first: barley → lentil 0.512 (before: wheat → lentil 0.508, still second); barley → fallow 0.490 replaces lentil → fallow |
| Konya, full irrigation | 01-01 → 07-07, 0.85 | lentil → barley 0.622 enters as second |
| Punjab, rainfed | 12-16 → 03-25, 0.24 (water-limited; below the rotation threshold) | unchanged |
| Punjab, full irrigation | 07-16 → 09-09 (56 d), 0.61 — the GGCMI irrigated barley calendar for this cell has a June planting (data source "unknown"), so the window is inside it; questionable | unchanged |
| Nakuru, rainfed | 10-01 → 12-30 (91 d), 0.67 (GGCMI: 10-12 → 01-23) | third card now sunflower → lentil + barley 0.673 |
| Nakuru, full irrigation | 09-01 → 11-30, 1.00 | unchanged |

**Tests:** table interpolation and cap, non-linear table, unchanged SIMPLE
formula without a table, emergence base and cap, emergence days added before
t_sum, capped table lengthens hot seasons, barley loaded with the report values,
crop counts.

### ECOCROP crops

Decided 2026-11-12 (plan `docs/drafts/plan_ecocrop_urun_artirma.md`, K1-a … K5-a).
Code: `engine.ecocrop_temperature_score`, `crops.Ecocrop`; data
`data/crop_phenology.yaml` (`ecocrop` blocks); values in `docs/DATA_SOURCES.md` §5.
Used only for crops without literature values (11 crops).

| Step | Definition | Type |
|---|---|---|
| Season length | FAO-56 Table 11 (median-length row), as for other crops without t_sum; ECOCROP cycle is shown, not used | data |
| Temperature score | season split into ~30-day blocks from sowing; each block mean temperature → trapezoid(TMIN, TOPMN, TOPMX, TMAX); season score = **worst block** (ECOCROP model in `dismo`, monthly means; 30-day blocks are our **assumption**) | method |
| Killing temperature | ECOCROP "killing temp. early growth" stored as `lethal_min`: reported as frost-risk days only, not scored (**assumption**, K2-a) | rule |
| Water, duration, light | as for every crop (FAO-56 Kc × ET0; ECOCROP rainfall ranges are not used, to avoid double counting) | physics |
| Confidence | always "low", reason `ecocrop_general_ranges` | rule |
| Analogies (**assumption**, K3-a) | chickpea: FAO-56 lentil stage rows; cereal rye: barley/oats/wheat stage rows and the barley Kc, height, root depth and p | rule |

**Effect at the demo points** (POWER, local calendar where GGCMI has one):

| Point | ECOCROP crops, best window | Rotations |
|---|---|---|
| Konya, rainfed | all < 0.17 (water) | unchanged |
| Konya, full irrigation | chickpea 05-16 1.00, faba bean 06-01 1.00, sweet potato 0.997, sesame 0.96 | new top 3 with chickpea, faba bean (07-01) + barley, safflower, sweet potato (0.646–0.649; before 0.639) |
| Punjab, rainfed | cowpea 06-16 0.69, safflower 0.48, sesame 0.39 | cowpea → millet 0.634 first (before soybean → millet 0.618) |
| Punjab, full irrigation | cowpea 07-16 0.99, safflower, sesame 0.90, cereal rye 11-01 0.85, oats 11-01 0.78 | cowpea enters two of three cards (0.716) |
| Nakuru, rainfed | flax, chickpea, dry pea, oats ~0.76–0.79 | pulse double crops with sweet potato / sugar beet (0.72–0.73; before 0.690) |

**Vegetables and pulses (added 2026-11-13, 15 crops, group `vegetable`; green
and mung bean `legume`):** FAO-56 Kc / height / root / p from the extracted
Tables 12 and 22, stages from Table 11, temperature from ECOCROP. Best windows
(full irrigation): Konya summer vegetables (cucumber, watermelon, pepper,
pumpkin ≥ 0.99; tomato 0.71); Punjab winter vegetables (onion 10-16 0.995,
lettuce 11-16 1.00, carrot 0.84, cabbage 0.76) and rainfed mung bean 06-16
(0.74), watermelon (0.75); Nakuru rainfed long-rain vegetables 0.57–0.90. Rotations:
Konya rainfed +0.009 (spinach / radish after lentil), Punjab rainfed mung bean →
millet first (0.639); Konya and Nakuru irrigated / Nakuru rainfed totals **lower**
than before (0.643 vs 0.649, 0.739 vs 0.758, 0.681 vs 0.726) because of the pruned
search; the two-stage search of 2026-11-14 finds 0.697, 0.772 and 0.727 (see
"Rotation engine", Search).

**Cut forage (added 2026-11-14, plan `docs/drafts/plan_veri_eksik_urunler.md`):**
Sudan grass (ECOCROP 9970, FAO-56 row "Sudan, 1st cutting cycle", 75 d) and
berseem clover (ECOCROP 10522; **analogy**: FAO-56 "Alfalfa 1st cutting cycle",
60 d) are evaluated from sowing to the **first cut only** (**assumption**,
labelled). Because their real field occupancy (several cuts over months) is
not modelled, they are **not used in recommended rotations** (`first_cut_only`;
the rotation page names them). Without this rule berseem and Sudan grass, as
cheap 60–75-day crops with forage and nitrogen credit, entered every
recommended rotation at the demo points (e.g. Konya rainfed barley → berseem
0.629, although berseem's own season score there is 0.24). Best windows
(first cut): Punjab full irrigation berseem 10-16 and Sudan grass 09-01 (1.00),
rainfed Sudan grass 07-01 (0.73); Nakuru rainfed berseem 07-01 (0.87).

Limits seen: ECOCROP ranges are wide, so summer sowings of cool-season
pulses at irrigated Konya score 1.0 (agronomically doubtful); at Punjab the
GGCMI calendar puts dry pea in May and irrigated sugar beet in February, where
the score is 0 (the out-of-calendar windows 11-16 and 10-16 score 1.00 / 0.81).

**Tests:** trapezoid at block means, worst block, single hot day smoothed,
fixed season in the engine, low confidence with reason, 11 crops loaded and
literature crops unchanged, labelled analogies, crop count 26.

### Season validation (MODIS)

Decided 2026-11-12 (plan `docs/drafts/plan_ndvi_dogrulama.md`, K1-a … K4-a).
Code: `app/validation/seasons.py`; table: `scripts/validate_seasons.py`
(offline, demo cache). A **diagnostic**: no score or season is changed.

| Step | Definition | Type |
|---|---|---|
| Satellite season | MODIS MCD12Q2 v6.1, 500 m pixel at the point, up to two cycles per year: `MidGreenup` / `MidGreendown` = 50 % of the EVI2 amplitude, `Peak` = maximum (product definitions); cycles with `QA_Overall` 3 ("Poor") dropped (**assumption**) | observation |
| Model season | engine season sown at the local GGCMI planting day (nearest 1st/16th), every year; mid-season centre from the FAO-56 Table 11 proportions | physics |
| Matching | the cycle whose peak lies between sowing and maturity + 45 days; two candidates → larger amplitude (**assumption**) | rule |
| Measures | median and IQR of (model maturity − MidGreendown) and (model mid-season − Peak) in days; Spearman correlation of the maturity and green-down day of year when ≥ 8 years match (**assumption**) | stat |
| Cross-check | the same 50 % rule on MOD13Q1 NDVI (1 km mean) | stat |

Reading the numbers: the green-down midpoint is not physiological maturity, so
a constant offset of a few weeks is expected; large offsets and the
year-to-year correlation matter. The pixel holds a mix of fields and the crop
is unknown: a row is meaningful only where the crop's GGCMI season coincides
with a cycle the satellite actually sees. Season length does not depend on
irrigation in the model, so rainfed runs are used.

**Result at the demo points** (days; positive = model later; full table from the script):

| Point | Satellite cycles (median day: MidGreenup / Peak / MidGreendown) | Crop (GGCMI sowing) | Maturity − green-down (IQR) | Mid − peak | NDVI check | Spearman |
|---|---|---|---|---|---|---|
| Punjab | wheat season 12 / 47 / 89; rice season 202 / 246 / 288 | rice (07-01) | **0** (−3…+6) | 0 | −2 | 0.24 |
| | | winter wheat (11-01) | **−20** (−22…−17) | −3 | −25 | **0.60** |
| | | spring wheat (12-01) | +6 (+4…+8) | −7 | 0 | 0.60 |
| | | barley (11-01) | −48 (−50…−43) | −50 | −36 | 0.56 |
| Konya (Çumra) | one summer cycle 168 / 214 / 260 | maize (05-01) | +20 (+7…+29) | +5 | +12 | 0.39 |
| | | sorghum (06-01) | +7 (0…+16) | +11 | 0 | 0.72 |
| | | sunflower (05-01) | −18 (−35…+29) | −17 | −17 | −0.13 |
| | | winter wheat, barley | **not validatable**: no winter–spring cycle in this pixel | | | |
| Nakuru | main cycle 121 / 160 / 209 (19 years); Oct–Jan cycle in 4 years | sunflower (04-01) | +20 (−6…+27) | +16 | +14 | −0.27 |
| | | winter wheat (09-16), barley (10-16) | −9 / −4 (4 years) | +17 / +5 | 0 / −1 | — |
| | | maize (10-16) | inconclusive (8 of 24 years match, IQR −89…+73) | | | |

Findings: at Punjab the rice season matches the satellite to within a few
days, and the wheat season ends about **three weeks early** with the
spring-type SIMPLE cultivar (winter wheat), while its year-to-year timing
follows the satellite (ρ 0.60). Barley (spring-barley calibration) ends ~7
weeks early there. At Konya the pixel is dominated by irrigated summer crops;
winter cereals cannot be checked at this point. MCD12Q2 and our NDVI rule agree
within ~5 days where the cycle is clear.

**Tests:** date conversion and QA filter, cycle matching window and amplitude
rule, 50 % crossings on a synthetic curve, flat curve, nearest sowing date,
offsets on a synthetic climate, demo cache contents.

### Kc climate adjustment (FAO-56 eq. 62 / 65)

Decided 2026-11-12 (plan `docs/drafts/plan_kc_iklim_duzeltmesi.md`, K1-a, K2-a).
Code: `app/features/kc_climate.py`, used in `engine.season_rows`. Sources:
`docs/DATA_SOURCES.md` §9.

| Step | Definition | Type |
|---|---|---|
| Daily RHmin | RHmin = 100 e°(Tdew) / e°(Tmax) (eq. 63), Tdew = NASA POWER `T2MDEW`, capped at 100 % | physics |
| Stage means | For every season (year × sowing date) the mean daily u2 (`WS2M`) and RHmin over the mid-season and over the late season; stage days from the Table 11 proportions of that season's length (as in the Kc curve) | physics |
| Kc_mid | Kc_mid(Tab) + [0.04 (u2 − 2) − 0.004 (RHmin − 45)] (h/3)^0.3 (eq. 62) | physics |
| Kc_end | Same with late-season means (eq. 65), **only when Kc_end(Tab) > 0.45** | physics |
| Crop height h | FAO-56 Table 12 `max_height_m`; no adjustment when h is unknown or < 0.1 m | data |

**Assumptions (labelled):**
- Stage means outside the FAO-56 validity limits are clipped to them
  (1–6 m/s, 20–80 % RHmin; h ≤ 10 m).
- One h for both stages (FAO-56: "generally, a single value for h is used").
- Tabulated ranges use the midpoint, as everywhere else (K2-a): maize and
  cowpea Kc_end 0.35–0.60 → 0.475 > 0.45, so they are adjusted.
- Kc_ini is not adjusted (it depends on wetting frequency, FAO-56 Annex 7).
- POWER is a ~50 km cell: regional, not field humidity and wind.
- Scenario sliders keep the observed RHmin (constant-RH assumption, as for ET0).
- Bare-soil gaps (fallow) are unaffected: with h = 0 the eq. 72 climate term is 0.

Why RHmin from the dew point and not from RH2M: POWER has no daily RHmin.
Computing it from the daily mean RH (eq. 19) gives 4–7 points more humid
values at all three demo points (FAO-56 Example 5 shows the same bias); Tmin
instead of Tdew (eq. 64) is far too humid in dry months.

**Tests:** FAO-56 Example 27 (maize, Taipei 1.07 / Mocha 1.30), the standard
climate leaves the table value, Kc_end ≤ 0.45 unchanged, validity limits,
eq. 63, stage means use the right days, engine end-to-end, scenario keeps RHmin.

**Effect at the demo points** (POWER rain, rainfed, local calendar; best window):

| Point | Kc_mid (table → adjusted) | Season ETc | Best-window score |
|---|---|---|---|
| Konya (dry summer) | wheat 1.15 → 1.16, maize 1.20 → 1.30, sunflower 1.08 → 1.15 | maize 873 → 947 mm, wheat 476 → 477 mm | −0.001 … −0.007 |
| Punjab (humid monsoon) | monsoon crops −0.01 … −0.04 (maize 1.20 → 1.16), winter wheat 1.15 → 1.20 | sorghum 511 → 493 mm | −0.004 … +0.010 |
| Nakuru (humid, calm) | −0.001 … −0.04 (millet 1.00 → 0.96), maize 1.20 → 1.22 | sunflower 391 → 379 mm | −0.009 … +0.013 |

Best sowing dates change only for Nakuru potato (04-16 → 05-01, near tie).
Rotations: Konya and Punjab keep the same recommendations and order (totals
change by ≤ 0.003; wheat → fallow 0.459 → 0.457). At Nakuru millet → lentil
moves to first place (0.688 → 0.690), the sunflower double-crop cards shift
their second-season sowing dates, and potato → lentil + winter wheat drops out
of the top three. Earlier figures in this document were computed before this
adjustment and differ by these small amounts.

### Confidence

- Stage 1 never reports "high": the only climate input is a ~50 km grid.
- The level is lowered to "low" by: missing heat thresholds, a large gap
  between median and bad year (> 0.3), or failure in > 30 % of years.
- Every "low" result is marked `needs_local_validation` and comes with
  concrete questions (irrigation, frost damage, heat at flowering, local
  variety season length).
- Crops without sourced temperature limits are `insufficient_data`: the
  model does not guess. A crop needs t_base plus either t_sum (thermal-time
  season) or a growth optimum t_opt (fixed FAO-56 season); t_opt is optional
  when t_sum is known.

## Known limitations (stage 1)

- **Coarse climate.** POWER is ~0.5°; rainfall in particular may differ from
  the field. Stage 3 compares it with GPM IMERG (0.1°), see below: POWER is
  ~24 % wetter than IMERG at Konya, and its rainfall trends at Punjab and
  Nakuru are not confirmed by IMERG. Suitability uses POWER rainfall by default; IMERG and
  CHIRPS are options. At Konya POWER is 1.6 x a nearby rain gauge and 1.8 x CHIRPS, so
  the app warns there (see "POWER rain check (CHIRPS)").
- **One reference cultivar per crop.** SIMPLE t_sum values come from one or a
  few cultivars. Local varieties can be much shorter or longer (e.g. dry bean
  is "not suitable by model" in the Kenyan highlands, which is likely a
  cultivar mismatch).
- **Not modelled yet:** vernalisation and photoperiod (winter wheat; the local
  sowing calendar stands in for them, see above; our winter-wheat parameters
  come from a spring-type cultivar, DATA_SOURCES §8), frost
  kill (frost days are reported and turned into questions), sowing-moisture
  rules, waterlogging, soil water storage between 10-day blocks inside a season (between crops it is
  modelled, see "Soil water between crops"), and soil (stage 3).
- **Temperature limits for 43 of 50 crops**: 15 from literature (10 with heat
  thresholds; sorghum, millet, lentil, sunflower and barley have none) and 28
  from FAO ECOCROP general ranges (see "ECOCROP crops"). Still without data:
  rapeseed, mustard, ryegrass (no season length), buckwheat, vetch, phacelia
  (no Kc); alfalfa (perennial).
- **Cut forage** (Sudan grass, berseem clover) is modelled only from sowing to
  the first cut; regrowth cuts are not, so these crops are shown in the crop
  list but not used in recommended rotations.
- **Rotation search is a heuristic.** Only the 150 best year options (by
  their own score) are combined and only the 300 best cycles without soil
  water carry-over are scored in full (see "Rotation engine", Search). At the
  demo points this gives the same top 3 as a 10× wider search in 24 of 24
  checked cases; a cycle that gains very much from stored soil water could
  still be missed. Rotation requests take ~3–4 s offline at the demo points.
- **SIMPLE values** are a second-hand transcription, not yet checked against
  the original paper (not openly accessible; DATA_SOURCES §5).
- **Season length checked against MODIS only at a few points.** At Punjab the
  wheat season ends ~3 weeks before the satellite green-down and barley ~7
  weeks; rice matches (see "Season validation (MODIS)"). A field record
  confirms it (Kaur et al. 2025, PAU Ludhiana 2023-24, Table 1: sowing 6 Nov /
  24 Nov / 12 Dec matured after 154 / 146 / 136 days; the model, with POWER for
  the same season, after 138 / 133 / 127 days). **Corrected 2026-11-14** with a
  regional cultivar variant (see "Regional cultivar variants"): winter wheat
  now ends 4 days before the green-down (was 20). Heat thresholds for sorghum,
  millet, lentil, sunflower and barley: no peer-reviewed SIMPLE-type source
  found (search 2026-11-14).
- **Perennials** (alfalfa) are not evaluated until the rotation engine (stage 4).

## Rotation engine (stage 4) — rules, no ML

`POST /api/rotations` takes the point, irrigation, six priority weights
(0–5), constraints (excluded crops, equipment limits, crops with a market)
and optionally the current rotation. Inputs are used for the request only.

**Building blocks.** A *slot* is one crop in one sowing window from the
suitability results. Crops are used only if their best window scores at
least max(0.2, 0.5 × the best crop here). A *year* holds one slot, two
slots whose seasons do not overlap and whose families differ (double
cropping), or nothing (a **fallow** year, at most one per cycle).

**Search** (two stages, `app/rotation/search.py`; decided 2026-11-14, plan
`docs/drafts/plan_rotasyon_arama.md`):

1. *Screen.* Every year option (single crop or double crop) gets its own
   total with the rotation score below, without the soil water carried
   between crops; the 150 best options (`MAX_PLANS`) are combined into every
   2- and 3-year cycle that keeps the hard rules (up to ~10 million cycles).
   Without carry-over every sub-score is a ratio of per-year sums, so all
   cycles are scored with numpy in well under a second; the screen total
   equals the rotation score without carry-over (unit test, ±0.002 from rounding).
2. *Exact scoring.* The 300 best screened cycles (`N_CANDIDATES`, at most 3
   with the same crop set) are scored with the full score, including the
   soil water carried between crops, and the three best that differ by a
   crop-set Jaccard distance ≥ 0.5 are shown.

Both cuts are heuristics (**assumption**). Check at the 3 demo points ×
rainfed / full irrigation × 4 priority profiles (default; water 5;
nitrogen 5 + forage 5; soil 5 + erosion 5 + water 0): the shown top 3 are
identical to those of a 10× wider search (all year options, 3000 exact
candidates) in 24 of 24 cases. Carried soil water raised a candidate's total
by 0 to 0.113 over its screen total (median 0.011), so a cycle with a very
large carry-over could still be missed.

Before / after at the demo points (`scripts/bench_rotations.py`, offline demo
cache, default priorities, fastest of 3 runs on the development laptop):

| Point | Water | Best total before → after | Search time, s | Request time, s |
|---|---|---|---|---|
| Konya | rainfed | 0.521 → 0.521 | 0.12 → 0.07 | 3.1 → 3.0 |
| Konya | full | 0.643 → **0.697** | 5.63 → 0.58 | 8.6 → 3.5 |
| Punjab | rainfed | 0.639 → 0.639 | 1.09 → 0.33 | 4.1 → 3.3 |
| Punjab | full | 0.719 → **0.724** | 4.36 → 0.57 | 7.4 → 3.6 |
| Nakuru | rainfed | 0.681 → **0.727** | 3.23 → 0.62 | 6.3 → 3.7 |
| Nakuru | full | 0.739 → **0.772** | 2.88 → 0.71 | 5.9 → 3.6 |

The second and third cards improved as well (e.g. Nakuru full irrigation
0.691 / 0.682 → 0.770 / 0.768). The rest of a request (~3 s) is the
suitability run of all 50 crops. Before, the search used only the 30 year
options with the best crop scores (`PLAN_POOL`), which missed good double crops.

**Hard rules** (the user's current rotation is scored anyway, with broken
rules listed): no two consecutive slots of the same family, also across the
cycle boundary and inside a double-cropped year (breaks pest/disease cycles);
no crop in consecutive years; a fallow year breaks both sequences; excluded
crops and crops needing missing equipment (root harvester → root/tuber
crops, paddy → rice) are not used.

**Sub-scores (0–1).**

| Sub-score | Definition | Type |
|---|---|---|
| Productivity | Σ normal-year season scores / years (fallow = 0, double cropping capped at 1); a crop's season score includes the water stored before it | physics + rules |
| Bad-year resilience | mean 20th-percentile season score | statistics |
| Water | 1 − rain deficit / crop water use (FAO-56 ETc); soil water stored in the gap before a crop (e.g. a fallow year) covers its deficit first, see "Soil water between crops" | physics |
| Soil health | **proxy**: 0.5 × root depth (FAO-56 Table 22, full credit at 1.5 m) + 0.5 × share of months with living roots | rule (proxy) |
| Erosion | 1 − bare share of months (weighted by heavy-rain days per month, R95p) × relative RUSLE slope factor S/S(9 %) from NASADEM (stage 3; factor 1 when slope is unavailable) | rule |
| Nitrogen | 0.6 × share of years with a legume + 0.4 × share of cereal slots that follow a legume | rule |
| Income | share of slots with a crop the user marked as having a market; **unknown** without input (no prices are invented) | user input |
| Forage | share of slots with a forage crop | rule |
| Family diversity | distinct families / slots | rule |

Total = weighted mean over known sub-scores: user weights for water, soil,
erosion, nitrogen, income and forage; fixed weights 3 (productivity),
3 (bad-year resilience) and 1 (diversity).

**Cards** list, from these numbers only: why (strongest weighted
sub-scores), benefits, risks (broken rules, water deficit, frequent failure,
bare-soil periods), data gaps (soil proxy, no market data, slope is the
surrounding cell or unavailable, soil water between crops is a model —
or not modelled when SoilGrids is unavailable — unmodelled crops),
the water stored in a fallow year, cover-crop
opportunities in bare periods ≥ 2 months (cover crops themselves are not
modelled yet), confidence (the lowest of its crops) and questions for a
local expert.

**Explanations.** By default the app writes a template sentence from the
card's codes. Optionally (`explain: "llm"` and an API key on the server)
Claude rewrites the card facts into plain language; it receives no
coordinates and is told to add nothing that is not in the facts. Without
credentials, or on any error or refusal, the template is used.

### Easy mode (2026-11-14, plan `docs/drafts/plan_kolay_mod.md`)

The easy mode calls `/api/rotations` automatically with default priorities (all 3)
and no constraints, and writes the first recommended card as a plan: per slot the
best sowing date, median harvest, and the median season rain deficit after stored
soil water (1 mm = 1 t of water per decare, a unit conversion). Display rules (not
model parameters): a deficit below 10 mm is shown as "rain is usually enough";
idle periods of ≥ 2 months are listed with grazing / cover crop as an *option* to
check locally (not modelled). Tillage dates and irrigation schedules are not
modelled and not shown. On flat terrain (`slope.flat_terrain`) the erosion priority
weight is set to 0 for every request (`erosion_ignored_flat_terrain`), since the
RUSLE slope factor there is ~0.05.

### Irrigation interval, field corners and row direction (2026-11-14)

**Irrigation interval** (`app/water/irrigation.py`, FAO-56 ch. 8): for each crop of a
rotation card, in its mid-season (FAO-56 Table 11 proportions of the modelled season):
TAW = 1000 (θFC − θWP) Zr (eq. 82, SoilGrids, Table 22 root depth), p = p_table +
0.04 (5 − ETc) limited to 0.1–0.8 (Table 22 footnote), RAW = p TAW (eq. 83), ETc =
Kc_mid (climate-adjusted) × mean daily ET0 of those months (POWER). Interval = RAW / ETc
days, depth = RAW (net mm). **Assumptions:** a dry spell (rain lengthens the interval;
the mean daily rain is reported and the plan says when it usually covers ETc), full
root depth in the mid-season, no application losses. When the interval is longer than
the mid-season the plan says "one irrigation of RAW if the period stays dry".

**Field corners** (browser only, `frontend/src/field.ts`): the user taps ≥ 3 corners;
area by the shoelace formula on a local equirectangular projection (decares); the
centroid becomes the selected point. Water per field = mm × decares (1 mm = 1 t/da).

**Row direction** (`terrain.fall_direction`): a plane z = c0 + cx·east + cy·north is
fitted to NASADEM over the 0.05° cell (Earth Engine `linearRegression`); the downhill
azimuth is atan2(−cx, −cy) and rows are advised **across the slope** (contour
farming, a support practice that reduces soil loss: Renard et al. 1997, USDA
Agriculture Handbook 703, ch. 6). Only where the slope is resolved (not
`flat_terrain`); the cell's main slope, not the field's (**assumption**, stated in the
plan). Demo: Nakuru falls to the south-west (229°, 2.0 %), rows NW–SE — consistent
with Lake Nakuru lying south-west of the point; Konya and Punjab are flat, no advice.
No advice is given from sun angle: studies disagree (east–west rows better for wheat
and barley in Western Australia, Borger et al. 2010, Weed Science 58(2), doi:10.1614/WS-09-094.1; north–south
slightly better in Punjab, J. Agric. Sci.).

## Soil water between crops — fallow (physics, FAO-56)

Decided 2026-11-11/12 (plan `docs/drafts/plan_nadas_ortu_bitkisi.md`,
options K1-A, K2, K3-b). Code: `app/water/fao56_soil.py`,
`app/rotation/water_carry.py`, `app/sources/soilgrids.py`. Sources:
`docs/DATA_SOURCES.md` §3b and §7.

For every crop that follows another crop in a rotation, and every year of the
record, the gap from the previous harvest to this sowing is simulated day by
day. A fallow year is simply a long gap (K2: every gap, not only fallow).

| Step | Definition | Type |
|---|---|---|
| Gap | From the day after crop A's season ends (per year, thermal time) to the first sowing date of crop B after it, plus one year per fallow year in between | rule |
| Topsoil | FAO-56 ch. 7 eq. 71, 73–79 with Kcb = 0 and Kc max = 1.20 (eq. 72, h = 0), as prescribed for bare soil in non-growing periods (ch. 11); evaporation layer Ze = 0.10 m | physics |
| Root zone | FAO-56 ch. 8 eq. 85, 86, 88 over crop B's FAO-56 Table 22 root depth | physics |
| Soil | TAW = 1000 (θFC − θWP) Zr (eq. 82) and TEW (eq. 73) from SoilGrids wv0033 / wv1500, median of 250 m pixels within 1 km | physics |
| Use | The water stored at B's sowing (TAW − Dr) covers B's 10-day rain deficits first; irrigation then covers the rest (K1-A). B's season score, bad-year score and failure rate are recomputed per year | physics |

**Assumptions (labelled in the card):**
- θFC = water content at 33 kPa, θWP = at 1500 kPa (FAO-56 gives no suction).
- REW = 9 mm (FAO-56 Table 19 has no clay-loam row; neighbouring classes 8–12 mm), at most TEW.
- The profile is empty at A's harvest (Dr = TAW, De = TEW).
- No runoff (RO = 0), no weeds or volunteer plants, no stubble/mulch effect,
  no separate treatment of frozen soil or snow; rain falls early in the day
  (FAO-56 Example 35); transpiration from the evaporation layer Tew = 0.
- Within B's season the 10-day block method is unchanged: surplus rain inside
  the season is still not stored (K1-A). A full daily root-zone balance for
  every crop (option B) would change every water score and is left for later.
- Years at the edges of the record without a predecessor count as "no stored water".
- A year that is empty because the user's crop cannot be modelled is not a
  fallow year: nothing is carried across it.

**Tests:** FAO-56 Example 31 (bare loam, day-by-day De and Kr) and Example 35
(dual Kc with irrigation and rain; the printed E of day 3 contradicts its own
Ke × ETo and is checked as Ke × ETo), vectorised kernel = scalar reference,
mass balance (rain = evaporation + transpiration + drainage + storage), bounds,
Konya fallow efficiency inside 10–35 %, unchanged scores without soil data.

**Results at the demo points** (POWER rain, rainfed, 2001–2025):

| Point | Transition | Stored at sowing (median) | Next crop's median score |
|---|---|---|---|
| Konya | winter wheat → fallow → winter wheat (≈ 15.5 months) | 133 mm, **22 %** of the gap rain (IMERG: 132 mm, 23 %) | 0.38 → 0.60 (IMERG 0.36 → 0.56) |
| Konya | winter wheat → winter wheat (summer gap) | ≈ 0 mm | unchanged |
| Konya | winter wheat → lentil | 64 mm | 0.25 → 0.33 |
| Punjab | soybean → millet, sorghum → soybean, soybean → maize | 20–70 mm | +0.05 … +0.13 |
| Nakuru | millet → millet, lentil → spring wheat | 117–142 mm | about +0.2 (e.g. millet 0.80 → 0.99) |

Plausibility (not a model input): Janssen (1972) found fallow efficiencies of
14–33 % in the Great Konya Basin; the model gives 22 %. **Discrepancy:** with
POWER rain the model drains about 107 mm below the root zone during the fallow,
while Janssen observed no deep percolation. With IMERG rain this drops to about
18 mm, which again points to POWER rain being too high at Konya (stage 3). In
dry years (IMERG, 20th percentile) only 71 mm is stored.

Konya recommendations (with the local sowing calendar): wheat → lentil stays
first; wheat → fallow (total 0.459) and lentil → fallow are now among the
three shown.

At Nakuru (humid, two rainy seasons) every gap refills the profile, so all
water scores rise; the ranking changes little because all crops gain. The
"profile empty at harvest" assumption limits, but does not remove, this effect.

**Cover crops** stay unmodelled (K3-b). The gap balance already accepts a
cover-crop Kcb curve (fc from eq. 76, Ks from eq. 84), but no cover crop has a
sourced Kc curve, stage lengths and temperature limits yet (cereal rye: Kc in
Pereira et al. 2021 Table 13 rests on "non-cited material"; vetch, mustard,
phacelia: nothing found). Rules for later, so that nothing is counted twice:
the cover crop's water use only lowers the next crop's stored water; its
months count as covered (erosion) and as living roots (soil proxy), but not in
root depth, production, income, forage or diversity; it takes part in the
family rule.

## Stage 3 — satellite layers, harmonisation, pattern comparison

`GET /api/satellite?lat=&lon=` is separate from `/api/analyze`: a first live
Earth Engine extraction for a new point takes 10–30 s. Results are cached per
rounded point; the demo points are also in `demo_cache/`.

### Harmonisation

| Step | Rule | Type |
|---|---|---|
| Space | No resampling. Every layer is sampled at the rounded analysis point with its native footprint, which is reported: POWER ~0.5°, IMERG 0.1°, SMAP 9 km, NDVI mean of 250 m pixels within 1 km, slope over the 0.05° cell | rule |
| Time | Calendar months: sums for precipitation, means for NDVI and soil moisture | stat |
| NDVI | MOD13Q1 16-day composites, `SummaryQA` ≤ 1; a composite counts at its mid-date (+8 days); dropped if it has < 50 % of the valid pixels of the best composite (**assumption**) | rule |
| SMAP | `retrieval_qual_flag_am` == 0 only; a month needs ≥ 5 valid days (**assumption**; revisit is 2–3 days) | rule |
| SMAP 005 + 006 | 006 (reprocessed, now 2015 to present) is the primary series; days with no passing 006 retrieval are filled from 005 minus the mean 006−005 offset over days where both pass. With < 30 overlap days no offset is applied and this is reported | stat |
| IMERG | monthly mean rate (mm/h) × hours in the month = mm/month | unit conversion |

SMAP measures the top ~5 cm; POWER `GWETROOT` is a modelled root-zone index.
They are shown side by side as different quantities, never merged.

### POWER vs IMERG rainfall

Only complete years present in both (2001–2024; the monthly IMERG product
ends 2025-09). Reported: annual means and relative difference ("agree" < 15 %,
"large" > 30 %, **assumption**), Pearson r of annual and monthly totals,
Mann-Kendall / Sen trends of both, and a **homogeneity check**: Mann-Kendall
and the Pettitt (1979) change-point test on the annual POWER − IMERG
difference. A POWER trend counts as *confirmed* only if IMERG has the same
direction and significance and the difference series is homogeneous.

Results for the demo points (2026-11-11):

| Point | POWER mm/yr | IMERG mm/yr | r (annual) | POWER trend /10 yr | IMERG trend /10 yr | Difference series |
|---|---|---|---|---|---|---|
| Konya | 560 | 453 (POWER +24 %) | 0.78 | −42 (n.s.) | −20 (n.s.) | homogeneous |
| Punjab | 715 | 637 (+12 %) | 0.66 | **+239 (p < 0.001)** | +51 (n.s.) | step after 2013 (p = 0.0004): POWER/IMERG 0.92 to 1.36 |
| Nakuru | 1260 | 1275 (−1 %) | 0.79 | **+357 (p < 0.001)** | +101 (n.s.) | step after 2014 (p = 0.0006): 0.83 to 1.19 |

(The POWER means differ slightly from `/api/analyze`, which averages 2001–2025.)

Reading: at Konya POWER is consistently wetter than IMERG (mostly Nov–Feb),
so the suitability water scores there may be optimistic, but without gauge
data we cannot say which source is right. At Punjab and Nakuru the strong
POWER rainfall trends coincide with a step in the POWER − IMERG difference;
they are most likely an artefact of the POWER (MERRA-2 corrected)
precipitation record rather than a climate signal, and the UI says so. We do
not claim a cause for the step.

### POWER rain check (CHIRPS)

Decided 2026-11-14 (plan `docs/drafts/plan_konya_yagis.md`, K1-a, K2 = 30 %, K3-a).
Code: `app/harmonize/rainfall.py` (`rescale_to_monthly`, `rain_check`),
`app/sources/gee.py` (`chirps` layer, `load_layer`); sources in `docs/DATA_SOURCES.md` §4.

| Step | Definition | Type |
|---|---|---|
| CHIRPS monthly | CHIRPS v2.0 daily rain summed to calendar months at the 0.05° pixel (Earth Engine) | observation (satellite + gauges) |
| Rain check | mean annual POWER vs CHIRPS over the complete years in both; `power_may_be_too_wet` when POWER / CHIRPS > 1.3 (**assumption**: the existing "large difference" limit); shown as a warning in the UI only when POWER is the rain source | rule |
| `precip_source=chirps` | each month's daily POWER rain × CHIRPS month / POWER month (same rule as IMERG, **assumption**) | rule |

Why: at Konya the only independent check is the GHCN-Daily gauge KONYA
(45 km, 59 complete months 2001–2024): POWER 1.63 ×, IMERG 1.39 ×, CHIRPS
0.98 × the gauge total, mostly Oct–Feb. CHIRPS may include this gauge (not
independent) and gauges under-catch snow. At Punjab the nearest gauges with
recent data (Ludhiana, 33 km) have no complete month since 2001, so no gauge
check was possible there; Nakuru's nearest gauge is 125 km away.

**Result at the demo points (2001–2025):**

| Point | POWER mm/yr | CHIRPS mm/yr | Ratio | Warning |
|---|---|---|---|---|
| Konya | 551 | 306 | 1.80 | yes |
| Punjab | 733 | 637 | 1.15 | no |
| Nakuru | 1283 | 1149 | 1.12 | no |

With `precip_source=chirps` at Konya (rainfed): winter wheat 0.38 → 0.32,
barley 0.48 → 0.40, lentil 0.25 → 0.22 (same order); recommended rotations
0.521 → 0.489. Punjab and Nakuru change by a few hundredths.

**Tests:** monthly totals and daily pattern after rescaling, IMERG keys kept,
rain-check limit (wet / not wet), incomplete years, demo cache CHIRPS layer,
API end to end (warning at Konya, none at Punjab; chirps source in analyze and rotations).

### Slope (erosion)

NASADEM 30 m slope, median over the 0.05° analysis cell, converted to the
RUSLE slope steepness factor S (McCool et al. 1987, as given in USDA
Agriculture Handbook 703, ch. 4, p. 107, eq. 4-4 / 4-5) and divided by S at
the 9 % unit-plot slope (≈ 1.0). Erosion sub-score =
1 − bare_weighted_share × S/S(9 %). Limitations: a ~5 km cell median,
not the field; slope length (L) and soil erodibility (K) are not used.

**Flat-terrain rule (2026-11-14, assumption).** NASADEM heights are whole
metres, so the smallest non-zero 30 m slope is one 1 m step across two pixels,
atan(1 / 61.7 m) = 0.93° — exactly the 10th-percentile slope at all three demo
points. When the median pixel slope is at most two such steps (≤ 1.86°), the
DEM does not resolve the slope (rounding and noise dominate) and the cell-scale
gradient is used instead: 10–90 % elevation range / half the cell (2.78 km).
Demo points: Konya 2.6 % → **0.2 %** (5 m range; S/S9 0.31 → 0.05), Punjab
3.2 % → **0.2 %** (5 m; 0.38 → 0.05), Nakuru 4.6 % unchanged (0.52; 86 m range).
Before, the plains got a spurious slope from height rounding, which overstated
erosion on bare soil there. Best rotation totals: Konya rainfed 0.521 → 0.525,
Punjab rainfed 0.639 → 0.655, Punjab full irrigation 0.736 → 0.741 (watermelon +
lentil → sorghum + dry pea); Nakuru unchanged.

### Pattern finding: three approaches on the same data

Year table: one row per calendar year with the 12 monthly NDVI means (gaps
≤ 2 months filled by circular linear interpolation, otherwise the year is
dropped) and POWER annual precipitation, mean temperature, ET0, hot and frost
days.

| | Approach | What it does | Type |
|---|---|---|---|
| A | z-score / threshold | Years whose NDVI integral (sum of monthly means) or peak deviates ≥ 1.5 SD (**assumption**) | stat |
| B1 | k-means on NDVI curves | k = 2…4, best silhouette; < 0.25 reported as "no clear structure" (**assumption**). With k = 2 a Pettitt test on the label sequence detects a regime shift (clusters ordered in time) | ml |
| B2 | Isolation Forest | 500 trees, `contamination="auto"`, fixed seed; features = z-scored NDVI curve + climate; flagged where the decision score < 0 | ml |
| C | Analog years | 3 nearest years in z-scored climate space; leave-one-out skill of predicting the NDVI integral vs climatology: skill = 1 − MAE_analog / MAE_climatology | stat |

Results for the demo points:

| Point | A: z-score | B2: Isolation Forest | A/B2 Jaccard | B1: k-means | C: analog skill |
|---|---|---|---|---|---|
| Konya | 2001, 2006, 2007, 2020 | 2009, 2010, 2011, 2013, 2024, 2025 | 0.0 | k = 2, silhouette 0.40; **regime shift after 2015** (June peak, two seasons, to August peak, one season) | −0.04 (none) |
| Punjab | 2001, 2002, 2009, 2022, 2024 | 2002, 2023, 2025 | 0.14 | k = 2, silhouette 0.25, mixed in time | 0.23 |
| Nakuru | 2008, 2009, 2010, 2017 | 2005, 2009, 2015, 2017, 2018, 2020 | 0.25 | no clear structure (0.21) | 0.22 |

What the comparison shows:

- **A and B2 answer different questions.** z-scores flag years with an
  unusual NDVI *level* (e.g. low greenness at Konya in 2006–2007). Isolation
  Forest flags unusual *combinations* of curve shape and climate, mostly hot
  or very wet/dry years whose NDVI total was normal. They rarely agree
  (Jaccard 0–0.25). The z-score result is easier to explain; the Isolation
  Forest result is a list of "years worth a closer look".
- **k-means found the most useful pattern**: at Konya the seasonal NDVI curve
  changed after 2015 from a spring/early-summer peak to an August peak. That
  is consistent with more summer (irrigated) crops, which these data cannot
  confirm. A z-score on NDVI totals does not see it.
- **Analog years** work only where vegetation follows climate (Punjab,
  Nakuru: ~22 % better than climatology). At Konya they have no skill, which
  again points to management rather than weather driving NDVI.
- Where POWER rainfall is not homogeneous (Punjab, Nakuru) the climate-based
  methods (B2, C) inherit the problem; the API adds a note.
- ~25 years per point is a small sample. Pattern results are shown as
  context and questions; they are not fed into the rotation scores.

## Stage 5 — risk layers, time slider, layer compare, scenario sliders

No new data sets and no new dependencies: everything uses the POWER record
and the stage 3 Earth Engine series, so the 3 demo points work offline from
`demo_cache/`.

### Rainfall source (option, default POWER)

`precip_source=imerg` (in `/api/analyze`, `/api/rotations`, `/api/risk`)
replaces POWER rainfall with GPM IMERG for the water balance. The suitability
engine needs daily rain and our IMERG product is monthly, so (**assumption**)
each month's daily POWER rain is multiplied by IMERG_month / POWER_month: the
monthly total is IMERG's, the day-to-day pattern stays POWER's. A month stays
POWER, and is counted in the response (`variant.imerg_rescale`), when IMERG
has no value (the monthly product ends 2025-09, so Oct–Dec 2025), or when POWER
has no rain in a month where IMERG has some (that IMERG rain cannot be placed
on a day; 3 months / 3 mm at Konya). POWER stays the default because IMERG is
monthly here and ends earlier. Which source is closer to the field is not
known without gauge data (stage 3).

### Scenario sliders: a sensitivity test, not a projection

`delta_t` (−2 … +4 °C) and `delta_p` (−30 … +30 %). The slider limits are
**assumptions** for the demo, not values from a climate model. This is a
"delta change" perturbation of the observed 25 years: every day gets +ΔT on
Tmax, Tmin and T2M, and its rain is multiplied by (1 + ΔP/100); ET0 is
recomputed with FAO-56 Penman-Monteith. **Assumptions:** relative humidity,
wind and radiation are unchanged (so vapour pressure rises with temperature);
the number of wet days and the day-to-day sequence do not change.
Suitability, rotation cards and the climate risk layers are recomputed. The
crop list shows each crop's best score without the scenario next to the
scenario score. SMAP and NDVI are observations and are never changed by the
sliders.

Best-window median score of the top crops (2001–2025, rainfed):

| Point | POWER (default) | IMERG rainfall | +2 °C | −20 % rain |
|---|---|---|---|---|
| Konya | winter wheat 0.38, spring wheat 0.38, lentil 0.25 | winter wheat 0.36, spring wheat 0.36, lentil 0.27 | spring wheat 0.48, winter wheat 0.38, lentil 0.29 | spring wheat 0.34, winter wheat 0.34, lentil 0.21 |
| Punjab | sorghum 0.62, soybean 0.61, millet 0.56 | sorghum 0.58, soybean 0.57, sunflower 0.54 | sorghum 0.63, soybean 0.50, millet 0.49 | soybean 0.56, sorghum 0.56, millet 0.52 |
| Nakuru | millet 0.80, sunflower 0.79, lentil 0.79 | millet 0.81, sunflower 0.81, lentil 0.80 | spring wheat 0.69, lentil 0.68, sunflower 0.67 | millet 0.73, lentil 0.73, sunflower 0.71 |

(With the light factor below; the scenario runs use the baseline season
radiation as reference.) Annual rain used: Konya 551 mm with POWER vs 448 mm
with IMERG, Punjab 733 vs 650, Nakuru 1283 vs 1279.

**Light factor — fix found with the scenario sliders.** Without it, +2 °C
*raised* the Konya wheat scores (winter wheat 0.42 → 0.47, spring wheat
0.38 → 0.51). Warming shortens the thermal-time season, which lowers its water
deficit, but the score had no cost for a shorter season: the duration factor
only bites below 75 % of the shortest FAO-56 season. That contradicts the
literature, which finds warming lowers wheat yields on average (−6.0 % per
°C of global warming, Zhao C. et al. 2017, PNAS 114(35):9326–9331,
doi:10.1073/pnas.1701762114, abstract). The cause is that crop growth is
proportional to the solar radiation the crop intercepts (radiation-use
efficiency, Monteith 1977, Phil. Trans. R. Soc. B 281:277–294,
doi:10.1098/rstb.1977.0140 — bibliographic data checked via Crossref, full text
not read; SIMPLE, Zhao et al. 2019, is built on the same principle), so a
shorter season collects less light.

Rule: light factor = min(1, R / R_ref), with R = Σ daily POWER solar radiation
(`ALLSKY_SFC_SW_DWN`) over the season and R_ref = the median R of the matured
seasons for the same sowing date in the baseline (observed) climate. In a run
without a scenario the reference is the run's own median, so the factor only
lowers years with shorter-than-usual seasons (scores fall by ≤ 0.04 at the demo
points). In a scenario run, a season that becomes shorter loses light. The cap
at 1 (a longer season gains nothing) is an **assumption**; it also keeps scores
≤ 1. Sowing dates without a matured baseline season get factor 1.

Result: at Konya +2 °C now leaves winter wheat unchanged (0.38) and lowers
the top crops at Punjab and Nakuru. Spring wheat at Konya (sown in autumn by
the model) still rises (0.38 → 0.48): its season moves away from the dry early
summer ("drought escape", less water deficit). This is a real mechanism, but
the size is uncertain: the model still has no vernalisation and heat stress
only above t_heat (34 °C for wheat). The UI calls the sliders a sensitivity
test.

### Risk layers (`GET /api/risk`, `app/risk/layers.py`)

Point time series at the analysis point (no maps): one value per layer, year
(2001–2025) and month.

| Layer | Monthly value | Threshold / source | Type | Scenario |
|---|---|---|---|---|
| Frost days | days with Tmin < 0 °C | rule (as in the climate profile) | rule | yes |
| Lethal cold days (only if a crop with a sourced value is chosen) | days with Tmin < crop lethal minimum | Luo 2011 Tables 1–2 (winter wheat −17.2 °C; barley: midpoint of −17.3 … −12.9) | rule | yes |
| Hot days | days with Tmax > threshold | crop t_heat from SIMPLE (Zhao et al. 2019) if a crop with a value is chosen; otherwise generic 35 °C (**assumption**, labelled) | rule | yes |
| Heavy-rain days | days with P > R95p of baseline wet days | ETCCDI R95p style | stat | yes |
| Water balance | P − ET0 (mm) | FAO-56 ET0; chosen rainfall source | physics | yes |
| Soil moisture | SMAP monthly mean (2015 onwards) | stage 3 harmonisation (QA, ≥ 5 days) | observation | no |
| NDVI | MOD13Q1 monthly mean | stage 3 harmonisation | observation | no |

**Anomaly.** Each month is compared with the same calendar month of the
*baseline* (the observed record with the chosen rainfall source, without the
scenario): z = (value − mean) / SD. It is oriented so that + = worse (more
frost / hot / heavy-rain days, less water, drier soil, lower NDVI) and shown
as a red–blue colour. **Assumptions:**
- a month needs at least 5 baseline years for that calendar month (`MIN_YEARS`);
- |z| ≥ 1 counts as "unusual";
- z is capped at ±3;
- when the baseline never varies (SD = 0, e.g. no frost in July), a different
  value gets ±3 ("outside the observed range").

The annual column is the sum for counts and water balance (complete years
only) and the mean for SMAP (≥ 6 months) and NDVI (≥ 8 months). It is
compared with the baseline annual values in the same way.

The lethal-cold layer uses 2 m air temperature on a ~0.5° grid, not the
temperature at the plant crown. Snow cover protects plants, so the layer
overstates risk in snowy winters; the UI says so.

**Time slider and layer compare (PWA).** A year slider picks the year for the
12-month risk table; tapping a cell shows its value, the normal and z. The
compare view puts any two layers on the same z scale: the chosen year by
month, and all years (annual z) with the chosen year marked.

Example (Konya, +2 °C, POWER rain): frost days fall from 95 to 59 per year,
hot days (> 35 °C) rise from 12 to 27, and the water balance goes from −639 to
−708 mm. In 2025 (observed) Konya had 33 hot days (annual z +2.6), a −931 mm
water balance (+1.9) and the driest SMAP year in the record (+2.5).
