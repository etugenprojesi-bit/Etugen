"""NASA POWER daily point API client (no authentication).

Verified in scripts/probe/probe_power.py; see docs/DATA_SOURCES.md §1.
"""

from __future__ import annotations

import gzip
import json
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import numpy as np
import pandas as pd

from app.config import demo_cache_first
from app.cache.store import ResponseCache, cache_key
from app.sources import SourceError

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = [
    "T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN",
    # Dew point: daily RHmin for the FAO-56 Kc climate adjustment (eq. 63), DATA_SOURCES §9.
    "T2MDEW",
    # Model-based soil wetness (MERRA-2 land surface model), NOT SMAP observations.
    "GWETTOP", "GWETROOT",
]
RESOLUTION = "0.5° × 0.625° (MERRA-2 grid); solar ~1°"


@dataclass
class PowerData:
    daily: pd.DataFrame  # index: date; columns: PARAMETERS (fill values -> NaN)
    elevation_m: float
    api_version: str | None
    upstream_sources: list[str]
    origin: str  # "network" | "cache" | "demo_cache"
    meta: dict = field(default_factory=dict)


def parse(raw: dict, origin: str) -> PowerData:
    try:
        header = raw.get("header", {})
        fill = header.get("fill_value", -999.0)
        series = raw["properties"]["parameter"]
        frame = pd.DataFrame({p: pd.Series(series[p]) for p in PARAMETERS if p in series})
        frame.index = pd.to_datetime(frame.index, format="%Y%m%d")
        frame = frame.sort_index().replace(fill, np.nan).astype(float)
        elevation = float(raw["geometry"]["coordinates"][2])
    except (KeyError, IndexError, TypeError, ValueError) as e:
        raise SourceError(f"NASA POWER response could not be parsed: {e!r}") from e
    missing = [p for p in PARAMETERS if p not in frame.columns]
    if missing:
        raise SourceError(f"NASA POWER response lacks parameters: {missing}")
    return PowerData(
        daily=frame,
        elevation_m=elevation,
        api_version=(header.get("api") or {}).get("version"),
        upstream_sources=header.get("sources") or [],
        origin=origin,
    )


def demo_cache_file(demo_dir: Path, lat: float, lon: float) -> Path:
    return demo_dir / f"power_{lat:.2f}_{lon:.2f}.json.gz"


async def fetch_daily(
    client: httpx.AsyncClient,
    lat: float,
    lon: float,
    first_year: int,
    last_year: int,
    cache: ResponseCache | None = None,
    demo_dir: Path | None = None,
) -> PowerData:
    """Daily POWER data for complete years. Order: SQLite cache, network, demo cache."""
    start, end = f"{first_year}0101", f"{last_year}1231"
    key = cache_key("power_daily", lat, lon, start=start, end=end, params=",".join(PARAMETERS))
    if cache is not None and (hit := cache.get(key)) is not None:
        return parse(hit, "cache")
    if demo_cache_first() and demo_dir is not None and (f := demo_cache_file(demo_dir, lat, lon)).exists():
        return parse(json.loads(gzip.decompress(f.read_bytes())), "demo_cache")

    params = {"parameters": ",".join(PARAMETERS), "community": "AG", "latitude": lat,
              "longitude": lon, "start": start, "end": end, "format": "JSON"}
    try:
        response = await client.get(URL, params=params, timeout=60)
        response.raise_for_status()
        raw = response.json()
    except (httpx.HTTPError, json.JSONDecodeError) as network_error:
        if demo_dir is not None and (f := demo_cache_file(demo_dir, lat, lon)).exists():
            return parse(json.loads(gzip.decompress(f.read_bytes())), "demo_cache")
        raise SourceError(f"NASA POWER request failed: {network_error!r}") from network_error

    data = parse(raw, "network")
    if cache is not None:
        cache.put(key, raw)
    return data
