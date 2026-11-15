"""GET /api/analyze — climate profile and crop suitability for one point (stage 1)."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import httpx
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.cache.store import ResponseCache, round_coord
from app.config import get_settings
from app.features import climate, scenario
from app.harmonize import rainfall, series
from app.sources import SourceError, gee, power
from app.suitability import calendar
from app.suitability.confidence import assess
from app.suitability.crops import load_crops, localize, source_citations
from app.suitability.engine import IRRIGATION_MODES, ClimateArrays, evaluate_crop

router = APIRouter()

DISCLAIMER = (
    "This tool supports, it does not replace, the farmer's judgement and local agronomic "
    "expertise. Check every result marked 'needs local validation' with a local expert."
)


def _crop_entry(crop, result, irrigation: str) -> dict:
    entry = {
        "id": crop.id,
        "name": crop.name,
        "scientific": crop.scientific,
        "family": crop.family,
        "group": crop.group,
        "nitrogen_fixing": crop.nitrogen_fixing,
        "status": result["status"],
        "confidence": assess(crop, result, irrigation),
    }
    entry["cultivar_variant"] = crop.variant
    entry["local_calendar"] = result.get("local_calendar")
    entry["calendar_rule"] = result.get("calendar_rule", False)
    entry["calendar_conflict"] = result.get("calendar_conflict", False)
    if result["status"] == "evaluated":
        t = crop.temperature
        entry |= {
            "best_window_outside_calendar": result.get("best_window_outside_calendar"),
            "best_window": result["best_window"],
            "good_sowing_dates": result["good_sowing_dates"],
            "windows": [{k: w[k] for k in ("sowing", "score_median", "score_p20", "fail_rate",
                                           "season_days_median", "in_local_calendar")} for w in result["windows"]],
            "evidence": {
                "climate": "NASA POWER daily (MERRA-2 / CERES), ~0.5° grid",
                "water_use": ("FAO-56 Kc (Table 12, mid/end adjusted to local wind and RHmin, "
                              "eq. 62/65) x ET0 (Penman-Monteith)"),
                "stages": f"FAO-56 Table 11 row: {crop.stages.row}",
                "temperature": f"{t.source} (verified against original: {t.verified})",
                "season_length": ("FAO-56 Table 11 length" if t.t_sum is None
                                  else "thermal time (t_sum, WOFOST DTSMTB table)" if t.dev_rate_table
                                  else "thermal time (t_sum)"),
            },
            "method": ["physics:fao56_et0_kc", "rule:simple_temperature_response",
                       "rule:dekad_water_deficit"],
        }
    elif result["status"] == "not_suitable_by_model":
        entry["reason"] = result["reason"]
        entry["windows"] = [{k: w[k] for k in ("sowing", "score_median", "matured_share")}
                            for w in result["windows"]]
    else:
        entry["missing"] = result.get("missing", [])
    return entry


STATUS_ORDER = {"evaluated": 0, "not_suitable_by_model": 1, "insufficient_data": 2,
                "perennial_not_evaluated": 3}


@dataclass
class PointData:
    lat: float  # rounded analysis point
    lon: float
    power: power.PowerData
    daily: pd.DataFrame  # with TMEAN and ET0
    clim: ClimateArrays


async def load_point(lat: float, lon: float) -> PointData:
    """NASA POWER daily data for the rounded point (cache -> network -> demo cache) + ET0."""
    s = get_settings()
    qlat, qlon = round_coord(lat, s.cache_grid_deg), round_coord(lon, s.cache_grid_deg)
    cache = ResponseCache(s.cache_path)
    try:
        async with httpx.AsyncClient() as client:
            pdata = await power.fetch_daily(client, qlat, qlon, s.first_year, s.last_full_year,
                                            cache=cache, demo_dir=s.demo_cache_dir)
    except SourceError as e:
        raise HTTPException(status_code=502, detail={"source": "nasa_power", "error": str(e)}) from e
    df = climate.add_derived(pdata.daily, pdata.elevation_m, qlat)
    return PointData(qlat, qlon, pdata, df, ClimateArrays.from_frame(df))


PRECIP_SOURCES = ("power", "imerg", "chirps")


def load_imerg_monthly(lat: float, lon: float) -> tuple[pd.Series, dict]:
    """IMERG monthly totals (mm) at the rounded point, from cache / Earth Engine / demo cache."""
    s = get_settings()
    try:
        raw, origin = gee.load_point(lat, lon, s.first_year, s.last_full_year,
                                     ResponseCache(s.cache_path), s.demo_cache_dir)
    except SourceError as e:
        raise HTTPException(status_code=502, detail={"source": "earth_engine", "error": str(e)}) from e
    if "imerg" not in raw.get("layers", {}):
        err = raw.get("errors", {}).get("imerg", "IMERG layer missing")
        raise HTTPException(status_code=502, detail={"source": "earth_engine", "error": err})
    entry = {"id": "gpm_imerg_monthly", "name": "GPM IMERG V07 monthly (via Earth Engine)",
             "dataset": gee.IMERG_MONTHLY_ID, "resolution": gee.FOOTPRINTS["imerg"], "origin": origin,
             "is_cached": origin in ("cache", "demo_cache"), "is_demo_cache": origin == "demo_cache"}
    return series.imerg_monthly_mm(raw["layers"]["imerg"]), entry


def load_chirps_monthly(lat: float, lon: float) -> tuple[pd.Series | None, dict, str | None]:
    """CHIRPS monthly totals (mm) at the rounded point: (series or None, source entry, error)."""
    s = get_settings()
    entry = {"id": "chirps_v2", "name": "CHIRPS v2.0 daily, summed to months (via Earth Engine)",
             "dataset": gee.CHIRPS_ID, "resolution": gee.FOOTPRINTS["chirps"], "licence": "public domain"}
    try:
        layer, origin = gee.load_layer(lat, lon, "chirps", s.first_year, s.last_full_year,
                                       ResponseCache(s.cache_path), s.demo_cache_dir)
    except SourceError as e:
        return None, entry | {"origin": "none"}, str(e)
    entry |= {"origin": origin, "is_cached": origin in ("cache", "demo_cache"), "is_demo_cache": origin == "demo_cache"}
    return series.chirps_monthly_mm(layer), entry, None


@dataclass
class Variant:
    """The point's data with the chosen rainfall source and scenario applied."""
    pt: PointData          # evaluated data (rain source + scenario)
    baseline: pd.DataFrame  # rain source, no scenario (reference for anomalies / deltas)
    info: dict
    sources: list[dict]


async def load_variant(lat: float, lon: float, precip_source: str = "power",
                       delta_t: float = 0.0, delta_p_pct: float = 0.0) -> Variant:
    if precip_source not in PRECIP_SOURCES:
        raise HTTPException(status_code=422, detail=f"precip_source must be one of {PRECIP_SOURCES}")
    pt = await load_point(lat, lon)
    raw, elev = pt.power.daily, pt.power.elevation_m
    sources = [data_source_entry(pt.power)]
    info: dict = {"precip_source": precip_source, "delta_t_c": delta_t, "delta_p_pct": delta_p_pct,
                  "scenario_active": scenario.is_active(delta_t, delta_p_pct)}
    base = pt.daily
    if precip_source == "imerg":
        imerg, entry = await asyncio.to_thread(load_imerg_monthly, pt.lat, pt.lon)
        raw, diag = rainfall.rescale_to_imerg(raw, imerg)
        info["imerg_rescale"] = diag
        sources.append(entry)
        base = climate.add_derived(raw, elev, pt.lat)
    elif precip_source == "chirps":
        chirps, entry, err = await asyncio.to_thread(load_chirps_monthly, pt.lat, pt.lon)
        if chirps is None:
            raise HTTPException(status_code=502, detail={"source": "earth_engine", "error": err})
        raw, diag = rainfall.rescale_to_monthly(raw, chirps, "CHIRPS")
        info["chirps_rescale"] = diag
        sources.append(entry)
        base = climate.add_derived(raw, elev, pt.lat)
    df = base
    if info["scenario_active"]:
        try:
            df = scenario.apply(raw, delta_t, delta_p_pct, elev, pt.lat)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        info["note"] = ("Scenario = sensitivity test on the observed record (delta change), "
                        "not a climate projection. RH, wind and radiation unchanged.")
    out = PointData(pt.lat, pt.lon, pt.power, df, ClimateArrays.from_frame(df))
    return Variant(out, base, info, sources)


def evaluate_variant(crops, var: Variant, irrigation: str,
                     explore_sowing: bool = False) -> tuple[dict, dict | None]:
    """Suitability for every crop. With a scenario, the baseline is evaluated first and its
    season radiation is the light-factor reference, so a shorter (warmer) season loses light.

    Each crop's best window follows the local sowing calendar (GGCMI) unless explore_sowing."""
    s = get_settings()
    cal = {c.id: calendar.lookup(s.data_dir, c.id, var.pt.lat, var.pt.lon, irrigation) for c in crops}
    use = not explore_sowing
    if not var.info["scenario_active"]:
        return {c.id: evaluate_crop(c, var.pt.clim, irrigation, None, cal[c.id], use) for c in crops}, None
    base_clim = ClimateArrays.from_frame(var.baseline)
    baseline = {c.id: evaluate_crop(c, base_clim, irrigation, None, cal[c.id], use) for c in crops}
    results = {c.id: evaluate_crop(c, var.pt.clim, irrigation, baseline[c.id].get("light_ref", {}),
                                   cal[c.id], use)
               for c in crops}
    return results, baseline


def calendar_source_entry() -> dict:
    return {"id": "ggcmi_crop_calendar", "name": calendar.ATTRIBUTION, "doi": "10.5281/zenodo.5062513",
            "resolution": "0.5° grid, multi-year average", "licence": "CC BY 4.0", "origin": "data file",
            "rule": f"best sowing window within ±{calendar.WINDOW_DAYS} days of the local planting day "
                    "(assumption); switch off with explore_sowing"}


def data_source_entry(pdata: power.PowerData) -> dict:
    s = get_settings()
    return {
        "id": "nasa_power_daily",
        "name": "NASA POWER daily point API",
        "api_version": pdata.api_version,
        "upstream": pdata.upstream_sources,
        "resolution": power.RESOLUTION,
        "period": f"{s.first_year}-01-01..{s.last_full_year}-12-31",
        "origin": pdata.origin,
        "is_cached": pdata.origin != "network",
        "is_demo_cache": pdata.origin == "demo_cache",
        "missing_days": int(pdata.daily.isna().any(axis=1).sum()),
    }


@router.get("/api/analyze")
async def analyze(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    irrigation: str = Query("none", pattern="^(none|limited|full)$"),
    precip_source: str = Query("power", pattern="^(power|imerg|chirps)$"),
    delta_t: float = Query(0.0, ge=scenario.DELTA_T_RANGE[0], le=scenario.DELTA_T_RANGE[1]),
    delta_p: float = Query(0.0, ge=scenario.DELTA_P_RANGE[0], le=scenario.DELTA_P_RANGE[1]),
    explore_sowing: bool = Query(False, description="ignore the local sowing calendar (GGCMI)"),
) -> dict:
    t0 = time.perf_counter()
    s = get_settings()
    var = await load_variant(lat, lon, precip_source, delta_t, delta_p)
    pt = var.pt
    df, pdata = pt.daily, pt.power
    crops = localize(load_crops(s.data_dir), pt.lat, pt.lon, s.data_dir)
    results, baseline = evaluate_variant(crops, var, irrigation, explore_sowing)
    # Rain check (plan_konya_yagis.md K1-a): POWER vs CHIRPS mean annual rain at this point.
    chirps, chirps_entry, chirps_err = await asyncio.to_thread(load_chirps_monthly, pt.lat, pt.lon)
    rain_check = (rainfall.rain_check(pdata.daily, chirps) if chirps is not None
                  else {"status": "missing", "error": chirps_err})
    rain_check["source"] = chirps_entry
    entries = [_crop_entry(c, results[c.id], irrigation) for c in crops]
    if baseline is not None:
        # Same crops without the scenario, so the UI can show what changed.
        for c, e in zip(crops, entries):
            b = baseline[c.id]
            e["baseline"] = {"status": b["status"],
                             "score_median": b.get("best_window", {}).get("score_median"),
                             "sowing": b.get("best_window", {}).get("sowing")}
    entries.sort(key=lambda e: (STATUS_ORDER[e["status"]],
                                -(e.get("best_window", {}).get("score_median") or 0)))

    return {
        "query": {"lat": lat, "lon": lon, "irrigation": irrigation, "precip_source": precip_source,
                  "delta_t": delta_t, "delta_p": delta_p, "explore_sowing": explore_sowing},
        "analysis_point": {"lat": pt.lat, "lon": pt.lon, "elevation_m": pdata.elevation_m,
                           "note": f"Coordinates rounded to {s.cache_grid_deg}° for analysis and caching."},
        "disclaimer": DISCLAIMER,
        "variant": var.info,
        "data_sources": [*var.sources, calendar_source_entry()],
        "climate": {
            "annual": climate.annual_means(df),
            "monthly": climate.monthly_profile(df),
            "trends": climate.trends(df),
            "method": ["physics:fao56_penman_monteith", "stat:etccdi_r95p", "stat:mann_kendall+sens_slope"],
            "labels": {"soil_wetness_root_model": "Model-based soil wetness (MERRA-2), not SMAP observation"},
            "rain_check": rain_check,
        },
        "crops": entries,
        "crop_sources": source_citations(s.data_dir),
        "irrigation_modes": {"none": "rainfed", "limited": "assumption: covers 50% of the rain deficit",
                             "full": "no water limitation"},
        "timing_s": round(time.perf_counter() - t0, 2),
        "stage": 1,
    }


assert set(IRRIGATION_MODES) == {"none", "limited", "full"}
