"""ECOCROP path: general temperature ranges for crops without literature parameters."""

import dataclasses

import numpy as np
import pytest

from app.config import ROOT
from app.suitability.confidence import assess
from app.suitability.crops import Ecocrop, Temperature, load_crops
from app.suitability.engine import ecocrop_temperature_score, evaluable, evaluate_crop
from tests.test_engine import crop, make_climate

OATS = (5.0, 16.0, 20.0, 30.0)  # ECOCROP data sheet 481: TMIN, TOPMN, TOPMX, TMAX


def eco_crop(temp=OATS, stages_total=100):
    c = crop(stages_total=stages_total)
    t = Temperature(temp[0], temp[1], None, None, None, "ecocrop", True,
                    ecocrop=Ecocrop(481, temp, (110.0, 270.0)))
    return dataclasses.replace(c, temperature=t)


@pytest.mark.parametrize("tm, score", [(18.0, 1.0), (16.0, 1.0), (10.5, 0.5), (25.0, 0.5), (5.0, 0.0), (31.0, 0.0)])
def test_trapezoid_on_block_mean(tm, score):
    assert ecocrop_temperature_score(np.full(60, tm), OATS) == pytest.approx(score)


def test_season_takes_the_worst_block():
    # 30 days at 18 °C (1.0) then 30 days at 25 °C (0.5) -> 0.5, not the mean 0.75
    season = np.concatenate([np.full(30, 18.0), np.full(30, 25.0)])
    assert ecocrop_temperature_score(season, OATS) == pytest.approx(0.5)


def test_block_mean_smooths_single_hot_days():
    season = np.full(30, 18.0)
    season[5] = 40.0  # one hot day; block mean 18.73 -> still optimal
    assert ecocrop_temperature_score(season, OATS) == pytest.approx(1.0)


def test_engine_uses_fixed_season_and_trapezoid():
    res = evaluate_crop(eco_crop(stages_total=100), make_climate(tmean=25.0, precip=10.0))
    w = res["best_window"]
    assert res["status"] == "evaluated"
    assert w["season_days_median"] == 100
    assert w["temperature_score_median"] == pytest.approx(0.5)


def test_confidence_is_low_with_ecocrop_reason():
    c = eco_crop()
    res = evaluate_crop(c, make_climate(tmean=18.0, precip=10.0))
    conf = assess(c, res, "none")
    codes = [r["code"] for r in conf["reasons"]]
    assert conf["level"] == "low" and "ecocrop_general_ranges" in codes


def test_loaded_ecocrop_crops_and_literature_crops_unchanged():
    crops = {c.id: c for c in load_crops(ROOT / "data")}
    for cid in ("oats", "faba_bean", "dry_pea", "cowpea", "safflower", "sesame", "flax",
                "sweet_potato", "sugar_beet", "chickpea", "cereal_rye"):
        c = crops[cid]
        assert evaluable(c) == (True, None), cid
        assert c.temperature.source == "ecocrop" and c.temperature.ecocrop is not None
    assert crops["oats"].temperature.ecocrop.temp == OATS
    assert crops["oats"].temperature.ecocrop.url.endswith("dataSheet?id=481")
    # literature crops keep their own parameters
    assert crops["winter_wheat"].temperature.source == "zhao2019"
    assert crops["lentil"].temperature.ecocrop is None


def test_analogies_are_labelled():
    crops = {c.id: c for c in load_crops(ROOT / "data")}
    rye, barley = crops["cereal_rye"], crops["barley"]
    assert (rye.kc_mid, rye.root_depth_m) == (barley.kc_mid, barley.root_depth_m)
    assert rye.stages.row.startswith("Barley/Oats/Wheat") and len(rye.assumptions) == 2
    assert crops["chickpea"].stages.row.startswith("Lentil") and crops["chickpea"].assumptions
    assert "fao56_kc" not in rye.missing


def test_reason_codes_are_unique_per_crop():
    from app.suitability.engine import evaluate_crop as ev
    crops = {c.id: c for c in load_crops(ROOT / "data")}
    rye = crops["cereal_rye"]
    conf = assess(rye, ev(rye, make_climate(tmean=17.0, precip=10.0)), "none")
    codes = [r["code"] for r in conf["reasons"]]
    assert len(codes) == len(set(codes)) and "analogy_assumption" in codes


def test_counts_after_ecocrop():
    crops = load_crops(ROOT / "data")
    # 15 literature + 11 + 15 ECOCROP crops (2026-11-12/13) + Sudan grass and berseem (2026-11-14)
    assert sum(evaluable(c)[0] for c in crops) == 43


def test_cut_forage_first_cut_only_is_labelled_and_kept_out_of_rotations():
    from app.rotation.engine import make_slots
    crops = {c.id: c for c in load_crops(ROOT / "data")}
    sudan, berseem = crops["sudan_grass"], crops["berseem_clover"]
    assert sudan.temperature.ecocrop.id == 9970 and sudan.scientific == "Sorghum × drummondii"
    assert berseem.temperature.ecocrop.id == 10522
    assert sudan.stages.row.startswith("Sudan, 1^st cutting cycle") and sudan.stages.total == 75
    assert berseem.stages.row.startswith("Alfalfa 1^st cutting cycle") and "Analogy" in berseem.assumptions[0]
    assert sudan.first_cut_only and berseem.first_cut_only and not crops["oats"].first_cut_only
    res = evaluate_crop(berseem, make_climate(tmean=18.0, precip=10.0))
    assert res["status"] == "evaluated"
    assert make_slots(berseem, res) == []                   # evaluated, but never a rotation slot
    for cid in ("rapeseed", "mustard", "buckwheat", "ryegrass", "vetch", "phacelia"):
        assert evaluable(crops[cid]) == (False, "insufficient_data"), cid
    assert evaluable(crops["alfalfa"]) == (False, "perennial_not_evaluated")
