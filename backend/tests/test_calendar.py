"""Local sowing calendar (GGCMI Phase 3) and the best-window rule (decision K1-a)."""

import asyncio

import pytest

from app.api.analyze import load_point
from app.config import get_settings
from app.suitability import calendar
from app.suitability.crops import load_crops
from app.suitability.engine import evaluate_crop

KONYA, PUNJAB = (37.60, 32.75), (30.80, 75.60)


@pytest.fixture(scope="module")
def setup(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    mp.setenv("CACHE_PATH", str(tmp_path_factory.mktemp("c") / "cache.sqlite"))
    mp.setenv("LAST_FULL_YEAR", "2025")
    get_settings.cache_clear()
    s = get_settings()
    crops = {c.id: c for c in load_crops(s.data_dir)}
    points = {k: asyncio.run(load_point(*p)) for k, p in (("konya", KONYA), ("punjab", PUNJAB))}
    yield s.data_dir, crops, points
    mp.undo()
    get_settings.cache_clear()


def test_lookup_values_from_ggcmi(setup):
    data_dir, _, _ = setup
    c = calendar.lookup(data_dir, "winter_wheat", *KONYA)
    # DATA_SOURCES §8: nearest cell 37.75, 32.75; rainfed winter wheat 10-21 -> 07-09 (SAGE)
    assert (c["planting"], c["maturity"], c["data_source"]) == ("10-21", "07-09", "SAGE")
    assert c["cell"] == {"lat": 37.75, "lon": 32.75} and c["system"] == "rainfed"
    assert calendar.lookup(data_dir, "winter_wheat", *PUNJAB)["planting"] == "11-04"
    assert calendar.lookup(data_dir, "maize_grain", *KONYA, irrigation="full")["system"] == "irrigated"
    assert calendar.lookup(data_dir, "lentil", *KONYA) is None          # not in GGCMI
    assert calendar.lookup(data_dir, "winter_wheat", 0.0, -30.0) is None  # ocean cell: no value
    # longitudes outside -180..180 wrap around
    assert calendar.lookup(data_dir, "winter_wheat", 37.60, 32.75 + 360) == c


def test_days_apart_is_circular():
    assert calendar.days_apart("01-01", 365) == 1
    assert calendar.days_apart("12-16", 15) == 30   # doy 350 -> 15: 15 + 15
    assert calendar.days_apart("10-16", 294) == 5


def test_best_window_follows_local_calendar(setup):
    data_dir, crops, points = setup
    for key, latlon in (("konya", KONYA), ("punjab", PUNJAB)):
        cal = calendar.lookup(data_dir, "winter_wheat", *latlon)
        r = evaluate_crop(crops["winter_wheat"], points[key].clim, local_calendar=cal)
        assert r["calendar_rule"]
        assert r["best_window"]["in_local_calendar"]
        assert r["best_window"]["days_from_local_planting"] <= calendar.WINDOW_DAYS
        assert all(w["sowing"] in [x["sowing"] for x in r["windows"] if x["in_local_calendar"]]
                   for w in [r["best_window"]])
        free = evaluate_crop(crops["winter_wheat"], points[key].clim, local_calendar=cal, use_calendar=False)
        assert not free["calendar_rule"]
        assert free["best_window"]["score_median"] >= r["best_window"]["score_median"]
    # Punjab: free choice sows wheat into the monsoon (July); the calendar rule moves it to the rabi season
    cal = calendar.lookup(data_dir, "winter_wheat", *PUNJAB)
    r = evaluate_crop(crops["winter_wheat"], points["punjab"].clim, local_calendar=cal)
    assert r["best_window"]["sowing"][:2] in ("09", "10", "11", "12")
    assert r["best_window_outside_calendar"]["sowing"][:2] in ("06", "07", "08")


def test_without_calendar_nothing_changes(setup):
    _, crops, points = setup
    a = evaluate_crop(crops["lentil"], points["konya"].clim)
    assert a["local_calendar"] is None and not a["calendar_rule"]
    assert a["best_window_outside_calendar"] is None
    assert all(w["in_local_calendar"] is None for w in a["windows"])


def test_gap_filled_irrigated_cell_falls_back_to_observed_rainfed(setup):
    """Punjab cell: irrigated barley (June) and sugar beet have no named GGCMI source (0)."""
    data_dir, _, _ = setup
    bar = calendar.lookup(data_dir, "barley", *PUNJAB, irrigation="full")
    assert bar["system"] == "rainfed" and bar["fallback_from"] == "irrigated"
    assert bar["planting"] == "11-01" and bar["data_source"] == "MIRCA2000" and not bar["gap_filled"]
    sgb = calendar.lookup(data_dir, "sugar_beet", *PUNJAB, irrigation="full")
    assert sgb["system"] == "rainfed" and sgb["planting"] == "06-01"
    # observed irrigated cells are kept
    wwh = calendar.lookup(data_dir, "winter_wheat", *PUNJAB, irrigation="full")
    assert wwh["system"] == "irrigated" and wwh["fallback_from"] is None and not wwh["gap_filled"]


def test_calendar_conflict_when_no_in_calendar_window_grows(setup):
    """Punjab dry pea: GGCMI (India statistics) says June; the model fails every summer window."""
    data_dir, crops, points = setup
    cal = calendar.lookup(data_dir, "dry_pea", *PUNJAB)
    assert cal["planting"] == "06-11" and cal["data_source"] == "India agricultural statistics"
    r = evaluate_crop(crops["dry_pea"], points["punjab"].clim, local_calendar=cal)
    assert r["calendar_conflict"] and not r["calendar_rule"]
    assert all(w["score_median"] == 0 for w in r["windows"] if w["in_local_calendar"])
    assert r["best_window"]["score_median"] > 0 and not r["best_window"]["in_local_calendar"]
    ok = evaluate_crop(crops["winter_wheat"], points["punjab"].clim,
                       local_calendar=calendar.lookup(data_dir, "winter_wheat", *PUNJAB))
    assert ok["calendar_rule"] and not ok["calendar_conflict"]
