"""Probe: SoilGrids v2.0 volumetric water retention (wv0010 / wv0033 / wv1500) via WCS.

Layers from Turek et al. (2023), Int. Soil Water Conserv. Res. 11(2):225-239,
doi:10.1016/j.iswcr.2022.08.001, published by ISRIC as part of SoilGrids 2.0
(CC BY 4.0). Same WCS endpoint and pixel handling as probe_soilgrids_wcs.py.

Units (ISRIC SoilGrids FAQ, "conversion factors"): mapped value is
10^-3 cm3/cm3 = 0.1 vol% = 1 mm of water per m of soil, conversion factor 10.
So (wv0033 - wv1500) in mapped units is directly mm water per m soil.

What this probe checks, for the three demo points:
  1. all 3 x 6 coverages answer and give valid pixels within 1 km;
  2. total available water TAW = 1000 (theta_FC - theta_WP) Zr (FAO-56 eq. 82)
     for Zr = 0.6 / 1.0 / 1.5 / 1.8 m, with theta_FC at 33 kPa and theta_WP
     at 1500 kPa (the convention used for these maps; 10 kPa shown as a
     sensitivity case for coarse soils);
  3. total evaporable water TEW = 1000 (theta_FC - 0.5 theta_WP) Ze (FAO-56
     eq. 73) with Ze = 0.10 m, from the 0-5 and 5-15 cm layers;
  4. topsoil sand/silt/clay (to place the point in a FAO-56 Table 19 class
     for REW) and a plausibility check of theta_FC / theta_WP against the
     Table 19 range of that class.

Run: backend/.venv/Scripts/python scripts/probe/probe_soilgrids_water.py
"""

from __future__ import annotations

import asyncio

import httpx

from _common import DEMO_POINTS, Timer, report, save
from probe_soilgrids_wcs import URL, buffer_median, params

WATER = ["wv0010", "wv0033", "wv1500"]
TEXTURE = ["sand", "silt", "clay"]
DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
TOP_DEPTHS = ["0-5cm", "5-15cm"]
BOUNDS_M = {"0-5cm": (0.0, 0.05), "5-15cm": (0.05, 0.15), "15-30cm": (0.15, 0.30),
            "30-60cm": (0.30, 0.60), "60-100cm": (0.60, 1.00), "100-200cm": (1.00, 2.00)}
ROOT_DEPTHS_M = [0.6, 1.0, 1.5, 1.8]
ZE_M = 0.10


def layer_mean(values: dict[str, float], top: float, bottom: float) -> float | None:
    """Thickness-weighted mean of SoilGrids depth layers over [top, bottom] m."""
    num = den = 0.0
    for d, (a, b) in BOUNDS_M.items():
        overlap = max(0.0, min(b, bottom) - max(a, top))
        if overlap > 0:
            if values.get(d) is None:
                return None
            num += values[d] * overlap
            den += overlap
    return num / den if den else None


async def probe_point(client: httpx.AsyncClient, key: str, lat: float, lon: float) -> bool:
    jobs = [(p, d) for p in WATER for d in DEPTHS] + [(p, d) for p in TEXTURE for d in TOP_DEPTHS]
    with Timer() as t:
        responses = await asyncio.gather(
            *(client.get(URL, params=params(p, d, lat, lon)) for p, d in jobs), return_exceptions=True)
    raw: dict[str, dict[str, float | None]] = {}
    ok, errors = True, {}
    for (p, d), r in zip(jobs, responses):
        if isinstance(r, Exception) or r.status_code != 200 or not r.headers.get(
                "content-type", "").startswith("image/tiff"):
            ok = False
            errors[f"{p} {d}"] = f"ERROR {r!r}"[:200]
            raw.setdefault(p, {})[d] = None
            continue
        med, n_valid, n_buf, _ = buffer_median(r.content, lat, lon)
        raw.setdefault(p, {})[d] = med
        if med is None:
            ok = False
            errors[f"{p} {d}"] = f"no valid pixel ({n_buf} px in buffer)"

    # mapped units -> m3/m3
    theta = {p: {d: (v / 1000 if v is not None else None) for d, v in raw[p].items()} for p in WATER}
    taw = {}
    for zr in ROOT_DEPTHS_M:
        fc33, fc10, wp = (layer_mean(theta[p], 0, zr) for p in ("wv0033", "wv0010", "wv1500"))
        taw[f"{zr} m"] = {
            "TAW_mm_33kPa": None if fc33 is None or wp is None else round(1000 * (fc33 - wp) * zr, 1),
            "TAW_mm_10kPa": None if fc10 is None or wp is None else round(1000 * (fc10 - wp) * zr, 1),
        }
    fc_top, wp_top = layer_mean(theta["wv0033"], 0, ZE_M), layer_mean(theta["wv1500"], 0, ZE_M)
    tew = None if fc_top is None or wp_top is None else round(1000 * (fc_top - 0.5 * wp_top) * ZE_M, 1)
    texture_top = {p: (None if (v := layer_mean({d: (x / 10 if x is not None else None)
                                                 for d, x in raw[p].items()}, 0, 0.15)) is None else round(v, 1))
                   for p in TEXTURE}  # g/kg -> %
    out = {
        "point": {"lat": lat, "lon": lon},
        "raw_mapped_units": raw,
        "theta_m3m3_0_15cm": {"fc_33kPa": fc_top, "wp_1500kPa": wp_top},
        "TAW_by_root_depth": taw,
        "TEW_mm_Ze_0.10": tew,
        "texture_0_15cm_percent": texture_top,
        "errors": errors,
    }
    save(f"soilgrids_water_{key}.json", out)
    report(f"SoilGrids water retention {key}", ok, {
        "requests": len(jobs), "seconds_parallel": f"{t.seconds:.1f}",
        "theta_FC33 / theta_WP 0-15cm": f"{fc_top:.3f} / {wp_top:.3f}" if fc_top and wp_top else None,
        "TEW (Ze 0.10 m, eq. 73)": tew,
        "TAW 33 kPa by Zr": {k: v["TAW_mm_33kPa"] for k, v in taw.items()},
        "TAW 10 kPa by Zr": {k: v["TAW_mm_10kPa"] for k, v in taw.items()},
        "sand/silt/clay % 0-15cm": texture_top,
        **errors,
    })
    return ok


async def main() -> None:
    limits = httpx.Limits(max_connections=8)
    async with httpx.AsyncClient(timeout=60, limits=limits) as client:
        results = [await probe_point(client, k, p["lat"], p["lon"]) for k, p in DEMO_POINTS.items()]
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    asyncio.run(main())
