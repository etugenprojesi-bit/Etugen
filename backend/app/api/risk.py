"""GET /api/risk — risk layers per year and month at the analysis point (stage 5).

Climate layers follow the chosen rainfall source and scenario; SMAP and NDVI
are observations and are shown as they are. If Earth Engine (and the demo
cache) cannot provide them, the climate layers are still returned and the
missing layers are listed with the error.
"""

from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, HTTPException, Query

from app.api.analyze import DISCLAIMER, load_variant
from app.api.satellite import gee_source_entry
from app.cache.store import ResponseCache
from app.config import get_settings
from app.features import climate, scenario
from app.harmonize import series
from app.risk import layers as risk
from app.sources import SourceError, gee
from app.suitability.crops import load_crops, mid

router = APIRouter()

GENERIC_HEAT = {"threshold_c": climate.HOT_C, "source": "generic, no crop chosen", "assumption": True}


def _crop_thresholds(crop_id: str | None) -> tuple[dict, dict | None, dict | None]:
    """Heat and lethal-cold thresholds for the chosen crop (sourced values only)."""
    if not crop_id:
        return GENERIC_HEAT, None, None
    crops = {c.id: c for c in load_crops(get_settings().data_dir)}
    if crop_id not in crops:
        raise HTTPException(status_code=422, detail=f"unknown crop '{crop_id}'")
    c = crops[crop_id]
    heat = GENERIC_HEAT
    if c.temperature is not None and c.temperature.t_heat is not None:
        heat = {"threshold_c": c.temperature.t_heat,
                "source": f"t_heat, {c.temperature.source} (crop_phenology.yaml)", "assumption": False}
    lethal = None
    if c.lethal_min and c.lethal_min.get("value") is not None:
        lethal = {"threshold_c": mid(c.lethal_min["value"]),
                  "source": f"lethal minimum, {c.lethal_min.get('source')}: {c.lethal_min.get('note', '')}".strip()}
    return heat, lethal, {"id": c.id, "name": c.name}


def crop_options() -> list[dict]:
    out = []
    for c in load_crops(get_settings().data_dir):
        t_heat = c.temperature.t_heat if c.temperature else None
        lethal = mid(c.lethal_min["value"]) if c.lethal_min and c.lethal_min.get("value") is not None else None
        if t_heat is not None or lethal is not None:
            out.append({"id": c.id, "name": c.name, "t_heat": t_heat, "lethal_min": lethal})
    return out


def _satellite_table(pt) -> tuple[object, dict]:
    s = get_settings()
    try:
        raw, origin = gee.load_point(pt.lat, pt.lon, s.first_year, s.last_full_year,
                                     ResponseCache(s.cache_path), s.demo_cache_dir)
    except SourceError as e:
        return None, gee_source_entry(None, "none", str(e), ("ndvi", "smap"))
    lay = raw.get("layers", {})
    ndvi = series.ndvi_series(lay["ndvi"]) if "ndvi" in lay else None
    smap = series.merge_smap(lay["smap"]["versions"])[0] if "smap" in lay else None
    table = series.monthly_table(pt.daily, ndvi, smap, None)
    return table, gee_source_entry(raw, origin, None, ("ndvi", "smap"))


@router.get("/api/risk")
async def risk_layers(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    crop: str | None = Query(None, max_length=40),
    precip_source: str = Query("power", pattern="^(power|imerg|chirps)$"),
    delta_t: float = Query(0.0, ge=scenario.DELTA_T_RANGE[0], le=scenario.DELTA_T_RANGE[1]),
    delta_p: float = Query(0.0, ge=scenario.DELTA_P_RANGE[0], le=scenario.DELTA_P_RANGE[1]),
) -> dict:
    t0 = time.perf_counter()
    heat, lethal, crop_info = _crop_thresholds(crop)
    var = await load_variant(lat, lon, precip_source, delta_t, delta_p)
    table, sat_source = await asyncio.to_thread(_satellite_table, var.pt)
    result = risk.build(var.baseline, var.pt.daily, table, heat, lethal)
    notes = []
    if var.info["scenario_active"]:
        notes.append("scenario_applies_to_climate_only")
    if heat["assumption"]:
        notes.append("generic_heat_threshold")
    if lethal:
        notes.append("lethal_cold_is_air_temperature")
    return {
        "analysis_point": {"lat": var.pt.lat, "lon": var.pt.lon},
        "disclaimer": DISCLAIMER,
        "variant": var.info,
        "crop": crop_info,
        "crop_options": crop_options(),
        "data_sources": [*var.sources, sat_source],
        **result,
        "notes": notes,
        "method": ["rule:threshold_day_counts", "physics:fao56_et0", "stat:monthly_standardised_anomaly"],
        "timing_s": round(time.perf_counter() - t0, 2),
        "stage": 5,
    }
