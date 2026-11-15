"""Two-stage rotation search (app.rotation.search) against the exhaustive search and scoring.score."""

import itertools

import numpy as np
import pytest

from app.rotation.engine import Rotation, candidate_cycles, recommend, rule_violations, year_plans
from app.rotation.scoring import score
from app.rotation.search import Screen, plan_compat
from tests.test_rotation import MONTHS, SUMMER, WINTER, crop, slot

WHEAT = crop("wheat", "Poaceae", root=1.6)
BARLEY = crop("barley", "Poaceae", root=1.2)
LENTIL = crop("lentil", "Fabaceae", group="legume", n_fix=True, root=0.7)
CHICKPEA = crop("chickpea", "Fabaceae", group="legume", n_fix=True, root=0.8)
SUNFLOWER = crop("sunflower", "Asteraceae", group="oilseed", root=1.2)
MAIZE = crop("maize", "Poaceae", root=1.0)
VETCH = crop("vetch", "Fabaceae", group="forage", n_fix=True, root=0.6)
POTATO = crop("potato", "Solanaceae", group="root_tuber", root=0.5)
SPRING = [3, 4, 5]
AUTUMN = [9, 10]


def slots_example():
    """Winter and summer crops, so that double-cropped year plans exist."""
    return {
        "wheat": [slot(WHEAT, [11, 12, 1, 2, 3, 4, 5], score=0.9, p20=0.7, etc=450, deficit=120)],
        "barley": [slot(BARLEY, [11, 12, 1, 2, 3, 4], score=0.85, p20=0.6, etc=400, deficit=90)],
        "lentil": [slot(LENTIL, [11, 12, 1, 2, 3, 4], score=0.7, p20=0.5, etc=300, deficit=40)],
        "chickpea": [slot(CHICKPEA, SPRING, score=0.6, p20=0.3, etc=250, deficit=60)],
        "sunflower": [slot(SUNFLOWER, [6, 7, 8, 9], score=0.75, p20=0.4, etc=500, deficit=300)],
        "maize": [slot(MAIZE, [6, 7, 8, 9, 10], score=0.65, p20=0.2, etc=600, deficit=350)],
        "vetch": [slot(VETCH, AUTUMN, score=0.5, p20=0.4, etc=120, deficit=10)],
        "potato": [slot(POTATO, SPRING, score=0.55, p20=0.3, etc=350, deficit=150)],
    }


def canonical(rot: Rotation, index: dict) -> tuple:
    ids = tuple(index[tuple(id(s) for s in y)] if y else -1 for y in rot.years)
    return min(ids[i:] + ids[:i] for i in range(len(ids)))


def as_rotation(plans, cyc) -> Rotation:
    return Rotation("recommended", [plans[i] if i >= 0 else () for i in cyc if i != -2])


@pytest.fixture
def plans():
    return year_plans(slots_example())


SLOPE = {"status": "ok", "relative_s": 0.6, "slope_pct_median": 4.0}
SETTINGS = [
    ({}, set(), None),
    ({"water": 5, "nitrogen": 0, "forage": 4}, {"lentil", "sunflower"}, SLOPE),
    ({"soil": 1, "erosion": 5, "income": 2}, {"wheat"}, None),
]


@pytest.mark.parametrize("weights,market,slope", SETTINGS)
def test_screen_total_equals_rotation_score_without_carry(plans, weights, market, slope):
    screen = Screen(MONTHS, weights, market, slope)
    tot, cyc = screen.cycles(plans)
    assert len(tot) > 100
    for t, c in zip(tot, cyc):
        exact = score(as_rotation(plans, c), MONTHS, weights, market, slope)["total"]
        assert t == pytest.approx(exact, abs=2e-3)  # score() rounds sub-scores to 3 decimals


def test_screen_enumerates_exactly_the_rule_abiding_cycles(plans):
    assert any(len(p) == 2 for p in plans)
    index = {tuple(id(s) for s in p): i for i, p in enumerate(plans)}
    brute = {canonical(r, index) for r in candidate_cycles(plans)}
    _, cyc = Screen(MONTHS, {}, set()).cycles(plans)
    screened = [canonical(as_rotation(plans, c), index) for c in cyc]
    assert len(screened) == len(set(screened))  # each cycle once
    assert set(screened) == brute
    assert all(not rule_violations(as_rotation(plans, c)) for c in cyc)


def test_plan_compat_matches_the_rules(plans):
    c = plan_compat(plans)
    for i, j in itertools.permutations(range(len(plans)), 2):
        # a 3-year cycle i, j, fallow breaks a rule exactly when j cannot follow i
        assert c[i, j] == (not rule_violations(Rotation("x", [plans[i], plans[j], ()])))
    assert not c.diagonal().any()


def test_top_cycles_caps_crop_sets_and_maps_plan_indices(plans):
    screen = Screen(MONTHS, {}, set())
    top = screen.top_cycles(plans, k=50, per_crop_set=1)
    sets = [frozenset(cid for i in cyc if i >= 0 for cid in (s.crop.id for s in plans[i])) for _, cyc in top]
    assert len(sets) == len(set(sets))
    assert [t for t, _ in top] == sorted((t for t, _ in top), reverse=True)
    # with a plan cut, indices still point into the full plan list and only the best plans are used
    few = screen.top_cycles(plans, k=50, max_plans=5)
    best5 = set(np.argsort(-screen.plan_totals(plans), kind="stable")[:5].tolist())
    for t, cyc in few:
        assert {i for i in cyc if i >= 0} <= best5
        assert t == pytest.approx(score(as_rotation(plans, cyc), MONTHS, {}, set())["total"], abs=2e-3)


def test_recommend_with_screen_matches_exhaustive_search():
    slots = slots_example()
    fn = lambda r: score(r, MONTHS, {}, set())  # noqa: E731
    exhaustive = recommend(slots, fn)
    screened = recommend(slots, fn, screen=Screen(MONTHS, {}, set()))
    assert [fn(r)["total"] for r in screened] == [fn(r)["total"] for r in exhaustive]
    assert all(not rule_violations(r) for r in screened)


def test_on_candidates_sees_every_scored_rotation():
    seen = []
    recommend(slots_example(), lambda r: score(r, MONTHS, {}, set()), on_candidates=seen.extend,
              screen=Screen(MONTHS, {}, set()))
    assert 0 < len(seen) <= 300 and all(isinstance(r, Rotation) for r in seen)


def test_screen_handles_only_fallow_compatible_plans():
    one = {"wheat": [slot(WHEAT, WINTER, score=0.5)], "barley": [slot(BARLEY, SUMMER, score=0.4)]}
    plans = year_plans(one)  # same family: no double crop, wheat <-> barley incompatible
    tot, cyc = Screen(MONTHS, {}, set()).cycles(plans)
    assert sorted(tuple(c) for c in cyc.tolist()) == [(0, -1, -2), (1, -1, -2)]
    assert Screen(MONTHS, {}, set()).cycles([])[1].shape == (0, 3)
