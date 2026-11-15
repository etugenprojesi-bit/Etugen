"""POST /api/rotations — compare the current rotation with recommended ones (stage 4).

Priorities, constraints and the current rotation are used only for this
request and are not stored (docs/PRIVACY.md).
"""

from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.analyze import DISCLAIMER, calendar_source_entry, evaluate_variant, load_variant
from app.api.satellite import load_slope_summary
from app.config import get_settings
from app.explain.llm import explain_cards
from app.features import climate, scenario
from app.rotation import engine as rot
from app.rotation.cards import build_card
from app.rotation.scoring import score
from app.rotation.search import Screen
from app.water.irrigation import schedule as irrigation_schedule
from app.rotation.water_carry import WaterCarry
from app.sources import SourceError, soilgrids
from app.cache.store import ResponseCache
from app.suitability.confidence import assess
from app.suitability.crops import load_crops, localize

router = APIRouter()

Weight = Field(3, ge=0, le=5)


class Priorities(BaseModel):
    water: float = Weight
    soil: float = Weight
    erosion: float = Weight
    nitrogen: float = Weight
    income: float = Weight
    forage: float = Weight


class Constraints(BaseModel):
    excluded_crops: list[str] = []
    equipment_limits: list[str] = Field(default=[], description=f"any of {sorted(rot.EQUIPMENT_EXCLUSIONS)}")
    market_crops: list[str] = []


class RotationRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    irrigation: str = Field("none", pattern="^(none|limited|full)$")
    priorities: Priorities = Priorities()
    constraints: Constraints = Constraints()
    current_rotation: list[list[str]] | None = Field(
        None, description="Crop ids per year, e.g. [['winter_wheat'], ['lentil'], ['winter_wheat']]; "
                          "null = unknown", max_length=4)
    precip_source: str = Field("power", pattern="^(power|imerg|chirps)$")
    delta_t: float = Field(0.0, ge=scenario.DELTA_T_RANGE[0], le=scenario.DELTA_T_RANGE[1])
    delta_p: float = Field(0.0, ge=scenario.DELTA_P_RANGE[0], le=scenario.DELTA_P_RANGE[1])
    explore_sowing: bool = Field(False, description="ignore the local sowing calendar (GGCMI)")
    explain: str = Field("template", pattern="^(template|llm)$")
    lang: str = Field("tr", pattern="^(tr|en)$")


async def load_soil_water(lat: float, lon: float) -> tuple[soilgrids.SoilWater | None, dict]:
    """SoilGrids water retention at the rounded point; None (reported) when unavailable."""
    s = get_settings()
    entry = {"id": "soilgrids_water_retention", "name": "ISRIC SoilGrids v2.0 water retention (wv0033, wv1500)",
             "resolution": soilgrids.FOOTPRINT, "licence": "CC BY 4.0"}
    try:
        raw, origin = await soilgrids.load_point(lat, lon, ResponseCache(s.cache_path), s.demo_cache_dir)
    except SourceError as e:
        return None, entry | {"origin": "none", "error": str(e)}
    return soilgrids.parse(raw, origin), entry | {"origin": origin, "is_cached": origin != "network",
                                                   "is_demo_cache": origin == "demo_cache"}


def soil_summary(soil: soilgrids.SoilWater | None) -> dict | None:
    if soil is None:
        return None
    return {"tew_mm": _r(soil.tew_mm()), "taw_mm_per_m": _r(soil.taw_mm(1.0)),
            "texture_0_15cm_pct": soil.texture_pct(),
            "field_capacity": "33 kPa (assumption)", "wilting_point": "1500 kPa"}


def _r(v: float | None) -> float | None:
    return None if v is None else round(v, 1)


@router.post("/api/rotations")
async def rotations(req: RotationRequest) -> dict:
    t0 = time.perf_counter()
    s = get_settings()
    var = await load_variant(req.lat, req.lon, req.precip_source, req.delta_t, req.delta_p)
    pt = var.pt
    months = climate.monthly_profile(pt.daily)["months"]
    slope, slope_source = await asyncio.to_thread(load_slope_summary, pt.lat, pt.lon)

    crops = {c.id: c for c in localize(load_crops(s.data_dir), pt.lat, pt.lon, s.data_dir)}
    results, _ = evaluate_variant(list(crops.values()), var, req.irrigation, req.explore_sowing)
    conf = {cid: assess(crops[cid], r, req.irrigation) for cid, r in results.items()}
    constraints = req.constraints.model_dump()
    allowed_results = {cid: r for cid, r in results.items() if rot.allowed(crops[cid], constraints)}
    threshold = rot.slot_threshold({cid: r for cid, r in allowed_results.items() if not crops[cid].first_cut_only})
    slots = {cid: sl for cid, r in allowed_results.items() if (sl := rot.make_slots(crops[cid], r, threshold))}
    weights = req.priorities.model_dump()
    # Flat terrain (terrain.slope_summary): water erosion needs slope, so the erosion priority
    # is not used there (plan_kolay_mod.md, K5).
    erosion_ignored = bool(slope.get("flat_terrain"))
    if erosion_ignored:
        weights["erosion"] = 0.0
    market = set(req.constraints.market_crops)
    cover = [{"id": c.id, "name": c.name} for c in crops.values() if c.group == "cover"]

    soil, soil_source = await load_soil_water(pt.lat, pt.lon)
    carry = (WaterCarry(pt.clim, soil, req.irrigation, {cid: r.get("light_ref") for cid, r in results.items()})
             if soil is not None else None)
    if carry is not None and not carry.available:
        carry = None

    def score_fn(r: rot.Rotation) -> dict:
        return score(r, months, weights, market, slope, carry)

    def card(r: rot.Rotation) -> dict:
        c = build_card(r, score_fn(r), conf, cover, req.irrigation)
        for y_rot, y_card in zip(r.years, c["years"]):  # FAO-56 mid-season irrigation interval
            for s, v in zip(y_rot, y_card):
                v["irrigation_schedule"] = irrigation_schedule(s.crop, s.window, months, soil)
        return c

    cards = []
    if req.current_rotation:
        cards.append(card(rot.current_rotation(req.current_rotation, crops, results)))
    elif (ref := rot.monoculture_reference(slots)) is not None:
        cards.append(card(ref))
    screen = Screen(months, weights, market, slope)
    recommended = rot.recommend(slots, score_fn, on_candidates=carry.prepare_rotations if carry else None,
                                screen=screen)
    cards += [card(r) for r in recommended]
    for i, c in enumerate(cards):
        c["id"] = f"{c['kind']}-{i}"

    explanation = await explain_cards(cards, req.lang) if req.explain == "llm" else None

    return {
        "analysis_point": {"lat": pt.lat, "lon": pt.lon},
        "disclaimer": DISCLAIMER,
        "variant": var.info,
        "data_sources": [*var.sources, slope_source, soil_source, calendar_source_entry()],
        "soil_water": soil_summary(soil),
        "slope": slope,
        "erosion_ignored_flat_terrain": erosion_ignored,
        "cards": cards,
        "n_recommended": len(recommended),
        "usable_crops": sorted(slots),
        "min_crop_score": round(threshold, 3),
        "excluded_by_constraints": sorted(cid for cid, c in crops.items() if not rot.allowed(c, constraints)),
        "not_used_first_cut_only": sorted(cid for cid, c in crops.items()
                                          if c.first_cut_only and results[cid].get("status") == "evaluated"),
        "explanation": explanation,
        "subscore_weights_fixed": rot.FIXED_WEIGHTS | {"suitability": 3.0},
        "timing_s": round(time.perf_counter() - t0, 2),
        "stage": 4,  # + stage 3 slope
    }
