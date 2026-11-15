"""WOFOST-style development (DTSMTB table + emergence phase) and the barley parameters."""

import dataclasses

import numpy as np
import pytest

from app.config import ROOT
from app.suitability.crops import Emergence, load_crops
from app.suitability.engine import daily_thermal_time, evaluate_crop, evaluable
from tests.test_engine import crop, make_climate


def test_dev_rate_table_interpolates_and_caps():
    t = dataclasses.replace(crop().temperature, dev_rate_table=((0, 0), (35, 35), (45, 35)))
    got = daily_thermal_time(t, np.array([-5.0, 0.0, 12.5, 35.0, 40.0, 50.0]))
    assert got.tolist() == pytest.approx([0, 0, 12.5, 35, 35, 35])


def test_nonlinear_table_is_used_as_given():
    # Field-bean DTSMTB shape (Boons-Prins et al. 1993, App. G1): 20 °C -> 22.5 °C·d
    t = dataclasses.replace(crop().temperature, dev_rate_table=((0, 0), (20, 22.5), (25, 25), (35, 25)))
    assert daily_thermal_time(t, np.array([10.0, 20.0, 30.0])).tolist() == pytest.approx([11.25, 22.5, 25])


def test_without_table_the_simple_formula_is_unchanged():
    t = crop(t_base=5).temperature
    assert daily_thermal_time(t, np.array([0.0, 5.0, 20.0])).tolist() == [0, 0, 15]


def test_emergence_rate_has_own_base_and_cap():
    em = Emergence(t_base=3, t_sum=110, t_eff_max=30)
    assert em.rate(np.array([0.0, 13.0, 40.0])).tolist() == [0, 10, 27]


def test_emergence_phase_is_added_before_t_sum():
    # Tmean 20: emergence (3 °C base) 17 °C·d/day -> 110 °C·d after 7 days (119 >= 110);
    # then 1000 °C·d at 20 °C·d/day = 50 days -> 57 days in total.
    c = crop(t_sum=1000)
    c = dataclasses.replace(c, temperature=dataclasses.replace(
        c.temperature, emergence=Emergence(3, 110, 30), dev_rate_table=((0, 0), (35, 35), (45, 35))))
    res = evaluate_crop(c, make_climate(tmean=20.0, precip=10.0))
    assert res["best_window"]["season_days_median"] == 57


def test_capped_table_lengthens_hot_seasons():
    hot = make_climate(tmean=40.0, precip=10.0)
    plain = evaluate_crop(crop(t_sum=1050, t_heat=50, t_ext=60), hot)["best_window"]["season_days_median"]
    c = crop(t_sum=1050, t_heat=50, t_ext=60)
    c = dataclasses.replace(c, temperature=dataclasses.replace(
        c.temperature, dev_rate_table=((0, 0), (35, 35), (45, 35))))
    capped = evaluate_crop(c, hot)["best_window"]["season_days_median"]
    assert (plain, capped) == (27, 30)  # 1050/40 -> 27 days, 1050/35 -> 30 days


def test_barley_is_evaluable_with_report_values():
    crops = {c.id: c for c in load_crops(ROOT / "data")}
    b = crops["barley"]
    assert evaluable(b) == (True, None)
    t = b.temperature
    assert (t.t_base, t.t_sum, t.t_heat) == (0.0, 1550.0, None)
    assert t.dev_rate_table == ((0, 0), (35, 35), (45, 35))
    assert t.emergence == Emergence(3.0, 110.0, 30.0)
    assert t.verified and b.missing == ["heat_thresholds"]


def test_crop_counts():
    crops = load_crops(ROOT / "data")
    usable = [c.id for c in crops if "temperature_limits" not in c.missing]
    full = [c.id for c in crops if not c.missing]
    assert len(crops) == 50 and len(usable) == 43 and len(full) == 10  # 43 incl. 28 ECOCROP crops
