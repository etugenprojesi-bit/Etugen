"""FAO-56 climate adjustment of the crop coefficients Kc_mid and Kc_end.

Allen et al. (1998), FAO Irrigation and Drainage Paper 56, chapter 6
(https://www.fao.org/4/X0490E/x0490e0b.htm), read in the original HTML and the
equation images; see docs/DATA_SOURCES.md §9. Physics, not machine learning.

* eq. 62: Kc_mid = Kc_mid(Tab) + [0.04 (u2 - 2) - 0.004 (RHmin - 45)] (h/3)^0.3
* eq. 65: the same for Kc_end, applied only when Kc_end(Tab) > 0.45
* u2, RHmin: means of the daily values over the mid-season (eq. 62) or the late
  season (eq. 65), as in the FAO-56 Annex 8 spreadsheet
* eq. 63: daily RHmin = 100 e°(Tdew) / e°(Tmax), Tdew from NASA POWER T2MDEW
* validity: 1 <= u2 <= 6 m/s, 20 <= RHmin <= 80 %, 0.1 < h < 10 m. FAO-56 says
  the limits "should be observed"; we clip the stage means to them
  (assumption). Below h = 0.1 m eq. 62 "should not be applied".
"""

from __future__ import annotations

import numpy as np

from app.features.et0 import sat_vapour_pressure

U2_LIMITS = (1.0, 6.0)        # m/s, FAO-56 eq. 62 / 65
RHMIN_LIMITS = (20.0, 80.0)   # %, FAO-56 eq. 62 / 65
H_MIN = 0.1                   # m: below this the crop behaves like grass, no adjustment
H_MAX = 10.0                  # m: upper validity limit (clipped, assumption)
KC_END_THRESHOLD = 0.45       # eq. 65 only when the tabulated Kc_end exceeds this


def rh_min_daily(tdew_c, tmax_c):
    """FAO-56 eq. 63, %. Capped at 100 (dew point above Tmax is not physical)."""
    rh = 100.0 * sat_vapour_pressure(tdew_c) / sat_vapour_pressure(tmax_c)
    return np.minimum(rh, 100.0)


def climate_term(u2: float, rh_min: float, h: float) -> float:
    """The additive term of eq. 62 / 65 with the validity limits applied (0 if h < H_MIN)."""
    if h is None or not np.isfinite(h) or h < H_MIN or not np.isfinite(u2) or not np.isfinite(rh_min):
        return 0.0
    u2 = min(max(u2, U2_LIMITS[0]), U2_LIMITS[1])
    rh_min = min(max(rh_min, RHMIN_LIMITS[0]), RHMIN_LIMITS[1])
    h = min(h, H_MAX)
    return (0.04 * (u2 - 2.0) - 0.004 * (rh_min - 45.0)) * (h / 3.0) ** 0.3


def kc_mid_adjusted(kc_mid_tab: float, u2: float, rh_min: float, h: float) -> float:
    """FAO-56 eq. 62 (u2, RHmin = mid-season means)."""
    return kc_mid_tab + climate_term(u2, rh_min, h)


def kc_end_adjusted(kc_end_tab: float, u2: float, rh_min: float, h: float) -> float:
    """FAO-56 eq. 65 (u2, RHmin = late-season means); unchanged when Kc_end(Tab) <= 0.45."""
    if kc_end_tab <= KC_END_THRESHOLD:
        return kc_end_tab
    return kc_end_tab + climate_term(u2, rh_min, h)


def stage_bounds(n_days: int, fractions: tuple[float, float, float, float]) -> tuple[int, int]:
    """Day offsets (start of mid-season, start of late season) of a season of n_days.

    Same stage proportions as engine.kc_curve (FAO-56 Table 11, scaled to the season).
    Both stages get at least one day where the season allows it.
    """
    f_ini, f_dev, f_mid, _ = fractions
    a = int(round((f_ini + f_dev) * n_days))
    b = int(round((f_ini + f_dev + f_mid) * n_days))
    a = min(max(a, 0), max(n_days - 1, 0))
    b = min(max(b, a + 1), n_days)
    return a, b


def season_kc(fractions, kc_mid_tab: float, kc_end_tab: float, h: float | None,
              u2: np.ndarray, rh_min: np.ndarray) -> tuple[float, float, dict]:
    """Adjusted (Kc_mid, Kc_end) for one season from its daily u2 and RHmin arrays.

    Returns the values and the stage means used (for reporting).
    """
    n = len(u2)
    a, b = stage_bounds(n, fractions)
    with np.errstate(all="ignore"):
        u_mid, rh_mid = float(np.nanmean(u2[a:b])), float(np.nanmean(rh_min[a:b]))
        late = slice(b, n) if b < n else slice(n - 1, n)  # season too short: last day
        u_late, rh_late = float(np.nanmean(u2[late])), float(np.nanmean(rh_min[late]))
    kmid = kc_mid_adjusted(kc_mid_tab, u_mid, rh_mid, h)
    kend = kc_end_adjusted(kc_end_tab, u_late, rh_late, h)
    return kmid, kend, {"u2_mid": u_mid, "rh_min_mid": rh_mid, "u2_late": u_late, "rh_min_late": rh_late}
