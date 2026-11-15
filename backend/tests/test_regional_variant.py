"""Regional cultivar variants (Punjab wheat, decision 2026-11-14)."""

from app.config import ROOT
from app.suitability.confidence import assess
from app.suitability.crops import load_crops, localize
from app.suitability.engine import evaluate_crop
from tests.test_engine import make_climate

DATA = ROOT / "data"
PUNJAB, KONYA, LAHORE = (30.80, 75.60), (37.60, 32.75), (31.55, 74.35)


def at(lat, lon):
    return {c.id: c for c in localize(load_crops(DATA), lat, lon, DATA)}


def test_punjab_wheat_gets_the_derived_thermal_time():
    p = at(*PUNJAB)
    for cid in ("winter_wheat", "spring_wheat"):
        c = p[cid]
        assert c.variant["id"] == "punjab_india" and c.variant["source"] == "kaur2025"
        assert c.temperature.t_sum == (2482 + 2639) / 2 and c.temperature.t_base == 0
        assert "154 / 146 / 136 days" in c.variant["assumption"]
        # everything else is the base cultivar
        base = {x.id: x for x in load_crops(DATA)}[cid]
        assert (c.temperature.t_opt, c.temperature.t_heat, c.kc_mid) == (
            base.temperature.t_opt, base.temperature.t_heat, base.kc_mid)


def test_other_places_and_crops_unchanged():
    base = {c.id: c for c in load_crops(DATA)}
    for point in (KONYA, LAHORE):  # Lahore lies in the box but its GGCMI cell is not Indian statistics
        loc = at(*point)
        assert all(loc[k] is base[k] for k in base)
    p = at(*PUNJAB)
    assert p["rice"] is base["rice"] and p["barley"] is base["barley"]


def test_variant_lengthens_the_season_and_is_reported():
    p, base = at(*PUNJAB), {c.id: c for c in load_crops(DATA)}
    clim = make_climate(tmean=15.0, precip=10.0)
    r_var = evaluate_crop(p["winter_wheat"], clim)
    r_base = evaluate_crop(base["winter_wheat"], clim)
    assert r_var["best_window"]["season_days_median"] > r_base["best_window"]["season_days_median"]
    codes = [x["code"] for x in assess(p["winter_wheat"], r_var, "none")["reasons"]]
    assert "regional_variant" in codes and "analogy_assumption" not in codes
