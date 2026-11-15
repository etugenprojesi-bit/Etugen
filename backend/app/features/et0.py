"""FAO-56 Penman-Monteith reference evapotranspiration (daily).

Allen et al. (1998), FAO Irrigation and Drainage Paper 56, chapter 3-4.
Equation numbers refer to FAO-56. All functions accept numpy arrays.
Physics, not machine learning.
"""

from __future__ import annotations

import numpy as np

ALBEDO = 0.23            # grass reference crop (eq. 38)
SIGMA = 4.903e-9         # Stefan-Boltzmann, MJ K-4 m-2 day-1 (eq. 39)
GSC = 0.0820             # solar constant, MJ m-2 min-1 (eq. 21)


def atmospheric_pressure(elevation_m):
    """Eq. 7, kPa."""
    return 101.3 * ((293.0 - 0.0065 * np.asarray(elevation_m, float)) / 293.0) ** 5.26


def psychrometric_constant(pressure_kpa):
    """Eq. 8, kPa/°C."""
    return 0.665e-3 * np.asarray(pressure_kpa, float)


def sat_vapour_pressure(t_c):
    """Eq. 11, kPa."""
    t = np.asarray(t_c, float)
    return 0.6108 * np.exp(17.27 * t / (t + 237.3))


def svp_slope(t_c):
    """Eq. 13, kPa/°C."""
    t = np.asarray(t_c, float)
    return 4098.0 * sat_vapour_pressure(t) / (t + 237.3) ** 2


def actual_vapour_pressure_rhmean(rh_mean_pct, tmax_c, tmin_c):
    """Eq. 19, kPa — used because NASA POWER provides daily mean RH only."""
    es = (sat_vapour_pressure(tmax_c) + sat_vapour_pressure(tmin_c)) / 2.0
    return np.asarray(rh_mean_pct, float) / 100.0 * es


def extraterrestrial_radiation(lat_deg, doy):
    """Eq. 21-25, MJ m-2 day-1."""
    phi = np.radians(np.asarray(lat_deg, float))
    j = np.asarray(doy, float)
    dr = 1 + 0.033 * np.cos(2 * np.pi / 365 * j)                    # eq. 23
    delta = 0.409 * np.sin(2 * np.pi / 365 * j - 1.39)              # eq. 24
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1.0, 1.0))  # eq. 25 (polar-safe)
    return (24 * 60 / np.pi) * GSC * dr * (
        ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws)
    )


def clear_sky_radiation(ra, elevation_m):
    """Eq. 37, MJ m-2 day-1."""
    return (0.75 + 2e-5 * np.asarray(elevation_m, float)) * np.asarray(ra, float)


def net_longwave_radiation(tmax_c, tmin_c, ea_kpa, rs, rso):
    """Eq. 39, MJ m-2 day-1. Rs/Rso is limited to <= 1.0 as FAO-56 prescribes."""
    tk4 = ((np.asarray(tmax_c, float) + 273.16) ** 4 + (np.asarray(tmin_c, float) + 273.16) ** 4) / 2
    ratio = np.clip(np.asarray(rs, float) / np.asarray(rso, float), 0.0, 1.0)
    return SIGMA * tk4 * (0.34 - 0.14 * np.sqrt(ea_kpa)) * (1.35 * ratio - 0.35)


def et0_from_components(t_mean, u2, es, ea, delta, gamma, rn, g=0.0):
    """Eq. 6, mm/day."""
    num = 0.408 * delta * (rn - g) + gamma * 900.0 / (t_mean + 273.0) * u2 * (es - ea)
    return num / (delta + gamma * (1 + 0.34 * u2))


def et0_daily(tmax_c, tmin_c, rh_mean_pct, u2_ms, rs_mj, elevation_m, lat_deg, doy):
    """Daily ET0 (mm/day) from NASA POWER-style inputs. Soil heat flux G = 0 (eq. 42)."""
    tmax = np.asarray(tmax_c, float)
    tmin = np.asarray(tmin_c, float)
    t_mean = (tmax + tmin) / 2.0                     # eq. 9
    gamma = psychrometric_constant(atmospheric_pressure(elevation_m))
    es = (sat_vapour_pressure(tmax) + sat_vapour_pressure(tmin)) / 2.0
    ea = actual_vapour_pressure_rhmean(rh_mean_pct, tmax, tmin)
    ra = extraterrestrial_radiation(lat_deg, doy)
    rso = clear_sky_radiation(ra, elevation_m)
    rn = (1 - ALBEDO) * np.asarray(rs_mj, float) - net_longwave_radiation(tmax, tmin, ea, rs_mj, rso)
    et0 = et0_from_components(t_mean, np.asarray(u2_ms, float), es, ea, svp_slope(t_mean), gamma, rn)
    return np.maximum(et0, 0.0)
