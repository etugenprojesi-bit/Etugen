"""Slope steepness factor for the erosion sub-score (stage 3).

RUSLE slope steepness factor S, McCool et al. (1987), as given in
Renard et al. (1997), USDA Agriculture Handbook 703, chapter 4, p. 107:

    S = 10.8 sin(theta) + 0.03     for s <  9 %      [4-4]
    S = 16.8 sin(theta) - 0.50     for s >= 9 %      [4-5]

(s = slope in percent, theta = slope angle). The RUSLE unit plot has a 9 %
slope, where S ~ 1.0; we divide by S(9 %) so 1.0 means "as steep as the unit
plot". Slope comes from NASADEM (30 m) over the 0.05° analysis cell, so it
describes the surroundings of the point, not one field.

Flat-terrain rule (decision 2026-11-14, docs/METHOD.md "Slope (erosion)"): NASADEM heights
are whole metres, so the smallest non-zero 30 m slope is one 1 m step across two pixels,
atan(1 / 61.7 m) = 0.93 deg (seen as the 10th percentile at all demo points). When the
median pixel slope is at most two such steps, the slope is not resolved by the DEM (height
rounding and noise dominate) and the cell-scale gradient is used instead: the 10-90 %
elevation range over half the 0.05 deg cell (assumption).
"""

from __future__ import annotations

import math

UNIT_PLOT_SLOPE_PCT = 9.0
PIXEL_M = 30.87                      # NASADEM 1 arc-second along a meridian
DEM_STEP_DEG = math.degrees(math.atan(1.0 / (2 * PIXEL_M)))   # one 1 m height step, 0.93 deg
FLAT_STEPS = 2                        # assumption: <= 2 height steps = not resolved
HALF_CELL_M = 0.025 * 111_320         # half of the 0.05 deg analysis cell along a meridian


def rusle_s(slope_deg: float) -> float:
    theta = math.radians(slope_deg)
    s_pct = math.tan(theta) * 100.0
    if s_pct < UNIT_PLOT_SLOPE_PCT:
        return 10.8 * math.sin(theta) + 0.03
    return 16.8 * math.sin(theta) - 0.50


S_UNIT_PLOT = rusle_s(math.degrees(math.atan(UNIT_PLOT_SLOPE_PCT / 100.0)))


def relative_s(slope_deg: float) -> float:
    """S relative to the 9 % unit plot (1.0 at 9 %)."""
    return rusle_s(slope_deg) / S_UNIT_PLOT


def fall_direction(plane: dict | None) -> dict | None:
    """Main downhill direction of the cell from the fitted plane (azimuth, degrees clockwise
    from north) and the across-slope (contour) row direction, 0-180 degrees."""
    if not plane or plane.get("dz_de") is None or plane.get("dz_dn") is None:
        return None
    ge, gn = plane["dz_de"], plane["dz_dn"]
    if ge == 0 and gn == 0:
        return None
    down = math.degrees(math.atan2(-ge, -gn)) % 360
    return {"downhill_azimuth_deg": round(down), "contour_rows_azimuth_deg": round((down + 90) % 180),
            "plane_slope_pct": round(math.hypot(ge, gn) * 100, 2)}


def slope_summary(stats: dict, plane: dict | None = None) -> dict:
    """Summary used by the API and the erosion score, from the NASADEM layer stats."""
    deg = stats.get("slope_deg_p50")
    if deg is None:
        return {"status": "missing"}
    pixel_deg = deg
    lo, hi = stats.get("elevation_p10"), stats.get("elevation_p90")
    flat = lo is not None and hi is not None and deg <= FLAT_STEPS * DEM_STEP_DEG * 1.001
    if flat:
        deg = min(deg, math.degrees(math.atan(max(0.0, hi - lo) / HALF_CELL_M)))
    return {
        "status": "ok",
        "flat_terrain": flat,
        "slope_deg_median_pixels": round(pixel_deg, 2),
        "slope_method": ("flat terrain: 10-90 % elevation range over half the cell (pixel slope below "
                         "the DEM's 1 m height resolution; assumption)") if flat else "median of 30 m pixel slopes",
        "slope_deg_median": round(deg, 2),
        "slope_pct_median": round(math.tan(math.radians(deg)) * 100, 1),
        "slope_deg_p90": None if stats.get("slope_deg_p90") is None else round(stats["slope_deg_p90"], 2),
        "elevation_m_median": None if stats.get("elevation_p50") is None else round(stats["elevation_p50"]),
        "rusle_s": round(rusle_s(deg), 3),
        "relative_s": round(relative_s(deg), 3),
        # contour rows only matter where the slope is resolved (not on flat terrain)
        "fall": None if flat else fall_direction(plane),
        "source": "NASADEM 30 m, 0.05° analysis cell, median; RUSLE S (McCool et al. 1987; AH-703 eq. 4-4/4-5)",
    }
