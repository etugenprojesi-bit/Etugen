"""Scenario sliders (stage 5): a sensitivity test, not a climate projection.

"Delta change" perturbation of the observed daily record: every day gets
+delta_t °C on Tmax, Tmin and T2M, and its precipitation is multiplied by
(1 + delta_p / 100). ET0 is then recomputed with FAO-56 Penman-Monteith.

Assumptions (also in docs/METHOD.md):
* relative humidity, wind and radiation stay as observed (so the actual vapour
  pressure rises with temperature, as with constant RH); the daily RHmin used
  for the Kc climate adjustment (FAO-56 eq. 62/65) is kept from the observed record;
* the day-to-day pattern and the number of wet days do not change; only the
  amounts and the temperature level shift;
* slider ranges are UI limits chosen for the demo, not scenario values from
  any climate model.
"""

from __future__ import annotations

import pandas as pd

from app.features.climate import add_derived

DELTA_T_RANGE = (-2.0, 4.0)     # assumption: slider limits, °C
DELTA_P_RANGE = (-30.0, 30.0)   # assumption: slider limits, %
TEMP_COLUMNS = ("T2M", "T2M_MAX", "T2M_MIN")


def is_active(delta_t: float, delta_p_pct: float) -> bool:
    return bool(delta_t) or bool(delta_p_pct)


def perturb(daily: pd.DataFrame, delta_t: float, delta_p_pct: float) -> pd.DataFrame:
    """Raw POWER daily frame with the deltas applied (no derived columns)."""
    lo_t, hi_t = DELTA_T_RANGE
    lo_p, hi_p = DELTA_P_RANGE
    if not (lo_t <= delta_t <= hi_t) or not (lo_p <= delta_p_pct <= hi_p):
        raise ValueError(f"delta_t must be in {DELTA_T_RANGE}, delta_p in {DELTA_P_RANGE}")
    df = daily.copy()
    for c in TEMP_COLUMNS:
        if c in df:
            df[c] = df[c] + delta_t
    df["PRECTOTCORR"] = df["PRECTOTCORR"] * (1.0 + delta_p_pct / 100.0)
    return df


def apply(daily: pd.DataFrame, delta_t: float, delta_p_pct: float,
          elevation_m: float, lat: float) -> pd.DataFrame:
    """Perturbed frame with TMEAN and a recomputed ET0 (RHmin as observed: constant RH)."""
    df = add_derived(perturb(daily, delta_t, delta_p_pct), elevation_m, lat)
    if "RHMIN" in df:
        df["RHMIN"] = add_derived(daily, elevation_m, lat)["RHMIN"]
    return df
