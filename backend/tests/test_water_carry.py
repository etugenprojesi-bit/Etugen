"""Soil water carried between crops (fallow), on the Konya demo data (offline)."""

import asyncio

import numpy as np
import pytest

from app.api.analyze import load_point
from app.config import get_settings
from app.rotation.engine import Rotation, make_slots
from app.rotation.scoring import score
from app.rotation.water_carry import WaterCarry, effective_windows, predecessors
from app.sources import soilgrids
from app.suitability.crops import load_crops
from app.suitability.engine import evaluate_crop

KONYA = (37.60, 32.75)
MONTHS = [{"month": m, "heavy_rain_days": 1.0} for m in range(1, 13)]


@pytest.fixture(scope="module")
def konya(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    mp.setenv("CACHE_PATH", str(tmp_path_factory.mktemp("c") / "cache.sqlite"))
    mp.setenv("LAST_FULL_YEAR", "2025")
    get_settings.cache_clear()

    async def offline(*a, **k):
        raise soilgrids.SourceError("offline (test)")

    mp.setattr(soilgrids, "fetch_raw", offline)
    pt = asyncio.run(load_point(*KONYA))
    raw, origin = asyncio.run(soilgrids.load_point(pt.lat, pt.lon, None, get_settings().demo_cache_dir))
    crops = {c.id: c for c in load_crops(get_settings().data_dir)}
    res = {cid: evaluate_crop(crops[cid], pt.clim) for cid in ("winter_wheat", "lentil")}
    yield pt, soilgrids.parse(raw, origin), crops, res
    mp.undo()
    get_settings.cache_clear()


def _carry(pt, soil, res):
    return WaterCarry(pt.clim, soil, "none", {cid: r["light_ref"] for cid, r in res.items()})


def test_soilgrids_demo_values(konya):
    _, soil, crops, _ = konya
    assert soil.origin == "demo_cache"
    assert soil.tew_mm() == pytest.approx(20.3, abs=0.1)          # probe result, DATA_SOURCES §3b
    assert soil.taw_mm(1.5) == pytest.approx(137.6, abs=0.1)
    assert soil.taw_mm(3.0) == soil.taw_mm(2.0)                    # capped at the deepest layer


def test_season_rows_reproduce_the_window(konya):
    pt, soil, crops, res = konya
    s = make_slots(crops["winter_wheat"], res["winter_wheat"])[0]
    rows = _carry(pt, soil, res).rows(s)
    assert np.median([r["score"] for r in rows.values()]) == pytest.approx(s.window["score_median"], abs=5e-4)


def test_predecessors_count_fallow_years():
    a, b = object(), object()
    rot = Rotation("recommended", [(a,), (), (b,)])
    assert [(s is x, p is y, k) for (s, p, k), (x, y) in zip(predecessors(rot), [(a, b), (b, a)])] == \
        [(True, True, 0), (True, True, 1)]


def test_wheat_fallow_stores_plausible_water(konya):
    pt, soil, crops, res = konya
    w = make_slots(crops["winter_wheat"], res["winter_wheat"])[0]
    carry = _carry(pt, soil, res)
    t = carry.transition(w, w, 1)
    assert t.usable and len(t.years) >= 20
    eff = np.median(t.stored / t.precip)
    # Janssen (1972), Great Konya Basin: fallow efficiency 14-33 % (DATA_SOURCES §7)
    assert 0.10 <= eff <= 0.35
    assert np.all(t.stored <= t.taw + 1e-9)
    assert np.all(t.gap_days > 365)
    # a direct wheat -> wheat summer gap stores (almost) nothing
    assert np.median(carry.transition(w, w, 0).stored) < 10


def test_fallow_raises_next_crop_score_not_production(konya):
    pt, soil, crops, res = konya
    w = make_slots(crops["winter_wheat"], res["winter_wheat"])[0]
    rot = Rotation("recommended", [(w,), ()])
    without = score(rot, MONTHS, {}, set())
    with_carry = score(rot, MONTHS, {}, set(), carry=_carry(pt, soil, res))
    win = effective_windows(rot, _carry(pt, soil, res))[0]
    assert win["score_median"] > w.window["score_median"]
    assert win["rain_deficit_mm_median"] < w.window["rain_deficit_mm_median"]
    assert with_carry["subscores"]["water"]["value"] > without["subscores"]["water"]["value"]
    # the fallow year itself still produces nothing: production = wheat score / 2 years
    assert with_carry["subscores"]["suitability"]["value"] == pytest.approx(win["score_median"] / 2, abs=1e-3)
    assert with_carry["carry"][0]["n_fallow_years"] == 1


def test_no_soil_data_leaves_scores_unchanged(konya):
    pt, soil, crops, res = konya
    w = make_slots(crops["winter_wheat"], res["winter_wheat"])[0]
    rot = Rotation("recommended", [(w,), ()])
    empty = soilgrids.SoilWater({}, "none")
    carry = _carry(pt, empty, res)
    assert not carry.available
    assert score(rot, MONTHS, {}, set(), carry=carry)["subscores"] == score(rot, MONTHS, {}, set())["subscores"]
