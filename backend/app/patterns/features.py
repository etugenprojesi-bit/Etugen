"""Year-level feature table for pattern finding (stage 3).

One row per calendar year: the monthly NDVI curve (12 values) plus annual
climate summaries from NASA POWER. Years whose NDVI curve has more than
MAX_MISSING_MONTHS gaps are dropped; smaller gaps are filled by linear
interpolation along the calendar (circular), and the number filled is kept.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MAX_MISSING_MONTHS = 2   # assumption
NDVI_COLS = [f"ndvi_{m:02d}" for m in range(1, 13)]
CLIMATE_COLS = ["precip_mm", "tmean_c", "et0_mm", "hot_days", "frost_days"]


def year_table(monthly: pd.DataFrame, annual_climate: pd.DataFrame) -> pd.DataFrame:
    """monthly: harmonised monthly table (PeriodIndex, column 'ndvi').
    annual_climate: features.climate.annual_summary() output (index = year)."""
    nd = monthly["ndvi"]
    rows = {}
    for year, s in nd.groupby(nd.index.year):
        curve = np.full(12, np.nan)
        curve[s.index.month.to_numpy() - 1] = s.to_numpy()
        missing = int(np.isnan(curve).sum())
        if missing > MAX_MISSING_MONTHS:
            continue
        if missing:
            x = np.arange(36)
            tiled = np.tile(curve, 3)
            ok = ~np.isnan(tiled)
            curve = np.interp(x, x[ok], tiled[ok])[12:24]
        rows[int(year)] = list(curve) + [missing]
    t = pd.DataFrame.from_dict(rows, orient="index", columns=NDVI_COLS + ["ndvi_filled_months"])
    t["ndvi_integral"] = t[NDVI_COLS].sum(axis=1)  # sum of monthly means (NDVI x months)
    t["ndvi_peak"] = t[NDVI_COLS].max(axis=1)
    t["ndvi_peak_month"] = t[NDVI_COLS].to_numpy().argmax(axis=1) + 1
    clim = annual_climate.rename(columns={"precip": "precip_mm", "tmean": "tmean_c", "et0": "et0_mm"})
    t = t.join(clim[CLIMATE_COLS], how="inner")
    t.index.name = "year"
    return t.sort_index()


def zscores(x: pd.DataFrame) -> pd.DataFrame:
    sd = x.std(ddof=1).replace(0, np.nan)
    return (x - x.mean()) / sd
