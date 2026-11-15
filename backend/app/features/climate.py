"""Climate profile features from daily NASA POWER data.

All thresholds are stated here and in docs/METHOD.md. Rule/statistics based.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.features.et0 import et0_daily
from app.features.kc_climate import rh_min_daily
from app.features.trends import mann_kendall

FROST_C = 0.0          # Tmin < 0 °C = frost day
HOT_C = 35.0           # Tmax > 35 °C = hot day (generic; crop-specific thresholds in suitability)
WET_DAY_MM = 1.0       # ETCCDI wet-day definition
HEAVY_PCTL = 95        # ETCCDI R95p: days above the 95th percentile of wet-day precipitation


def add_derived(daily: pd.DataFrame, elevation_m: float, lat: float) -> pd.DataFrame:
    df = daily.copy()
    df["TMEAN"] = (df["T2M_MAX"] + df["T2M_MIN"]) / 2.0
    df["ET0"] = et0_daily(
        df["T2M_MAX"].to_numpy(), df["T2M_MIN"].to_numpy(), df["RH2M"].to_numpy(),
        df["WS2M"].to_numpy(), df["ALLSKY_SFC_SW_DWN"].to_numpy(),
        elevation_m, lat, df.index.day_of_year.to_numpy(),
    )
    if "T2MDEW" in df:  # daily RHmin, FAO-56 eq. 63 (Kc climate adjustment)
        df["RHMIN"] = rh_min_daily(df["T2MDEW"].to_numpy(), df["T2M_MAX"].to_numpy())
    return df


def heavy_rain_threshold(precip: pd.Series) -> float | None:
    wet = precip[precip >= WET_DAY_MM].dropna()
    return float(np.percentile(wet, HEAVY_PCTL)) if len(wet) >= 20 else None


def monthly_profile(df: pd.DataFrame) -> dict:
    """Climatological month-by-month values (mean over years)."""
    years = df.index.year.nunique()
    thr = heavy_rain_threshold(df["PRECTOTCORR"])
    by_ym = df.groupby([df.index.year, df.index.month])
    ym = pd.DataFrame({
        "tmean": by_ym["TMEAN"].mean(),
        "tmax": by_ym["T2M_MAX"].mean(),
        "tmin": by_ym["T2M_MIN"].mean(),
        "precip_mm": by_ym["PRECTOTCORR"].sum(min_count=1),
        "et0_mm": by_ym["ET0"].sum(min_count=1),
        "frost_days": by_ym["T2M_MIN"].apply(lambda s: int((s < FROST_C).sum())),
        "hot_days": by_ym["T2M_MAX"].apply(lambda s: int((s > HOT_C).sum())),
        "heavy_rain_days": by_ym["PRECTOTCORR"].apply(
            lambda s: int((s > thr).sum()) if thr is not None else np.nan),
        "soil_wetness_root_model": by_ym["GWETROOT"].mean(),
    })
    month = ym.index.get_level_values(1)
    clim = ym.groupby(month).mean()
    frost_prob = ym["frost_days"].gt(0).groupby(month).mean()
    out = []
    for m in range(1, 13):
        r = clim.loc[m]
        out.append({
            "month": m,
            "tmean_c": round(r.tmean, 1),
            "tmax_c": round(r.tmax, 1),
            "tmin_c": round(r.tmin, 1),
            "precip_mm": round(r.precip_mm, 1),
            "et0_mm": round(r.et0_mm, 1),
            "water_balance_mm": round(r.precip_mm - r.et0_mm, 1),
            "frost_days": round(r.frost_days, 1),
            "frost_probability": round(float(frost_prob.loc[m]), 2),
            "hot_days": round(r.hot_days, 1),
            "heavy_rain_days": None if np.isnan(r.heavy_rain_days) else round(r.heavy_rain_days, 2),
            "soil_wetness_root_model": round(r.soil_wetness_root_model, 3),
        })
    return {"years": int(years), "heavy_rain_threshold_mm": None if thr is None else round(thr, 1),
            "months": out}


def annual_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(df.index.year)
    return pd.DataFrame({
        "tmean": g["TMEAN"].mean(),
        "precip": g["PRECTOTCORR"].sum(min_count=1),
        "et0": g["ET0"].sum(min_count=1),
        "frost_days": g["T2M_MIN"].apply(lambda s: int((s < FROST_C).sum())),
        "hot_days": g["T2M_MAX"].apply(lambda s: int((s > HOT_C).sum())),
        "soil_wetness_root_model": g["GWETROOT"].mean(),
    })


def trends(df: pd.DataFrame) -> dict:
    ann = annual_summary(df)
    years = ann.index.to_numpy(dtype=float)
    spec = {
        "tmean": ("°C", "per_decade"),
        "precip": ("mm", "per_decade"),
        "et0": ("mm", "per_decade"),
        "frost_days": ("days", "per_decade"),
        "hot_days": ("days", "per_decade"),
        "soil_wetness_root_model": ("0-1", "per_decade"),
    }
    out = {}
    for col, (unit, _) in spec.items():
        tr = mann_kendall(ann[col].to_numpy(), years)
        out[col] = {
            "slope_per_decade": None if tr.slope_per_year is None else round(tr.slope_per_year * 10, 4),
            "unit": unit,
            "p_value": round(tr.p_value, 4),
            "significant_5pct": tr.significant,
            "n_years": tr.n,
            "method": "stat:mann_kendall+sens_slope",
        }
    out["soil_wetness_root_model"]["note"] = "MERRA-2 model output via NASA POWER, not SMAP observation"
    return out


def annual_means(df: pd.DataFrame) -> dict:
    ann = annual_summary(df)
    return {
        "tmean_c": round(float(ann["tmean"].mean()), 1),
        "precip_mm": round(float(ann["precip"].mean()), 0),
        "et0_mm": round(float(ann["et0"].mean()), 0),
        "aridity_index_p_over_et0": round(float(ann["precip"].mean() / ann["et0"].mean()), 2),
        "frost_days": round(float(ann["frost_days"].mean()), 1),
        "hot_days": round(float(ann["hot_days"].mean()), 1),
    }
