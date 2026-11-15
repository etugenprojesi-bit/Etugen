"""GET /api/satellite — satellite layers, harmonisation and pattern comparison (stage 3).

Separate from /api/analyze because a first live Earth Engine extraction for a
new point takes 1-3 minutes; results are cached per rounded point.
"""

from __future__ import annotations

import asyncio
import time

import numpy as np
from fastapi import APIRouter, HTTPException, Query

from app.api.analyze import DISCLAIMER, data_source_entry, load_point
from app.cache.store import ResponseCache
from app.config import get_settings
from app.features import climate, terrain
from app.harmonize import compare, series
from app.patterns import features as pfeat
from app.patterns import methods
from app.sources import SourceError, gee

router = APIRouter()

LABELS = {
    "power_gwetroot_model": "Model-based root-zone soil wetness (MERRA-2 via NASA POWER), 0-1 — not SMAP observation",
    "smap_sm": "SMAP L3 enhanced observed surface soil moisture (top ~5 cm), m³/m³",
    "imerg_precip_mm": "GPM IMERG V07 satellite-gauge precipitation, mm/month",
    "power_precip_mm": "NASA POWER PRECTOTCORR (MERRA-2 bias-corrected), mm/month",
    "ndvi": "MODIS MOD13Q1 NDVI (QA good/marginal), 1 km mean",
}


def gee_source_entry(raw: dict | None, origin: str, error: str | None = None,
                     layers: tuple[str, ...] = gee.LAYERS) -> dict:
    ids = {"ndvi": gee.NDVI_ID, "smap": ", ".join(gee.SMAP_IDS), "imerg": gee.IMERG_MONTHLY_ID,
           "slope": gee.DEM_ID, "phenology": gee.PHENOLOGY_ID,
           "chirps": gee.CHIRPS_ID}
    errors = dict((raw or {}).get("errors", {}))
    if error:
        errors["_all"] = error
    return {
        "id": "earth_engine",
        "name": "Google Earth Engine (NASA datasets)",
        "layers": {k: {"dataset": ids[k], "footprint": gee.FOOTPRINTS[k],
                       "available": raw is not None and k in raw.get("layers", {})} for k in layers},
        "origin": origin,
        "is_cached": origin in ("cache", "demo_cache"),
        "is_demo_cache": origin == "demo_cache",
        "errors": errors,
    }


def load_slope_summary(lat: float, lon: float) -> tuple[dict, dict]:
    s = get_settings()
    layer, origin, err = gee.load_slope(lat, lon, ResponseCache(s.cache_path), s.demo_cache_dir)
    summary = (terrain.slope_summary(layer["stats"], layer.get("plane")) if layer
               else {"status": "missing", "error": err})
    entry = gee_source_entry({"layers": {"slope": layer}} if layer else None, origin, err, ("slope",))
    return summary, entry


def _r(v, d=3):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), d)


@router.get("/api/satellite")
async def satellite(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
) -> dict:
    t0 = time.perf_counter()
    s = get_settings()
    pt = await load_point(lat, lon)
    try:
        raw, origin = await asyncio.to_thread(gee.load_point, pt.lat, pt.lon, s.first_year, s.last_full_year,
                                              ResponseCache(s.cache_path), s.demo_cache_dir)
    except SourceError as e:
        raise HTTPException(status_code=502, detail={"source": "earth_engine", "error": str(e)}) from e

    layers = raw.get("layers", {})
    ndvi = series.ndvi_series(layers["ndvi"]) if "ndvi" in layers else None
    smap, smap_diag = series.merge_smap(layers["smap"]["versions"]) if "smap" in layers else (None, None)
    imerg = series.imerg_monthly_mm(layers["imerg"]) if "imerg" in layers else None
    table = series.monthly_table(pt.daily, ndvi, smap, imerg)

    cols = ["power_precip_mm", "imerg_precip_mm", "power_gwetroot_model", "smap_sm", "ndvi"]
    precip = compare.compare_precip(table) if imerg is not None else {"status": "missing"}

    # Soil moisture: observation vs model, months where both exist.
    sm_block: dict = {"status": "missing"}
    if smap is not None and not smap.empty:
        both = table[["smap_sm", "power_gwetroot_model"]].dropna()
        sm_block = {
            "status": "ok",
            "merge": smap_diag,
            "monthly_months": int(table["smap_sm"].notna().sum()),
            "correlation_with_model": _r(np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1]) if len(both) > 3 else None,
            "note": "SMAP measures the top ~5 cm; POWER GWETROOT is a modelled root-zone wetness index (0-1). "
                    "Compare their ups and downs, not their values.",
        }

    patterns: dict = {"status": "missing_ndvi"}
    if ndvi is not None and len(ndvi):
        yt = pfeat.year_table(table, climate.annual_summary(pt.daily))
        patterns = methods.compare(yt)
        patterns["status"] = "ok"
        if precip.get("difference_series", {}).get("homogeneous") is False:
            patterns["notes"].append("POWER precipitation is not homogeneous here (see precipitation comparison); "
                                     "climate-based results (Isolation Forest, analogs) inherit that problem.")

    recent = table[table.index.year == table.index.year.max()]
    return {
        "analysis_point": {"lat": pt.lat, "lon": pt.lon},
        "disclaimer": DISCLAIMER,
        "data_sources": [data_source_entry(pt.power), gee_source_entry(raw, origin)],
        "labels": LABELS,
        "slope": terrain.slope_summary(layers["slope"]["stats"], layers["slope"].get("plane")) if "slope" in layers else {"status": "missing"},
        "monthly_climatology": series.climatology(table, cols),
        "recent_year": {"year": int(table.index.year.max()),
                        "months": [{"month": int(p.month), **{c: _r(r[c]) for c in cols}}
                                   for p, r in recent.iterrows()]},
        "precipitation_comparison": precip,
        "soil_moisture": sm_block,
        "patterns": patterns,
        "method": ["stat:monthly_aggregation", "stat:pettitt_change_point", "stat:zscore_threshold",
                   "ml:kmeans", "ml:isolation_forest", "stat:analog_nearest_neighbours",
                   "rule:rusle_slope_factor"],
        "timing_s": round(time.perf_counter() - t0, 2),
        "stage": 3,
    }
