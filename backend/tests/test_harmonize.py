"""Stage 3: slope factor, Pettitt test, harmonisation and precipitation comparison."""

import math

import numpy as np
import pandas as pd
import pytest

from app.features.terrain import S_UNIT_PLOT, relative_s, rusle_s, slope_summary
from app.features.trends import pettitt
from app.harmonize import compare, series

MS_DAY = 86_400_000


# --- RUSLE S (AH-703 eq. 4-4 / 4-5) -------------------------------------------------


def deg(pct):
    return math.degrees(math.atan(pct / 100))


def test_rusle_s_equations():
    assert rusle_s(0.0) == pytest.approx(0.03)
    th = math.atan(0.05)  # 5 % slope -> eq. 4-4
    assert rusle_s(deg(5)) == pytest.approx(10.8 * math.sin(th) + 0.03)
    th = math.atan(0.20)  # 20 % slope -> eq. 4-5
    assert rusle_s(deg(20)) == pytest.approx(16.8 * math.sin(th) - 0.50)


def test_unit_plot_is_about_one_and_monotonic():
    assert S_UNIT_PLOT == pytest.approx(1.0, abs=0.01)
    assert relative_s(deg(9)) == pytest.approx(1.0)
    values = [relative_s(deg(p)) for p in range(0, 40)]
    assert all(b > a for a, b in zip(values, values[1:]))
    # the two branches nearly meet at 9 % (no big jump)
    assert abs(rusle_s(deg(8.999)) - rusle_s(deg(9.0))) < 0.05


def test_slope_summary_uses_median():
    out = slope_summary({"slope_deg_p50": 1.5, "slope_deg_p90": 3.0, "elevation_p50": 1010.0})
    assert out["status"] == "ok" and out["slope_pct_median"] == pytest.approx(2.6, abs=0.05)
    assert slope_summary({})["status"] == "missing"


# --- Pettitt ------------------------------------------------------------------------


def test_pettitt_finds_step():
    rng = np.random.default_rng(1)
    y = np.r_[rng.normal(0, 1, 12), rng.normal(4, 1, 12)]
    cp = pettitt(y)
    assert cp.significant and cp.index == 11


def test_pettitt_no_step_in_noise():
    y = np.random.default_rng(2).normal(0, 1, 24)
    assert not pettitt(y).significant
    assert pettitt([1, 2]).p_value == 1.0


# --- SMAP merge -------------------------------------------------------------------------


def smap_rows(start, days, value, flag=0):
    t0 = pd.Timestamp(start).value // 1_000_000
    return [[t0 + i * MS_DAY, value, flag] for i in range(days)]


def test_merge_smap_prefers_006_and_adjusts_005():
    v5 = smap_rows("2020-01-01", 60, 0.20)            # 005: Jan-Feb
    v6 = smap_rows("2020-01-01", 40, 0.22)            # 006: first 40 days only, +0.02
    merged, diag = series.merge_smap({series.SECONDARY_SMAP: v5, series.PRIMARY_SMAP: v6})
    assert diag["overlap_days"] == 40
    assert diag["offset_006_minus_005"] == pytest.approx(0.02)
    assert diag["days_006"] == 40 and diag["days_from_005"] == 20
    assert (merged["version"] == "006").sum() == 40
    filled = merged[merged["version"] == "005_adjusted"]["sm"]
    assert np.allclose(filled, 0.22)  # 0.20 + offset


def test_merge_smap_rejects_failed_qa_and_reports_missing_overlap():
    v6 = smap_rows("2020-01-01", 10, 0.3, flag=1) + smap_rows("2020-01-11", 10, 0.25)
    v5 = smap_rows("2019-01-01", 10, 0.1)
    merged, diag = series.merge_smap({series.PRIMARY_SMAP: v6, series.SECONDARY_SMAP: v5})
    assert diag["rejected_by_qa_006"] == 10
    assert diag["offset_006_minus_005"] is None and "note" in diag
    assert len(merged) == 20 and not (merged["sm"] == 0.3).any()


def test_merge_smap_empty():
    merged, diag = series.merge_smap({})
    assert merged.empty and diag["first"] is None


# --- IMERG, NDVI, monthly table -----------------------------------------------------------


def test_imerg_rate_to_monthly_total():
    rows = [[pd.Timestamp("2021-01-01").value // 1_000_000, 0.1],
            [pd.Timestamp("2021-02-01").value // 1_000_000, 0.1],
            [pd.Timestamp("2021-03-01").value // 1_000_000, None]]
    s = series.imerg_monthly_mm({"rows": rows})
    assert s.loc[pd.Period("2021-01", "M")] == pytest.approx(0.1 * 31 * 24)
    assert s.loc[pd.Period("2021-02", "M")] == pytest.approx(0.1 * 28 * 24)
    assert pd.Period("2021-03", "M") not in s.index


def test_ndvi_sentinel_and_low_coverage_dropped():
    layer = {"dates": ["2021-01-01", "2021-01-17", "2021-02-02"], "ndvi_raw": [5000, -9999, 6000],
             "valid_pixels": [60, 0, 10], "scale_factor": 0.0001, "missing": -9999}
    s = series.ndvi_series(layer)
    assert list(s.round(2)) == [0.5]                     # sentinel and 10/60 pixels dropped
    assert s.index[0] == pd.Timestamp("2021-01-09")      # composite mid-date


def power_daily(years=range(2001, 2004), precip=1.0):
    idx = pd.date_range(f"{min(years)}-01-01", f"{max(years)}-12-31", freq="D")
    return pd.DataFrame({"PRECTOTCORR": precip, "TMEAN": 10.0, "ET0": 2.0, "GWETROOT": 0.5}, index=idx)


def test_monthly_table_applies_smap_min_days():
    df = power_daily()
    smap = pd.DataFrame({"sm": [0.2] * 4 + [0.3] * 6, "version": "006"},
                        index=pd.to_datetime(["2001-01-0%d" % d for d in range(1, 5)]
                                             + ["2001-02-%02d" % d for d in range(1, 7)]))
    t = series.monthly_table(df, None, smap, None)
    assert np.isnan(t.loc[pd.Period("2001-01", "M"), "smap_sm"])       # 4 days < SMAP_MIN_DAYS
    assert t.loc[pd.Period("2001-02", "M"), "smap_sm"] == pytest.approx(0.3)
    assert t.loc[pd.Period("2001-01", "M"), "power_precip_mm"] == pytest.approx(31.0)


# --- precipitation comparison ---------------------------------------------------------------


def comparison_table(power_by_year, imerg_by_year):
    idx = pd.period_range(f"{min(power_by_year)}-01", f"{max(power_by_year)}-12", freq="M")
    return pd.DataFrame({"power_precip_mm": [power_by_year[p.year] / 12 for p in idx],
                         "imerg_precip_mm": [imerg_by_year[p.year] / 12 for p in idx]}, index=idx)


def test_compare_detects_inhomogeneous_power_trend():
    rng = np.random.default_rng(3)
    years = range(2001, 2025)
    imerg = {y: 1000 + rng.normal(0, 80) for y in years}
    power = {y: imerg[y] * (0.85 if y <= 2013 else 1.3) for y in years}   # step in POWER only
    c = compare.compare_precip(comparison_table(power, imerg))
    assert c["status"] == "ok" and c["common_full_years"] == 24
    assert c["difference_series"]["change_point"]["significant_5pct"]
    assert c["difference_series"]["change_point"]["step"]["last_year_before"] == 2013
    assert c["difference_series"]["homogeneous"] is False
    assert c["trend"]["power"]["significant_5pct"]
    assert c["power_trend_confirmed_by_imerg"] is False


def test_compare_constant_bias_is_homogeneous():
    rng = np.random.default_rng(4)
    years = range(2001, 2025)
    imerg = {y: 450 + rng.normal(0, 60) for y in years}
    power = {y: imerg[y] * 1.24 for y in years}
    c = compare.compare_precip(comparison_table(power, imerg))
    assert c["verdict"] == "moderate_difference"
    assert c["power_relative_difference"] == pytest.approx(0.24, abs=0.005)
    assert c["difference_series"]["homogeneous"] is True
    assert c["correlation"]["annual"] == pytest.approx(1.0)


def test_compare_needs_overlap():
    t = comparison_table({2001: 1, 2002: 1}, {2001: 1, 2002: 1})
    assert compare.compare_precip(t)["status"] == "insufficient_overlap"


def test_flat_terrain_rule_replaces_unresolved_pixel_slope():
    from app.features.terrain import DEM_STEP_DEG
    assert DEM_STEP_DEG == pytest.approx(0.9274, abs=0.001)  # p10 slope seen at every demo point
    # Punjab demo cell: 5 m relief, median pixel slope = two 1 m steps -> flat
    flat = slope_summary({"slope_deg_p50": 1.8543, "elevation_p10": 235.0, "elevation_p90": 240.0})
    assert flat["flat_terrain"] and flat["slope_pct_median"] == pytest.approx(0.2)
    assert flat["slope_deg_median_pixels"] == pytest.approx(1.85)
    # Nakuru demo cell: steeper than two steps -> pixel median kept
    hill = slope_summary({"slope_deg_p50": 2.6215, "elevation_p10": 1899.0, "elevation_p90": 1985.0})
    assert not hill["flat_terrain"] and hill["slope_pct_median"] == pytest.approx(4.6, abs=0.05)
    # without elevation percentiles the rule cannot be applied
    assert not slope_summary({"slope_deg_p50": 1.5})["flat_terrain"]
