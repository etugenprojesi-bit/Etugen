"""Probe: ISRIC SoilGrids v2.0 via OGC WCS 2.0.1 (maps.isric.org, no authentication).

The REST point API (probe_soilgrids.py) works but takes 30-60 s per point;
WCS returns a small GeoTIFF per layer in ~0.5 s. We request a 0.1 deg window
reprojected to EPSG:4326 and take the median of valid pixels within 1 km of
the point (0 = nodata / masked, e.g. urban or water).

Note: very small windows (~0.02 deg) came back as all-zero tiles during
testing, so the window is deliberately larger than the analysis buffer.

Run: backend/.venv/Scripts/python scripts/probe/probe_soilgrids_wcs.py
"""

from __future__ import annotations

import asyncio
import io
import math

import httpx
import numpy as np
import tifffile

from _common import DEMO_POINTS, Timer, report, save

URL = "https://maps.isric.org/mapserv"
PROPERTIES = ["clay", "sand", "silt", "phh2o", "soc", "bdod", "cec"]
DEPTHS = ["0-5cm", "5-15cm", "15-30cm"]
HALF_WINDOW_DEG = 0.05
BUFFER_KM = 1.0


def params(prop: str, depth: str, lat: float, lon: float) -> list[tuple[str, str]]:
    h = HALF_WINDOW_DEG
    return [
        ("map", f"/map/{prop}.map"), ("SERVICE", "WCS"), ("VERSION", "2.0.1"),
        ("REQUEST", "GetCoverage"), ("COVERAGEID", f"{prop}_{depth}_mean"),
        ("FORMAT", "image/tiff"),
        ("SUBSET", f"long({lon - h},{lon + h})"), ("SUBSET", f"lat({lat - h},{lat + h})"),
        ("SUBSETTINGCRS", "http://www.opengis.net/def/crs/EPSG/0/4326"),
        ("OUTPUTCRS", "http://www.opengis.net/def/crs/EPSG/0/4326"),
    ]


def buffer_median(content: bytes, lat: float, lon: float) -> tuple[float | None, int, int, tuple]:
    with tifffile.TiffFile(io.BytesIO(content)) as tif:
        arr = tif.asarray().astype(float)
        tags = tif.pages[0].tags
        sx, sy, _ = tags["ModelPixelScaleTag"].value
        _, _, _, x0, y0, _ = tags["ModelTiepointTag"].value
    rows, cols = np.indices(arr.shape)
    plon = x0 + (cols + 0.5) * sx
    plat = y0 - (rows + 0.5) * sy
    dy = (plat - lat) * 111.32
    dx = (plon - lon) * 111.32 * math.cos(math.radians(lat))
    in_buf = np.hypot(dx, dy) <= BUFFER_KM
    vals = arr[in_buf & (arr > 0)]
    med = float(np.median(vals)) if vals.size else None
    return med, int(vals.size), int(in_buf.sum()), (sx, sy)


async def probe_point(client: httpx.AsyncClient, key: str, lat: float, lon: float) -> bool:
    jobs = [(p, d) for p in PROPERTIES for d in DEPTHS]
    with Timer() as t:
        responses = await asyncio.gather(
            *(client.get(URL, params=params(p, d, lat, lon)) for p, d in jobs),
            return_exceptions=True,
        )
    out, details, ok = {}, {}, True
    for (p, d), r in zip(jobs, responses):
        if isinstance(r, Exception) or r.status_code != 200 or not r.headers.get(
            "content-type", ""
        ).startswith("image/tiff"):
            ok = False
            details[f"{p} {d}"] = f"ERROR {r!r}"[:200]
            continue
        med, n_valid, n_buf, scale = buffer_median(r.content, lat, lon)
        out[f"{p}_{d}"] = {"median_raw": med, "valid_px": n_valid, "buffer_px": n_buf,
                           "pixel_deg": scale}
        if d == "0-5cm":
            details[p] = f"median_raw={med} ({n_valid}/{n_buf} valid px in {BUFFER_KM} km)"
    save(f"soilgrids_wcs_{key}.json", out)
    report(f"SoilGrids WCS {key}", ok, {"requests": len(jobs), "seconds_parallel": f"{t.seconds:.1f}", **details})
    return ok


async def main() -> None:
    limits = httpx.Limits(max_connections=8)
    async with httpx.AsyncClient(timeout=60, limits=limits) as client:
        results = [await probe_point(client, k, p["lat"], p["lon"]) for k, p in DEMO_POINTS.items()]
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    asyncio.run(main())
