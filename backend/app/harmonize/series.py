"""Harmonisation of point time series onto one monthly time step (stage 3).

Spatial side: no resampling. Every source is sampled at the same rounded
analysis point and keeps its native footprint (POWER ~0.5°, IMERG 0.1°,
SMAP 9 km, MODIS NDVI 1 km mean of 250 m pixels). The footprints are
reported with the data, never hidden.

Temporal side: everything is aggregated to calendar months
(sums for precipitation, means for state variables) with explicit
minimum-coverage rules; months that fail them are NaN, not filled.
"""

from __future__ import annotations

import calendar

import numpy as np
import pandas as pd

NDVI_MIN_PIXEL_SHARE = 0.5   # assumption: a composite needs >= 50 % valid pixels of the best composite
SMAP_MIN_DAYS = 5            # assumption: a month needs >= 5 valid SMAP retrievals (revisit 2-3 days)
PRIMARY_SMAP = "NASA/SMAP/SPL3SMP_E/006"
SECONDARY_SMAP = "NASA/SMAP/SPL3SMP_E/005"


# --- per-source parsing ---------------------------------------------------------------


def ndvi_series(layer: dict) -> pd.Series:
    """16-day MOD13Q1 composites -> NDVI (scaled), indexed by composite mid-date.

    Composites with fewer valid (QA good/marginal) pixels than
    NDVI_MIN_PIXEL_SHARE of the best composite are dropped.
    """
    df = pd.DataFrame({"t": pd.to_datetime(layer["dates"]), "ndvi": layer["ndvi_raw"],
                       "n": layer["valid_pixels"]})
    raw = pd.to_numeric(df["ndvi"], errors="coerce")
    df["ndvi"] = raw.where(raw != layer.get("missing", -9999)) * layer.get("scale_factor", 0.0001)
    df["n"] = pd.to_numeric(df["n"], errors="coerce").fillna(0)
    if df["n"].max() > 0:
        df.loc[df["n"] < NDVI_MIN_PIXEL_SHARE * df["n"].max(), "ndvi"] = np.nan
    # A 16-day composite starting at t represents t .. t+15; use its middle for the month.
    idx = df["t"] + pd.Timedelta(days=8)
    return pd.Series(df["ndvi"].to_numpy(), index=pd.DatetimeIndex(idx), name="ndvi").dropna()


def _smap_frame(rows: list) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["sm", "flag"], index=pd.DatetimeIndex([], name="date"))
    df = pd.DataFrame(rows, columns=["t", "sm", "flag"])
    df["date"] = pd.to_datetime(df["t"], unit="ms").dt.normalize()
    df = df.drop(columns="t").groupby("date").first()
    return df.astype(float)


def merge_smap(versions: dict[str, list]) -> tuple[pd.DataFrame, dict]:
    """Merge SPL3SMP_E versions into one daily series (QA: flag == 0 only).

    Rule: version 006 is primary (it is the reprocessed record). Days where
    006 has no passing retrieval are filled from 005 after removing the mean
    006-005 offset measured on days where both pass. Without overlap the
    offset is not estimated (0) and this is reported.
    """
    v6 = _smap_frame(versions.get(PRIMARY_SMAP, []))
    v5 = _smap_frame(versions.get(SECONDARY_SMAP, []))
    ok6 = v6[(v6["flag"] == 0) & v6["sm"].notna()]["sm"]
    ok5 = v5[(v5["flag"] == 0) & v5["sm"].notna()]["sm"]

    both = pd.concat([ok5.rename("v5"), ok6.rename("v6")], axis=1, join="inner")
    diag: dict = {"overlap_days": int(len(both))}
    if len(both) >= 30:
        diff = both["v6"] - both["v5"]
        offset = float(diff.mean())
        diag |= {"offset_006_minus_005": round(offset, 5),
                 "rmsd": round(float(np.sqrt((diff ** 2).mean())), 5),
                 "r": (round(float(np.corrcoef(both["v5"], both["v6"])[0, 1]), 4)
                       if both["v5"].std() > 0 and both["v6"].std() > 0 else None)}
    else:
        offset = 0.0
        diag |= {"offset_006_minus_005": None,
                 "note": "fewer than 30 overlapping days: no cross-calibration, 005 used unadjusted"}

    fill = (ok5 + offset).loc[ok5.index.difference(ok6.index)]
    merged = pd.concat([
        pd.DataFrame({"sm": ok6, "version": "006"}),
        pd.DataFrame({"sm": fill, "version": "005_adjusted"}),
    ]).sort_index()
    merged.index.name = "date"
    diag |= {"days_006": int(len(ok6)), "days_from_005": int(len(fill)),
             "first": None if merged.empty else str(merged.index.min().date()),
             "last": None if merged.empty else str(merged.index.max().date()),
             "rejected_by_qa_006": int(((v6["flag"] != 0) & v6["sm"].notna()).sum())}
    return merged, diag


def imerg_monthly_mm(layer: dict) -> pd.Series:
    """IMERG monthly mean rate (mm/h) -> monthly total (mm) = rate x hours in month."""
    rows = [r for r in layer["rows"] if r[1] is not None]
    if not rows:
        return pd.Series(dtype=float, name="imerg_precip_mm")
    t = pd.to_datetime([r[0] for r in rows], unit="ms")
    hours = np.array([calendar.monthrange(d.year, d.month)[1] * 24 for d in t])
    s = pd.Series(np.array([r[1] for r in rows], float) * hours, index=t.to_period("M"),
                  name="imerg_precip_mm")
    return s.groupby(level=0).first()


def chirps_monthly_mm(layer: dict) -> pd.Series:
    """CHIRPS monthly totals (mm), rows [["YYYY-MM", mm], ...] summed on the Earth Engine side."""
    rows = [r for r in layer["rows"] if r[1] is not None]
    if not rows:
        return pd.Series(dtype=float, name="chirps_precip_mm")
    idx = pd.PeriodIndex([r[0] for r in rows], freq="M")
    return pd.Series([float(r[1]) for r in rows], index=idx, name="chirps_precip_mm")


# --- monthly table ------------------------------------------------------------------


def monthly_table(power_daily: pd.DataFrame, ndvi: pd.Series | None, smap: pd.DataFrame | None,
                  imerg_mm: pd.Series | None) -> pd.DataFrame:
    """One row per calendar month (PeriodIndex) with all sources side by side."""
    p = power_daily
    per = p.index.to_period("M")
    days = p.groupby(per).size()
    full = days == pd.Series(per.days_in_month, index=per).groupby(level=0).first()
    out = pd.DataFrame({
        "power_precip_mm": p["PRECTOTCORR"].groupby(per).sum(min_count=1).where(full),
        "power_tmean_c": p["TMEAN"].groupby(per).mean() if "TMEAN" in p else np.nan,
        "power_et0_mm": p["ET0"].groupby(per).sum(min_count=1).where(full) if "ET0" in p else np.nan,
        "power_gwetroot_model": p["GWETROOT"].groupby(per).mean(),
    })
    if imerg_mm is not None and len(imerg_mm):
        out = out.join(imerg_mm.rename("imerg_precip_mm"), how="left")
    else:
        out["imerg_precip_mm"] = np.nan
    if ndvi is not None and len(ndvi):
        out = out.join(ndvi.groupby(ndvi.index.to_period("M")).mean().rename("ndvi"), how="left")
    else:
        out["ndvi"] = np.nan
    if smap is not None and len(smap):
        g = smap["sm"].groupby(smap.index.to_period("M"))
        sm = g.mean().where(g.count() >= SMAP_MIN_DAYS)
        out = out.join(sm.rename("smap_sm"), how="left")
        out = out.join(g.count().rename("smap_days"), how="left")
    else:
        out["smap_sm"] = np.nan
        out["smap_days"] = np.nan
    out.index.name = "month"
    return out


def climatology(table: pd.DataFrame, cols: list[str]) -> list[dict]:
    """Mean per calendar month over all years with data, plus the number of years used."""
    m = table.index.month
    res = []
    for k in range(1, 13):
        sub = table[m == k]
        row = {"month": k}
        for c in cols:
            v = sub[c].dropna()
            row[c] = None if v.empty else round(float(v.mean()), 4)
            row[f"{c}_years"] = int(len(v))
        res.append(row)
    return res
