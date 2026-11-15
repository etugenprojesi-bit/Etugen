"""ISRIC SoilGrids v2.0 water retention at a point (fallow / soil water balance).

Layers wv0010, wv0033 and wv1500 (volumetric water content at 10, 33 and
1500 kPa; Turek et al. 2023, doi:10.1016/j.iswcr.2022.08.001), six standard
depths, plus topsoil sand/silt/clay. Licence CC BY 4.0. Verified by
scripts/probe/probe_soilgrids_water.py; see docs/DATA_SOURCES.md §3b.

Access: OGC WCS 2.0.1 at maps.isric.org (no authentication). A 0.1° window is
requested (smaller windows came back all-zero during probing) and the median
of the valid 250 m pixels within 1 km of the rounded point is used. 0 = nodata
(urban, water).

Units (ISRIC SoilGrids FAQ, conversion factors): wv* mapped value is
10^-3 cm3/cm3 = 1 mm water per m soil; sand/silt/clay g/kg.

Order: SQLite cache -> network -> demo cache, like POWER and Earth Engine.
"""

from __future__ import annotations

import asyncio
import gzip
import io
import json
import math
from dataclasses import dataclass
from pathlib import Path

import httpx
import numpy as np

from app.config import demo_cache_first
from app.cache.store import ResponseCache, cache_key
from app.sources import SourceError

URL = "https://maps.isric.org/mapserv"
WATER = ("wv0010", "wv0033", "wv1500")
TEXTURE = ("sand", "silt", "clay")
DEPTHS = ("0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm")
TOP_DEPTHS = ("0-5cm", "5-15cm")
BOUNDS_M = {"0-5cm": (0.0, 0.05), "5-15cm": (0.05, 0.15), "15-30cm": (0.15, 0.30),
            "30-60cm": (0.30, 0.60), "60-100cm": (0.60, 1.00), "100-200cm": (1.00, 2.00)}
MAX_DEPTH_M = 2.0
HALF_WINDOW_DEG = 0.05
BUFFER_KM = 1.0
SCHEMA = 1
FOOTPRINT = "SoilGrids 250 m pixels, median within 1 km of the analysis point"

# Assumption (labelled in docs/METHOD.md): field capacity = water content at 33 kPa,
# wilting point = at 1500 kPa. FAO-56 defines both physically, not by suction.
FC_LAYER = "wv0033"
WP_LAYER = "wv1500"


def _params(prop: str, depth: str, lat: float, lon: float) -> list[tuple[str, str]]:
    h = HALF_WINDOW_DEG
    return [
        ("map", f"/map/{prop}.map"), ("SERVICE", "WCS"), ("VERSION", "2.0.1"),
        ("REQUEST", "GetCoverage"), ("COVERAGEID", f"{prop}_{depth}_mean"), ("FORMAT", "image/tiff"),
        ("SUBSET", f"long({lon - h},{lon + h})"), ("SUBSET", f"lat({lat - h},{lat + h})"),
        ("SUBSETTINGCRS", "http://www.opengis.net/def/crs/EPSG/0/4326"),
        ("OUTPUTCRS", "http://www.opengis.net/def/crs/EPSG/0/4326"),
    ]


def buffer_median(content: bytes, lat: float, lon: float) -> tuple[float | None, int]:
    """Median of valid (> 0) pixels within BUFFER_KM of the point, and their count."""
    import tifffile  # imported lazily: only needed for live requests

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
    vals = arr[(np.hypot(dx, dy) <= BUFFER_KM) & (arr > 0)]
    return (float(np.median(vals)) if vals.size else None), int(vals.size)


async def fetch_raw(lat: float, lon: float) -> dict:
    """Live WCS requests. Returns {"values": {prop: {depth: raw}}, "pixels": ..., "errors": {...}}."""
    jobs = [(p, d) for p in WATER for d in DEPTHS] + [(p, d) for p in TEXTURE for d in TOP_DEPTHS]
    async with httpx.AsyncClient(timeout=60, limits=httpx.Limits(max_connections=8)) as client:
        responses = await asyncio.gather(*(client.get(URL, params=_params(p, d, lat, lon)) for p, d in jobs),
                                         return_exceptions=True)
    values: dict[str, dict[str, float | None]] = {}
    pixels: dict[str, int] = {}
    errors: dict[str, str] = {}
    for (p, d), r in zip(jobs, responses):
        values.setdefault(p, {})[d] = None
        if isinstance(r, Exception):
            errors[f"{p}_{d}"] = repr(r)[:200]
            continue
        if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image/tiff"):
            errors[f"{p}_{d}"] = f"HTTP {r.status_code} {r.headers.get('content-type', '')}"[:200]
            continue
        med, n = buffer_median(r.content, lat, lon)
        values[p][d] = med
        pixels[f"{p}_{d}"] = n
        if med is None:
            errors[f"{p}_{d}"] = "no valid pixel within 1 km (masked: urban/water?)"
    return {"schema": SCHEMA, "lat": lat, "lon": lon, "values": values, "pixels": pixels, "errors": errors}


def demo_cache_file(demo_dir: Path, lat: float, lon: float) -> Path:
    return demo_dir / f"soilgrids_{lat:.2f}_{lon:.2f}.json.gz"


def _demo(demo_dir: Path | None, lat: float, lon: float) -> dict | None:
    if demo_dir is not None and (f := demo_cache_file(demo_dir, lat, lon)).exists():
        return json.loads(gzip.decompress(f.read_bytes()))
    return None


async def load_point(lat: float, lon: float, cache: ResponseCache | None = None,
                     demo_dir: Path | None = None) -> tuple[dict, str]:
    """Raw values for a rounded point and their origin ("cache" | "network" | "demo_cache").

    Raises SourceError when nothing usable is available. Results with errors are not cached.
    """
    key = cache_key("soilgrids_water", lat, lon, schema=SCHEMA)
    if cache is not None and (hit := cache.get(key)) is not None:
        return hit, "cache"
    if demo_cache_first() and (demo := _demo(demo_dir, lat, lon)) is not None:
        return demo, "demo_cache"
    try:
        raw = await fetch_raw(lat, lon)
    except (httpx.HTTPError, OSError, SourceError) as e:
        if (demo := _demo(demo_dir, lat, lon)) is not None:
            return demo, "demo_cache"
        raise SourceError(f"SoilGrids request failed: {e!r}") from e
    if raw["errors"]:
        if (demo := _demo(demo_dir, lat, lon)) is not None:
            return demo, "demo_cache"
        raise SourceError(f"SoilGrids: {raw['errors']}")
    if cache is not None:
        cache.put(key, raw)
    return raw, "network"


def _layer_mean(values: dict[str, float | None], top: float, bottom: float) -> float | None:
    """Thickness-weighted mean of the depth layers over [top, bottom] m (None if any is missing)."""
    num = den = 0.0
    for d, (a, b) in BOUNDS_M.items():
        overlap = max(0.0, min(b, bottom) - max(a, top))
        if overlap > 0:
            v = values.get(d)
            if v is None:
                return None
            num += v * overlap
            den += overlap
    return num / den if den else None


@dataclass(frozen=True)
class SoilWater:
    """Water retention at a point, from SoilGrids raw values."""
    values: dict          # {prop: {depth: mapped value}}
    origin: str

    def theta(self, layer: str, top: float, bottom: float) -> float | None:
        """Mean volumetric water content (m3/m3) of a wv* layer over [top, bottom] m."""
        v = _layer_mean(self.values.get(layer, {}), top, min(bottom, MAX_DEPTH_M))
        return None if v is None else v / 1000.0

    def taw_mm(self, root_depth_m: float, fc_layer: str = FC_LAYER) -> float | None:
        """FAO-56 eq. 82: TAW = 1000 (theta_FC - theta_WP) Zr. Zr is capped at 2 m (deepest layer)."""
        zr = min(root_depth_m, MAX_DEPTH_M)
        fc, wp = self.theta(fc_layer, 0.0, zr), self.theta(WP_LAYER, 0.0, zr)
        return None if fc is None or wp is None else max(0.0, 1000.0 * (fc - wp) * zr)

    def tew_mm(self, ze_m: float = 0.10) -> float | None:
        """FAO-56 eq. 73: TEW = 1000 (theta_FC - 0.5 theta_WP) Ze, from the top layers."""
        fc, wp = self.theta(FC_LAYER, 0.0, ze_m), self.theta(WP_LAYER, 0.0, ze_m)
        return None if fc is None or wp is None else max(0.0, 1000.0 * (fc - 0.5 * wp) * ze_m)

    def texture_pct(self) -> dict[str, float | None]:
        """Topsoil (0-15 cm) sand/silt/clay in %, for reporting."""
        out = {}
        for p in TEXTURE:
            v = _layer_mean(self.values.get(p, {}), 0.0, 0.15)
            out[p] = None if v is None else round(v / 10.0, 1)
        return out


def parse(raw: dict, origin: str) -> SoilWater:
    return SoilWater(raw["values"], origin)
