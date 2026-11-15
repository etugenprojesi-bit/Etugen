"""Risk layers at the analysis point: one value per layer, year and month (stage 5).

Layers are point time series, not maps. Each month's value is compared with
the same calendar month in the *baseline* record (observed data, chosen
rainfall source, no scenario), giving a standardised anomaly z. The anomaly is
oriented so that positive = worse ("risk z"): more frost / hot / heavy-rain
days, less water balance, drier soil, lower NDVI.

Thresholds:
* frost day: Tmin < 0 °C (rule, as in the climate profile);
* lethal cold day: Tmin < the crop's lethal minimum (Luo 2011, from
  data/crop_phenology.yaml) — 2 m air temperature on a ~0.5° grid, not the
  temperature at the plant's crown (snow cover protects); only for crops with
  a sourced value;
* hot day: Tmax > the crop's SIMPLE t_heat (Zhao et al. 2019) when a crop with
  a sourced value is chosen, otherwise the generic 35 °C (assumption);
* heavy-rain day: P > R95p of baseline wet days (ETCCDI style);
* water balance: monthly P - ET0 (FAO-56);
* SMAP surface soil moisture and MODIS NDVI: monthly means from the stage 3
  harmonisation (observations; the scenario sliders do not change them).

Assumptions: |risk z| >= 1 counts as "unusual" (RISK_Z_FLAG); a month's
anomaly needs >= MIN_YEARS baseline years for that calendar month; when the
baseline never varies (SD = 0, e.g. no frost in July in any year) a different
value gets risk z = +/-Z_CAP ("outside the observed range").
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.features.climate import FROST_C, HOT_C, heavy_rain_threshold

RISK_Z_FLAG = 1.0   # assumption: |z| >= 1 SD is shown as unusual
MIN_YEARS = 5       # assumption: anomalies need >= 5 baseline years per calendar month
Z_CAP = 3.0         # assumption: display cap for z, and value for "outside an invariant baseline"


def monthly_climate(df: pd.DataFrame, heat_c: float, lethal_c: float | None,
                    heavy_thr: float | None) -> pd.DataFrame:
    """Per calendar month (PeriodIndex): day counts and P - ET0 from a daily frame with ET0."""
    per = df.index.to_period("M")
    g = df.groupby(per)
    out = pd.DataFrame({
        "frost_days": g["T2M_MIN"].apply(lambda s: float((s < FROST_C).sum())),
        "hot_days": g["T2M_MAX"].apply(lambda s: float((s > heat_c).sum())),
        "heavy_rain_days": (g["PRECTOTCORR"].apply(lambda s: float((s > heavy_thr).sum()))
                            if heavy_thr is not None else np.nan),
        "water_balance_mm": g["PRECTOTCORR"].sum(min_count=1) - g["ET0"].sum(min_count=1),
    })
    if lethal_c is not None:
        out["lethal_cold_days"] = g["T2M_MIN"].apply(lambda s: float((s < lethal_c).sum()))
    return out


def month_stats(ref: pd.Series) -> pd.DataFrame:
    """Mean, SD (ddof=1) and number of years per calendar month of a monthly PeriodIndex series."""
    v = ref.dropna()
    g = v.groupby(v.index.month)
    stats = pd.DataFrame({"mean": g.mean(), "sd": g.std(ddof=1), "n": g.count()})
    return stats.reindex(range(1, 13))


def risk_z(values: pd.Series, stats: pd.DataFrame, higher_is_worse: bool) -> pd.Series:
    """Standardised anomaly of each month vs the baseline month, oriented so + = worse, capped."""
    m = values.index.month
    mean = stats["mean"].reindex(m).to_numpy()
    sd = stats["sd"].reindex(m).to_numpy()
    n = stats["n"].reindex(m).fillna(0).to_numpy()
    x = values.to_numpy(dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (x - mean) / sd
    flat = ~(sd > 0)  # SD 0 or NaN
    diff = x - mean
    z = np.where(flat & (np.abs(diff) < 1e-9), 0.0, z)
    z = np.where(flat & (np.abs(diff) >= 1e-9), np.sign(diff) * Z_CAP, z)
    z = np.where((n < MIN_YEARS) | np.isnan(x), np.nan, z)
    if not higher_is_worse:
        z = -z
    return pd.Series(np.clip(z, -Z_CAP, Z_CAP), index=values.index)


def _annual(values: pd.Series, how: str) -> pd.Series:
    g = values.groupby(values.index.year)
    return g.sum(min_count=1) if how == "sum" else g.mean()


def _r(v, d):
    return None if v is None or not np.isfinite(v) else round(float(v), d)


def layer_block(spec: dict, base: pd.Series, values: pd.Series, years: list[int]) -> dict:
    """Arrays aligned with `years` x 12 months, plus climatology and annual anomaly."""
    hiw = spec["higher_is_worse"]
    stats = month_stats(base)
    z = risk_z(values, stats, hiw)
    d = spec["decimals"]
    grid_v, grid_z = [], []
    for y in years:
        idx = [pd.Period(year=y, month=mo, freq="M") for mo in range(1, 13)]
        grid_v.append([_r(values.get(p), d) for p in idx])
        grid_z.append([_r(z.get(p), 2) for p in idx])

    # Annual: sum (counts, water balance) or mean (state variables) vs baseline years.
    how = spec["annual"]
    base_ann = _annual(base, how)
    val_ann = _annual(values, how)
    # A year counts only if all months it needs are present in the baseline sense.
    months_present = values.groupby(values.index.year).count()
    need = 12 if how == "sum" else spec.get("min_months", 6)
    val_ann = val_ann.where(months_present.reindex(val_ann.index).fillna(0) >= need)
    base_ok = base.groupby(base.index.year).count()
    base_ann = base_ann.where(base_ok.reindex(base_ann.index).fillna(0) >= need).dropna()
    mu, sd = (base_ann.mean(), base_ann.std(ddof=1)) if len(base_ann) >= MIN_YEARS else (np.nan, np.nan)
    ann_z = (val_ann - mu) / sd if sd and sd > 0 else val_ann * np.nan
    if not hiw:
        ann_z = -ann_z
    return {
        **{k: spec[k] for k in ("id", "unit", "kind", "type", "source", "observation",
                                "scenario_applies", "higher_is_worse", "threshold", "assumption")},
        "label": spec["label"],
        "climatology": [_r(stats["mean"].get(mo), d + 1) for mo in range(1, 13)],
        "climatology_years": [int(stats["n"].get(mo)) if np.isfinite(stats["n"].get(mo)) else 0
                              for mo in range(1, 13)],
        "values": grid_v,
        "risk_z": grid_z,
        "annual": [_r(val_ann.get(y), d) for y in years],
        "annual_risk_z": [_r(np.clip(ann_z.get(y), -Z_CAP, Z_CAP), 2) if y in ann_z.index else None
                          for y in years],
        "annual_baseline_mean": _r(mu, d),
        "annual_how": how,
    }


def build(base_df: pd.DataFrame, df: pd.DataFrame, sat_table: pd.DataFrame | None,
          heat: dict, lethal: dict | None) -> dict:
    """All risk layers.

    base_df: baseline daily frame (with ET0) — defines the climatology and R95p.
    df: the frame to evaluate (baseline or scenario).
    sat_table: stage 3 monthly table (PeriodIndex) with 'smap_sm' and 'ndvi', or None.
    heat: {"threshold_c", "source", "assumption"}; lethal: {"threshold_c", "source"} or None.
    """
    heavy_thr = heavy_rain_threshold(base_df["PRECTOTCORR"])
    lethal_c = lethal["threshold_c"] if lethal else None
    base_m = monthly_climate(base_df, heat["threshold_c"], lethal_c, heavy_thr)
    val_m = monthly_climate(df, heat["threshold_c"], lethal_c, heavy_thr)
    years = sorted(set(df.index.year))

    clim_common = {"kind": "count", "type": "rule", "observation": False, "scenario_applies": True,
                   "higher_is_worse": True, "unit": "days", "decimals": 0, "annual": "sum",
                   "source": "NASA POWER daily (MERRA-2), ~0.5° grid"}
    specs = [
        clim_common | {"id": "frost_days", "label": "Frost days (Tmin < 0 °C)",
                       "threshold": {"value": FROST_C, "unit": "°C", "source": "rule (climate profile)"},
                       "assumption": False},
        clim_common | {"id": "hot_days",
                       "label": f"Hot days (Tmax > {heat['threshold_c']:g} °C)",
                       "threshold": {"value": heat["threshold_c"], "unit": "°C", "source": heat["source"]},
                       "assumption": heat["assumption"]},
        clim_common | {"id": "heavy_rain_days", "label": "Heavy-rain days (> R95p of wet days)",
                       "threshold": {"value": None if heavy_thr is None else round(heavy_thr, 1), "unit": "mm/day",
                                     "source": "ETCCDI R95p style, baseline wet days (P >= 1 mm)"},
                       "assumption": False},
        clim_common | {"id": "water_balance_mm", "label": "Water balance P - ET0", "kind": "amount",
                       "type": "physics", "unit": "mm", "higher_is_worse": False,
                       "threshold": None, "assumption": False,
                       "source": "NASA POWER rain (or IMERG-scaled) - FAO-56 ET0"},
    ]
    if lethal:
        specs.insert(1, clim_common | {
            "id": "lethal_cold_days", "label": f"Lethal cold days (Tmin < {lethal['threshold_c']:g} °C)",
            "threshold": {"value": lethal["threshold_c"], "unit": "°C", "source": lethal["source"]},
            "assumption": False})

    layers = [layer_block(s, base_m[s["id"]], val_m[s["id"]], years) for s in specs
              if base_m[s["id"]].notna().any()]

    sat_specs = [
        {"id": "smap_sm", "label": "SMAP surface soil moisture (observed, top ~5 cm)", "unit": "m³/m³",
         "decimals": 3, "source": "NASA SMAP SPL3SMP_E 005+006, 9 km", "min_months": 6},
        {"id": "ndvi", "label": "MODIS NDVI (1 km mean)", "unit": "NDVI", "decimals": 3,
         "source": "NASA MODIS MOD13Q1 v6.1", "min_months": 8},
    ]
    missing = []
    for s in sat_specs:
        col = None if sat_table is None or s["id"] not in sat_table else sat_table[s["id"]]
        if col is None or col.notna().sum() == 0:
            missing.append(s["id"])
            continue
        spec = s | {"kind": "anomaly", "type": "stat", "observation": True, "scenario_applies": False,
                    "higher_is_worse": False, "threshold": None, "assumption": False, "annual": "mean"}
        col = col[(col.index.year >= years[0]) & (col.index.year <= years[-1])]
        layers.append(layer_block(spec, col, col, years))

    return {"years": years, "layers": layers, "missing_layers": missing,
            "risk_z_flag": RISK_Z_FLAG, "min_years": MIN_YEARS, "z_cap": Z_CAP}
