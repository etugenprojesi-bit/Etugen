"""Rotation rules and scoring on hand-made crops and windows (no climate data)."""

import pytest

from app.rotation.engine import (
    Rotation, Slot, allowed, current_rotation, monoculture_reference, recommend, rule_violations, year_plans,
)
from app.rotation.scoring import fallow_periods, score
from app.suitability.crops import Crop


def crop(cid, family, group="cereal", n_fix=False, root=1.0):
    return Crop(id=cid, name={"en": cid, "tr": cid}, scientific=cid, family=family, group=group,
                nitrogen_fixing=n_fix, perennial=False, kc_ini=0.3, kc_mid=1.1, kc_end=0.3,
                root_depth_m=root, temperature=None, stages=None)


def window(months, score=0.8, p20=0.6, fail=0.1, etc=500, deficit=100, sowing=None):
    sow = sowing or f"{months[0]:02d}-01"
    return {"sowing": sow, "harvest_median": f"{months[-1]:02d}-15", "season_days_median": 30 * len(months),
            "season_months": months, "score_median": score, "score_p20": p20, "fail_rate": fail,
            "etc_mm_median": etc, "rain_deficit_mm_median": deficit}


def slot(c, months, **kw):
    w = window(months, **kw)
    return Slot(c, w, frozenset(months))


WHEAT = crop("wheat", "Poaceae", root=1.6)
BARLEY = crop("barley", "Poaceae", root=1.2)
LENTIL = crop("lentil", "Fabaceae", group="legume", n_fix=True, root=0.7)
SUNFLOWER = crop("sunflower", "Asteraceae", group="oilseed", root=1.2)
RICE = crop("rice", "Poaceae", root=0.75)
CHICKPEA = crop("chickpea", "Fabaceae", group="legume", n_fix=True, root=0.8)
WINTER = [10, 11, 12, 1, 2, 3, 4, 5, 6]
SUMMER = [6, 7, 8, 9, 10]
MONTHS = [{"month": m, "heavy_rain_days": 2.0 if m in (11, 12, 1, 2) else 0.0} for m in range(1, 13)]


def test_rules_catch_same_family_and_repeated_crop_including_cycle_wrap():
    rot = Rotation("current", [(slot(WHEAT, WINTER),), (slot(LENTIL, WINTER),), (slot(BARLEY, WINTER),)])
    v = rule_violations(rot)
    # barley (year 3) -> wheat (year 1) wraps around: both Poaceae
    assert {x["code"] for x in v} == {"same_family_consecutive"}
    mono = Rotation("reference", [(slot(WHEAT, WINTER),)] * 3)
    codes = {x["code"] for x in rule_violations(mono)}
    assert codes == {"same_family_consecutive", "same_crop_consecutive_years"}


def test_double_crop_needs_disjoint_months_and_different_families():
    plans = year_plans({
        "rice": [slot(RICE, [6, 7, 8, 9, 10])],
        "wheat": [slot(WHEAT, [11, 12, 1, 2, 3])],
        "lentil": [slot(LENTIL, [11, 12, 1, 2, 3])],
        "sunflower": [slot(SUNFLOWER, [4, 5, 6, 7])],
    })
    pairs = {tuple(sorted(s.crop.id for s in p)) for p in plans if len(p) == 2}
    assert ("lentil", "rice") in pairs           # disjoint, different families
    assert ("rice", "wheat") not in pairs        # both Poaceae
    assert ("rice", "sunflower") not in pairs    # overlap in June-July
    assert ("lentil", "wheat") not in pairs      # same months


def test_recommendations_follow_rules_and_are_diverse():
    slots = {c.id: [slot(c, WINTER, score=s)] for c, s in
             [(WHEAT, 0.9), (BARLEY, 0.85), (LENTIL, 0.7), (CHICKPEA, 0.65), (SUNFLOWER, 0.6)]}
    fn = lambda r: score(r, MONTHS, {}, set())  # noqa: E731
    recs = recommend(slots, fn)
    assert 1 <= len(recs) <= 3
    for r in recs:
        assert not rule_violations(r)
    sets = [set(r.crop_ids()) for r in recs]
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            assert len(sets[i] & sets[j]) / len(sets[i] | sets[j]) <= 0.5


def test_nitrogen_rewards_legume_before_cereal():
    with_legume = Rotation("x", [(slot(LENTIL, WINTER),), (slot(WHEAT, WINTER),), (slot(SUNFLOWER, SUMMER),)])
    without = Rotation("x", [(slot(SUNFLOWER, SUMMER),), (slot(WHEAT, WINTER),), (slot(SUNFLOWER, SUMMER),)])
    a = score(with_legume, MONTHS, {}, set())["subscores"]["nitrogen"]
    b = score(without, MONTHS, {}, set())["subscores"]["nitrogen"]
    assert a["value"] == pytest.approx(0.6 / 3 + 0.4 * 1.0)
    assert b["value"] == 0


def test_water_score_and_irrigation_need():
    rot = Rotation("x", [(slot(WHEAT, WINTER, etc=400, deficit=100),),
                         (slot(LENTIL, WINTER, etc=300, deficit=0),),
                         (slot(SUNFLOWER, SUMMER, etc=500, deficit=200),)])
    s = score(rot, MONTHS, {}, set())
    assert s["subscores"]["water"]["value"] == pytest.approx(1 - 300 / 1200)
    assert s["irrigation_need_mm_per_year"] == 100


def test_erosion_weights_cover_in_heavy_rain_months():
    winter_cover = Rotation("x", [(slot(WHEAT, [11, 12, 1, 2]),)] * 3)
    summer_cover = Rotation("x", [(slot(SUNFLOWER, [5, 6, 7, 8]),)] * 3)
    e_w = score(winter_cover, MONTHS, {}, set())["subscores"]["erosion"]["value"]
    e_s = score(summer_cover, MONTHS, {}, set())["subscores"]["erosion"]["value"]
    assert e_w > 0.8 > 0.1 > e_s


def test_income_unknown_without_market_input_and_weights_matter():
    rot = Rotation("x", [(slot(WHEAT, WINTER),), (slot(LENTIL, WINTER),), (slot(SUNFLOWER, SUMMER),)])
    no_market = score(rot, MONTHS, {}, set())
    assert no_market["subscores"]["income"]["value"] is None and "income" in no_market["unknown"]
    market = score(rot, MONTHS, {"income": 5}, {"lentil"})
    assert market["subscores"]["income"]["value"] == pytest.approx(1 / 3, abs=1e-3)
    nitrogen_first = score(rot, MONTHS, {"nitrogen": 5, "water": 0, "soil": 0, "erosion": 0, "forage": 0}, set())
    water_first = score(rot, MONTHS, {"water": 5, "nitrogen": 0, "soil": 0, "erosion": 0, "forage": 0}, set())
    assert nitrogen_first["total"] != water_first["total"]


def test_fallow_periods_wrap_around_the_cycle():
    rot = Rotation("x", [(slot(SUNFLOWER, [4, 5, 6, 7, 8]),)] * 3)
    gaps = fallow_periods(rot)
    assert [g["months"] for g in gaps] == [7, 7, 7]   # Sep..Mar each year
    assert gaps[0]["start_month"] == 9


def test_constraints_and_current_rotation():
    assert not allowed(WHEAT, {"excluded_crops": ["wheat"]})
    potato = crop("potato", "Solanaceae", group="root_tuber")
    assert not allowed(potato, {"equipment_limits": ["no_root_harvester"]})
    assert allowed(potato, {"equipment_limits": ["no_paddy"]})
    results = {"wheat": {"status": "evaluated", "best_window": window(WINTER), "windows": [window(WINTER)]},
               "chickpea": {"status": "insufficient_data"}}
    rot = current_rotation([["wheat"], ["chickpea"], ["wheat"]], {"wheat": WHEAT, "chickpea": CHICKPEA}, results)
    assert [len(y) for y in rot.years] == [1, 0, 1]
    assert rot.missing_slots == [{"year": 2, "crop_id": "chickpea", "status": "insufficient_data"}]


def test_monoculture_reference_uses_best_crop():
    ref = monoculture_reference({"wheat": [slot(WHEAT, WINTER, score=0.9)], "lentil": [slot(LENTIL, WINTER, score=0.5)]})
    assert ref.kind == "reference" and [s.crop.id for s in ref.slots] == ["wheat"] * 3


def test_fallow_year_breaks_sequences_but_costs_production():
    w, b, ln = slot(WHEAT, WINTER, score=0.8), slot(BARLEY, WINTER, score=0.8), slot(LENTIL, WINTER, score=0.8)
    assert not rule_violations(Rotation("x", [(w,), (ln,), ()]))          # wheat, lentil, fallow
    assert rule_violations(Rotation("x", [(w,), (), (w,)]))               # wheat meets wheat at the wrap
    assert not rule_violations(Rotation("x", [(w,), (), (ln,)]))
    with_fallow = score(Rotation("x", [(w,), (ln,), ()]), MONTHS, {}, set())["subscores"]["suitability"]
    no_fallow = score(Rotation("x", [(w,), (ln,), (b,)]), MONTHS, {}, set())["subscores"]["suitability"]
    assert with_fallow["value"] == pytest.approx(1.6 / 3, abs=1e-3) and with_fallow["fallow_years"] == 1
    assert no_fallow["value"] == pytest.approx(0.8, abs=1e-3)


def test_only_cereals_available_still_gives_a_rotation_with_fallow():
    slots = {"wheat": [slot(WHEAT, WINTER, score=0.5)], "barley": [slot(BARLEY, WINTER, score=0.45)]}
    recs = recommend(slots, lambda r: score(r, MONTHS, {}, set()))
    assert recs, "a cereal-fallow cycle must be possible"
    assert all(any(not y for y in r.years) for r in recs) and not any(rule_violations(r) for r in recs)
    assert {len(r.years) for r in recs} == {2}  # wheat-fallow / barley-fallow
