"""Suitability engine on synthetic climates (no network)."""

import numpy as np
import pandas as pd
import pytest

from app.config import ROOT
from app.suitability.crops import Crop, Stages, Temperature, load_crops
from app.suitability.engine import ClimateArrays, dekad_deficit, evaluate_crop, kc_curve


def make_climate(tmean=20.0, amplitude=0.0, precip=0.0, et0=4.0, years=(2001, 2005), tmax_extra=6.0):
    dates = pd.date_range(f"{years[0]}-01-01", f"{years[1]}-12-31", freq="D")
    doy = dates.day_of_year.to_numpy()
    t = tmean + amplitude * np.sin(2 * np.pi * (doy - 105) / 365)
    n = len(dates)
    return ClimateArrays(dates, t, t + tmax_extra, t - tmax_extra, np.full(n, float(precip)),
                         np.full(n, float(et0)))


def crop(t_sum=1000.0, t_base=0.0, t_opt=15.0, t_heat=34.0, t_ext=45.0, stages_total=100,
         max_total=280):
    return Crop(
        id="test", name={"en": "Test"}, scientific="X", family="Poaceae", group="cereal",
        nitrogen_fixing=False, perennial=False, kc_ini=0.3, kc_mid=1.15, kc_end=0.25,
        root_depth_m=1.0,
        temperature=Temperature(t_base, t_opt, t_heat, t_ext, t_sum, "test", True),
        stages=Stages(20, 30, 30, 20, total=stages_total, row="test", max_total=max_total),
    )


def test_summer_crop_cannot_overwinter():
    # Continental climate: ~0 °C winters, ~24 °C summers. A warm crop sown in
    # autumn would need far longer than its longest FAO-56 season -> fails.
    clim = make_climate(tmean=12.0, amplitude=12.0, precip=5.0)
    warm = crop(t_sum=1500, t_base=10, t_opt=28, max_total=180)
    res = evaluate_crop(warm, clim)
    assert res["status"] == "evaluated"
    autumn = next(w for w in res["windows"] if w["sowing"] == "09-01")
    assert autumn["matured_share"] == 0 and autumn["score_median"] == 0
    assert res["best_window"]["season_days_median"] <= 225
    assert int(res["best_window"]["sowing"][:2]) in (3, 4, 5)
    assert res["best_window"]["sowing"] in res["good_sowing_dates"]
    assert "09-01" not in res["good_sowing_dates"]


def test_kc_curve_follows_fao56_shape():
    kc = kc_curve(100, (0.2, 0.3, 0.3, 0.2), 0.3, 1.15, 0.25)
    assert kc[0] == pytest.approx(0.3)
    assert kc[60] == pytest.approx(1.15)
    assert kc[-1] == pytest.approx(0.25, abs=0.03)
    assert np.all(np.diff(kc[:50]) >= -1e-12)


def test_dekad_deficit_lets_rain_offset_within_ten_days():
    etc = np.full(20, 2.0)
    p = np.zeros(20)
    p[0] = 20.0  # 20 mm on day 1 covers the first dekad's 20 mm demand
    assert dekad_deficit(etc, p) == pytest.approx(20.0)


def test_thermal_time_sets_season_length():
    # Tmean 20 °C, base 0 -> 20 °C·d per day -> 1000 °C·d in 50 days
    res = evaluate_crop(crop(t_sum=1000), make_climate(tmean=20.0, precip=10.0))
    w = res["best_window"]
    assert res["status"] == "evaluated"
    assert w["season_days_median"] == 50
    assert w["temperature_score_median"] == pytest.approx(1.0)
    assert w["water_score_median"] == pytest.approx(1.0)  # 10 mm/day rain > ETc


def test_dry_climate_scores_low_rainfed_and_full_with_irrigation():
    dry = make_climate(tmean=20.0, precip=0.0, et0=5.0)
    rainfed = evaluate_crop(crop(), dry, "none")
    irrigated = evaluate_crop(crop(), dry, "full")["best_window"]
    limited = evaluate_crop(crop(), dry, "limited")["best_window"]
    assert rainfed["status"] == "not_suitable_by_model"
    assert rainfed["reason"]["code"] == "water"
    assert all(w["water_score_median"] == 0 and w["rain_deficit_mm_median"] > 0
               for w in rainfed["windows"])
    assert irrigated["water_score_median"] == pytest.approx(1.0)
    assert limited["water_score_median"] == pytest.approx(0.5)


def test_too_cold_to_mature_fails():
    res = evaluate_crop(crop(t_sum=5000, t_base=10), make_climate(tmean=8.0, tmax_extra=1.0))
    assert res["status"] == "not_suitable_by_model"
    assert res["reason"]["code"] == "does_not_mature"
    assert all(w["matured_share"] == 0 and w["fail_rate"] == 1 for w in res["windows"])
    assert "best_window" not in res


def test_very_short_hot_season_is_penalised():
    hot = make_climate(tmean=30.0, tmax_extra=2.0, precip=10.0)  # 30 °C·d/day -> 1000 °C·d in 34 d
    short = crop(t_sum=1000)
    normal_ref = Stages(20, 30, 30, 20, total=120, row="test", max_total=200, min_total=120)
    short = Crop(**{**short.__dict__, "stages": normal_ref})
    w = evaluate_crop(short, hot)["best_window"]
    assert w["season_days_median"] == 34
    assert w["duration_factor_median"] == pytest.approx(34 / 90, abs=0.01)
    assert w["score_median"] == pytest.approx(34 / 90, abs=0.02)


def test_heat_reduces_temperature_score():
    hot = make_climate(tmean=34.0, tmax_extra=6.0, precip=10.0)  # Tmax 40 -> (45-40)/(45-34)
    w = evaluate_crop(crop(), hot)["best_window"]
    assert w["temperature_score_median"] == pytest.approx(5 / 11, abs=0.01)
    assert w["heat_days_median"] > 0


def test_seasonal_climate_picks_warm_season_for_warm_crop():
    clim = make_climate(tmean=12.0, amplitude=12.0, precip=5.0)  # peak in mid-July
    warm = crop(t_sum=1500, t_base=10, t_opt=28, t_heat=34, t_ext=50)
    w = evaluate_crop(warm, clim)["best_window"]
    assert int(w["sowing"][:2]) in (3, 4, 5, 6)


def test_real_crop_table_loads_and_reports_missing_data():
    crops = {c.id: c for c in load_crops(ROOT / "data")}
    assert len(crops) == 50
    assert crops["maize_grain"].temperature.t_sum == 2050
    assert crops["rapeseed"].missing  # no temperature source and no FAO-56 Table 11 row
    res = evaluate_crop(crops["rapeseed"], make_climate())
    assert res["status"] == "insufficient_data"
    assert evaluate_crop(crops["alfalfa"], make_climate())["status"] == "perennial_not_evaluated"


def test_partial_temperature_block_without_t_opt():
    clim = make_climate()
    assert evaluate_crop(crop(t_sum=None, t_opt=None), clim)["status"] == "insufficient_data"
    assert evaluate_crop(crop(t_sum=1000.0, t_opt=None), clim)["status"] != "insufficient_data"
    crops = {c.id: c for c in load_crops(ROOT / "data")}
    assert crops["lentil"].temperature.t_opt is None and crops["lentil"].temperature.t_sum is not None
    assert "temperature_limits" not in crops["lentil"].missing


def _with_rad(clim, rad=20.0):
    clim.rad = np.full(len(clim.dates), float(rad))
    return clim


def test_light_factor_is_one_against_own_climate():
    # Constant climate: every season has the same radiation -> reference = own median -> factor 1.
    res = evaluate_crop(crop(t_sum=1000), _with_rad(make_climate(tmean=20.0, precip=10.0)))
    w = res["best_window"]
    assert w["light_factor_median"] == pytest.approx(1.0)
    assert res["light_ref"]["01-01"] == pytest.approx(50 * 20.0)


def test_warmer_shorter_season_loses_light_against_baseline():
    # Warming shortens the thermal-time season (50 -> 40 days). Against the baseline
    # radiation reference the season gets 40/50 of the light, so it no longer scores better.
    base = evaluate_crop(crop(t_sum=1000), _with_rad(make_climate(tmean=20.0, precip=10.0)))
    warm_clim = _with_rad(make_climate(tmean=25.0, precip=10.0))
    own = evaluate_crop(crop(t_sum=1000), warm_clim)["best_window"]
    vs_base = evaluate_crop(crop(t_sum=1000), warm_clim, light_ref=base["light_ref"])["best_window"]
    assert own["light_factor_median"] == pytest.approx(1.0)
    assert vs_base["light_factor_median"] == pytest.approx(0.8)
    assert vs_base["score_median"] == pytest.approx(own["score_median"] * 0.8, abs=1e-3)


def test_light_factor_capped_at_one_and_skipped_without_radiation():
    longer = evaluate_crop(crop(t_sum=1000), _with_rad(make_climate(tmean=20.0, precip=10.0)),
                           light_ref={"01-01": 10.0})
    w = next(x for x in longer["windows"] if x["sowing"] == "01-01")
    assert w["light_factor_median"] == 1.0
    no_rad = evaluate_crop(crop(t_sum=1000), make_climate(tmean=20.0, precip=10.0))
    assert no_rad["best_window"]["light_factor_median"] == 1.0
