"""Stage 3: pattern-finding methods on synthetic year tables with a known answer."""

import numpy as np
import pandas as pd
import pytest

from app.patterns import features, methods

SINGLE = np.array([.2, .2, .3, .5, .7, .6, .3, .2, .2, .2, .2, .2])   # spring peak
DOUBLE = np.array([.6, .7, .5, .3, .2, .2, .4, .7, .7, .4, .2, .3])   # two seasons


def year_table(curves, precip, seed=0):
    rng = np.random.default_rng(seed)
    years = range(2001, 2001 + len(curves))
    rows = {}
    for y, c, p in zip(years, curves, precip):
        rows[y] = list(np.asarray(c) + rng.normal(0, 0.01, 12)) + [0]
    t = pd.DataFrame.from_dict(rows, orient="index", columns=features.NDVI_COLS + ["ndvi_filled_months"])
    t["ndvi_integral"] = t[features.NDVI_COLS].sum(axis=1)
    t["ndvi_peak"] = t[features.NDVI_COLS].max(axis=1)
    t["ndvi_peak_month"] = t[features.NDVI_COLS].to_numpy().argmax(axis=1) + 1
    t["precip_mm"] = precip
    t["tmean_c"] = 12 + rng.normal(0, 0.5, len(t))
    t["et0_mm"] = 1100 + rng.normal(0, 30, len(t))
    t["hot_days"] = rng.integers(0, 10, len(t))
    t["frost_days"] = rng.integers(40, 60, len(t))
    return t


def test_year_table_fills_small_gaps_and_drops_large():
    idx = pd.period_range("2001-01", "2002-12", freq="M")
    ndvi = np.r_[SINGLE, SINGLE]
    ndvi[3] = np.nan                    # 2001: one gap -> filled
    ndvi[12:16] = np.nan                # 2002: four gaps -> dropped
    monthly = pd.DataFrame({"ndvi": ndvi}, index=idx)
    ann = pd.DataFrame({"precip": [400.0, 500.0], "tmean": [11.0, 12.0], "et0": [1000.0, 1100.0],
                        "hot_days": [1, 2], "frost_days": [50, 40]}, index=[2001, 2002])
    t = features.year_table(monthly, ann)
    assert list(t.index) == [2001]
    assert t.loc[2001, "ndvi_filled_months"] == 1
    assert t.loc[2001, "ndvi_04"] == pytest.approx((0.3 + 0.7) / 2)
    assert t.loc[2001, "precip_mm"] == 400.0


def test_zscore_flags_the_drought_year():
    curves = [SINGLE] * 20
    curves[7] = SINGLE * 0.5                                 # failed season
    precip = [400.0] * 20
    t = year_table(curves, precip)
    a = methods.zscore_anomalies(t)
    assert a["anomalous_years"] == [2008]
    assert a["years"][0]["direction"] == "low"


def test_kmeans_separates_season_shapes_and_detects_regime_shift():
    curves = [SINGLE] * 12 + [DOUBLE] * 12
    t = year_table(curves, [400.0] * 24)
    km = methods.kmeans_curves(t)
    assert km["status"] == "ok" and km["k"] == 2
    groups = sorted(sorted(c["years"]) for c in km["clusters"])
    assert groups == [list(range(2001, 2013)), list(range(2013, 2025))]
    peaks = sorted(c["n_peaks"] for c in km["clusters"])
    assert peaks == [1, 2]
    assert km["regime_shift"]["last_year_before"] == 2012


def test_kmeans_mixed_years_no_regime_shift():
    curves = [SINGLE if i % 2 else DOUBLE for i in range(24)]
    km = methods.kmeans_curves(year_table(curves, [400.0] * 24))
    assert km["k"] == 2 and km["regime_shift"] is None


def test_isolation_forest_flags_outlier_and_is_reproducible():
    curves = [SINGLE] * 24
    curves[5] = DOUBLE
    t = year_table(curves, [400.0] * 24)
    a = methods.isolation_forest(t)
    b = methods.isolation_forest(t)
    assert 2006 in a["anomalous_years"]
    assert a == b


def test_analogs_have_skill_when_ndvi_follows_climate():
    rng = np.random.default_rng(5)
    precip = rng.uniform(250, 650, 25)
    curves = [SINGLE * (0.6 + p / 1000) for p in precip]   # wetter year -> greener
    t = year_table(curves, list(precip))
    an = methods.analog_years(t)
    assert an["status"] == "ok" and len(an["target_analogs"]) == methods.ANALOG_K
    assert an["target_year"] == 2025
    assert an["loo"]["skill"] > 0.3


def test_compare_reports_agreement():
    curves = [SINGLE] * 24
    curves[3] = SINGLE * 0.4
    out = methods.compare(year_table(curves, [400.0] * 24))
    assert 2004 in out["zscore"]["anomalous_years"]
    ag = out["agreement"]
    assert set(ag["both"]) | set(ag["only_zscore"]) | set(ag["only_isolation_forest"]) == \
        {c["year"] for c in out["flagged_year_context"]}
