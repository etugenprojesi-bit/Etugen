"""FAO-56 eq. 62 / 63 / 65 (Kc climate adjustment), docs/DATA_SOURCES.md §9."""

import numpy as np
import pytest

from app.features.kc_climate import (
    climate_term, kc_end_adjusted, kc_mid_adjusted, rh_min_daily, season_kc, stage_bounds,
)


def test_fao56_example_27_taipei_and_mocha():
    # Maize, Kc_mid(Tab) = 1.20, h = 2 m. FAO-56 prints 1.07 and 1.30.
    assert kc_mid_adjusted(1.20, 1.3, 75, 2.0) == pytest.approx(1.07, abs=0.005)
    assert kc_mid_adjusted(1.20, 4.6, 44, 2.0) == pytest.approx(1.30, abs=0.005)


def test_standard_climate_leaves_table_value():
    assert kc_mid_adjusted(1.15, 2.0, 45, 1.0) == pytest.approx(1.15)
    assert kc_end_adjusted(0.60, 2.0, 45, 1.0) == pytest.approx(0.60)


def test_kc_end_only_above_045():
    assert kc_end_adjusted(0.25, 5.0, 20, 1.0) == 0.25
    assert kc_end_adjusted(0.45, 5.0, 20, 1.0) == 0.45
    assert kc_end_adjusted(0.60, 5.0, 20, 1.0) > 0.60


def test_validity_limits_are_clipped():
    assert climate_term(0.5, 45, 2.0) == pytest.approx(climate_term(1.0, 45, 2.0))
    assert climate_term(9.0, 45, 2.0) == pytest.approx(climate_term(6.0, 45, 2.0))
    assert climate_term(2.0, 5, 2.0) == pytest.approx(climate_term(2.0, 20, 2.0))
    assert climate_term(2.0, 95, 2.0) == pytest.approx(climate_term(2.0, 80, 2.0))


def test_no_adjustment_for_short_or_unknown_height():
    assert climate_term(5.0, 20, 0.05) == 0.0
    assert climate_term(5.0, 20, None) == 0.0
    assert climate_term(np.nan, 20, 1.0) == 0.0


def test_rh_min_eq63():
    assert rh_min_daily(25.0, 25.0) == pytest.approx(100.0)
    assert rh_min_daily(30.0, 25.0) == pytest.approx(100.0)  # capped
    # e°(10) / e°(30) = 1.228 / 4.243 (FAO-56 Annex 2 Table 2.3)
    assert rh_min_daily(10.0, 30.0) == pytest.approx(100 * 1.228 / 4.243, abs=0.1)


def test_stage_means_use_the_right_days():
    fractions = (0.2, 0.3, 0.3, 0.2)  # mid-season = days 50..79, late = 80..99 of 100
    n = 100
    u2 = np.full(n, 2.0)
    rh = np.full(n, 45.0)
    u2[50:80] = 4.0     # windy mid-season only
    rh[80:] = 20.0      # dry late season only
    a, b = stage_bounds(n, fractions)
    assert (a, b) == (50, 80)
    kmid, kend, means = season_kc(fractions, 1.15, 0.60, 1.0, u2, rh)
    assert means["u2_mid"] == pytest.approx(4.0) and means["rh_min_mid"] == pytest.approx(45.0)
    assert means["u2_late"] == pytest.approx(2.0) and means["rh_min_late"] == pytest.approx(20.0)
    assert kmid == pytest.approx(1.15 + 0.08 * (1 / 3) ** 0.3)
    assert kend == pytest.approx(0.60 + 0.1 * (1 / 3) ** 0.3)


def test_engine_adjusts_kc_only_with_wind_humidity_and_height():
    from dataclasses import replace

    from tests.test_engine import crop, make_climate

    c = replace(crop(), kc_end=0.60, max_height_m=1.0)
    still = make_climate(tmean=20.0, precip=10.0)  # wet: the crop is evaluated
    from app.suitability.engine import evaluate_crop
    w0 = evaluate_crop(c, still)["best_window"]
    assert w0["kc_mid_median"] == pytest.approx(1.15) and w0["kc_end_median"] == pytest.approx(0.60)

    n = len(still.dates)
    windy_dry = replace(still, u2=np.full(n, 4.0), rh_min=np.full(n, 20.0))
    w1 = evaluate_crop(c, windy_dry)["best_window"]
    term = (0.04 * 2 + 0.004 * 25) * (1 / 3) ** 0.3
    assert w1["kc_mid_median"] == pytest.approx(1.15 + term, abs=1e-3)
    assert w1["kc_end_median"] == pytest.approx(0.60 + term, abs=1e-3)
    assert w1["etc_mm_median"] > w0["etc_mm_median"]

    no_height = replace(c, max_height_m=None)
    assert evaluate_crop(no_height, windy_dry)["best_window"]["kc_mid_median"] == pytest.approx(1.15)


def test_scenario_keeps_observed_rh_min():
    import pandas as pd

    from app.features import climate, scenario

    dates = pd.date_range("2001-01-01", periods=10, freq="D")
    daily = pd.DataFrame({"T2M": 20.0, "T2M_MAX": 26.0, "T2M_MIN": 14.0, "PRECTOTCORR": 1.0,
                          "RH2M": 60.0, "WS2M": 2.0, "ALLSKY_SFC_SW_DWN": 20.0, "T2MDEW": 10.0},
                         index=dates)
    base = climate.add_derived(daily, 1000.0, 37.6)
    warm = scenario.apply(daily, 3.0, 0.0, 1000.0, 37.6)
    assert np.allclose(warm["RHMIN"], base["RHMIN"])
    assert (warm["ET0"] > base["ET0"]).all()
