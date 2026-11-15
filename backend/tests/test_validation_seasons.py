"""Season validation against MODIS MCD12Q2 phenology (no network)."""

import gzip
import json
from datetime import date

import numpy as np
import pandas as pd
import pytest

from app.config import ROOT
from app.sources import gee
from app.validation.seasons import (compare, match_cycle, ndvi_half_amplitude, nearest_sowing_date,
                                    parse_phenology)
from tests.test_engine import crop, make_climate

COLS = ["time_ms", *gee.PHENOLOGY_BANDS]


def days(d: date) -> int:
    return (d - date(1970, 1, 1)).days


def layer(rows):
    full = []
    for r in rows:
        full.append([r.get(c) for c in COLS])
    return {"columns": COLS, "rows": full}


def test_parse_converts_days_since_1970_and_drops_poor_qa():
    t = int(pd.Timestamp("2024-01-01").value // 10**6)
    lay = layer([{"time_ms": t, "Peak_1": 19723 + 46, "MidGreendown_1": 19723 + 88, "MidGreenup_1": 19723 + 11,
                  "EVI_Amplitude_1": 0.4, "QA_Overall_1": 0,
                  "Peak_2": 19723 + 245, "QA_Overall_2": 3}])
    cyc = parse_phenology(lay)
    assert len(cyc) == 1  # cycle 2 has QA "Poor" (3)
    c = cyc[0]
    assert (c["year"], c["cycle"]) == (2024, 1)
    assert c["peak"] == date(2024, 2, 16) and c["greendown"] == date(2024, 3, 29)


def test_match_cycle_window_and_amplitude():
    a = {"peak": date(2020, 3, 1), "amplitude": 0.2, "greendown": date(2020, 4, 1)}
    b = {"peak": date(2020, 3, 20), "amplitude": 0.5, "greendown": date(2020, 4, 20)}
    c = {"peak": date(2020, 9, 1), "amplitude": 0.9, "greendown": date(2020, 10, 1)}
    assert match_cycle([a, b, c], date(2019, 11, 1), date(2020, 3, 10)) is b  # peak <= maturity + 45 d
    assert match_cycle([c], date(2019, 11, 1), date(2020, 3, 10)) is None


def test_ndvi_half_amplitude_on_triangle():
    idx = pd.date_range("2020-01-01", periods=201, freq="D")
    v = np.concatenate([np.linspace(0.2, 0.8, 101), np.linspace(0.8, 0.2, 101)[1:]])
    h = ndvi_half_amplitude(pd.Series(v, index=idx), date(2020, 1, 1), date(2020, 7, 31))
    assert h["peak"] == date(2020, 4, 10)
    assert h["greenup"] == date(2020, 2, 20)   # 0.5 reached after 50 days
    assert h["greendown"] == date(2020, 5, 30)


def test_flat_ndvi_has_no_cycle():
    idx = pd.date_range("2020-01-01", periods=100, freq="D")
    assert ndvi_half_amplitude(pd.Series(0.3, index=idx), date(2020, 1, 1), date(2020, 4, 1)) is None


@pytest.mark.parametrize("doy, md", [(305, (11, 1)), (2, (1, 1)), (364, (1, 1)), (290, (10, 16))])
def test_nearest_sowing_date(doy, md):
    assert nearest_sowing_date(doy) == md


def test_compare_reports_offsets_in_days():
    # Tmean 20 °C, t_sum 1000 -> 50-day seasons; sown 1 Mar -> maturity 19 Apr.
    clim = make_climate(tmean=20.0, precip=10.0)
    cycles = [{"year": y, "cycle": 1, "greenup": None, "peak": date(y, 4, 1),
               "greendown": date(y, 4, 29), "amplitude": 0.4, "qa": 0} for y in range(2001, 2006)]
    r = compare(crop(t_sum=1000), clim, date(2001, 3, 1).timetuple().tm_yday, "none", cycles)
    assert r["sowing"] == "03-01" and r["n_matched"] == r["n_seasons"] == 5
    assert r["maturity_minus_greendown_days"]["median"] == -10
    # mid-season centre: (0.2 + 0.3 + 0.15) x 50 = 32.5 -> day 32 or 33 after sowing (Apr 2/3)
    assert r["midseason_minus_peak_days"]["median"] in (1, 2)
    assert r["interannual_spearman"] is None  # < 8 matched years


@pytest.mark.parametrize("name", ["37.60_32.75", "30.80_75.60", "-0.25_36.15"])
def test_demo_cache_has_phenology_for_25_years(name):
    raw = json.loads(gzip.decompress((ROOT / "demo_cache" / f"gee_{name}.json.gz").read_bytes()))
    cyc = parse_phenology(raw["layers"]["phenology"])
    years = {c["year"] for c in cyc}
    assert raw["layers"]["phenology"]["id"] == gee.PHENOLOGY_ID
    assert min(years) == 2001 and len(years) >= 19
