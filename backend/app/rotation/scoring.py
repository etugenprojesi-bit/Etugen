"""Sub-scores (0-1, higher is better) and weighted total for a rotation.

| key          | meaning                                                   | type          |
|--------------|-----------------------------------------------------------|---------------|
| suitability  | production: sum of normal-year season scores / years      | physics/rule  |
|              | (fallow year = 0, double cropping capped at 1)            |               |
| climate_risk | mean bad-year (20th percentile) season score              | stat          |
| water        | 1 - rain deficit / crop water use (FAO-56 ETc); soil      | physics       |
|              | water stored in the gap before a crop (fallow) covers     |               |
|              | its deficit first (app.rotation.water_carry)              |               |
| soil         | PROXY: 0.5 x root depth (FAO-56 Table 22) + 0.5 x share   | rule (proxy)  |
|              | of months with living roots                               |               |
| erosion      | 1 - (bare share, weighted by heavy-rain days per month    | rule          |
|              | (ETCCDI R95p)) x relative RUSLE slope factor S/S(9 %)     |               |
|              | (NASADEM); without slope data S/S(9 %) = 1 (assumption)   |               |
| nitrogen     | 0.6 x share of years with a legume + 0.4 x share of       | rule          |
|              | cereal slots that follow a legume                         |               |
| income       | share of slots with a crop the user says has a market;    | user input    |
|              | unknown (excluded) when the user gave no market crops     |               |
| forage       | share of slots with a forage crop (crops.yaml group)      | rule          |
| diversity    | distinct families / slots                                 | rule          |

Total = weighted mean over known sub-scores. User weights (0-5) apply to
PRIORITIES; suitability, climate_risk and diversity have fixed weights.
"""

from __future__ import annotations

from app.rotation.engine import FIXED_WEIGHTS, PRIORITIES, ROOT_DEPTH_REF_M, Rotation
from app.rotation.water_carry import WaterCarry, effective_windows

KIND = {
    "suitability": "physics", "climate_risk": "stat", "water": "physics", "soil": "proxy",
    "erosion": "rule", "nitrogen": "rule", "income": "user_input", "forage": "rule", "diversity": "rule",
}
SUITABILITY_WEIGHT = 3.0
CEREAL_GROUPS = {"cereal"}


def covered_months(rot: Rotation) -> list[set[int]]:
    return [set().union(*(s.months for s in y)) if y else set() for y in rot.years]


def fallow_periods(rot: Rotation) -> list[dict]:
    """Runs of uncovered months over the whole cycle (wrapping around), as (year, start month, length)."""
    flat = [m in cov for cov in covered_months(rot) for m in range(1, 13)]
    n = len(flat)
    if all(flat) or not any(flat):
        return [] if all(flat) else [{"year": 1, "start_month": 1, "months": n}]
    start = next(i for i in range(n) if flat[i] and not flat[(i + 1) % n])  # last covered month before a gap
    out, i = [], (start + 1) % n
    run_start, length = None, 0
    for _ in range(n):
        if not flat[i]:
            if run_start is None:
                run_start, length = i, 0
            length += 1
        elif run_start is not None:
            out.append({"year": run_start // 12 + 1, "start_month": run_start % 12 + 1, "months": length})
            run_start = None
        i = (i + 1) % n
    if run_start is not None:
        out.append({"year": run_start // 12 + 1, "start_month": run_start % 12 + 1, "months": length})
    return out


def score(rot: Rotation, months_climate: list[dict], weights: dict[str, float], market_crops: set[str],
          slope: dict | None = None, carry: WaterCarry | None = None) -> dict:
    slots = rot.slots
    wins = effective_windows(rot, carry)  # windows with the soil water carried from the previous gap
    n_years = max(1, len(rot.years))
    sub: dict[str, dict] = {}

    def put(key, value, **detail):
        sub[key] = {"value": None if value is None else round(max(0.0, min(1.0, value)), 3),
                    "kind": KIND[key], **detail}

    if not slots:
        return {"total": 0.0, "subscores": {}, "unknown": list(KIND), "irrigation_need_mm_per_year": None,
                "carry": [], "carry_available": False}

    # Production per year: a fallow year adds 0, a double-cropped year can add up to 2 (capped at 1).
    put("suitability", sum(w["score_median"] for w in wins) / n_years,
        fallow_years=sum(1 for y in rot.years if not y))
    put("climate_risk", sum(w["score_p20"] for w in wins) / len(wins),
        max_fail_rate=max(w["fail_rate"] for w in wins))

    etc = sum(w["etc_mm_median"] for w in wins)
    deficit = sum(w["rain_deficit_mm_median"] for w in wins)
    stored = [w["carry"]["stored_mm_median"] for w in wins if "carry" in w]
    put("water", 1 - deficit / etc if etc else None, etc_mm_total=round(etc), rain_deficit_mm_total=round(deficit),
        stored_soil_water_mm_total=sum(stored) if carry is not None and carry.available else None)

    cov = covered_months(rot)
    living_share = sum(len(c) for c in cov) / (12 * n_years)
    depths = [min(1.0, (s.crop.root_depth_m or 0) / ROOT_DEPTH_REF_M) for s in slots]
    put("soil", 0.5 * sum(depths) / len(depths) + 0.5 * living_share,
        living_root_month_share=round(living_share, 2), proxy=True)

    weights_m = {m["month"]: (m.get("heavy_rain_days") or 0.0) + 0.1 for m in months_climate} or \
        {m: 1.0 for m in range(1, 13)}
    total_w = sum(weights_m.values()) * n_years
    covered_w = sum(weights_m.get(m, 1.0) for c in cov for m in c) / total_w
    if slope and slope.get("status") == "ok":
        rel_s = slope["relative_s"]
        put("erosion", 1 - (1 - covered_w) * rel_s, bare_weighted_share=round(1 - covered_w, 3),
            relative_slope_factor=rel_s, slope_pct=slope["slope_pct_median"])
    else:
        put("erosion", covered_w, bare_weighted_share=round(1 - covered_w, 3), relative_slope_factor=None,
            note="slope unknown: unit-plot slope (9 %) assumed")

    legume_years = sum(any(s.crop.nitrogen_fixing for s in y) for y in rot.years) / n_years
    seq = slots
    cereal_idx = [i for i, s in enumerate(seq) if s.crop.group in CEREAL_GROUPS]
    after_legume = sum(seq[i - 1].crop.nitrogen_fixing for i in cereal_idx) / len(cereal_idx) if cereal_idx else 0.0
    put("nitrogen", 0.6 * legume_years + 0.4 * after_legume,
        legume_year_share=round(legume_years, 2), cereal_after_legume_share=round(after_legume, 2))

    if market_crops:
        put("income", sum(s.crop.id in market_crops for s in slots) / len(slots))
    else:
        put("income", None, reason="no_market_input")
    put("forage", sum(s.crop.group == "forage" for s in slots) / len(slots))
    put("diversity", len({s.crop.family for s in slots}) / len(slots))

    w = {k: float(weights.get(k, 3.0)) for k in PRIORITIES} | FIXED_WEIGHTS | {"suitability": SUITABILITY_WEIGHT}
    num = den = 0.0
    for k, v in sub.items():
        v["weight"] = w[k]
        if v["value"] is not None and w[k] > 0:
            num += w[k] * v["value"]
            den += w[k]
    return {
        "total": round(num / den, 3) if den else 0.0,
        "subscores": sub,
        "unknown": [k for k, v in sub.items() if v["value"] is None],
        "irrigation_need_mm_per_year": round(deficit / n_years),
        "carry": [w.get("carry") for w in wins],
        "slot_stats": [{k: w[k] for k in ("score_median", "score_p20", "fail_rate", "rain_deficit_mm_median")}
                       for w in wins],
        "carry_available": bool(carry is not None and carry.available),
    }
