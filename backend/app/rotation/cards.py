"""Turn a scored rotation into a comparison card: why, benefits, risks, data
gaps, confidence and questions for local experts.

Every statement is a `code` + `params` (translated in the UI) with an English
`text`, derived only from the scores, rules and crop data — nothing invented.
"""

from __future__ import annotations

from app.rotation.engine import Rotation, rule_violations
from app.rotation.scoring import fallow_periods

GOOD = 0.7
POOR = 0.4
MIN_COVER_GAP_MONTHS = 2
MAX_QUESTIONS = 6
LEVEL_ORDER = {"unknown": 0, "low": 1, "medium": 2}


def _item(code: str, text: str, **params) -> dict:
    return {"code": code, "text": text, "params": params}


def slot_view(s, stats: dict | None = None, carry: dict | None = None) -> dict:
    """One crop of the card. `stats` are the window numbers after the soil water carried from
    the previous gap (scoring.slot_stats); `carry` describes that gap (water_carry)."""
    w = {**s.window, **(stats or {})}
    return {
        "crop_id": s.crop.id, "name": s.crop.name, "family": s.crop.family, "group": s.crop.group,
        "nitrogen_fixing": s.crop.nitrogen_fixing, "sowing": w["sowing"], "harvest": w["harvest_median"],
        "season_days": w["season_days_median"], "months": sorted(s.months),
        "score_median": w["score_median"], "score_p20": w["score_p20"], "fail_rate": w["fail_rate"],
        "rain_deficit_mm": w["rain_deficit_mm_median"],
        "score_median_without_stored_water": s.window["score_median"],
        "stored_soil_water": carry,
    }


def _years_view(rot: Rotation, scored: dict) -> list[list[dict]]:
    n = len(rot.slots)
    pairs = iter(zip(scored.get("slot_stats") or [None] * n, scored.get("carry") or [None] * n))
    return [[slot_view(s, *next(pairs)) for s in y] for y in rot.years]


def _group_gaps(gaps: list[dict]) -> list[dict]:
    """Merge identical bare periods that recur every year into one entry with a list of years."""
    grouped: dict[tuple[int, int], dict] = {}
    for g in gaps:
        key = (g["start_month"], g["months"])
        grouped.setdefault(key, {"start_month": g["start_month"], "months": g["months"], "years": []})
        grouped[key]["years"].append(g["year"])
    return list(grouped.values())


def build_card(rot: Rotation, scored: dict, crop_conf: dict[str, dict], cover_crops: list[dict],
               irrigation: str) -> dict:
    sub = scored["subscores"]
    violations = rule_violations(rot)
    gaps = _group_gaps([g for g in fallow_periods(rot) if g["months"] >= MIN_COVER_GAP_MONTHS])

    # Why: the strongest weighted contributions.
    contrib = sorted(((v["weight"] * v["value"], k) for k, v in sub.items()
                      if v["value"] is not None and v["weight"] > 0), reverse=True)
    why = [_item(f"strong_{k}", f"Strong on {k} ({sub[k]['value']:.0%}).", value=sub[k]["value"])
           for _, k in contrib[:3] if sub[k]["value"] >= GOOD]
    if rot.kind == "current":
        why.insert(0, _item("is_current", "This is the rotation you entered, scored with the same rules."))
    elif rot.kind == "reference":
        why.insert(0, _item("is_reference", "Reference: the single best-suited crop every year (monoculture). "
                                            "Shown because the current rotation is unknown."))

    benefits = []
    if sub.get("nitrogen", {}).get("value", 0) and sub["nitrogen"].get("cereal_after_legume_share", 0) > 0:
        benefits.append(_item("legume_before_cereal", "A legume precedes a cereal: less nitrogen fertiliser needed."))
    if sub.get("diversity", {}).get("value", 0) >= GOOD:
        benefits.append(_item("pest_break", "Different plant families in a row break pest and disease cycles."))
    if sub.get("soil", {}).get("value", 0) >= GOOD:
        benefits.append(_item("roots_structure", "Deep roots and long living-root periods support soil structure "
                                                 "and infiltration (proxy)."))
    if sub.get("erosion", {}).get("value", 0) >= GOOD:
        benefits.append(_item("cover_in_rainy_months", "The soil is covered in most heavy-rain months."))
    if any(len(y) > 1 for y in rot.years):
        benefits.append(_item("double_cropping", "Two crops in one year use the season fully."))
    if sub.get("income", {}).get("value") is not None and sub["income"]["value"] >= GOOD:
        benefits.append(_item("market_crops", "Most crops are ones you marked as having a market."))

    risks = []
    for v in violations:
        risks.append(_item(v["code"], "Rule broken: " + v["code"].replace("_", " "),
                           **{k: val for k, val in v.items() if k != "code"}))
    if sub.get("water", {}).get("value") is not None and sub["water"]["value"] < POOR:
        risks.append(_item("water_deficit", "Rain covers little of the crops' water use.",
                           irrigation_need_mm_per_year=scored["irrigation_need_mm_per_year"],
                           irrigation=irrigation))
    if sub.get("climate_risk", {}).get("max_fail_rate", 0) > 0.3:
        risks.append(_item("frequent_failure", "At least one crop fails in many years of the record.",
                           max_fail_rate=sub["climate_risk"]["max_fail_rate"]))
    for g in gaps:
        risks.append(_item("bare_soil", "The field is bare for {months} months starting month {start_month}.", **g))

    data_gaps = [_item("soil_proxy", "Soil-health score is a proxy (root depth, living roots); "
                                     "organic-matter data per crop are not yet sourced.")]
    if "income" in scored["unknown"]:
        data_gaps.append(_item("no_market_data", "No market/price data: mark crops with a market to score income."))
    erosion = sub.get("erosion", {})
    if erosion.get("relative_slope_factor") is None:
        data_gaps.append(_item("no_slope", "Slope data unavailable: erosion score assumes a 9 % slope."))
    else:
        data_gaps.append(_item("slope_is_area", "Slope is the median of the surrounding ~5 km cell (NASADEM), "
                                                "not your field.", slope_pct=erosion["slope_pct"]))
    fallow_years = [i + 1 for i, y in enumerate(rot.years) if not y and rot.kind != "current"]
    if fallow_years:
        benefits.append(_item("fallow_break", "A fallow year breaks the cereal sequence and pest cycles.",
                              years=fallow_years))
    stats = scored.get("slot_stats") or []
    if scored.get("carry_available"):
        for c, st, s in zip(scored.get("carry") or [], stats, rot.slots):
            if c and c["n_fallow_years"] > 0:
                benefits.append(_item(
                    "fallow_stores_water", "During the fallow the soil stores about {stored_mm_median} mm of water "
                    "({storage_efficiency_median} of the rain) for the next crop (FAO-56 model, not measured).",
                    crop_id=s.crop.id, score_median_with=st["score_median"], **{k: c[k] for k in (
                        "stored_mm_median", "stored_mm_p20", "stored_mm_p80", "storage_efficiency_median",
                        "gap_rain_mm_median", "gap_days_median", "deep_percolation_mm_median",
                        "score_median_without")}))
        data_gaps.append(_item("soil_water_model", "Soil water between crops is a FAO-56 model with SoilGrids "
                                                   "250 m soil data: no runoff, no weeds or residue, empty profile "
                                                   "at harvest (assumptions)."))
    elif fallow_years:
        data_gaps.append(_item("fallow_not_modelled", "Soil water stored during the fallow year is not modelled "
                                                      "(soil data unavailable); the fallow year counts as no "
                                                      "production.", years=fallow_years))
    if rot.missing_slots:
        data_gaps.append(_item("unmodelled_current_crops", "Some crops of your rotation cannot be modelled yet.",
                               crops=[m["crop_id"] for m in rot.missing_slots]))

    # Cover-crop opportunities: honest that cover crops are not modelled yet.
    opportunities = [_item("cover_crop_window", "Fallow window: consider a cover or catch crop "
                                                "(not modelled; choose locally).",
                           **g, candidates=[c["id"] for c in cover_crops]) for g in gaps]

    levels = [crop_conf[s.crop.id]["level"] for s in rot.slots if s.crop.id in crop_conf]
    level = min(levels, key=lambda lv: LEVEL_ORDER.get(lv, 0)) if levels else "unknown"
    if rot.missing_slots:
        level = "low" if level != "unknown" else level
    questions, seen = [], set()
    for s in rot.slots:
        for q in crop_conf.get(s.crop.id, {}).get("questions", []):
            key = (q["code"], s.crop.id)
            if q["code"] in {"local_variety"} or key in seen:
                continue
            seen.add(key)
            questions.append({**q, "params": {**q["params"], "crop_id": s.crop.id}})
    if fallow_years:
        questions.append(_item("fallow_management", "During the fallow, is stubble left and are weeds controlled?"))
    for g in gaps:
        questions.append(_item("cover_crop_local", "Which cover crop could grow in the {months}-month fallow "
                                                    "starting month {start_month}?", **g))
    questions.append(_item("drainage", "Does this field have drainage or waterlogging problems?"))

    return {
        "kind": rot.kind,
        "years": _years_view(rot, scored),
        "missing_slots": rot.missing_slots,
        "total": scored["total"],
        "subscores": sub,
        "unknown_subscores": scored["unknown"],
        "irrigation_need_mm_per_year": scored["irrigation_need_mm_per_year"],
        "rule_violations": violations,
        "fallow_periods": fallow_periods(rot),
        "why": why,
        "benefits": benefits,
        "risks": risks,
        "data_gaps": data_gaps,
        "opportunities": opportunities,
        "confidence": {"level": level, "needs_local_validation": level != "medium"},
        "questions": questions[:MAX_QUESTIONS],
        "evidence": [
            "NASA POWER daily 25 years (~0.5° grid): temperature, rain, ET0 (FAO-56)",
            "FAO-56 Tables 11, 12, 22: stages, Kc, root depth",
            "Crop temperature response: literature (see crop_sources)",
            "Soil water between crops: FAO-56 ch. 7, 8, 11 with ISRIC SoilGrids water retention (250 m)",
            "Rules: family sequence, legume-cereal, cover in heavy-rain months (docs/METHOD.md)",
        ],
        "method": ["rule:rotation_rules", "physics:fao56_water_use", "physics:fao56_soil_water_balance",
                   "stat:bad_year_p20", "proxy:soil_health"],
    }
