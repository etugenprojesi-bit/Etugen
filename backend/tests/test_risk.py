"""Stage 5: scenario deltas, IMERG rainfall rescaling and risk-layer anomalies."""

import numpy as np
import pandas as pd
import pytest

from app.features import scenario
from app.harmonize.rainfall import rescale_to_imerg
from app.risk import layers as risk


def _daily(start="2001-01-01", end="2002-12-31", seed=0):
    idx = pd.date_range(start, end, freq="D")
    rng = np.random.default_rng(seed)
    n = len(idx)
    doy = idx.day_of_year.to_numpy()
    tmean = 10 - 12 * np.cos(2 * np.pi * doy / 365)
    return pd.DataFrame({
        "T2M": tmean, "T2M_MAX": tmean + 6, "T2M_MIN": tmean - 6,
        "PRECTOTCORR": rng.gamma(0.5, 3.0, n), "RH2M": np.full(n, 60.0), "WS2M": np.full(n, 2.0),
        "ALLSKY_SFC_SW_DWN": 15 + 8 * np.sin(2 * np.pi * (doy - 80) / 365),
        "GWETTOP": np.full(n, 0.4), "GWETROOT": np.full(n, 0.5),
    }, index=idx)


# --- scenario ---------------------------------------------------------------------


def test_perturb_shifts_temperature_and_scales_rain():
    d = _daily()
    p = scenario.perturb(d, 2.0, -20.0)
    for c in ("T2M", "T2M_MAX", "T2M_MIN"):
        np.testing.assert_allclose(p[c], d[c] + 2.0)
    np.testing.assert_allclose(p["PRECTOTCORR"], d["PRECTOTCORR"] * 0.8)
    np.testing.assert_allclose(p["RH2M"], d["RH2M"])  # assumption: RH unchanged
    assert d["T2M_MAX"].iloc[0] == pytest.approx(p["T2M_MAX"].iloc[0] - 2.0)  # input not modified


def test_perturb_rejects_out_of_range():
    with pytest.raises(ValueError):
        scenario.perturb(_daily(), 5.0, 0)
    with pytest.raises(ValueError):
        scenario.perturb(_daily(), 0, -50)


def test_warming_raises_et0_with_constant_rh():
    d = _daily()
    base = scenario.apply(d, 0, 0, 1000, 37.6)
    warm = scenario.apply(d, 2, 0, 1000, 37.6)
    assert warm["ET0"].sum() > base["ET0"].sum()
    assert (warm["TMEAN"] - base["TMEAN"]).abs().max() == pytest.approx(2.0)


def test_scenario_inactive_at_zero():
    assert not scenario.is_active(0, 0)
    assert scenario.is_active(0, 5)


# --- IMERG rescaling -------------------------------------------------------------


def test_rescale_matches_imerg_month_totals():
    d = _daily("2001-01-01", "2001-03-31")
    d.loc["2001-02", "PRECTOTCORR"] = 0.0  # POWER dry month
    imerg = pd.Series({pd.Period("2001-01", "M"): 30.0, pd.Period("2001-02", "M"): 12.0})
    out, diag = rescale_to_imerg(d, imerg)
    assert out.loc["2001-01", "PRECTOTCORR"].sum() == pytest.approx(30.0)
    # Daily pattern kept: proportional to POWER.
    jan_in, jan_out = d.loc["2001-01", "PRECTOTCORR"], out.loc["2001-01", "PRECTOTCORR"]
    np.testing.assert_allclose(jan_out, jan_in * 30.0 / jan_in.sum())
    # February: POWER dry, IMERG wet -> left as POWER, reported.
    assert out.loc["2001-02", "PRECTOTCORR"].sum() == 0.0
    assert diag["months_imerg_rain_without_power_rain"] == 1
    assert diag["imerg_rain_not_placed_mm"] == pytest.approx(12.0)
    # March: no IMERG -> unchanged, reported.
    np.testing.assert_allclose(out.loc["2001-03", "PRECTOTCORR"], d.loc["2001-03", "PRECTOTCORR"])
    assert diag["months_without_imerg"] == 1 and diag["months_without_imerg_range"] == "2001-03..2001-03"
    assert diag["months_rescaled"] == 1


# --- risk anomalies --------------------------------------------------------------


def _monthly(values_by_year: dict[int, list[float]]) -> pd.Series:
    idx, vals = [], []
    for y, row in values_by_year.items():
        for m, v in enumerate(row, start=1):
            idx.append(pd.Period(year=y, month=m, freq="M"))
            vals.append(v)
    return pd.Series(vals, index=pd.PeriodIndex(idx))


def test_risk_z_standardises_per_calendar_month_and_orients():
    base = _monthly({y: [float(y - 2000)] * 12 for y in range(2001, 2007)})  # 1..6
    stats = risk.month_stats(base)
    assert stats.loc[1, "mean"] == pytest.approx(3.5)
    sd = np.std([1, 2, 3, 4, 5, 6], ddof=1)
    z = risk.risk_z(base, stats, higher_is_worse=True)
    assert z[pd.Period("2006-01", "M")] == pytest.approx((6 - 3.5) / sd)
    z_neg = risk.risk_z(base, stats, higher_is_worse=False)
    assert z_neg[pd.Period("2006-01", "M")] == pytest.approx(-(6 - 3.5) / sd)


def test_risk_z_flat_baseline_and_min_years():
    base = _monthly({y: [0.0] * 12 for y in range(2001, 2007)})
    stats = risk.month_stats(base)
    vals = _monthly({2001: [0.0] + [2.0] * 11})
    z = risk.risk_z(vals, stats, higher_is_worse=True)
    assert z[pd.Period("2001-01", "M")] == 0.0
    assert z[pd.Period("2001-02", "M")] == risk.Z_CAP  # outside an invariant baseline
    short = risk.month_stats(_monthly({y: [1.0 * y] * 12 for y in range(2001, 2001 + risk.MIN_YEARS - 1)}))
    assert np.isnan(risk.risk_z(vals, short, True)).all()


def test_monthly_climate_counts():
    d = scenario.apply(_daily(), 0, 0, 500, 40.0)
    d.loc["2001-07-10", "T2M_MAX"] = 40.0
    m = risk.monthly_climate(d, heat_c=35.0, lethal_c=-15.0, heavy_thr=1000.0)
    jul = m.loc[pd.Period("2001-07", "M")]
    expected_hot = float((d.loc["2001-07", "T2M_MAX"] > 35).sum())
    assert jul["hot_days"] == expected_hot >= 1
    assert m["heavy_rain_days"].sum() == 0
    jan = m.loc[pd.Period("2001-01", "M")]
    assert jan["frost_days"] == float((d.loc["2001-01", "T2M_MIN"] < 0).sum())
    assert jan["water_balance_mm"] == pytest.approx(
        d.loc["2001-01", "PRECTOTCORR"].sum() - d.loc["2001-01", "ET0"].sum())


def test_build_scenario_shifts_counts_against_baseline():
    raw = _daily("2001-01-01", "2008-12-31")
    base = scenario.apply(raw, 0, 0, 500, 40.0)
    warm = scenario.apply(raw, 3, 0, 500, 40.0)
    heat = {"threshold_c": 25.0, "source": "test", "assumption": True}
    out = risk.build(base, warm, None, heat, None)
    assert out["years"] == list(range(2001, 2009))
    assert out["missing_layers"] == ["smap_sm", "ndvi"]
    lay = {lyr["id"]: lyr for lyr in out["layers"]}
    assert set(lay) == {"frost_days", "hot_days", "heavy_rain_days", "water_balance_mm"}
    # Warmer: more hot days and fewer frost days than the baseline mean.
    assert all(v > lay["hot_days"]["annual_baseline_mean"] for v in lay["hot_days"]["annual"])
    assert all(v < lay["frost_days"]["annual_baseline_mean"] for v in lay["frost_days"]["annual"])
    assert all(len(row) == 12 for row in lay["hot_days"]["values"])
    assert lay["water_balance_mm"]["higher_is_worse"] is False
