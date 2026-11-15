"""Confidence level, reasons and questions for local experts (rule-based).

Stage 1 never reports "high": the only climate input is the ~0.5° NASA POWER
grid. Each reason and question has a stable `code` (for UI translation),
English `text` and the numbers behind it in `params`.
"""

from __future__ import annotations

from app.suitability.crops import Crop

SPREAD_LIMIT = 0.3     # median - p20 above this = large year-to-year variation
FAIL_LIMIT = 0.3       # fails in more than 30 % of years
WATER_LIMIT = 0.7      # rainfed water score below this = irrigation question


def _item(code: str, text: str, **params) -> dict:
    return {"code": code, "text": text, "params": params}


def assess(crop: Crop, result: dict, irrigation: str) -> dict:
    reasons = [_item("coarse_climate_grid",
                     "Climate data come from a ~50 km grid (NASA POWER); field conditions can differ.")]
    questions = []
    level = "medium"

    if result["status"] == "not_suitable_by_model":
        r = result["reason"]
        questions = [_item("local_experience",
                           "Is this crop grown locally? When is it sown and harvested?")]
        if r["code"] == "does_not_mature":
            questions.insert(0, _item(
                "short_season_variety",
                "Are there local varieties with a shorter season? The model's thermal-time value "
                "comes from a single reference cultivar."))
        return {
            "level": "low",
            "needs_local_validation": True,
            "reasons": reasons + [_item("model_unsuitable", r["text"], limiting_factor=r["code"])],
            "questions": questions,
        }

    if result["status"] != "evaluated":
        return {
            "level": "unknown",
            "needs_local_validation": True,
            "reasons": [_item("missing_parameters", "Crop parameters are missing: " + ", ".join(crop.missing),
                              missing=crop.missing)],
            "questions": [_item("local_experience",
                                "Is this crop grown locally? When is it sown and harvested?")],
        }

    t = crop.temperature
    w = result["best_window"]
    if not t.verified:
        reasons.append(_item("unverified_transcription",
                             "Temperature parameters were transcribed second-hand and not yet checked "
                             "against the original paper.", source=t.source))
    if t.ecocrop is not None:
        level = "low"
        reasons.append(_item("ecocrop_general_ranges",
                             "Temperature limits are general ranges from FAO ECOCROP (no licence stated, "
                             "FAO asked), not a calibrated crop model.", url=t.ecocrop.url))
    if crop.variant:
        reasons.append(_item("regional_variant",
                             "Season length of the regional cultivar variant '{name}' ({source}): {assumption}",
                             name=crop.variant["name"]["en"], name_tr=crop.variant["name"]["tr"],
                             source=crop.variant["source"], assumption=crop.variant["assumption"]))
    if crop.assumptions:  # one reason per crop (codes are UI keys), all assumption texts in params
        reasons.append(_item("analogy_assumption", " ".join(crop.assumptions), assumptions=crop.assumptions))
    if result.get("calendar_conflict"):
        level = "low"
        cal = result["local_calendar"]
        reasons.append(_item("calendar_conflict",
                             "The model cannot grow this crop around the local planting day ({planting}, "
                             "GGCMI, {source}); the best window outside the local calendar is shown.",
                             planting=cal["planting"], source=cal["data_source"]))
    if t.t_heat is None:
        level = "low"
        reasons.append(_item("no_heat_threshold", "No heat-stress thresholds are known for this crop."))
    if t.t_sum is None:
        reasons.append(_item("fixed_season_length",
                             "Season length is a fixed FAO-56 reference value, not adjusted to local temperature.",
                             row=crop.stages.row))
    if w["score_median"] - w["score_p20"] > SPREAD_LIMIT:
        level = "low"
        reasons.append(_item("high_variability", "Results vary strongly from year to year.",
                             median=w["score_median"], p20=w["score_p20"]))
    if w["fail_rate"] > FAIL_LIMIT:
        level = "low"
        reasons.append(_item("frequent_failure", "The season fails in many years of the record.",
                             fail_rate=w["fail_rate"]))

    if irrigation == "none" and w["water_score_median"] < WATER_LIMIT:
        questions.append(_item(
            "irrigation_available",
            "Is irrigation water available in the dry part of the season? The model estimates a rain "
            "deficit of about {deficit} mm.", deficit=w["rain_deficit_mm_median"]))
    if w["frost_days_median"] > 0:
        questions.append(_item(
            "frost_damage",
            "Frost occurs in a typical season (~{days} days below 0 °C). Do local varieties of this crop "
            "survive frost at that stage?", days=w["frost_days_median"]))
    if w.get("heat_days_median"):
        questions.append(_item(
            "heat_at_flowering",
            "Hot days above {t} °C occur in the season (~{days} days). Does heat around flowering reduce "
            "yields locally?", t=t.t_heat, days=w["heat_days_median"]))
    questions.append(_item("local_variety",
                           "Which local varieties are used, and how long is their season compared with "
                           "{days} days?", days=w["season_days_median"]))

    return {"level": level, "needs_local_validation": level == "low", "reasons": reasons,
            "questions": questions}
