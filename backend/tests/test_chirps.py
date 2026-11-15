"""CHIRPS rain source and the POWER rain check (plan_konya_yagis.md, K1-a / K2)."""

import gzip
import json

import numpy as np
import pandas as pd
import pytest

from app.config import ROOT
from app.harmonize.rainfall import WET_RATIO_LIMIT, rain_check, rescale_to_imerg, rescale_to_monthly
from app.harmonize.series import chirps_monthly_mm
from app.sources import gee


def power_daily(years=(2001, 2002), mm=2.0):
    idx = pd.date_range(f"{years[0]}-01-01", f"{years[1]}-12-31", freq="D")
    return pd.DataFrame({"PRECTOTCORR": np.full(len(idx), mm)}, index=idx)


def monthly(daily, factor):
    m = daily["PRECTOTCORR"].groupby(daily.index.to_period("M")).sum()
    return m * factor


def test_rescale_hits_monthly_totals_and_keeps_pattern():
    d = power_daily()
    d.iloc[3, 0] = 10.0  # one wet day
    target = monthly(d, 0.5)
    out, diag = rescale_to_monthly(d, target, "CHIRPS")
    got = out["PRECTOTCORR"].groupby(out.index.to_period("M")).sum()
    assert np.allclose(got.to_numpy(), target.to_numpy())
    assert out["PRECTOTCORR"].iloc[3] / out["PRECTOTCORR"].iloc[4] == pytest.approx(5.0)
    assert diag["source"] == "CHIRPS" and diag["factor_median"] == pytest.approx(0.5)


def test_imerg_wrapper_keeps_its_api_keys():
    d = power_daily()
    _, diag = rescale_to_imerg(d, monthly(d, 0.8))
    assert "months_without_imerg" in diag and "source" not in diag


@pytest.mark.parametrize("factor, wet", [(1 / 1.8, True), (1 / 1.2, False), (1.0, False)])
def test_rain_check_flags_power_wetter_than_limit(factor, wet):
    d = power_daily()
    rc = rain_check(d, monthly(d, factor))
    assert rc["status"] == "ok" and rc["years"] == "2001..2002"
    assert rc["power_may_be_too_wet"] is wet and rc["limit"] == WET_RATIO_LIMIT


def test_rain_check_needs_complete_years():
    d = power_daily()
    partial = monthly(d, 1.0).iloc[:6]
    assert rain_check(d, partial)["status"] == "missing"


@pytest.mark.parametrize("name, mean_mm", [("37.60_32.75", 309), ("30.80_75.60", 617), ("-0.25_36.15", 1141)])
def test_demo_cache_chirps_layer(name, mean_mm):
    raw = json.loads(gzip.decompress((ROOT / "demo_cache" / f"gee_{name}.json.gz").read_bytes()))
    layer = raw["layers"]["chirps"]
    s = chirps_monthly_mm(layer)
    assert layer["id"] == gee.CHIRPS_ID and len(s) == 300
    sub = s[(s.index.year >= 2001) & (s.index.year <= 2024)]
    assert round(sub.sum() / 24) == mean_mm  # probe result 2026-11-14
